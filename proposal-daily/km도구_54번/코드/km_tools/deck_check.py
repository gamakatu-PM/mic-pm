# -*- coding: utf-8 -*-
# 54판 v12 2026-09-27  (★제안서_PPT.py 가 이 줄의 v숫자로 새 판인지 가린다)
"""deck_check - 만든 제안서 pptx 의 글자 넘침·겹침·붙음·표 밀림을 잰다. 토큰 0. 메뉴 번호 없음(부품).

왜 만들었나
  2026-09-27 미리보기에서 사람 눈으로 찾은 결함(도어락 구성도 선 위 글자 겹침, 평면 마킹 「현관」 이
  표시 상자에 붙음)을 PC 에서 뽑을 때마다 기계가 먼저 찾게 하려고. 프로님 : "검사기 pc에도 넣어"

어떻게 재나
  브라우저 없이, python-pptx 가 이미 쓰는 Pillow 로 **실제 글꼴(맑은 고딕) 폭**을 재서
  줄바꿈을 계산한다. 그 결과로 글자가 차지하는 자리를 구해 서로 겹치는지 본다.
  PC 에 맑은 고딕이 없으면 비슷한 한글 글꼴로 재고, 어느 글꼴로 쟀는지 결과에 적는다.

재는 것
  넘침      글자가 제 상자보다 길다 (아래로 흘러넘침)
  겹침      서로 다른 두 글자 덩어리가 겹친다
  붙음      글자가 다른 색칠 도형에 걸치거나 3pt 안으로 붙는다 (그 도형 안에 든 글자는 제외)
  표 밀림   표 칸 글자가 줄바꿈되어 표가 바닥글(5.15in)까지 내려온다
  장 밖     글자가 장 아래로 나간다

회사 원본에서 복사한 장(사진·그룹·자리표시자가 있는 장)은 서식을 모르므로 건너뛰고 몇 장인지만 적는다.

쓰는 법
  import deck_check; probs, note = deck_check.check('제안서.pptx')
  python deck_check.py 파일.pptx [폴더 ...]
"""
import os, sys, glob, re

from pptx import Presentation
from pptx.util import Emu
from pptx.enum.shapes import MSO_SHAPE_TYPE

EMU_IN = 914400.0
FOOTER_Y = 5.15          # 바닥글(5.22in) 바로 위
TOUCH = 3 / 72.0         # 3pt 안으로 붙으면 「붙음」

_FONT_CANDS = {
    False: [r'C:\Windows\Fonts\malgun.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'],
    True: [r'C:\Windows\Fonts\malgunbd.ttf', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
           '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'],
}
_cache = {}
FONT_USED = ''


def _font(bold):
    """기준 100px 크기의 글꼴. 폭은 크기에 비례하므로 한 번만 연다."""
    global FONT_USED
    if bold in _cache:
        return _cache[bold]
    from PIL import ImageFont
    f = None
    for p in _FONT_CANDS[bold]:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, 100)
                FONT_USED = FONT_USED or os.path.basename(p)
                break
            except Exception:
                continue
    if f is None:                                   # 글꼴이 하나도 없으면 한글 한 자 = 1em 로 어림
        f = False
        FONT_USED = FONT_USED or '(글꼴 없음 - 어림)'
    _cache[bold] = f
    return f


def _w(text, size_pt, bold):
    """글자 폭 (인치)"""
    f = _font(bold)
    if f:
        try:
            return f.getlength(text) * size_pt / 100.0 / 72.0          # Pillow 8 이상
        except Exception:
            pass
        try:
            b = f.getbbox(text)                                          # Pillow 8 이상 다른 길
            return (b[2] - b[0]) * size_pt / 100.0 / 72.0
        except Exception:
            pass
        try:
            return f.getsize(text)[0] * size_pt / 100.0 / 72.0           # 옛 Pillow (10 에서 없어짐)
        except Exception:
            pass
    return sum((1.0 if ord(c) > 0x2E80 else 0.55) for c in text) * size_pt / 72.0


def _lh(size_pt, bold):
    """한 줄 높이 (인치). 글꼴마다 위·아래 여백이 달라(맑은 고딕 ≈1.3, Noto ≈1.45)
    글꼴에서 읽지 않고 1.25 배로 고정한다 - 미리보기(렌더 검수)와 같은 값."""
    return size_pt * 1.25 / 72.0


def _wrap(text, width, size, bold):
    """어절(띄어쓰기) 단위로 줄을 나눈다. 한 어절이 폭보다 길면 글자 단위로 자른다.
    돌려주는 것 : 줄마다의 폭 목록"""
    out = []
    for para in text.split('\n'):
        words = para.split(' ')
        cur = ''
        for wd in words:
            cand = wd if not cur else cur + ' ' + wd
            if _w(cand, size, bold) <= width + 1e-6 or not cur:
                if _w(cand, size, bold) > width + 1e-6 and not cur:
                    # 어절 하나가 폭보다 길다 -> 글자 단위
                    piece = ''
                    for ch in wd:
                        if _w(piece + ch, size, bold) > width + 1e-6 and piece:
                            out.append(_w(piece, size, bold))
                            piece = ch
                        else:
                            piece += ch
                    cur = piece
                else:
                    cur = cand
            else:
                out.append(_w(cur, size, bold))
                cur = wd
        out.append(_w(cur, size, bold))
    return out


def _runs_info(tf):
    """문단마다 (글자, 크기pt, 굵기, 정렬, 문단 뒤 간격pt)"""
    paras = []
    for p in tf.paragraphs:
        txt = ''.join(r.text for r in p.runs)
        size, bold = 11.0, False
        for r in p.runs:
            if r.font.size:
                size = r.font.size.pt
            if r.font.bold:
                bold = True
        sa = p.space_after.pt if p.space_after is not None else 0.0
        paras.append((txt, size, bold, str(p.alignment or ''), sa))
    return paras


def _text_extent(sh):
    """글상자 안 글자가 실제로 차지하는 자리 (x1, y1, x2, y2) 인치, 그리고 필요한 높이"""
    tf = sh.text_frame
    x, y = sh.left / EMU_IN, sh.top / EMU_IN
    w, h = sh.width / EMU_IN, sh.height / EMU_IN
    ml = (tf.margin_left if tf.margin_left is not None else Emu(91440)) / EMU_IN
    mr = (tf.margin_right if tf.margin_right is not None else Emu(91440)) / EMU_IN
    mt = (tf.margin_top if tf.margin_top is not None else Emu(45720)) / EMU_IN
    mb = (tf.margin_bottom if tf.margin_bottom is not None else Emu(45720)) / EMU_IN
    iw = max(0.05, w - ml - mr)
    total, widest, left_most, right_most = 0.0, 0.0, None, None
    paras = _runs_info(tf)
    for i, (txt, size, bold, al, sa) in enumerate(paras):
        widths = _wrap(txt, iw, size, bold) if tf.word_wrap is not False else [_w(txt, size, bold)]
        total += len(widths) * _lh(size, bold) + (sa / 72.0 if i < len(paras) - 1 else 0)
        for lw in widths:
            if not txt.strip():
                continue
            if 'CENTER' in al:
                lx = x + ml + (iw - lw) / 2
            elif 'RIGHT' in al:
                lx = x + ml + iw - lw
            else:
                lx = x + ml
            left_most = lx if left_most is None else min(left_most, lx)
            right_most = lx + lw if right_most is None else max(right_most, lx + lw)
    if left_most is None:
        return None, 0
    anchor = str(tf.vertical_anchor or '')
    ih = h - mt - mb
    if 'MIDDLE' in anchor:
        ty = y + mt + (ih - total) / 2
    elif 'BOTTOM' in anchor:
        ty = y + mt + ih - total
    else:
        ty = y + mt
    # 첫 줄 위쪽 여백(글꼴 위 공간)만큼 실제 글자는 조금 아래 - 겹침 판정은 가운데 80% 로 본다
    return (left_most, ty, right_most, ty + total), total + mt + mb


def _box(sh):
    return (sh.left / EMU_IN, sh.top / EMU_IN, (sh.left + sh.width) / EMU_IN, (sh.top + sh.height) / EMU_IN)


def _filled(sh):
    try:
        return sh.fill.type == 1
    except Exception:
        return False


def _inter(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1])


def _is_copied(slide):
    """회사 원본에서 복사해 온 장인가 (사진·그룹·자리표시자·차트가 있으면)"""
    for sh in slide.shapes:
        t = sh.shape_type
        if t in (MSO_SHAPE_TYPE.PICTURE, MSO_SHAPE_TYPE.GROUP, MSO_SHAPE_TYPE.PLACEHOLDER,
                 MSO_SHAPE_TYPE.CHART) or getattr(sh, 'is_placeholder', False):
            return True
    return False


def _table_bottom(sh):
    """표는 칸 글자가 줄바꿈되면 줄이 스스로 늘어난다 -> 실제 바닥"""
    tbl = sh.table
    y = sh.top / EMU_IN
    for r in tbl.rows:
        need = r.height / EMU_IN
        for ci, c in enumerate(r.cells):
            cw = tbl.columns[ci].width / EMU_IN
            ml = (c.margin_left or Emu(91440)) / EMU_IN
            mr = (c.margin_right or Emu(91440)) / EMU_IN
            mt = (c.margin_top or Emu(45720)) / EMU_IN
            mb = (c.margin_bottom or Emu(45720)) / EMU_IN
            hh = 0.0
            for txt, size, bold, al, sa in _runs_info(c.text_frame):
                hh += len(_wrap(txt, max(0.05, cw - ml - mr), size, bold)) * _lh(size, bold) + sa / 72.0
            need = max(need, hh + mt + mb)
        y += need
    return y


def check(path, skip_copied=True):
    """돌려주는 것 : ([(장, 종류, 설명)], 메모)"""
    prs = Presentation(path)
    sh_h = prs.slide_height / EMU_IN
    probs, skipped = [], 0
    for si, slide in enumerate(prs.slides, 1):
        if skip_copied and _is_copied(slide):
            skipped += 1
            continue
        texts, fills = [], []
        for sh in slide.shapes:
            if getattr(sh, 'has_table', False) and sh.has_table:
                bot = _table_bottom(sh)
                if bot > FOOTER_Y + 0.02:
                    probs.append((si, '표 밀림', '표가 바닥글까지 내려옴 (%.2fin 넘침)' % (bot - FOOTER_Y)))
                continue
            if _filled(sh):
                fills.append((sh.shape_id, _box(sh)))
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            ext, need = _text_extent(sh)
            if not ext:
                continue
            label = sh.text_frame.text.strip().replace('\n', ' ')[:18]
            if re.search(r'\[\s*\[|\]\s*\]', sh.text_frame.text):
                probs.append((si, '글자', '「%s」 괄호가 겹침' % label))
            over = need - sh.height / EMU_IN
            if over > 0.06:
                probs.append((si, '넘침', '「%s」 상자보다 %.2fin 김' % (label, over)))
            if ext[3] > sh_h + 0.01:
                probs.append((si, '장 밖', '「%s」 장 아래로 나감' % label))
            texts.append((sh.shape_id, ext, _box(sh), label))
        # 겹침 (글자끼리)
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                ox, oy = _inter(texts[i][1], texts[j][1])
                if ox > 0.03 and oy > 0.03:
                    probs.append((si, '겹침', '「%s」 / 「%s」' % (texts[i][3], texts[j][3])))
        # 붙음 (글자가 다른 색칠 도형에 걸치거나 바로 옆)
        for tid, ext, tbox, label in texts:
            for fid, fb in fills:
                if fid == tid:
                    continue
                if ext[0] >= fb[0] - 0.005 and ext[2] <= fb[2] + 0.005 and ext[1] >= fb[1] - 0.005 and ext[3] <= fb[3] + 0.005:
                    continue                                   # 그 도형 안에 든 글자
                ox, oy = _inter(ext, fb)
                # 얇은 선(구분선 0.01in)을 글자가 가로지르는 것도 잡는다 - 2026-09-27 목차 7줄에서 실제로 났다
                if oy > min(0.02, (fb[3] - fb[1]) * 0.5) and ox > -TOUCH:
                    probs.append((si, '붙음', '「%s」 가 다른 도형에 걸침/붙음' % label))
                    break
    note = '글꼴 %s 로 잼' % FONT_USED
    if skipped:
        note += ' · 회사 원본 장 %d장은 건너뜀' % skipped
    return probs, note


def report(path, quiet_ok=False):
    """화면에 한 줄(이상 없음) 또는 문제 목록을 찍는다. 문제 수를 돌려준다."""
    try:
        probs, note = check(path)
    except Exception as e:
        print('  점검 : 못 함 (%s)' % e)
        return -1
    if not probs:
        if not quiet_ok:
            print('  점검 : 이상 없음  (%s)' % note)
        return 0
    print('  점검 : 확인할 곳 %d군데  (%s)' % (len(probs), note))
    for si, kind, msg in probs:
        print('     %2d장 %-4s %s' % (si, kind, msg))
    return len(probs)


def run(paths=None):
    """★제안서_PPT.py 4번 : 최근 만든 제안서 폴더를 통째로 점검"""
    if not paths:
        try:
            from common import cfg
            root = os.path.join(cfg('out'), '제안서PPT')
        except Exception:
            root = ''
        days = sorted(d for d in glob.glob(os.path.join(glob.escape(root), '*')) if os.path.isdir(d)) if root else []
        if not days:
            print('점검할 제안서가 없습니다. 먼저 1번으로 만드십시오.')
            return
        paths = sorted(glob.glob(os.path.join(glob.escape(days[-1]), '*.pptx')))
        print('점검 폴더 : %s  (%d개)' % (days[-1], len(paths)))
    total = 0
    for p in paths:
        if os.path.basename(p).startswith('~$'):
            continue
        print(os.path.basename(p))
        n = report(p)
        total += max(0, n)
    print('')
    print('확인할 곳 합계 %d군데' % total if total else '전부 이상 없음')
    if total:
        print('→ 위 장 번호를 파워포인트에서 열어 보시고, 이상하면 그 목록을 클로드에게 보여 주십시오.')


if __name__ == '__main__':
    try:                                   # 슬라이드 글자에 cp949 에 없는 글자(–·✓)가 있어도 멈추지 않게
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    args = sys.argv[1:]
    ps = []
    for a in args:
        ps += sorted(glob.glob(os.path.join(glob.escape(a), '*.pptx'))) if os.path.isdir(a) else [a]
    run(ps or None)

# -*- coding: utf-8 -*-
"""deck_core - 회사 표준 서식으로 슬라이드를 그리는 부품. 메뉴 번호 없음.

54번(t54_deck)이 이것을 불러 쓴다. 단독으로 실행하지 않는다.

10번(t15 제안서 후보+초안)과 역할이 다르다.
  10번 = 회의록에서 "자료 달라"는 말을 찾아 무엇을 만들지 고르는 것 (txt 초안)
  26번 = 고른 것을 실제 제출 가능한 pptx 로 뽑는 것

내용은 이미 json 안에 다 들어 있으므로 이 도구는 인터넷도 AI 도 쓰지 않는다. 토큰 0.
현장명을 물어 {{현장}} 자리에 넣으므로, 같은 내용으로 범용본과 현장 맞춤본 둘 다 나온다.
"""
import os, io, json, datetime
from common import *

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -- 회사 표준 디자인 (km-proposal 빌더와 같은 값. 바꾸지 말 것) --
NAVY = RGBColor(0x1F, 0x38, 0x64)
NAVY_D = RGBColor(0x17, 0x28, 0x4A)
BLUE = RGBColor(0x2E, 0x74, 0xB5)
RED = RGBColor(0xC0, 0x00, 0x00)
GREEN_BG = RGBColor(0xE2, 0xEF, 0xD9)
GREEN_TX = RGBColor(0x37, 0x56, 0x23)
GRAY_BG = RGBColor(0xF2, 0xF2, 0xF2)
GRAY_TX = RGBColor(0x59, 0x59, 0x59)
LINE = RGBColor(0xD9, 0xD9, 0xD9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BODY = RGBColor(0x33, 0x33, 0x33)
SKY = RGBColor(0xDE, 0xEA, 0xF6)
FONT = '맑은 고딕'

ML, MW, MTOP = 0.5, 9.0, 0.45
SLIDE_W, SLIDE_H = 10.0, 5.625

SPECS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '제안서_내용')


# ---------- 기본 그리기 ----------
def _tb(slide, x, y, w, h, text, size=11, color=BODY, bold=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=2):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = str(text).split('\n')
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = ln
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return box


def _rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, lw=1.0):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    if s.has_text_frame:
        s.text_frame.text = ''
    return s


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _footer(slide, note):
    _tb(slide, ML, 5.22, MW, 0.25, note or '한국마이크로닉(주)', size=8, color=GRAY_TX)


def _page_title(slide, title_text, eyebrow=None, pill=None):
    y = MTOP
    if eyebrow:
        _tb(slide, ML, y, 6.0, 0.22, eyebrow, size=9, color=GRAY_TX)
        y += 0.24
    _tb(slide, ML, y, 7.0, 0.42, title_text, size=19, color=NAVY, bold=True)
    if pill:
        w = min(3.2, 0.14 * len(pill) + 0.5)
        _rect(slide, ML + MW - w, y + 0.04, w, 0.3, fill=SKY, line=None,
              shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        _tb(slide, ML + MW - w, y + 0.08, w, 0.24, pill, size=9, color=NAVY,
            bold=True, align=PP_ALIGN.CENTER)
    y += 0.5
    _rect(slide, ML, y, MW, 0.02, fill=NAVY)
    return y + 0.18


# ---------- 슬라이드 종류 ----------
def s_cover(slide, d):
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=NAVY)
    _rect(slide, 0, 0, 0.18, SLIDE_H, fill=BLUE)
    _tb(slide, 1.0, 1.55, 8.2, 0.3, d.get('eyebrow', ''), size=11, color=SKY, bold=True)
    _tb(slide, 1.0, 1.95, 8.2, 1.1, d.get('title', ''), size=30, color=WHITE, bold=True, space=4)
    if d.get('subtitle'):
        _tb(slide, 1.0, 3.15, 8.2, 0.5, d['subtitle'], size=14, color=SKY)
    _rect(slide, 1.0, 3.85, 1.4, 0.03, fill=BLUE)
    _tb(slide, 1.0, 4.1, 8.2, 0.4, d.get('meta', ''), size=10.5, color=LINE)


def s_conclusion(slide, d):
    y = _page_title(slide, d.get('title', '결론'), d.get('eyebrow'), d.get('pill'))
    if d.get('headline'):
        h = 0.62 if len(d['headline']) < 60 else 0.85
        _rect(slide, ML, y, MW, h, fill=GREEN_BG)
        _tb(slide, ML + 0.18, y + 0.1, MW - 0.36, h - 0.2, d['headline'], size=12.5,
            color=GREEN_TX, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        y += h + 0.22
    cards = d.get('cards', [])
    if cards:
        n = len(cards)
        gap = 0.18
        cw = (MW - gap * (n - 1)) / n
        ch = 1.55
        for i, c in enumerate(cards):
            x = ML + i * (cw + gap)
            _rect(slide, x, y, cw, ch, fill=GRAY_BG, line=LINE)
            _rect(slide, x, y, cw, 0.05, fill=BLUE)
            _tb(slide, x + 0.14, y + 0.16, cw - 0.28, 0.24, c.get('label', ''), size=9.5,
                color=GRAY_TX, bold=True)
            _tb(slide, x + 0.14, y + 0.44, cw - 0.28, 0.42, c.get('big', ''), size=14,
                color=NAVY, bold=True)
            _tb(slide, x + 0.14, y + 0.92, cw - 0.28, ch - 1.02, c.get('body', ''), size=9.5,
                color=BODY)
        y += ch + 0.2
    if d.get('banner'):
        _rect(slide, ML, y, MW, 0.52, fill=None, line=RED, lw=1.25)
        _tb(slide, ML + 0.16, y + 0.1, MW - 0.32, 0.34, d['banner'], size=10,
            color=RED, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def s_table(slide, d):
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    headers = d.get('headers', [])
    rows = d.get('rows', [])
    colw = d.get('colW') or [MW / max(1, len(headers))] * len(headers)
    note_h = 0.34 if d.get('note') else 0.0
    avail = 5.05 - y - note_h
    nrow = len(rows) + 1
    rh = max(0.24, min(0.62, avail / nrow))
    shape = slide.shapes.add_table(nrow, len(headers), Inches(ML), Inches(y),
                                   Inches(sum(colw)), Inches(rh * nrow))
    tbl = shape.table
    tbl.first_row = True
    for j, w in enumerate(colw):
        tbl.columns[j].width = Inches(w)
    for i in range(nrow):
        tbl.rows[i].height = Inches(rh)
    data = [headers] + rows
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (
                WHITE if i % 2 else RGBColor(0xF7, 0xF9, 0xFC))
            tf = cell.text_frame
            tf.word_wrap = True
            for k, ln in enumerate(str(val).split('\n')):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                p.space_after = Pt(0)
                r = p.add_run()
                r.text = ln
                r.font.name = FONT
                r.font.size = Pt(9 if i == 0 else 8.5)
                r.font.bold = (i == 0)
                r.font.color.rgb = WHITE if i == 0 else BODY
    if d.get('note'):
        _tb(slide, ML, y + rh * nrow + 0.08, MW, 0.3, '※ ' + d['note'], size=8.5, color=GRAY_TX)


def s_items(slide, d):
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    if d.get('lead'):
        _tb(slide, ML, y, MW, 0.3, d['lead'], size=10.5, color=GRAY_TX)
        y += 0.36
    items = d.get('items', [])
    box = d.get('box')
    box_h = 0.0
    if box:
        box_h = 0.42 + 0.26 * len(box.get('lines', []))
    avail = 5.05 - y - (box_h + 0.18 if box else 0)
    ih = min(0.62, max(0.34, avail / max(1, len(items))))
    for i, it in enumerate(items):
        yy = y + i * ih
        _rect(slide, ML, yy + 0.03, 0.26, 0.26, fill=BLUE, shape=MSO_SHAPE.OVAL)
        _tb(slide, ML, yy + 0.06, 0.26, 0.2, str(i + 1), size=9.5, color=WHITE,
            bold=True, align=PP_ALIGN.CENTER)
        _tb(slide, ML + 0.38, yy + 0.02, MW - 2.5, 0.28, it.get('text', ''), size=11,
            color=BODY, bold=True)
        if it.get('desc'):
            _tb(slide, ML + MW - 2.0, yy + 0.04, 2.0, 0.26, '[ %s ]' % it['desc'],
                size=9.5, color=BLUE, bold=True, align=PP_ALIGN.RIGHT)
    if box:
        by = 5.05 - box_h
        _rect(slide, ML, by, MW, box_h, fill=GRAY_BG, line=LINE)
        _tb(slide, ML + 0.16, by + 0.08, MW - 0.32, 0.24,
            box.get('title', '확인 · 협의 사항'), size=10, color=NAVY, bold=True)
        for i, ln in enumerate(box.get('lines', [])):
            _tb(slide, ML + 0.28, by + 0.36 + i * 0.26, MW - 0.5, 0.24, '· ' + ln,
                size=9.5, color=BODY)


def s_diagram(slide, d):
    """구성도를 그림이 아니라 도형으로 그린다 - 파워포인트에서 직접 고칠 수 있다."""
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    if d.get('lead'):
        _tb(slide, ML, y, MW, 0.3, d['lead'], size=10, color=GRAY_TX)
        y += 0.34
    STYLE = {'main': (NAVY, WHITE), 'device': (SKY, NAVY), 'sub': (GRAY_BG, GRAY_TX)}
    canvas = d.get('canvas', [10.0, 3.0])
    steps = d.get('steps', [])
    ch = (1.55 if steps else 2.9)
    sx, sy = MW / canvas[0], ch / canvas[1]
    pos = {}
    for b in d.get('boxes', []):
        x = ML + b['x'] * sx
        yy = y + b['y'] * sy
        w, h = b['w'] * sx, b['h'] * sy
        pos[b['id']] = (x, yy, w, h)
        fill, tx = STYLE.get(b.get('style', 'sub'), STYLE['sub'])
        _rect(slide, x, yy, w, h, fill=fill, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        body = b.get('title', '')
        for ln in b.get('lines', []):
            body += '\n' + ln
        _tb(slide, x + 0.06, yy + 0.05, w - 0.12, h - 0.1, body, size=b.get('fs', 9),
            color=tx, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
    for lk in d.get('links', []):
        a, b = pos.get(lk['from']), pos.get(lk['to'])
        if not a or not b:
            continue
        col = BLUE if lk.get('style', 'comm') == 'comm' else (
            RED if lk['style'] == 'power' else GRAY_TX)
        if abs(a[1] - b[1]) < 0.05:                       # 가로
            x1 = min(a[0] + a[2], b[0] + b[2]) if a[0] < b[0] else b[0] + b[2]
            x1 = (a[0] + a[2]) if a[0] < b[0] else (b[0] + b[2])
            x2 = b[0] if a[0] < b[0] else a[0]
            yy = a[1] + a[3] / 2
            _rect(slide, x1, yy - 0.01, max(0.02, x2 - x1), 0.025, fill=col)
            if lk.get('label'):
                _tb(slide, x1, yy - 0.28, max(0.5, x2 - x1), 0.24, lk['label'], size=8,
                    color=col, bold=True, align=PP_ALIGN.CENTER)
        else:                                             # 세로
            xx = a[0] + a[2] / 2
            y1 = (a[1] + a[3]) if a[1] < b[1] else (b[1] + b[3])
            y2 = b[1] if a[1] < b[1] else a[1]
            _rect(slide, xx - 0.01, y1, 0.025, max(0.02, y2 - y1), fill=col)
            if lk.get('label'):
                _tb(slide, xx + 0.08, y1, 2.4, 0.22, lk['label'], size=8, color=col, bold=True)
    if steps:
        by = 5.05 - 1.15
        n = len(steps)
        gap = 0.14
        cw = (MW - gap * (n - 1)) / n
        for i, st in enumerate(steps):
            x = ML + i * (cw + gap)
            _rect(slide, x, by, cw, 1.1, fill=GRAY_BG, line=LINE)
            _rect(slide, x + 0.1, by + 0.1, 0.24, 0.24, fill=BLUE, shape=MSO_SHAPE.OVAL)
            _tb(slide, x + 0.1, by + 0.13, 0.24, 0.2, st.get('num', str(i + 1)), size=9,
                color=WHITE, bold=True, align=PP_ALIGN.CENTER)
            _tb(slide, x + 0.42, by + 0.12, cw - 0.52, 0.24, st.get('text', ''), size=9.5,
                color=NAVY, bold=True)
            _tb(slide, x + 0.1, by + 0.42, cw - 0.2, 0.22, '[ %s ]' % st.get('who', ''),
                size=8.5, color=BLUE, bold=True)
            _tb(slide, x + 0.1, by + 0.66, cw - 0.2, 0.4, st.get('desc', ''), size=8, color=BODY)


def s_split(slide, d):
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    cw = (MW - 0.24) / 2
    for i, side in enumerate(('left', 'right')):
        blk = d.get(side, {})
        x = ML + i * (cw + 0.24)
        h = 5.0 - y
        _rect(slide, x, y, cw, h, fill=(GRAY_BG if i == 0 else SKY), line=LINE)
        _tb(slide, x + 0.16, y + 0.14, cw - 0.32, 0.3, blk.get('label', ''), size=11.5,
            color=(GRAY_TX if i == 0 else NAVY), bold=True)
        for j, ln in enumerate(blk.get('lines', [])):
            _tb(slide, x + 0.28, y + 0.56 + j * 0.34, cw - 0.5, 0.3, '· ' + ln, size=10,
                color=BODY)


def s_request(slide, d):
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=NAVY)
    _rect(slide, 0, 0, 0.18, SLIDE_H, fill=BLUE)
    _tb(slide, 0.9, 0.55, 8.4, 0.45, d.get('title', '요청드리는 사항'), size=22,
        color=WHITE, bold=True)
    if d.get('lead'):
        _tb(slide, 0.9, 1.08, 8.4, 0.3, d['lead'], size=11, color=SKY)
    y = 1.6
    for i, it in enumerate(d.get('items', [])):
        _rect(slide, 0.9, y + 0.02, 0.26, 0.26, fill=BLUE, shape=MSO_SHAPE.OVAL)
        _tb(slide, 0.9, y + 0.05, 0.26, 0.2, str(i + 1), size=9.5, color=WHITE,
            bold=True, align=PP_ALIGN.CENTER)
        _tb(slide, 1.3, y, 8.0, 0.28, it.get('text', ''), size=12, color=WHITE, bold=True)
        if it.get('desc'):
            _tb(slide, 1.3, y + 0.3, 8.0, 0.26, it['desc'], size=9.5, color=LINE)
        y += 0.72
    if d.get('contact'):
        _rect(slide, 0.9, 4.75, 8.4, 0.02, fill=BLUE)
        _tb(slide, 0.9, 4.9, 8.4, 0.3, d['contact'], size=10, color=SKY)


KIND = {'cover': s_cover, 'conclusion': s_conclusion, 'table': s_table, 'items': s_items,
        'diagram': s_diagram, 'split': s_split, 'request': s_request}


# ---------- 조립 ----------
def fill(obj, mapping):
    if isinstance(obj, str):
        for k, v in mapping.items():
            obj = obj.replace(k, v)
        return obj
    if isinstance(obj, list):
        return [fill(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return dict((k, fill(v, mapping)) for k, v in obj.items())
    return obj


def build(spec, out_path):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    foot = spec.get('footer', '한국마이크로닉(주)')
    for i, sl in enumerate(spec.get('slides', [])):
        fn = KIND.get(sl.get('type'))
        if not fn:
            raise ValueError('모르는 슬라이드 종류: %s (%d번째 장)' % (sl.get('type'), i + 1))
        slide = _blank(prs)
        fn(slide, sl)
        if sl.get('type') not in ('cover', 'request'):
            _footer(slide, foot)
    prs.save(out_path)
    return len(spec.get('slides', []))


def load_specs():
    out = []
    if not os.path.isdir(SPECS):
        return out
    for name in sorted(os.listdir(SPECS)):
        if not name.lower().endswith('.json'):
            continue
        p = os.path.join(SPECS, name)
        try:
            d = json.loads(io.open(p, encoding='utf-8').read())
            out.append((p, d))
        except Exception as e:
            print('  건너뜀 : %s (%s)' % (name, e))
    return out


def run():
    title('26. 제안서 PPT (미리 써 둔 내용을 회사 서식으로)')
    specs = load_specs()
    if not specs:
        print('제안서_내용 폴더에 json 이 없습니다.')
        print('위치 : %s' % SPECS)
        return
    print('')
    print('만들 수 있는 제안서 %s건' % won(len(specs)))
    cur = ''
    for i, (p, d) in enumerate(specs, 1):
        g = d.get('요일', '')
        if g != cur:
            cur = g
            print('')
            print(' -- %s --' % (g or '기타'))
        print(' %2d. %s  (%d장)' % (i, d.get('title', '?'), len(d.get('slides', []))))
    print('')
    sel = ask('번호 (엔터=전부 만들기) > ')
    pick = [specs[int(sel) - 1]] if sel.isdigit() and 1 <= int(sel) <= len(specs) else specs
    site = ask('현장명 (엔터 = 현장명 없는 범용 표준본) > ').strip()
    od = outdir('제안서PPT')
    mapping = {'{{현장}}': site if site else '귀사',
               '{{현장_제목}}': (site + ' ') if site else '',
               '{{날짜}}': today().strftime('%Y. %m. %d')}
    print('')
    made = 0
    for p, d in pick:
        d2 = fill(d, mapping)
        base = '%s_%s_%s_r1.pptx' % (safe_name(site or '표준'),
                                     safe_name(d2.get('파일명', d2.get('title', '제안서'))[:30]),
                                     ymd6())
        f = os.path.join(od, base)
        try:
            n = build(d2, f)
            print('만듦 : %s  (%d장)' % (f, n))
            made += 1
        except Exception as e:
            print('실패 : %s  (%s)' % (d2.get('title'), e))
    print('')
    print('%s건 완료. 대외 제출 전 반드시 한 번 열어 확인하십시오.' % won(made))
    log('제안서PPT', '%d건 %s' % (made, site or '범용'))


if __name__ == '__main__':
    run(); pause()

# -*- coding: utf-8 -*-
"""54. 제안서 PPT - 회사 제안서의 고정 장을 그대로 가져오고, 현장 내용만 새로 만들어 붙인다.

왜 이렇게 하는가
  청담PJ 제안서(260715, 26장)를 뜯어보니 20장이 회사개요·핵심경쟁력·제품·납품실적·A/S 였다.
  이 20장은 현장이 바뀌어도 그대로다. 다시 그리면 사진·마감이 원본보다 나빠질 뿐이다.
  그래서 고정 장은 원본 pptx 에서 통째로 복사하고, 현장별로 바뀌는 장만 파이썬이 만든다.

쓰는 법
  3_공통사용\\원틀\\제안서\\ 안에 회사 제안서 pptx 를 넣어두고 이 도구를 누른다.
  인터넷도 AI 도 쓰지 않는다. 사용료 0 원.
"""
import os, io, json, copy, datetime
from common import *

from pptx import Presentation
from pptx.util import Inches

import deck_core as deck          # 슬라이드 그리는 부분. 메뉴 번호를 갖지 않는 부품이다

SPECS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '제안서_내용')
SKIP_REL = ('slideLayout', 'notesSlide', 'slideMaster')

# 고정 장 판별 키워드 (이 글자가 그 장에 있으면 고정 장으로 본다)
FIXED_KEYS = ('목차', '회사개요', '회사소개', '설립', '핵심경쟁력', '경쟁력',
              '납품실적', '실적', 'A/S', 'AS ', '사후관리', '유지보수', '무상보증',
              '제품라인업', '시리즈', '원스톱', 'Opera', 'PMS 연동', '별첨')


# ---------- 슬라이드 복사 ----------
def copy_slide(src_slide, dst_prs, layout_idx=6):
    dst = dst_prs.slides.add_slide(dst_prs.slide_layouts[layout_idx])
    for ph in list(dst.shapes):
        ph._element.getparent().remove(ph._element)
    for shp in src_slide.shapes:
        dst.shapes._spTree.append(copy.deepcopy(shp._element))
    for rel in src_slide.part.rels.values():
        if any(k in rel.reltype for k in SKIP_REL):
            continue
        if rel.is_external:
            new_rId = dst.part.rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
        else:
            new_rId = dst.part.relate_to(rel.target_part, rel.reltype)
        if new_rId != rel.rId:
            for el in dst.shapes._spTree.iter():
                for k, v in list(el.attrib.items()):
                    if v == rel.rId and (k.endswith('}embed') or k.endswith('}id')
                                         or k.endswith('}link')):
                        el.attrib[k] = new_rId
    return dst


def slide_text(s, limit=60):
    out = []
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            out.append(sh.text_frame.text.strip().replace('\n', ' '))
    t = ' / '.join(out)
    return t[:limit] if t else '(글자 없음)'


def scan_source(path):
    """원본 pptx 의 장별 요약과 고정 장 후보를 낸다."""
    prs = Presentation(path)
    rows = []
    for i, s in enumerate(prs.slides, 1):
        t = slide_text(s, 200)
        pics = sum(1 for sh in s.shapes if sh.shape_type == 13)
        fixed = any(k in t for k in FIXED_KEYS)
        rows.append({'no': i, 'text': t, 'pics': pics, 'fixed': fixed})
    return prs, rows


def find_sources():
    """원틀\\제안서 폴더에서 pptx 를 찾는다. 없으면 _원틀 전체에서 '제안' 들어간 것."""
    cands = []
    base = cfg('tpl') if 'tpl' in (cfg('tpl') or '') else None
    roots = []
    for key in ('tpl', 'out', 'plaud'):
        try:
            v = cfg(key)
        except Exception:
            v = None
        if v:
            roots.append(v)
    roots.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
    seen = set()
    for r in roots:
        if not r or not os.path.isdir(r):
            continue
        for dirpath, dirs, files in os.walk(r):
            if '제안' not in dirpath and '원틀' not in dirpath:
                continue
            for f in files:
                if f.lower().endswith('.pptx') and not f.startswith('~$'):
                    p = os.path.join(dirpath, f)
                    if p not in seen:
                        seen.add(p)
                        cands.append(p)
    return sorted(cands)


# ---------- 27번(도면수량) 결과를 그대로 제안서에 꽂는다 ----------
def find_qty_csv(site):
    """_도구결과\\도면수량\\ 에서 그 현장의 가장 최근 도면수량 csv 를 찾는다."""
    import glob
    try:
        root = os.path.join(cfg('out'), '도면수량')
    except Exception:
        return None
    if not os.path.isdir(root):
        return None
    pat = os.path.join(root, '*', '*도면수량*.csv')
    cands = [p for p in glob.glob(pat)
             if (not site) or safe_name(site) in os.path.basename(p)]
    if not cands:
        return None
    cands.sort(key=lambda p: os.path.getmtime(p))
    return cands[-1]


def read_qty(path):
    """품목 / 채택수량 / 채택근거 만 뽑는다. 수량 0 이거나 비어 있으면 버린다."""
    import csv
    rows = []
    site = ''
    for enc in ('utf-8-sig', 'cp949', 'utf-8'):
        try:
            with io.open(path, encoding=enc) as fp:
                for r in csv.reader(fp):
                    if not r:
                        continue
                    if r[0] == '[현장]' and len(r) > 1:
                        site = r[1]
                    if r[0] in ('품목', '[현장]', '[읽은 파일]', '[규칙 대조]', ''):
                        continue
                    qty = (r[3] if len(r) > 3 else '').strip()
                    if not qty or qty in ('0', '-'):
                        continue
                    rows.append([r[0].strip(), qty, (r[4] if len(r) > 4 else '').strip()])
            break
        except Exception:
            continue
    return site, rows


def qty_slides(site, rows, src_name=''):
    """도면에서 읽은 물량으로 「그 현장 이야기」 2장을 만든다."""
    head = ['품목', '수량', '근거']
    body = [[a, b, c or '도면 판독'] for a, b, c in rows[:9]]
    t = {'type': 'table', 'title': '%s 물량 (도면에서 읽은 값)' % (site or '본 현장'),
         'eyebrow': '그 현장 이야기', 'pill': '도면 기준',
         'headers': head, 'colW': [3.6, 1.8, 3.6], 'rows': body,
         'note': '이 표는 도면을 기계로 읽어 센 값입니다. 발주처 수량표와 대조해 확정합니다.'
                 + (('  (읽은 도면: %s)' % src_name) if src_name else '')}
    it = {'type': 'items', 'title': '%s 적용 범위' % (site or '본 현장'),
          'eyebrow': '그 현장 이야기',
          'lead': '위 물량을 기준으로 당사가 공급·시공하는 범위입니다.',
          'items': [
              {'text': 'CB 외함 제작 · 현장 납품', 'desc': '선납품'},
              {'text': '제어 분전함(속판) 설치 · 약전 결선', 'desc': '객실관리'},
              {'text': '객실 기구물 제작 · 설치', 'desc': '벽지·페인트 완료 후'},
              {'text': '시운전 및 운영자 인계 교육', 'desc': '전원 공급 후'}],
          'box': {'title': '확인 · 협의 사항', 'lines': [
              '조명 스위치 구수는 전등 설계가 나와야 확정됩니다. 도면에는 L 로만 표기합니다.',
              '도면에서 읽지 못한 기호는 별도 목록으로 정리해 두었습니다. 함께 확인 부탁드립니다.',
              '강전 결선과 외함 취부는 전기공사 범위입니다.']}}
    return [t, it]


# ---------- 조립 ----------
def build_merged(spec, src_path, fixed_nos, out_path, mapping):
    prs = Presentation()
    prs.slide_width = Inches(deck.SLIDE_W)
    prs.slide_height = Inches(deck.SLIDE_H)
    foot = spec.get('footer', '한국마이크로닉(주)')
    made = 0
    for sl in spec.get('slides', []):
        fn = deck.KIND.get(sl.get('type'))
        if not fn:
            continue
        s = prs.slides.add_slide(prs.slide_layouts[6])
        fn(s, sl)
        if sl.get('type') not in ('cover', 'request'):
            deck._footer(s, foot)
        made += 1
    copied = 0
    if src_path and fixed_nos:
        src = Presentation(src_path)
        n = len(src.slides)
        for no in fixed_nos:
            if 1 <= no <= n:
                copy_slide(src.slides[no - 1], prs)
                copied += 1
    prs.save(out_path)
    return made, copied


def run():
    title('39. 제안서 PPT (회사 원본 + 현장 내용 합본)')
    # 1) 원본 고르기
    srcs = find_sources()
    src_path = None
    fixed_nos = []
    if srcs:
        print('')
        print('찾은 회사 제안서 %s개' % won(len(srcs)))
        for i, p in enumerate(srcs, 1):
            print(' %2d. %s' % (i, os.path.basename(p)))
        s = ask('번호 (엔터 = 안 붙이고 현장 내용만) > ').strip()
        if s.isdigit() and 1 <= int(s) <= len(srcs):
            src_path = srcs[int(s) - 1]
    else:
        print('')
        print('회사 제안서 pptx 를 못 찾았습니다.')
        print('3_공통사용\\원틀\\제안서\\ 안에 넣어두시면 다음부터 자동으로 찾습니다.')
        print('지금은 현장 내용만 만듭니다.')

    if src_path:
        prs, rows = scan_source(src_path)
        print('')
        print('%s : 모두 %s장' % (os.path.basename(src_path), won(len(rows))))
        auto = [r['no'] for r in rows if r['fixed']]
        for r in rows:
            print(' %s %2d. %s%s' % ('[고정]' if r['fixed'] else '      ',
                                     r['no'],
                                     ('사진%d ' % r['pics']) if r['pics'] else '',
                                     r['text'][:58]))
        print('')
        print('[고정] 으로 잡은 장 : %s' % (','.join(str(x) for x in auto) if auto else '없음'))
        s = ask('그대로 쓰려면 엔터, 바꾸려면 번호를 쉼표로 (예 2,3,4,13-20) > ').strip()
        fixed_nos = parse_nos(s) if s else auto

    # 2) 현장 내용 고르기
    specs = []
    if os.path.isdir(SPECS):
        for name in sorted(os.listdir(SPECS)):
            if name.lower().endswith('.json'):
                try:
                    specs.append((os.path.join(SPECS, name),
                                  json.loads(io.open(os.path.join(SPECS, name),
                                                     encoding='utf-8').read())))
                except Exception as e:
                    print('  건너뜀 : %s (%s)' % (name, e))
    if not specs:
        print('제안서_내용 폴더에 json 이 없습니다.')
        return
    print('')
    print('현장 내용 %s건' % won(len(specs)))
    for i, (p, d) in enumerate(specs, 1):
        print(' %2d. %s  (%d장)' % (i, d.get('title', '?'), len(d.get('slides', []))))
    sel = ask('\n번호 (엔터 = 전부) > ')
    pick = [specs[int(sel) - 1]] if sel.isdigit() and 1 <= int(sel) <= len(specs) else specs
    site = ask('현장명 (엔터 = 현장명 없는 범용 표준본) > ').strip()

    # 27번 도면수량 결과가 있으면 「그 현장 이야기」 2장을 자동으로 끼운다
    qrows = []
    qcsv = find_qty_csv(site)
    if qcsv:
        qsite, qrows = read_qty(qcsv)
        if qrows:
            print('')
            print('도면수량 결과를 찾았습니다 : %s' % os.path.basename(qcsv))
            print('  품목 %s개를 제안서에 그대로 넣습니다.' % won(len(qrows)))
            for a, b, c in qrows[:6]:
                print('   - %s : %s (%s)' % (a, b, c or '도면 판독'))
        else:
            print('')
            print('도면수량 파일은 있으나 채택수량이 비어 있습니다. 물량 장은 넣지 않습니다.')
    elif site:
        print('')
        print('27번 도면수량 결과가 없습니다. 도면을 넣고 27번을 먼저 누르시면')
        print('그 현장 물량이 제안서에 자동으로 들어갑니다.')

    od = outdir('제안서PPT')
    mapping = {'{{현장}}': site if site else '귀사',
               '{{현장_제목}}': (site + ' ') if site else '',
               '{{날짜}}': today().strftime('%Y. %m. %d')}
    print('')
    for p, d in pick:
        d2 = deck.fill(d, mapping)
        if qrows:
            sl = d2.setdefault('slides', [])
            at = 1 if sl and sl[0].get('type') == 'cover' else 0
            for k, extra in enumerate(qty_slides(site, qrows, os.path.basename(qcsv))):
                sl.insert(at + k, extra)
        base = '%s_%s_%s_r1.pptx' % (safe_name(site or '표준'),
                                     safe_name(d2.get('파일명', d2.get('title', '제안서'))[:30]),
                                     ymd6())
        f = os.path.join(od, base)
        try:
            made, copied = build_merged(d2, src_path, fixed_nos, f, mapping)
            print('만듦 : %s  (새로 %d장 + 원본에서 %d장 = %d장)'
                  % (f, made, copied, made + copied))
        except Exception as e:
            print('실패 : %s  (%s)' % (d2.get('title'), e))
    print('')
    print('대외 제출 전 반드시 한 번 열어 확인하십시오.')
    log('제안서PPT', '%d건 %s' % (len(pick), site or '범용'))


def parse_nos(s):
    out = []
    for part in s.replace(' ', '').split(','):
        if not part:
            continue
        if '-' in part:
            a, b = part.split('-')[:2]
            if a.isdigit() and b.isdigit():
                out.extend(range(int(a), int(b) + 1))
        elif part.isdigit():
            out.append(int(part))
    return out


if __name__ == '__main__':
    run(); pause()

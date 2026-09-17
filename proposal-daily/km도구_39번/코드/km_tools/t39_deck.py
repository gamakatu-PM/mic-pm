# -*- coding: utf-8 -*-
"""39. 제안서 PPT - 회사 제안서의 고정 장을 그대로 가져오고, 현장 내용만 새로 만들어 붙인다.

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

import t26_deck as deck          # 슬라이드 그리는 부분은 26번 것을 그대로 쓴다

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

    od = outdir('제안서PPT')
    mapping = {'{{현장}}': site if site else '귀사',
               '{{현장_제목}}': (site + ' ') if site else '',
               '{{날짜}}': today().strftime('%Y. %m. %d')}
    print('')
    for p, d in pick:
        d2 = deck.fill(d, mapping)
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

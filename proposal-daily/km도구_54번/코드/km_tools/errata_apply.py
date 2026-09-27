# -*- coding: utf-8 -*-
# 54판 v7 2026-09-27  (★제안서_PPT.py 가 이 줄의 v숫자로 새 판인지 가린다)
"""errata_apply - 회사 제안서 pptx 의 5성급 점유율을 「해외스펙 제외 80% 이상」 으로 통일한다. 토큰 0.

왜 만들었나
  청담PJ 제안서(260715)에 5성급 점유율이 70% · 70%+ · 75% · 80% 로 섞여 있었다.
  프로님이 2026-09-17 「해외스펙 제외 80% 이상」 으로 확정하셨다.
  pptx 원본이 들어오는 순간 손 없이 고치려고 만들었다.

지키는 것
  ★ 원본을 덮어쓰지 않는다. 같은 폴더에 「_점유율80」 을 붙인 새 파일로 낸다.
  ★ 점유율 문장만 건드린다. 「점유」 「5성급」 이 있는 문단 안의 70% · 75% 만 80% 로 바꾼다.
     다른 숫자(6시간, 40년, 52개 호텔 …)는 절대 안 건드린다.
  ★ 바꾼 곳을 하나도 빠짐없이 화면과 _점유율80_바꾼곳.csv 에 남긴다.

쓰는 법
  python errata_apply.py "원본.pptx"
  또는 인수 없이 누르면 원틀\\제안서 폴더의 pptx 를 골라 준다.
"""
import os, re, sys, io, csv

from pptx import Presentation

PCT = re.compile(r'7[05]\s*%')          # 70% · 75% (70%+ 도 여기서 걸린다)
NEED = ('점유', '5성급', '5 성급', '10곳')  # 이 말이 든 문단만 본다
SCOPE = '(해외스펙 제외)'


def _paras(prs):
    for si, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            frames = []
            if sh.has_text_frame:
                frames.append(sh.text_frame)
            if getattr(sh, 'has_table', False) and sh.has_table:
                for row in sh.table.rows:
                    for c in row.cells:
                        frames.append(c.text_frame)
            for tf in frames:
                for p in tf.paragraphs:
                    yield si, p


ALONE = re.compile(r'^\s*7[05]\s*%\s*\+?\s*$')          # 「70%+」 처럼 숫자만 있는 큰 글씨
WITH_TAIL = re.compile(r'7[05](\s*)%((?:\s*이상)?(?:\s*(?:점유|설치))?)')


def fix(src, dst=None):
    prs = Presentation(src)
    log = []
    # 장마다 「점유」 가 있는지 먼저 본다 - 숫자만 있는 큰 글씨는 이걸로 판단한다
    share_slides = set()
    for si, p in _paras(prs):
        if '점유' in ''.join(r.text for r in p.runs):
            share_slides.add(si)
    for si, p in _paras(prs):
        text = ''.join(r.text for r in p.runs)
        if not text:
            continue
        # ① 숫자만 있는 큰 글씨 (「70%+」) - 같은 장에 「점유」 가 있을 때만
        if ALONE.match(text) and si in share_slides:
            for r in p.runs:
                if PCT.search(r.text):
                    before = r.text
                    r.text = PCT.sub('80%', r.text)
                    log.append([si, before, r.text])
            continue
        # ② 점유율 설명 글귀 (숫자 없음) - 기준을 붙인다
        if '점유율' in text and not PCT.search(text) and '해외' not in text and p.runs:
            last = p.runs[-1]
            before = text
            last.text = last.text.rstrip() + ' ' + SCOPE
            log.append([si, before, ''.join(r.text for r in p.runs)])
            continue
        # ③ 점유율 문장 - 숫자를 80 으로, 기준이 없으면 숫자 바로 뒤에 붙인다
        if not any(k in text for k in NEED) or not PCT.search(text):
            continue
        has_scope = '해외' in text
        for r in p.runs:
            if PCT.search(r.text):
                before = r.text
                if has_scope:
                    r.text = PCT.sub('80%', r.text)
                else:
                    r.text = WITH_TAIL.sub(lambda m: '80' + m.group(1) + '%' + m.group(2) + ' ' + SCOPE,
                                           r.text, count=1)
                    r.text = PCT.sub('80%', r.text)
                    has_scope = True
                log.append([si, before, r.text])
    if dst is None:
        base, ext = os.path.splitext(src)
        dst = base + '_점유율80' + ext
    prs.save(dst)
    with io.open(os.path.splitext(dst)[0] + '_바꾼곳.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['장', '전', '후'])
        w.writerows(log)
    return dst, log


def run(path=None):
    if not path:
        try:
            from t54_deck import find_sources
            srcs = [s for s in find_sources() if '_점유율80' not in s]
        except Exception:
            srcs = []
        if not srcs:
            print('고칠 pptx 를 못 찾았습니다. 3_공통사용\\원틀\\제안서\\ 에 넣어 주십시오.')
            return
        for i, s in enumerate(srcs, 1):
            print(' %2d. %s' % (i, os.path.basename(s)))
        sel = input('번호 > ').strip()
        if not sel.isdigit() or not (1 <= int(sel) <= len(srcs)):
            return
        path = srcs[int(sel) - 1]
    dst, log = fix(path)
    print('')
    print('바꾼 곳 %d군데' % len(log))
    for si, a, b in log:
        print('  %2d장 : %s  ->  %s' % (si, a, b))
    print('')
    print('새 파일 : %s' % dst)
    print('원본은 그대로 있습니다.')


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else None)

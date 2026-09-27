# -*- coding: utf-8 -*-
"""18. 전화번호 사전 - PLAUD 파일명/회의록에서 이름-번호-현장을 모아 즉시 조회."""
import os, sys, re
from common import *

PHONE = re.compile(r'(01[016789][-\s]?\d{3,4}[-\s]?\d{4})')
TAIL = re.compile(r'_\d{8,14}$')

def norm(p):
    return re.sub(r'\D', '', p)

def pretty(p):
    d = norm(p)
    if len(d) == 11:
        return '%s-%s-%s' % (d[:3], d[3:7], d[7:])
    if len(d) == 10:
        return '%s-%s-%s' % (d[:3], d[3:6], d[6:])
    return p

def build():
    """{번호: {이름들, 현장들, 마지막날짜}} - 파일명/폴더명/회의록 본문 전부에서 모은다."""
    book = {}
    root = sites_root()
    if not os.path.isdir(root):
        return book

    def add(num, who, site, datehint):
        e = book.setdefault(num, {'who': set(), 'site': set(), 'last': ''})
        if who:
            e['who'].add(who[:30])
        if site:
            e['site'].add(site)
        if datehint and datehint > e['last']:
            e['last'] = datehint

    def scan(text, site):
        for m in PHONE.finditer(text.replace('_', ' ')):
            raw = m.group(1)
            num = norm(raw)
            if len(num) < 10:
                continue
            head = text.split(raw)[0]
            toks = [t for t in re.split(r'[\s_\-/|,]+', head) if t.strip()]
            who = toks[-1] if toks else ''
            who = TAIL.sub('', who)
            dm = re.findall(r'(20\d{6})', text)
            add(num, who, site, max(dm) if dm else '')

    for p in walk_files(root):
        rel = os.path.relpath(p, root)
        site = rel.split(os.sep)[0]
        scan(os.path.splitext(os.path.basename(p))[0], site)
        scan(os.path.dirname(rel).replace(os.sep, ' '), site)
        if os.path.splitext(p)[1].lower() in ('.txt', '.md'):
            scan(read_text(p), site)
    return book

def run(q=None):
    title('18. 전화번호 사전')
    book = build()
    print('모은 번호 %s개' % won(len(book)))
    out = os.path.join(outdir('전화번호사전'), '전화번호사전_%s.csv' % ymd6())
    rows = [[pretty(k), ' / '.join(sorted(v['who'])), ' / '.join(sorted(v['site'])), v['last']]
            for k, v in sorted(book.items(), key=lambda x: -len(x[1]['site']))]
    write_csv(out, rows, ['전화번호', '이름', '현장', '마지막통화'])
    print('사전 파일 : %s' % out)
    q = q if q is not None else ask('\n번호나 이름으로 찾기 (그냥 엔터=건너뜀) > ')
    if not q:
        return
    qn = norm(q)
    print('-' * 56)
    found = 0
    for k, v in book.items():
        if (qn and qn in k) or (not qn and any(q in w for w in v['who'])) or any(q in s for s in v['site']):
            print('%s | %s | %s | 마지막 %s' % (pretty(k), ' / '.join(sorted(v['who'])),
                                               ' / '.join(sorted(v['site'])), v['last']))
            found += 1
    if not found:
        print('못 찾았습니다.')

if __name__ == '__main__':
    run(' '.join(sys.argv[1:]) or None)
    pause()

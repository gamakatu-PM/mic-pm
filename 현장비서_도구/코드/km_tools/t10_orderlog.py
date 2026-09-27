# -*- coding: utf-8 -*-
"""24. 작업의뢰서 발행대장 - 만들어 둔 작업의뢰서를 전부 훑어 무엇을 언제 어느 현장에 냈는지 목록화.
작업의뢰서가 모든 부서 행위의 관문이므로, 빠뜨린 것을 찾는 것이 목적."""
import os, datetime
from common import *

KEY = ('작업의뢰', 'MB-004', '의뢰서')

def run():
    title('24. 작업의뢰서 발행대장')
    root = cfg('plaud')
    if not need(root, 'plaud\\26년 폴더를 설정.ini 에 넣어주십시오'):
        return
    rows = []
    for p in walk_files(root, {'.xlsx', '.xlsm', '.pdf', '.docx'}):
        base = os.path.basename(p)
        if not any(k in base for k in KEY):
            continue
        rel = os.path.relpath(p, root)
        site = rel.split(os.sep)[0]
        st = os.path.getmtime(p)
        rows.append([site, base, datetime.date.fromtimestamp(st).isoformat(), p])
    rows.sort(key=lambda r: r[2], reverse=True)
    print('찾은 작업의뢰서 %s건' % won(len(rows)))
    print('%-18s %-12s %s' % ('현장', '만든 날', '파일'))
    print('-' * 80)
    for r in rows[:40]:
        print('%-18s %-12s %s' % (r[0][:18], r[2], r[1][:44]))
    if len(rows) > 40:
        print('... 외 %s건 (CSV 참조)' % won(len(rows) - 40))
    sites = {}
    for r in rows:
        sites[r[0]] = sites.get(r[0], 0) + 1
    print('')
    print('[현장별 건수]  ' + ' | '.join('%s %d' % (k, v) for k, v in sorted(sites.items(), key=lambda x: -x[1])[:12]))
    o = os.path.join(outdir('의뢰서대장'), '작업의뢰서대장_%s.csv' % ymd6())
    write_csv(o, rows, ['현장', '파일명', '만든 날', '경로'])
    print('파일 : %s' % o)

if __name__ == '__main__':
    run(); pause()

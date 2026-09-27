# -*- coding: utf-8 -*-
"""5. 오늘의 콜 카드 - 오래 연락 안 한 곳부터 전화할 순서를 낸다.
누구에게 걸지는 프로님이 정하십니다. 도구는 '얼마나 안 했는지'만 셉니다."""
import os, datetime
from common import *
import t02_phonebook, sitebook

def run():
    title('5. 오늘의 콜 카드')
    book = t02_phonebook.build()
    if not book:
        print('통화 기록을 못 찾았습니다. plaud\\26년 경로를 확인해 주십시오.'); return
    t0 = today()
    rows = []
    for num, v in book.items():
        last = v['last']
        try:
            d = datetime.datetime.strptime(last, '%Y%m%d').date()
            gap = (t0 - d).days
        except Exception:
            d, gap = None, 9999
        rows.append([' / '.join(sorted(v['site']))[:24], ' / '.join(sorted(v['who']))[:24],
                     t02_phonebook.pretty(num), d.isoformat() if d else '기록없음', gap])
    rows.sort(key=lambda r: -r[4])
    n = int(ask('몇 곳을 뽑을까요? (기본 10) > ', '10') or 10)
    print('')
    print('%-24s %-24s %-15s %-12s %s' % ('현장', '상대', '번호', '마지막', '경과'))
    print('-' * 92)
    for r in rows[:n]:
        gap = '기록없음' if r[4] == 9999 else '%d일' % r[4]
        print('%-24s %-24s %-15s %-12s %s' % (r[0], r[1], r[2], r[3], gap))
    out = os.path.join(outdir('콜카드'), '콜카드_%s.csv' % ymd6())
    write_csv(out, [[a, b, c, e, ('' if f == 9999 else f)] for a, b, c, e, f in rows],
              ['현장', '상대', '번호', '마지막통화', '경과일'])
    log('콜카드', '%d곳' % len(rows))
    print('')
    print('파일 : %s' % out)

if __name__ == '__main__':
    run(); pause()

# -*- coding: utf-8 -*-
"""26+2. 월말 계산서 집계 - 수금대장을 월별로 묶어 발행/미발행/입금 현황을 낸다."""
import os, datetime
from common import *
import t06_collect

def run():
    title('26. 월말 계산서 집계')
    p = t06_collect.book_path()
    if not os.path.exists(p):
        t06_collect.make_blank(p)
        print('수금대장이 없어 빈 양식을 만들었습니다 : %s' % p); return
    rows = t06_collect.load(p)
    months = {}
    for r in rows[1:]:
        r = (r + [''] * 7)[:7]
        site, kind, dlv, amt, bill, paid, term = r
        if not site.strip() or site.startswith('예)'):
            continue
        try:
            amt_n = int(str(amt).replace(',', '') or 0)
        except Exception:
            amt_n = 0
        key = (t06_collect.d(bill) or t06_collect.d(dlv))
        ym = key.strftime('%Y-%m') if key else '미정'
        m = months.setdefault(ym, {'발행': 0, '미발행': 0, '입금': 0, '건수': 0})
        m['건수'] += 1
        if t06_collect.d(paid):
            m['입금'] += amt_n; m['발행'] += amt_n
        elif t06_collect.d(bill):
            m['발행'] += amt_n
        else:
            m['미발행'] += amt_n
    out = []
    print('%-10s %6s %14s %14s %14s %14s' % ('월', '건수', '발행액', '입금액', '미입금', '미발행'))
    print('-' * 78)
    for ym in sorted(months):
        m = months[ym]
        unpaid = m['발행'] - m['입금']
        print('%-10s %6s %14s %14s %14s %14s' % (ym, won(m['건수']), won(m['발행']),
                                                 won(m['입금']), won(unpaid), won(m['미발행'])))
        out.append([ym, m['건수'], m['발행'], m['입금'], unpaid, m['미발행']])
    o = os.path.join(outdir('월말집계'), '월말집계_%s.csv' % ymd6())
    write_csv(o, out, ['월', '건수', '발행액', '입금액', '미입금', '미발행'])
    log('월말집계', '%d개월' % len(months))
    print('')
    print('파일 : %s' % o)

if __name__ == '__main__':
    run(); pause()

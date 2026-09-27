# -*- coding: utf-8 -*-
"""9. 수금 레이더 - 납품 3회(외함/속판/기구물) 기준으로 계산서 발행분과 미수 D-day 를 낸다.
입력 : _도구결과\\수금\\수금대장.csv  (없으면 빈 양식을 만들어 드립니다)
금액은 프로님이 넣으십니다. 도구는 날짜 계산만 합니다."""
import os, csv, io, datetime
from common import *

HEAD = ['현장', '구분(외함/속판/기구물)', '납품일', '금액', '계산서발행일', '입금일', '결제조건일수']

def book_path():
    p = os.path.join(cfg('out'), '수금')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '수금대장.csv')

def make_blank(p):
    write_csv(p, [['예) 광희동1가', '외함', '2026-09-01', '', '', '', '30'],
                  ['예) 광희동1가', '속판', '', '', '', '', '30']], HEAD)
    return p

def load(p):
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                return list(csv.reader(fp))
        except Exception:
            continue
    return []

def d(s):
    s = (s or '').strip()
    for f in ('%Y-%m-%d', '%Y/%m/%d', '%y%m%d', '%Y.%m.%d'):
        try:
            return datetime.datetime.strptime(s, f).date()
        except Exception:
            pass
    return None

def run():
    title('9. 수금 레이더')
    p = book_path()
    if not os.path.exists(p):
        make_blank(p)
        print('수금대장이 없어 빈 양식을 만들었습니다.')
        print(p)
        print('현장/구분/납품일/금액을 채우고 다시 실행하십시오.')
        return
    rows = load(p)
    if not rows:
        print('대장을 읽지 못했습니다.'); return
    t0 = today()
    out, tot_un, tot_wait = [], 0, 0
    print('%-16s %-8s %-12s %12s %-10s %s' % ('현장', '구분', '납품일', '금액', '상태', 'D-day'))
    print('-' * 78)
    for r in rows[1:]:
        r = (r + [''] * 7)[:7]
        site, kind, dlv, amt, bill, paid, term = r
        if not site or site.startswith('예)'):
            continue
        dd, bd, pd = d(dlv), d(bill), d(paid)
        try:
            term_n = int(term or 30)
        except Exception:
            term_n = 30
        try:
            amt_n = int(str(amt).replace(',', '') or 0)
        except Exception:
            amt_n = 0
        if pd:
            state, days = '입금완료', ''
        elif bd:
            due = bd + datetime.timedelta(days=term_n)
            state, days = '입금대기', 'D%+d' % (due - t0).days
            tot_wait += amt_n
        elif dd:
            state, days = '계산서미발행', '납품 %d일 경과' % (t0 - dd).days
            tot_un += amt_n
        else:
            state, days = '납품전', ''
        print('%-16s %-8s %-12s %12s %-10s %s' % (site[:16], kind[:8], dlv, won(amt_n), state, days))
        out.append([site, kind, dlv, amt_n, bill, paid, state, days])
    print('-' * 78)
    print('계산서 미발행 합계 : %s 원' % won(tot_un))
    print('입금 대기 합계     : %s 원' % won(tot_wait))
    o = os.path.join(outdir('수금'), '수금현황_%s.csv' % ymd6())
    write_csv(o, out, ['현장', '구분', '납품일', '금액', '계산서발행일', '입금일', '상태', 'D-day'])
    print('파일 : %s' % o)

if __name__ == '__main__':
    run(); pause()

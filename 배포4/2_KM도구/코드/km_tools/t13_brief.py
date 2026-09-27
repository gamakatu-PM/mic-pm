# -*- coding: utf-8 -*-
"""3. 아침 브리핑 - 오늘 볼 것 한 장(HTML). 납기/수금/미처리/의뢰서를 한 화면에 모은다.
글을 읽지 않고 색과 숫자만 보고 판단한다 (신호등 3색)."""
import os, datetime
from common import *
import sitebook, t05_schedule, t06_collect, t11_plaudgap

def due_rows():
    red, yel = [], []
    t0 = today()
    for s in sitebook.load():
        if not s['due']:
            continue
        try:
            due = datetime.datetime.strptime(s['due'], '%Y-%m-%d').date()
        except Exception:
            continue
        for name, d, why in t05_schedule.back(due):
            dd = (d - t0).days
            if not name.startswith('[의뢰서]') and '벽지' not in name:
                continue
            if dd < 0:
                red.append((s['site'], name, d, dd))
            elif dd <= 21:
                yel.append((s['site'], name, d, dd))
    return red, yel

def money_rows():
    p = t06_collect.book_path()
    if not os.path.exists(p):
        return [], []
    rows = t06_collect.load(p)
    t0 = today()
    unbilled, waiting = [], []
    for r in rows[1:]:
        r = (r + [''] * 7)[:7]
        site, kind, dlv, amt, bill, paid, term = r
        if not site.strip() or site.startswith('예)') or paid.strip():
            continue
        try:
            amt_n = int(str(amt).replace(',', '') or 0)
        except Exception:
            amt_n = 0
        dd, bd = t06_collect.d(dlv), t06_collect.d(bill)
        if bd:
            try:
                term_n = int(term or 30)
            except Exception:
                term_n = 30
            waiting.append((site, kind, amt_n, (bd + datetime.timedelta(days=term_n) - t0).days))
        elif dd:
            unbilled.append((site, kind, amt_n, (t0 - dd).days))
    return unbilled, waiting

def run():
    title('3. 아침 브리핑')
    added = sitebook.sync_from_folders()
    if added:
        print('현장대장에 새 현장 %s개를 추가했습니다.' % won(added))
    red, yel = due_rows()
    unbilled, waiting = money_rows()
    inbox = os.path.join(cfg('biseo'), '1.여기에_v10결과_넣기')
    pending = t11_plaudgap.count_parts(inbox)[0] if os.path.isdir(inbox) else 0

    B1 = [('red', '%s · %s 기한 %s (%d일 지남)' % (s, n, d.isoformat(), -dd)) for s, n, d, dd in
          sorted(red, key=lambda x: x[3])]
    B1 += [('red', '계산서 미발행 : %s %s · %s원 (납품 %d일 경과)' % (s, k, won(a), g))
           for s, k, a, g in sorted(unbilled, key=lambda x: -x[3])]
    B2 = [('yellow', '%s · %s 까지 %s (D%+d)' % (s, n, d.isoformat(), dd)) for s, n, d, dd in
          sorted(yel, key=lambda x: x[3])]
    B2 += [('yellow', '입금 대기 : %s %s · %s원 (D%+d)' % (s, k, won(a), g))
           for s, k, a, g in sorted(waiting, key=lambda x: x[3])]
    B3 = []
    if pending:
        B3.append(('red', 'PLAUD 미처리 회의 %s건 - 시작.bat 을 돌리십시오' % won(pending)))
    else:
        B3.append(('green', 'PLAUD 대기함 비어 있음'))
    sites = sitebook.load()
    nodue = [s['site'] for s in sites if not s['due']]
    if nodue:
        B3.append(('gray', '준공일이 안 적힌 현장 %s개 : %s' % (won(len(nodue)), ', '.join(nodue[:8]))))

    for label, rows in (('오늘 결정하셔야 할 것', B1), ('곧 옵니다 (3주 안)', B2), ('상태', B3)):
        print('')
        print('[%s] %s건' % (label, won(len(rows))))
        for _, line in rows[:12]:
            print('  - %s' % line)
    out = os.path.join(outdir('아침브리핑'), '아침브리핑_%s.html' % ymd6())
    write_html(out, 'KM 아침 브리핑', [('오늘 결정하셔야 할 것', B1), ('곧 옵니다 (3주 안)', B2), ('상태', B3)])
    log('아침브리핑', '빨강 %d / 노랑 %d' % (len(B1), len(B2)))
    print('')
    print('파일 : %s' % out)
    print('(더블클릭하면 브라우저로 열립니다. 폰에서도 보입니다)')

if __name__ == '__main__':
    run(); pause()

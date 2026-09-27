# -*- coding: utf-8 -*-
"""34. 캘린더 내보내기 - 납기 역산·결정대기·도면 접수를 .ics 한 파일로. 더블클릭하면 아웃룩/구글캘린더에 들어간다. 토큰 0.

담는 것
  현장대장 준공일이 있는 현장 -> 역산 단계(의뢰서 발행·벽지 완료·시운전 등) 종일 일정
  결정대기 ★급함 -> 내일 종일 「[KM 결정] ...」
  도면 판 접수(31번 대장) -> 읽은 날 종일 「[도면] {현장} r{n}」
인터넷·계정 없이 파일만 만듭니다. 구글캘린더는 「설정 > 가져오기」, 아웃룩은 더블클릭.
"""
import os, datetime, glob, re
from common import *
import sitebook, t05_schedule, t24_handover
import t31_intake as I

TOOL = '캘린더'

def esc(s):
    return str(s).replace('\\', '\\\\').replace(';', '\;').replace(',', '\\,').replace('\n', '\\n')

def vevent(uid, day, summary, desc=''):
    d1 = day.strftime('%Y%m%d')
    d2 = (day + datetime.timedelta(days=1)).strftime('%Y%m%d')
    now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    return ['BEGIN:VEVENT', 'UID:%s@km' % uid, 'DTSTAMP:%s' % now,
            'DTSTART;VALUE=DATE:%s' % d1, 'DTEND;VALUE=DATE:%s' % d2,
            'SUMMARY:%s' % esc(summary), 'DESCRIPTION:%s' % esc(desc), 'END:VEVENT']

def events(days_ahead=400):
    ev = []
    t0 = today()
    # 납기 역산
    for s in sitebook.load():
        if not s['due']:
            continue
        try:
            due = datetime.datetime.strptime(s['due'], '%Y-%m-%d').date()
        except Exception:
            continue
        for name, d, why in t05_schedule.back(due):
            if d < t0 - datetime.timedelta(days=30) or d > t0 + datetime.timedelta(days=days_ahead):
                continue
            ev.append(('due-%s-%s' % (safe_name(s['site']), d.isoformat()), d,
                       '[납기] %s · %s' % (s['site'], name), '근거 : %s / 준공 %s' % (why, s['due'])))
        ev.append(('fin-%s' % safe_name(s['site']), due, '[준공] %s' % s['site'], ''))
    # 결정대기 ★급함
    x = t24_handover.latest_xlsx(cfg('handover'))
    if x:
        try:
            import openpyxl
            ws = openpyxl.load_workbook(x, data_only=True)['결정대기']
            for r in ws.iter_rows(min_row=5, values_only=True):
                if not r or not r[0] or str(r[1] or '') != '★급함':
                    continue
                ans = r[8] if len(r) > 8 else ''
                done = r[9] if len(r) > 9 else ''
                if done or (ans and str(ans).strip()):
                    continue
                ev.append(('dec-%s' % r[0], t0 + datetime.timedelta(days=1),
                           '[KM 결정] %s' % str(r[3] or '')[:60], str(r[4] or '')))
        except Exception:
            pass
    # 도면 접수
    for name, p in I.sites():
        for r in I.load_ledger(p):
            try:
                d = datetime.datetime.strptime(r['읽은날'], '%Y-%m-%d').date()
            except Exception:
                continue
            ev.append(('dwg-%s-r%s' % (safe_name(name), r['판']), d,
                       '[도면] %s r%s 접수' % (name, r['판']), r['파일']))
    return ev

def write_ics(ev, path):
    L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//KM 현장비서//KO', 'CALSCALE:GREGORIAN',
         'X-WR-CALNAME:KM 현장']
    for uid, d, s, desc in ev:
        L += vevent(uid, d, s, desc)
    L.append('END:VCALENDAR')
    import io as _io
    _io.open(path, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(L) + '\n')
    return path

def run(quiet=False):
    title('34. 캘린더 내보내기   (.ics 한 파일. 토큰 0)')
    sitebook.sync_from_folders()
    ev = events()
    od = outdir(TOOL)
    p = write_ics(ev, os.path.join(od, 'KM_일정_%s.ics' % ymd6()))
    kinds = {}
    for uid, d, s, desc in ev:
        k = s.split(']')[0] + ']'
        kinds[k] = kinds.get(k, 0) + 1
    print('일정 %d개 : %s' % (len(ev), ' / '.join('%s %d' % (k, v) for k, v in kinds.items())))
    for uid, d, s, desc in sorted(ev, key=lambda x: x[1])[:12]:
        print('   %s  %s' % (d.isoformat(), s[:70]))
    print('')
    print('파일 : %s' % p)
    print('* 아웃룩 : 더블클릭 / 구글캘린더 : 설정 > 가져오기 에서 이 파일 선택')
    print('* 현장대장(현장·준공일)이 비어 있으면 납기 일정이 없습니다. 1번 도구에서 채우십시오.')
    log(TOOL, '%d개' % len(ev))
    if not quiet:
        open_file(p)
    return p

if __name__ == '__main__':
    run(); pause()

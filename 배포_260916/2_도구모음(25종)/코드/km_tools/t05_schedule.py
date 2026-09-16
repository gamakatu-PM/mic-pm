# -*- coding: utf-8 -*-
"""10. 납기 역산 경보 - 준공일에서 거꾸로 빼서 '언제까지 해야 하는가'를 낸다.
소요일은 배성윤 프로 확정값 (km-site-schedule).
주의 : 외함 계열(제작/납품)은 현장 공법이 정하는 값이라 역산 대상이 아니다. 여기서는 참고치만 낸다."""
import sys, datetime
from common import *

D = datetime.timedelta

def back(due, spare=7):
    """준공일에서 역산. 반환 : [(단계, 기한일, 설명)]"""
    r = []
    t = due - D(days=spare)
    r.append(['시운전 완료', t, '준공 %d일 전' % spare])
    t -= D(days=7);  r.append(['시운전 시작 (기구물 설치 완료)', t, '시운전 7일'])
    t -= D(days=7);  r.append(['기구물 설치 시작 (빽커버 완료)', t, '기구물 설치 7일'])
    t -= D(days=10); r.append(['빽커버 설치 시작 = 벽지/페인트 완료 요구일', t, '빽커버 10일'])
    wall = t
    t -= D(days=60); r.append(['[의뢰서] 기구물 제작 발행', t, '기구물 제작 2달'])
    t2 = wall - D(days=30); r.append(['강전 접속 완료', t2, '속판 납품 후 1달'])
    t3 = t2 - D(days=60); r.append(['[의뢰서] 속판 제작 발행', t3, '속판 제작 2달'])
    t4 = t3 - D(days=14); r.append(['[참고] 외함 제작 2주', t4, '실제 시점은 현장 공법이 정함'])
    return sorted(r, key=lambda x: x[1])

def run():
    title('10. 납기 역산 경보')
    site = ask('현장명 > ', '현장미정')
    s = ask('준공일 (YYYY-MM-DD) > ')
    try:
        due = datetime.datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        print('날짜 형식이 2026-12-31 이어야 합니다.'); return
    spare = int(ask('준공 전 여유일 (기본 7) > ', '7') or 7)
    rows = back(due, spare)
    t0 = today()
    print('')
    print('%-38s %-12s %-8s %s' % ('단계', '기한', 'D-day', '근거'))
    print('-' * 86)
    out_rows = []
    for name, d, why in rows:
        dd = (d - t0).days
        mark = '지남' if dd < 0 else ('급함' if dd <= 14 else '')
        print('%-38s %-12s %-8s %s %s' % (name, d.isoformat(), 'D%+d' % dd, why, mark))
        out_rows.append([name, d.isoformat(), dd, why, mark])
    out_rows.append(['준공', due.isoformat(), (due - t0).days, '기준일', ''])
    out = os.path.join(outdir('납기역산'), '%s_역산_%s.csv' % (safe_name(site), ymd6()))
    write_csv(out, out_rows, ['단계', '기한', 'D-day', '근거', '경보'])
    print('')
    print('파일 : %s' % out)
    print('* 계산서 발행은 물건 들어갈 때마다 3회(외함/속판/기구물)입니다.')

if __name__ == '__main__':
    run(); pause()

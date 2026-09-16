# -*- coding: utf-8 -*-
"""19. 객실 기구물 수량표 - 성급 표준 배치 규칙으로 물량을 자동 산출 (도면 없이 영업 즉답용).
규칙 출처 : 배성윤 프로 확정 배치 규칙 (km-room-layout).
조명 스위치 구수는 전등 설계가 나와야 확정되므로 여기서 정하지 않고 L 로만 센다."""
import sys
from common import *

def calc(star, rooms, resort=False, veranda=0, desk=0, living=0, floors=0, linen_per_floor=1):
    hi = star >= 4
    q = []
    a = q.append
    a(['챠임벨 (문 입구 복도, 도어락 손잡이쪽)', rooms, '실당 1'])
    a(['KEY SENSOR (K)', rooms, '문 입구'])
    if hi and not resort:
        a(['DM (도어 표시)', rooms, '4~5성급만. 리조트 제외'])
    else:
        a(['DM (도어 표시)', 0, '1~3성급/리조트는 K만'])
    if hi:
        a(['BSP (온도+조명+USB+유니버셜, 침대 옆)', rooms, '4~5성급 침대 옆 통합'])
    else:
        a(['온도조절기 (침대 옆)', rooms, '1~3성급'])
        a(['LIGHT S.W "L" (침대 옆)', rooms, '구수는 전등 설계 후 확정'])
    if hi:
        a(['LIGHT S.W "L" (화장실)', rooms, '4~5성급만 객실관리'])
    else:
        a(['LIGHT S.W "L" (화장실)', 0, '1~3성급은 전기 텀블러 = 전기업체 공사'])
    if hi:
        a(['LIGHT S.W "L" (베란다 문 옆)', veranda, '4~5성급은 별도'])
    else:
        a(['LIGHT S.W "L" (베란다)', 0, '1~3성급은 침대 L 에서 제어'])
    a(['멀티아울렛 (유니버셜+콘센트2+USB, 책상)', desk, '책상 있는 실'])
    a(['온도조절기 (거실 입구)', living, '1~5성급 공통'])
    a(['LIGHT S.W "L" (거실 입구)', living, '1~5성급 공통'])
    a(['FIP (각층 린넨실)', floors * linen_per_floor, '층당 %d개' % linen_per_floor])
    a(['OPERATION PC (방재실)', 1, '현장당 1EA'])
    return q

def run():
    title('19. 객실 기구물 수량표 (성급 표준 배치)')
    site = ask('현장명 > ', '현장미정')
    star = int(ask('성급 1~5 > ', '3') or 3)
    resort = ask('리조트입니까? (y/n) > ', 'n').lower().startswith('y')
    rooms = int(ask('총 객실 수 > ', '0') or 0)
    veranda = int(ask('베란다 있는 실 수 (없으면 0) > ', '0') or 0)
    desk = int(ask('책상 있는 실 수 (없으면 0) > ', '0') or 0)
    living = int(ask('거실 있는 실 수 (없으면 0) > ', '0') or 0)
    floors = int(ask('객실 층 수 > ', '0') or 0)
    rows = calc(star, rooms, resort, veranda, desk, living, floors)
    print('')
    print('%-46s %8s  %s' % ('품목', '수량', '근거'))
    print('-' * 90)
    for r in rows:
        print('%-46s %8s  %s' % (r[0], won(r[1]), r[2]))
    out = os.path.join(outdir('객실수량표'),
                       '%s_객실수량표_%s.csv' % (safe_name(site), ymd6()))
    head = ['품목', '수량', '근거']
    meta = [['[현장]', site, ''], ['[성급]', star, '리조트' if resort else ''],
            ['[객실수]', rooms, ''], ['', '', '']]
    write_csv(out, meta + rows, head)
    print('')
    print('파일 : %s' % out)
    print('* 조명 스위치 구수(1~6구)는 전등 설계가 나와야 확정됩니다. 여기서는 L 개수만 셉니다.')

if __name__ == '__main__':
    run(); pause()

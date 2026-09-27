# -*- coding: utf-8 -*-
"""20. CB 외함 세트 계산 - W*H*D 하나로 MC / C-H / 부스바 단수까지 자동.
규칙 : C/H = W x H  |  MC = (W-80) x (H-80)  |  부스바 단수 = RCBO 수량 + 1
매입형 = C/B(커버미포함) + MC + C/H  |  노출형 = C/B(커버포함) + MC"""
import sys
from common import *

def calc(w, h, d, form='매입', rcbo=0):
    mc = (w - 80, h - 80)
    ch = (w, h)
    rows = [['C/B 외함 본체', '%d*%d*%d' % (w, h, d),
             '커버 미포함' if form == '매입' else '커버 포함'],
            ['MC 속판', '%d*%d' % mc, '(W-80) x (H-80)']]
    if form == '매입':
        rows.append(['C/H 커버', '%d*%d' % ch, '외함과 동일 W x H. 공사 후 별도 제작'])
    else:
        rows.append(['C/H 커버', '-', '노출형은 C/B 에 포함'])
    if rcbo:
        rows.append(['부스바', '%d단' % (rcbo + 1), 'RCBO %d + 1. CB 내부 자재(외함 아님)' % rcbo])
    return rows

def run():
    title('20. CB 외함 세트 계산')
    w = int(ask('외함 W > ', '0') or 0)
    h = int(ask('외함 H > ', '0') or 0)
    d = int(ask('외함 D > ', '0') or 0)
    form = ask('형식 (매입/노출) > ', '매입')
    rcbo = int(ask('RCBO 수량 (모르면 0) > ', '0') or 0)
    if not (w and h):
        print('W, H 가 있어야 계산됩니다.'); return
    rows = calc(w, h, d, form, rcbo)
    print('')
    for r in rows:
        print('%-16s %-18s %s' % (r[0], r[1], r[2]))
    print('')
    print('[검산] 속판이 도면에 %d*%d 로 적혀 있지 않으면 외함 규격을 잘못 읽은 것입니다.' % (w - 80, h - 80))
    print('[주의] 부스바는 외함이 아니라 CB 내부 자재입니다. 모듈 표 안(합계 위)에 세우십시오.')
    out = os.path.join(outdir('외함세트'), '외함세트_%dx%dx%d_%s.csv' % (w, h, d, ymd6()))
    write_csv(out, rows, ['품목', '규격', '비고'])
    print('파일 : %s' % out)

if __name__ == '__main__':
    run(); pause()

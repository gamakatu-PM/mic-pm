# -*- coding: utf-8 -*-
"""32. 현장 한 방에 - 현장 하나를 골라 31 -> 27 -> 28 -> 29 -> 30 을 묻지 않고 연달아 돌린다. 토큰 0.

끝나면 「이 현장은 지금 어디까지 됐고 무엇이 비었나」 한 장이 뜹니다.
비는 것은 30번이 부탁서로 묶어 두므로, 그 파일만 클로드에게 주시면 됩니다.
"""
import os, sys, traceback
import common
from common import *
import t31_intake as I
import t27_drawing as D
import t28_cost as C
import t29_pricebook as P
import t30_finish as F
import t33_dashboard as DB

TOOL = '한방에'

def run_site(site, sdir, with_intake=True, with_dash=True):
    """현장 하나를 묻지 않고 끝까지. 돌아온 값 : [(단계, 결과)]"""
    common.AUTO = True
    steps = []
    if with_intake:
        steps.append(('31 도면 접수·판 비교', lambda: I.run(site_hint=site)))
    steps += [('27 도면 수량', lambda: D.run(folder=sdir, site_hint=site)),
              ('28 단가 붙이기', lambda: C.run(site_hint=site)),
              ('29 단가장 채우기', lambda: P.run(folder=sdir, site_hint=site)),
              ('30 완성품 점검·부탁서', lambda: F.run(site_hint=site))]
    if with_dash:
        steps.append(('33 현황판', lambda: DB.run(quiet=True)))
    done = []
    try:
        for name, fn in steps:
            print('')
            print('-' * 74)
            print(' >> %s' % name)
            print('-' * 74)
            try:
                fn(); done.append((name, '완료'))
            except Exception as e:
                done.append((name, '오류 : %s' % e))
                print('[오류] %s 에서 멈췄지만 다음 단계로 갑니다.' % name)
                traceback.print_exc()
    finally:
        common.AUTO = False
    return done

def run():
    title('32. 현장 한 방에   (31 -> 27 -> 28 -> 29 -> 30 -> 33 연달아. 토큰 0)')
    ss = I.sites()
    if not ss:
        print('[현장 폴더가 없습니다] 3_공통사용\\도면\\{현장명}\\ 을 만들고 도면을 넣어주십시오.')
        open_folder(D.dwg_root())
        return
    for i, (n, p) in enumerate(ss, start=1):
        print(' %2d. %s' % (i, n))
    s = ask('\n현장 번호 (엔터=1) > ', '1')
    if not s.isdigit() or not (1 <= int(s) <= len(ss)):
        return
    site, sdir = ss[int(s) - 1]
    print('')
    print('=' * 74)
    print(' [%s]  묻지 않고 연달아 돌립니다. 기본값은 화면에 [자동] 으로 찍힙니다.' % site)
    print('=' * 74)
    done = run_site(site, sdir)
    print('')
    print('=' * 74)
    print(' [%s] 한 방에 끝' % site)
    for n, r in done:
        print('   %-24s %s' % (n, r))
    print('=' * 74)
    print(' 빈 곳은 30번이 「_클로드부탁서_%s_*.md」 로 묶어 뒀습니다. 그 파일만 주시면 됩니다.' % safe_name(site))
    log(TOOL, '%s %s' % (site, ' / '.join('%s=%s' % (n[:2], r[:2]) for n, r in done)))

if __name__ == '__main__':
    run(); pause()

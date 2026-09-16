# -*- coding: utf-8 -*-
"""36. 오늘 한 방에 - 시작.py 에서 엔터만 누르면 이것이 돈다. 손이 안 간다.

  1) 다운로드/바탕화면에 지금보다 새 KM zip 이 있으면 스스로 적용한다 (98번 손 제거)
  2) 받은함(_여기에_넣으십시오)의 도면을 [현장명] 으로 현장 폴더에 나눠 넣는다 (폴더 만드는 손 제거)
  3) 모든 현장의 새 도면을 읽고(31), 새 판이 생긴 현장만 27->28->29->30 을 돌린다
  4) 현황판(33)을 만들어 띄운다. 클로드에게 넘길 것은 30번 부탁서에 모여 있다
"""
import os, sys, traceback
import common
from common import *
import t98_update as U
import t31_intake as I
import t32_oneshot as O
import t33_dashboard as DB

TOOL = '오늘한방에'

def auto_update(quiet=False):
    z = U.fetch_latest(quiet=quiet) or U.newer_zip()
    if not z:
        return False
    print('새 판 zip 을 찾았습니다 : %s' % os.path.basename(z))
    if not ask('적용할까요? (y=엔터 / n) > ', 'y').lower().startswith('y'):
        return False
    try:
        r, err = U.apply(z)
        if err:
            print('[적용 실패] %s' % err); return False
        n, backup, extra = r
        print('도구 %d개를 갈아끼웠습니다. %s' % (n, ' / '.join(extra)))
        log(TOOL, '자동 업데이트 %s' % os.path.basename(z))
        if quiet:
            # 스케줄러 모드 : 새 코드로 나 자신을 다시 띄운다 (손 0)
            try:
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception:
                pass
            return True
        print('')
        print('=' * 60)
        print(' 새 판이 들어갔습니다. 이 창을 닫고 시작.py 를 다시 눌러주십시오.')
        print('=' * 60)
        return True
    except Exception as e:
        print('[적용 실패] %s' % e)
        return False

def run(quiet=False):
    """quiet=True : 작업 스케줄러가 부르는 모드. 묻지 않고, 새 판이 생긴 현장이 있을 때만 현황판을 띄운다."""
    title('오늘 한 방에   (엔터 한 번. 새 zip 적용 -> 도면 분류 -> 새 판 처리 -> 현황판)')
    common.AUTO = True
    try:
        for sc in make_shortcuts(I.D.dwg_root()) + make_shortcuts(desktop_dir()):
            print('바로가기 만듦 : %s' % sc)
        if auto_update(quiet=quiet):
            return
        print('')
        print('-' * 74); print(' >> 31 도면 접수 (받은함 분류 + 전 현장 새 판 찾기)'); print('-' * 74)
        results = []
        try:
            results = I.run() or []
        except Exception:
            traceback.print_exc()
        todo = [(r['site'], os.path.join(I.D.dwg_root(), safe_name(r['site']))) for r in results if r.get('items')]
        summary = []
        for site, sdir in todo:
            print('')
            print('=' * 74); print(' [%s] 새 판 -> 27·28·29·30' % site); print('=' * 74)
            done = O.run_site(site, sdir, with_intake=False, with_dash=False)
            summary.append((site, done))
        if not todo:
            print('')
            print('새 판이 생긴 현장이 없습니다. 현황판만 새로 만듭니다.')
        print('')
        print('-' * 74); print(' >> 33 현황판'); print('-' * 74)
        top = None
        try:
            top, mdp, blocks = DB.build(quiet=True)
        except Exception:
            traceback.print_exc()
    finally:
        common.AUTO = False
    print('')
    print('=' * 74)
    print(' 오늘 한 방에 끝')
    for site, done in summary:
        print('   [%s]  %s' % (site, ' / '.join('%s=%s' % (n[:2], r[:2]) for n, r in done)))
    if top:
        print('   현황판 : %s' % top)
    print('=' * 74)
    print(' 클로드에게 넘길 것은 현황판 ③ 에 있습니다. 부탁서 파일만 대화창에 던지십시오.')
    log(TOOL, '현장%d%s' % (len(summary), ' 자동' if quiet else ''))
    if top and (not quiet or summary):
        open_file(top)

if __name__ == '__main__':
    run(); pause()

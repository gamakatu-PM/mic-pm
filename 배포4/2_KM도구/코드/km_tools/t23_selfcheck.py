# -*- coding: utf-8 -*-
"""자가진단 - 경로/부품/도구가 제대로 있는지 스스로 점검한다. 오류가 나면 여기부터 돌리십시오."""
import os, sys, importlib
from common import *

def run():
    title('자가진단')
    ok, bad = [], []
    import platform, getpass
    print('[1] 파이썬  %s   (%s / %s)' % (sys.version.split()[0],
          platform.node(), getpass.getuser()))
    for mod, why in (('openpyxl', '엑셀 도구(견적서/사진대지/서식검사/단가장검진)'),
                     ('PIL', '사진대지 회전보정/축소'),
                     ('pptx', '이미지 모음 PPT(15번)')):
        try:
            importlib.import_module(mod); ok.append(mod)
            print('    %-10s 있음  (%s)' % (mod, why))
        except ImportError:
            bad.append(mod)
            print('    %-10s 없음  -> _처음_한번만_설치.bat 을 눌러주십시오 (%s)' % (mod, why))
    print('')
    print('[2] 경로')
    for k in ('base', 'plaud', 'biseo', 'template', 'out'):
        p = cfg(k)
        mark = '있음' if os.path.isdir(p) else '없음'
        print('    %-9s %-4s %s' % (k, mark, p))
        if mark == '없음' and k != 'out':
            bad.append('경로:' + k)
    sr = sites_root()
    print('    %-9s %-4s %s' % ('현장폴더', '있음' if os.path.isdir(sr) else '없음', sr))
    print('')
    print('[3] 원틀')
    for nm, keys in (('견적서', ('견적',)), ('작업의뢰서', ('작업의뢰',)),
                     ('자재사양서', ('자재',)), ('시방서', ('시방',)), ('제안서', ('제안',))):
        t = find_template(*keys)
        print('    %-10s %s' % (nm, os.path.basename(t) if t else '없음 (그 도구는 못 씁니다)'))
    print('')
    print('[4] 대장')
    import sitebook, t06_collect
    sb = sitebook.ensure(); cb = t06_collect.book_path()
    added = sitebook.sync_from_folders()
    if added:
        print('    현장 폴더에서 %s개를 현장대장에 새로 넣었습니다.' % won(added))
    nsite = len(sitebook.load())
    print('    현장대장   %s  (현장 %s개)' % ('있음' if os.path.exists(sb) else '없음', won(nsite)))
    if nsite == 0:
        print('               [경고] 현장이 0개입니다. 현장 폴더 경로를 확인해 주십시오.')
        bad.append('현장 0개')
    print('    수금대장   %s' % ('있음' if os.path.exists(cb) else '없음 - 6번을 한 번 돌리면 생깁니다'))
    print('')
    print('[5] 도구 점검')
    import menu
    fail = []
    for label, mod in menu.flat():
        try:
            m = importlib.import_module(mod)
            assert hasattr(m, 'run')
        except Exception as e:
            fail.append((mod, str(e)[:60]))
    print('    도구 %s개 중 정상 %s개' % (won(len(menu.flat())), won(len(menu.flat()) - len(fail))))
    for mod, e in fail:
        print('    [고장] %s : %s' % (mod, e))
    print('')
    if bad or fail:
        print('=> 위의 [없음]/[고장] 줄을 그대로 클로드에게 보여주십시오.')
    else:
        print('=> 전부 정상입니다.')
    log('자가진단', '부족 %d / 고장 %d' % (len(bad), len(fail)))

if __name__ == '__main__':
    run(); pause()

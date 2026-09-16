# -*- coding: utf-8 -*-
"""38. 자동 실행 등록 - 프로님 손 0. 윈도우 작업 스케줄러에 「오늘 한 방에」 를 걸어 둔다.
  · 로그온할 때 1번 + 2시간마다 1번, 조용히 돈다 (묻지 않음)
  · 정본(GitHub)에 새 판이 있으면 스스로 받아 갈아끼우고 다시 돈다  -> zip 받기·98번 손 없음
  · 받은함/현장 폴더에 새 도면이 있으면 27~30 을 돌리고 현황판을 띄운다 -> 시작.py·번호 누르는 손 없음
  · 새 도면이 없으면 아무것도 띄우지 않는다
"""
import os, sys, subprocess
from common import *

TOOL = '자동실행'
TASKS = (('KM_자동_로그온', ['/SC', 'ONLOGON', '/DELAY', '0002:00']),
         ('KM_자동_2시간', ['/SC', 'HOURLY', '/MO', '2']))

def launcher_path():
    return os.path.join(os.path.dirname(os.path.dirname(HERE)), 'KM_자동.py')

def write_launcher():
    p = launcher_path()
    code = """# -*- coding: utf-8 -*-
\"\"\"KM 자동 - 작업 스케줄러가 부르는 파일. 직접 눌러도 됩니다 (묻지 않고 「오늘 한 방에」).\"\"\"
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '코드', 'km_tools')
sys.path.insert(0, TOOLS)
import common
common.AUTO = True
import t36_today
t36_today.run(quiet=True)
"""
    import io as _io
    _io.open(p, 'w', encoding='utf-8').write(code)
    return p

def status():
    if os.name != 'nt':
        return {}
    out = {}
    for name, _ in TASKS:
        r = subprocess.run(['schtasks', '/Query', '/TN', name], capture_output=True, text=True)
        out[name] = (r.returncode == 0)
    return out

def register():
    if os.name != 'nt':
        print('윈도우에서만 등록됩니다.'); return False
    lp = write_launcher()
    py = sys.executable.replace('python.exe', 'pythonw.exe')   # 검은 창 없이
    if not os.path.exists(py):
        py = sys.executable
    tr = '"%s" "%s"' % (py, lp)
    ok = True
    for name, sched in TASKS:
        cmd = ['schtasks', '/Create', '/F', '/TN', name, '/TR', tr] + sched
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print('등록 : %s' % name)
        else:
            ok = False; print('[등록 실패] %s : %s' % (name, (r.stderr or r.stdout).strip()[:200]))
    if ok:
        print('')
        print('이제 프로님 손은 두 번뿐입니다 : ① 도면을 넣는다  ② 부탁서를 클로드에게 던진다')
        print('  zip 받기·98번·시작.py·번호 누르기는 없어졌습니다. (정본에 새 판이 오면 스스로 갈아끼웁니다)')
        print('  실행 파일 : %s' % lp)
        log(TOOL, '등록')
    return ok

def unregister():
    if os.name != 'nt':
        return
    for name, _ in TASKS:
        subprocess.run(['schtasks', '/Delete', '/F', '/TN', name], capture_output=True, text=True)
    print('해제했습니다.'); log(TOOL, '해제')

def run():
    title('38. 자동 실행 등록   (로그온 때 + 2시간마다 「오늘 한 방에」 조용히. 손 0)')
    st = status()
    if st:
        for k, v in st.items():
            print('  %s : %s' % (k, '등록됨' if v else '없음'))
    print('')
    print('  1) 등록 (추천)   2) 해제   3) 지금 한 번 조용히 돌려보기   0) 뒤로')
    c = ask('> ', '1').strip()
    if c == '1':
        register()
    elif c == '2':
        unregister()
    elif c == '3':
        import t36_today
        t36_today.run(quiet=True)

if __name__ == '__main__':
    run(); pause()

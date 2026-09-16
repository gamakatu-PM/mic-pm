# -*- coding: utf-8 -*-
"""KM 도구 — 이 파일 하나만 더블클릭하십시오.
없는 부품은 알아서 받고, 바로 메뉴를 띄웁니다."""
import os, sys, subprocess, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools')
NEED = [('openpyxl', 'openpyxl'), ('PIL', 'pillow'), ('pptx', 'python-pptx')]

def line(s=''):
    print(s)

def ensure():
    missing = []
    for mod, pkg in NEED:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return True
    line('=' * 56)
    line(' 처음이시군요. 필요한 부품 %d개를 받겠습니다.' % len(missing))
    line(' 인터넷이 연결돼 있어야 하고, 1~2분 걸립니다.')
    line('=' * 56)
    for pkg in missing:
        line('')
        line('[%s] 받는 중...' % pkg)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=False)
        except Exception as e:
            line('  실패: %s' % e)
    still = []
    for mod, pkg in NEED:
        try:
            importlib.import_module(mod)
        except ImportError:
            still.append(pkg)
    if still:
        line('')
        line('아래 부품을 못 받았습니다: %s' % ', '.join(still))
        line('인터넷이 막혀 있을 수 있습니다. 이 화면을 클로드에게 보여주십시오.')
        line('(그래도 대부분의 도구는 돕니다 — 계속 진행합니다)')
        line('')
    else:
        line('')
        line('부품 준비 끝. 메뉴를 띄웁니다.')
        line('')
    return True

def main():
    if not os.path.isdir(TOOLS):
        line('[오류] 도구 폴더를 못 찾았습니다.')
        line('  찾은 곳 : %s' % TOOLS)
        line('  -> 이 파일(시작.py)이 KM도구 폴더 안에 있어야 합니다.')
        input('\n엔터를 누르면 닫힙니다...')
        return
    ensure()
    sys.path.insert(0, TOOLS)
    import runpy
    try:
        runpy.run_path(os.path.join(TOOLS, 'menu.py'), run_name='__main__')
    except Exception:
        import traceback
        line('')
        line('[오류] 아래 글자를 그대로 클로드에게 보여주십시오.')
        traceback.print_exc()
        try:
            input('\n엔터를 누르면 닫힙니다...')
        except EOFError:
            pass

if __name__ == '__main__':
    main()

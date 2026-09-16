# -*- coding: utf-8 -*-
"""KM 도구 — 이 파일 하나만 더블클릭하십시오.
없는 부품은 알아서 받고, 바로 메뉴를 띄웁니다."""
import os, sys, subprocess, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = [os.path.join(HERE, '코드', 'km_tools'),
         os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
         os.path.join(HERE, 'km_tools')]
TOOLS = next((p for p in CANDS if os.path.isdir(p)), CANDS[0])
NEED = [('openpyxl', 'openpyxl'), ('PIL', 'pillow'), ('pptx', 'python-pptx')]

def ensure():
    missing = []
    for mod, pkg in NEED:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return
    print('=' * 56)
    print(' 처음이시군요. 필요한 부품 %d개를 받겠습니다.' % len(missing))
    print(' 인터넷이 연결돼 있어야 하고, 1~2분 걸립니다.')
    print('=' * 56)
    for pkg in missing:
        print('\n[%s] 받는 중...' % pkg)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=False)
        except Exception as e:
            print('  실패: %s' % e)
    still = [pkg for mod, pkg in NEED
             if not _ok(mod)]
    if still:
        print('\n못 받은 부품: %s' % ', '.join(still))
        print('인터넷이 막혀 있을 수 있습니다. 대부분의 도구는 그래도 돕니다.\n')
    else:
        print('\n부품 준비 끝. 메뉴를 띄웁니다.\n')

def _ok(mod):
    try:
        importlib.import_module(mod); return True
    except ImportError:
        return False

def main():
    if not os.path.isdir(TOOLS):
        print('[오류] 도구 폴더를 못 찾았습니다.')
        print('  찾은 곳 : %s' % TOOLS)
        print('  -> 시작.py 와 같은 자리에 「코드」 폴더가 있어야 합니다.')
        input('\n엔터를 누르면 닫힙니다...')
        return
    ensure()
    sys.path.insert(0, TOOLS)
    import runpy
    try:
        runpy.run_path(os.path.join(TOOLS, 'menu.py'), run_name='__main__')
    except Exception:
        import traceback
        print('\n[오류] 아래 글자를 그대로 클로드에게 보여주십시오.')
        traceback.print_exc()
        try:
            input('\n엔터를 누르면 닫힙니다...')
        except EOFError:
            pass

if __name__ == '__main__':
    main()

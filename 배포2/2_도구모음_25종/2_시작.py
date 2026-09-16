# -*- coding: utf-8 -*-
"""도구모음 실행 — bat 이 막힐 때 이 파일을 더블클릭하십시오."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '코드', 'km_tools'))
try:
    runpy.run_path(os.path.join(HERE, '코드', 'km_tools', 'menu.py'), run_name='__main__')
except Exception:
    import traceback
    traceback.print_exc()
    try:
        input('\n엔터를 누르면 닫힙니다...')
    except EOFError:
        pass

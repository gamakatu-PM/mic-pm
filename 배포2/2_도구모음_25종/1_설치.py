# -*- coding: utf-8 -*-
"""처음 한 번만 — 필요한 부품을 받습니다. (bat 이 막힐 때 이 파일을 더블클릭하십시오)"""
import sys, subprocess
print('=' * 56)
print(' KM 도구모음 — 처음 한 번만 설치')
print('=' * 56)
print('파이썬 %s' % sys.version.split()[0])
for pkg in ('openpyxl', 'pillow', 'python-pptx'):
    print('\n[%s] 받는 중...' % pkg)
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', pkg], check=False)
    except Exception as e:
        print('  실패: %s' % e)
print('\n끝났습니다. 이제 2_시작.py 를 더블클릭하시면 됩니다.')
try:
    input('\n엔터를 누르면 닫힙니다...')
except EOFError:
    pass

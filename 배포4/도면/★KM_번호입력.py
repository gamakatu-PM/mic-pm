# -*- coding: utf-8 -*-
# KM 바로가기 - 더블클릭만 하십시오. 어디에 두어도 됩니다. (번호 하나 넣고 그 도구 실행)
import os, sys, subprocess
START = '/home/user/mic-pm/배포4/2_KM도구/시작.py'
if not os.path.exists(START):
    # 폴더를 옮기셨으면 이 파일 위쪽 7단계에서 2_KM도구\시작.py 를 찾아본다
    d = os.path.dirname(os.path.abspath(__file__)); START = None
    for _ in range(7):
        c = os.path.join(d, '2_KM도구', '시작.py')
        if os.path.exists(c):
            START = c; break
        d = os.path.dirname(d)
if not START:
    print('2_KM도구\시작.py 를 못 찾았습니다. 시작.py 를 한 번 눌러 주시면 바로가기가 다시 만들어집니다.')
    input('엔터...'); sys.exit(1)
subprocess.call([sys.executable, START] + ['--ask'])

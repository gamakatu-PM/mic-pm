# -*- coding: utf-8 -*-
"""★앱 회신 — 앱에서 「보내기」 한 것을 받아 회사 대장(csv)에 덧붙입니다.  (v1, 2026-09-27)

누르면 끝입니다. 외울 것이 없습니다.  AI 사용량 0.

    읽는 곳 : [KM] 회신 메일 (gamakatu0924@gmail.com, IMAP) 또는 다운로드\KM_회의록받는함\앱회신.txt
    내는 것 : _대장 의 확정사항.csv · 전화번호부.csv · 경계.csv · 하자.csv 에 줄을 덧붙임 (지우지 않음)
              + 산출물\도구결과\앱받기\{날짜}\_클로드부탁서_앱.md (못 알아들은 줄은 클로드에게)
    확정만 대장에 들어갑니다. 추정은 들어가지 않습니다.

부품 t50_appback.py 는 코드\km_tools 에 있습니다. 메뉴 번호는 붙이지 않았습니다 (★제안서_PPT·★작업의뢰서_초안 과 같은 방식 — menu.py 를 건드리지 않으려고).
"""
import os, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))


def find_tools():
    for p in (os.path.join(HERE, '코드', 'km_tools'),
              os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
              os.path.join(HERE, 'km_tools')):
        if os.path.isdir(p):
            return p
    return ''


def main():
    tools = find_tools()
    if not tools:
        print('km_tools 폴더를 못 찾았습니다. 이 파일은 2_KM도구 바로 아래에 있어야 합니다.')
        input('엔터를 누르면 닫힙니다 ')
        return 1
    sys.path.insert(0, tools)
    os.chdir(HERE)          # 시작.py 와 같은 자리(2_KM도구). 부품은 설정.ini 로 3_공통사용 을 찾는다
    try:
        import importlib
        m = importlib.import_module('t50_appback')
        r = m.run()
        return 0 if r in (None, 0, True) else 1
    except SystemExit as e:
        return int(e.code or 0)
    except Exception:
        traceback.print_exc()
        print()
        print('멈췄습니다. 위 글자를 그대로 클로드 대화창에 붙여 주십시오.')
        input('엔터를 누르면 닫힙니다 ')
        return 1


if __name__ == '__main__':
    sys.exit(main())

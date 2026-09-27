# -*- coding: utf-8 -*-
"""★앱 피드 — 회의록·대장을 읽어 「KM 손바닥」 앱에 붙여 넣을 글을 클립보드에 복사합니다.  (v1, 2026-09-27)

누르면 끝입니다. 외울 것이 없습니다.  AI 사용량 0.

    읽는 곳 : plaud\26년\...\원문.txt (회의록) · _도구결과\_대장 의 확정사항·현장대장·견적발송·앞으로할것 csv · 40번 회의연결 결과
    내는 것 : _도구결과\앱피드\{날짜}\앱피드.json  + 클립보드 복사 + 앱(3호) 열기
    그다음  : 폰(또는 PC 브라우저) 앱 → 설정 → 「PC에서 붙여넣기」 에 붙이고 「받기」.  같은 것을 두 번 넣어도 늘어나지 않습니다.

부품 t49_appfeed.py 는 코드\km_tools 에 있습니다. 메뉴 번호는 붙이지 않았습니다 (★제안서_PPT·★작업의뢰서_초안 과 같은 방식 — menu.py 를 건드리지 않으려고).
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
        m = importlib.import_module('t49_appfeed')
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

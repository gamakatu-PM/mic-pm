# -*- coding: utf-8 -*-
"""★회의록 드라이브로 — 이 파일만 더블클릭하십시오. (2026-09-22)

회의록을 저장하신 뒤 이것 하나만 누르시면 됩니다.
  · 회의록을 찾아 구글 드라이브 「회의록\\incoming」 으로 복사합니다
  · 결과를 화면과 「드라이브올림_결과.txt」 에 남깁니다
  · 그 뒤 클로드 대화창에 「올렸어」 라고만 하시면 나머지는 클로드가 합니다

왜 시작.py 가 아니라 이 파일인가
  시작.py 엔터는 「오늘 한 방에」 가 돌면서 새 zip 을 자동 적용합니다.
  그 zip 이 51번 연결을 지워 버리는 일이 반복됐습니다(2026-09-22).
  이 파일은 2_KM도구 폴더 바로 아래에 있어 zip 이 건드리지 않고,
  도면·현황판 같은 다른 일도 하지 않습니다. 회의록만 올립니다.
"""
import os, sys, io, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = [os.path.join(HERE, '코드', 'km_tools'),
         os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
         os.path.join(HERE, 'km_tools')]


def find_tools():
    for p in CANDS:
        if os.path.isfile(os.path.join(p, 't51_driveup.py')):
            return p
    # 못 찾으면 아래로 3단계까지 뒤진다
    for root, dirs, files in os.walk(HERE):
        if 't51_driveup.py' in files:
            if root.count(os.sep) - HERE.count(os.sep) <= 3:
                return root
    return ''


def main():
    print('=' * 60)
    print(' 회의록 -> 구글 드라이브        %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
    print('=' * 60)

    tools = find_tools()
    if not tools:
        print('')
        print('★ t51_driveup.py 를 못 찾았습니다.')
        print('  코드\\km_tools 폴더에 그 파일이 있어야 합니다.')
        print('  이 화면을 클로드에게 보여 주십시오.')
        return

    sys.path.insert(0, tools)
    try:
        import t51_driveup as DU
    except Exception:
        import traceback
        print('')
        print('★ 51번을 불러오지 못했습니다. 아래 글자를 클로드에게 보여 주십시오.')
        traceback.print_exc()
        return

    try:
        r = DU.run()          # 화면에 찍고, 결과 txt 를 남기고 띄운다
    except Exception:
        import traceback
        print('')
        print('★ 도는 중에 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        traceback.print_exc()
        return

    print('')
    if r.get('올림'):
        print(' 끝났습니다. 클로드 대화창에 「올렸어」 라고만 하십시오.')
    elif r.get('이유'):
        print(' 못 올렸습니다 : %s' % r['이유'])
    elif not r.get('찾음'):
        print(' 회의록을 못 찾았습니다. 위 「본 곳」 목록을 클로드에게 보여 주십시오.')
    else:
        print(' 새로 저장하신 회의록이 없습니다 (전부 전에 올린 것).')


if __name__ == '__main__':
    try:
        main()
    finally:
        try:
            input('\n엔터를 누르면 닫힙니다... ')
        except Exception:
            pass

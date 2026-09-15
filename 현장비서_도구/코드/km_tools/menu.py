# -*- coding: utf-8 -*-
"""KM 현장비서 도구모음 - 번호 메뉴.
기존 시작.bat(회의록)은 건드리지 않습니다. 이것은 그 옆에 붙는 별도 런처입니다."""
import os, sys, importlib, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import title, pause, cfg

MENU = [
    ('회의록 검색기        - 전 현장 회의록에서 한 단어 찾기', 't01_search'),
    ('전화번호 사전        - 번호/이름으로 누구,어느 현장인지', 't02_phonebook'),
    ('객실 수량표          - 성급만 넣으면 기구물 물량 자동', 't03_roomqty'),
    ('CB 외함 세트 계산    - WxHxD 하나로 속판/커버/부스바', 't04_enclosure'),
    ('납기 역산 경보       - 준공일에서 거꾸로, 의뢰서 발행일', 't05_schedule'),
    ('수금 레이더          - 계산서 미발행/입금 대기 D-day', 't06_collect'),
    ('증감(Rev) 비교       - 수량표 2개를 빼서 증/감 목록', 't07_delta'),
    ('사진대지             - 사진 폴더를 A4 엑셀 사진대지로', 't08_photo'),
    ('엑셀 서식 검사       - 숫자 표시형식 위반 칸 찾기', 't09_fmtcheck'),
    ('작업의뢰서 발행대장  - 무엇을 언제 어느 현장에 냈나', 't10_orderlog'),
    ('PLAUD 미처리 감지    - 안 돌린 회의가 남아있는지', 't11_plaudgap'),
    ('파일 정리 계획       - 어느 현장 파일인지 분류(계획만)', 't12_fileorg'),
]

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        title('KM 현장비서 도구모음')
        for i, (name, _) in enumerate(MENU, 1):
            print(' %2d. %s' % (i, name))
        print('')
        print('  0. 닫기')
        print('  9. 저장 폴더 열기')
        try:
            s = input('\n번호를 누르고 엔터 > ').strip()
        except EOFError:
            return
        if s == '0':
            return
        if s == '9':
            p = cfg('out')
            os.makedirs(p, exist_ok=True)
            os.system(('start "" "%s"' if os.name == 'nt' else 'xdg-open "%s"') % p)
            continue
        if not s.isdigit() or not (1 <= int(s) <= len(MENU)):
            continue
        mod = MENU[int(s) - 1][1]
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            m = importlib.import_module(mod)
            importlib.reload(m)
            m.run()
        except Exception:
            print('[오류] 이 화면을 그대로 클로드에게 보여주십시오.')
            traceback.print_exc()
        pause()

if __name__ == '__main__':
    main()

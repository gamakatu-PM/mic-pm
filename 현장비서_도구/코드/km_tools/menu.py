# -*- coding: utf-8 -*-
"""KM 현장비서 도구모음 - 번호 메뉴 (24종).
기존 시작.bat(PLAUD 회의록)은 건드리지 않습니다. 이것은 그 옆에 붙는 별도 런처입니다."""
import os, sys, importlib, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import title, pause, cfg, open_folder

GROUPS = [
 ('매일 아침', [
   ('아침 브리핑        오늘 결정할 것만 한 장(HTML)', 't13_brief'),
   ('오늘의 콜 카드     오래 연락 안 한 곳부터', 't14_callcard'),
   ('PLAUD 미처리 감지  안 돌린 회의가 남았는지', 't11_plaudgap')]),
 ('찾기', [
   ('회의록 검색기      전 현장에서 한 단어 찾기', 't01_search'),
   ('전화번호 사전      번호/이름으로 누구,어느 현장', 't02_phonebook')]),
 ('영업 / 견적', [
   ('객실 수량표        성급만 넣으면 물량 자동', 't03_roomqty'),
   ('CB 외함 세트 계산  WxHxD 로 속판/커버/부스바', 't04_enclosure'),
   ('견적서 채우기      수량표를 원틀에 부어넣기', 't18_quotefill'),
   ('증감(Rev) 비교     수량표 2개를 빼서 증/감', 't07_delta')]),
 ('문서 만들기', [
   ('제안서 후보+초안   자료 요청이 나온 건만', 't15_proposal'),
   ('자재사양서         원틀에 현장명만 갈아끼움', 't19_matspec'),
   ('시방서 갈아끼우기  원틀에 현장/객실수 치환', 't20_specbook'),
   ('부서 전달 메일     회의록을 부서별 초안으로', 't16_deptmail'),
   ('사진대지           사진 폴더를 A4 엑셀로', 't08_photo')]),
 ('일정 / 돈', [
   ('납기 역산 경보     준공일에서 거꾸로', 't05_schedule'),
   ('수금 레이더        미발행/입금대기 D-day', 't06_collect'),
   ('월말 계산서 집계   월별 발행/입금/미수', 't21_taxmonth')]),
 ('점검 / 정리', [
   ('엑셀 서식 검사     숫자 표시형식 위반 칸', 't09_fmtcheck'),
   ('단가장 검진        요율 하드코딩/검산/중복', 't17_pricecheck'),
   ('의뢰서 발행대장    무엇을 언제 어디에 냈나', 't10_orderlog'),
   ('파일 정리 계획     현장별 분류(계획만)', 't12_fileorg'),
   ('신규 현장 레이더   건축허가에서 새 현장', 't22_siteradar'),
   ('자가진단           고장난 데가 있는지', 't23_selfcheck'),
   ('인수인계함         클로드가 여쭌 것 / 결정 대기', 't24_handover')]),
]

def flat():
    out = []
    for _, items in GROUPS:
        out.extend(items)
    return out

def main():
    items = flat()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        title('KM 현장비서 도구모음')
        i = 0
        for gname, gitems in GROUPS:
            print('')
            print(' -- %s --' % gname)
            for name, _ in gitems:
                i += 1
                print(' %2d. %s' % (i, name))
        print('')
        print('  0. 닫기     99. 저장 폴더 열기')
        try:
            s = input('\n번호를 누르고 엔터 > ').strip()
        except EOFError:
            return
        if s == '0':
            return
        if s == '99':
            open_folder(cfg('out')); continue
        if not s.isdigit() or not (1 <= int(s) <= len(items)):
            continue
        mod = items[int(s) - 1][1]
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            m = importlib.import_module(mod)
            importlib.reload(m)
            m.run()
        except Exception:
            print('')
            print('[오류] 아래 글자를 그대로 클로드에게 보여주십시오.')
            traceback.print_exc()
        pause()

if __name__ == '__main__':
    main()

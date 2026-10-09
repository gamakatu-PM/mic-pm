# -*- coding: utf-8 -*-
"""t100_site 시험 (가짜 시트) — python t100_site_시험.py → OK"""
from __future__ import print_function
import os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t100_site as T

H = ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)']
DATA = {'valueRanges': [
    {'range': "'답요청'!A1:G10", 'values': [H,
        ['2026-09-20', 'A현장', '- 답할 것1', '', '', '', 'A현장'],
        ['', '', '- 답할 것2', '', '', '', 'A현장'],
        ['', '', '- 끝난 것', 'TRUE', '', '', 'A현장'],
        ['2026-09-21', 'A현장 리뉴얼', '- 리뉴얼 할 일', '', '', '', 'A현장 리뉴얼'],
        ['', 'B현장', '- 오늘탭과 겹침', '', '', '', 'B현장']]},
    {'range': "'오늘 할일'!A1:G10", 'values': [H,
        ['2026-10-01', 'B현장', '- 오늘탭과 겹침', '', '', '', 'B현장'],
        ['', 'A현장', '- 지난 기한', '완료', '', '', 'A현장']]},
    {'range': "'앞으로 할일'!A1:G10", 'values': [['기한'] + H[1:],
        ['2026-10-15', 'A현장', '- 다음 할 것', '', '', '', 'A현장'],
        ['2026-09-30', 'A현장', '- 기한 지난 앞으로', '', '', '', 'A현장']]},
    {'range': "'회의록'!A1:G10", 'values': [['날짜', '현장', '시각·협의자', '안건', '협의내용', '결정사항', '조치사항'],
        ['26년 10월 01일_회의 2건'],
        ['2026-10-01', 'A현장', '10:00 김 과장', '일정', '...', '10/15 납품하기로 함', ''],
        ['', 'A현장', '10:00 김 과장', '단가', '...', '없음 — 재협의', ''],
        ['2026-09-01', 'B현장', '09:00 이 부장', '옛 회의', '...', '옛 결정', '']]},
]}
TODAY = datetime.date(2026, 10, 9)
n = 0
def ok(c, m):
    global n
    n += 1
    assert c, m

todos, meets = T.load(DATA)
ok(not any(t['text'] == '끝난 것' for t in todos), '1 완료(TRUE) 뺌')
ok(not any(t['text'] == '지난 기한' for t in todos), '2 완료(「완료」) 뺌')
ok(sum(1 for t in todos if t['text'] == '오늘탭과 겹침') == 1, '3 같은 현장·같은 할 일 한 번만')
ok([t for t in todos if t['text'] == '오늘탭과 겹침'][0]['tab'] == '오늘 할일', '4 겹치면 기한 있는 쪽')
ok([t for t in todos if t['text'] == '답할 것2'][0]['date'] == datetime.date(2026, 9, 20), '5 병합 날짜 내려씀')
ok(len(meets) == 3, '6 제목줄 뺌')
ov = T.overview(todos, meets, TODAY)
ok(ov.index('A현장 —') < ov.index('B현장 —'), '7 기한 지난 것 많은 현장 먼저')
ok('기한 지남 1' in ov and '다음 10/15' in ov and '회의 10/1' in ov, '8 한 줄 숫자')
one = T.by_name('A현장', todos, meets, TODAY)
ok('2곳' in one and '■ A현장\n' in one and '■ A현장 리뉴얼' in one, '9 비슷한 이름은 따로(합치지 않음)')
ok('마지막 회의 10/1 · 10:00 김 과장' in one, '10 마지막 회의·협의자')
ok('10/15 납품하기로 함' in one and '재협의' not in one, '11 결정 있는 것만, 「없음」 뺌')
ok('기한 지난 것 1건' in one and '9/30 기한 지난 앞으로' in one, '12 기한 지난 것')
ok('다음 할 것 1건' in one and '10/15 다음 할 것' in one, '13 다음 할 것')
ok('답 안 한 것 2건' in one, '14 답요청 남은 것')
ok('없습니다' in T.by_name('없는현장', todos, meets, TODAY), '15 없는 이름')
ok('■ A현장' in T.by_name('a 현장', todos, meets, TODAY), '16 띄어쓰기·대소문자 무시')
print('OK', n)

# -*- coding: utf-8 -*-
"""t53_sheetmd 자가시험 — 2026-09-24 드라이브 read_file_content 실제 모양을 그대로 옮긴 것."""
from __future__ import print_function
import os, io, sys, json, tempfile, shutil, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t53_sheetmd as M
import t53_daily as T

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

MD = ("|  |  |  |  |  |  |  |\n| :-: | :-: | :-: | :-: | :-: | :-: | :-: |\n"
      "| 날짜 | 현장 | 할일 | 완료 | 고르기 | 메모 | 현장(걸러보기) |\n"
      "| \\[merged\\] 2026-09-22 | \\[merged\\] 수유초등학교 | \\- 맨 아래 차단기 리셋 후 동작 확인 | 완료 |  |  | 수유초등학교 |\n"
      "| \\[merged\\] 2026-09-22 | \\[merged\\] 수유초등학교 | \\- 리셋 후 무한 로딩 지속 여부 확인 |  | 진행중 | 오후에 다시 | 수유초등학교 |\n"
      "| \\[merged\\] 2026-09-22 | 양양 쏠비치 | \\- 권 매니저 방문 목적 및 요청사항 확인 |  |  |  | 양양 쏠비치 |\n"
      "| \\[merged\\] 2026-09-22 | \\[merged\\] 연합기숙사 | \\- 송내동 현장 작업 가능 여부 확인  (기한 2026-09-23) |  |  |  | 연합기숙사 |\n"
      "\n"
      "|  |  |  |  |  |  |  |\n| :-: | :-: | :-: | :-: | :-: | :-: | :-: |\n"
      "| 날짜 | 현장 | 할일 | 완료 | 고르기 | 메모 | 현장(걸러보기) |\n"
      "| \\[merged\\] 2026-09-23 | 선유도 가족호텔 | \\- 선유도 가족호텔 최종 도면안 및 내용 정리 |  |  |  | 선유도 가족호텔 |\n"
      "| \\[merged\\] 2026-09-23 | 복합회의 | \\- 납품 가능 여부 확인 |  |  |  | 복합회의 |\n"
      "\n"
      "|  |  |  |  |  |  |  |\n| :-: | :-: | :-: | :-: | :-: | :-: | :-: |\n"
      "| 날짜 | 현장 | 시각·협의자 | 안건 | 협의내용 | 결정사항 | 조치사항 |\n"
      "| \\[merged\\] 26년 09월 22일\\_회의 18건 | \\[merged\\] 26년 09월 22일\\_회의 18건 | x | x | x | x | x |\n"
      "| \\[merged\\] 46287 | 수유초등학교 | 수유초등학교 | 교실 전등 | 미점등 | 없음 | 확인 |\n"
      "\n"
      "|  |  |  |  |  |  |  |\n| :-: | :-: | :-: | :-: | :-: | :-: | :-: |\n"
      "| 기한 | 현장 | 할일 | 완료 | 고르기 | 메모 | 현장(걸러보기) |\n"
      "| \\[merged\\] 2026-09-28 | 앵커 호텔 | \\- 제본용 최종 도면 출력소 의뢰 여부 확인 |  | 만들어줘 |  | 앵커 호텔 |\n"
      "| 2026-10-06 | 앵커 호텔 | \\- 16층\\~11층 일정 의미 및 작업 가능 여부 확인 |  |  |  | 앵커 호텔 |\n"
      "| 2026-09-30 | \\_현장미정 | \\- 설계 완료 마무리 | 완료 |  |  | \\_현장미정 |\n")

d = tempfile.mkdtemp()
try:
    src = os.path.join(d, 'r.json')
    io.open(src, 'w', encoding='utf-8').write(json.dumps({'fileContent': MD}, ensure_ascii=False))
    counts, paths = M.run(src, os.path.join(d, 'o'))
    print('--- 표 가르기')
    chk('탭 4개 찾음', set(paths) == {'답요청', '오늘 할일', '회의록', '앞으로 할일'}, paths)
    chk('줄 수 (머리 뺌)', counts == {'답요청': 4, '오늘 할일': 2, '회의록': 2, '앞으로 할일': 3}, counts)
    a = json.load(io.open(paths['답요청'], encoding='utf-8'))
    chk('머리 줄', a['values'][0][:4] == ['날짜', '현장', '할일', '완료'])
    chk('[merged] 떼고 값 채움', a['values'][1][:2] == ['2026-09-22', '수유초등학교'], a['values'][1])
    chk('\\- → - (할일 앞 「- 」 그대로)', a['values'][1][2] == '- 맨 아래 차단기 리셋 후 동작 확인', a['values'][1][2])
    chk('체크 「완료」 · ▼ · 메모 읽음', a['values'][1][3] == '완료' and a['values'][2][4] == '진행중' and a['values'][2][5] == '오후에 다시')
    f = json.load(io.open(paths['앞으로 할일'], encoding='utf-8'))
    chk('\\~ · \\_ 되돌림', f['values'][2][2] == '- 16층~11층 일정 의미 및 작업 가능 여부 확인' and f['values'][3][1] == '_현장미정', f['values'][2:])
    print('--- t53 에 그대로 먹이기')
    board = T.load_board(','.join([paths['답요청'], paths['오늘 할일'], paths['앞으로 할일']]))
    chk('load_board 가 탭을 제대로 앎', sorted(set(b['tab'] for b in board)) == ['답요청', '앞으로 할일', '오늘 할일'], set(b['tab'] for b in board))
    dn = T._done_of(board)
    chk('체크 2건 (답요청 1 · 앞으로 1)', len(dn['pair']) == 2, dn)
    pm = T.pick_map(board)
    chk('▼ 2건 (진행중 · 만들어줘)', sorted(v[0] for v in pm.values()) == ['만들어줘', '진행중'], pm)
    chk('기한 : 답요청은 글 끝, 앞으로 할일은 A열', any(b['due'] == '2026-09-23' and b['tab'] == '답요청' for b in board) and any(b['due'] == '2026-09-28' for b in board))
finally:
    shutil.rmtree(d, ignore_errors=True)
print('\n통과 %d / 실패 %d %s' % (OK[0], len(NG), NG or ''))
sys.exit(1 if NG else 0)

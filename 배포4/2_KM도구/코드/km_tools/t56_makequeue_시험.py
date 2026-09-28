# -*- coding: utf-8 -*-
"""56. t56_makequeue 자가시험 — 「만들 차례」 탭 값 → 실제 파일."""
from __future__ import print_function
import os, sys, io, json, shutil, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t56_makequeue as T

OK = 0
NG = []


def chk(name, cond, why=''):
    global OK
    if cond:
        OK += 1
        print('  OK   ' + name)
    else:
        NG.append(name)
        print('  NG   ' + name + '  ' + str(why))


HEAD = ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)', '원본탭', '처리일', '생성결과']

PAYLOAD = {'ok': True, 'valueRanges': [{'range': "'만들 차례'!A1:J10", 'values': [
    HEAD,
    ['2026-09-27', '수유초등학교', '- 화재 감지기 재설치', '', '작업의뢰서', '', '수유초등학교', '답요청', '2026-09-28', ''],
    ['2026-09-28', '양양 쏠비치', '- 견적 재확인 메일 보내기', '', '메일', '', '양양 쏠비치', '오늘 할일', '2026-09-28', ''],
    ['2026-09-28', '단양디캠프', '- 이번 주 진행 상황 정리', '', '보고서', '', '단양디캠프', '오늘 할일', '2026-09-28', ''],
    ['2026-09-28', '앵커 호텔', '- 제안 범위 넓혀서 다시', '', '제안서', '', '앵커 호텔', '오늘 할일', '2026-09-28', ''],
    ['2026-09-27', '연합기숙사', '- 이미 만든 것', '', '메일', '', '연합기숙사', '답요청', '2026-09-28', '만듦 · 옛파일.txt'],  # 이미 만듦(J열 있음) → 건너뜀
]}]}

print('--- parse : 대상 골라내기')
rows = T.rows_of(PAYLOAD)
items = T.parse(rows)
chk('4건만 골라냄 (이미 만든 줄 제외)', len(items) == 4, len(items))
chk('행 번호 = 인덱스+2 (헤더 다음이 2행)', items[0]['row'] == 2, items[0])
chk('할일 글 앞 「- 」 는 뗀다', items[0]['task'] == '화재 감지기 재설치', items[0]['task'])
chk('제안서도 목록엔 들어감(run 에서 건너뜀)', any(i['pick'] == '제안서' for i in items))

print('--- run : 실제 파일 생성')
tmp = tempfile.mkdtemp(prefix='km_t56_')
try:
    rep = T.run(PAYLOAD, out_root=tmp, today='260928')
    chk('결과에 tab 키 있음 (그대로 markqueue 에 먹일 수 있게)', rep.get('tab') == '만들 차례', rep.get('tab'))
    chk('제안서는 대기 1건으로만 세고 안 만듦', rep['제안서대기'] == 1, rep['제안서대기'])
    chk('만든 것 3건(작업의뢰서·메일·보고서)', len(rep['made']) == 3, len(rep['made']))
    chk('marks 도 3건 (제안서는 표시 안 함 → 다음에도 또 뜸)', len(rep['marks']) == 3, rep['marks'])

    wo = [m for m in rep['made'] if m['pick'] == '작업의뢰서'][0]
    mail = [m for m in rep['made'] if m['pick'] == '메일'][0]
    rpt = [m for m in rep['made'] if m['pick'] == '보고서'][0]

    chk('작업의뢰서 파일이 실제로 생김', os.path.isfile(wo['path']), wo)
    chk('메일초안 파일이 실제로 생김', os.path.isfile(mail['path']), mail)
    chk('보고서 파일이 실제로 생김', os.path.isfile(rpt['path']), rpt)

    if os.path.isfile(mail['path']):
        body = io.open(mail['path'], encoding='utf-8').read()
        chk('메일초안 본문에 현장·할일 글이 그대로 있음(지어내지 않음)', '양양 쏠비치' in body and '견적 재확인 메일 보내기' in body, body)
    if os.path.isfile(rpt['path']):
        body = io.open(rpt['path'], encoding='utf-8').read()
        chk('보고서 본문에 현장·할일 글이 그대로 있음', '단양디캠프' in body and '이번 주 진행 상황 정리' in body, body)

    if rep['template'] and os.path.isfile(wo['path']):
        import openpyxl
        wb = openpyxl.load_workbook(wo['path'])
        ws = wb.worksheets[0]
        chk('작업의뢰서 : 현장(E12)이 채워짐', ws['E12'].value == '수유초등학교', ws['E12'].value)
        chk('작업의뢰서 : G4 = 배성윤', ws['G4'].value == '배성윤', ws['G4'].value)
        chk('작업의뢰서 : 본문 B19 에 할일 글', '화재 감지기' in str(ws['B19'].value or '') or '화재 감지기' in str(ws['B20'].value or ''), ws['B19'].value)
        chk('작업의뢰서 : O4(납기일) 는 비워 둠(차장님 몫)', ws['O4'].value in (None, ''), ws['O4'].value)
    else:
        print('  (참고) 원틀을 못 찾아 작업의뢰서 xlsx 자체 시험은 건너뜀 — 파일 있으면 위에서 이미 통과')

    print('--- 두 번째 실행 : 덮어쓰지 않음(이미 있음)')
    rep2 = T.run(PAYLOAD, out_root=tmp, today='260928')
    states = set(m['state'] for m in rep2['made'])
    chk('두 번째는 전부 「이미 있음」', states == {'이미 있음'} or states == {'이미 있음', '원틀 없음 — 만들지 않음'}, states)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('\n합계 %d개 중 통과 %d · 실패 %d' % (OK + len(NG), OK, len(NG)))
if NG:
    print('실패 : ' + ', '.join(NG))
    sys.exit(1)

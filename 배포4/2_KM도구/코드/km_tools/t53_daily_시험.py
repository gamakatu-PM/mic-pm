# -*- coding: utf-8 -*-
"""53번 자가시험. 통과해야 도구를 드린다."""
from __future__ import print_function
import os, io, sys, json, shutil, tempfile, datetime, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t53_daily as T

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

def meta(site, ymd, person='홍길동 부장', company='일능', name='홍길동', rank='부장',
         items=None, todo=None, sched=None, hm='10:00'):
    return {'meta': {'site': site, 'ymd': ymd, 'hm': hm, 'person': person, 'company': company,
                     'name': name, 'rank': rank},
            'sec': {'1': {'현장': site, '안건목록': items or [], '일정': sched or ['- 없음']},
                    '2': {'할 일': todo or []}}}

def write(d, name, obj):
    p = os.path.join(d, name)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False))
    return p

TODAY = datetime.date(2026, 9, 23)
d = tempfile.mkdtemp()
try:
    it = lambda t, b, dec, a: {'title': t, 'bullets': b, 'decision': dec, 'actions': a}
    # 어제(9/22) 회의 3건 : 앵커 호텔 2건(띄어쓰기 다름) + 수유초 1건(회사=이름 자료)
    write(d, 'a__meta.json', meta('앵커 호텔', '260922', hm='09:00',
          items=[it('회로도 구성', ['냉장고·비데·세면대 회로 구성 협의함', '기존 도면상 확인'],
                    '없음 — 회로도 구성 확인 후 재협의 예정', ['한국마이크로닉 · 회로도 구성 재확인'])],
          todo=['- 260923 | 회로도 제출 | 배성윤 → 김경원 상무', '- 미정 | 샘플 발송 | 배성윤 → 현장']))
    write(d, 'b__meta.json', meta('앵커호텔', '260922', hm='14:00', person='박철수 대리', name='박철수', rank='대리',
          items=[it('단가', ['센서 단가 언급'], '', [])],
          todo=['- 260923 | 회로도 제출 | 배성윤 → 김경원 상무',   # a 와 같은 할 일 → 한 번만
                '- 261001 | 계약서 제출 | 배성윤 → 발주처']))
    write(d, 'c__meta.json', meta('수유초등학교', '260922', hm='', person='수유초등학교', company='수유초', name='등학교', rank='',
          items=[it('무한로딩', ['무한 로딩 발생'], '없음 — 리셋 후 확인', ['리셋'])],
          todo=['- 미정 | 차단기 리셋 후 동작 확인 | 배성윤 → 확인 예정', '=========='],
          sched=['- 설치 | 260923 | 수업 끝나고 방문']))
    # 어제 아닌 것 : 9/21 복합회의(현장이 아닌 것) 에 오늘 기한 할 일, 9/20 지난 기한
    write(d, 'd__meta.json', meta('복합회의', '260921', hm='17:26', person='김경원 상무', name='김경원', rank='상무',
          items=[it('센서', ['센서 40,000 → 80,000 언급'], '없음', [])],
          todo=['- 260923 | 센서 단가 회신 | 배성윤 → 김경원 상무', '- 260917 | 도면 발송 | 배성윤 → 부천대']))
    write(d, 'e__meta.json', meta('제천', '260920', hm='11:00', person='최영희 과장', name='최영희', rank='과장',
          items=[it('일정', ['설치 일정'], '', [])], todo=['- 260917 | 도면 발송 | 배성윤 → 발주처']))
    write(d, '_삭제요망_x__meta.json', meta('부천대', '260922', items=[it('x', ['x'], '', [])], todo=['- 260923 | 지워야 함 | 배성윤 → x']))

    (t1, t2, t3), st = T.run(d, TODAY, out=os.path.join(d, 'out'),
                             sheet_url='https://docs.google.com/spreadsheets/d/SHEET')

    print('--- 기본')
    chk('어제 회의 3건', st['어제회의'] == 3, st)
    chk('삭제요망 제외', st['meta전체'] == 5, st['meta전체'])
    chk('파일 4개 + json', all(os.path.exists(p) for p in st['파일'].values()) and
        os.path.exists(os.path.join(d, 'out', '아침3통_260923.json')))

    print('--- ① 답해 주십시오 (하루치 줄 + 시트 링크, 그 밖의 말 없음)')
    chk('시트 링크 있음', '26년 회의록2 : https://docs.google.com/spreadsheets/d/SHEET' in t1)
    chk('어제 할 일만 4건 (같은 할 일 1번)', st['①할일'] == 4, st['①할일'])
    chk('9/21 복합회의 할 일은 ① 에 없음', '센서 단가 회신' not in t1)
    chk('「N일 지남」·설명문 없음', '지남' not in t1 and '완료한 것은' not in t1 and '하루치' not in t1)
    chk('v6 날짜 머리줄 한 번 → 현장 머리줄 → 할일 들여쓰기 (기한·담당은 글 끝에)',
        t1.startswith('2026-09-22\n\n수유초등학교\n  - 차단기 리셋 후 동작 확인\n\n앵커 호텔\n  - 회로도 제출  (기한 2026-09-23)\n'), t1)
    chk('v9 ① 은 「- 」 로 시작 · 담당 괄호 없음 · 기한 괄호는 남음',
        '(확인 예정)' not in t1 and '(김경원 상무)' not in t1 and '(현장)' not in t1 and '(기한 2026-10-01)' in t1 and
        all(ln.startswith('  - ') for ln in t1.split('\n') if ln.startswith('  ')), t1)
    chk('v6 날짜·현장은 한 번만', t1.count('2026-09-22\n') == 1 and t1.count('앵커 호텔\n') == 1 and '\t' not in t1, t1)
    chk('기한 없으면 (기한) 안 붙임', '\n  - 샘플 발송\n' in t1, t1)
    chk('종류 칸 없음', '\t발송\t' not in t1 and '\t제출\t' not in t1)
    chk('현장명 띄어쓰기 그대로 (앵커 호텔)', '앵커 호텔' in t1 and '앵커호텔' not in t1)
    rows = list(csv.DictReader(io.open(st['파일']['할일추가'], encoding='utf-8-sig')))
    chk('csv 머리 4칸 (날짜·현장·할일·완료)', list(rows[0].keys()) == ['날짜', '현장', '할일', '완료'], list(rows[0].keys()))
    chk('csv 줄 수 = ① 건수', len(rows) == st['①할일'])
    chk('csv 날짜 = 회의한 날 2026-09-22, 빈칸 없음', all(r['날짜'] == '2026-09-22' for r in rows), [r['날짜'] for r in rows])
    chk('csv 완료 칸 비어 있음', all(r['완료'] == '' for r in rows))

    print('--- ② 오늘 할 것 (오늘 날짜 할 일만)')
    chk('오늘 2건 (회로도 제출·센서 회신)', st['②오늘'] == 2, st['②오늘'])
    chk('지난 기한(9/17 도면 발송) 없음', '도면 발송' not in t2)
    chk('미정 없음', '샘플 발송' not in t2)
    chk('일정 칸은 안 잡음', '수업 끝나고 방문' not in t2)
    chk('출처·설명문 없음', '회의 17:26' not in t2 and '지난 것은' not in t2)
    chk('복합회의 할 일을 다른 현장으로 안 옮김', '\n복합회의\n  - 센서 단가 회신' in t2 and '부천대' not in t2 and '제천' not in t2, t2)
    chk('v10 ② 줄 모양 (날짜 한 번 → 현장 → 「- 」, 담당 괄호 없음, 현장이 아닌 것은 뒤)', t2.startswith('2026-09-23\n\n앵커 호텔\n  - 회로도 제출\n') and t2.index('앵커 호텔') < t2.index('복합회의') and t2.count('2026-09-23') == 1 and '(김경원 상무)' not in t2, t2)

    print('--- ③ 어제 있었던 일 (차장님 모양 그대로)')
    chk('머리말·꼬리말 없음', not t3.startswith('어제') and 't53' not in t3 and '회의 3건' not in t3)
    chk('현장 번호만 (건수 안 붙임)', '1. 앵커 호텔\n' in t3 and '2. 수유초등학교\n' in t3 and '회의 2건' not in t3)
    chk('현장별 건수 정확 (앵커 2 · 수유초 1)', st['어제_현장별'] == {'앵커 호텔': 2, '수유초등학교': 1}, st['어제_현장별'])
    chk('날짜 시각 사람이름 줄', '9/22   09:00  일능 홍길동 부장' in t3 and '9/22   14:00  일능 박철수 대리' in t3)
    chk('회사=이름 자료도 이름 나옴', '9/22   수유초등학교' in t3 and '상대 미상' not in t3)
    chk('안건마다 날짜 사람 → 빈 줄 → 안건/협의내용/결정사항/조치사항',
        '9/22   09:00  일능 홍길동 부장\n\n안건 : 회로도 구성\n협의내용 : 냉장고·비데·세면대 회로 구성 협의함\n기존 도면상 확인\n결정사항 : 없음 — 회로도 구성 확인 후 재협의 예정\n조치사항 : 한국마이크로닉 · 회로도 구성 재확인\n' in t3, t3)
    chk('협의내용 둘째 줄부터는 줄바꿈 (/ 로 안 잇는다)', '협의함 / 기존' not in t3)
    chk('결정 없으면 「없음」', '결정사항 : 없음\n' in t3)
    chk('9/21·9/20 회의는 ③ 에 없음', '센서 40,000' not in t3 and '제천' not in t3)
    chk('회신 요청 사항 안 적음', '회신 요청' not in t3)

    print('--- v4 한 통 · 시트 3탭')
    one = io.open(st['파일']['오늘의정리'], encoding='utf-8').read()
    chk('제목', st['제목'] == '[KM] 오늘의 정리 입니다. 2026-09-23 (수)', st['제목'])
    chk('한 통 순서 ①→②→③', one.index('━━ 1. 답해 주십시오') < one.index('━━ 2. 오늘 할 것') < one.index('━━ 3. 어제 있었던 일'))
    chk('링크는 맨 위 한 번', one.startswith('26년 회의록2 : https://docs.google.com/spreadsheets/d/SHEET') and one.count('26년 회의록2 :') == 1)
    chk('③ 머리 「26년 09월 22일_회의 3건」', '━━ 3. 어제 있었던 일 ━━  26년 09월 22일_회의 3건' in one)
    chk('① ② ③ 본문이 다 들어감', t1.split('\n')[0] in one and t2.split('\n')[0] in one and '1. 앵커 호텔' in one)
    chk('시트줄 수', st['시트줄'] == {'답요청': 4, '오늘 할일': 2, '회의록': 4, '앞으로 할일': 1}, st['시트줄'])
    rj = json.load(io.open(st['파일']['시트_회의록'], encoding='utf-8'))['rows']
    chk('회의록 탭 첫 줄 = 날짜 제목', rj[0] == {'COL$A': '26년 09월 22일_회의 3건'}, rj[0])
    chk('회의록 탭 줄 = 안건 하나', rj[1]['COL$D'] == '회로도 구성' and rj[1]['COL$E'] == '냉장고·비데·세면대 회로 구성 협의함\n기존 도면상 확인', rj[1])
    tj = json.load(io.open(st['파일']['시트_오늘 할일'], encoding='utf-8'))['rows']
    chk('오늘 할일 탭 날짜 = 오늘', all(r['COL$A'] == '2026-09-23' for r in tj))
    plan = json.load(io.open(st['파일']['시트계획'], encoding='utf-8'))
    mb = T.merge_body(plan, {'답요청': '8-11', '오늘 할일': "'오늘 할일'!A2:D3", '회의록': '2-6'})['requests']
    chk('병합 : 답요청 A8:A11', {'mergeCells': {'range': {'sheetId': 0, 'startRowIndex': 7, 'endRowIndex': 11, 'startColumnIndex': 0, 'endColumnIndex': 1}, 'mergeType': 'MERGE_ALL'}} in mb)
    mg = [x['mergeCells']['range'] for x in mb if 'mergeCells' in x]
    chk('병합 : 회의록 제목줄 A2:G2', {'sheetId': 2, 'startRowIndex': 1, 'endRowIndex': 2, 'startColumnIndex': 0, 'endColumnIndex': 7} in mg, mg)
    chk('병합 : 회의록 날짜 A3:A6', {'sheetId': 2, 'startRowIndex': 2, 'endRowIndex': 6, 'startColumnIndex': 0, 'endColumnIndex': 1} in mg, mg)
    chk('v6 병합 : 답요청 현장 B9:B11 (수유초 1줄은 안 합침, 앵커 호텔 3줄)',
        {'sheetId': 0, 'startRowIndex': 8, 'endRowIndex': 11, 'startColumnIndex': 1, 'endColumnIndex': 2} in mg and
        not any(r['sheetId'] == 0 and r['startColumnIndex'] == 1 and r['startRowIndex'] == 7 for r in mg), mg)
    chk('v6 회의록 탭은 현장 칸 병합 안 함', not any(r['sheetId'] == 2 and r['startColumnIndex'] == 1 for r in mg), mg)
    chk('v6 오늘 할일 현장 다르면 B 병합 없음', not any(r['sheetId'] == 1 and r['startColumnIndex'] == 1 for r in mg), mg)
    aj = json.load(io.open(st['파일']['시트_답요청'], encoding='utf-8'))['rows']
    chk('v6 시트 줄 순서 = 메일 순서 (같은 현장이 붙어 있음)', [r['COL$B'] for r in aj] == ['수유초등학교', '앵커 호텔', '앵커 호텔', '앵커 호텔'], [r['COL$B'] for r in aj])
    one_row = T.merge_body(plan, {'답요청': '5-5'})['requests']
    chk('한 줄뿐이면 병합 안 함 (날짜 서식 · 체크박스만)', [list(x)[0] for x in one_row] == ['repeatCell', 'setDataValidation', 'setDataValidation', 'repeatCell'], one_row)
    cb = [x['setDataValidation'] for x in mb if 'setDataValidation' in x and x['setDataValidation']['rule']['condition']['type'] == 'BOOLEAN']
    chk('v8 완료 칸 체크박스 : 답요청 D8:D11 · 오늘 할일 D2:D3, 회의록 탭은 없음',
        [(c['range']['sheetId'], c['range']['startRowIndex'], c['range']['endRowIndex'], c['range']['startColumnIndex']) for c in cb] == [(0, 7, 11, 3), (1, 1, 3, 3)], cb)
    chk('v8 체크 값 = 「완료」', cb[0]['rule']['condition'] == {'type': 'BOOLEAN', 'values': [{'userEnteredValue': '완료'}]})

    print('--- v5 레이더 합치기')
    rad = {'results': [{'body': {'valueRanges': [
        {'range': "'구글AI_실행로그'!A1:G2000", 'values': [['실행일시'], ['2026. 9. 22 오전 6:40:48', '일일', '0', '0', '0', '0', 'x: Error: {"message":"models/gemini-3.1-pro is not found"}'],
                    ['2026. 9. 23 오전 6:40:51', '일일', '0', '0', '0', '0', 'a: Error: {"message":"models/gemini-3.1-pro is not found"} / b: Error: {"message":"models/gemini-3.1-pro is not found"}']]},
        {'range': "'구글AI_백필_확정'!A1:M5000", 'values': [['수집일시']]}, {'range': "'구글AI_백필_재검토필요'!A1:F1000", 'values': [['수집일시']]}]}}]}
    rp = os.path.join(d, 'radar.json')
    with io.open(rp, 'w', encoding='utf-8') as f:
        f.write(json.dumps(rad, ensure_ascii=False))
    (_a, _b, _c), st5 = T.run(d, TODAY, out=os.path.join(d, 'out5'), sheet_url='https://SHEET', radar_path=rp)
    one5 = io.open(st5['파일']['오늘의정리'], encoding='utf-8').read()
    chk('4번 칸이 ③ 뒤에', one5.index('━━ 3. 어제 있었던 일') < one5.index('━━ 4. 신규 현장 레이더'))
    chk('오늘 실행만 (9/23)', '실행 2026. 9. 23 오전 6:40:51 · 확정 0건 · 재검토 0건' in one5, one5[-300:])
    chk('오류면 「못 찾은 것」 이라고 밝힘', '검색 2곳 모두 오류' in one5 and '모델 없음 : gemini-3.1-pro' in one5)
    chk('레이더 통계', st5['레이더'] == {'실행': 1, '확정': 0, '재검토': 0, '오류': 2}, st5['레이더'])
    rad['results'][0]['body']['valueRanges'][1]['values'].append(['2026. 9. 23 오전 6:40:51', '일일', '서울', '중구', '착공', '가나호텔', '300실', 'A사', 'B건설', 'C설계', '요약글', 'http://x', '호텔신축_서울'])
    rad['results'][0]['body']['valueRanges'][0]['values'][-1][6] = ''
    with io.open(rp, 'w', encoding='utf-8') as f:
        f.write(json.dumps(rad, ensure_ascii=False))
    t4, s4 = T.build_radar(T.load_radar(rp), TODAY)
    chk('확정 현장 적힘', '가나호텔  (서울 · 중구)' in t4 and '발주처 : A사 · 시공사 : B건설 · 설계 : C설계' in t4 and '못 찾은' not in t4, t4)
    chk('레이더 없으면 칸 없음', '━━ 4.' not in one)
    # 파일 3개로 나눠 줘도 같다
    parts = []
    for i, vr in enumerate(rad['results'][0]['body']['valueRanges']):
        pp = os.path.join(d, 'r%d.json' % i)
        with io.open(pp, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'results': [{'body': vr}]}, ensure_ascii=False))
        parts.append(pp)
    chk('파일 3개로 나눠도 같음', T.build_radar(T.load_radar(','.join(parts)), TODAY) == (t4, s4))
    chk('어제 실행만 있으면', '(오늘 레이더 실행 기록 없음)' in T.build_radar(T.load_radar(rp), datetime.date(2026, 9, 25))[0])

    print('--- 현장이 아닌 것 이 어제 있을 때')
    write(d, 'f__meta.json', meta('복합회의', '260922', hm='16:00', person='이순신 이사', name='이순신', rank='이사',
          items=[it('여러 현장', ['부천대·제천 얘기'], '', [])], todo=['- 미정 | 부천대 확인 | 배성윤 → x']))
    (u1, u2, u3), st2 = T.run(d, TODAY, out=os.path.join(d, 'out2'))
    chk('③ 따로 절', '※ 현장이 아닌 것 — 어느 현장 것인지는 차장님이 정하십시오' in u3)
    chk('③ 현장 2개 뒤에 3번으로', '3. 복합회의\n' in u3 and st2['어제_현장별'].get('복합회의') == 1)
    chk('① 도 현장명 그대로 (귀속 안 함)', '\n복합회의\n  - 부천대 확인' in u1)
    chk('v6 ① 현장이 아닌 것은 맨 뒤', u1.index('앵커 호텔') < u1.index('복합회의'), u1)

    print('--- 기간 지정')
    (g1, g2), gs = T.run_range(d, '260920', '260922', out=os.path.join(d, 'o4'), sheet_url='https://SHEET')
    chk('기간 안 회의 6건 (9/20 제천 · 9/21 복합 · 9/22 앵커2·수유초·복합)', gs['회의'] == 6, gs['회의'])
    chk('현장별 건수', gs['현장별'] == {'앵커 호텔': 2, '수유초등학교': 1, '제천': 1, '복합회의': 2}, gs['현장별'])
    chk('③ 모양 그대로', '1. 앵커 호텔\n\n9/22   09:00  일능 홍길동 부장\n\n안건 : 회로도 구성' in g1, g1[:200])
    chk('현장이 아닌 것 절', '※ 현장이 아닌 것' in g1 and '복합회의' in g1)
    chk('기간 할 일 (회의한 날짜 머리줄 → 현장 → 들여쓰기)', g2.startswith('2026-09-20\n\n제천\n  도면 발송  (기한 2026-09-17)') and '\n\n2026-09-21\n\n복합회의\n' in g2 and '26년 회의록2 : https://SHEET' in g2, g2)
    chk('기간 파일 4개', all(os.path.exists(x) for x in gs['파일'].values()) and os.path.exists(os.path.join(d, 'o4', '기간_260920-260922.json')))
    chk('--month 범위', T._month_range('2609') == ('260901', '260930') and T._month_range('2602') == ('260201', '260228') and T._month_range('2612') == ('261201', '261231'))
    chk('기간 밖이면 비어 있음', '회의록 없음' in T.run_range(d, '261001', '261031', out=os.path.join(d, 'o5'))[0][0])

    print('--- v7 「배성윤 →」 빼기 · 시트 완료 표시는 ①② 에서 뺌')
    chk('「배성윤 →」 없음', '배성윤' not in t1 and '배성윤' not in t2)
    chk('_whom', T._whom('배성윤 → 김경원 상무') == '김경원 상무' and T._whom('배성윤->AS') == 'AS' and T._whom('배성윤') == '' and T._whom('김경원 → 배성윤') == '김경원 → 배성윤')
    dj = write(d, 'done_a.json', {'results': [{'status': 200, 'body': {'range': "'답요청'!A1:D200", 'values': [
        ['날짜', '현장', '할일', '완료'],
        ['46287', '앵커호텔', '샘플 발송  (배성윤 → 현장)', '완료'],        # 옛 글꼴(배성윤 →) · 띄어쓰기 다른 현장명도 맞춘다
        ['', '', '계약서 제출  (기한 2026-10-01)  (발주처)', ''],          # 병합 칸 : 현장 빈칸 → 위 값
        ['', '', '회로도 제출', 'FALSE'],                                  # 체크 안 함
        ['', '제천', '차단기 리셋 후 동작 확인', '완료']]}}]})            # 현장이 다르면 안 뺀다
    dt = write(d, 'done_t.json', {'range': "'오늘 할일'!A1:D50", 'values': [
        ['날짜', '현장'], ['2026-09-23', '복합회의', '센서 단가 회신  (x)', 'TRUE']]})
    dn = T.load_done(dj + ',' + dt)
    chk('완료 3건 읽음 (FALSE·빈칸 제외)', len(dn['pair']) == 3, dn)
    (v1, v2, _v3), sv = T.run(d, TODAY, out=os.path.join(d, 'out7'), done_path=dj + ',' + dt)
    chk('① 완료한 「샘플 발송」 빠짐', '샘플 발송' not in v1 and '계약서 제출' in v1 and '회로도 제출' in v1, v1)
    chk('① 현장이 다르면 안 뺌 (수유초 차단기 남음)', '차단기 리셋 후 동작 확인' in v1, v1)
    chk('② 완료한 「센서 단가 회신」 빠짐, 회로도 남음', '센서 단가 회신' not in v2 and '회로도 제출' in v2, v2)
    chk('완료로 뺀 수 = 2', sv['완료로뺌'] == 2, sv['완료로뺌'])
    aj7 = json.load(io.open(sv['파일']['시트_답요청'], encoding='utf-8'))['rows']
    chk('시트 답요청에도 완료한 것 안 넣음', not any('샘플 발송' in r.get('COL$C', '') for r in aj7) and len(aj7) == st2['①할일'] - 1, aj7)
    chk('--done 없으면 그대로', T.run(d, TODAY, out=os.path.join(d, 'out8'))[1]['①할일'] == st2['①할일'])
    chk('--done 파일 없으면 멈추지 않음', T.run(d, TODAY, out=os.path.join(d, 'out9'), done_path=os.path.join(d, '없음.json'))[1]['①할일'] == st2['①할일'])

    print('--- v9 ① 만 바뀜 (② · 시트 · 기간 메일은 그대로)')
    chk('v10 ② 도 「- 」 · 담당 괄호 없음', '\n  - 회로도 제출\n' in t2 and '(김경원 상무)' not in t2, t2)
    sj = json.load(io.open(st['파일']['시트_답요청'], encoding='utf-8'))['rows']
    chk('v10 시트 답요청 글 = 「- 」 + 기한만 (담당 괄호 없음)', any(r.get('COL$C') == '- 회로도 제출  (기한 2026-09-23)' for r in sj) and all(r['COL$C'].startswith('- ') for r in sj), sj)
    tj10 = json.load(io.open(st['파일']['시트_오늘 할일'], encoding='utf-8'))['rows']
    chk('v10 시트 오늘 할일 글 = 「- 」 + 무엇', [r['COL$C'] for r in tj10] == ['- 회로도 제출', '- 센서 단가 회신'], tj10)
    chk('v10 csv 도 시트와 같음', [r['할일'] for r in rows] == [r['COL$C'] for r in sj], ([r['할일'] for r in rows], sj))
    chk('sheet_text : 옛 글 고치기', T.sheet_text('회로도 제출  (기한 2026-09-23)  (배성윤 → 김경원 상무)') == '- 회로도 제출  (기한 2026-09-23)' and T.sheet_text('샘플 발송  (배성윤 → 현장)') == '- 샘플 발송' and T.sheet_text('- 샘플 발송') == '- 샘플 발송' and T.sheet_text('') == '')
    chk('v10 완료 대조 : 「- 」 붙은 시트 글도 맞춤', T._core('- 샘플 발송  (기한 2026-09-23)') == '샘플 발송')
    chk('csv 는 4칸 그대로 (_메일 안 들어감)', list(rows[0].keys()) == ['날짜', '현장', '할일', '완료'])
    chk('기간 메일 할 일은 그대로 (들여쓰기 두 칸 · 담당 괄호 있음)', '\n  도면 발송  (기한 2026-09-17)  (발주처)' in g2 and '  - ' not in g2, g2)

    print('--- v11 체크 안 한 것은 계속 · ⑤ 앞으로 할 것 · 앞으로 할일 탭')
    bj = write(d, 'b_a.json', {'range': "'답요청'!A1:D50", 'values': [
        ['날짜', '현장', '할일', '완료'],
        ['2026-09-20', '제천', '- 옛 확인 일', ''],                              # ① 에 이어짐 (기한 없음 · 체크 안 함)
        ['', '', '- 옛 끝난 일', '완료'],                                        # 체크 → 안 나옴
        ['', '', '- 지난 기한 일  (기한 2026-09-21)', ''],                        # ② 원래 기한 9/21 아래
        ['', '', '- 먼 일  (기한 2026-10-15)', '']]})                            # ⑤
    bt = write(d, 'b_t.json', {'range': "'오늘 할일'!A1:D50", 'values': [
        ['날짜', '현장', '할일', '완료'], ['46287', '제천', '- 어제 못 한 일', '']]})   # 숫자 날짜 = 2026-09-22 → ② 9/22 아래
    bf = write(d, 'b_f.json', {'range': "'앞으로 할일'!A1:D50", 'values': [
        ['기한', '현장', '할일', '완료'],
        ['2026-09-23', '제천', '- 오늘 된 일', ''],                              # 오늘이 됨 → ② 오늘
        ['2026-10-01', '앵커 호텔', '- 계약서 제출', ''],                          # 이미 탭에 있음 → 새로 안 붙임
        ['2026-11-01', '제천', '- 체크한 먼 일', '완료']]})                        # 체크 → ⑤ 에 안 나옴
    (w1, w2, _w3), sw = T.run(d, TODAY, out=os.path.join(d, 'out11'), done_path=','.join([bj, bt, bf]))
    one11 = io.open(sw['파일']['오늘의정리'], encoding='utf-8').read()
    chk('숫자 날짜 46287 = 2026-09-22', T._cell_date('46287') == '2026-09-22' and T._cell_date('2026-09-22') == '2026-09-22')
    chk('① 체크 안 한 지난 할 일 (회의한 날 아래)', '2026-09-20\n\n제천\n  - 옛 확인 일\n' in w1 and '옛 끝난 일' not in w1 and sw['①지난것'] == 1, w1)
    chk('① 기한 있는 지난 것은 ① 에 안 넣음', '지난 기한 일' not in w1 and '먼 일' not in w1, w1)
    chk('② 기한 지난 것 = 원래 기한 아래, 오늘 것은 맨 뒤',
        w2.startswith('2026-09-21\n\n제천\n  - 지난 기한 일\n\n2026-09-22\n\n제천\n  - 어제 못 한 일\n\n2026-09-23\n') and sw['②기한지난것'] == 2, w2)
    chk('② 앞으로 할일 탭에서 오늘이 된 것', '  - 오늘 된 일' in w2 and '(기한' not in w2, w2)
    chk('머리 줄 숫자', '체크 안 한 지난 할 일 1건' in one11 and '기한 지난 것 2건' in one11, one11[:400])
    t5 = one11.split('━━ 5. 앞으로 할 것 ━━')[1] if '━━ 5. 앞으로 할 것 ━━' in one11 else ''
    chk('⑤ 메일 맨 끝 (④ 다음)', one11.index('━━ 5. 앞으로 할 것') > one11.index('━━ 3. 어제 있었던 일') and sw['⑤앞으로'] == 2, sw['⑤앞으로'])
    chk('⑤ 기한 순 · 기한 머리 · 「- 」', '2026-10-01\n\n앵커 호텔\n  - 계약서 제출\n\n2026-10-15\n\n제천\n  - 먼 일' in t5, t5)
    chk('⑤ 체크한 것 · 오늘 것은 없음', '체크한 먼 일' not in t5 and '오늘 된 일' not in t5, t5)
    fj = json.load(io.open(sw['파일']['시트_앞으로 할일'], encoding='utf-8'))['rows']
    chk('앞으로 할일 탭 = 새로 생긴 것만 (이미 있는 계약서 제출 제외)', fj == [{'COL$A': '2026-10-15', 'COL$B': '제천', 'COL$C': '- 먼 일', 'COL$G': '제천'}], fj)
    oj = json.load(io.open(sw['파일']['시트_오늘 할일'], encoding='utf-8'))['rows']
    chk('오늘 할일 탭 = 오늘 것만 (지난 것은 다시 안 붙임)', all(r['COL$A'] == '2026-09-23' for r in oj) and any(r['COL$C'] == '- 오늘 된 일' for r in oj), oj)
    pl = {'앞으로 할일': {'kind': 'date', 'cols': 4, 'values': [['2026-10-01', 'A', '- x', ''], ['2026-10-01', 'A', '- y', ''], ['2026-10-02', 'A', '- z', '']]}}
    mg11 = [x['mergeCells']['range'] for x in T.merge_body(pl, {'앞으로 할일': '2-4'})['requests'] if 'mergeCells' in x]
    chk('앞으로 할일 병합 : 같은 기한 A2:A3, 현장은 기한이 바뀌면 끊김 B2:B3',
        mg11 == [{'sheetId': 3, 'startRowIndex': 1, 'endRowIndex': 3, 'startColumnIndex': 0, 'endColumnIndex': 1},
                 {'sheetId': 3, 'startRowIndex': 1, 'endRowIndex': 3, 'startColumnIndex': 1, 'endColumnIndex': 2}], mg11)
    chk('시트 없으면 예전과 같음 (⑤ 는 회의록 기한만)', T.run(d, TODAY, out=os.path.join(d, 'out12'))[1]['①지난것'] == 0)

    print('--- v12 한 곳·한 통·두 동작 (▼고르기·메모·걸러보기·자료 상태·급한 것)')
    bj12 = write(d, 'b12_a.json', {'range': "'답요청'!A1:G50", 'values': [
        ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
        ['2026-09-20', '제천', '- 옛 확인 일', '', '진행중', '', '제천'],
        ['', '', '- 틀린 일', '', '아니야', '바른 일로 고침', '제천'],
        ['', '', '- 만들 일', '', '만들어줘', '', '제천'],
        ['', '', '- 끝난 일', '완료', '진행중', '', '제천'],                       # 체크했으면 ▼는 무시
        ['', '', '- 지난 기한 일  (기한 2026-09-21)', '', '맞아', '', '제천']]})
    (x1, x2, _x3), sx = T.run(d, TODAY, out=os.path.join(d, 'out12b'), done_path=bj12)   # 오늘 할일·앞으로 할일 탭 없음
    o12 = io.open(sx['파일']['오늘의정리'], encoding='utf-8').read()
    chk('▼진행중 → (진행중) 할일', '  - (진행중) 옛 확인 일' in x1, x1)
    chk('▼아니야 + 메모 → 할일 → 메모', '  - 틀린 일 → 바른 일로 고침' in x1, x1)
    chk('▼만들어줘 → (만들어줘) 할일', '  - (만들어줘) 만들 일' in x1, x1)
    chk('▼맞아 → (맞아) 할일 (② 에서도)', '  - (맞아) 지난 기한 일' in x2, x2)
    chk('체크한 줄은 ▼ 있어도 안 나옴', '끝난 일' not in o12, o12[:300])
    chk('▼ 고르신 것 절 : 만들어줘 · 맞아', '━━ ▼ 고르신 것 ━━' in o12 and '만들어줘 1건' in o12 and '  - 제천 · 만들 일' in o12 and '맞아 1건' in o12, o12[:900])
    chk('메일 순서 : 링크 → 자료 상태 → 급한 것 → ▼ → 1', 0 < o12.index('━━ 자료 상태') < o12.index('━━ 급한 것') < o12.index('━━ ▼ 고르신 것') < o12.index('━━ 1. 답해 주십시오'), o12[:600])
    chk('자료 상태 : 시트 못 읽은 탭 ※', '※ 시트 못 읽음 : 오늘 할일·앞으로 할일' in o12, o12[:400])
    chk('자료 상태 : 어제 회의 3건이면 ※ 없음', '어제(9/22) 회의록 4건' in o12 and '※ 어제' not in o12, o12[:400])
    chk('급한 것 : 기한 오래된 것이 먼저', o12.split('━━ 급한 것')[1].split('\n\n', 1)[1].startswith('2026-09-21\n\n제천\n  - (맞아) 지난 기한 일'), o12.split('━━ 급한 것')[1][:200])
    chk('숫자 : ▼고르신것 4 · 만들차례 1', sx['▼고르신것'] == 4 and sx['만들차례'] == 1, (sx['▼고르신것'], sx['만들차례']))
    (y1, y2, _y3), sy = T.run(d, datetime.date(2026, 9, 25), out=os.path.join(d, 'out12c'), done_path=bj12 + ',' + bt + ',' + bf)
    oy = io.open(sy['파일']['오늘의정리'], encoding='utf-8').read()
    chk('어제 회의 0건이면 ※ 한방에 안내', '※ 어제(9/24) 회의록 0건 — 통화·회의가 있었는데 한방에를 안 누르셨으면 빠진 것입니다' in oy, oy[:400])
    chk('세 탭 다 읽으면 「시트 체크 읽음」', '시트 체크 읽음 : 답요청·오늘 할일·앞으로 할일' in oy, oy[:400])
    chk('급한 것은 5줄까지', len([l for l in oy.split('━━ 급한 것')[1].split('━━ ▼')[0].split('\n') if l.startswith('  - ')]) <= 5)
    chk('시트 없이 돌리면 급한 것·▼ 없음', '━━ 급한 것' not in io.open(T.run(d, TODAY, out=os.path.join(d, 'out12d'))[1]['파일']['오늘의정리'], encoding='utf-8').read())
    aj12 = json.load(io.open(sx['파일']['시트_답요청'], encoding='utf-8'))['rows']
    chk('시트 새 줄 G열 = 현장(걸러보기)', all(r.get('COL$G') == r.get('COL$B') for r in aj12) and aj12, aj12)
    pl12 = {'답요청': {'kind': 'date', 'cols': 4, 'values': [['2026-10-01', 'A', '- x', '', '', '', 'A']] * 2}}
    ev = [x['setDataValidation'] for x in T.merge_body(pl12, {'답요청': '5-6'})['requests'] if 'setDataValidation' in x and x['setDataValidation']['rule']['condition']['type'] == 'ONE_OF_LIST']
    chk('새 줄 E열 ▼목록 = 진행중·아니야·맞아·만들어줘', ev and [v['userEnteredValue'] for v in ev[0]['rule']['condition']['values']] == ['진행중', '아니야', '맞아', '만들어줘'] and ev[0]['range']['startColumnIndex'] == 4, ev)

    print('--- v12 쓰기 한 번 (Zapier 1회)')
    wb, wr = T.write_body(json.load(io.open(sw['파일']['시트계획'], encoding='utf-8')), {'답요청': 108, '오늘 할일': 11, '회의록': 78, '앞으로 할일': 9})
    uc = [x['updateCells'] for x in wb['requests'] if 'updateCells' in x]
    chk('탭마다 updateCells 하나 (빈 탭은 건너뜀)', [u['range']['sheetId'] for u in uc] == [0, 1, 2, 3], [u['range']['sheetId'] for u in uc])
    chk('새 줄 = 지금 줄 수 바로 아래 (답요청 110행부터)', uc[0]['range']['startRowIndex'] == 109 and wr['답요청'] == '110-%d' % (109 + len(uc[0]['rows'])), (uc[0]['range'], wr))
    chk('날짜는 날짜 숫자로 (2026-09-22 = 46287)', uc[0]['rows'][0]['values'][0] == {'userEnteredValue': {'numberValue': 46287}}, uc[0]['rows'][0]['values'][0])
    chk('글은 글로 · 빈 칸은 비움', uc[0]['rows'][0]['values'][2]['userEnteredValue']['stringValue'].startswith('- ') and uc[0]['rows'][0]['values'][3] == {})
    chk('회의록 제목줄은 글', uc[2]['rows'][0]['values'][0]['userEnteredValue'] == {'stringValue': '26년 09월 22일_회의 4건'}, uc[2]['rows'][0]['values'][0])
    chk('병합·체크박스·▼ 가 같은 본문에', any('mergeCells' in x for x in wb['requests']) and any('setDataValidation' in x for x in wb['requests']))
    chk('회의록 날짜 서식도 같이 (46287 로 보이던 것)', wb['requests'][-1]['repeatCell']['range']['sheetId'] == 2)
    chk('줄수.json 에 없는 탭은 안 씀', [x for x in T.write_body({'답요청': {'kind': 'date', 'cols': 4, 'values': [['2026-09-24', 'A', '- x', '']]}}, {})[0]['requests'] if 'updateCells' in x] == [])

    print('--- 낱개')
    chk('parse_todo', T.parse_todo('- 260922 | 무엇 | 배성윤 → 누구') == ('260922', '무엇', '배성윤 → 누구'))
    chk('parse_todo 미정', T.parse_todo('미정 | 무엇') == ('미정', '무엇', ''))
    chk('parse_todo 줄 아님', T.parse_todo('==========') is None)
    chk('어제 회의 없을 때', '(2026-10-29 회의록 없음)' in T.run(d, datetime.date(2026, 10, 30), out=os.path.join(d, 'o3'))[0][2])
    chk('_iso', T._iso('260923') == '2026-09-23' and T._iso('미정') == '' and T._iso('') == '')
finally:
    shutil.rmtree(d, ignore_errors=True)

print('\n통과 %d / 실패 %d %s' % (OK[0], len(NG), NG or ''))
sys.exit(1 if NG else 0)

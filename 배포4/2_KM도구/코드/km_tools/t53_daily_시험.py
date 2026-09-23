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
        t1.startswith('2026-09-22\n\n수유초등학교\n  차단기 리셋 후 동작 확인  (확인 예정)\n\n앵커 호텔\n  회로도 제출  (기한 2026-09-23)  (김경원 상무)\n'), t1)
    chk('v6 날짜·현장은 한 번만', t1.count('2026-09-22\n') == 1 and t1.count('앵커 호텔\n') == 1 and '\t' not in t1, t1)
    chk('기한 없으면 (기한) 안 붙임', '\n  샘플 발송  (현장)\n' in t1, t1)
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
    chk('복합회의 할 일을 다른 현장으로 안 옮김', '\n복합회의\n  센서 단가 회신' in t2 and '부천대' not in t2 and '제천' not in t2)
    chk('v6 줄 모양 (날짜 한 번 → 현장 → 들여쓰기, 현장이 아닌 것은 뒤)', t2.startswith('2026-09-23\n\n앵커 호텔\n  회로도 제출') and t2.index('앵커 호텔') < t2.index('복합회의') and t2.count('2026-09-23') == 1, t2)

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
    chk('시트줄 수', st['시트줄'] == {'답요청': 4, '오늘 할일': 2, '회의록': 4}, st['시트줄'])
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
    chk('한 줄뿐이면 병합 안 함 (체크박스만)', [list(x)[0] for x in one_row] == ['setDataValidation'], one_row)
    cb = [x['setDataValidation'] for x in mb if 'setDataValidation' in x]
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
    chk('① 도 현장명 그대로 (귀속 안 함)', '\n복합회의\n  부천대 확인' in u1)
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
    chk('「배성윤 →」 없음 (상대는 남김)', '배성윤' not in t1 and '배성윤' not in t2 and '(김경원 상무)' in t1, t1)
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

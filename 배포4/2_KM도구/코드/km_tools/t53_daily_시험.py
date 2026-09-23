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

    print('--- ① 답해 주십시오 (하루치 + 시트 링크)')
    chk('시트 링크 있음', 'spreadsheets/d/SHEET' in t1)
    chk('어제 할 일만 (5건: 앵커 3 + 수유초 1, 같은 할 일 1번)', st['①할일'] == 4, st['①할일'])
    chk('9/21 복합회의 할 일은 ① 에 없음', '센서 단가 회신' not in t1)
    chk('「N일 지남」 안 적음', '지남' not in t1)
    chk('현장명 띄어쓰기 그대로 (앵커 호텔)', '앵커 호텔' in t1 and '앵커호텔\n' not in t1)
    chk('종류 낱말 (제출·발송)', '[제출] 회로도 제출' in t1 and '[발송] 샘플 발송' in t1)
    chk('담당은 괄호', '(배성윤 → 김경원 상무)' in t1 and '→ 배성윤 →' not in t1)
    rows = list(csv.DictReader(io.open(st['파일']['할일추가'], encoding='utf-8-sig')))
    chk('csv 머리 6칸', list(rows[0].keys()) == T.SHEET_HEAD, list(rows[0].keys()))
    chk('csv 줄 수 = ① 건수', len(rows) == st['①할일'])
    chk('csv 현장 = 손으로 넣으신 것', any(r['현장'] == '앵커 호텔' for r in rows))
    chk('csv 완료 칸 비어 있음', all(r['완료'] == '' for r in rows))

    print('--- ② 오늘 할 것 (오늘 날짜만)')
    chk('오늘 3건 (회로도 제출·센서 회신·설치 일정)', st['②오늘'] == 3, st['②오늘'])
    chk('지난 기한(9/17 도면 발송) 없음', '도면 발송' not in t2)
    chk('미정 없음', '샘플 발송' not in t2)
    chk('일정 칸도 잡음', '[일정] 설치 · 수업 끝나고 방문' in t2)
    chk('복합회의는 「현장이 아닌 것」 표시', '복합회의   (현장이 아닌 것)' in t2)
    chk('복합회의 할 일을 다른 현장으로 안 옮김', '부천대' not in t2 and '제천' not in t2)
    chk('어느 회의에서 나왔는지', '(9/21 회의 17:26' in t2)

    print('--- ③ 어제 있었던 일 (전문 정리)')
    chk('회의 수 = meta 수', '회의 3건 · 현장 2개' in t3)
    chk('현장별 건수 정확 (앵커 2 · 수유초 1)', st['어제_현장별'] == {'앵커 호텔': 2, '수유초등학교': 1}, st['어제_현장별'])
    chk('현장 번호 매김', '1. 앵커 호텔        회의 2건' in t3 and '2. 수유초등학교        회의 1건' in t3)
    chk('날짜 사람이름 줄', '9/22   09:00  일능 홍길동 부장' in t3 and '9/22   14:00  일능 박철수 대리' in t3)
    chk('회사=이름 자료도 이름 나옴', '9/22   수유초등학교' in t3 and '상대 미상' not in t3)
    chk('안건/협의내용/결정사항/조치사항 4줄', all(k in t3 for k in ('안건 : 회로도 구성', '협의내용 : 냉장고·비데·세면대 회로 구성 협의함 / 기존 도면상 확인',
                                                       '결정사항 : 없음 — 회로도 구성 확인 후 재협의 예정', '조치사항 : 한국마이크로닉 · 회로도 구성 재확인')))
    chk('결정 없으면 「없음」', '결정사항 : 없음\n' in t3)
    chk('9/21·9/20 회의는 ③ 에 없음', '센서 40,000' not in t3 and '제천' not in t3)
    chk('회신 요청 사항 안 적음', '회신 요청' not in t3)

    print('--- 현장이 아닌 것 이 어제 있을 때')
    write(d, 'f__meta.json', meta('복합회의', '260922', hm='16:00', person='이순신 이사', name='이순신', rank='이사',
          items=[it('여러 현장', ['부천대·제천 얘기'], '', [])], todo=['- 미정 | 부천대 확인 | 배성윤 → x']))
    (u1, u2, u3), st2 = T.run(d, TODAY, out=os.path.join(d, 'out2'))
    chk('③ 따로 절', '[ 현장이 아닌 것 ]' in u3 and '어느 현장 것인지는 차장님이 정하십시오' in u3)
    chk('③ 머리에 「그 밖에 복합회의 1건」', '(그 밖에 복합회의 1건)' in u3)
    chk('③ 현장 수는 그대로 2', '회의 4건 · 현장 2개' in u3)
    chk('① 도 표시', '복합회의   (현장이 아닌 것' in u1)

    print('--- 낱개')
    chk('parse_todo', T.parse_todo('- 260922 | 무엇 | 배성윤 → 누구') == ('260922', '무엇', '배성윤 → 누구'))
    chk('parse_todo 미정', T.parse_todo('미정 | 무엇') == ('미정', '무엇', ''))
    chk('parse_todo 줄 아님', T.parse_todo('==========') is None)
    chk('kind_of 없으면 확인', T.kind_of('아무 낱말') == '확인' and T.kind_of('도면 제출') == '도면')
    chk('어제 회의 없을 때', '어제 회의록이 없습니다' in T.run(d, datetime.date(2026, 10, 30), out=os.path.join(d, 'o3'))[0][2])
finally:
    shutil.rmtree(d, ignore_errors=True)

print('\n통과 %d / 실패 %d %s' % (OK[0], len(NG), NG or ''))
sys.exit(1 if NG else 0)

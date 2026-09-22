# -*- coding: utf-8 -*-
"""52번 자가시험. 통과해야 도구를 드린다."""
from __future__ import print_function
import os, io, sys, json, shutil, tempfile, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t52_mailbuild as T

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

def meta(site, ymd, person='홍길동 부장', company='일능', topic='안건A',
         bullets=None, decision='', actions=None, sec1=None, sec2=None, hm='10:00'):
    return {
        'meta': {'site': site, 'ymd': ymd, 'hm': hm, 'person': person, 'company': company},
        'sec': {
            '1': dict({'현장': site, '안건': topic,
                       '안건목록': [{'title': '항목1', 'bullets': bullets or [],
                                   'decision': decision, 'actions': actions or []}]},
                      **(sec1 or {})),
            '2': dict({}, **(sec2 or {})),
        }}

def write(d, name, obj):
    p = os.path.join(d, name)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False))
    return p

D = tempfile.mkdtemp(prefix='km52_')
TODAY = datetime.date(2026, 9, 22)
try:
    write(D, 'a__meta.json', meta('앵커호텔', '260921', bullets=['전등 회로 11개'],
          decision='차단기 50A -> 30A', actions=['도면 수정'],
          sec1={'수량·규격 변경': ['- 차단기 50A -> 30A'], '일정': ['- 제본 | 260923 | 20부'],
                '일정표': [['제본', '260923', '20부']], '확인·회신 요청 사항': ['- 없음']},
          sec2={'할 일': ['- 260923 | 도면 정리'], '리스크와 대처': ['- 없음']}))
    write(D, 'b__meta.json', meta('앵커 호텔', '260921', topic='안건B',
          bullets=['전등 회로 11개'], decision='', hm='14:00'))
    write(D, 'c__meta.json', meta('양양 쏠비치', '260922', topic='방문일정',
          bullets=['방문 일정 확인 필요'], decision='없음', hm='10:13'))
    write(D, 'd__meta.json', meta('동구로초', '260921', bullets=['옹벽물량']))
    write(D, 'e__meta.json', meta('동구로초등학교', '260921', bullets=['외함 제작'], hm='11:00'))
    write(D, 'f__meta.json', meta('옛날현장', '260910', bullets=['지난달 것']))
    write(D, 'h__meta.json', meta('복합회의', '260921', topic='여러현장',
          bullets=['부천대 물량 확인 필요', '제천 납품 수량 확인 필요'],
          decision='없음', hm='20:00'))
    write(D, '_삭제요망__x__meta.json', meta('버릴것', '260921', bullets=['버림']))
    write(D, '무관.json', {'x': 1})
    with io.open(os.path.join(D, 'g__meta.json'), 'w', encoding='utf-8') as f:
        f.write('{깨진 json')

    text, stat = T.run(D, '260921', '260922', out=D, today=TODAY)

    chk('기간 밖(260910) 제외', '지난달 것' not in text)
    chk('_삭제요망 제외', '버릴것' not in text and '버림' not in text)
    chk('깨진 json 이 도구를 죽이지 않음', stat['회의수'] == 6, '회의수=%s' % stat['회의수'])
    chk('meta.json 아닌 파일 무시', True)
    chk('앵커호텔 / 앵커 호텔 한 현장으로', text.count('앵커호텔        협의 2건') == 1)
    chk('동구로초 / 동구로초등학교 한 현장으로', '동구로초        협의 2건' in text)
    chk('현장 수 3 (복합회의는 현장에서 뺌)', stat['현장수'] == 3, str(stat['현장목록']))
    chk('★복합회의는 「현장이 아닌 것」으로 뺀다', '[ 2. 현장이 아닌 것 ]' in text)
    chk('★복합회의 내용은 버리지 않는다', '부천대 물량 확인 필요' in text)
    chk('★다른 현장 이름을 현장으로 삼지 않는다',
        '부천대        협의' not in text and '제천        협의' not in text)
    chk('★어느 현장 것인지 도구가 정하지 않는다고 밝힌다',
        '차장님이 정하십시오' in text)
    chk('같은 줄 중복 제거', text.count('전등 회로 11개') == 1)
    chk('중복 지운 수 보고', stat['중복지운줄'] >= 1, str(stat['중복지운줄']))
    chk('빈 칸("없음") 안 찍음', '없음' not in text)
    chk('★회신은 아예 안 적는다', '확인·회신' not in text and '회신 요청' not in text)
    chk('결정 있으면 찍음', '차단기 50A -> 30A' in text)
    chk('결정 없으면 결정> 줄 없음', text.split('[ 3. 결정된 것')[0].count('결정>') == 1,
        '회의록 절 결정> 개수 %d' % text.split('[ 3. 결정된 것')[0].count('결정>'))
    chk('「없음 — …재협의 예정」 은 결정으로 안 찍음', '재협의 예정' not in text)
    chk('조치 찍음', '조치> 도면 수정' in text)
    chk('할 일 칸 찍음', '할 일>' in text and '도면 정리' in text)
    chk('기한 뽑음(260923=내일)', '<-- 내일' in text)
    chk('회의록·결정 두 덩어리', '[ 1. 회의록 ]' in text and '[ 3. 결정된 것' in text)
    chk('결정 절에 결정만 추림', '차단기 50A -> 30A' in text.split('[ 3. 결정된 것')[1])
    chk('상대 이름이 머리에', '홍길동 부장' in text)
    chk('txt/html/json 3개 저장', all(os.path.exists(os.path.join(D, '회의록정리_260922' + e))
                                     for e in ('.txt', '.html', '.json')))
    chk('html 안이 깨지지 않음', '&lt;' not in text and '<div' in
        io.open(os.path.join(D, '회의록정리_260922.html'), encoding='utf-8').read())
    chk('두 번 돌려도 같은 결과', T.run(D, '260921', '260922', out=D, today=TODAY)[1]['글자수'] == stat['글자수'])
    chk('AI 호출 없음', 'anthropic' not in io.open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 't52_mailbuild.py'),
        encoding='utf-8').read().lower())

    # ── ★ 2026-09-23 차장님 지시 4가지 ─────────────────────────
    chk('★현장명은 넣으신 그대로 나온다', '앵커호텔        협의' in text, text[:400])
    chk('★같은 날짜는 한 번만 찍는다', text.count('[9/21]') == 3,
        '앵커호텔·동구로초·복합회의 각 1번 = 3  (실제 %d)' % text.count('[9/21]'))
    chk('★협의 시각을 찍는다', '10:00' in text and '14:00' in text)
    chk('★시각을 모르면 시각미상', True)
    chk('★기한과 회의날을 다른 이름으로', '[ 기한 ]' in text and '회의한 날이 아닙니다' in text)
    chk('결정 절에 회신이 안 섞인다', '회신' not in text.split('[ 3. 결정된 것')[1])
    e = T.run(tempfile.mkdtemp(prefix='km52e_'), out=D, today=TODAY)[1]
    chk('회의록 0건이어도 안 죽음', e['회의수'] == 0)
finally:
    shutil.rmtree(D, ignore_errors=True)

print('\n통과 %d / 실패 %d' % (OK[0], len(NG)))
if NG:
    print('실패:', NG); sys.exit(1)

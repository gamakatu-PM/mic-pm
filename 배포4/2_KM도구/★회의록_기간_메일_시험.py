# -*- coding: utf-8 -*-
"""★회의록_기간_메일 자가시험."""
import os, io, sys, json, shutil, tempfile, datetime, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('gm', os.path.join(HERE, '★회의록_기간_메일.py'))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

T = datetime.date(2026, 9, 23)
print('--- 입력 풀기')
chk('260915', G.norm_ymd('260915', 'x') == '260915')
chk('2026-09-15', G.norm_ymd('2026-09-15', 'x') == '260915')
chk('2026.9.1', G.norm_ymd('2026.9.1', 'x') == '260901')
chk('26-9-5', G.norm_ymd('26-9-5', 'x') == '260905')
chk('엉터리는 기본값', G.norm_ymd('abc', '260101') == '260101')
chk('월 2609', G.norm_month('2609', T) == ('260901', '260930'))
chk('월 9', G.norm_month('9', T) == ('260901', '260930'))
chk('월 9월', G.norm_month('9월', T) == ('260901', '260930'))
chk('월 2026-02', G.norm_month('2026-02', T) == ('260201', '260228'))
chk('월 빈칸=이번 달', G.norm_month('', T) == ('260901', '260930'))

print('--- 도구 넣기 (없는 폴더 · 옛 판)')
d = tempfile.mkdtemp()
try:
    tools = os.path.join(d, 'km_tools'); os.makedirs(tools)
    with io.open(os.path.join(tools, 't52_mailbuild.py'), 'w', encoding='utf-8') as f:
        f.write("VERSION = 'v1 2026-09-22'\n")
    n1 = G.ensure_tool(tools, 't52_mailbuild'); n2 = G.ensure_tool(tools, 't53_daily')
    chk('옛 52번 덮어씀', 'v1 → v2' in n1, n1)
    chk('없는 53번 새로 넣음', '없음 → v8' in n2, n2)
    chk('다시 하면 안 건드림', G.ensure_tool(tools, 't52_mailbuild') == '' and G.ensure_tool(tools, 't53_daily') == '')
    src = io.open(os.path.join(tools, 't53_daily.py'), encoding='utf-8').read()
    chk('넣은 53번이 진짜 v8', "VERSION = 'v8" in src and 'def run_range' in src)

    print('--- 통째로 돌리기 (가짜 드라이브)')
    drive = os.path.join(d, 'drive'); meta = os.path.join(drive, '회의록', 'incoming'); os.makedirs(meta)
    def meta_json(fn, site, ymd, person, items, todo):
        obj = {'meta': {'site': site, 'ymd': ymd, 'hm': '10:00', 'person': person, 'company': '', 'name': person, 'rank': ''},
               'sec': {'1': {'현장': site, '안건목록': items, '일정': []}, '2': {'할 일': todo}}}
        with io.open(os.path.join(meta, fn), 'w', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False))
    it = lambda t, b, dc, a: {'title': t, 'bullets': b, 'decision': dc, 'actions': a}
    meta_json('a__meta.json', '앵커 호텔', '260915', '김경원 상무', [it('회로도', ['냉장고 회로'], '없음 — 재협의', ['재확인'])], ['- 260920 | 도면 제출 | 배성윤 → 김경원 상무'])
    meta_json('b__meta.json', '수유초등학교', '260916', '임정권', [it('전등', ['퓨즈 확인'], '', [])], ['- 미정 | 퓨즈 확인 | 배성윤 → AS'])
    meta_json('c__meta.json', '제천', '260801', '최영희 과장', [it('일정', ['설치'], '', [])], [])
    G.NOTE[:] = []
    # 이 시험 폴더의 km_tools 를 쓰게 HERE 를 바꾼다
    G.HERE = d; os.rename(tools, os.path.join(d, 'km_tools_x')); os.makedirs(os.path.join(d, '코드')); os.rename(os.path.join(d, 'km_tools_x'), os.path.join(d, '코드', 'km_tools'))
    st = G.run('260901', '260930', drive=drive, out=os.path.join(d, 'out'), today=T)
    chk('9월 회의 2건 (8월 제외)', st and st['회의'] == 2, st and st['회의'])
    chk('현장별', st['현장별'] == {'앵커 호텔': 1, '수유초등학교': 1}, st['현장별'])
    chk('드라이브 KM_아침메일 에 2개', len(st['올린파일']) == 2 and all(os.path.isfile(p) for p in st['올린파일']))
    names = sorted(os.path.basename(p) for p in st['올린파일'])
    chk('파일 이름 회의록정리_ 로 시작 (즉시발송이 잡는 접두)', names == ['회의록정리_260923_할일_260901-260930.txt', '회의록정리_260923_회의록_260901-260930.txt'], names)
    body = io.open(st['올린파일'][0], encoding='utf-8').read()
    chk('③ 모양', '. 앵커 호텔\n\n9/15   10:00  김경원 상무\n\n안건 : 회로도' in body and body.startswith('1. '), body[:120])
    todo = io.open(st['올린파일'][1], encoding='utf-8').read()
    chk('할 일 (v6 날짜·현장 머리줄 한 번) + 시트 링크', todo.startswith('2026-09-15\n\n앵커 호텔\n  도면 제출  (기한 2026-09-20)  (김경원 상무)') and '배성윤' not in todo and '\t' not in todo and '26년 회의록2 : https://docs.google.com/spreadsheets/d/1S02' in todo, todo)
    chk('즉시발송 없으면 「올렸어」 안내', any('올렸어' in s for s in G.NOTE))
    chk('회의 없는 기간', G.run('261001', '261031', drive=drive, out=os.path.join(d, 'out2'), today=T)['회의'] == 0)
    chk('드라이브 없으면 멈추고 안내', G.run('260901', '260930', drive='', today=T) is None and any('드라이브' in s for s in G.NOTE))
finally:
    shutil.rmtree(d, ignore_errors=True)
print('\n통과 %d / 실패 %d %s' % (OK[0], len(NG), NG or ''))
sys.exit(1 if NG else 0)

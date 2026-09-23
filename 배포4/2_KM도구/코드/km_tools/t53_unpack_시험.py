# -*- coding: utf-8 -*-
"""53-1 자가시험."""
from __future__ import print_function
import os, io, sys, json, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t53_unpack as U

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

# 구글이 되돌려 주는 모양 그대로 흉내 : 줄 끝 "  \n", \_ \[ \] 탈출, 따옴표 이중 탈출
snip = ('{  \n "meta": {  \n "site": "양양 쏠비치",  \n "ymd": "260922",  \n "hm": "10:13",  \n "person": "이은승 이사",  \n'
        ' "company": "삼우MEP", "name": "이은승", "rank": "이사", "date\\_iso": "2026-09-22", "phone": "010"  \n },  \n'
        ' "sec": {  \n "1": {  \n "현장": "양양 쏠비치",  \n "안건목록": \\[  \n {  \n "title": "방문 일정",  \n "bullets": \\[ "\\\\"한번만 더\\\\" 발언 — 확인 필요" \\],  \n'
        ' "decision": "없음 — 확인 후 재협의", "actions": \\[ "확인" \\] } \\],  \n "일정": \\[ "- 협의 | 260922 | 방문" \\],  \n "확인·회신 요청 사항": \\[ "x" \\]  \n },  \n'
        ' "2": {  \n "할 일": \\[ "- 260922 | 권 매니저 방문 목적 확인 | 배성윤 → 권 매니저" \\],  \n "전체 협의 내용": \\[ "긴 글" \\]  \n }  \n }  \n}')
res = {'files': [
    {'title': '양양 쏠비치__260922_삼우MEP_이은승이사_방문일정__meta.json', 'contentSnippet': snip},
    {'title': '양양 쏠비치__260922_x__원문.txt', 'contentSnippet': '아무거나'},
    {'title': '깨진__260922__meta.json', 'contentSnippet': '{ "meta": '},
]}
d = tempfile.mkdtemp()
try:
    src = os.path.join(d, 'r.txt')
    with io.open(src, 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False))
    ok, bad = U.run(src, os.path.join(d, 'o'))
    chk('meta.json 만 1건 풀림', ok == ['양양 쏠비치__260922_삼우MEP_이은승이사_방문일정__meta.json'], ok)
    chk('깨진 것은 실패로 보고', len(bad) == 1 and bad[0][0].startswith('깨진'), bad)
    j = json.load(io.open(os.path.join(d, 'o', ok[0]), encoding='utf-8'))
    chk('현장명 그대로 (띄어쓰기 포함)', j['meta']['site'] == '양양 쏠비치')
    chk('안 쓰는 칸 버림 (phone·date_iso·전체 협의 내용)', 'phone' not in j['meta'] and '전체 협의 내용' not in j['sec']['2'])
    chk('이중 탈출 따옴표 풀림', j['sec']['1']['안건목록'][0]['bullets'][0] == '"한번만 더" 발언 — 확인 필요', j['sec']['1']['안건목록'][0]['bullets'])
    chk('할 일 그대로', j['sec']['2']['할 일'] == ['- 260922 | 권 매니저 방문 목적 확인 | 배성윤 → 권 매니저'])
    chk('일정 그대로', j['sec']['1']['일정'] == ['- 협의 | 260922 | 방문'])
    chk('unescape 낱개', U.unescape('a\\_b \\[c\\] \\-d') == 'a_b [c] -d')
    # 53번이 그대로 읽을 수 있는가
    import t53_daily as T
    r = T.read_raw(os.path.join(d, 'o', ok[0]))
    chk('53번이 읽음', r['site'] == '양양 쏠비치' and r['todos'][0][0] == '260922' and r['person'] == '삼우MEP 이은승 이사', r)
finally:
    shutil.rmtree(d, ignore_errors=True)
print('\n통과 %d / 실패 %d %s' % (OK[0], len(NG), NG or ''))
sys.exit(1 if NG else 0)

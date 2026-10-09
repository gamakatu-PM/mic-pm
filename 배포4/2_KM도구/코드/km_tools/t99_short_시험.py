# -*- coding: utf-8 -*-
"""t99_short 시험 (가짜 자료) — python t99_short_시험.py → OK"""
from __future__ import print_function
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t99_short as T

TXT = u"""26년 회의록2 : x

━━ 자료 상태 ━━

※ 어제 회의록 2건

━━ 급한 것 ━━  기한이 가장 오래된 것부터

2026-06-21

복합회의
  - 바닥 작업 확인

2026-07-06

A현장
  - 하나
① 이어지는 줄
  - 둘

━━ 1. 답해 주십시오 ━━  …

2026-07-03

B현장
  - 답할 것

━━ 2. 오늘 할 것 ━━  2026-10-09 · 4건 · 기한 지난 것 1건

2026-09-01

C현장
  - 지난 것

2026-10-09

D현장
  - 오늘1
  - 오늘2 매우 긴 글매우 긴 글매우 긴 글매우 긴 글매우 긴 글매우 긴 글매우 긴 글매우 긴 글

E현장
  - 오늘3
  - 오늘4

━━ 3. 어제 있었던 일 ━━  26년 10월 08일_회의 2건
"""

META = {u'제목': u'[KM] 오늘의 정리 입니다. 2026-10-09 (금)', u'어제회의': 2, u'①지난것': 10, u'①할일': 1,
        u'②기한지난것': 1, u'제안서대기': 2, u'어제_현장별': {u'유한대': 1, u'조선호텔': 1}}

n = 0
def ok(c, m):
    global n
    n += 1
    assert c, m

out = T.build(TXT, META, '261009')
L = out.splitlines()
ok(L[0] == META[u'제목'], '1 제목')
ok(u'답 안 한 할 일 11건' in out, '2 ①지난것+①할일')
ok(u'기한 지난 것 1건' in out and u'제안서 대기 2건' in out, '3 숫자')
ok(u'D현장 — 오늘1' in out and u'E현장 — 오늘3' in out, '4 오늘 것만')
ok(u'지난 것' not in out.split(u'■ 오늘 할 것')[1].split(u'■')[0], '5 지난 날짜 안 섞임')
ok(u'그 밖 1건은 시트' in out, '6 3개 넘으면 줄임')
ok(u'…' in out, '7 긴 글 자름')
ok(u'06/21 복합회의' in out and u'07/06 A현장 — 하나' in out and u'07/06 A현장 — 둘' in out, '8 급한 것 3개')
ok(u'이어지는 줄' not in out, '9 이어지는 줄 버림')
ok(u'유한대 1' in out and u'조선호텔 1' in out, '10 어제 회의 현장')
ok(u'답할 것' not in out, '11 ①은 넣지 않음')
ok(len(L) <= 16, '12 짧게(16줄 이하)')
out0 = T.build(TXT.replace(u'2026-10-09\n\nD현장', u'2026-10-10\n\nD현장').replace(u'\nE현장\n  - 오늘3\n  - 오늘4\n', u''), dict(META, **{u'어제_현장별': {}}), '261009')
ok(u'오늘 기한인 할 일 없음' in out0, '13 오늘 0건')
ok(u'■ 어제 회의' not in out0, '14 회의 0건이면 줄 없음')
print('OK', n)

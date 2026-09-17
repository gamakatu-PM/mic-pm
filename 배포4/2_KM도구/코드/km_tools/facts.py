# -*- coding: utf-8 -*-
"""확정 대장 - 프로님이 고친 것이 결정 사항이 된다. 토큰 0.
_도구결과\\_대장\\확정사항.csv  (일자, 현장, 항목, 값, 근거, 누가, 상태)
  · 덮어쓰지 않는다. 같은 현장·항목을 다시 넣으면 새 줄이 위(최신)가 되고 옛 줄은 상태=이전 으로 남는다 (B등급 이력).
  · 도구가 추정한 값보다 항상 우선한다. 아침 한 장·현황판·부탁서·클로드용 md 가 이 파일을 먼저 읽는다.
  · 넣는 길 3가지 : 43번(번호입력) / 받은답 csv 한 줄 `확정,현장,항목,값,근거` / 이 csv 를 직접 편집
표준 항목(자유 글자도 됨) : 공정단계(외함·속판·기구물제작·벽지·빽커버·기구물설치·강전·약전·시운전) · 객실수 · 준공일 · 발주처 · 시공사 · 담당자 · 결정 · 메모
"""
import os, io, csv, re
from common import *

HEAD = ['일자', '현장', '항목', '값', '근거', '누가', '상태']
STEPS = ['외함', '속판', '기구물제작', '벽지', '빽커버', '기구물설치', '강전', '약전', '시운전']

def path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '확정사항.csv')

def _read(p):
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                return list(csv.reader(fp))
        except Exception:
            continue
    return []

def load(active_only=True):
    """[dict(일자,현장,항목,값,근거,누가,상태)] 최신이 앞"""
    p = path()
    if not os.path.exists(p):
        write_csv(p, [['예) 2026-09-17', '연합기숙사', '공정단계', '외함', '외함만 납품 중 (프로님)', '프로님', '확정']], HEAD)
        return []
    out = []
    for r in _read(p)[1:]:
        r = (r + [''] * 7)[:7]
        if not r[1].strip() or r[0].startswith('예)'):
            continue
        d = dict(zip(['일자', '현장', '항목', '값', '근거', '누가', '상태'], [c.strip() for c in r]))
        if active_only and d['상태'] in ('이전', '취소'):
            continue
        out.append(d)
    out.sort(key=lambda d: d['일자'], reverse=True)
    return out

def _norm(s):
    return re.sub(r'[\s_\-\[\]\(\)]', '', str(s or '')).lower()

def get(site, item):
    """현장·항목의 최신 확정값 dict 또는 None (현장은 포함관계로 맞춤)"""
    for d in load():
        if _norm(d['항목']) == _norm(item) and (_norm(d['현장']) == _norm(site) or (_norm(site) and (_norm(site) in _norm(d['현장']) or _norm(d['현장']) in _norm(site)))):
            return d
    return None

def for_site(site):
    return [d for d in load() if _norm(d['현장']) == _norm(site) or (_norm(site) in _norm(d['현장']) or _norm(d['현장']) in _norm(site))]

def search(q):
    q = _norm(q)
    return [d for d in load(active_only=False) if q and any(q in _norm(v) for v in d.values())]

def add(site, item, value, basis='', who='프로님', day=None):
    """새 줄을 맨 위에 넣고, 같은 현장·항목의 옛 줄은 상태=이전 으로 (덮어쓰지 않음)"""
    p = path()
    rows = _read(p)
    if not rows:
        rows = [HEAD]
    body = rows[1:]
    for r in body:
        r += [''] * (7 - len(r))
        if r[1].strip() == site and _norm(r[2]) == _norm(item) and r[6].strip() not in ('이전', '취소'):
            r[6] = '이전'
    new = [(day or today().isoformat()), site, item, str(value), basis, who, '확정']
    body = [r for r in body if not (r and r[0].startswith('예)'))]
    write_csv(p, [new] + body, HEAD)
    log('확정', '%s %s=%s' % (site, item, value))
    return new

def step_index(value):
    """공정단계 값 -> 0~8 (모르면 None). '외함 납품 중' 처럼 문장이어도 단계 이름이 들어 있으면 잡는다"""
    v = _norm(value)
    best = None
    for i, s in enumerate(STEPS):
        if _norm(s) in v:
            best = i
    return best

# ---------------- 회의록 확인 대장 (v37) ----------------
# 프로님이 PLAUD 회의록을 저장만 하고 못 읽고 넘어가는 것을 막는다.
# 읽으신 회의는 44번(또는 받은답 `회의확인,<회의폴더>,확인`)으로 표시하고,
# 표시 안 된 회의는 42 아침 한 장 맨 위에 「미확인 회의록」 으로 매일 뜬다.

CHK = '회의확인.csv'
CHK_HEAD = ['확인일', '회의폴더', '현장', '메모', '누가']

def chk_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, CHK)

def checked(folder=None):
    """확인 처리된 회의폴더 이름 집합 (folder 를 주면 그것만 True/False)"""
    p = chk_path()
    if not os.path.exists(p):
        write_csv(p, [], CHK_HEAD)
        return set() if folder is None else False
    s = set()
    for r in _read(p)[1:]:
        r = (r + [''] * 5)[:5]
        if r[1].strip():
            s.add(_norm(r[1]))
    return s if folder is None else (_norm(folder) in s)

def check_meeting(folder, site='', memo='', who='프로님'):
    """이 회의를 읽었다고 표시 (같은 폴더는 한 번만)"""
    p = chk_path()
    rows = _read(p)
    body = [r for r in rows[1:] if r and len(r) > 1]
    if _norm(folder) in {_norm(r[1]) for r in body if len(r) > 1}:
        return None
    new = [today().isoformat(), folder, site, memo, who]
    write_csv(p, [new] + body, CHK_HEAD)
    log('회의확인', folder[:40])
    return new

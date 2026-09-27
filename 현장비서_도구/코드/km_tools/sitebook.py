# -*- coding: utf-8 -*-
"""현장대장 - 현장 기본정보 한 곳. 여러 도구가 같이 쓴다.
_도구결과\\_대장\\현장대장.csv  (현장, 준공일, 성급, 리조트, 객실수, 층수, 발주처, 시공사, 담당자, 비고)"""
import os, csv, io
from common import *

HEAD = ['현장', '준공일(YYYY-MM-DD)', '성급', '리조트(y/n)', '객실수', '층수',
        '발주처', '시공사', '담당자', '비고']

def path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '현장대장.csv')

def ensure():
    p = path()
    if not os.path.exists(p):
        write_csv(p, [['예) 광희동1가', '2027-03-31', '3', 'n', '203', '12', '', '', '', '']], HEAD)
    return p

def load():
    p = ensure()
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                rows = list(csv.reader(fp))
            break
        except Exception:
            rows = []
    out = []
    for r in rows[1:]:
        r = (r + [''] * 10)[:10]
        if not r[0].strip() or r[0].startswith('예)'):
            continue
        out.append(dict(zip(['site', 'due', 'star', 'resort', 'rooms', 'floors',
                             'owner', 'builder', 'pic', 'memo'], [c.strip() for c in r])))
    return out

def sync_from_folders():
    """plaud\\26년 폴더 이름으로 현장대장에 없는 현장을 추가만 한다(A등급)."""
    root = cfg('plaud')
    if not os.path.isdir(root):
        return 0
    known = {d['site'] for d in load()}
    new = []
    for d in sorted(os.listdir(root)):
        if os.path.isdir(os.path.join(root, d)) and not d.startswith(('_', '.')) and d not in known:
            new.append([d, '', '', '', '', '', '', '', '', '폴더에서 자동 추가'])
    if not new:
        return 0
    p = path()
    rows = []
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                rows = list(csv.reader(fp))
            break
        except Exception:
            pass
    write_csv(p, rows[1:] + new, HEAD)
    return len(new)

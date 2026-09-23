# -*- coding: utf-8 -*-
"""
53-1. 드라이브 검색 결과(search_files MAX_ALLOWED) → meta.json 풀기  (km_tools / t53_unpack)

클로드 창에서 Google_Drive search_files 결과가 디스크(tool-results/*.txt)에 떨어지면
그 파일을 읽어 meta.json 을 다시 만든다. base64 내려받기(14배 비쌈)를 안 쓰기 위한 것.

    python t53_unpack.py <검색결과.txt 또는 .json> <나올 폴더>

구글이 본문에 붙이는 마크다운 탈출(\\_ \\[ \\] \\- \\. 와 \\\\" 이중 탈출)을 되돌린다.
53번이 쓰는 칸만 남긴다 : meta(site·ymd·hm·person·company·name·rank) · 안건목록 · 일정 · 할 일.
현장명(meta.site)은 한 글자도 바꾸지 않는다.
"""
from __future__ import print_function
import os, sys, io, json, re

VERSION = 'v1 2026-09-23'
KEEP_META = ('site', 'ymd', 'hm', 'person', 'company', 'name', 'rank')


def unescape(s):
    s = s.replace('\\\\"', '\\"')                      # 이중 탈출된 따옴표
    s = re.sub(r'\\([^"\\/bfnrtu])', r'\1', s)          # JSON 이 모르는 탈출은 전부 벗긴다
    return s


def slim(j):
    m = j.get('meta') or {}
    s1 = (j.get('sec') or {}).get('1') or {}
    s2 = (j.get('sec') or {}).get('2') or {}
    return {'meta': dict((k, m.get(k, '')) for k in KEEP_META),
            'sec': {'1': {'현장': s1.get('현장', ''), '안건목록': s1.get('안건목록') or [],
                          '일정': s1.get('일정') or []},
                    '2': {'할 일': s2.get('할 일') or []}}}


def parse_one(snippet):
    return slim(json.loads(unescape(snippet or '')))


def run(src, out):
    with io.open(src, 'r', encoding='utf-8') as f:
        raw = f.read()
    d = json.loads(raw)
    files = d.get('files') if isinstance(d, dict) else d
    if not os.path.isdir(out):
        os.makedirs(out)
    ok, bad = [], []
    for f in files or []:
        title = f.get('title') or ''
        if not title.endswith('meta.json'):
            continue
        try:
            j = parse_one(f.get('contentSnippet'))
        except Exception as e:
            bad.append((title, str(e)))
            continue
        p = os.path.join(out, re.sub(r'[\\/:*?"<>|]', '_', title))
        with io.open(p, 'w', encoding='utf-8') as w:
            w.write(json.dumps(j, ensure_ascii=False, indent=1))
        ok.append(title)
    return ok, bad


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    ok, bad = run(argv[1], argv[2])
    print('풀림 %d건 / 실패 %d건' % (len(ok), len(bad)))
    for t, e in bad:
        print('  실패  %s  %s' % (t[:50], e))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

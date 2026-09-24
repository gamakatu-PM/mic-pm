# -*- coding: utf-8 -*-
"""
53-2. 드라이브로 읽은 구글 시트(마크다운 표) → t53 이 읽는 json   (km_tools / t53_sheetmd)   v1 2026-09-24

왜 : Zapier 사용 한도가 찼다(2026-09-24). 시트 읽기를 Zapier 없이 Google_Drive read_file_content 로 한다.
     read_file_content 는 시트의 모든 탭을 마크다운 표로 돌려준다. 병합 칸은 「[merged] 값」 으로 모든 줄에 채워져 온다.

    python t53_sheetmd.py <읽은 결과 파일(json 또는 md)> <출력 폴더>
      → 답요청.json · 오늘할일.json · 앞으로할일.json · 회의록.json  (t53 --done 이 읽는 {"range","values"} 모양)
      → 레이더 시트면 로그.json · 확정.json · 재검토.json  (t53 --radar 가 읽는 모양)
      → 줄수.json  {탭: 데이터 줄 수}  (t53 --write 가 새 줄을 어디에 쓸지 정할 때 쓴다)

어느 탭인지는 표 머리 칸으로 가린다 (탭 순서가 바뀌어도 된다):
   날짜|현장|할일|완료…   첫 번째 = 답요청, 두 번째 = 오늘 할일
   기한|현장|할일|완료…   = 앞으로 할일
   날짜|현장|시각·협의자… = 회의록
   수집일시|실행유형|지역… = 레이더 확정 / 수집일시|실행유형|현장명… = 레이더 재검토 / 그 밖의 레이더 로그 머리 = 실행로그
"""
from __future__ import print_function
import os, sys, io, json, re

VERSION = 'v1 2026-09-24'


def _text_of(path):
    raw = io.open(path, 'r', encoding='utf-8').read()
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            for k in ('fileContent', 'content', 'text'):
                if isinstance(d.get(k), str):
                    return d[k]
    except Exception:
        pass
    return raw


def _cell(c):
    c = c.strip()
    c = re.sub(r'^\\\[merged\\\]\s*', '', c)
    c = re.sub(r'^\[merged\]\s*', '', c)
    c = re.sub(r'\\([\\`*_{}\[\]()#+\-.!~|<>])', r'\1', c)
    return c.replace('<br>', '\n').strip()


def _split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    parts, cur, esc = [], '', False
    for ch in s:
        if esc:
            cur += '\\' + ch
            esc = False
        elif ch == '\\':
            esc = True
        elif ch == '|':
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return [_cell(p) for p in parts]


def tables(text):
    """마크다운 표들 → [[행…], …]. 빈 머리줄·구분줄(:-:)은 뺀다."""
    out, cur = [], []
    for line in text.split('\n'):
        if line.strip().startswith('|'):
            row = _split_row(line)
            if all(re.match(r'^:?-+:?$', x) for x in row if x) and any(row):
                continue
            if not any(row) and not cur:
                continue
            cur.append(row)
        else:
            if cur:
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    return out


def classify(tbls):
    """머리 칸으로 탭 이름을 붙인다."""
    named, date_tabs = {}, []
    for t in tbls:
        head = t[0] if t else []
        h = [x.strip() for x in head]
        if len(h) >= 4 and h[0] == '기한' and h[2] == '할일':
            named['앞으로 할일'] = t
        elif len(h) >= 4 and h[0] == '날짜' and h[2] == '할일':
            date_tabs.append(t)
        elif len(h) >= 3 and h[0] == '날짜' and h[2].startswith('시각'):
            named['회의록'] = t
        elif len(h) >= 3 and h[0] == '수집일시' and h[2] == '지역':
            named['구글AI_백필_확정'] = t
        elif len(h) >= 3 and h[0] == '수집일시' and h[2] == '현장명':
            named['구글AI_백필_재검토필요'] = t
        elif len(h) >= 2 and h[0] == '실행일시' and h[1] == '실행유형':
            named.setdefault('구글AI_실행로그', t)
    if date_tabs:
        named['답요청'] = date_tabs[0]
    if len(date_tabs) > 1:
        named['오늘 할일'] = date_tabs[1]
    return named


FILES = {'답요청': '답요청.json', '오늘 할일': '오늘할일.json', '앞으로 할일': '앞으로할일.json', '회의록': '회의록.json',
         '구글AI_실행로그': '로그.json', '구글AI_백필_확정': '확정.json', '구글AI_백필_재검토필요': '재검토.json'}


def run(src, out):
    if not os.path.isdir(out):
        os.makedirs(out)
    named = classify(tables(_text_of(src)))
    counts, paths = {}, {}
    for tab, rows in named.items():
        p = os.path.join(out, FILES[tab])
        with io.open(p, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'range': "'%s'!A1:Z%d" % (tab, len(rows)), 'values': rows}, ensure_ascii=False))
        counts[tab] = len(rows) - 1
        paths[tab] = p
    with io.open(os.path.join(out, '줄수.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(counts, ensure_ascii=False))
    return counts, paths


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    c, p = run(sys.argv[1], sys.argv[2])
    print(json.dumps({'version': VERSION, '줄수': c, '파일': p}, ensure_ascii=False, indent=1))

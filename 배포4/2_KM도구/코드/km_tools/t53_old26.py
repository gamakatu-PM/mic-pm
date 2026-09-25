# -*- coding: utf-8 -*-
"""
53-3. meta.json → 옛 「26년 회의록」 현장 탭 7칸 줄  (km_tools / t53_old26)  AI 사용량 0

차장님 확정 (2026-09-25) : 26년 회의록에는 예전처럼 「전체모음 + 현장별」 로 기록만 한다.
  · C(내용)·F(통찰) 는 코드가 회의록에서 그대로 옮긴다 — 클로드가 새로 쓰지 않는다
  · D·E(캘린더 칸) 는 기한 있는 할 일만 적고, 구글 캘린더에는 넣지 않는다
  · 「할 일 모음」 탭에는 넣지 않는다 (할 일·체크는 26년 회의록2 한 곳)
  · 탭이 없는 현장은 새 탭 (이름 = meta.site 그대로. 복합회의·_현장미정 도 이름 그대로)
  · 넣는 것은 KM_시트쓰기.gs(old26) 가 한다. 흰 바탕, 새 탭은 현장 구역 끝

7칸 (km-11 §4-2) : A 날짜(6자리 글자) | B 담당자 | C 내용 | D 캘린더1 | E 캘린더2 | F 💡통찰 | G 회의록 링크
  A : meta.ymd. 같은 날 같은 현장 회의가 여럿이면 각각 한 줄 (시각 hm 이 있으면 B 앞에)
  B : t52.who (협의자)
  C : 안건별 「n. 제목 — 협의내용 」 줄바꿈. 끝에 빈 줄 3개 (v24 「아래가 꽉 차서 보기 힘들다」)
  D·E : 「할 일」 중 날짜(6자리) 박힌 것 앞 2개 → 「YYMMDD(예정) 무엇」. 3개 이상은 F 끝에 「그 밖의 할 일」
  F : 💡 결정사항·조치사항 (안건별). 없으면 「💡 결정 없음 — 확인 후 재협의」. 끝에 빈 줄 3개
  G : 드라이브 회의록 폴더 링크 (PLAUD 링크는 meta 에 없다)

    python t53_old26.py <meta 폴더> <나올 파일.json> [--from 260912 --to 260924] [--map 옛시트_탭이름.json]
      --map : 차장님이 정하신 {"meta.site": "옛 시트 탭 이름"} 표. 표에 없는 현장은 meta.site 그대로 새 탭
    → {"records":[{"tab","rows":[[7칸]],"person","preview"}, …], "n":건수}
"""
from __future__ import print_function
import os, sys, io, json, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t52_mailbuild as T52

VERSION = 'v1.1 2026-09-26'   # v1.1 : 할 일 칸의 「=====」 같은 구분선을 할 일로 옮기던 것 뺌 (9/26 옛 시트 96건 넣은 뒤 발견)
DRIVE_FOLDER = 'https://drive.google.com/drive/folders/1FWev-4Hzy2KmDT_H25S7BGMtpaKFeSgm'
TAIL = '\n\n\n'                       # 셀 끝 빈 줄 3개
D8 = re.compile(r'(?<!\d)(2[0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))(?!\d)')


def _todo_text(line):
    """「- 260923 | 무엇 | 배성윤 → 건축」 → (260923, 무엇 → 건축). 「- 미정 | 무엇 | 배성윤」 → ('', 무엇)"""
    s = re.sub(r'^\s*-\s*', '', line or '').strip()
    parts = [p.strip() for p in s.split('|')]
    date = ''
    if len(parts) >= 2:
        m = D8.search(parts[0])
        date = m.group(1) if m else ''
        what = parts[1]
        who = parts[2] if len(parts) > 2 else ''
        who = re.sub(r'배성윤', '', who)
        who = re.sub(r'^[\s→]+', '', who).strip()
        if who:
            what = what + ' → ' + who
    else:
        what = s
        m2 = D8.search(what)
        if m2:
            date = m2.group(1)
    return date, what


def row_of(rec, todos):
    """t52.read_meta 결과 + 원본 할 일 줄 → 7칸"""
    a = rec['ymd']
    b = rec['person']
    if rec.get('hm'):
        b = rec['hm'] + '  ' + b

    c_lines, f_lines = [], []
    for i, it in enumerate(rec['items'], 1):
        head = '%d. %s' % (i, it['title']) if it['title'] else '%d.' % i
        body = ' / '.join(it['bullets'])
        c_lines.append((head + ' — ' + body) if body else head)
        dec = it['decision']
        act = ' / '.join(it['actions'])
        if dec or act:
            f_lines.append('%d. %s%s' % (i, dec or '결정 없음', ('  → ' + act) if act else ''))
    for k, v in rec['blocks']:
        if k in ('일정', '수량·규격 변경'):
            c_lines.append('[%s] ' % k + ' / '.join(v))
    c = '\n'.join(c_lines) if c_lines else '(안건 없음)'

    dated, undated = [], []
    for t in todos:
        d, w = _todo_text(t)
        (dated if d else undated).append((d, w))
    dated.sort()
    de = ['%s(예정) %s' % (d, w) for d, w in dated]
    d_cell = de[0] if len(de) > 0 else ''
    e_cell = de[1] if len(de) > 1 else ''
    rest = de[2:] + [w for _, w in undated]

    f = '💡 ' + ('\n'.join(f_lines) if f_lines else '결정 없음 — 확인 후 재협의')
    if rest:
        f += '\n그 밖의 할 일 : ' + ' / '.join(rest)
    return [a, b, c + TAIL, d_cell, e_cell, f + TAIL, DRIVE_FOLDER]


def load_tabmap(path):
    """차장님이 정하신 「meta.site → 옛 시트 탭 이름」 표 (JSON {"조선호텔": "조선호텔 리뉴얼 "}).
       없으면 빈 표 = meta.site 그대로 새 탭. 클로드는 이 표를 채우지 않는다 (현장명 절대 규칙)."""
    if not path or not os.path.isfile(path):
        return {}
    with io.open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    return dict((str(k).strip(), str(v)) for k, v in (d or {}).items()
                if str(v).strip() and not str(k).startswith('_'))   # _설명 같은 안내 줄은 뺀다


def build(meta_dir, d_from=None, d_to=None, tabmap=None):
    tabmap = tabmap or {}
    recs = []
    for p in sorted(glob.glob(os.path.join(meta_dir, '*meta.json'))):
        try:
            r = T52.read_meta(p)
            with io.open(p, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception:
            continue
        if not r['ymd'] or not r['site_raw']:
            continue
        if d_from and r['ymd'] < d_from:
            continue
        if d_to and r['ymd'] > d_to:
            continue
        todos = ((raw.get('sec') or {}).get('2') or {}).get('할 일') or []
        todos = [t for t in todos if re.search(r'[0-9A-Za-z가-힣]', str(t))]   # v1.1 : 「=====」 구분선 제외
        recs.append((r, todos))
    recs.sort(key=lambda x: (x[0]['ymd'], x[0]['hm'], x[0]['site_raw']))

    by_tab = {}
    order = []
    for r, todos in recs:
        tab = r['site_raw'].strip()          # ★ 현장명은 meta.site 그대로 — 귀속 판단 없음
        tab = tabmap.get(tab, tab)           # 차장님 표에 있는 것만 그 탭으로 (없으면 그대로)
        if tab not in by_tab:
            by_tab[tab] = {'tab': tab, 'rows': [], 'person': r['person'], 'preview': ''}
            order.append(tab)
        by_tab[tab]['rows'].append(row_of(r, todos))
    out = []
    for tab in order:
        rec = by_tab[tab]
        first = rec['rows'][0]
        rec['preview'] = '%s / 담당자:%s / %s' % (first[0], first[1], first[2].strip().replace('\n', ' ')[:200])
        rec['person'] = first[1]
        out.append(rec)
    return {'version': VERSION, 'n': len(recs), 'records': out}


def main(argv):
    if len(argv) < 3:
        print(__doc__); return 2
    d_from = d_to = mp = None
    i = 3
    while i < len(argv):
        if argv[i] == '--from':
            d_from = argv[i + 1]; i += 2
        elif argv[i] == '--to':
            d_to = argv[i + 1]; i += 2
        elif argv[i] == '--map':
            mp = argv[i + 1]; i += 2
        else:
            i += 1
    res = build(argv[1], d_from, d_to, load_tabmap(mp))
    with io.open(argv[2], 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({'version': VERSION, '회의': res['n'], '탭': [(r['tab'], len(r['rows'])) for r in res['records']]}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

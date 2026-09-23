# -*- coding: utf-8 -*-
"""
53. 아침 메일 3통 원고 만들기  (km_tools / t53_daily)

meta.json 만 읽는다. 클로드(AI)를 전혀 쓰지 않는다 → 사용량 0.

    python t53_daily.py <meta폴더> [--today 260923] [--out 폴더] [--sheet <26년 할 일 모음 링크>]
    python t53_daily.py <meta폴더> --from 260901 --to 260915 [--out 폴더]     기간 지정
    python t53_daily.py <meta폴더> --month 2609                                 한 달
    python t53_daily.py <meta폴더> --day 260915                                 하루
    python t53_daily.py --merge <시트계획.json> "답요청=8-60" "오늘 할일=2-12" "회의록=2-80"   덧붙인 줄 번호로 병합 본문

만드는 것 (v4 추가)
    오늘의정리_YYMMDD.txt     ①②③ 을 순서대로 한 통에. 제목 [KM] 오늘의 정리 입니다. YYYY-MM-DD (요일)
    시트_답요청_·시트_오늘할일_·시트_회의록_YYMMDD.json   「26년 회의록2」 각 탭에 Zapier add_row_lines 로 넣을 rows
    시트계획_YYMMDD.json      덧붙인 뒤 병합할 칸 계산용

만드는 것 (오늘 = YYMMDD)
    답해주십시오_YYMMDD.txt   ① 어제 회의록에서 새로 생긴 「할 일」 하루치 + 시트 링크
    할일추가_YYMMDD.csv       ① 과 같은 내용. 「26년 할 일 모음」 시트에 덧붙일 줄 (날짜|종류|현장|할일|어디서|완료)
    오늘할것_YYMMDD.txt       ② 회의록 「할 일」·「일정」 중 날짜가 오늘인 것만. 지난 것은 안 적는다
    어제있었던일_YYMMDD.txt   ③ 어제 회의록 전문 정리. 현장명 → 날짜 사람 → 안건/협의내용/결정사항/조치사항
    아침3통_YYMMDD.json       몇 건을 어디서 뽑았는지 (자가진단)

차장님 확정 (2026-09-23)
    · ① 은 하루치. 쌓인 것은 시트에서 보신다 → 메일에 「N일 지남」 을 적지 않는다
    · ② 는 오늘 날짜인 것만
    · ③ 은 현장별 회의 수 = meta.json 수 (PLAUD 회의록 수와 정확히 일치)
    · 현장명은 차장님이 손으로 넣으신 것(meta.site) 그대로. 도구가 바꾸지 않는다
    · 여러 현장이 섞인 회의(복합회의 등)는 「현장이 아닌 것」 으로 따로 둔다
"""
from __future__ import print_function
import os, sys, io, json, re, csv, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t52_mailbuild as T52

VERSION = 'v4 2026-09-23'   # v4 : 3통 → 1통 「오늘의 정리」 · 시트 「26년 회의록2」 탭 3개(답요청·오늘 할일·회의록)에 날짜별 누적
# v3 : 종류 칸 삭제 · 날짜 = 회의한 날(기한은 할일 글 끝에) · 기간 지정(--from --to / --month)

# 「26년 할 일 모음」 시트의 종류 칸. 차장님 예시(26년 회의록 시트)에 나온 낱말 그대로.
KINDS = ('발송', '도면', '회의', '확인', '전달', '샘플', '제작', '발행', '설치',
         '납품', '회신', '제출', '계약', '발주', '연락')
SHEET_NAME = '26년 회의록2'
TABS = ('답요청', '오늘 할일', '회의록')          # sheetId 0 · 1 · 2 (2026-09-23 만들 때 고정)
TAB_ID = {'답요청': 0, '오늘 할일': 1, '회의록': 2}
MEET_HEAD = ['날짜', '현장', '시각·협의자', '안건', '협의내용', '결정사항', '조치사항']
SHEET_HEAD = ['날짜', '현장', '할일', '완료']   # 차장님 확정 (2026-09-23) : 종류 칸 없음. 날짜 = 회의한 날. 완료 = 차장님 체크

TODO_RE = re.compile(r'^\s*[-·•]?\s*(\d{6}|미정)\s*\|\s*(.+?)\s*(?:\|\s*(.*?))?\s*$')
SCHED_RE = re.compile(r'^\s*[-·•]?\s*([^|]+?)\s*\|\s*(\d{6})\s*\|\s*(.+?)\s*$')


def _iso(ymd):
    """260922 -> 2026-09-22. 미정·빈칸은 빈칸 (차장님 예시 : 기한 미지정은 날짜 칸이 비어 있다)."""
    if not ymd or not re.match(r'^\d{6}$', ymd):
        return ''
    return '20%s-%s-%s' % (ymd[:2], ymd[2:4], ymd[4:6])


def _row_line(date, site, what):
    return '%s\t%s\t%s' % (date, site, what)


def _todo_text(ymd, what, whom):
    """할일 글 = 무엇 + (기한 2026-09-23) + (배성윤 → 누구). 기한이 없으면 안 붙인다."""
    t = what
    if _iso(ymd):
        t += '  (기한 %s)' % _iso(ymd)
    if whom:
        t += '  (%s)' % whom
    return t


def kind_of(text):
    """할 일 글에서 종류를 고른다. 낱말이 없으면 「확인」."""
    for k in KINDS:
        if k in text:
            return k
    return '확인'


def parse_todo(line):
    """'- 260922 | 무엇 | 배성윤 → 누구'  ->  (날짜|미정, 무엇, 누구)"""
    m = TODO_RE.match(line or '')
    if not m:
        return None
    return m.group(1), m.group(2).strip(), (m.group(3) or '').strip()


def _who(m):
    w = T52.who(m)
    person = re.sub(r'\s+', ' ', (m.get('person') or '')).strip()
    if person and (w == '상대 미상' or re.sub(r'\s', '', w) == re.sub(r'\s', '', person)):
        return person
    return w


def read_raw(path):
    with io.open(path, 'r', encoding='utf-8-sig') as f:
        d = json.load(f)
    m = d.get('meta') or {}
    s1 = (d.get('sec') or {}).get('1') or {}
    s2 = (d.get('sec') or {}).get('2') or {}
    rec = {
        'file': os.path.basename(path),
        'site': re.sub(r'\s+', ' ', (m.get('site') or s1.get('현장') or '')).strip(),   # ★ 손으로 넣으신 그대로
        'key': T52.norm_site(m.get('site') or s1.get('현장') or ''),
        'ymd': m.get('ymd') or '',
        'hm': m.get('hm') or '',
        'person': _who(m),
        'items': [],
        'todos': [],
        'sched': [],
    }
    for it in (s1.get('안건목록') or []):
        if not isinstance(it, dict):
            continue
        rec['items'].append({
            'title': T52._clean(it.get('title') or ''),
            'bullets': T52._lines(it.get('bullets')),
            'decision': T52._clean(it.get('decision') or ''),   # ★ 「없음 — …」 도 그대로 보여드린다
            'actions': T52._lines(it.get('actions')),
        })
    for ln in T52._lines(s2.get('할 일')):
        t = parse_todo(ln)
        if t:
            rec['todos'].append(t)
    for ln in T52._lines(s1.get('일정')):
        m2 = SCHED_RE.match(ln)
        if m2:
            rec['sched'].append((m2.group(2), m2.group(1).strip(), m2.group(3).strip()))
    return rec


def collect(meta_dir):
    recs, skipped = [], []
    for root, _dirs, files in os.walk(meta_dir):
        for fn in sorted(files):
            if not fn.endswith('meta.json') or fn.startswith('_삭제요망'):
                continue
            try:
                recs.append(read_raw(os.path.join(root, fn)))
            except Exception as e:
                skipped.append((fn, str(e)))
    return recs, skipped


def _group(recs):
    """현장별로 묶는다. (현장 목록, 현장이 아닌 것 목록, 묶음)"""
    rep = T52.merge_sites([r['key'] for r in recs])
    byk = {}
    for r in recs:
        byk.setdefault(rep.get(r['key'], r['key']) or '현장미정', []).append(r)
    bag = {}
    for k, rs in byk.items():
        rs.sort(key=lambda r: (r['ymd'], r['hm'] or '99:99', r['file']))
        bag[rs[0]['site'] or '현장미정'] = rs
    sites = sorted([k for k in bag if T52.is_site(k)], key=lambda k: (-len(bag[k]), k))
    others = sorted([k for k in bag if not T52.is_site(k)], key=lambda k: (-len(bag[k]), k))
    return sites, others, bag


def _names(recs):
    """공백만 다른 이름(앵커호텔/앵커 호텔)은 한 현장. 이름은 그 묶음 첫 회의의 site 그대로."""
    _s, _o, bag = _group(recs)
    out = {}
    for name, rs in bag.items():
        for r in rs:
            out[r['key']] = name
    return out


def _head(title, day):
    return ['%s  %s (%s)' % (title, day.strftime('%Y-%m-%d'), T52.WD[day.weekday()]), '']


def _src(r):
    return '%s 회의 %s%s' % (T52._d(r['ymd']), (r['hm'] + ' ') if r['hm'] else '', r['person'] or '')


# ── ① 답해 주십시오 ─────────────────────────────────────────
def todo_rows(recs_y):
    """어제 회의록에서 새로 생긴 할 일 → 시트 줄(날짜|종류|현장|할일|완료). 현장명은 meta.site 그대로."""
    rows, seen = [], set()
    nm = _names(recs_y)
    for r in recs_y:
        site = nm.get(r['key'], r['site'])
        for ymd, what, whom in r['todos']:
            key = (site, what)
            if key in seen:
                continue
            seen.add(key)
            rows.append({'날짜': _iso(r['ymd']), '현장': site, '할일': _todo_text(ymd, what, whom), '완료': ''})
    return rows


def build_answer(recs_y, yday, sheet_url=''):
    """차장님 지시 : 하루치 내용을 메일에 적고, 「26년 할 일 모음」 링크를 넣는다. 그 밖의 말은 안 적는다."""
    rows = todo_rows(recs_y)
    L = []
    for row in sorted(rows, key=lambda x: (not T52.is_site(x['현장']), x['현장'], x['날짜'])):
        L.append(_row_line(row['날짜'], row['현장'], row['할일']))
    if not rows:
        L.append('(%s 회의록에서 새로 생긴 할 일 없음)' % _iso(yday.strftime('%y%m%d')))
    L.append('')
    L.append('%s : %s' % (SHEET_NAME, sheet_url or '(링크 없음)'))
    return '\n'.join(L), rows


# ── ② 오늘 할 것 ────────────────────────────────────────────
def build_today(recs_all, today):
    """차장님 지시 : 회의록 「할 일」 중 날짜가 오늘인 것만. 지난 것·미정은 안 적는다."""
    ty = today.strftime('%y%m%d')
    picked, seen = [], set()
    nm = _names(recs_all)
    for r in recs_all:
        site = nm.get(r['key'], r['site'])
        for ymd, what, whom in r['todos']:
            if ymd == ty and (site, what) not in seen:
                seen.add((site, what))
                picked.append((site, what + (('  (%s)' % whom) if whom else ''), _iso(r['ymd'])))
    picked.sort(key=lambda x: (not T52.is_site(x[0]), x[0]))
    L = [_row_line(_iso(ty), site, what) for site, what, _src in picked]
    if not picked:
        L.append('(회의록에 %s 로 적힌 할 일 없음)' % _iso(ty))
    return '\n'.join(L), picked


# ── ③ 어제 있었던 일 ────────────────────────────────────────
def build_yesterday(recs_y, yday):
    """차장님 모양 (2026-09-23 원문) :
         1. 현장명
         (빈 줄)
         날짜   사람이름
         (빈 줄)
         안건 : …
         협의내용 : 첫 줄
         다음 줄들…
         결정사항 : …
         조치사항 : …
         (안건이 있을 때마다 「날짜 사람이름」 부터 다시)
       머리말·꼬리말·건수 설명은 적지 않는다."""
    sites, others, bag = _group(recs_y)
    L = []

    def one(idx, name, rs):
        L.append('%d. %s' % (idx, name))
        L.append('')
        for r in rs:
            head = '%s   %s%s' % (T52._d(r['ymd']), (r['hm'] + '  ') if r['hm'] else '', r['person'] or '상대 미상')
            items = r['items'] or [{'title': '(안건 없음)', 'bullets': [], 'decision': '', 'actions': []}]
            for it in items:
                L.append(head)
                L.append('')
                L.append('안건 : %s' % it['title'])
                b = it['bullets'] or ['']
                L.append('협의내용 : %s' % b[0])
                for x in b[1:]:
                    L.append(x)
                L.append('결정사항 : %s' % (it['decision'] or '없음'))
                L.append('조치사항 : %s' % ' / '.join(it['actions']))
                L.append('')
        L.append('')

    n = 0
    if not recs_y:
        L.append('(%s 회의록 없음)' % _iso(yday.strftime('%y%m%d')))
    for name in sites:
        n += 1
        one(n, name, bag[name])
    if others:
        L.append('※ 현장이 아닌 것 — 어느 현장 것인지는 차장님이 정하십시오')
        L.append('')
        for name in others:
            n += 1
            one(n, name, bag[name])
    return '\n'.join(L).rstrip('\n') + '\n', {s: len(bag[s]) for s in sites + others}


# ── 시트 「26년 회의록2」 에 넣을 줄 ──────────────────────────
def _kday(ymd):
    """260922 -> 26년 09월 22일"""
    return '%s년 %s월 %s일' % (ymd[:2], ymd[2:4], ymd[4:6])


def meet_title(yy, n):
    """차장님 지시 : 「oo년 oo월 oo일_회의 oo건」"""
    return '%s_회의 %d건' % (_kday(yy), n)


def meet_rows(recs_y):
    """회의록 탭 : 날짜 | 현장 | 시각·협의자 | 안건 | 협의내용 | 결정사항 | 조치사항  (안건 하나가 한 줄)"""
    sites, others, bag = _group(recs_y)
    out = []
    for name in sites + others:
        for r in bag[name]:
            who = '%s%s' % ((r['hm'] + '  ') if r['hm'] else '', r['person'] or '상대 미상')
            for it in (r['items'] or [{'title': '(안건 없음)', 'bullets': [], 'decision': '', 'actions': []}]):
                out.append([_iso(r['ymd']), name, who, it['title'], '\n'.join(it['bullets']),
                            it['decision'] or '없음', ' / '.join(it['actions'])])
    return out


def sheet_plan(rows, picked, recs_y, today, yday):
    """탭별로 덧붙일 줄과, 덧붙인 뒤 합칠 칸.
       kind : 'date' = A열 날짜 세로 병합 / 'title' = 첫 줄 제목(A:G 병합·굵게) + 나머지 A열 병합"""
    yy = yday.strftime('%y%m%d')
    ty = today.strftime('%y%m%d')
    plan = {}
    plan['답요청'] = {'kind': 'date', 'cols': 4,
                     'values': [[r['날짜'], r['현장'], r['할일'], ''] for r in rows]}
    plan['오늘 할일'] = {'kind': 'date', 'cols': 4,
                      'values': [[_iso(ty), site, what, ''] for site, what, _k in picked]}
    mr = meet_rows(recs_y)
    plan['회의록'] = {'kind': 'title', 'cols': len(MEET_HEAD),
                    'values': ([[meet_title(yy, len(recs_y))] + [''] * (len(MEET_HEAD) - 1)] + mr) if mr else []}
    return plan


def zap_rows(values):
    """Zapier add_row_lines 의 rows 모양으로. 빈 칸은 뺀다."""
    out = []
    for v in values:
        out.append(dict(('COL$%s' % chr(65 + i), x) for i, x in enumerate(v) if x != ''))
    return out


def merge_body(plan, ranges):
    """덧붙인 줄 범위 (예 '회의록'!A12:G40  또는  12-40) 를 받아 병합 batchUpdate 본문을 만든다."""
    req = []
    for tab, rng in ranges.items():
        if not rng or tab not in plan:
            continue
        m = re.search(r'!A(\d+)(?::[A-Z]+(\d+))?', rng) or re.match(r'^\s*(\d+)\s*(?:-\s*(\d+))?\s*$', rng)
        if not m:
            continue
        top = int(m.group(1)) - 1                        # 0 부터
        bot = int(m.group(2) or m.group(1))              # 끝 (포함 안 함)
        sid = TAB_ID[tab]
        cols = plan[tab]['cols']
        if plan[tab]['kind'] == 'title':
            req.append({'mergeCells': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': top + 1,
                                                 'startColumnIndex': 0, 'endColumnIndex': cols}, 'mergeType': 'MERGE_ALL'}})
            req.append({'repeatCell': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': top + 1,
                                                 'startColumnIndex': 0, 'endColumnIndex': cols},
                                       'cell': {'userEnteredFormat': {'textFormat': {'bold': True},
                                                                      'horizontalAlignment': 'LEFT',
                                                                      'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8}}},
                                       'fields': 'userEnteredFormat(textFormat,horizontalAlignment,backgroundColor)'}})
            top += 1
        if bot - top >= 2:
            req.append({'mergeCells': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': bot,
                                                 'startColumnIndex': 0, 'endColumnIndex': 1}, 'mergeType': 'MERGE_ALL'}})
    return {'requests': req}


# ── 한 통으로 ─────────────────────────────────────────────
def build_one(t1, t2, t3, rows, picked, recs_y, today, yday, sheet_url=''):
    """차장님 지시 (2026-09-23) : 3통을 순서대로 한 통에. 제목 [KM] 오늘의 정리 입니다. 날짜"""
    yy = yday.strftime('%y%m%d')
    t1_body = '\n'.join(ln for ln in t1.split('\n') if not ln.startswith(SHEET_NAME + ' :')).rstrip('\n')
    L = ['%s : %s' % (SHEET_NAME, sheet_url or '(링크 없음)'), '']
    L.append('━━ 1. 답해 주십시오 ━━  %s 회의에서 생긴 할 일 %d건' % (T52._d(yy), len(rows)))
    L.append('')
    L.append(t1_body)
    L.append('')
    L.append('━━ 2. 오늘 할 것 ━━  %s · %d건' % (_iso(today.strftime('%y%m%d')), len(picked)))
    L.append('')
    L.append(t2.rstrip('\n'))
    L.append('')
    L.append('━━ 3. 어제 있었던 일 ━━  %s' % meet_title(yy, len(recs_y)))
    L.append('')
    L.append(t3.rstrip('\n'))
    subject = '[KM] 오늘의 정리 입니다. %s (%s)' % (today.strftime('%Y-%m-%d'), T52.WD[today.weekday()])
    return '\n'.join(L) + '\n', subject


# ── 한 번에 ───────────────────────────────────────────────
def run(meta_dir, today=None, out=None, sheet_url=''):
    today = today or datetime.date.today()
    yday = today - datetime.timedelta(days=1)
    yy = yday.strftime('%y%m%d')
    recs_all, skipped = collect(meta_dir)
    recs_y = [r for r in recs_all if r['ymd'] == yy]

    t1, rows = build_answer(recs_y, yday, sheet_url)
    t2, picked = build_today(recs_all, today)
    t3, per_site = build_yesterday(recs_y, yday)

    out = out or meta_dir
    if not os.path.isdir(out):
        os.makedirs(out)
    st = today.strftime('%y%m%d')
    paths = {}
    for name, txt in (('답해주십시오', t1), ('오늘할것', t2), ('어제있었던일', t3)):
        p = os.path.join(out, '%s_%s.txt' % (name, st))
        with io.open(p, 'w', encoding='utf-8') as f:
            f.write(txt)
        paths[name] = p
    p = os.path.join(out, '할일추가_%s.csv' % st)
    with io.open(p, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=SHEET_HEAD)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    paths['할일추가'] = p

    one, subject = build_one(t1, t2, t3, rows, picked, recs_y, today, yday, sheet_url)
    p = os.path.join(out, '오늘의정리_%s.txt' % st)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(one)
    paths['오늘의정리'] = p
    plan = sheet_plan(rows, picked, recs_y, today, yday)
    for tab in TABS:
        p = os.path.join(out, '시트_%s_%s.json' % (tab.replace(' ', ''), st))
        with io.open(p, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'rows': zap_rows(plan[tab]['values'])}, ensure_ascii=False))
        paths['시트_' + tab] = p
    p = os.path.join(out, '시트계획_%s.json' % st)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(plan, ensure_ascii=False))
    paths['시트계획'] = p

    stat = {'version': VERSION, '오늘': st, '어제': yy, '제목': subject,
            '시트줄': dict((t, len(plan[t]['values'])) for t in TABS),
            'meta전체': len(recs_all), '어제회의': len(recs_y),
            '어제_현장별': per_site,
            '①할일': len(rows), '②오늘': len(picked),
            '건너뜀': skipped, '파일': paths}
    with io.open(os.path.join(out, '아침3통_%s.json' % st), 'w', encoding='utf-8') as f:
        f.write(json.dumps(stat, ensure_ascii=False, indent=1))
    return (t1, t2, t3), stat


def run_range(meta_dir, d_from, d_to, out=None, sheet_url=''):
    """차장님이 정한 기간(YYMMDD~YYMMDD)의 회의록을 ③ 모양으로 정리 + 그 기간에 생긴 할 일 줄.
         기간정리_<from>-<to>.txt   ③ 모양 (현장 → 날짜 사람 → 안건/협의내용/결정사항/조치사항)
         기간할일_<from>-<to>.txt   날짜\t현장\t할일 줄 + 시트 링크
         기간할일_<from>-<to>.csv   시트에 넣을 줄
         기간_<from>-<to>.json      건수"""
    recs_all, skipped = collect(meta_dir)
    recs = [r for r in recs_all if r['ymd'] and d_from <= r['ymd'] <= d_to]
    recs.sort(key=lambda r: (r['ymd'], r['hm'] or '99:99', r['file']))
    sites, others, bag = _group(recs)
    L = []
    n = 0

    def one(idx, name, rs):
        L.append('%d. %s' % (idx, name))
        L.append('')
        for r in rs:
            head = '%s   %s%s' % (T52._d(r['ymd']), (r['hm'] + '  ') if r['hm'] else '', r['person'] or '상대 미상')
            items = r['items'] or [{'title': '(안건 없음)', 'bullets': [], 'decision': '', 'actions': []}]
            for it in items:
                L.append(head)
                L.append('')
                L.append('안건 : %s' % it['title'])
                b = it['bullets'] or ['']
                L.append('협의내용 : %s' % b[0])
                for x in b[1:]:
                    L.append(x)
                L.append('결정사항 : %s' % (it['decision'] or '없음'))
                L.append('조치사항 : %s' % ' / '.join(it['actions']))
                L.append('')
        L.append('')

    if not recs:
        L.append('(%s ~ %s 회의록 없음)' % (_iso(d_from), _iso(d_to)))
    for name in sites:
        n += 1
        one(n, name, bag[name])
    if others:
        L.append('※ 현장이 아닌 것 — 어느 현장 것인지는 차장님이 정하십시오')
        L.append('')
        for name in others:
            n += 1
            one(n, name, bag[name])
    t_meet = '\n'.join(L).rstrip('\n') + '\n'

    rows = todo_rows(recs)
    M = [_row_line(row['날짜'], row['현장'], row['할일'])
         for row in sorted(rows, key=lambda x: (x['날짜'], not T52.is_site(x['현장']), x['현장']))]
    if not rows:
        M.append('(%s ~ %s 할 일 없음)' % (_iso(d_from), _iso(d_to)))
    M.append('')
    M.append('%s : %s' % (SHEET_NAME, sheet_url or '(링크 없음)'))
    t_todo = '\n'.join(M)

    out = out or meta_dir
    if not os.path.isdir(out):
        os.makedirs(out)
    tag = '%s-%s' % (d_from, d_to)
    paths = {}
    for name, txt in (('기간정리', t_meet), ('기간할일', t_todo)):
        p = os.path.join(out, '%s_%s.txt' % (name, tag))
        with io.open(p, 'w', encoding='utf-8') as f:
            f.write(txt)
        paths[name] = p
    p = os.path.join(out, '기간할일_%s.csv' % tag)
    with io.open(p, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=SHEET_HEAD)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    paths['기간할일csv'] = p
    stat = {'version': VERSION, '기간': [_iso(d_from), _iso(d_to)], 'meta전체': len(recs_all),
            '회의': len(recs), '현장': len(sites), '현장별': {k: len(bag[k]) for k in sites + others},
            '할일': len(rows), '건너뜀': skipped, '파일': paths}
    with io.open(os.path.join(out, '기간_%s.json' % tag), 'w', encoding='utf-8') as f:
        f.write(json.dumps(stat, ensure_ascii=False, indent=1))
    return (t_meet, t_todo), stat


def _month_range(yymm):
    y, m = 2000 + int(yymm[:2]), int(yymm[2:4])
    last = (datetime.date(y + (m == 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)).day
    return '%s01' % yymm, '%s%02d' % (yymm, last)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == '--merge':
        # python3 t53_daily.py --merge <시트계획.json> "답요청=<updatedRange>" "오늘 할일=<updatedRange>" "회의록=<updatedRange>"
        with io.open(argv[2], 'r', encoding='utf-8') as f:
            plan = json.load(f)
        ranges = dict(a.split('=', 1) for a in argv[3:] if '=' in a)
        print(json.dumps(merge_body(plan, ranges), ensure_ascii=False))
        return 0
    meta_dir, today, out, sheet = argv[1], None, None, ''
    d_from = d_to = None
    i = 2
    while i < len(argv):
        if argv[i] == '--today':
            today = datetime.datetime.strptime(argv[i + 1], '%y%m%d').date(); i += 2
        elif argv[i] == '--out':
            out = argv[i + 1]; i += 2
        elif argv[i] == '--sheet':
            sheet = argv[i + 1]; i += 2
        elif argv[i] == '--from':
            d_from = argv[i + 1]; i += 2
        elif argv[i] == '--to':
            d_to = argv[i + 1]; i += 2
        elif argv[i] == '--month':                       # --month 2609
            d_from, d_to = _month_range(argv[i + 1]); i += 2
        elif argv[i] == '--day':                         # --day 260915  (하루)
            d_from = d_to = argv[i + 1]; i += 2
        else:
            i += 1
    if d_from or d_to:
        d_from = d_from or d_to
        d_to = d_to or d_from
        _t, stat = run_range(meta_dir, d_from, d_to, out, sheet)
    else:
        _t, stat = run(meta_dir, today, out, sheet)
    print(json.dumps(stat, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

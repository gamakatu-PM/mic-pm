# -*- coding: utf-8 -*-
"""
53. 아침 메일 3통 원고 만들기  (km_tools / t53_daily)

meta.json 만 읽는다. 클로드(AI)를 전혀 쓰지 않는다 → 사용량 0.

    python t53_daily.py <meta폴더> [--today 260923] [--out 폴더] [--sheet <26년 할 일 모음 링크>]
    python t53_daily.py <meta폴더> --from 260901 --to 260915 [--out 폴더]     기간 지정
    python t53_daily.py <meta폴더> --month 2609                                 한 달
    python t53_daily.py <meta폴더> --day 260915                                 하루
    python t53_daily.py <meta폴더> --today 260924 --radar <로그.json,확정.json,재검토.json>   4. 신규 현장 레이더 칸 넣기
    python t53_daily.py <meta폴더> --today 260924 --done <답요청.json,오늘할일.json>          v7 시트에 완료 표시한 할 일은 ①② 에서 뺀다
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

VERSION = 'v12 2026-09-24'  # v12 : 한 곳·한 통·두 동작 (차장님 「1번으로」) — 시트 E열 ▼고르기(진행중·아니야·맞아·만들어줘)·F열 메모·G열 현장(걸러보기) / 메일 맨 위 자료 상태·급한 것 5줄·▼고르신 것
# v11 2026-09-23  # v11 : 체크가 곧 소통 — 체크 안 한 것은 계속 적는다. ① 기한 없는 지난 할 일 · ② 기한 지난 할 일(원래 기한 아래) · ⑤ 앞으로 할 것 + 시트 4번째 탭 「앞으로 할일」
# v10 2026-09-23  # v10 : 「26년 회의록2」 에 들어가는 것 전부 — ①② 메일·시트 답요청·오늘 할일 : 「- 」 + 담당 괄호 뺌. 기간 메일은 그대로
# v9 2026-09-23   # v9 : 메일 ① 만 — 할 일 앞에 「- 」, 오른쪽 담당 괄호 뺌 (기한 괄호는 그대로). ②·시트·기간 메일은 안 바꿈
# v8 2026-09-23   # v8 : 답요청·오늘 할일 완료 칸(D열) = 체크박스 (체크 = 「완료」, 끄면 빈칸)
# v7 2026-09-23   # v7 : 담당 칸의 「배성윤 →」 뺌 · 시트에서 완료 표시한 할 일은 메일 ①② 에서 뺌 (--done)
# v6 2026-09-23   # v6 : ①② 날짜·현장은 머리줄로 한 번만 (할 일은 들여쓰기) · 시트 답요청·오늘 할일 현장 칸(B열) 세로 병합
# v5 : 「신규 현장 레이더」 결과를 한 통 끝(4번)에 합침
# v4 : 3통 → 1통 「오늘의 정리」 · 시트 「26년 회의록2」 탭 3개(답요청·오늘 할일·회의록)에 날짜별 누적
# v3 : 종류 칸 삭제 · 날짜 = 회의한 날(기한은 할일 글 끝에) · 기간 지정(--from --to / --month)

# 「26년 할 일 모음」 시트의 종류 칸. 차장님 예시(26년 회의록 시트)에 나온 낱말 그대로.
KINDS = ('발송', '도면', '회의', '확인', '전달', '샘플', '제작', '발행', '설치',
         '납품', '회신', '제출', '계약', '발주', '연락')
SHEET_NAME = '26년 회의록2'
TABS = ('답요청', '오늘 할일', '회의록', '앞으로 할일')          # sheetId 0 · 1 · 2 · 3 (2026-09-23 만들 때 고정)
TAB_ID = {'답요청': 0, '오늘 할일': 1, '회의록': 2, '앞으로 할일': 3}
FUTURE_HEAD = ['기한', '현장', '할일', '완료']
EXTRA_HEAD = ['고르기', '메모', '현장(걸러보기)']   # v12 : E·F·G 열 (답요청·오늘 할일·앞으로 할일)
PICKS = ('진행중', '아니야', '맞아', '만들어줘')    # v12 : E열 ▼ 목록. 완료는 D열 체크로만
_PICK = {}            # v12 : run() 이 시트에서 읽어 채운다. key -> (고르기, 메모)
_BOARD_TABS = set()   # v12 : 읽은 탭 (자료 상태 줄)
_TODAY_ITEMS = []     # v12 : ② 줄 (급한 것 5줄 재료)   # v11 차장님 (2026-09-23) : 앞으로 날짜가 있는 할 일 — 체크할 때까지 계속
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


def _grouped(items, bullet='  '):
    """v6 차장님 확정 (2026-09-23 「날짜와 현장명이 반복되는 것은 하나만」 → A. 머리줄로 한 번) :
         2026-09-22
         (빈 줄)
         수유초등학교
           할 일
           할 일
         (빈 줄)
         앵커 호텔
           할 일
       items = [(날짜, 현장, 할일)] 이미 정렬된 것. 날짜가 바뀌면 날짜 줄, 현장이 바뀌면 현장 줄만 다시."""
    L, last_d, last_s = [], None, None
    for d, site, what in items:
        if d != last_d:
            if L:
                L.append('')
            L.append(d or '(기한 미정)')
            last_d, last_s = d, None
        if site != last_s:
            L.append('')
            L.append(site)
            last_s = site
        L.append(bullet + deco(site, what))
    return L


def _whom(whom):
    """v7 차장님 (2026-09-23) : 「내가 배성윤인데 (배성윤 → …) 는 빼」 → 앞의 「배성윤 →」 만 뺀다. 상대는 남긴다."""
    w = re.sub(r'^\s*배성윤\s*(?:→|->|>)\s*', '', whom or '').strip()
    return '' if w == '배성윤' else w


def _core(text):
    """할일 글에서 뒤에 붙은 「  (기한 …)」「  (담당)」 을 떼고 무엇만. 완료 대조용."""
    t = re.sub(r'^\s*-\s+', '', str(text or ''))          # v10 : 시트 글 앞 「- 」 도 뗀다
    return re.sub(r'\s+', ' ', t.split('  (')[0]).strip()


def sheet_text(text):
    """v10 차장님 (2026-09-23 「시트에 들어가는 것들은 다 적용」) : 시트 할일 글 = 「- 」 + 무엇 + (기한 …). 담당 괄호는 뺀다.
       옛 글 「무엇  (기한 2026-09-23)  (배성윤 → 확인 예정)」 → 「- 무엇  (기한 2026-09-23)」"""
    t = re.sub(r'^\s*-\s+', '', str(text or '')).strip()
    parts = t.split('  (')
    keep = [parts[0].strip()] + ['(' + x for x in parts[1:] if x.startswith('기한 ')]
    return '- ' + '  '.join(keep) if keep[0] else ''



def _todo_text(ymd, what, whom):
    """할일 글 = 무엇 + (기한 2026-09-23) + (배성윤 → 누구). 기한이 없으면 안 붙인다."""
    t = what
    if _iso(ymd):
        t += '  (기한 %s)' % _iso(ymd)
    whom = _whom(whom)
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


# ── 완료 표시 (v7) ─────────────────────────────────────────
DONE_NO = ('', 'FALSE', 'false', '0', '미완료', 'N', 'n', '-')


def _cell_date(v):
    """시트 날짜 칸 → 'YYYY-MM-DD'. 「2026-09-22」 도, 날짜 서식이 없어 숫자(46287)로 보이는 것도 받는다."""
    v = str(v or '').strip()
    m = re.match(r'^(\d{4})\D(\d{1,2})\D(\d{1,2})', v)
    if m:
        return '%s-%02d-%02d' % (m.group(1), int(m.group(2)), int(m.group(3)))
    if re.match(r'^\d{5}(\.0+)?$', v):
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(v)))).isoformat()
    return ''


def _due_in(text):
    m = re.search(r'\(기한 (\d{4}-\d{2}-\d{2})\)', str(text or ''))
    return m.group(1) if m else ''


def load_board(path):
    """v11 : 「26년 회의록2」 답요청·오늘 할일·앞으로 할일 탭을 읽은 응답 파일(들) → 줄 목록.
       path : 쉼표로 여럿. Zapier 응답 그대로 / values:get 모두 받는다. 칸 : 날짜(기한) | 현장 | 할일 | 완료
       병합된 칸(날짜·현장)은 아래 줄이 비어 있으므로 위 값을 내려 쓴다. 어느 탭인지는 응답의 range 이름으로 가린다.
       기한 : 답요청은 글 끝 「(기한 …)」, 오늘 할일·앞으로 할일은 A열 날짜.
       완료 칸이 비었거나 FALSE·0·미완료 가 아니면 완료로 본다 (체크박스 「완료」·TRUE 모두)."""
    out = []
    for one in [x for x in str(path or '').split(',') if x.strip()]:
        if not os.path.isfile(one.strip()):
            continue
        with io.open(one.strip(), 'r', encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, dict) and 'results' in d:
            d = d['results'][0].get('body', d)
        blocks = d.get('valueRanges') if isinstance(d, dict) and 'valueRanges' in d else [d]
        for blk in blocks:
            rng = str(blk.get('range', ''))
            tab = '앞으로 할일' if '앞으로' in rng else ('오늘 할일' if '오늘' in rng else '답요청')
            _BOARD_TABS.add(tab)
            date = site = ''
            for row in (blk.get('values') or [])[1:]:
                row = [str(x) for x in row] + [''] * 7
                if _cell_date(row[0]):
                    date = _cell_date(row[0])
                if row[1].strip():
                    site = row[1].strip()
                if not _core(row[2]):
                    continue
                due = _due_in(row[2]) if tab == '답요청' else date
                out.append({'tab': tab, 'date': date, 'site': site, 'text': row[2], 'due': due,
                            'done': row[3].strip() not in DONE_NO,
                            'pick': row[4].strip(), 'memo': row[5].strip(),
                            'key': (T52.norm_site(site), _core(row[2]))})
    return out


def load_done(path):
    """완료 표시된 할 일 (v7). v11 부터 load_board 를 쓴다."""
    return _done_of(load_board(path))


def _done_of(board):
    done = {'pair': set(), 'what': set()}
    for b in board or []:
        if b['done']:
            done['pair'].add(b['key'])
            done['what'].add(b['key'][1])
    return done


def _key(site, what):
    return (T52.norm_site(site), _core(what))


def pick_map(board):
    """v12 : E열 ▼고르기 · F열 메모 → {key: (고르기, 메모)}. 체크(완료)한 것은 뺀다."""
    dn = _done_of(board)
    out = {}
    for b in board or []:
        if b['key'] in dn['pair'] or not (b.get('pick') or b.get('memo')):
            continue
        out[b['key']] = (b.get('pick', ''), b.get('memo', ''))
    return out


def deco(site, text):
    """v12 차장님 확정 (2026-09-24 「1번으로」) : ▼고르신 것을 메일 줄에 붙인다.
         진행중 → 「(진행중) 할일」 · 아니야 → 「할일 → 메모」 · 맞아 → 「(맞아) 할일」 · 만들어줘 → 「(만들어줘) 할일」"""
    p = _PICK.get(_key(site, text))
    if not p:
        return text
    pick, memo = p
    if pick == '진행중':
        return '(진행중) ' + text
    if pick == '아니야':
        return (text + ' → ' + memo) if memo else '(아니야) ' + text
    if pick in ('맞아', '만들어줘'):
        return '(%s) %s' % (pick, text)
    return text


def _is_done(done, site, what):
    """같은 현장 + 같은 할일(무엇) 이면 완료. 현장명 띄어쓰기 차이는 norm_site 로 맞춘다."""
    if not done:
        return False
    return (T52.norm_site(site), _core(what)) in done['pair']


# ── ① 답해 주십시오 ─────────────────────────────────────────
def todo_rows(recs_y, done=None):
    """어제 회의록에서 새로 생긴 할 일 → 시트 줄(날짜|종류|현장|할일|완료). 현장명은 meta.site 그대로."""
    rows, seen = [], set()
    nm = _names(recs_y)
    for r in recs_y:
        site = nm.get(r['key'], r['site'])
        for ymd, what, whom in r['todos']:
            key = (site, what)
            if key in seen or _is_done(done, site, what):
                continue
            seen.add(key)
            rows.append({'날짜': _iso(r['ymd']), '현장': site, '할일': _todo_text(ymd, what, whom), '완료': '',
                         '_메일': _todo_text(ymd, what, '')})   # v9 : 메일 ① 은 담당 괄호 없이
    # v6 : 메일·시트 같은 순서 (날짜 → 현장 → 현장이 아닌 것은 뒤로) — 같은 현장이 붙어 있어야 한 번만 쓰고 병합한다
    rows.sort(key=lambda x: (x['날짜'], not T52.is_site(x['현장']), x['현장']))
    return rows


def build_answer(recs_y, yday, sheet_url='', done=None, board=None):
    """차장님 지시 : 하루치 내용을 메일에 적고, 「26년 할 일 모음」 링크를 넣는다. 그 밖의 말은 안 적는다.
       v11 (차장님 「체크 안 된 것들은 계속 적어줘」) : 시트 답요청 탭에서 체크 안 한 기한 없는 지난 할 일도 회의한 날 아래에 계속 적는다.
       (기한이 있는 것은 ② 오늘 할 것 · ⑤ 앞으로 할 것 이 맡는다)"""
    rows = todo_rows(recs_y, done)
    carry = answer_carry(board, rows, yday)
    # v9 차장님 확정 (2026-09-23 캡처) : 할 일 앞에 「- 」 / 오른쪽 담당 괄호 (확인 예정)(한국마이크로닉) 등은 안 적는다.
    #    「표시한 것만」 — ② 오늘 할 것 · 시트 · 기간 메일 · (기한) 괄호는 차장님께 여쭌 뒤에만 바꾼다
    items = [(row['날짜'], row['현장'], row['_메일']) for row in rows] + carry
    items.sort(key=lambda x: (x[0], not T52.is_site(x[1]), x[1]))
    L = _grouped(items, bullet='  - ')
    if not rows:
        L.append('(%s 회의록에서 새로 생긴 할 일 없음)' % _iso(yday.strftime('%y%m%d')))
    L.append('')
    L.append('%s : %s' % (SHEET_NAME, sheet_url or '(링크 없음)'))
    return '\n'.join(L), rows, len(carry)


def _plain(text):
    return re.sub(r'^\s*-\s+', '', str(text or '')).strip()


def answer_carry(board, rows, yday):
    """① 에 이어 적을 것 : 답요청 탭, 체크 안 함, 기한 없음, 어제보다 앞선 회의. (회의한 날, 현장, 글)"""
    if not board:
        return []
    done = _done_of(board)
    seen = set(_key(r['현장'], r['_메일']) for r in rows)
    yd = yday.isoformat()
    out = []
    for b in board:
        if b['tab'] != '답요청' or b['due'] or not b['date'] or b['date'] >= yd:
            continue
        if b['key'] in done['pair'] or b['key'] in seen:
            continue
        seen.add(b['key'])
        out.append((b['date'], b['site'], _plain(b['text'])))
    return out


# ── ② 오늘 할 것 ────────────────────────────────────────────
def build_today(recs_all, today, done=None, board=None):
    """차장님 지시 : 회의록 「할 일」 중 날짜가 오늘인 것만. 미정은 안 적는다.
       v11 (차장님 「체크 안 된 것들은 날짜가 지나가도 계속」) : 시트에서 기한이 지났는데 체크 안 한 것도 원래 기한 날짜 아래에 계속 적는다.
       시트 앞으로 할일 탭에서 기한이 오늘이 된 것도 오늘 것으로 넣는다."""
    ty = today.strftime('%y%m%d')
    picked, seen = [], set()
    nm = _names(recs_all)
    for r in recs_all:
        site = nm.get(r['key'], r['site'])
        for ymd, what, whom in r['todos']:
            if ymd == ty and (site, what) not in seen:
                seen.add((site, what))
                if _is_done(done, site, what):
                    continue
                picked.append((site, what, _iso(r['ymd'])))   # v10 : 담당 괄호 없이
    carry = []
    if board:
        dn = _done_of(board)
        keys = set(_key(site, what) for site, what, _s in picked)
        for b in board:
            if not b['due'] or b['due'] > today.isoformat() or b['key'] in dn['pair'] or b['key'] in keys:
                continue
            keys.add(b['key'])
            if b['due'] == today.isoformat():
                picked.append((b['site'], _core(b['text']), b['date']))
            else:
                carry.append((b['due'], b['site'], _core(b['text'])))
    picked.sort(key=lambda x: (not T52.is_site(x[0]), x[0]))
    items = sorted(carry, key=lambda x: (x[0], not T52.is_site(x[1]), x[1])) + [(_iso(ty), site, what) for site, what, _src in picked]
    _TODAY_ITEMS[:] = items
    L = _grouped(items, bullet='  - ')
    if not items:
        L.append('(회의록에 %s 로 적힌 할 일 없음)' % _iso(ty))
    return '\n'.join(L), picked, len(carry)


# ── ⑤ 앞으로 할 것 (v11) ─────────────────────────────────────
def build_future(recs_all, today, done=None, board=None):
    """차장님 (2026-09-23) : 「오늘보다 앞선 날짜가 있는 것들은 내가 완료 체크를 할 때까지 … 계속 적어 줘」
       「매우 중요 — 앞으로 해야 될 일을 미리 알아야 하니 메일 아래에도, 시트에도 따로」
       재료 : 회의록 할 일 중 기한이 내일 이후 + 시트(답요청 기한·앞으로 할일 탭) 중 기한이 내일 이후. 체크한 것은 뺀다.
       돌려주는 것 : (메일 글, 전체 [(기한, 현장, 무엇)], 시트 앞으로 할일 탭에 새로 붙일 것)"""
    ty = today.isoformat()
    dn = _done_of(board) if board else (done or {'pair': set()})
    have = set(b['key'] for b in (board or []) if b['tab'] == '앞으로 할일')
    fut, seen = [], set()
    nm = _names(recs_all)
    for r in recs_all:
        site = nm.get(r['key'], r['site'])
        for ymd, what, whom in r['todos']:
            due = _iso(ymd)
            k = _key(site, what)
            if not due or due <= ty or k in seen or k in dn['pair']:
                continue
            seen.add(k)
            fut.append((due, site, what))
    for b in board or []:
        if not b['due'] or b['due'] <= ty or b['key'] in seen or b['key'] in dn['pair']:
            continue
        seen.add(b['key'])
        fut.append((b['due'], b['site'], _core(b['text'])))
    fut.sort(key=lambda x: (x[0], not T52.is_site(x[1]), x[1]))
    new = [f for f in fut if _key(f[1], f[2]) not in have]
    L = _grouped(fut, bullet='  - ')
    if not fut:
        L.append('(앞으로 날짜가 잡힌 할 일 없음)')
    return '\n'.join(L), fut, new


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


def sheet_plan(rows, picked, recs_y, today, yday, new_future=None):
    """탭별로 덧붙일 줄과, 덧붙인 뒤 합칠 칸.
       kind : 'date' = A열 날짜 세로 병합 / 'title' = 첫 줄 제목(A:G 병합·굵게) + 나머지 A열 병합"""
    yy = yday.strftime('%y%m%d')
    ty = today.strftime('%y%m%d')
    plan = {}
    plan['답요청'] = {'kind': 'date', 'cols': 4,
                     'values': [[r['날짜'], r['현장'], r['할일'], '', '', '', r['현장']] for r in rows]}   # v12 : G = 현장(걸러보기)
    plan['오늘 할일'] = {'kind': 'date', 'cols': 4,
                      'values': [[_iso(ty), site, '- ' + what, '', '', '', site] for site, what, _k in picked]}
    mr = meet_rows(recs_y)
    plan['회의록'] = {'kind': 'title', 'cols': len(MEET_HEAD),
                    'values': ([[meet_title(yy, len(recs_y))] + [''] * (len(MEET_HEAD) - 1)] + mr) if mr else []}
    plan['앞으로 할일'] = {'kind': 'date', 'cols': 4,
                        'values': [[due, site, '- ' + what, '', '', '', site] for due, site, what in (new_future or [])]}
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
        if plan[tab]['kind'] == 'title':
            if bot - top >= 2:
                req.append({'mergeCells': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': bot,
                                                     'startColumnIndex': 0, 'endColumnIndex': 1}, 'mergeType': 'MERGE_ALL'}})
        else:
            vals = plan[tab]['values'][:bot - top]
            req.extend(run_merge(sid, top, [v[0] for v in vals], 0, center=False))          # A : 같은 날짜
            req.extend(run_merge(sid, top, [(v[0], v[1]) for v in vals], 1))                 # B : 같은 날짜 안의 같은 현장
            req.append(date_format(sid, top, bot))
            req.append(done_checkbox(sid, top, bot))
            req.extend(extra_cols(sid, top, bot))
    return {'requests': req}


def done_checkbox(sid, top, bot):
    """v8 차장님 (2026-09-23 「완료 칸 체크박스로」) : D열 체크박스. 체크하면 칸 값이 「완료」, 끄면 빈칸.
       (값이 「완료」 라서 차장님이 손으로 적으신 옛 「완료」 도 그대로 체크로 보이고, load_done 도 그대로 읽는다)"""
    return {'setDataValidation': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': bot,
                                            'startColumnIndex': 3, 'endColumnIndex': 4},
                                  'rule': {'condition': {'type': 'BOOLEAN', 'values': [{'userEnteredValue': '완료'}]},
                                           'strict': True}}}


def _serial(iso):
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', str(iso or ''))
    if not m:
        return None
    return (datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) - datetime.date(1899, 12, 30)).days


def write_body(plan, counts):
    """v12 (2026-09-24 Zapier 한도) : 네 탭 덧붙이기 + 병합·서식을 batchUpdate 한 번으로.
       counts = t53_sheetmd 의 줄수.json {탭: 지금 데이터 줄 수}. 새 줄은 그 바로 아래(counts+2 번째 줄)부터 쓴다.
       날짜 칸(A열)은 날짜 숫자로 넣어 2026-09-24 로 보이게 한다. 돌려주는 것 : (본문, {탭: "F-L"})"""
    req, ranges = [], {}
    for tab in TABS:
        vals = (plan.get(tab) or {}).get('values') or []
        if not vals or tab not in counts:
            continue
        top = int(counts[tab]) + 1
        rows = []
        for v in vals:
            cells = []
            for i, x in enumerate(v):
                if x == '' or x is None:
                    cells.append({})
                elif i == 0 and _serial(x) is not None:
                    cells.append({'userEnteredValue': {'numberValue': _serial(x)}})
                else:
                    cells.append({'userEnteredValue': {'stringValue': str(x)}})
            rows.append({'values': cells})
        req.append({'updateCells': {'range': {'sheetId': TAB_ID[tab], 'startRowIndex': top, 'endRowIndex': top + len(rows),
                                              'startColumnIndex': 0, 'endColumnIndex': max(len(v) for v in vals)},
                                    'rows': rows, 'fields': 'userEnteredValue'}})
        ranges[tab] = '%d-%d' % (top + 1, top + len(rows))
    req += merge_body(plan, ranges)['requests']
    req.append(date_format(TAB_ID['회의록'], 1, 1000))       # 회의록 탭 날짜가 46287 로 보이던 것 (9/24 발견)
    return {'requests': req}, ranges


def extra_cols(sid, top, bot):
    """v12 : E열 ▼고르기 목록 + G열(현장 걸러보기) 회색 작은 글씨"""
    return [{'setDataValidation': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': bot,
                                             'startColumnIndex': 4, 'endColumnIndex': 5},
                                   'rule': {'condition': {'type': 'ONE_OF_LIST',
                                                          'values': [{'userEnteredValue': v} for v in PICKS]},
                                            'showCustomUi': True, 'strict': True}}},
            {'repeatCell': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': bot,
                                      'startColumnIndex': 6, 'endColumnIndex': 7},
                            'cell': {'userEnteredFormat': {'textFormat': {'fontSize': 8,
                                                                          'foregroundColor': {'red': 0.6, 'green': 0.6, 'blue': 0.6}}}},
                            'fields': 'userEnteredFormat.textFormat'}}]


def date_format(sid, top, bot):
    """v11 : A열 날짜를 2026-09-24 로 보이게 (숫자 46289 로 보이던 것 고침) + 가운데."""
    return {'repeatCell': {'range': {'sheetId': sid, 'startRowIndex': top, 'endRowIndex': bot,
                                     'startColumnIndex': 0, 'endColumnIndex': 1},
                           'cell': {'userEnteredFormat': {'numberFormat': {'type': 'DATE', 'pattern': 'yyyy-mm-dd'},
                                                          'horizontalAlignment': 'CENTER', 'verticalAlignment': 'MIDDLE'}},
                           'fields': 'userEnteredFormat(numberFormat,horizontalAlignment,verticalAlignment)'}}


def run_merge(sid, top, vals, col, center=True):
    """같은 값이 이어지는 칸을 세로로 합친다 (col 0 = 날짜, 1 = 현장)."""
    req, i = [], 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        if j > i:
            rng = {'sheetId': sid, 'startRowIndex': top + i, 'endRowIndex': top + j + 1,
                   'startColumnIndex': col, 'endColumnIndex': col + 1}
            req.append({'mergeCells': {'range': rng, 'mergeType': 'MERGE_ALL'}})
            if center:
                req.append({'repeatCell': {'range': rng,
                                           'cell': {'userEnteredFormat': {'verticalAlignment': 'MIDDLE', 'horizontalAlignment': 'CENTER'}},
                                           'fields': 'userEnteredFormat(verticalAlignment,horizontalAlignment)'}})
        i = j + 1
    return req


def site_merge(sid, top, sites):
    """v6 차장님 확정 : 답요청·오늘 할일 탭의 현장 칸(B열)도 같은 현장이 이어지면 세로로 합친다 (가운데 정렬).
       top = 첫 줄의 0 부터 번호, sites = 그 아래로 이어지는 B열 값들."""
    req, i = [], 0
    while i < len(sites):
        j = i
        while j + 1 < len(sites) and sites[j + 1] == sites[i]:
            j += 1
        if j > i:
            rng = {'sheetId': sid, 'startRowIndex': top + i, 'endRowIndex': top + j + 1,
                   'startColumnIndex': 1, 'endColumnIndex': 2}
            req.append({'mergeCells': {'range': rng, 'mergeType': 'MERGE_ALL'}})
            req.append({'repeatCell': {'range': rng,
                                       'cell': {'userEnteredFormat': {'verticalAlignment': 'MIDDLE', 'horizontalAlignment': 'CENTER'}},
                                       'fields': 'userEnteredFormat(verticalAlignment,horizontalAlignment)'}})
        i = j + 1
    return req


# ── 4. 신규 현장 레이더 (차장님 지시 2026-09-23 : 레이더 메일을 오늘의 정리에 합친다) ──
RADAR_SHEET = '1LWK3fmXgf2_aG12B3cunutLUHnSqNMDf_sr3lXOyr-c'
RADAR_RANGES = ["'구글AI_실행로그'!A1:G2000", "'구글AI_백필_확정'!A1:M5000", "'구글AI_백필_재검토필요'!A1:F5000"]   # 하나씩 values/<범위> 로 읽는다


def _radar_day(v):
    """'2026. 9. 23 오전 6:40:51' / '2026-09-23 06:40' -> '260923'"""
    m = re.match(r'\s*(\d{4})\D+(\d{1,2})\D+(\d{1,2})', str(v or ''))
    return '%s%02d%02d' % (m.group(1)[2:], int(m.group(2)), int(m.group(3))) if m else ''


def load_radar(path):
    """레이더 시트를 읽은 응답 파일(들)을 (로그, 확정, 재검토) 줄 목록으로.
       path : 파일 하나 또는 쉼표로 여럿. Zapier 응답 그대로 / values:get / values:batchGet 모두 받는다.
       어느 탭인지는 응답의 range 이름(실행로그·확정·재검토)으로 가린다."""
    out = {'로그': [], '확정': [], '재검토': []}
    for one in [x for x in str(path).split(',') if x.strip()]:
        with io.open(one.strip(), 'r', encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, dict) and 'results' in d:
            d = d['results'][0].get('body', d)
        blocks = d.get('valueRanges') if isinstance(d, dict) and 'valueRanges' in d else [d]
        for blk in blocks:
            rng = str(blk.get('range', ''))
            key = '로그' if '실행로그' in rng else ('재검토' if '재검토' in rng else ('확정' if '확정' in rng else ''))
            if key:
                out[key] = (blk.get('values') or [])[1:]
    return out['로그'], out['확정'], out['재검토']


def build_radar(radar, today):
    """오늘 날짜 실행 결과만. 오류로 0건이면 「없음」 이 아니라 「못 찾음」 이라고 적는다."""
    ty = today.strftime('%y%m%d')
    logs, conf, rev = radar
    runs = [r for r in logs if _radar_day(r[0] if r else '') == ty]
    conf = [r for r in conf if _radar_day(r[0] if r else '') == ty]
    rev = [r for r in rev if _radar_day(r[0] if r else '') == ty]
    L = []
    if not runs:
        L.append('(오늘 레이더 실행 기록 없음)')
        return '\n'.join(L), {'실행': 0, '확정': 0, '재검토': 0, '오류': 0}
    last = runs[-1] + [''] * 7
    err = str(last[6] or '')
    n_err = err.count(': Error')
    L.append('실행 %s · 확정 %d건 · 재검토 %d건' % (last[0], len(conf), len(rev)))
    if n_err:
        models = sorted(set(re.findall(r'models/([\w.\-]+)', err)))
        why = ('모델 없음 : %s' % ', '.join(models)) if models else err.split(': Error')[1][:80].strip()
        L.append('※ 검색 %d곳 모두 오류 — 「0건」 은 없는 게 아니라 못 찾은 것 (%s)' % (n_err, why) if not conf and not rev
                 else '※ 검색 중 %d곳 오류 (%s)' % (n_err, why))
    for r in conf:
        r = list(r) + [''] * 13
        L.append('')
        L.append('%s  (%s · %s)' % (r[5], r[2], r[3]))
        L.append('단계 : %s · 규모 : %s' % (r[4], r[6]))
        L.append('발주처 : %s · 시공사 : %s · 설계 : %s' % (r[7], r[8], r[9]))
        if r[10]:
            L.append(r[10])
        if r[11]:
            L.append(r[11])
    if rev:
        L.append('')
        L.append('재검토 필요')
        for r in rev:
            r = list(r) + [''] * 6
            L.append('  %s — %s' % (r[2], r[4]))
    return '\n'.join(L), {'실행': len(runs), '확정': len(conf), '재검토': len(rev), '오류': n_err}


# ── 한 통으로 ─────────────────────────────────────────────
def build_status(recs_y, yday, rstat, board_on):
    """v12 : 자료 상태 — 옛 메일의 [ 자료 상태 ] 를 되살림 (9/23 새 메일로 바뀌며 빠졌던 것). 문제가 있으면 줄 앞에 ※"""
    L = []
    n = len(recs_y)
    L.append('%s어제(%s) 회의록 %d건%s' % ('※ ' if not n else '', T52._d(yday.strftime('%y%m%d')), n,
             ' — 통화·회의가 있었는데 한방에를 안 누르셨으면 빠진 것입니다' if not n else ''))
    if board_on:
        miss = [t for t in ('답요청', '오늘 할일', '앞으로 할일') if t not in _BOARD_TABS]
        L.append(('※ 시트 못 읽음 : %s — 체크를 반영하지 못했습니다' % '·'.join(miss)) if miss else '시트 체크 읽음 : 답요청·오늘 할일·앞으로 할일')
    else:
        L.append('※ 시트를 읽지 않았습니다 — 체크를 반영하지 못했습니다')
    if rstat.get('오류'):
        L.append('※ 신규 현장 레이더 오류 %d곳 (4번)' % rstat['오류'])
    elif rstat.get('읽기실패'):
        L.append('※ 신규 현장 레이더 못 읽음 (4번)')
    else:
        L.append('신규 현장 레이더 : 정상')
    return '\n'.join(L)


def build_urgent(items, n=5):
    """v12 : 급한 것 — ② 줄 가운데 기한이 가장 오래된 것부터 n 줄. ② 에도 그대로 남는다(겹침, 차장님 확인 2026-09-24)."""
    items = sorted(items, key=lambda x: (x[0], not T52.is_site(x[1]), x[1]))[:n]
    return '\n'.join(_grouped(items, bullet='  - ')) if items else ''


def build_picks():
    """v12 : ▼고르신 것 — 만들어줘 : 제가 이렇게 만들겠습니다 (맞으면 ▼맞아) / 맞아 : 만들 차례"""
    make = [(k, v) for k, v in _PICK.items() if v[0] == '만들어줘']
    ok = [(k, v) for k, v in _PICK.items() if v[0] == '맞아']
    L = []
    if make:
        L.append('만들어줘 %d건 — 제가 아래 할 일의 문안·서류를 만들겠습니다. 이대로면 ▼맞아 로 바꿔 주십시오' % len(make))
        for (site, what), (_p, memo) in sorted(make):
            L.append('  - %s · %s%s' % (site, what, ('  (메모 : %s)' % memo) if memo else ''))
    if ok:
        if L:
            L.append('')
        L.append('맞아 %d건 — 대화창에 「만들어」 한마디면 바로 만듭니다' % len(ok))
        for (site, what), (_p, memo) in sorted(ok):
            L.append('  - %s · %s' % (site, what))
    return '\n'.join(L)


def build_one(t1, t2, t3, rows, picked, recs_y, today, yday, sheet_url='', t4=None, t5=None, n1c=0, n2c=0, n5=0,
              status=None, urgent=None, picks=None):
    """차장님 지시 (2026-09-23) : 3통을 순서대로 한 통에. 제목 [KM] 오늘의 정리 입니다. 날짜"""
    yy = yday.strftime('%y%m%d')
    t1_body = '\n'.join(ln for ln in t1.split('\n') if not ln.startswith(SHEET_NAME + ' :')).rstrip('\n')
    L = ['%s : %s' % (SHEET_NAME, sheet_url or '(링크 없음)'), '']
    if status:
        L += ['━━ 자료 상태 ━━', '', status, '']
    if urgent:
        L += ['━━ 급한 것 ━━  기한이 가장 오래된 것부터 (2번에도 있습니다)', '', urgent, '']
    if picks:
        L += ['━━ ▼ 고르신 것 ━━', '', picks, '']
    L.append('━━ 1. 답해 주십시오 ━━  %s 회의에서 생긴 할 일 %d건%s' % (T52._d(yy), len(rows), (' · 체크 안 한 지난 할 일 %d건' % n1c) if n1c else ''))
    L.append('')
    L.append(t1_body)
    L.append('')
    L.append('━━ 2. 오늘 할 것 ━━  %s · %d건%s' % (_iso(today.strftime('%y%m%d')), len(picked), (' · 기한 지난 것 %d건' % n2c) if n2c else ''))
    L.append('')
    L.append(t2.rstrip('\n'))
    L.append('')
    L.append('━━ 3. 어제 있었던 일 ━━  %s' % meet_title(yy, len(recs_y)))
    L.append('')
    L.append(t3.rstrip('\n'))
    if t4 is not None:
        L.append('')
        L.append('━━ 4. 신규 현장 레이더 ━━')
        L.append('')
        L.append(t4.rstrip('\n'))
    if t5 is not None:
        L.append('')
        L.append('━━ 5. 앞으로 할 것 ━━  %d건' % n5)
        L.append('')
        L.append(t5.rstrip('\n'))
    subject = '[KM] 오늘의 정리 입니다. %s (%s)' % (today.strftime('%Y-%m-%d'), T52.WD[today.weekday()])
    return '\n'.join(L) + '\n', subject


# ── 한 번에 ───────────────────────────────────────────────
def run(meta_dir, today=None, out=None, sheet_url='', radar_path='', done_path=''):
    today = today or datetime.date.today()
    yday = today - datetime.timedelta(days=1)
    yy = yday.strftime('%y%m%d')
    recs_all, skipped = collect(meta_dir)
    recs_y = [r for r in recs_all if r['ymd'] == yy]

    _BOARD_TABS.clear()
    board = load_board(done_path) if done_path else None
    done = _done_of(board) if done_path else None
    _PICK.clear()
    _PICK.update(pick_map(board) if board else {})
    t1, rows, n1c = build_answer(recs_y, yday, sheet_url, done, board)
    rows = [dict(r, 할일='- ' + r['_메일']) for r in rows]      # v10 : 시트·csv 도 「- 」 + 담당 괄호 없이
    t2, picked, n2c = build_today(recs_all, today, done, board)
    today_items = list(_TODAY_ITEMS)      # v12 : 급한 것 재료 (아래 n_done 계산이 build_today 를 한 번 더 부르므로 먼저 떠 둔다)
    t5, fut, new_fut = build_future(recs_all, today, done, board)
    n_done = ((len(todo_rows(recs_y)) - len(rows)) +
              len([q for q in build_today(recs_all, today)[1] if _key(q[0], q[1]) in done['pair']])) if done else 0
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
        w = csv.DictWriter(f, fieldnames=SHEET_HEAD, extrasaction='ignore')
        w.writeheader()
        for row in rows:
            w.writerow(row)
    paths['할일추가'] = p

    t4, rstat = (None, {})
    if radar_path:
        try:
            t4, rstat = build_radar(load_radar(radar_path), today)
        except Exception as e:
            t4, rstat = '(레이더 결과를 읽지 못함 : %s)' % e, {'읽기실패': str(e)}
    status = build_status(recs_y, yday, rstat, bool(done_path))
    urgent = build_urgent(today_items) if done_path else ''
    picks = build_picks()
    one, subject = build_one(t1, t2, t3, rows, picked, recs_y, today, yday, sheet_url, t4, t5, n1c, n2c, len(fut),
                             status, urgent, picks)
    p = os.path.join(out, '오늘의정리_%s.txt' % st)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(one)
    paths['오늘의정리'] = p
    plan = sheet_plan(rows, picked, recs_y, today, yday, new_fut)
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
            '시트줄': dict((t, len(plan[t]['values'])) for t in TABS), '레이더': rstat,
            'meta전체': len(recs_all), '어제회의': len(recs_y),
            '어제_현장별': per_site,
            '①할일': len(rows), '②오늘': len(picked), '완료로뺌': n_done,
            '①지난것': n1c, '▼고르신것': len(_PICK), '만들차례': len([1 for v in _PICK.values() if v[0] == '맞아']), '②기한지난것': n2c, '⑤앞으로': len(fut), '⑤새로시트에': len(new_fut),
            '완료표시': len(done['pair']) if done else None,
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
    M = _grouped([(row['날짜'], row['현장'], row['할일']) for row in rows])
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
        w = csv.DictWriter(f, fieldnames=SHEET_HEAD, extrasaction='ignore')
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
    if argv[1] == '--write' and len(argv) >= 4:
        # python3 t53_daily.py --write <시트계획.json> <줄수.json>   → Zapier 1번으로 네 탭 덧붙이기 + 병합 (v12)
        with io.open(argv[2], 'r', encoding='utf-8') as f:
            plan = json.load(f)
        with io.open(argv[3], 'r', encoding='utf-8') as f:
            counts = json.load(f)
        for extra in argv[4:]:                 # 대기 파일(예 : KM 11건) — 같은 탭 줄 뒤에 붙인다
            if os.path.isfile(extra):
                with io.open(extra, 'r', encoding='utf-8') as f:
                    for tab, pv in json.load(f).items():
                        plan.setdefault(tab, {'kind': pv.get('kind', 'date'), 'cols': pv.get('cols', 4), 'values': []})
                        plan[tab]['values'] = list(plan[tab].get('values') or []) + list(pv.get('values') or [])
        print(json.dumps(write_body(plan, counts)[0], ensure_ascii=False))
        return 0
    if argv[1] == '--merge':
        # python3 t53_daily.py --merge <시트계획.json> "답요청=<updatedRange>" "오늘 할일=<updatedRange>" "회의록=<updatedRange>"
        with io.open(argv[2], 'r', encoding='utf-8') as f:
            plan = json.load(f)
        ranges = dict(a.split('=', 1) for a in argv[3:] if '=' in a)
        print(json.dumps(merge_body(plan, ranges), ensure_ascii=False))
        return 0
    meta_dir, today, out, sheet, radar, donep = argv[1], None, None, '', '', ''
    d_from = d_to = None
    i = 2
    while i < len(argv):
        if argv[i] == '--today':
            today = datetime.datetime.strptime(argv[i + 1], '%y%m%d').date(); i += 2
        elif argv[i] == '--out':
            out = argv[i + 1]; i += 2
        elif argv[i] == '--sheet':
            sheet = argv[i + 1]; i += 2
        elif argv[i] == '--radar':
            radar = argv[i + 1]; i += 2
        elif argv[i] == '--done':                        # --done 답요청.json,오늘할일.json
            donep = argv[i + 1]; i += 2
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
        _t, stat = run(meta_dir, today, out, sheet, radar, donep)
    print(json.dumps(stat, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

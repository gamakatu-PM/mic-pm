# -*- coding: utf-8 -*-
"""42. 아침 한 장 (B안 v3, 7층) - 회의록·도면·돈·점검을 한 장에, 접어서. 토큰 0.
36번 끝에 저절로 만들어지고 35번 아침 메일이 이것을 보낸다. 따로 눌러도 된다.

  1층 지금 할 것   : 회의 할 일(업무판 00_미결_할일) + 결정대기 + 부탁서 + 수금 을 급한 순으로 한 줄씩
  2층 현장 카드    : 회의·공정 9단계·도면·돈·연락처·리스크·대외금지 (확정 대장이 추정보다 우선)
  3층 부서별      : 작업의뢰서 대기 (업무판 00_작업의뢰서_대기 ↔ 10번 발행대장)
  4층 회의 이력    : 회의록 폴더 14일 (PLAUD 녹음 대조는 클로드 「PLAUD 가져와」)
  5층 돈 총괄      : 계약(확정 대장)·증감·계산서·입금 대기 (수금대장)
  6층 점검        : 41 총괄 점검 결과 + PLAUD 대기 + 번복 + 대외금지
  7층 표·검색      : 전체 표 · 확정 대장 · 원본 링크
★ 추정과 확정을 구분한다. 공정단계는 확정 대장(43번)에 있으면 「확정」, 없으면 준공일 역산 「추정」, 둘 다 없으면 「미확정」.
  프로님이 고친 값(확정 대장)이 항상 이긴다. 찾기칸은 이 파일 안에서 도는 것이라 토큰 0.
결과 : base\\_아침한장.html + _도구결과\\아침한장\\{날짜}\\ + 인수인계함\\_아침한장.md (클로드용, 확정 대장이 맨 위)
"""
import os, re, io, csv, glob, json, datetime, html
import common
from common import *
import facts

TOOL = '아침한장'
STEPN = facts.STEPS
BOARD_FILES = {'할일': '00_미결_할일', '의뢰서': '00_작업의뢰서_대기', '카톡': '00_카톡_보낼문구', '색인': '회의록_색인',
               '끝난현장': '00_끝난현장', '현장설정': '00_현장설정', '업무판': '00_업무판'}

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=False)

# ---------------- 자료 읽기 (전부 방어적) ----------------

def find_board_files():
    """업무판이 내놓는 파일들을 plaud·biseo 아래에서 찾는다 (위치가 코드마다 달라서)"""
    found = {}
    roots = [cfg('plaud'), cfg('biseo'), os.path.dirname(cfg('plaud'))]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            if dp[len(root):].count(os.sep) > 3:
                dn[:] = []
            dn[:] = [d for d in dn if not d.startswith(('_삭제요망', '.', '3.처리완료'))]
            for f in fn:
                for k, stem in BOARD_FILES.items():
                    if f.startswith(stem) and k not in found:
                        found[k] = os.path.join(dp, f)
        if found:
            break
    return found

def read_rows(p):
    if not p or not os.path.exists(p):
        return [], []
    rows = []
    for enc in ('utf-8-sig', 'cp949', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                rows = list(csv.reader(fp))
            break
        except Exception:
            rows = []
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return [], []
    return [c.strip() for c in rows[0]], [[c.strip() for c in r] for r in rows[1:]]

def col(head, *keys):
    """머리글에서 열 번호 찾기 (부분 일치)"""
    for k in keys:
        for i, h in enumerate(head):
            if k in h:
                return i
    return None

def cell(row, i, default=''):
    return row[i] if i is not None and i < len(row) else default

def parse_day(s):
    s = str(s or '').strip()
    m = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', s)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return None
    m = re.search(r'^(\d{2})(\d{2})(\d{2})$', s)
    if m:
        try:
            return datetime.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return None
    m = re.search(r'(\d{1,2})\s*/\s*(\d{1,2})', s)
    if m:
        try:
            return datetime.date(today().year, int(m.group(1)), int(m.group(2)))
        except Exception:
            return None
    return None

def board_todos(files):
    """업무판 미결 할 일 -> [dict(site, due, text, who, src, level)]"""
    head, rows = read_rows(files.get('할일'))
    out = []
    if not head:
        return out
    ci = {'site': col(head, '현장'), 'due': col(head, '기한', '날짜', '일자', '마감'), 'text': col(head, '내용', '할일', '할 일', '제목'),
          'who': col(head, '담당', '누가', '부서'), 'src': col(head, '회의', '출처', '근거', '폴더')}
    t0 = today()
    for r in rows:
        text = cell(r, ci['text']) or ' '.join(r)
        due_s = cell(r, ci['due'])
        d = parse_day(due_s)
        if d is None:
            lv, dd = 'gry', None
        else:
            dd = (d - t0).days
            lv = 'red' if dd < 0 else ('yel' if dd <= 3 else 'blu')
        out.append({'site': cell(r, ci['site']), 'due': due_s or '미정', 'dd': dd, 'text': text, 'who': cell(r, ci['who']),
                    'src': cell(r, ci['src']), 'level': lv})
    order = {'red': 0, 'yel': 1, 'blu': 2, 'gry': 3}
    out.sort(key=lambda x: (order[x['level']], x['dd'] if x['dd'] is not None else 999))
    return out

def board_orders(files):
    head, rows = read_rows(files.get('의뢰서'))
    out = []
    if not head:
        return out
    ci = {'site': col(head, '현장'), 'dept': col(head, '부서', '팀'), 'text': col(head, '내용', '의뢰', '제목'),
          'src': col(head, '회의', '출처', '일자', '날짜'), 'state': col(head, '상태', '발행')}
    for r in rows:
        out.append({'site': cell(r, ci['site']), 'dept': cell(r, ci['dept']) or '미정', 'text': cell(r, ci['text']) or ' '.join(r),
                    'src': cell(r, ci['src']), 'state': cell(r, ci['state'])})
    return out

def issued_orders():
    """10번 발행대장 (있으면) : 낸 의뢰서 내용 목록"""
    out = []
    try:
        for p in glob.glob(os.path.join(cfg('out'), '의뢰서발행대장', '*', '*.csv')) + glob.glob(os.path.join(cfg('out'), '_대장', '*의뢰서*.csv')):
            h, rows = read_rows(p)
            for r in rows:
                out.append(' '.join(r))
    except Exception:
        pass
    return out

def kakao_text(files):
    p = files.get('카톡')
    return read_text(p).strip() if p and os.path.exists(p) else ''

SEC = lambda name: re.compile(r'^\s*■\s*' + name, re.M)
SEC_ANY = re.compile(r'^\s*(■|━|【)', re.M)

def section(text, name):
    m = SEC(name).search(text)
    if not m:
        return []
    # 머리글 줄의 남은 글자(「■ 수량·규격 변경」 의 '변경' 같은 것)를 내용으로 잡지 않는다
    nl = text.find('\n', m.end())
    rest = text[(nl + 1) if nl >= 0 else m.end():]
    n = SEC_ANY.search(rest)
    body = rest[:n.start()] if n else rest
    out = []
    for line in body.splitlines():
        s = line.strip().lstrip('-•·ㆍ*').strip()
        if s and s not in ('없음', '해당 없음', '-') and not s.startswith('('):
            out.append(s)
    return out

def first(text, name):
    m = re.search(r'^\s*■\s*' + name + r'\s*[:：]\s*(.+?)\s*$', text, re.M)
    return m.group(1).strip() if m else ''

def meetings():
    """회의록 폴더 전부 -> [dict] 최신순"""
    import t40_meeting as M
    out = []
    for p in M.meeting_files():
        folder = os.path.dirname(p)
        try:
            text = read_text(p)
        except Exception:
            continue
        fname = os.path.basename(folder)
        site = first(text, '현장') or os.path.basename(os.path.dirname(os.path.dirname(folder)))
        day = parse_day(first(text, '일자')) or parse_day(fname[:6])
        who = first(text, '협의자')
        if not who or who in ('확인 예정', '미정'):
            parts = fname.split('_')
            who = '_'.join(parts[1:3]) if len(parts) >= 3 else fname
        agenda = first(text, '안건')
        decisions = [l.split(':', 1)[1].strip() for l in text.splitlines() if l.strip().startswith('결정사항') and ':' in l]
        actions = [l.split(':', 1)[1].strip() for l in text.splitlines() if l.strip().startswith('조치사항') and ':' in l]
        docx = [f for f in os.listdir(folder) if f.lower().endswith('.docx')]
        out.append({'site': site, 'day': day, 'who': who, 'agenda': agenda, 'decisions': [d for d in decisions if d and d != '없음'],
                    'actions': [a for a in actions if a and a != '없음'], 'todos': section(text, '할 일'),
                    'secret': section(text, '★\\s*대외'), 'risk': section(text, '리스크'), 'dept': section(text, '타부서'),
                    'changes': section(text, '수량\\s*[·ㆍ・,/]?\\s*규격'), 'folder': folder,
                    'docx': os.path.join(folder, docx[0]) if docx else p})
    out.sort(key=lambda m: m['day'] or datetime.date(2000, 1, 1), reverse=True)
    return out

def money():
    try:
        import t13_brief, t06_collect
        unb, wait = t13_brief.money_rows()
        p = t06_collect.book_path()
        rows = t06_collect.load(p)[1:] if os.path.exists(p) else []
    except Exception:
        unb, wait, rows = [], [], []
    return unb, wait, rows

def drawing_state():
    try:
        import t33_dashboard as DB
        srows = DB.site_rows()
        reqs, pending = DB.request_rows()
    except Exception:
        srows, reqs, pending = [], [], []
    return srows, reqs, pending

def decisions_waiting():
    try:
        import t33_dashboard as DB
        urg, xfile = DB.urgent_rows()
        return urg, xfile
    except Exception:
        return [], None

def totalcheck_rows():
    try:
        import t41_totalcheck as TC
        TC.build(quick=True, quiet=True)
        return list(TC.R)
    except Exception:
        return []

# ---------------- 공정 단계 : 확정 > 역산 추정 > 미확정 ----------------

def site_stage(site, due):
    f = facts.get(site, '공정단계')
    if f:
        idx = facts.step_index(f['값'])
        return idx, '확정 · %s (%s %s)' % (f['값'], f['누가'], f['일자']), 'sure'
    d = parse_day(due) if due else None
    if d:
        try:
            import t05_schedule
            steps = t05_schedule.back(d)
            t0 = today()
            passed = [n for n, dd, w in steps if dd <= t0]
            # 역산 단계명 -> 9단계 번호
            key = ''.join(passed[-1:]) if passed else ''
            idx = 0
            for i, s in enumerate(STEPN):
                if s[:2] in key or s in key:
                    idx = i
            if '외함' in key: idx = 0
            elif '속판' in key: idx = 1
            elif '기구물 제작' in key: idx = 2
            elif '빽커버' in key: idx = 4
            elif '강전' in key: idx = 6
            elif '기구물 설치' in key: idx = 5
            elif '시운전 시작' in key: idx = 8
            nxt = [(n, dd) for n, dd, w in steps if dd > t0]
            return idx, '추정(준공 %s 역산) · 다음 「%s」 %s (D%+d) · 확정하려면 43번' % (
                due, nxt[0][0][:22], nxt[0][1].isoformat(), (nxt[0][1] - t0).days) if nxt else '추정(역산) · 시운전 지남', 'guess'
        except Exception:
            pass
    return None, '미확정 · 43번에 공정단계를 넣으면 표시', 'none'

def steps_html(idx, kind):
    cls = lambda i: ('' if idx is None else ('d' if i < idx else ('n' if i == idx else '')))
    extra = ' guess' if kind == 'guess' else (' none' if kind == 'none' else '')
    return ('<div class="steps%s">' % extra + ''.join('<i class="%s"></i>' % cls(i) for i in range(9)) + '</div><div class="stepl">'
            + ''.join('<span>%s</span>' % n for n in STEPN) + '</div>')

# ---------------- HTML 조각 ----------------

CSS = '''<style>
:root{--ink:#1a1f26;--ink2:#4a5561;--mute:#8E99A4;--line:#e6e9ed;--card:#f7f8fa;--red:#C0392B;--yel:#C77B2B;--grn:#2E7D5B;--blu:#2A6099;--pur:#6B4FA8;--gry:#8E99A4}
*{box-sizing:border-box}body{font-family:"맑은 고딕",system-ui;margin:0;padding:14px 16px 60px;color:var(--ink);max-width:980px;background:#fff}
h1{font-size:19px;margin:0 0 2px}.sub{color:var(--mute);font-size:12px;margin-bottom:10px}
h2{font-size:14.5px;margin:22px 0 6px;padding-bottom:4px;border-bottom:2px solid var(--line);display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap}
h2 small{font-weight:normal;color:var(--mute);font-size:11px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:8px;margin:10px 0}
.tile{background:var(--card);border-radius:10px;padding:9px 11px;border-top:4px solid var(--gry)}
.tile b{display:block;font-size:24px;line-height:1.1}.tile span{font-size:11.5px;color:var(--ink2)}
.tile.red{border-color:var(--red)}.tile.yel{border-color:var(--yel)}.tile.grn{border-color:var(--grn)}.tile.blu{border-color:var(--blu)}.tile.pur{border-color:var(--pur)}
.r{display:flex;gap:8px;padding:7px 10px;border-left:5px solid #ccc;background:var(--card);margin:4px 0;font-size:13.5px;line-height:1.45;border-radius:0 6px 6px 0}
.r .tag{flex:0 0 auto;font-size:11px;font-weight:bold;padding:1px 6px;border-radius:4px;color:#fff;height:fit-content;margin-top:2px;min-width:44px;text-align:center}
.red{border-color:var(--red)}.red .tag{background:var(--red)}.yel{border-color:var(--yel)}.yel .tag{background:var(--yel)}
.grn{border-color:var(--grn)}.grn .tag{background:var(--grn)}.blu{border-color:var(--blu)}.blu .tag{background:var(--blu)}
.pur{border-color:var(--pur)}.pur .tag{background:var(--pur)}.gry{border-color:var(--gry)}.gry .tag{background:var(--gry)}
.src{color:var(--mute);font-size:11.5px}.src a{color:var(--blu)}
.k{background:#eef4fb;border:1px dashed var(--blu);border-radius:8px;padding:10px 12px;font-size:13.5px;white-space:pre-line;margin:6px 0 4px}
.bar{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;align-items:center}.bar button{border:1px solid var(--line);background:#fff;border-radius:16px;padding:4px 10px;font-size:12px;cursor:pointer}
.bar button.on{background:var(--ink);color:#fff;border-color:var(--ink)}.bar input{flex:1;min-width:160px;border:1px solid var(--line);border-radius:16px;padding:5px 10px;font-size:13px}
.card{background:var(--card);border-radius:10px;padding:10px 12px;margin:10px 0;font-size:13px;border-left:5px solid var(--gry)}
.card.red{border-left-color:var(--red)}.card.yel{border-left-color:var(--yel)}.card.grn{border-left-color:var(--grn)}.card.blu{border-left-color:var(--blu)}
.card h3{margin:0 0 6px;font-size:15px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px}.card h3 small{color:var(--mute);font-weight:normal;font-size:12px}
.steps{display:flex;gap:3px;margin:6px 0 2px}.steps i{flex:1;height:10px;background:#e2e5e9;border-radius:2px}.steps i.d{background:var(--grn)}.steps i.n{background:var(--yel)}
.steps.guess i.d{background:repeating-linear-gradient(45deg,#8fbfa8 0 4px,#d7e8de 4px 8px)}.steps.guess i.n{background:repeating-linear-gradient(45deg,#e0b070 0 4px,#f3e2c4 4px 8px)}
.stepl{display:flex;gap:3px;font-size:9.5px;color:var(--mute)}.stepl span{flex:1;text-align:center;overflow:hidden;white-space:nowrap}
.stage{font-size:12px;margin:2px 0 4px}.stage.sure{color:var(--grn);font-weight:bold}.stage.guess{color:var(--yel)}.stage.none{color:var(--red)}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:6px 14px;margin-top:6px}
.g div{font-size:12.5px}.g b{color:var(--ink2);font-weight:normal;display:block;font-size:11px}
details{margin:6px 0}details summary{cursor:pointer;font-size:13px;color:var(--blu);padding:4px 0}details.top summary{font-size:14px;font-weight:bold;color:var(--ink);margin-top:18px}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin:4px 0;background:#fff}th{text-align:left;color:var(--mute);font-weight:normal;border-bottom:1px solid var(--line);padding:4px 6px}td{padding:5px 6px;border-bottom:1px solid var(--line);vertical-align:top}
a{color:var(--blu)}.foot{color:var(--mute);font-size:11px;margin-top:22px;line-height:1.6}
.sure-tag{background:#e3f2ea;color:#1f5f43;font-size:11px;padding:1px 6px;border-radius:4px}
.lvl{position:sticky;top:0;background:#fff;z-index:5;padding:6px 0;border-bottom:1px solid var(--line);display:flex;gap:6px;flex-wrap:wrap;font-size:12px}
.lvl a{padding:3px 9px;border:1px solid var(--line);border-radius:14px;text-decoration:none;color:var(--ink2)}
.tl{border-left:2px solid var(--line);margin-left:6px;padding-left:12px}.tl .e{position:relative;margin:6px 0;font-size:12.5px}.tl .e:before{content:"";position:absolute;left:-17px;top:6px;width:8px;height:8px;border-radius:50%;background:var(--blu)}
.hide{display:none}
</style>
<script>
function f(s,b){document.querySelectorAll('[data-site]').forEach(e=>{e.classList.toggle('hide',!(s==='all'||e.dataset.site===s||e.dataset.site===''))});document.querySelectorAll('.bar button').forEach(x=>x.classList.remove('on'));b.classList.add('on')}
function q(v){v=v.trim();document.querySelectorAll('.r,.card,.e,tr').forEach(e=>{if(e.tagName==='TR'&&!e.querySelector('td'))return;e.classList.toggle('hide',v&&!e.textContent.includes(v))});var n=document.querySelectorAll('.r:not(.hide),.card:not(.hide),.e:not(.hide),tr:not(.hide)').length;document.getElementById('qn').textContent=v?('찾음 '+n+'줄 (이 파일 안에서, 토큰 0)'):''}
function openAll(o){document.querySelectorAll('details').forEach(d=>d.open=o)}
</script>'''

def r(c, t, tag, site='', src=''):
    return '<div class="r %s" data-site="%s"><span class="tag">%s</span><span>%s%s</span></div>' % (
        c, esc(site), esc(tag), t, ('<br><span class="src">%s</span>' % src) if src else '')

def h2(t, small=''):
    return '<h2>%s<small>%s</small></h2>' % (t, small)

def tile(c, n, label, anchor):
    return '<a href="#%s" style="text-decoration:none;color:inherit"><div class="tile %s"><b>%s</b><span>%s</span></div></a>' % (anchor, c, n, label)

def det(title, body, top=False, open_=False):
    return '<details class="%s"%s><summary>%s</summary>%s</details>' % ('top' if top else '', ' open' if open_ else '', title, body)

def tbl(head, rows):
    if not rows:
        return '<div class="src">없음</div>'
    return '<table><tr>' + ''.join('<th>%s</th>' % esc(h) for h in head) + '</tr>' + ''.join(
        '<tr>' + ''.join('<td>%s</td>' % c for c in row) + '</tr>' for row in rows) + '</table>'

def link(p, label=None):
    if not p:
        return ''
    return '<a href="%s">%s</a>' % (file_url(p), esc(label or os.path.basename(p)))

def _norm(s):
    return facts._norm(s)

def same_site(a, b):
    a, b = _norm(a), _norm(b)
    return bool(a and b) and (a == b or a in b or b in a)

# ---------------- 만들기 ----------------

def build(quiet=True):
    import sitebook
    try:
        sitebook.sync_from_folders()
    except Exception:
        pass
    t0 = today()
    files = find_board_files()
    todos = board_todos(files)
    orders = board_orders(files)
    issued = issued_orders()
    kakao = kakao_text(files)
    mts = meetings()
    unb, wait, mrows = money()
    srows, reqs, pending = drawing_state()
    urg, xfile = decisions_waiting()
    chk = totalcheck_rows()
    # ★ 미확인 회의록 (저장만 하고 못 읽은 것) — 매일 맨 위에 뜬다
    try:
        import t44_meetingcheck as MC
        unread_mt = MC.unchecked()
        mt_xlsx, mt_csv = MC.build_xlsx(unread_mt, quiet=True)
    except Exception:
        unread_mt, mt_xlsx, mt_csv = [], None, None
    fx = facts.load()
    book = {d['site']: d for d in sitebook.load()}
    # 현장 목록 = 현장대장 ∪ 회의록 현장 ∪ 도면 현장 ∪ 확정 대장
    names = []
    for s in list(book.keys()) + [m['site'] for m in mts] + [x[0] for x in srows] + [d['현장'] for d in fx]:
        if s and not any(same_site(s, n) for n in names):
            names.append(s)
    # ---- 1층 ----
    L1 = []
    for no, u, k, w in urg:
        L1.append(('red' if u == '★급함' else 'yel', '', '[결정대기 %s] %s · %s' % (u, esc(k), esc(w[:90])), '결정', '출처 1_결정대기 ' + (link(xfile) if xfile else '')))
    for t in todos:
        tag = {'red': 'D%+d 지남' % t['dd'] if t['dd'] is not None else '지남', 'yel': ('오늘' if t['dd'] == 0 else 'D+%d' % t['dd']) if t['dd'] is not None else '임박', 'blu': 'D+%d' % (t['dd'] or 0), 'gry': '미정'}[t['level']]
        L1.append((t['level'], t['site'], '%s · %s%s' % (esc(t['site']), esc(t['text']), (' → ' + esc(t['who'])) if t['who'] else ''), tag,
                   ('기한 %s · 출처 %s' % (esc(t['due']), esc(t['src']))) + ' · ' + link(files.get('할일'), '00_미결_할일.csv')))
    for site, n, p, d in reqs:
        L1.append(('yel', site, '%s · 부탁서 %d항목 → 클로드 대화창에 던지기' % (esc(site), n), '클로드', link(p)))
    if pending:
        L1.append(('yel', '', '받은답 %d개 반영 대기 → 30번 (또는 ★KM_도면넣고_여기클릭)' % len(pending), '받은답', ''))
    for s, k, a, g in unb:
        L1.append(('red', s, '%s · 계산서 미발행 %s · %s원 (납품 %d일 경과) → 발행' % (esc(s), esc(k), won(a), g), '수금', '출처 수금대장'))
    for s, k, a, g in wait:
        L1.append(('yel' if g <= 3 else 'blu', s, '%s · 입금 대기 %s · %s원 (D%+d)' % (esc(s), esc(k), won(a), g), '입금', '출처 수금대장'))
    # 46 앞으로 해야 될 것 (클로드가 회의록을 읽고 대장에 넣은 것) : 오늘·지남·3일 내는 1층에. 「만들기」 가 차 있으면 「제가 만들까요?」
    try:
        import t46_plan as PL
        plan_rows = PL.rows()
        plan_x, plan_c = PL.build_xlsx(plan_rows, quiet=True)
    except Exception:
        plan_rows, plan_x, plan_c = [], None, None
    for d in plan_rows:
        if d['level'] not in ('red', 'yel'):
            continue
        L1.append((d['level'], d['현장'], '%s · %s%s%s' % (esc(d['현장']), esc(d['할일']),
                   (' → ' + esc(d['누가'])) if d['누가'] else '',
                   (' <b style="color:#6B4FA8">· 제가 %s 만들까요?</b>' % esc(d['만들기'])) if d['만들기'] else ''),
                   PL.tag(d) + ' · ' + d['등급'], ('왜 : ' + esc(d['왜'])) if d['왜'] else '출처 앞으로할것.csv'))
    # 47 견적 보낸 곳 : 보내 놓고 안 가보시면 그대로 식는다. 「찾아가실 곳」 을 1층에 매일
    try:
        import t47_visit as VS
        visit_rows = VS.rows()
        visit_x, visit_c = VS.build_xlsx(visit_rows, quiet=True)
    except Exception:
        visit_rows, visit_x, visit_c = [], None, None
    for d in visit_rows:
        if not d['need']:
            continue
        L1.append(('red' if not d['마지막방문'] else 'yel', d['현장'],
                   '%s · <b style="color:#2A6099">찾아가실 곳</b> %s%s — 견적 보낸 뒤 그대로입니다'
                   % (esc(d['현장']), esc(d['받는곳'] or ''), (' ' + esc(d['담당자'])) if d['담당자'] else ''),
                   '방문', esc(d['why']) + (' · ' + link(visit_x, '찾아갈곳 목록') if visit_x else '')))
    # 45 요청 분기 : 도면이 없어 견적을 못 만드는 현장은 「도면 요청 메일」 이 이미 만들어져 있다
    try:
        import t45_askgate as AG
        for g in AG.gate_all():
            if g['state'] != '도면필요':
                continue
            mp = AG.mail_path(g['site'])
            L1.append(('red', g['site'], '%s · 도면이 없어 견적을 못 만듭니다 → 도면 요청 메일 본문 준비됨'
                       % esc(g['site']), '도면요청',
                       link(mp, '보낼메일_도면요청_%s.txt' % g['site']) if mp else '45번을 누르시면 메일 본문이 만들어집니다'))
    except Exception:
        pass
    order = {'red': 0, 'yel': 1, 'blu': 2, 'gry': 3}
    L1.sort(key=lambda x: order.get(x[0], 9))
    # ---- 미확인 회의록 ----
    L0 = []
    for m in unread_mt:
        gap = m.get('gap')
        lv = 'red' if (gap is None or gap >= 3) else 'yel'
        tag = ('%d일 지남' % gap) if gap else ('오늘' if gap == 0 else '날짜?')
        bits = []
        if m['agenda']:
            bits.append('안건 ' + esc(m['agenda'][:60]))
        if m['decisions']:
            bits.append('결정 ' + esc(m['decisions'][0][:60]))
        if m['todos']:
            bits.append('할 일 %d건 (%s)' % (len(m['todos']), esc(m['todos'][0][:40])))
        if m['changes']:
            bits.append('<b>수량·규격 변경 %d줄</b>' % len(m['changes']))
        if m['secret']:
            bits.append('★대외금지 %d' % len(m['secret']))
        detail = ''
        for nm, key in (('결정사항', 'decisions'), ('조치사항', 'actions'), ('할 일', 'todos'),
                        ('수량·규격 변경', 'changes'), ('★ 대외 언급 금지', 'secret'), ('리스크', 'risk'), ('타부서 전달(의뢰서)', 'dept')):
            v = m.get(key) or []
            if v:
                detail += '<b>%s</b><ul style="margin:2px 0 6px 18px">%s</ul>' % (nm, ''.join('<li>%s</li>' % esc(x) for x in v))
        body = '%s · %s · %s %s' % (esc(m['day'] or '날짜?'), esc(m['site'] or '?'), esc(m['who'] or ''), link(m['docx'], '회의록 열기'))
        if detail:
            body += det('내용 펼치기 (빠진 것 없이 전부)', detail)
        L0.append((lv, m['site'], body, tag, ' · '.join(bits) or '내용 없음'))

    # ---- 2층 ----
    cards = ''
    quiet_sites = []
    for site in names:
        b = book.get(site) or next((v for k, v in book.items() if same_site(k, site)), {})
        due = (facts.get(site, '준공일') or {}).get('값') or b.get('due', '')
        rooms = (facts.get(site, '객실수') or {}).get('값') or b.get('rooms', '')
        idx, stage_txt, kind = site_stage(site, due)
        ms = [m for m in mts if same_site(m['site'], site)]
        last = ms[0] if ms else None
        gap = (t0 - last['day']).days if last and last['day'] else None
        col_ = 'grn'
        if gap is None or gap >= 14:
            col_ = 'red'; quiet_sites.append((site, gap))
        my_todos = [t for t in todos if same_site(t['site'], site)]
        my_orders = [o for o in orders if same_site(o['site'], site)]
        my_unb = [x for x in unb if same_site(x[0], site)]
        my_wait = [x for x in wait if same_site(x[0], site)]
        my_req = [x for x in reqs if same_site(x[0], site)]
        my_draw = next((x for x in srows if same_site(x[0], site)), None)
        my_fx = [d for d in fx if same_site(d['현장'], site)]
        if any(t['level'] == 'red' for t in my_todos) or my_unb:
            col_ = 'red'
        elif col_ != 'red' and (my_req or any(t['level'] == 'yel' for t in my_todos)):
            col_ = 'yel'
        g = [('발주처·시공사', esc(((facts.get(site, '발주처') or {}).get('값') or b.get('owner', '') or '-') + ' / ' + ((facts.get(site, '시공사') or {}).get('값') or b.get('builder', '') or '-'))),
             ('준공·객실', esc('%s · %s실' % (due or '미확정', rooms or '?'))),
             ('마지막 회의', esc('%s · %s' % ('%d일 전' % gap if gap is not None else '없음', last['who'] if last else '-'))),
             ('할 일', '%d건 (지남 %d)' % (len(my_todos), sum(1 for t in my_todos if t['level'] == 'red'))),
             ('의뢰서 대기', '%d건' % len(my_orders)),
             ('부탁서', ('%d항목' % my_req[0][1]) if my_req else '없음'),
             ('도면', ('%d개 · r%d · 판 변경 %d품목' % (my_draw[1], my_draw[2], my_draw[4])) if my_draw else '없음'),
             ('돈', esc('미발행 %d · 입금대기 %d' % (len(my_unb), len(my_wait))))]
        body = '<div class="card %s" data-site="%s" id="s_%s"><h3>%s <small>%s</small></h3>%s<div class="stage %s">%s</div><div class="g">%s</div>' % (
            col_, esc(site), esc(safe_name(site)), esc(site), esc(last['day'].isoformat() + ' ' + last['who']) if last and last['day'] else '회의록 없음',
            steps_html(idx, kind), kind, esc(stage_txt), ''.join('<div><b>%s</b>%s</div>' % (k, v) for k, v in g))
        if my_fx:
            body += det('<span class="sure-tag">확정</span> 프로님이 정한 값 %d건 (추정보다 우선)' % len(my_fx),
                        tbl(['일자', '항목', '값', '근거', '누가'], [[esc(d['일자']), esc(d['항목']), '<b>%s</b>' % esc(d['값']), esc(d['근거']), esc(d['누가'])] for d in my_fx]), open_=True)
        body += det('최근 회의 %d건 · 안건·결정·조치' % len(ms), tbl(['일자·협의자', '안건', '결정', '조치', '원문'],
                    [[esc('%s %s' % (m['day'] or '', m['who'])), esc(m['agenda']), esc(' / '.join(m['decisions'])[:120]), esc(' / '.join(m['actions'])[:120]), link(m['docx'], '열기')] for m in ms[:8]]))
        body += det('할 일 %d건' % len(my_todos), tbl(['상태', '기한', '내용', '담당'], [[esc({'red': '지남', 'yel': '임박', 'blu': '예정', 'gry': '미정'}[t['level']]), esc(t['due']), esc(t['text']), esc(t['who'])] for t in my_todos]))
        body += det('작업의뢰서 %d건' % len(my_orders), tbl(['부서', '내용', '나온 회의', '발행'], [[esc(o['dept']), esc(o['text']), esc(o['src']), '<b>발행됨</b>' if any(o['text'][:12] and o['text'][:12] in x for x in issued) else esc(o['state'] or '미발행')] for o in my_orders]))
        chg = [(m['day'], c) for m in ms for c in m['changes']]
        body += det('수량·규격 변경 %d건 → 수량표 반영 여부는 부탁서에서' % len(chg), tbl(['일자', '내용'], [[esc(d), esc(c)] for d, c in chg]))
        if my_draw:
            body += det('도면 · 실행 · 견적', tbl(['항목', '값'], [['도면', '%d개 · r%d · 마지막 읽음 %s' % (my_draw[1], my_draw[2], esc(my_draw[3] or '-'))], ['판 변경', '%d품목 %s' % (my_draw[4], link(my_draw[5], '증감표') if my_draw[5] else '')],
                                                          ['부탁서', link(my_req[0][2]) if my_req else '없음']]))
        body += det('돈', tbl(['구분', '금액', '상태'], [[esc(k), won(a) + '원', '<b>미발행 %d일</b>' % gd] for s, k, a, gd in my_unb] + [[esc(k), won(a) + '원', '입금 대기 D%+d' % gd] for s, k, a, gd in my_wait]))
        who_list = []
        for m in ms:
            if m['who'] and m['who'] not in [w for w, d in who_list]:
                who_list.append((m['who'], m['day']))
        body += det('협의자 %d명 (마지막 회의일)' % len(who_list), tbl(['협의자', '마지막'], [[esc(w), esc(d)] for w, d in who_list[:12]]))
        my_plan = [d for d in plan_rows if same_site(d['현장'], site)]
        if my_plan:
            body += det('앞으로 해야 될 것 %d건%s' % (len(my_plan), (' · 제가 만들까요? %d' % len([d for d in my_plan if d['만들기']])) if any(d['만들기'] for d in my_plan) else ''),
                        tbl(['때', '등급', '할 일', '누가', '왜', '제가 만들까요?'],
                            [[esc(d['때']), esc(d['등급']), esc(d['할일']), esc(d['누가']), esc(d['왜']), esc(d['만들기'])] for d in my_plan]), open_=True)
        risks = [x for m in ms[:5] for x in m['risk']]
        secrets = [(m['day'], x) for m in ms for x in m['secret']]
        body += det('리스크 %d (2부)' % len(risks), '<ul style="margin:4px 0 4px 18px;font-size:12.5px">' + ''.join('<li>%s</li>' % esc(x) for x in risks[:10]) + '</ul>' if risks else '<div class="src">없음</div>')
        body += det('★ 대외 언급 금지 %d건' % len(secrets), '<ul style="margin:4px 0 4px 18px;font-size:12.5px">' + ''.join('<li>%s · %s</li>' % (esc(d), esc(x)) for d, x in secrets[:10]) + '</ul>' if secrets else '<div class="src">없음</div>')
        cards += body + '</div>'
    # ---- 3층 ----
    depts = {}
    for o in orders:
        depts.setdefault(o['dept'], []).append(o)
    L3 = ''
    for d, os_ in sorted(depts.items()):
        L3 += det('<b>%s</b> · %d건' % (esc(d), len(os_)), ''.join(r('grn' if any(o['text'][:12] and o['text'][:12] in x for x in issued) else 'yel', '%s · %s' % (esc(o['site']), esc(o['text'])),
                  '발행' if any(o['text'][:12] and o['text'][:12] in x for x in issued) else '미발행', o['site'], '나온 회의 %s' % esc(o['src'])) for o in os_), top=True, open_=True)
    if not orders:
        L3 = '<div class="src">업무판 00_작업의뢰서_대기.csv 를 못 찾았거나 비어 있습니다 (시작.bat 을 돌리면 생깁니다)</div>'
    # ---- 4층 ----
    cut = t0 - datetime.timedelta(days=14)
    recent = [m for m in mts if m['day'] and m['day'] >= cut]
    L4 = '<div class="tl">' + ''.join('<div class="e" data-site="%s"><b>%s</b> · %s · %s · %s%s %s</div>' % (
        esc(m['site']), esc(m['day']), esc(m['site']), esc(m['who']), esc(m['agenda'] or '-'), (' · 결정: ' + esc(m['decisions'][0][:60])) if m['decisions'] else '', link(m['docx'], '원문')) for m in recent) + '</div>'
    if not recent:
        L4 = '<div class="src">최근 14일 회의록 없음</div>'
    # ---- 5층 ----
    m5 = []
    for site in names:
        c = facts.get(site, '계약금액')
        d = facts.get(site, '증감누적')
        u = [x for x in unb if same_site(x[0], site)]
        w = [x for x in wait if same_site(x[0], site)]
        if not (c or d or u or w):
            continue
        m5.append([esc(site), esc(c['값']) if c else '-', esc(d['값']) if d else '-',
                   ' / '.join('%s %s원 (%d일)' % (esc(k), won(a), g) for s, k, a, g in u) or '-',
                   ' / '.join('%s %s원 (D%+d)' % (esc(k), won(a), g) for s, k, a, g in w) or '-'])
    L5 = tbl(['현장', '계약(확정 대장)', '증감 누적(확정 대장)', '계산서 미발행', '입금 대기'], m5) + '<div class="src">계약·증감은 43번으로 「계약금액」「증감누적」을 넣으면 채워집니다. 계산서·입금은 수금대장.</div>'
    # ---- 6층 ----
    L6 = ''
    lvmap = {'red': 'red', 'yellow': 'yel', 'green': 'grn', 'gray': 'gry'}
    for lv, sec, item, st, fix in chk:
        if lv in ('red', 'yellow'):
            L6 += r(lvmap[lv], '%s · %s : %s → %s' % (esc(sec), esc(item), esc(st), esc(fix)), '실패' if lv == 'red' else '주의')
    if not L6:
        L6 = r('grn', '41 총괄 점검(빠른) 실패·주의 없음', '점검')
    # 번복 감지 : 같은 현장에서 최근 결정이 이전 결정을 뒤집는 낱말(→) 포함 시 단순 표시
    for site in names:
        ms = [m for m in mts if same_site(m['site'], site)]
        decs = [(m['day'], d) for m in ms for d in m['decisions']]
        if len(decs) >= 2:
            a, b_ = decs[0][1], decs[1][1]
            if a and b_ and a != b_ and any(w in a for w in ('변경', '대신', '취소', '철회', '→')):
                L6 += r('yel', '%s · 결정 변경 가능성 : 「%s」(%s) ← 「%s」(%s)' % (esc(site), esc(a[:50]), esc(decs[0][0]), esc(b_[:50]), esc(decs[1][0])), '번복', site)
    for site, gap in quiet_sites:
        L6 += r('red', '%s · %s 회의 없음 → 전화 한 통' % (esc(site), ('%d일째' % gap) if gap is not None else '회의록 자체가'), '조용', site)
    L6 += r('gry', 'PLAUD 녹음 ↔ 회의록 대조는 파이썬이 못 봅니다 → 「PLAUD 가져와」 라고 하면 클로드가 회의록 없는 녹음 목록을 줍니다', 'PLAUD')
    # ---- 7층 ----
    L7 = det('전체 할 일 표', tbl(['상태', '현장', '기한', '내용', '담당', '출처'], [[esc({'red': '지남', 'yel': '임박', 'blu': '예정', 'gry': '미정'}[t['level']]), esc(t['site']), esc(t['due']), esc(t['text']), esc(t['who']), esc(t['src'])] for t in todos]), top=True)
    L7 += det('확정 대장 전체 (프로님이 정한 값 · 찾기칸에 낱말을 치면 여기서도 찾힘)', tbl(['일자', '현장', '항목', '값', '근거', '누가', '상태'], [[esc(d[k]) for k in facts.HEAD] for d in facts.load(active_only=False)]) + '<div class="src">%s</div>' % link(facts.path()), top=True, open_=True)
    links = [link(v, '%s' % os.path.basename(v)) for k, v in files.items()]
    links += [link(os.path.join(cfg('base'), '_현황판.html'), '_현황판.html'), link(os.path.join(cfg('base'), '_총괄점검.html'), '_총괄점검.html')]
    L7 += r('blu', ' · '.join(x for x in links if x), '원본')
    # ---- 조립 ----
    n_red = sum(1 for x in L1 if x[0] == 'red'); n_yel = sum(1 for x in L1 if x[0] == 'yel')
    n_wo = sum(1 for o in orders if not any(o['text'][:12] and o['text'][:12] in x for x in issued))
    n_secret = sum(len(m['secret']) for m in mts)
    H = ['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KM 아침 한 장</title>', CSS,
         '<h1>KM 아침 한 장 <small style="font-size:12px;color:#8E99A4">%s · 도구 %s</small></h1>' % (t0.isoformat(), VERSION),
         '<div class="sub">회의록(업무판)·도면·돈·점검을 한 장에. 굵은 <span class="sure-tag">확정</span> 은 프로님이 정한 값이고, 빗금 공정바는 역산 추정입니다. 찾기칸은 이 파일 안에서만 돕니다(토큰 0).</div>',
         '<div class="lvl"><a href="#l0" style="border-color:#C0392B;color:#C0392B">0층 미확인 회의록</a><a href="#l1">1층 오늘</a><a href="#l2">2층 현장</a><a href="#l3">3층 부서·의뢰서</a><a href="#l4">4층 회의 이력</a><a href="#l5">5층 돈</a><a href="#l6">6층 점검</a><a href="#l7">7층 표·확정</a></div>',
         '<div class="tiles">', tile('red', len(L0), '미확인 회의록', 'l0'), tile('red', n_red, '지남·미발행·결정', 'l1'), tile('yel', len([d for d in plan_rows if d['만들기']]), '제가 만들까요?', 'l1'), tile('blu', len([d for d in visit_rows if d['need']]), '찾아갈 곳', 'l1'), tile('yel', n_yel, '오늘·3일내·부탁서', 'l1'), tile('yel', n_wo, '의뢰서 미발행', 'l3'),
         tile('red', len(quiet_sites), '조용한 현장', 'l6'), tile('pur', n_secret, '대외 금지 누적', 'l2'), tile('blu', len(recent), '회의 14일', 'l4'),
         tile('grn', len(fx), '확정 대장', 'l7'), '</div>']
    if kakao:
        H.append(h2('카톡 문구 (길게 눌러 복사)', esc(os.path.basename(files.get('카톡', '')))) + '<div class="k">' + esc(kakao) + '</div>')
    if L0:
        H.append('<div class="k" style="border-color:#C0392B;background:#fdecea">미확인 회의록 %d건 — 가장 오래된 것 %s. ★KM_번호입력 → 44 로 읽고 확인하십시오.</div>'
                 % (len(L0), esc(unread_mt[0]['day'] or '날짜?')))
    H.append('<div class="bar"><button class="on" onclick="f(\'all\',this)">전체</button>' + ''.join('<button onclick="f(\'%s\',this)">%s</button>' % (esc(s), esc(s)) for s in names)
             + '<input placeholder="찾기 : 이름·품목·금액·날짜·확정" oninput="q(this.value)"><span id="qn" class="src"></span><button onclick="openAll(true)">모두 펼침</button><button onclick="openAll(false)">모두 접기</button></div>')
    H.append('<div id="l0"></div>' + h2('0층 · <span style="color:#C0392B">미확인 회의록 %d건</span> (저장만 되어 있습니다. 읽고 44번으로 확인)' % len(L0),
             '읽으시면 사라집니다 · ★KM_번호입력 → 44'))
    H.append(''.join(r(c, t, tag, s, src) for c, s, t, tag, src in L0) if L0 else r('grn', '미확인 회의록 없음 (전부 확인하셨습니다)', '없음'))
    if L0 and mt_xlsx:
        H.append(r('blu', '요약 엑셀로 보기 : %s  (1.요약 · 2.할 일 · 3.수량변경 · 4.대외금지 · 5.리스크 · 6.타부서 · 7.전체 내용)' % link(mt_xlsx), '엑셀'))
    H.append('<div id="l1"></div>' + h2('1층 · 지금 할 것 (급한 순 · 한 줄 = 한 행동)', '회의 할 일 + 앞으로 해야 될 것(46) + 결정대기 + 부탁서 + 수금 · 보라 글씨 = 클로드가 만들 수 있는 서류'))
    if plan_x:
        H.append('<div class="src">앞으로 해야 될 것 전체 %d건 · <a href="%s">요약 엑셀</a> · 끝난 것은 46번으로 완료 표시</div>' % (len(plan_rows), file_url(plan_x)))
    H.append(''.join(r(c, t, tag, s, src) for c, s, t, tag, src in L1) if L1 else r('grn', '오늘 급한 것 없음', '없음'))
    H.append('<div id="l2"></div>' + h2('2층 · 현장 카드', '확정 > 역산 추정 > 미확정 · 펼치면 표') + (cards or '<div class="src">현장이 없습니다</div>'))
    H.append('<div id="l3"></div>' + h2('3층 · 부서별 작업의뢰서 (의뢰서 없으면 아무도 안 움직임)', '업무판 ↔ 10번 발행대장') + L3)
    H.append('<div id="l4"></div>' + h2('4층 · 회의 이력 14일') + L4)
    H.append('<div id="l5"></div>' + h2('5층 · 돈 총괄') + L5)
    H.append('<div id="l6"></div>' + h2('6층 · 점검 (41 총괄 · 번복 · 조용한 현장 · PLAUD)') + L6)
    H.append('<div id="l7"></div>' + h2('7층 · 표 · 확정 대장 · 원본') + L7)
    H.append('<div class="foot">더 자세히 : 층 단추 → 현장 단추 → 찾기칸 → 접힌 칸 펼치기 → 표의 링크로 원문. 틀린 값이 보이면 ★KM_번호입력 → 43 (현장·항목·값·근거) 로 고치십시오. 고친 값이 결정 사항이 되어 다음 장부터 이깁니다.</div>')
    od = outdir(TOOL)
    hp = os.path.join(od, '아침한장_%s.html' % ymd6())
    io.open(hp, 'w', encoding='utf-8').write('\n'.join(H))
    top = os.path.join(cfg('base'), '_아침한장.html')
    try:
        import shutil; shutil.copy(hp, top)
    except Exception:
        top = hp
    # 클로드용 md : 확정 대장이 맨 위
    md = ['# KM 아침 한 장  (%s · 도구 %s)' % (t0.isoformat(), VERSION), '',
          '새 창의 클로드는 이 파일을 현황판·총괄점검 md 와 함께 먼저 읽는다. **「확정」 절의 값은 프로님이 정한 것이라 어떤 추정보다 우선한다.**', '',
          '## 확정 (프로님이 정한 값 · 최신 위)', '| 일자 | 현장 | 항목 | 값 | 근거 |', '|---|---|---|---|---|']
    md += ['| %s | %s | %s | **%s** | %s |' % (d['일자'], d['현장'], d['항목'], d['값'], d['근거']) for d in fx] or ['| - | - | - | (없음) | 43번으로 넣는다 |']
    md += ['', '## 미확인 회의록 (저장만 하고 아직 못 읽으신 것 — 매일 말씀드린다)']
    if unread_mt:
        for m in unread_mt:
            md.append('- **%s · %s · %s**%s' % (m['day'] or '날짜?', m['site'] or '?', m['who'] or '',
                      ('  [%d일 지남]' % m['gap']) if m.get('gap') else ''))
            if m['agenda']:
                md.append('  - 안건 : %s' % m['agenda'])
            for nm, key in (('결정', 'decisions'), ('조치', 'actions'), ('할 일', 'todos'), ('수량·규격 변경', 'changes'), ('★대외금지', 'secret')):
                for x in (m.get(key) or []):
                    md.append('  - %s : %s' % (nm, x))
        if mt_xlsx:
            md.append('')
            md.append('요약 엑셀 : %s' % mt_xlsx)
    else:
        md.append('- (없음. 전부 확인하셨습니다)')
    md += ['', '## 찾아갈 곳 (견적을 보내 놓고 아직 안 가보신 곳 — 매일 말씀드린다)']
    _vn = [d for d in visit_rows if d['need']]
    md += ['- **%s** · %s %s · %s (보낸날 %s)' % (d['현장'], d['받는곳'], d['담당자'], d['why'], d['보낸날']) for d in _vn] or ['- (없음)']
    md += ['', '## 제가 만들까요? (클로드가 먼저 물어야 할 것 — 프로님께 「만드세요」 라고 하지 않는다)']
    offers = [d for d in plan_rows if d['만들기']]
    md += ['- **%s** · %s · 「제가 %s 만들까요?」 (할 일 : %s)' % (d['현장'], d['때'], d['만들기'], d['할일']) for d in offers] or ['- (없음)']
    md += ['', '## 앞으로 해야 될 것 (현장별 · 클로드가 넣고 프로님이 46번으로 완료 표시)']
    for site in names:
        ps = [d for d in plan_rows if same_site(d['현장'], site)]
        if not ps:
            continue
        md.append('### %s' % site)
        md += ['- %s [%s] %s%s%s%s' % (d['때'], d['등급'], d['할일'], (' → ' + d['누가']) if d['누가'] else '',
                                        (' — ' + d['왜']) if d['왜'] else '', (' 【제가 %s 만들까요?】' % d['만들기']) if d['만들기'] else '') for d in ps]
    if plan_x:
        md.append(''); md.append('요약 엑셀 : %s' % plan_x)
    md += ['', '## 1층 지금 할 것'] + ['- [%s] %s' % (tag, re.sub(r'<[^>]+>', '', t)) for c, s, t, tag, src in L1]
    md += ['', '## 조용한 현장'] + ['- %s : %s' % (s, ('%d일째 회의 없음' % g) if g is not None else '회의록 없음') for s, g in quiet_sites]
    md += ['', '## 현장 공정 (확정/추정/미확정)']
    for site in names:
        b = book.get(site) or {}
        idx, txt, kind = site_stage(site, (facts.get(site, '준공일') or {}).get('값') or b.get('due', ''))
        md.append('- %s : %s' % (site, txt))
    md += ['', '## 6층 점검'] + ['- ' + re.sub(r'<[^>]+>', '', x.replace('</span><span>', ' · ')) for x in L6.split('</div>') if x.strip()][:20]
    hd = cfg('handover')
    mdp = os.path.join(hd if os.path.isdir(hd) else od, '_아침한장.md')
    io.open(mdp, 'w', encoding='utf-8').write('\n'.join(md))
    if not quiet:
        print('아침 한 장 : %s' % top)
        print('클로드용   : %s' % mdp)
        print('업무판 파일 : %s' % (', '.join(os.path.basename(v) for v in files.values()) or '못 찾음 (시작.bat 을 돌리면 생깁니다)'))
    log(TOOL, '1층%d 현장%d 확정%d' % (len(L1), len(names), len(fx)))
    return top, mdp

def run(quiet=False):
    title('42. 아침 한 장   (7층 · 회의록·도면·돈·점검 · 확정 대장 우선 · 토큰 0)')
    top, mdp = build(quiet=quiet)
    if not common.AUTO:
        open_file(top)
    return top

if __name__ == '__main__':
    run(); pause()

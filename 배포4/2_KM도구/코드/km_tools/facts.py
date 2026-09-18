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

# ---------------- 앞으로 해야 될 것 대장 (v40) ----------------
# 프로님 : "매일 아침 이걸로 보내. 서류 만들 게 있으면 나한테 만들라고 하지 말고 네가 만들까요 하고 물어봐.
#           내가 생각 못 해서 얘기를 못 할 수도 있는데 네가 챙겨서 이렇게 할까요 하고 물어봐야지. 체계를 바꾸라고."
# 판단(무엇을 해야 하는지)은 클로드가 회의록을 읽고 쓴다 -> 받은답 `앞으로,현장,때,등급,할일,누가,왜,만들기`
# 배달·표시·완료는 파이썬이 한다 -> 42 아침 한 장 1층·2층·md, 35 아침 메일, 46번 완료 표시.
# 「만들기」 칸 = 클로드가 만들 수 있는 서류 이름. 이 칸이 차 있으면 아침 한 장·md 에 「제가 만들까요?」 로 뜬다.
#   프로님께 「만드세요」 라고 하지 않는다. 클로드가 「제가 ○○ 만들까요?」 로 먼저 묻는다.

PLAN = '앞으로할것.csv'
PLAN_HEAD = ['일자', '현장', '때', '등급', '할일', '누가', '왜', '만들기', '상태', '완료일', '코드']

def plan_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, PLAN)

def _plan_rows():
    p = plan_path()
    if not os.path.exists(p):
        write_csv(p, [['예) 2026-09-17', '조선호텔', '9/17', '확정', '중도금 신청서 + 세금계산서 + 사진대지 묶어 제출', '배성윤 → 진현창 대리',
                       '이번 달을 넘기면 잔금과 같이 밀린다', '중도금 신청서 초안', '대기', '', 'KM-001']], PLAN_HEAD)
        return []
    out = []
    for r in _read(p)[1:]:
        r = (r + [''] * 11)[:11]
        if not r[1].strip() or r[0].startswith('예)') or not r[4].strip():
            continue
        out.append(dict(zip(PLAN_HEAD, [c.strip() for c in r])))
    return out

def _when_key(when):
    """'9/17 오전' -> (0, 9, 17, 0) / '미정' -> (2,...) / 그 외 글자 -> (1,...)"""
    m = re.search(r'(\d{1,2})/(\d{1,2})', when or '')
    if m:
        return (0, int(m.group(1)), int(m.group(2)), 0 if ('오전' in when or '아침' in when) else 1)
    if '미정' in (when or ''):
        return (2, 99, 99, 0)
    return (1, 99, 99, 0)

def plan_load(site=None, active_only=True):
    """앞으로 해야 될 것 [dict]. 때(날짜) 순. site 를 주면 그 현장만 (포함관계)"""
    out = []
    for d in _plan_rows():
        if active_only and d['상태'] in ('완료', '취소'):
            continue
        if site and not (_norm(d['현장']) == _norm(site) or _norm(site) in _norm(d['현장']) or _norm(d['현장']) in _norm(site)):
            continue
        out.append(d)
    out.sort(key=lambda d: _when_key(d['때']))
    return out

def plan_due(d, day=None):
    """이 줄이 며칠 남았는지 (0=오늘, 음수=지남, None=날짜 없음)"""
    import datetime
    day = day or today()
    m = re.search(r'(\d{1,2})/(\d{1,2})', d.get('때') or '')
    if not m:
        return None
    try:
        y = day.year
        t = datetime.date(y, int(m.group(1)), int(m.group(2)))
        if (t - day).days < -180:      # 해가 바뀐 뒤 적은 날짜
            t = datetime.date(y + 1, int(m.group(1)), int(m.group(2)))
        return (t - day).days
    except Exception:
        return None

def plan_add(site, when, grade, todo, who='', why='', make='', day=None):
    """새 줄 (같은 현장·같은 할 일이 대기 중이면 넣지 않는다 - 매일 다시 넣어도 안 쌓인다)"""
    p = plan_path()
    rows = _read(p)
    if not rows:
        rows = [PLAN_HEAD]
    body = [r for r in rows[1:] if r and not r[0].startswith('예)')]
    for r in body:
        r += [''] * (11 - len(r))
        if r[1].strip() == site and _norm(r[4]) == _norm(todo) and r[8].strip() not in ('완료', '취소'):
            return None
    grade = grade if grade in ('확정', '제안') else '제안'
    new = [(day or today().isoformat()), site, when, grade, todo, who, why, make, '대기', '', next_code(body)]
    write_csv(p, [new] + body, PLAN_HEAD)
    log('앞으로', '%s %s %s' % (site, when, todo[:30]))
    return new

def plan_done(site, todo_part, day=None):
    """완료 표시 (할 일 글자 일부만 맞아도 된다). 지운 게 아니라 상태=완료 로 남긴다"""
    p = plan_path()
    rows = _read(p)
    if not rows:
        return 0
    body = rows[1:]
    n = 0
    for r in body:
        r += [''] * (11 - len(r))
        if r[8].strip() in ('완료', '취소'):
            continue
        if (not site or _norm(site) in _norm(r[1]) or _norm(r[1]) in _norm(site)) and _norm(todo_part) and _norm(todo_part) in _norm(r[4]):
            r[8] = '완료'; r[9] = (day or today().isoformat()); n += 1
    if n:
        write_csv(p, body, PLAN_HEAD)
        log('앞으로완료', '%s %s x%d' % (site, todo_part[:30], n))
    return n

def plan_offers():
    """「제가 만들까요?」 로 물어야 할 것 = 만들기 칸이 찬 대기 줄"""
    return [d for d in plan_load() if d['만들기']]

# ---------------- 견적 보낸 곳 · 찾아갈 곳 대장 (v41) ----------------
# 프로님 : "견적을 보낸 곳을 찾아가 봐야 된다고, 방문해야 할 것을 메일에 적게 해."
# 견적을 보내고 가만히 있으면 그대로 식는다. 보낸 날부터 며칠 지났는지 세어
# 42 아침 한 장 1층·35 아침 메일에 「찾아갈 곳」 으로 매일 띄운다.
# 넣는 길 : 받은답 `견적발송,현장,받는곳,담당자,금액,메모` / 47번 / csv 직접 편집
# 다녀오시면 : 받은답 `방문,현장,메모` 또는 47번에서 번호 입력 -> 마지막 방문일이 갱신되고 날짜가 다시 센다

QUOTE = '견적발송.csv'
QUOTE_HEAD = ['보낸날', '현장', '받는곳', '담당자', '금액', '마지막방문', '방문횟수', '상태', '메모']
VISIT_DUE = 3        # 보낸 뒤 이 날짜가 지나도록 안 가보셨으면 빨강
VISIT_AGAIN = 14     # 다녀오신 뒤 이만큼 지나면 다시 가보실 때

def quote_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, QUOTE)

def _quote_rows():
    p = quote_path()
    if not os.path.exists(p):
        write_csv(p, [['예) 2026-09-17', '앵커호텔', '더힐이앤씨', '이요한 선임', '', '', '0', '대기', '네고 견적']], QUOTE_HEAD)
        return []
    out = []
    for r in _read(p)[1:]:
        r = (r + [''] * 9)[:9]
        if not r[1].strip() or r[0].startswith('예)'):
            continue
        out.append(dict(zip(['보낸날', '현장', '받는곳', '담당자', '금액', '마지막방문', '방문횟수', '상태', '메모'], [c.strip() for c in r])))
    return out

def _days_since(s, day=None):
    """'2026-09-17' -> 오늘까지 며칠 (못 읽으면 None)"""
    import datetime
    if not s:
        return None
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', s) or re.search(r'(\d{2})(\d{2})(\d{2})$', s)
    if not m:
        return None
    try:
        g = m.groups()
        y = int(g[0]) if len(g[0]) == 4 else 2000 + int(g[0])
        return ((day or today()) - datetime.date(y, int(g[1]), int(g[2]))).days
    except Exception:
        return None

def quote_load(active_only=True):
    """견적 보낸 곳 [dict] + gap(보낸 뒤 며칠) · vgap(다녀온 뒤 며칠) · need(찾아가실 때인가) · why"""
    out = []
    for d in _quote_rows():
        if active_only and d['상태'] in ('수주', '탈락', '취소', '끝'):
            continue
        d['gap'] = _days_since(d['보낸날'])
        d['vgap'] = _days_since(d['마지막방문'])
        if not d['마지막방문']:
            d['need'] = (d['gap'] is None) or (d['gap'] >= VISIT_DUE)
            d['why'] = ('보낸 지 %d일 · 아직 안 가보셨습니다' % d['gap']) if d['gap'] is not None else '보낸 날짜가 비어 있습니다'
        else:
            d['need'] = (d['vgap'] is not None and d['vgap'] >= VISIT_AGAIN)
            d['why'] = ('다녀오신 지 %d일 · 다시 가보실 때입니다' % d['vgap']) if d['need'] else ('%d일 전 다녀오심' % (d['vgap'] or 0))
        out.append(d)
    out.sort(key=lambda d: (0 if d['need'] else 1, -(d['gap'] or 0)))
    return out

def quote_add(site, to='', pic='', amount='', memo='', day=None):
    """견적 보낸 곳 한 줄 (같은 현장·같은 받는곳이 살아 있으면 보낸날만 새로 고친다)"""
    p = quote_path()
    rows = _read(p)
    if not rows:
        rows = [QUOTE_HEAD]
    body = [r for r in rows[1:] if r and not r[0].startswith('예)')]
    for r in body:
        r += [''] * (9 - len(r))
        if _norm(r[1]) == _norm(site) and _norm(r[2]) == _norm(to) and r[7].strip() not in ('수주', '탈락', '취소', '끝'):
            r[0] = (day or today().isoformat())
            if memo:
                r[8] = memo
            write_csv(p, body, QUOTE_HEAD)
            log('견적발송', '%s %s (다시 보냄)' % (site, to))
            return None
    new = [(day or today().isoformat()), site, to, pic, str(amount), '', '0', '대기', memo]
    write_csv(p, [new] + body, QUOTE_HEAD)
    log('견적발송', '%s -> %s' % (site, to))
    return new

def quote_visit(site, memo='', day=None, to=''):
    """다녀오셨다고 표시 (마지막 방문일 갱신 · 횟수 +1)"""
    p = quote_path()
    rows = _read(p)
    if not rows:
        return 0
    body = rows[1:]
    n = 0
    for r in body:
        r += [''] * (9 - len(r))
        if r[7].strip() in ('수주', '탈락', '취소', '끝'):
            continue
        if (_norm(site) in _norm(r[1]) or _norm(r[1]) in _norm(site)) and (not to or _norm(to) in _norm(r[2])):
            r[5] = (day or today().isoformat())
            try:
                r[6] = str(int(r[6] or 0) + 1)
            except Exception:
                r[6] = '1'
            if memo:
                r[8] = memo
            n += 1
    if n:
        write_csv(p, body, QUOTE_HEAD)
        log('방문', '%s x%d' % (site, n))
    return n


def next_code(body=None):
    """고정 번호 KM-001 … 한 번 준 번호는 다시 쓰지 않는다 (매일 번호가 바뀌면 프로님이 헷갈린다)"""
    if body is None:
        body = [r for r in _read(plan_path())[1:] if r and not r[0].startswith('예)')]
    mx = 0
    for r in body:
        c = (r + [''] * 11)[10] if isinstance(r, list) else (r.get('코드') or '')
        m = re.search(r'KM-(\d+)', str(c))
        if m:
            mx = max(mx, int(m.group(1)))
    return 'KM-%03d' % (mx + 1)

def plan_by_code(code):
    """고정 번호로 한 줄 찾기 (KM-003 / 003 / 3 전부 됨)"""
    c = re.sub(r'[^0-9]', '', str(code or ''))
    if not c:
        return None
    for d in plan_load(active_only=False):
        if re.sub(r'[^0-9]', '', d.get('코드') or '') == c.zfill(3).lstrip('0').zfill(3) or \
           re.sub(r'[^0-9]', '', d.get('코드') or '').lstrip('0') == c.lstrip('0'):
            return d
    return None

def plan_set(code, **kw):
    """고정 번호로 한 줄을 고친다 (등급·때·할일·만들기·상태). 옛 값은 소통 이력에 남긴다"""
    p = plan_path()
    rows = _read(p)
    if not rows:
        return None
    body = rows[1:]
    c = re.sub(r'[^0-9]', '', str(code or '')).lstrip('0')
    hit = None
    for r in body:
        r += [''] * (11 - len(r))
        if re.sub(r'[^0-9]', '', r[10]).lstrip('0') == c and c:
            old = dict(zip(PLAN_HEAD, r))
            for k, v in kw.items():
                if k in PLAN_HEAD and v is not None:
                    r[PLAN_HEAD.index(k)] = str(v)
            hit = (old, dict(zip(PLAN_HEAD, r)))
            break
    if hit:
        write_csv(p, body, PLAN_HEAD)
        log('앞으로수정', '%s %s' % (code, kw))
    return hit

# ---------------- 소통 이력 (프로님이 고치신 것 · v44) ----------------
# 프로님 : "니가 메일로 보낸 것이 틀릴 수 있어. 그걸 내가 바로잡아서 너와 소통을 해야 하는데 방법을 만들어."
#   · 메일 회신(A안) · 대화(C안) 어느 쪽으로 오든 여기 한 곳에 쌓인다
#   · 42 아침 한 장 md 「## 프로님이 고치신 것」 절에 들어가 **새 창도 읽는다**
#   · 못 알아들은 답은 버리지 않고 「## 제가 못 알아들은 답」 으로 되묻는다

TALK = '소통이력.csv'
TALK_HEAD = ['일자', '경로', '코드', '현장', '프로님 말', '내가 이해한 것', '반영', '상태']

def talk_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, TALK)

def talk_add(route, code, site, said, understood, applied, state='반영'):
    """state : 반영 / 못알아들음 / 되물음 / 무시"""
    p = talk_path()
    rows = _read(p)
    body = [r for r in rows[1:] if r and len(r) > 1]
    new = [today().isoformat(), route, str(code or ''), site or '', said or '', understood or '', applied or '', state]
    write_csv(p, [new] + body, TALK_HEAD)
    log('소통', '%s %s %s' % (route, code, state))
    return new

def talk_load(days=7, state=None):
    import datetime as _dt
    cut = today() - _dt.timedelta(days=days) if days else None
    out = []
    for r in _read(talk_path())[1:]:
        r = (r + [''] * 8)[:8]
        if not r[0].strip():
            continue
        d = dict(zip(TALK_HEAD, [c.strip() for c in r]))
        if cut:
            try:
                y, m, dd = [int(x) for x in d['일자'].split('-')]
                if _dt.date(y, m, dd) < cut:
                    continue
            except Exception:
                pass
        if state and d['상태'] != state:
            continue
        out.append(d)
    return out

def talk_close(code, said):
    """되물어 해결된 것을 닫는다 (못알아들음 -> 반영)"""
    p = talk_path()
    rows = _read(p)
    body = rows[1:]
    n = 0
    for r in body:
        r += [''] * (8 - len(r))
        if r[7] == '못알아들음' and (not code or _norm(code) in _norm(r[2])) and (not said or _norm(said)[:8] in _norm(r[4])):
            r[7] = '반영'; n += 1
    if n:
        write_csv(p, body, TALK_HEAD)
    return n

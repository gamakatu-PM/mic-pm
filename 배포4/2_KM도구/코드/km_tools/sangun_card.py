# -*- coding: utf-8 -*-
"""산군 + 뉴스 = 영업 카드 (50번이 쓰는 부품). 토큰 0.

프로님 (2026-09-19) :
  "산군 데이터와 너의 구글 신문 검색 데이터를 합치면 아주 멋진 새로운 업그레이드 데이터가
   나올 것 같아. 그것을 나에게 어떻게 비서로서 효율적으로 알려줄 수 있는지 생각을 해 보고
   메일로 정리를 잘해서 본문에다가 적어주고, 그다음에 아까 만든 앱으로 연결할 수 있어 보는
   이것도 앱으로 연결되면 좋을 것 같고."

── 합치면 새로 생기는 것 (둘 중 하나만으로는 안 나오는 값) ──
  산군만 : 허가일·착공일·연면적·설계사   → 「지금 무슨 일이 벌어지는지」 를 모른다
  뉴스만 : 착공했다·중단됐다·준공 언제   → 「어느 현장인지·얼마짜리인지」 를 모른다
  합치면 :
    ① 준공 예정(기사) + 착공일(산군) → **역산** : CB외함·속판·기구물 작업의뢰서를 언제까지 내야 하는가
       (프로님 업무의 관문은 작업의뢰서다. 이 한 줄이 이 도구의 핵심이다)
    ② 연면적(산군) → 객실 추정 → 실당 단가(프로님 입력칸) → 예상 규모
    ③ 기사 날짜 + 착공일 → 「지금 안 가면 늦는다」 D-day
    ④ 소재지(산군) → 같은 시·도끼리 묶어 **하루 동선**
  숫자(실당 단가·여유일·소요일)는 도구가 정하지 않는다. 설정.ini 입력칸이다 (규칙 19).
"""
import re
import datetime
import json

# 프로님 확정 소요일 (km-site-schedule). 설정.ini [역산] 에서 고치실 수 있습니다.
DAYS = {
    '여유일': 0,
    '시운전': 7,
    '기구물설치': 7,
    '빽커버': 10,
    '기구물제작': 50,     # 1달반~2달의 가운데
    '속판제작': 60,
    '강전접속': 30,
    '외함제작': 14,
    '외함선행': 180,      # 골조 올라갈 때 외함이 들어가야 하므로 착공 뒤 6개월 어림
}

Q = {'상반기': 6, '하반기': 12, '초': 3, '중': 6, '말': 12,
     '1분기': 3, '2분기': 6, '3분기': 9, '4분기': 12}


def cfg_days(c):
    out = dict(DAYS)
    if c and c.has_section('역산'):
        for k in out:
            if c.has_option('역산', k):
                try:
                    out[k] = int(re.sub(r'[^0-9]', '', c.get('역산', k)) or out[k])
                except Exception:
                    pass
    return out


def eom(y, m):
    return datetime.date(y + (m == 12), 1 if m == 12 else m + 1, 1) - datetime.timedelta(days=1)


def find_done(texts):
    """기사에서 준공·개관 예정 시점을 찾는다. → (날짜, 근거 문구) / 못 찾으면 (None, '')"""
    blob = ' '.join(t for t in texts if t)
    pats = [
        r'(20\d{2})\s*년\s*(상반기|하반기|초|중|말|[1-4]분기)?\s*(\d{1,2})?\s*월?\s*(?:준공|완공|개관|개장|오픈|입주)',
        r'(?:준공|완공|개관|개장|오픈|입주)\s*(?:목표|예정|예정일)?\s*[:은는]?\s*(20\d{2})\s*년\s*(상반기|하반기|[1-4]분기)?\s*(\d{1,2})?\s*월?',
    ]
    for p in pats:
        m = re.search(p, blob)
        if not m:
            continue
        y = int(m.group(1))
        mon = None
        if m.lastindex and m.lastindex >= 3 and m.group(3):
            mon = int(m.group(3))
        elif m.group(2):
            mon = Q.get(m.group(2))
        if not mon:
            mon = 12
        mon = min(max(mon, 1), 12)
        s = max(m.start() - 18, 0)
        return eom(y, mon), blob[s:m.end() + 6].strip()
    return None, ''


def backdate(done, d):
    """준공일에서 거꾸로 : 언제까지 무엇을 내야 하는가 (km-site-schedule 순서 그대로)"""
    시운전완료 = done - datetime.timedelta(days=d['여유일'])
    기구물설치 = 시운전완료 - datetime.timedelta(days=d['시운전'])
    빽커버 = 기구물설치 - datetime.timedelta(days=d['기구물설치'])
    벽지완료 = 빽커버 - datetime.timedelta(days=d['빽커버'])
    기구물의뢰 = 벽지완료 - datetime.timedelta(days=d['기구물제작'])
    강전접속 = 빽커버 - datetime.timedelta(days=d['강전접속'])
    속판의뢰 = 강전접속 - datetime.timedelta(days=d['속판제작'])
    return [
        ('기구물 작업의뢰서', 기구물의뢰, '제작 %d일' % d['기구물제작']),
        ('속판(제어분전함) 작업의뢰서', 속판의뢰, '제작 %d일 + 강전접속 %d일' % (d['속판제작'], d['강전접속'])),
        ('건축에 벽지·페인트 완료 요구', 벽지완료, '빽커버 %d일 전' % d['빽커버']),
        ('기구물 설치 시작', 빽커버, ''),
        ('시운전·계산서', 시운전완료, '시운전 %d일' % d['시운전']),
    ]


def enclosure_due(start, d):
    """외함은 준공이 아니라 골조가 정한다 — 착공일 기준 어림(추정이라고 반드시 적는다)"""
    if not start:
        return None
    return start + datetime.timedelta(days=d['외함선행'] - d['외함제작'])


def to_date(s):
    s = re.sub(r'[^0-9]', '', str(s or ''))
    if len(s) == 8:
        try:
            return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except Exception:
            return None
    return None


def to_f(s):
    try:
        return float(re.sub(r'[^0-9.]', '', str(s or '')) or 0)
    except Exception:
        return 0.0


def rooms(area):
    a = to_f(area)
    if a < 200:
        return 0, 0
    return int(a / 60.0), int(a / 40.0)


def money(lo, hi, per):
    """실당 단가는 프로님이 설정.ini [역산] 실당단가 에 넣으신 값만 쓴다. 비면 '' """
    p = to_f(per)
    if not p or not hi:
        return ''
    return '예상 %s~%s만원 (실당 %s원 × %d~%d실, 프로님 입력값)' % (
        format(int(lo * p / 10000), ','), format(int(hi * p / 10000), ','),
        format(int(p), ','), lo, hi)


SIDO = [('서울', '서울'), ('부산', '부산'), ('대구', '대구'), ('인천', '인천'), ('광주', '광주'),
        ('대전', '대전'), ('울산', '울산'), ('세종', '세종'), ('경기', '경기'), ('강원', '강원'),
        ('충청북', '충북'), ('충청남', '충남'), ('충북', '충북'), ('충남', '충남'),
        ('전라북', '전북'), ('전라남', '전남'), ('전북', '전북'), ('전남', '전남'),
        ('경상북', '경북'), ('경상남', '경남'), ('경북', '경북'), ('경남', '경남'), ('제주', '제주')]


def sido(addr):
    """「충청북도 음성군」 → 충북, 「강원특별자치도 속초시」 → 강원"""
    a = (addr or '').split()
    if not a:
        return '기타'
    s = a[0]
    for pre, name in SIDO:
        if s.startswith(pre):
            return name
    return s[:2]


def build(rec, res, c, days=None):
    """현장 하나 → 영업 카드 (메일·앱·CSV 가 같이 쓴다)"""
    d = days or cfg_days(c)
    arts = res.get('기사') or []
    texts = [a.get('제목', '') for a in arts] + [res.get('본문', '')]
    done, why_done = find_done(texts)
    start = to_date(rec.get('착공일'))
    lo, hi = rooms(rec.get('연면적'))
    per = c.get('역산', '실당단가', fallback='') if (c and c.has_section('역산')) else ''

    card = {
        '등급': res.get('등급', ''),
        '현장명': rec.get('현장명', ''),
        '소재지': rec.get('소재지', ''),
        '시도': sido(rec.get('소재지')),
        '단계': rec.get('단계', ''),
        '허가일': rec.get('허가일', ''),
        '착공일': rec.get('착공일', ''),
        '연면적': rec.get('연면적', ''),
        '객실': ('약 %d~%d실' % (lo, hi)) if hi else '',
        '규모금액': money(lo, hi, per),
        '설계사': rec.get('건축설계', ''),
        '시공사': rec.get('시공사', ''),
        '건축주': rec.get('건축주', ''),
        '한줄': res.get('한줄', ''),
        '행동': res.get('행동', ''),
        '기사': arts[:5],
        '준공예정': done.isoformat() if done else '',
        '준공근거': why_done,
        '역산': [],
        '외함의뢰': '',
        '급한것': '',
        '급한D': 9999,
    }

    t0 = datetime.date.today()
    if done:
        for name, day, memo in backdate(done, d):
            card['역산'].append({'무엇': name, '언제까지': day.isoformat(),
                                 'D': (day - t0).days, '근거': memo})
    enc = enclosure_due(start, d)
    if enc:
        card['외함의뢰'] = enc.isoformat()

    # 가장 급한 한 줄 (이미 지난 것 > 가장 가까운 것)
    cand = [x for x in card['역산'] if x['무엇'].endswith('작업의뢰서')]
    if enc:
        cand.append({'무엇': 'CB외함 작업의뢰서(착공 기준 어림)', '언제까지': enc.isoformat(),
                     'D': (enc - t0).days, '근거': '착공 후 골조'})
    if cand:
        cand.sort(key=lambda x: x['D'])
        x = cand[0]
        card['급한D'] = x['D']
        card['급한것'] = ('%s — %s (%s)' %
                        (x['무엇'], x['언제까지'],
                         ('이미 %d일 지났습니다' % -x['D']) if x['D'] < 0 else 'D-%d' % x['D']))
    return card


def top3(cards):
    """오늘 딱 할 것 세 줄 — 비서가 맨 위에 적어 드리는 것"""
    out = []
    red = [c for c in cards if c['등급'].startswith('🔴')]
    orange = [c for c in cards if c['등급'].startswith('🟠')]
    late = sorted([c for c in cards if c.get('급한D', 9999) < 90], key=lambda c: c['급한D'])
    if red:
        c = red[0]
        out.append('① %s — 착공했습니다. %s 에 오늘 전화하십시오.%s'
                   % (c['현장명'], c['설계사'] or c['시공사'] or '설계사',
                      (' ' + c['급한것']) if c['급한것'] else ''))
    for c in late:
        if red and c['현장명'] == red[0]['현장명']:
            continue
        head = '② %s — %s' % (c['현장명'], c['급한것'] or '납기가 가깝습니다')
        if c['급한D'] < 0:
            head += ' 이미 늦었는지 현장에 확인하십시오.'
        out.append(head)
        break
    if orange:
        c = orange[0]
        out.append('③ %s — 상황을 물어보셔야 합니다. %s' % (c['현장명'], c['한줄'][:60]))
    while len(out) < 1:
        out.append('오늘 급한 것은 없습니다. 아래 목록만 훑어보십시오.')
    return out[:3]


def routes(cards):
    """같은 시·도끼리 묶어 하루 동선으로 (🔴·🟠 만)"""
    g = {}
    for c in cards:
        if c['등급'].startswith(('🔴', '🟠')):
            g.setdefault(c['시도'], []).append(c)
    return sorted(g.items(), key=lambda kv: -len(kv[1]))


def app_cards(cards):
    """앱(한국마이크로닉 현장관리)의 영업 파이프라인에 그대로 들어가는 형태.
    단계는 전부 0(첫 접촉)로 둔다 — 단계 판단은 프로님이 하신다. 금액도 0(입력칸)."""
    out = []
    for c in cards:
        if c['등급'].startswith(('⚫', '⛔')):
            continue
        note = []
        note.append('[%s] %s' % (c['등급'], c['한줄']))
        if c['객실']:
            note.append('연면적 %s㎡ · %s%s' % (c['연면적'], c['객실'],
                                             (' · ' + c['규모금액']) if c['규모금액'] else ''))
        if c['착공일']:
            note.append('허가 %s · 착공 %s' % (c['허가일'] or '-', c['착공일']))
        if c['급한것']:
            note.append('★ %s' % c['급한것'])
        if c['준공예정']:
            note.append('준공 예정(기사) %s — %s' % (c['준공예정'], c['준공근거'][:60]))
        for x in c['역산']:
            note.append('  · %s : %s 까지 (%s)' % (x['무엇'], x['언제까지'], x['근거']))
        if c['행동']:
            note.append('다음 행동 : %s' % c['행동'])
        for a in c['기사'][:3]:
            note.append('기사 %s %s %s' % (a.get('날짜', ''), a.get('제목', '')[:50], a.get('링크', '')))
        note.append('(산군+뉴스 자동 · %s)' % datetime.date.today().isoformat())
        out.append({
            'name': c['현장명'],
            'client': c['설계사'] or c['시공사'] or c['건축주'] or '',
            'addr': c['소재지'],
            'stage': 0,
            'amount': 0,
            'note': '\n'.join(note),
            'src': 'sangun',
            'grade': c['등급'],
        })
    return out


def app_json(cards):
    return json.dumps({'type': 'km-sangun-cards', 'ver': 1,
                       'made': datetime.date.today().isoformat(),
                       'cards': app_cards(cards)}, ensure_ascii=False, indent=1)

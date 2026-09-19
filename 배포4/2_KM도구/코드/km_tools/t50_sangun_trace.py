# -*- coding: utf-8 -*-
"""50. 산군 현장 흔적 찾기 + 산군 전용 메일 - 산군에 뜬 현장을 인터넷에서 검색해
    「기사에 흔적이 남았는가」 를 보고, 빨리 가보실 곳 / 상황을 물어볼 곳 / 조용한 곳으로
    갈라 **메일 한 통**으로 보냅니다. 토큰 0(로컬 파이썬), API 키 없음.

프로님 (2026-09-19) :
  "산군 데이터를 인터넷에서 검색을 해서 흔적을 찾아 가지고 나한테 알려 주는 방식은 안 될까?
   흔적이 찾아지면 빨리 가 보라고, 아니면 어떤 상황이냐고 이메일로 알려 주는 방식.
   통합시키는 게 아니라 각각 다 따로따로 만들어야 되지 않냐? 메일도 각각 따로따로."

그래서 이 도구는 **산군 전용 메일 한 통**만 냅니다.
  · 알리미(뉴스모니터링) 메일 — 구글시트 스크립트가 따로 보냅니다. 여기에 섞지 않습니다.
  · 구글AI 레이더 메일 — 레이더 스크립트가 따로 보냅니다. 여기에 섞지 않습니다.
  · 아침 한 장(35번) — 그것도 따로입니다. 여기에 끼워 넣지 않습니다.

찾는 곳 : 구글 뉴스 검색(RSS). 키도 요금도 없습니다. 회사망이 막으면 「검색 막힘」 으로 적고
         메일은 그대로 갑니다(산군 정보만 담아서).

등급
  🔴 지금 가십시오   착공·기공식·첫 삽·시공사 선정·도급계약·실시설계 같은 말이 기사에 있음
  🟠 상황을 물어보십시오  중단·표류·무산·소송·유찰·연기 같은 말이 있음
  🟡 아직 이릅니다   협약·계획·추진·심의 단계 (설계 들어가기 전에 찍어 둘 곳)
  ⚪ 흔적 없음      기사가 없음 → 설계사·구청에 직접 물어보실 곳

쓰는 법 : 49번(산군 관심현장 정리)을 돌린 뒤 50번. 49번 끝에서 엔터만 치셔도 이어집니다.
대장 : _도구결과\\_대장\\산군_흔적.csv  (현장마다 마지막으로 찾아본 날·등급·기사 수)
메일 설정 : 설정.ini [메일] 을 그대로 씁니다(35번에서 이미 넣으신 값). 받는 주소만 다르게 하시려면
           [산군메일] to = ... 를 넣으시면 됩니다.
"""
import os
import io
import re
import csv
import ssl
import glob
import time
import smtplib
import configparser
import datetime
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from common import (INI, cfg, title, ask, pause, today, ymd6, outdir,
                    write_csv, won, log, open_file, AUTO)

TOOL = '산군흔적'
RSS = 'https://news.google.com/rss/search?q=%s&hl=ko&gl=KR&ceid=KR:ko'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

GO = ('착공', '기공', '첫 삽', '첫삽', '시공사 선정', '시공사선정', '도급계약', '수주',
      '실시설계', '설계 완료', '골조', '상량', '기공식', '터파기')
ASK = ('중단', '표류', '무산', '취소', '소송', '유찰', '연기', '좌초', '방치', '공매',
       '부도', '회생', '분쟁', '철회')
EARLY = ('협약', 'MOU', '추진', '계획', '심의', '유치', '공모', '투자', '검토', '승인')
DONE = ('준공', '개관', '오픈', '개장', '영업 시작', '입주 시작')

GRADE_GO, GRADE_ASK, GRADE_EARLY, GRADE_NONE, GRADE_DONE, GRADE_ERR = (
    '🔴 지금 가십시오', '🟠 상황을 물어보십시오', '🟡 아직 이릅니다', '⚪ 흔적 없음', '⚫ 이미 끝남',
    '⛔ 검색 못 함')
ORDER = {GRADE_GO: 0, GRADE_ASK: 1, GRADE_EARLY: 2, GRADE_NONE: 3, GRADE_DONE: 4, GRADE_ERR: 5}

BOOK_HEAD = ['마지막찾은날', '키', '현장명', '소재지', '등급', '기사수', '최근기사일', '한줄']
OUT_HEAD = ['등급', '현장명', '소재지', '단계', '허가일', '착공일', '연면적㎡', '객실추정',
            '건축설계(갈 곳)', '시공사', '건축주·발주처', '기사수', '최근기사일', '무슨 일이 있었나',
            '다음 행동', '기사1', '기사2', '기사3']


# ====================== 설정 ======================

def conf():
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        try:
            c.read(INI, encoding='utf-8')
        except Exception:
            pass
    return c


def mail_to(c):
    if c.has_option('산군메일', 'to') and c.get('산군메일', 'to').strip():
        return c.get('산군메일', 'to').strip()
    return c.get('메일', 'to', fallback='').strip()


def again_days(c):
    """한 번 찾아본 현장을 며칠 뒤에 다시 찾아볼지"""
    try:
        return int(re.sub(r'[^0-9]', '', c.get('산군메일', '다시찾기일수', fallback='7')) or 7)
    except Exception:
        return 7


# ====================== 검색 ======================

def query_of(rec):
    """현장명에서 지번·군더더기를 덜어 내고, 지역 한 조각을 붙여 검색어를 만든다."""
    name = str(rec.get('현장명') or '')
    name = re.sub(r'\d+[-–]\d+번?지?', ' ', name)          # 976-7, 1558-3
    name = re.sub(r'(산)?\d+번지', ' ', name)
    name = re.sub(r'\b\d{2,}\b', ' ', name)
    name = re.sub(r'(신축공사|신축|증축|공사)\s*$', '', name).strip()
    name = re.sub(r'\s+', ' ', name)
    addr = str(rec.get('소재지') or '').split()
    where = ''
    for a in addr:
        if a.endswith(('시', '군', '구')) and len(a) >= 2:
            where = a
            break
    if not where and addr:
        where = addr[0]
    q = ('%s %s' % (name, where)).strip()
    return q or name or where


def fetch_rss(q, timeout=20):
    url = RSS % urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def parse_rss(raw, limit=8):
    """구글 뉴스 RSS → [{제목, 날짜, 언론사, 링크}]"""
    out = []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return out
    for it in root.findall('.//item')[:limit]:
        t = (it.findtext('title') or '').strip()
        src = ''
        s = it.find('source')
        if s is not None and (s.text or '').strip():
            src = s.text.strip()
        elif ' - ' in t:
            src = t.rsplit(' - ', 1)[1].strip()
        out.append({
            '제목': t,
            '날짜': to_ymd(it.findtext('pubDate') or ''),
            '언론사': src,
            '링크': (it.findtext('link') or '').strip(),
        })
    return out


def to_ymd(s):
    s = (s or '').strip()
    for f in ('%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z'):
        try:
            return datetime.datetime.strptime(s, f).date().isoformat()
        except Exception:
            pass
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    return m.group(0) if m else ''


def search(rec, sleep=1.0):
    """현장 하나를 인터넷에서 찾아본다. (막히면 빈 목록 + 사유)"""
    q = query_of(rec)
    try:
        arts = parse_rss(fetch_rss(q))
        err = ''
    except Exception as e:
        arts, err = [], '검색 막힘(%s)' % type(e).__name__
    if sleep:
        time.sleep(sleep)     # 연달아 부르면 구글이 막는다
    return q, arts, err


# ====================== 판정 ======================

def recent(arts):
    ds = [a['날짜'] for a in arts if a.get('날짜')]
    return max(ds) if ds else ''


def hits(arts, words):
    got = []
    for a in arts:
        for w in words:
            if w in a['제목'] and w not in got:
                got.append(w)
    return got


def judge(rec, arts, err):
    """등급 · 무슨 일이 있었나 · 다음 행동(복사해서 바로 쓰실 문안까지)"""
    site = rec.get('현장명') or ''
    designer = (rec.get('건축설계') or '').strip()
    builder = (rec.get('시공사') or '').strip()
    where = (rec.get('소재지') or '').split(' ')
    gu = ' '.join(where[:2]) if len(where) >= 2 else (rec.get('소재지') or '')

    if err:
        return (GRADE_ERR, err + ' — 회사망이 막았거나 인터넷이 끊겼습니다',
                '집·휴대폰에서 다시 50번을 돌려 보십시오. 산군 정보만으로 먼저 보시려면 49번 파일을 보십시오.')
    if not arts:
        who = designer or ('%s 건축과' % gu)
        return (GRADE_NONE, '기사 한 줄 없음 — 조용히 진행 중이거나 아직 안 알려진 현장',
                '%s 에 전화 : "%s 건으로 연락드렸습니다. 객실관리(RCU) 설계 반영 시점을 여쭙고 싶습니다."' % (who, site))

    go, ask_, early, done = hits(arts, GO), hits(arts, ASK), hits(arts, EARLY), hits(arts, DONE)
    top = arts[0]['제목']

    if ask_:
        who = builder or designer or ('%s 건축과' % gu)
        return (GRADE_ASK, '기사에 「%s」 — %s' % ('·'.join(ask_), top),
                '%s 에 전화 : "%s 현장이 지금 어떤 상황인지 여쭙고 싶습니다. 재개되면 객실관리는 저희가 준비해 두겠습니다."' % (who, site))
    if done and not go:
        return (GRADE_DONE, '기사에 「%s」 — 이미 끝났을 수 있음 : %s' % ('·'.join(done), top),
                '신축은 늦었습니다. 교체·증축 영업으로 돌리시려면 운영사에 연락하십시오.')
    if go:
        who = builder or designer or '시공사'
        return (GRADE_GO, '기사에 「%s」 — %s' % ('·'.join(go), top),
                '%s 에 바로 연락 : "%s 착공 기사를 봤습니다. CB 외함 납품 시점 맞추려면 지금 도면 협의가 필요합니다. 방문드려도 되겠습니까?"' % (who, site))
    if early:
        who = designer or ('%s 건축과' % gu)
        return (GRADE_EARLY, '기사에 「%s」 — %s' % ('·'.join(early), top),
                '%s 에 미리 찍어 두기 : "%s 건으로 객실관리 시방서·심볼을 미리 드리고 싶습니다." (설계 단계가 제일 좋습니다)' % (who, site))
    return (GRADE_EARLY, '기사는 있으나 공사 단계 낱말이 없음 — %s' % top,
            '기사 먼저 읽어 보시고, 설계사(%s)에 진행 단계를 확인하십시오.' % (designer or '미표시'))


# ====================== 대상 현장 ======================

def latest_49_csv():
    pats = sorted(glob.glob(os.path.join(cfg('out'), '산군', '*', '산군_새현장_*.csv')),
                  key=lambda p: os.path.getmtime(p), reverse=True)
    return pats[0] if pats else ''


def read_csv_rows(p):
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                return list(csv.reader(fp))
        except Exception:
            continue
    return []


def targets(p):
    """49번이 낸 CSV → 현장 목록 (✕제외는 이미 빠져 있음)"""
    rows = read_csv_rows(p)
    if not rows:
        return []
    head = rows[0]
    idx = {name: i for i, name in enumerate(head)}

    def g(r, name):
        i = idx.get(name, -1)
        return r[i].strip() if 0 <= i < len(r) else ''

    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        out.append({
            '판정': g(r, '판정'), '현장명': g(r, '현장명'), '소재지': g(r, '소재지'),
            '단계': g(r, '단계'), '허가일': g(r, '허가일'), '착공일': g(r, '착공일'),
            '연면적': g(r, '연면적㎡'), '객실추정': g(r, '객실추정'),
            '건축설계': g(r, '건축설계(갈 곳)'), '시공사': g(r, '시공사'),
            '건축주': g(r, '건축주·발주처'),
        })
    return out


def book_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '산군_흔적.csv')


def key_of(rec):
    s = '%s|%s' % (rec.get('현장명', ''), rec.get('소재지', ''))
    return re.sub(r'[\s\-()·,]', '', s)[:120]


def load_book():
    p = book_path()
    if not os.path.exists(p):
        return {}
    rows = read_csv_rows(p)
    return {r[1]: r for r in rows[1:] if len(r) >= 2 and r[1]}


def days_since(s):
    try:
        y, m, d = [int(x) for x in s.split('-')]
        return (today() - datetime.date(y, m, d)).days
    except Exception:
        return 9999


# ====================== 메일 ======================

def esc(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def card(rec, res):
    g = res['등급']
    color = {GRADE_GO: '#C0392B', GRADE_ASK: '#C77B2B', GRADE_EARLY: '#2A6099',
             GRADE_NONE: '#8E99A4', GRADE_DONE: '#6B4FA8', GRADE_ERR: '#8E99A4'}.get(g, '#ccc')
    h = ['<div style="border-left:5px solid %s;background:#fafafa;padding:10px 12px;margin:10px 0">' % color]
    h.append('<div style="font-size:15px"><b>%s</b> <span style="color:%s">%s</span></div>'
             % (esc(rec.get('현장명')), color, esc(g)))
    line = [x for x in [rec.get('소재지'), rec.get('단계'),
                        (rec.get('연면적') and rec.get('연면적') + '㎡'), rec.get('객실추정')] if x]
    h.append('<div style="color:#444">%s</div>' % esc(' · '.join(line)))
    line2 = []
    if rec.get('허가일'):
        line2.append('허가 %s' % rec['허가일'])
    if rec.get('착공일'):
        line2.append('착공 %s' % rec['착공일'])
    if line2:
        h.append('<div style="color:#444">%s</div>' % esc(' · '.join(line2)))
    h.append('<div style="color:#444">설계 <b>%s</b> · 시공 %s · 건축주 %s</div>'
             % (esc(rec.get('건축설계') or '미표시'), esc(rec.get('시공사') or '미표시'),
                esc(rec.get('건축주') or '미표시')))
    h.append('<div style="margin-top:6px"><b>무슨 일이 있었나</b> : %s</div>' % esc(res['한줄']))
    if res['기사']:
        h.append('<div style="margin-top:4px"><b>기사 %d건</b><ul style="margin:4px 0 0 18px;padding:0">'
                 % len(res['기사']))
        for a in res['기사'][:5]:
            h.append('<li style="margin:2px 0">%s <span style="color:#888">%s %s</span> %s</li>'
                     % (esc(a['제목']), esc(a['날짜']), esc(a['언론사']),
                        ('<a href="%s">보기</a>' % esc(a['링크'])) if a['링크'] else ''))
        h.append('</ul></div>')
    h.append('<div style="margin-top:6px;background:#fff;border:1px dashed #bbb;padding:6px">'
             '<b>다음 행동</b> : %s</div>' % esc(res['행동']))
    h.append('</div>')
    return ''.join(h)


def build_html(groups, src, err_n):
    n = {k: len(v) for k, v in groups.items()}
    h = ['<div style="font-family:맑은 고딕,system-ui;font-size:14px;line-height:1.5">']
    h.append('<h2 style="margin:0 0 2px">산군 현장 흔적 %s</h2>' % today().isoformat())
    h.append('<div style="color:#666;font-size:12px">빨리 가보실 곳 <b>%d</b>곳 · 상황 물어보실 곳 <b>%d</b>곳 · '
             '아직 이른 곳 %d곳 · 흔적 없는 곳 %d곳 · 끝난 곳 %d곳</div>'
             % (n.get(GRADE_GO, 0), n.get(GRADE_ASK, 0), n.get(GRADE_EARLY, 0),
                n.get(GRADE_NONE, 0), n.get(GRADE_DONE, 0)))
    for g in (GRADE_GO, GRADE_ASK, GRADE_EARLY, GRADE_NONE, GRADE_DONE):
        if not groups.get(g):
            continue
        h.append('<h3 style="margin:18px 0 4px;border-bottom:2px solid #eee">%s (%d곳)</h3>'
                 % (esc(g), len(groups[g])))
        for rec, res in groups[g]:
            h.append(card(rec, res))
    h.append('<p style="color:#888;font-size:12px;margin-top:18px">'
             '산군 파일 : %s<br>'
             '이 메일은 PC 도구 50번이 구글 뉴스 검색으로 찾은 것입니다(클로드·Gemini 안 씀, 요금 0원).'
             '%s<br>알리미(뉴스모니터링) 메일과 구글AI 레이더 메일은 <b>따로</b> 갑니다. 이 메일에 섞지 않았습니다.<br>'
             '한 번 찾아본 현장은 며칠 뒤에 다시 찾습니다(설정.ini [산군메일] 다시찾기일수).</p></div>'
             % (esc(os.path.basename(src)),
                (' 검색이 막힌 현장 %d곳은 「흔적 없음」 으로 두었습니다.' % err_n) if err_n else ''))
    return ''.join(h)


def send_mail(subject, html):
    """산군 전용 메일 한 통. 설정.ini [메일] 값을 그대로 씁니다(35번과 같은 계정, 다른 메일)."""
    c = conf()
    g = lambda k, d='': c.get('메일', k, fallback=d)
    to = mail_to(c)
    if not (g('user') and g('password') and to):
        print('[메일 설정 없음] 35번에서 보내는 계정·앱 비밀번호를 먼저 넣어 주십시오.')
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = g('user')
    msg['To'] = to
    msg.attach(MIMEText('HTML 메일입니다. 안 보이시면 PC 의 산군_흔적 한 장을 여십시오.', 'plain', 'utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(g('smtp') or 'smtp.gmail.com', int(g('port') or 587), timeout=30) as s:
            s.starttls(context=ctx)
            s.login(g('user'), g('password'))
            s.sendmail(g('user'), [to], msg.as_string())
        print('메일 보냈습니다 -> %s' % to)
        return True
    except Exception as e:
        print('[메일 실패] %s' % e)
        print('  앱 비밀번호(16자리)인지, 회사망이 587 을 막는지 보십시오. 파일은 그대로 남아 있습니다.')
        return False


# ====================== 본체 ======================

def run(src='', send=None, sleep=1.0):
    title('50. 산군 현장 흔적 찾기 + 산군 전용 메일 (토큰 0)')
    c = conf()
    src = src or latest_49_csv()
    if not src or not os.path.exists(src):
        print('49번(산군 관심현장 정리) 결과가 없습니다. 49번을 먼저 돌려 주십시오.')
        return
    recs = targets(src)
    if not recs:
        print('찾아볼 현장이 없습니다 : %s' % src)
        return

    book = load_book()
    wait = again_days(c)
    todo = [r for r in recs if days_since((book.get(key_of(r)) or ['', '', '', '', '', '', '', ''])[0]) >= wait]
    skip = len(recs) - len(todo)
    print('현장 %s곳 중 %s곳을 찾아봅니다 (%s곳은 %d일 안에 이미 찾아봄)'
          % (won(len(recs)), won(len(todo)), won(skip), wait))
    if not todo:
        print('새로 찾아볼 현장이 없어 메일을 보내지 않습니다.')
        return

    groups, body, err_n = {}, [], 0
    for i, rec in enumerate(todo, 1):
        q, arts, err = search(rec, sleep=sleep)
        if err:
            err_n += 1
        g, why, act = judge(rec, arts, err)
        res = {'등급': g, '한줄': why, '행동': act, '기사': arts}
        groups.setdefault(g, []).append((rec, res))
        print('  [%d/%d] %s %s (기사 %d)' % (i, len(todo), g[:2], rec['현장명'][:24], len(arts)))
        a1 = arts[0] if arts else {}
        a2 = arts[1] if len(arts) > 1 else {}
        a3 = arts[2] if len(arts) > 2 else {}
        body.append([g, rec['현장명'], rec['소재지'], rec['단계'], rec['허가일'], rec['착공일'],
                     rec['연면적'], rec['객실추정'], rec['건축설계'], rec['시공사'], rec['건축주'],
                     len(arts), recent(arts), why, act,
                     a1.get('제목', ''), a2.get('제목', ''), a3.get('제목', '')])
        if g != GRADE_ERR:      # 검색이 막힌 현장은 대장에 안 적는다 -> 다음에 다시 찾는다
            book[key_of(rec)] = [today().isoformat(), key_of(rec), rec['현장명'], rec['소재지'],
                                 g.split(' ')[-1], len(arts), recent(arts), why[:80]]

    body.sort(key=lambda r: ORDER.get(r[0], 9))
    od = outdir(TOOL)
    cp = write_csv(os.path.join(od, '산군_흔적_%s.csv' % ymd6()), body, OUT_HEAD)
    html = build_html(groups, src, err_n)
    hp = os.path.join(od, '산군_흔적_%s.html' % ymd6())
    io.open(hp, 'w', encoding='utf-8').write(html)
    write_csv(book_path(), [book[k] for k in book], BOOK_HEAD)

    go_n = len(groups.get(GRADE_GO, []))
    ask_n = len(groups.get(GRADE_ASK, []))
    subject = '[산군] 빨리 가보실 곳 %d곳 · 상황 물어보실 곳 %d곳 (%s)' % (go_n, ask_n, today().isoformat())

    print('')
    print('빨리 가보실 곳 %d · 상황 물어보실 곳 %d · 아직 이른 곳 %d · 흔적 없음 %d'
          % (go_n, ask_n, len(groups.get(GRADE_EARLY, [])), len(groups.get(GRADE_NONE, []))))
    print('파일 : %s' % cp)
    print('한 장 : %s' % hp)

    only_err = (len(groups) == 1 and GRADE_ERR in groups)
    if only_err:
        # 검색이 통째로 막힌 날은 메일을 보내지 않는다 (볼 게 없는 메일은 안 보낸다)
        print('')
        print('인터넷 검색이 통째로 막혔습니다 - 메일은 보내지 않았습니다.')
        print('  회사망이 news.google.com 을 막았을 수 있습니다. 집이나 휴대폰 테더링에서 다시 돌려 보십시오.')
        send = False
    if send is None:
        send = (ask('메일로 보낼까요? (엔터=예) > ', '예') or '예').strip() not in ('아니오', 'n', 'N', '아니요')
    if send:
        send_mail(subject, html)
    log(TOOL, '%d곳 중 빨리%d 물어봄%d' % (len(todo), go_n, ask_n))
    try:
        open_file(hp)
    except Exception:
        pass


if __name__ == '__main__':
    run()
    pause()

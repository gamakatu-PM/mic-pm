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

v2 (2026-09-19 오후, 프로님 「객관식·주관식 다 적용해」) :
  ① 기사 **본문**까지 읽습니다. 제목에 「착공」 이 있어도 본문이 「착공 예정·앞두고」 면 🔴 이 아니라 🟡 로 내립니다.
     (구글 뉴스 링크 → 원래 신문사 주소로 풀어서 본문을 읽습니다. 못 풀면 제목만 봅니다)
  ② **주 1회 자동** : 50번 안의 「등록」 을 누르면 작업 스케줄러에 매주 월요일 07:30 이 들어갑니다.
     그때는 다운로드 폴더의 최신 산군 파일로 49번을 묻지 않고 돌리고, 지금까지 본 ★·△ 현장 전부를
     7일 주기로 다시 찾아 메일을 보냅니다. 새 흔적이 하나도 없으면 메일은 안 갑니다.
  ③ 🔴·🟠 현장에 **지도 링크 + 예상 소요 시간**. 지도는 키 없이 카카오맵·네이버지도 링크.
     소요 시간은 ㉠ 설정.ini [산군메일] kakao_key + 출발지 를 넣으시면 카카오 길찾기로 자동차 시간을 받아 오고
     ㉡ 키가 없으면 설정.ini [소요시간] 표(서울=, 강원=, …)를 프로님이 채우신 값으로 적습니다. 비어 있으면 안 적습니다.
     (숫자는 도구가 정하지 않습니다 — 규칙 19)

v3 (2026-09-19 밤, 프로님 「산군 + 신문 검색을 합치면 멋진 업그레이드 데이터가 나올 것 같다.
    비서로서 효율적으로 알려 주고, 앱으로도 연결해 달라」) :
  ④ **합친 값**을 냅니다 — 둘 중 하나만으로는 안 나오는 것
     · 기사의 준공 예정 + 산군의 착공일 → **역산** : 기구물·속판·CB외함 작업의뢰서를 언제까지 내야 하는가
     · 연면적 → 객실 추정 → 실당 단가(설정.ini [역산] 실당단가, 프로님 입력칸) → 예상 규모
     · 같은 시·도끼리 묶은 **하루 동선**
  ⑤ 메일 맨 위에 **「오늘 이것만」 세 줄** — 나머지는 아래에 펼쳐 둡니다
  ⑥ **앱 연결** : 같은 내용을 앱(한국마이크로닉 현장관리)의 영업 파이프라인 형식 JSON 으로 만들어
     메일에 첨부합니다. 앱 > 영업 파이프라인 > 「📡 산군 불러오기」 에서 그 파일을 고르시면 카드가 들어갑니다.
     (단계는 전부 「첫 접촉」, 금액은 0 으로 넣습니다 — 판단과 금액은 프로님 몫)

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
import sys
import json
import html as _html
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from common import (INI, HERE, cfg, title, ask, pause, today, ymd6, outdir,
                    write_csv, won, log, open_file)
import common
import sangun_card as SC
import sangun_mail as SM

TOOL = '산군흔적'
TASK = 'KM_산군메일_주1회'
WEEKLY_AT = '07:30'
WEEKLY_DAY = 'MON'
RSS = 'https://news.google.com/rss/search?q=%s&hl=ko&gl=KR&ceid=KR:ko'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'

GO = ('착공', '기공', '첫 삽', '첫삽', '시공사 선정', '시공사선정', '도급계약', '수주',
      '실시설계', '설계 완료', '골조', '상량', '기공식', '터파기')
ASK = ('중단', '표류', '무산', '취소', '소송', '유찰', '연기', '좌초', '방치', '공매',
       '부도', '회생', '분쟁', '철회')
EARLY = ('협약', 'MOU', '추진', '계획', '심의', '유치', '공모', '투자', '검토', '승인')
DONE = ('준공', '개관', '오픈', '개장', '영업 시작', '입주 시작')
# 본문에 이 말이 있으면 「착공」 이 아니라 「착공 예정」 이다
NOT_YET = ('착공 예정', '착공예정', '착공을 앞두', '착공 앞두', '착공할 예정', '착공 계획', '착공 목표',
           '연내 착공', '내년 착공', '착공에 들어갈', '착공할 계획', '착공 전')
YET_DONE = ('착공했', '착공식', '기공식', '첫 삽을', '착공에 들어갔', '공사에 들어갔', '공사가 시작')

GRADE_GO, GRADE_ASK, GRADE_EARLY, GRADE_NONE, GRADE_DONE, GRADE_ERR = (
    '🔴 지금 가십시오', '🟠 상황을 물어보십시오', '🟡 아직 이릅니다', '⚪ 흔적 없음', '⚫ 이미 끝남',
    '⛔ 검색 못 함')
ORDER = {GRADE_GO: 0, GRADE_ASK: 1, GRADE_EARLY: 2, GRADE_NONE: 3, GRADE_DONE: 4, GRADE_ERR: 5}

BOOK_HEAD = ['마지막찾은날', '키', '현장명', '소재지', '등급', '기사수', '최근기사일', '한줄']
OUT_HEAD = ['등급', '현장명', '소재지', '단계', '허가일', '착공일', '연면적㎡', '객실추정',
            '건축설계(갈 곳)', '시공사', '건축주·발주처', '기사수', '최근기사일', '무슨 일이 있었나',
            '다음 행동', '준공예정(기사)', '가장 급한 것', 'CB외함 의뢰', '기구물 의뢰', '속판 의뢰',
            '예상 규모', '기사1', '기사2', '기사3']


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


def ensure_ini():
    """[산군메일]·[소요시간] 입력칸이 없으면 빈 칸으로 만들어 둔다 (프로님이 채우시는 곳)"""
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        try:
            c.read(INI, encoding='utf-8')
        except Exception:
            pass
    changed = False
    if not c.has_section('산군메일'):
        c.add_section('산군메일'); changed = True
    for k, v in (('to', ''), ('다시찾기일수', '7'), ('출발지', ''), ('kakao_key', ''), ('본문읽기', '예'),
                 ('한번에', '60'), ('메일에펼칠곳', '25'), ('서식', 'v2')):
        if not c.has_option('산군메일', k):
            c.set('산군메일', k, v); changed = True
    if not c.has_section('역산'):
        c.add_section('역산'); changed = True
        c.set('역산', '실당단가', '')      # 비우면 예상 금액을 안 적습니다 (규칙 19)
        for k, v in SC.DAYS.items():
            c.set('역산', k, str(v))
    if not c.has_section('소요시간'):
        c.add_section('소요시간'); changed = True
        for k in ('서울', '경기', '인천', '강원', '충북', '충남', '대전', '세종', '전북', '전남', '광주',
                  '경북', '경남', '대구', '울산', '부산', '제주'):
            c.set('소요시간', k, '')
    if changed:
        try:
            with io.open(INI, 'w', encoding='utf-8') as fp:
                c.write(fp)
        except Exception:
            pass
    return c


def opt(c, k, d=''):
    try:
        return c.get('산군메일', k, fallback=d).strip()
    except Exception:
        return d


def num(c, k, d):
    try:
        return int(re.sub(r'[^0-9]', '', c.get('산군메일', k, fallback=str(d))) or d)
    except Exception:
        return d


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


# ====================== 기사 본문 ======================

def http_get(url, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ko'})
    r = urllib.request.urlopen(req, timeout=timeout)
    raw = r.read()
    final = r.geturl()
    enc = 'utf-8'
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000], re.I)
    if m:
        enc = m.group(1).decode('ascii', 'ignore')
    try:
        txt = raw.decode(enc, 'replace')
    except Exception:
        txt = raw.decode('utf-8', 'replace')
    return final, txt


def resolve_google(link):
    """구글 뉴스 링크 → (원래 신문사 주소, 이미 받은 본문 HTML). 못 풀면 ('', '')
    구글이 바로 신문사로 넘겨 주면 그 페이지를 그대로 쓴다(두 번 안 받는다)."""
    if 'news.google.com' not in link:
        return link, ''
    try:
        final, page = http_get(link)
    except Exception:
        return '', ''
    if 'news.google.com' not in final:
        return final, page
    for pat in (r'data-n-au="([^"]+)"', r'<a[^>]+href="(https?://(?!news\.google|www\.google|accounts\.google)[^"]+)"',
                r'"(https?://(?!news\.google|www\.google|accounts\.google|policies\.google)[^"\s]{12,})"'):
        m = re.search(pat, page)
        if m:
            return _html.unescape(m.group(1)), ''
    return '', ''


def strip_html(page, limit=5000):
    page = re.sub(r'(?is)<(script|style|noscript|header|footer|nav)[^>]*>.*?</\1>', ' ', page)
    page = re.sub(r'(?s)<[^>]+>', ' ', page)
    page = _html.unescape(page)
    page = re.sub(r'\s+', ' ', page).strip()
    return page[:limit]


def read_body(link):
    """기사 본문 앞부분. (제목만으로 안 갈리는 것을 본문으로 가른다) 못 읽으면 ''"""
    url, page = resolve_google(link)
    if not url:
        return ''
    if not page:
        try:
            _, page = http_get(url)
        except Exception:
            return ''
    return strip_html(page)


# ====================== 지도 · 소요 시간 ======================

def map_links(addr, origin=''):
    a = urllib.parse.quote(addr or '')
    out = {'카카오맵': 'https://map.kakao.com/?q=' + a,
           '네이버지도': 'https://map.naver.com/p/search/' + a}
    if origin:
        out['길찾기'] = 'https://map.kakao.com/?sName=%s&eName=%s' % (urllib.parse.quote(origin), a)
    return out


def kakao_xy(addr, key):
    for path, q in (('address', addr), ('keyword', addr)):
        url = 'https://dapi.kakao.com/v2/local/search/%s.json?query=%s' % (path, urllib.parse.quote(addr))
        req = urllib.request.Request(url, headers={'Authorization': 'KakaoAK ' + key, 'User-Agent': UA})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
            docs = d.get('documents') or []
            if docs:
                return docs[0]['x'], docs[0]['y']
        except Exception:
            continue
    return None


_XY = {}


def travel(addr, c):
    """예상 소요 시간 문구. ㉠ 카카오 키+출발지 있으면 길찾기 API ㉡ 없으면 [소요시간] 입력표 ㉢ 둘 다 없으면 ''"""
    key, origin = opt(c, 'kakao_key'), opt(c, '출발지')
    if key and origin and addr:
        try:
            if origin not in _XY:
                _XY[origin] = kakao_xy(origin, key)
            o, d = _XY[origin], kakao_xy(addr, key)
            if o and d:
                url = ('https://apis-navi.kakaomobility.com/v1/directions?origin=%s,%s&destination=%s,%s'
                       % (o[0], o[1], d[0], d[1]))
                req = urllib.request.Request(url, headers={'Authorization': 'KakaoAK ' + key, 'User-Agent': UA})
                js = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))
                sm = js['routes'][0]['summary']
                sec, km = int(sm['duration']), sm['distance'] / 1000.0
                h, m = sec // 3600, (sec % 3600) // 60
                return '자동차 약 %s%d분 · %.0fkm (카카오 길찾기, %s 출발)' % (('%d시간 ' % h) if h else '', m, km, origin)
        except Exception as e:
            pass
    # 입력표
    try:
        first = (addr or '').split(' ')[0]
        for k in c.options('소요시간') if c.has_section('소요시간') else []:
            v = c.get('소요시간', k).strip()
            if v and first.startswith(k):
                return '대략 %s (설정.ini 소요시간표 「%s」)' % (v, k)
    except Exception:
        pass
    return ''


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


def judge(rec, arts, err, bodies=None):
    """등급 · 무슨 일이 있었나 · 다음 행동(복사해서 바로 쓰실 문안까지)
    bodies = {링크: 본문} — 본문이 있으면 제목+본문으로 낱말을 찾고, 「착공 예정」 은 🔴 에서 뺀다"""
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

    bodies = bodies or {}
    pool = [dict(a, 제목=a['제목'] + ' ' + bodies.get(a['링크'], '')[:3000]) for a in arts]
    go, ask_, early, done = hits(pool, GO), hits(pool, ASK), hits(pool, EARLY), hits(pool, DONE)
    top = arts[0]['제목']
    text_all = ' '.join(p['제목'] for p in pool)
    not_yet = any(w in text_all for w in NOT_YET) and not any(w in text_all for w in YET_DONE)
    read_n = sum(1 for a in arts if bodies.get(a['링크']))
    tag = (' (본문 %d건 읽음)' % read_n) if read_n else ' (제목만 봄)'

    if ask_:
        who = builder or designer or ('%s 건축과' % gu)
        return (GRADE_ASK, '기사에 「%s」%s — %s' % ('·'.join(ask_), tag, top),
                '%s 에 전화 : "%s 현장이 지금 어떤 상황인지 여쭙고 싶습니다. 재개되면 객실관리는 저희가 준비해 두겠습니다."' % (who, site))
    if done and not go:
        return (GRADE_DONE, '기사에 「%s」%s — 이미 끝났을 수 있음 : %s' % ('·'.join(done), tag, top),
                '신축은 늦었습니다. 교체·증축 영업으로 돌리시려면 운영사에 연락하십시오.')
    if go and not_yet:
        who = designer or builder or ('%s 건축과' % gu)
        return (GRADE_EARLY, '기사에 「%s」 가 있지만 본문은 「착공 예정」%s — %s' % ('·'.join(go), tag, top),
                '%s 에 미리 연락 : "%s 착공 전에 객실관리 도면 협의를 하고 싶습니다. 착공 예정일이 언제입니까?"' % (who, site))
    if go:
        who = builder or designer or '시공사'
        return (GRADE_GO, '기사에 「%s」%s — %s' % ('·'.join(go), tag, top),
                '%s 에 바로 연락 : "%s 착공 기사를 봤습니다. CB 외함 납품 시점 맞추려면 지금 도면 협의가 필요합니다. 방문드려도 되겠습니까?"' % (who, site))
    if early:
        who = designer or ('%s 건축과' % gu)
        return (GRADE_EARLY, '기사에 「%s」%s — %s' % ('·'.join(early), tag, top),
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


def all_49_csv():
    return sorted(glob.glob(os.path.join(cfg('out'), '산군', '*', '산군_새현장_*.csv')),
                  key=lambda p: os.path.getmtime(p))


def targets_all():
    """지금까지 49번이 낸 CSV 전부 → 현장 목록(같은 현장은 한 번). 주 1회 자동 실행이 쓴다"""
    seen, out = set(), []
    for p in all_49_csv():
        for r in targets(p):
            k = key_of(r)
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
    return out


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
    cd = res.get('카드') or {}
    color = {GRADE_GO: '#C0392B', GRADE_ASK: '#C77B2B', GRADE_EARLY: '#2A6099',
             GRADE_NONE: '#8E99A4', GRADE_DONE: '#6B4FA8', GRADE_ERR: '#8E99A4'}.get(g, '#ccc')
    h = ['<div style="border-left:5px solid %s;background:#fafafa;padding:10px 12px;margin:10px 0">' % color]
    h.append('<div style="font-size:15px"><b>%s</b> <span style="color:%s">%s</span></div>'
             % (esc(rec.get('현장명')), color, esc(g)))
    line = [x for x in [rec.get('소재지'), rec.get('단계'),
                        (rec.get('연면적') and rec.get('연면적') + '㎡'), cd.get('객실') or rec.get('객실추정')] if x]
    h.append('<div style="color:#444">%s</div>' % esc(' · '.join(line)))
    if cd.get('규모금액'):
        h.append('<div style="color:#1a5">%s</div>' % esc(cd['규모금액']))
    line2 = []
    if rec.get('허가일'):
        line2.append('허가 %s' % rec['허가일'])
    if rec.get('착공일'):
        line2.append('착공 %s' % rec['착공일'])
    if cd.get('준공예정'):
        line2.append('<b>준공 예정 %s</b>(기사)' % cd['준공예정'])
    if line2:
        h.append('<div style="color:#444">%s</div>' % ' · '.join(line2))
    h.append('<div style="color:#444">설계 <b>%s</b> · 시공 %s · 건축주 %s</div>'
             % (esc(rec.get('건축설계') or '미표시'), esc(rec.get('시공사') or '미표시'),
                esc(rec.get('건축주') or '미표시')))
    h.append('<div style="margin-top:6px"><b>무슨 일이 있었나</b> : %s</div>' % esc(res['한줄']))

    # ---- 산군 + 뉴스를 합쳐야 나오는 것 ----
    if cd.get('급한것'):
        h.append('<div style="margin-top:6px;background:#fff3f2;border:1px solid #f3c5c0;padding:6px">'
                 '<b>가장 급한 것</b> : %s</div>' % esc(cd['급한것']))
    if cd.get('역산'):
        h.append('<div style="margin-top:6px"><b>언제까지 무엇을</b> '
                 '<span style="color:#888;font-size:12px">(기사의 준공 %s 에서 거꾸로 — 추정입니다)</span>'
                 '<table style="border-collapse:collapse;font-size:13px;margin-top:3px">' % esc(cd.get('준공예정')))
        for x in cd['역산']:
            late = x['D'] < 0
            h.append('<tr><td style="padding:2px 8px 2px 0">%s</td>'
                     '<td style="padding:2px 8px 2px 0;font-weight:700;color:%s">%s</td>'
                     '<td style="padding:2px 0;color:#888">%s</td></tr>'
                     % (esc(x['무엇']), '#C0392B' if late else '#111', esc(x['언제까지']),
                        esc(('이미 %d일 지남' % -x['D']) if late else ('D-%d' % x['D']))
                        + ((' · ' + esc(x['근거'])) if x['근거'] else '')))
        if cd.get('외함의뢰'):
            h.append('<tr><td style="padding:2px 8px 2px 0">CB외함 작업의뢰서</td>'
                     '<td style="padding:2px 8px 2px 0;font-weight:700">%s</td>'
                     '<td style="padding:2px 0;color:#888">착공 기준 어림</td></tr>' % esc(cd['외함의뢰']))
        h.append('</table></div>')
    elif cd.get('외함의뢰'):
        h.append('<div style="margin-top:6px"><b>CB외함 작업의뢰서</b> : %s 까지 '
                 '<span style="color:#888;font-size:12px">(착공 기준 어림. 준공일이 기사에 없어 나머지는 못 냅니다)</span></div>'
                 % esc(cd['외함의뢰']))

    if res['기사']:
        h.append('<div style="margin-top:6px"><b>기사 %d건</b><ul style="margin:4px 0 0 18px;padding:0">'
                 % len(res['기사']))
        for a in res['기사'][:5]:
            h.append('<li style="margin:2px 0">%s <span style="color:#888">%s %s</span> %s</li>'
                     % (esc(a['제목']), esc(a['날짜']), esc(a['언론사']),
                        ('<a href="%s">보기</a>' % esc(a['링크'])) if a['링크'] else ''))
        h.append('</ul></div>')
    if g in (GRADE_GO, GRADE_ASK) and rec.get('소재지'):
        links = ' · '.join('<a href="%s">%s</a>' % (esc(u), esc(k)) for k, u in res.get('지도', {}).items())
        h.append('<div style="margin-top:4px">%s%s</div>'
                 % (('<b>가는 길</b> : ' + esc(res['소요']) + ' · ') if res.get('소요') else '<b>지도</b> : ', links))
    h.append('<div style="margin-top:6px;background:#fff;border:1px dashed #bbb;padding:6px">'
             '<b>다음 행동</b> : %s</div>' % esc(res['행동']))
    h.append('</div>')
    return ''.join(h)


def build_html(groups, src, err_n, cards=None, jsonname=''):
    """설정.ini [산군메일] 서식 = v2(기본) / v1. v1 은 아래 build_html_v1 그대로입니다."""
    cards = cards or []
    c0 = conf()
    style = opt(c0, '서식', 'v2') or 'v2'
    if style != 'v1':
        return SM.build(groups, cards, src, err_n, jsonname,
                        today().isoformat(), wide=num(c0, '메일에펼칠곳', 25),
                        top3=(SC.top3(cards) if cards else []),
                        routes=(SC.routes(cards) if cards else []),
                        basename=os.path.basename)
    return build_html_v1(groups, src, err_n, cards, jsonname)


def build_html_v1(groups, src, err_n, cards=None, jsonname=''):
    cards = cards or []
    n = {k: len(v) for k, v in groups.items()}
    h = ['<div style="font-family:맑은 고딕,system-ui;font-size:14px;line-height:1.5">']
    h.append('<h2 style="margin:0 0 2px">산군 현장 %s</h2>' % today().isoformat())

    # ── ① 오늘 이것만 (비서가 맨 위에 적어 드리는 것) ──
    tops = SC.top3(cards) if cards else []
    if tops:
        h.append('<div style="background:#fff8e6;border:2px solid #f0c36d;padding:10px 12px;margin:8px 0">')
        h.append('<div style="font-size:15px;font-weight:700;margin-bottom:4px">오늘 이것만 하십시오</div>')
        for t in tops:
            h.append('<div style="margin:3px 0">%s</div>' % esc(t))
        h.append('</div>')

    h.append('<div style="color:#666;font-size:12px">빨리 가보실 곳 <b>%d</b>곳 · 상황 물어보실 곳 <b>%d</b>곳 · '
             '아직 이른 곳 %d곳 · 흔적 없는 곳 %d곳 · 끝난 곳 %d곳 · 검색 못 한 곳 %d곳</div>'
             % (n.get(GRADE_GO, 0), n.get(GRADE_ASK, 0), n.get(GRADE_EARLY, 0),
                n.get(GRADE_NONE, 0), n.get(GRADE_DONE, 0), n.get(GRADE_ERR, 0)))

    # ── ② 하루 동선 (같은 시·도끼리) ──
    rts = SC.routes(cards) if cards else []
    if rts:
        h.append('<div style="margin:10px 0;padding:8px 12px;background:#eef4ff;border:1px solid #c6d8ff">')
        h.append('<b>한 번 나가실 때 같이 보실 곳</b>')
        for sido, xs in rts:
            names = ' / '.join('%s %s' % (c['등급'][:2], c['현장명']) for c in xs)
            h.append('<div style="margin:2px 0">· <b>%s</b> %d곳 — %s</div>' % (esc(sido), len(xs), esc(names)))
        h.append('</div>')

    # ── ③ 납기가 급한 순서 (합쳐야 나오는 값) ──
    due = [c for c in cards if c.get('급한것')]
    due.sort(key=lambda c: c.get('급한D', 9999))
    if due:
        h.append('<div style="margin:10px 0"><b>작업의뢰서 납기 — 급한 순서</b>'
                 '<table style="border-collapse:collapse;font-size:13px;margin-top:4px">')
        h.append('<tr style="color:#888"><td style="padding:2px 10px 2px 0">현장</td>'
                 '<td style="padding:2px 10px 2px 0">무엇을 언제까지</td></tr>')
        for c in due[:10]:
            h.append('<tr><td style="padding:2px 10px 2px 0">%s</td><td style="padding:2px 0">%s</td></tr>'
                     % (esc(c['현장명']), esc(c['급한것'])))
        h.append('</table><div style="color:#888;font-size:12px">'
                 '기사에 적힌 준공 예정에서 거꾸로 계산한 <b>추정</b>입니다. 현장에 확인하시고 쓰십시오.</div></div>')

    # 🔴🟠🟡 는 카드로 펼치고, ⚪⚫⛔ 는 한 줄 표로 접는다 (300곳이면 메일이 감당이 안 됩니다)
    wide = num(conf(), '메일에펼칠곳', 25)
    left = wide
    for g in (GRADE_GO, GRADE_ASK, GRADE_EARLY):
        xs = groups.get(g) or []
        if not xs:
            continue
        h.append('<h3 style="margin:18px 0 4px;border-bottom:2px solid #eee">%s (%d곳)</h3>'
                 % (esc(g), len(xs)))
        for rec, res in xs[:max(left, 0)]:
            h.append(card(rec, res))
        if len(xs) > max(left, 0):
            h.append('<div style="color:#888;font-size:12px">이 등급의 나머지 %d곳은 붙임 파일(CSV·앱 카드)에 있습니다.</div>'
                     % (len(xs) - max(left, 0)))
        left -= len(xs)

    for g in (GRADE_NONE, GRADE_DONE, GRADE_ERR):
        xs = groups.get(g) or []
        if not xs:
            continue
        h.append('<h3 style="margin:18px 0 4px;border-bottom:2px solid #eee">%s (%d곳)</h3>' % (esc(g), len(xs)))
        h.append('<table style="border-collapse:collapse;font-size:13px">')
        for rec, res in xs[:60]:
            cd = res.get('카드') or {}
            h.append('<tr><td style="padding:2px 10px 2px 0">%s</td>'
                     '<td style="padding:2px 10px 2px 0;color:#666">%s</td>'
                     '<td style="padding:2px 10px 2px 0;color:#666">%s</td>'
                     '<td style="padding:2px 0;color:#888">%s</td></tr>'
                     % (esc(rec.get('현장명')), esc(rec.get('소재지')),
                        esc(cd.get('객실') or ''), esc(cd.get('급한것') or res.get('한줄', '')[:40])))
        if len(xs) > 60:
            h.append('<tr><td colspan="4" style="color:#888">… 그 밖 %d곳은 붙임 파일에</td></tr>' % (len(xs) - 60))
        h.append('</table>')

    # ── ④ 앱으로 넣기 ──
    if jsonname:
        h.append('<div style="margin:16px 0;padding:10px 12px;background:#f2fbf6;border:1px solid #bfe3cf">'
                 '<b>앱에 넣으시려면</b><br>이 메일에 붙은 <b>%s</b> 를 저장하시고, '
                 '앱(한국마이크로닉 현장관리) &gt; <b>영업 파이프라인</b> &gt; <b>📡 산군 불러오기</b> 에서 그 파일을 고르십시오.<br>'
                 '이미 있는 현장은 건너뛰고 새 현장만 「첫 접촉」 칸에 들어갑니다. 금액·단계는 프로님이 정하십시오.</div>'
                 % esc(jsonname))

    h.append('<p style="color:#888;font-size:12px;margin-top:18px">'
             '산군 파일 : %s<br>'
             '이 메일은 PC 도구 50번이 산군 자료와 구글 뉴스 검색을 합쳐 만든 것입니다(클로드·Gemini 안 씀, 요금 0원).'
             '%s<br>알리미(뉴스모니터링) 메일과 구글AI 레이더 메일은 <b>따로</b> 갑니다. 이 메일에 섞지 않았습니다.<br>'
             '한 번 찾아본 현장은 며칠 뒤에 다시 찾습니다(설정.ini [산군메일] 다시찾기일수).<br>'
             '예상 금액·소요 시간이 안 보이면 설정.ini [역산] 실당단가 · [산군메일] kakao_key·출발지 · [소요시간] 표를 채워 주십시오.</p></div>'
             % (esc(os.path.basename(src)),
                (' 검색이 막힌 현장 %d곳은 따로 모아 두었습니다.' % err_n) if err_n else ''))
    return ''.join(h)


def send_mail(subject, html, files=()):
    """산군 전용 메일 한 통. 설정.ini [메일] 값을 그대로 씁니다(35번과 같은 계정, 다른 메일)."""
    c = conf()
    g = lambda k, d='': c.get('메일', k, fallback=d)
    to = mail_to(c)
    if not (g('user') and g('password') and to):
        print('[메일 설정 없음] 35번에서 보내는 계정·앱 비밀번호를 먼저 넣어 주십시오.')
        return False
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = g('user')
    msg['To'] = to
    alt = MIMEMultipart('alternative')
    alt.attach(MIMEText('HTML 메일입니다. 안 보이시면 PC 의 산군_흔적 한 장을 여십시오.', 'plain', 'utf-8'))
    alt.attach(MIMEText(html, 'html', 'utf-8'))
    msg.attach(alt)
    for f in files or ():
        try:
            if not (f and os.path.exists(f)):
                continue
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(io.open(f, 'rb').read())
            encoders.encode_base64(part)
            import email.header
            nm = email.header.Header(os.path.basename(f), 'utf-8').encode()
            part.add_header('Content-Disposition', 'attachment', filename=nm)
            msg.attach(part)
        except Exception as e:
            print('[첨부 실패] %s : %s' % (os.path.basename(f), e))
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

def run(src='', send=None, sleep=1.0, everything=False, direct=False):
    """src = 49번 CSV 하나 / everything=True 면 지금까지 본 현장 전부(주 1회 자동이 씀)
    메뉴(시작.py)에서 아무 인자 없이 부르면 번호 메뉴를 먼저 보여 준다."""
    if not (direct or src or everything or send is not None):
        return menu()
    title('50. 산군 현장 흔적 찾기 + 산군 전용 메일 (토큰 0)')
    c = ensure_ini()
    if everything:
        recs = targets_all()
        src = latest_49_csv() or '(지금까지 본 현장 전부)'
    else:
        src = src or latest_49_csv()
        if not src or not os.path.exists(src):
            print('49번(산군 관심현장 정리) 결과가 없습니다. 49번을 먼저 돌려 주십시오.')
            return
        recs = targets(src)
    if not recs:
        print('찾아볼 현장이 없습니다 : %s' % src)
        return
    read_body_on = opt(c, '본문읽기', '예') not in ('아니오', '아니요', 'n', 'N', '0')

    book = load_book()
    wait = again_days(c)
    cap = max(num(c, '한번에', 60), 1)

    def last_seen(r):
        return (book.get(key_of(r)) or ['', '', '', '', '', '', '', ''])[0]

    todo = [r for r in recs if days_since(last_seen(r)) >= wait]
    skip = len(recs) - len(todo)
    # ★최우선 먼저, 그 다음 오래 안 본 것부터 (300곳을 한 번에 두드리면 구글이 막습니다)
    todo.sort(key=lambda r: (0 if str(r.get('판정', '')).startswith('★') else 1,
                             -days_since(last_seen(r))))
    rest = 0
    if len(todo) > cap:
        rest = len(todo) - cap
        todo = todo[:cap]
    print('현장 %s곳 중 %s곳을 찾아봅니다 (%s곳은 %d일 안에 이미 찾아봄%s)'
          % (won(len(recs)), won(len(todo)), won(skip), wait,
             (' · 오늘 못 한 %s곳은 다음에' % won(rest)) if rest else ''))
    if rest:
        print('  한 번에 찾는 곳수는 설정.ini [산군메일] 한번에 = %d 입니다.' % cap)
    if not todo:
        print('새로 찾아볼 현장이 없어 메일을 보내지 않습니다.')
        return

    groups, body, cards, err_n = {}, [], [], 0
    for i, rec in enumerate(todo, 1):
        q, arts, err = search(rec, sleep=sleep)
        if err:
            err_n += 1
        bodies = {}
        if read_body_on and arts:
            # 제목에 공사 단계 낱말이 있는 기사만 본문을 읽는다 (많이 읽을수록 느려지므로 최대 2건)
            for a in [a for a in arts if any(w in a['제목'] for w in GO + ASK + DONE)][:2]:
                b = read_body(a['링크']) if a['링크'] else ''
                if b:
                    bodies[a['링크']] = b
        g, why, act = judge(rec, arts, err, bodies)
        res = {'등급': g, '한줄': why, '행동': act, '기사': arts,
               '본문': ' '.join(bodies.values())[:4000]}
        res['카드'] = SC.build(rec, res, c)
        if g in (GRADE_GO, GRADE_ASK):
            res['지도'] = map_links(rec.get('소재지', ''), opt(c, '출발지'))
            res['소요'] = travel(rec.get('소재지', ''), c)
        groups.setdefault(g, []).append((rec, res))
        cards.append(res['카드'])
        print('  [%d/%d] %s %s (기사 %d)' % (i, len(todo), g[:2], rec['현장명'][:24], len(arts)))
        a1 = arts[0] if arts else {}
        a2 = arts[1] if len(arts) > 1 else {}
        a3 = arts[2] if len(arts) > 2 else {}
        cd = res['카드']
        due = {x['무엇']: x['언제까지'] for x in cd['역산']}
        body.append([g, rec['현장명'], rec['소재지'], rec['단계'], rec['허가일'], rec['착공일'],
                     rec['연면적'], cd['객실'] or rec['객실추정'], rec['건축설계'], rec['시공사'], rec['건축주'],
                     len(arts), recent(arts), why, act,
                     cd['준공예정'], cd['급한것'], cd['외함의뢰'],
                     due.get('기구물 작업의뢰서', ''), due.get('속판(제어분전함) 작업의뢰서', ''),
                     cd['규모금액'],
                     a1.get('제목', ''), a2.get('제목', ''), a3.get('제목', '')])
        if g != GRADE_ERR:      # 검색이 막힌 현장은 대장에 안 적는다 -> 다음에 다시 찾는다
            book[key_of(rec)] = [today().isoformat(), key_of(rec), rec['현장명'], rec['소재지'],
                                 g.split(' ')[-1], len(arts), recent(arts), why[:80]]

    body.sort(key=lambda r: ORDER.get(r[0], 9))
    od = outdir(TOOL)
    cp = write_csv(os.path.join(od, '산군_흔적_%s.csv' % ymd6()), body, OUT_HEAD)

    # 앱(한국마이크로닉 현장관리)의 영업 파이프라인으로 그대로 들어가는 파일
    jp = os.path.join(od, '산군_앱카드_%s.json' % ymd6())
    try:
        io.open(jp, 'w', encoding='utf-8').write(SC.app_json(cards))
    except Exception as e:
        print('[앱 카드 실패] %s' % e)
        jp = ''
    html = build_html(groups, src, err_n, cards, os.path.basename(jp) if jp else '')
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
    if jp:
        print('앱 카드 : %s  (앱 > 영업 파이프라인 > 📡 산군 불러오기)' % jp)

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
        send_mail(subject, html, files=[f for f in (jp,) if f])
    log(TOOL, '%d곳 중 빨리%d 물어봄%d' % (len(todo), go_n, ask_n))
    try:
        open_file(hp)
    except Exception:
        pass


# ====================== 주 1회 자동 (작업 스케줄러) ======================

def launcher_path():
    # 2_KM도구\\산군메일.py  (시작.py 옆)
    return os.path.join(os.path.dirname(os.path.dirname(HERE)), '산군메일.py')


def write_launcher():
    code = '''# -*- coding: utf-8 -*-
"""KM 산군 메일 - 작업 스케줄러가 매주 부르는 파일. 직접 눌러도 됩니다. 클로드 안 씀."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '코드', 'km_tools'))
import common
common.AUTO = True
import t50_sangun_trace
t50_sangun_trace.auto()
'''
    p = launcher_path()
    io.open(p, 'w', encoding='utf-8').write(code)
    return p


def auto():
    """주 1회 : 다운로드 폴더의 최신 산군 파일로 49번(묻지 않음) → 지금까지 본 현장 전부를 7일 주기로 다시 찾아 메일"""
    common.AUTO = True
    try:
        import t49_sangun
        t49_sangun.ask = common.ask
        t49_sangun.run(chain=False)
    except Exception as e:
        print('[49번 건너뜀] %s' % e)
    run(send=True, everything=True)


def register():
    if os.name != 'nt':
        print('윈도우에서만 등록됩니다.')
        return False
    lp = write_launcher()
    py = sys.executable.replace('pythonw.exe', 'python.exe')
    cmd = ['schtasks', '/Create', '/F', '/SC', 'WEEKLY', '/D', WEEKLY_DAY, '/ST', WEEKLY_AT,
           '/TN', TASK, '/TR', '"%s" "%s"' % (py, lp)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print('등록했습니다 : 매주 월요일 %s  「%s」' % (WEEKLY_AT, TASK))
            print('  실행 파일 : %s' % lp)
            print('  산군 파일만 다운로드 폴더에 받아 두시면 됩니다. PC 가 꺼져 있으면 그 주는 안 갑니다.')
            return True
        print('[등록 실패] %s' % (r.stderr or r.stdout))
    except Exception as e:
        print('[등록 실패] %s' % e)
    return False


def unregister():
    if os.name != 'nt':
        return
    subprocess.run(['schtasks', '/Delete', '/F', '/TN', TASK], capture_output=True, text=True)
    print('해제했습니다 : %s' % TASK)


def menu():
    title('50. 산군 현장 흔적 찾기 + 산군 전용 메일 (토큰 0)')
    print(' 1) 지금 찾기 (49번 최신 결과)')
    print(' 2) 지금까지 본 현장 전부 다시 찾기')
    print(' 3) 주 1회 자동 등록 (매주 월요일 %s)' % WEEKLY_AT)
    print(' 4) 자동 해제')
    print(' 5) 설정 보기 (설정.ini [산군메일]·[소요시간])')
    ensure_ini()
    v = ask('번호 (엔터=1) > ', '1')
    if v == '2':
        run(everything=True, direct=True)
    elif v == '3':
        register()
    elif v == '4':
        unregister()
    elif v == '5':
        print(INI)
        try:
            open_file(INI)
        except Exception:
            pass
    else:
        run(direct=True)


if __name__ == '__main__':
    run()
    pause()

# -*- coding: utf-8 -*-
"""49. 앱 피드 — 회의록·대장을 읽어 「KM 손바닥」 앱이 먹는 JSON 을 만든다. 토큰 0.

프로님 (2026-09-19) : "코드는 회의록을 읽는데 비용이 0이지? 각 앱 내용이, 회의록에 생기면 즉시 앱에 반영해야 돼."

  읽는 곳 (있는 것만 읽는다)
    plaud\\26년\\1.현장\\{현장}\\회의록\\{날짜_제목}\\원문.txt      ← _현장비서 v10 결과
    _도구결과\\_대장\\확정사항.csv / 현장대장.csv / 견적발송.csv / 앞으로할것.csv
    _도구결과\\회의연결\\{날짜}\\{현장}_회의변경수량.csv            ← 40번 결과
  내는 것
    _도구결과\\앱피드\\{YYMMDD}\\앱피드.json   (+ 클립보드 복사 + 앱 열기)

  프로님 손 : ① 이 번호 누르기(또는 36번이 자동) ② 앱 설정에서 「PC에서 붙여넣기」 → 붙여넣기
  ※ 앱은 보안상 인터넷에서 직접 못 읽습니다. 그래서 붙여넣기 한 번이 남습니다.
"""
import os, re, io, csv, json, glob, datetime, subprocess, sys

APP_URL = 'https://claude.ai/artifact/Mg52NGzLvSegFJYXhuzHwH'
TOOL = '앱피드'

# ── 할 일 → 공정 단계 (앱의 QUESTS 와 같은 규칙. 고치면 양쪽 같이 고칠 것)
QMAP = [
    (r'타공도|외함 설치|설치 업체', '외함설치'),
    (r'CB\s*외함|외함|석고',        '외함'),
    (r'도어락|승인원|인증서|자재승인', '기구물제작'),
    (r'수량|계량기|감액|증감|견적|계약|네고', '계약'),
    (r'도면|설계|평면|Rev',         '설계'),
    (r'속판|배선도|모듈',            '속판'),
    (r'결선|강전|약전|커버',         '결선'),
    (r'벽지|빽커버|기구물 설치',      '설치'),
    (r'시운전|하자|계산서|수금|중도금', '시운전'),
]
# ── 회의에서 나온 말 → 열쇠
KEYMAP = [
    (r'외함.*납품|납품.*외함|CB.*납기',      '외함/외함납기',   '추정'),
    (r'옹벽|스터드|매립|석고',               '외함/외함공법',   '추정'),
    (r'계약(서)?.*완료|계약.*하기로|발주서',   '계약/계약완료',   '진행중'),
    (r'수량표|수량.*확정|물량',              '계약/수량표',     '진행중'),
    (r'타공도|타공',                        '외함설치/타공도', '진행중'),
    (r'배선도|모듈.*구성',                   '속판/배선도',     '진행중'),
    (r'벽지|페인트.*완료',                   '기구물제작/벽지예정', '추정'),
    (r'색상|마감.*색',                      '기구물제작/마감',  '추정'),
    (r'강전.*결선|전기.*결선',               '결선/강전일정',   '추정'),
    (r'시운전',                             '시운전/시운전완료', '추정'),
    (r'준공',                               '',                ''),
]

def h36(s):
    v = 5381
    for c in s: v = ((v << 5) + v + ord(c)) & 0xffffffff
    d = '0123456789abcdefghijklmnopqrstuvwxyz'; o = ''
    while v: o = d[v % 36] + o; v //= 36
    return o or '0'

def sid(name): return 's_' + h36(re.sub(r'\s', '', name))

def rd(p):
    try: b = open(p, 'rb').read()
    except Exception: return ''
    for e in ('utf-8-sig', 'cp949', 'utf-8'):
        try: return b.decode(e)
        except Exception: pass
    return b.decode('utf-8', 'replace')

def quest_of(t):
    for pat, q in QMAP:
        if re.search(pat, t): return q
    return ''

def run(base=None, quiet=False):
    """base = 3_공통사용 폴더. 없으면 common 이 찾아 준다."""
    if base is None:
        try:
            import common
            base = common.cfg('common')
        except Exception:
            base = os.getcwd()
    today = datetime.date.today()
    YMD = today.strftime('%y%m%d')
    out = {'ts': datetime.datetime.now().isoformat(timespec='seconds'),
           'from': 'PC 도구 49번 앱피드', 'sites': {}, 'items': [], 'drops': [], 'src': {}}

    def site(name):
        name = name.strip()
        if name not in out['sites']:
            out['sites'][name] = {'id': sid(name), 'name': name, 'req': {}, 'facts': [],
                                  'meetings': [], 'lastMeeting': ''}
        return out['sites'][name]

    # 1) 회의록 원문 (토큰 0 — 파이썬이 글자만 읽는다)
    pats = [os.path.join(base, 'plaud', '**', '원문.txt'),
            os.path.join(base, '산출물', '회의록', '**', '원문.txt'),
            os.path.join(base, '..', '_현장비서', '**', '원문.txt')]
    seen = 0
    for pat in pats:
        for f in glob.glob(pat, recursive=True):
            txt = rd(f)
            if not txt: continue
            seen += 1
            m = re.search(r'■\s*현장\s*[:：]?\s*(.+)', txt)
            nm = (m.group(1).strip() if m else '')
            if not nm:
                d = os.path.basename(os.path.dirname(os.path.dirname(f)))
                nm = d if d and d not in ('회의록', '1.현장') else ''
            if not nm: continue
            s = site(nm)
            mt = os.path.basename(os.path.dirname(f))
            dm = re.match(r'(\d{6})', mt)
            mdate = ('20%s-%s-%s' % (dm.group(1)[:2], dm.group(1)[2:4], dm.group(1)[4:])) if dm else ''
            s['meetings'].append({'title': mt, 'date': mdate, 'file': f})
            if mdate > s['lastMeeting']: s['lastMeeting'] = mdate
            # 수량·규격 변경
            blk = re.search(r'■\s*수량[·・]?\s*규격\s*변경(.*?)(?=\n■|\Z)', txt, re.S)
            if blk:
                for ln in blk.group(1).split('\n'):
                    ln = ln.strip(' -·•\t')
                    if len(ln) < 3: continue
                    for pat2, key, st in KEYMAP:
                        if key and re.search(pat2, ln):
                            s['req'].setdefault(key, {'state': st, 'value': ln[:90],
                                'basis': '%s 회의 (%s)' % (mdate or mt, os.path.basename(os.path.dirname(f))),
                                'date': mdate or str(today), 'from': 'PC 49 회의록'})
                            break
            # 할 일
            blk = re.search(r'■\s*할\s*일(.*?)(?=\n■|\Z)', txt, re.S)
            if blk:
                for ln in blk.group(1).split('\n'):
                    ln = ln.strip(' -·•\t')
                    if len(ln) < 4: continue
                    out['items'].append({'id': 'T-' + h36(nm + ln), 'kind': 'ask', 'site': nm,
                        'text': ln[:120], 'when': '', 'quest': quest_of(ln), 'status': 'open',
                        'memo': '%s 회의' % (mdate or mt), 'from': 'PC 49 회의록'})
            # 본문 전체에서 날짜·공정 말
            for pat2, key, st in KEYMAP:
                if not key or key in s['req']: continue
                mm = re.search(pat2 + r'[^\n]{0,60}', txt)
                if mm:
                    s['req'][key] = {'state': st, 'value': mm.group(0)[:90],
                        'basis': '%s 회의록 본문' % (mdate or mt), 'date': mdate or str(today),
                        'from': 'PC 49 회의록'}
    out['src']['회의록'] = {'date': str(today), 'count': seen}

    # 2) 확정 대장
    led = os.path.join(base, '산출물', '도구결과', '_대장')
    if not os.path.isdir(led): led = os.path.join(base, '_도구결과', '_대장')
    f = os.path.join(led, '확정사항.csv')
    n = 0
    if os.path.exists(f):
        for r in csv.DictReader(io.StringIO(rd(f))):
            nm = (r.get('현장') or '').strip()
            if not nm: continue
            s = site(nm); n += 1
            s['facts'].append({'date': r.get('일자', ''), 'item': r.get('항목', ''),
                               'value': r.get('값', ''), 'basis': r.get('근거', '')})
    out['src']['확정 대장'] = {'date': str(today), 'count': n}

    # 3) 앞으로 할 것
    f = os.path.join(led, '앞으로할것.csv'); n = 0
    if os.path.exists(f):
        for r in csv.DictReader(io.StringIO(rd(f))):
            nm = (r.get('현장') or '').strip(); t = (r.get('할 일') or '').strip()
            if not nm or not t: continue
            n += 1
            out['items'].append({'id': 'T-' + h36(nm + t),
                'kind': 'todo' if (r.get('등급') or '') == '확정' else 'ask',
                'site': nm, 'text': t[:120], 'when': (r.get('때') or '').strip(),
                'to': (r.get('누가') or '').strip(), 'memo': (r.get('왜') or '').strip(),
                'quest': quest_of(t + ' ' + (r.get('왜') or '')),
                'status': 'done' if (r.get('상태') or '') == '완료' else 'open', 'from': 'PC 49 대장'})
    out['src']['앞으로 할 것'] = {'date': str(today), 'count': n}

    # 4) 현장대장 (준공일·객실수)
    f = os.path.join(led, '현장대장.csv')
    if os.path.exists(f):
        for r in csv.DictReader(io.StringIO(rd(f))):
            nm = (r.get('현장') or '').strip()
            if not nm or nm.startswith('예)'): continue
            s = site(nm)
            due = (r.get('준공일(YYYY-MM-DD)') or r.get('준공일') or '').strip()
            if due: s['due'] = due
            rooms = (r.get('객실수') or '').strip()
            if rooms: s['rooms'] = rooms

    # 같은 할 일이 회의록·대장 양쪽에서 나오면 하나로 (대장 쪽이 이긴다 — 때·누가·등급이 있다)
    merged = {}
    for it in out['items']:
        k = it['id']
        if k in merged:
            a = merged[k]
            for f in ('when', 'to', 'memo', 'quest'):
                if it.get(f) and not a.get(f): a[f] = it[f]
            if it.get('kind') == 'todo': a['kind'] = 'todo'
            if it.get('status') == 'done': a['status'] = 'done'
        else:
            merged[k] = it
    out['items'] = list(merged.values())

    # 5) 저장 + 클립보드 + 앱 열기
    d = os.path.join(base, '산출물', '도구결과', '앱피드', YMD)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, '앱피드.json')
    txt = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(path, 'w', encoding='utf-8').write(txt)
    ok = False
    try:
        if sys.platform.startswith('win'):
            subprocess.run('clip', input=txt.encode('utf-16le'), check=True); ok = True
    except Exception: pass
    if not quiet:
        print('앱피드 : 현장 %d곳 · 할 일 %d건 · 회의록 %d건' % (len(out['sites']), len(out['items']), seen))
        print('파일 :', path)
        print('클립보드 복사 :', '됨 — 앱 설정 「PC에서 붙여넣기」 에 그대로 붙이십시오' if ok else '안 됨 — 위 파일을 열어 전체 복사하십시오')
        if ok:
            try: os.startfile(APP_URL)
            except Exception: print('앱 :', APP_URL)
    return {'path': path, 'sites': len(out['sites']), 'items': len(out['items']), 'meetings': seen, 'clip': ok}

if __name__ == '__main__':
    run()

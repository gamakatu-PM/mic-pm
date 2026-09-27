# -*- coding: utf-8 -*-
"""35. 아침 메일 - 아침 한 장을 매일 내 메일로 보낸다. 하루 두 번. 토큰 0.

프로님 (2026-09-18) : "매일 파이썬이 아침 7시에 보내고, 내가 7시 전에 어제 PLAUD 회의록을 못 넣었으면
7시 것은 회의록 빼고 할 수 있는 것만 보내. 그 후 9시에 출근해서 회의록 넣고 시작을 누르면
그때 어제 회의록을 포함해서 다시 보내."

  ① 07:00 (작업 스케줄러)  : 회의록이 없어도 나머지(오늘 할 것·찾아갈 곳·수금·도면·점검)를 전부 보낸다
                             어제 회의록이 아직 안 들어왔으면 제목에 「어제 회의록 아직 안 들어옴」
  ② 회의록을 넣고 36번을 누르면 : 7시 이후 새로 들어온 회의가 있으면 **그때 한 번 더** 보낸다
                             제목에 「어제 회의록 포함 · 새 회의 n건」
  같은 날 같은 편은 두 번 가지 않는다 (_도구결과\\_대장\\메일발송.csv 로 기록)


처음 한 번
  설정.ini 의 [메일] 에 보내는 계정·앱 비밀번호·받는 주소를 넣는다 (35번이 물어봅니다)
  지메일이면 「구글 계정 > 보안 > 앱 비밀번호」 에서 16자리를 만듭니다 (일반 비밀번호는 안 됩니다)
  35번 안의 「등록」 을 누르면 윈도우 작업 스케줄러에 매일 05:00 이 등록됩니다

그 뒤
  05:00 에 33번(현황판) 을 만들고 그 HTML 을 본문으로 보냅니다. 클로드는 안 씁니다.
  PC 가 꺼져 있으면 그날은 안 갑니다 (켜면 다음날부터).
"""
import os, sys, ssl, smtplib, subprocess, configparser, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from common import *
import t33_dashboard as DB

TOOL = '아침메일'
TASK = 'KM_아침메일_0700'
SEND_AT = '07:00'      # 프로님 지정 2026-09-18
MAIL_HEAD = ['날짜', '구분', '회의건수', '보낸시각', '제목', '결과']

def conf():
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        c.read(INI, encoding='utf-8')
    if not c.has_section('메일'):
        c.add_section('메일')
    return c

def save(c):
    import io as _io
    with _io.open(INI, 'w', encoding='utf-8') as fp:
        c.write(fp)

def setup():
    c = conf()
    g = lambda k, d='': c.get('메일', k, fallback=d)
    print('보내는 계정과 받는 주소를 넣습니다. 엔터면 지금 값을 둡니다.')
    smtp = ask('SMTP 서버 [%s] > ' % (g('smtp') or 'smtp.gmail.com'), g('smtp') or 'smtp.gmail.com')
    port = ask('포트 [%s] > ' % (g('port') or '587'), g('port') or '587')
    user = ask('보내는 메일 주소 [%s] > ' % g('user'), g('user'))
    pw = ask('앱 비밀번호 (지메일 16자리) [%s] > ' % ('*' * 8 if g('password') else ''), g('password'))
    sp = ask('나눠 보낼까요? (예 = ①답해주십시오 ②오늘할것 ③회의록 세 통 / 아니오 = 한 통) [%s] > ' % (g('나눠보내기') or '예'), g('나눠보내기') or '예')
    c.set('메일', '나눠보내기', sp)
    to = ask('받는 메일 주소 [%s] > ' % (g('to') or 'bsy@micronic.co.kr'), g('to') or 'bsy@micronic.co.kr')   # 프로님 지정 2026-09-17
    for k, v in (('smtp', smtp), ('port', port), ('user', user), ('password', pw), ('to', to)):
        c.set('메일', k, v)
    save(c)
    print('저장했습니다 : %s' % INI)

def maillog_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '메일발송.csv')

def _mail_rows():
    import io as _io, csv as _csv
    p = maillog_path()
    if not os.path.exists(p):
        return []
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with _io.open(p, 'r', encoding=enc, newline='') as fp:
                rows = list(_csv.reader(fp))
            break
        except Exception:
            rows = []
    out = []
    for r in rows[1:]:
        r = (r + [''] * 6)[:6]
        if r[0].strip():
            out.append(dict(zip(MAIL_HEAD, [c.strip() for c in r])))
    return out

def sent_today(kind=None, day=None):
    """오늘 보낸 기록 (kind 를 주면 그 편만). 없으면 None"""
    d = (day or today()).isoformat()
    for r in _mail_rows():
        if r['날짜'] == d and (kind is None or r['구분'] == kind) and r['결과'] == '성공':
            return r
    return None

def mark_sent(kind, n_meeting, subject, ok=True):
    import datetime as _dt
    rows = _mail_rows()
    new = [today().isoformat(), kind, str(n_meeting), _dt.datetime.now().strftime('%H:%M'), subject, '성공' if ok else '실패']
    write_csv(maillog_path(), [new] + [[r[k] for k in MAIL_HEAD] for r in rows], MAIL_HEAD)
    return new

def meeting_count():
    """지금 회의록 폴더에 들어와 있는 회의 건수 (7시 이후 늘었는지 세는 기준)"""
    try:
        import t42_morning as MO
        return len(MO.meetings())
    except Exception:
        return 0

ATTACH = []       # 이번 발송에 붙일 파일 (미확인 회의록 요약 엑셀 등)
SUBJ = ['']       # 제목 꼬리 (미확인 n건)

def _morning_or(top):
    """아침 한 장(42)이 만들어지면 현황판 대신 그것을 보낸다. 미확인 회의록 요약 엑셀도 첨부한다."""
    del ATTACH[:]; SUBJ[0] = ''
    try:
        import t42_morning as MO
        am, _ = MO.build(quiet=True)
        try:
            import t44_meetingcheck as MC
            xs = MC.unchecked()
            if xs:
                x, c = MC.build_xlsx(xs, quiet=True)
                if x:
                    ATTACH.append(x)
                old = len([m for m in xs if m.get('gap') and m['gap'] >= 3])
                SUBJ[0] = ' · 미확인 회의 %d건%s' % (len(xs), ('(3일↑ %d)' % old) if old else '')
        except Exception:
            pass
        try:
            import t46_plan as PL
            ps = PL.rows()
            if ps:
                x, c = PL.build_xlsx(ps, quiet=True)
                if x:
                    ATTACH.append(x)
                SUBJ[0] += ' · 오늘 할 것 %d건' % len([d for d in ps if d['level'] == 'red'])
                n_off = len([d for d in ps if d['만들기']])
                if n_off:
                    SUBJ[0] += ' · 제가 만들까요 %d' % n_off
        except Exception:
            pass
        try:
            import t47_visit as VS
            vs = [d for d in VS.rows() if d['need']]
            if vs:
                x, c = VS.build_xlsx(quiet=True)
                if x:
                    ATTACH.append(x)
                SUBJ[0] += ' · 찾아갈 곳 %d곳' % len(vs)
        except Exception:
            pass
        if am and os.path.exists(am):
            return am
    except Exception:
        pass
    return top

def send(html_path, subject=None, files=()):
    c = conf()
    g = lambda k, d='': c.get('메일', k, fallback=d)
    if not (g('user') and g('password') and g('to')):
        print('[설정 없음] 35번에서 먼저 설정을 하십시오.')
        return False
    body = read_text(html_path)
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject or '[KM] 아침 한 장 %s' % today().isoformat()
    msg['From'] = g('user'); msg['To'] = g('to')
    alt = MIMEMultipart('alternative')
    alt.attach(MIMEText('HTML 을 볼 수 없는 메일앱입니다. 첨부 엑셀이나 PC 의 _아침한장.html 을 여십시오.', 'plain', 'utf-8'))
    alt.attach(MIMEText(body, 'html', 'utf-8'))
    msg.attach(alt)
    for f in files or ():
        try:
            if not (f and os.path.exists(f)):
                continue
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(f, 'rb').read())
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
            s.sendmail(g('user'), [g('to')], msg.as_string())
        print('보냈습니다 -> %s' % g('to'))
        return True
    except Exception as e:
        print('[보내기 실패] %s' % e)
        print('  지메일이면 2단계 인증 + 앱 비밀번호가 필요합니다. 회사망이 587 을 막았을 수도 있습니다.')
        return False

def launcher_path():
    # 2_KM도구\아침메일.py  (시작.py 옆)
    return os.path.join(os.path.dirname(os.path.dirname(HERE)), '아침메일.py')

def write_launcher():
    p = launcher_path()
    code = '''# -*- coding: utf-8 -*-
"""KM 아침 메일 - 작업 스케줄러가 05:00 에 부르는 파일. 직접 눌러도 됩니다."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '코드', 'km_tools')
sys.path.insert(0, TOOLS)
import common
common.AUTO = True
import t35_morningmail
t35_morningmail.auto()
'''
    import io as _io
    _io.open(p, 'w', encoding='utf-8').write(code)
    return p

def register():
    if os.name != 'nt':
        print('윈도우에서만 등록됩니다.'); return False
    lp = write_launcher()
    py = sys.executable.replace('pythonw.exe', 'python.exe')
    tr = '"%s" "%s"' % (py, lp)
    cmd = ['schtasks', '/Create', '/F', '/SC', 'DAILY', '/ST', SEND_AT, '/TN', TASK, '/TR', tr]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print('등록했습니다 : 매일 %s  「%s」' % (SEND_AT, TASK))
            print('  실행 파일 : %s' % lp)
            print('  PC 가 꺼져 있으면 그날은 안 갑니다.')
            return True
        print('[등록 실패] %s' % (r.stderr or r.stdout))
    except Exception as e:
        print('[등록 실패] %s' % e)
    return False

def unregister():
    if os.name != 'nt':
        return
    subprocess.run(['schtasks', '/Delete', '/F', '/TN', TASK], capture_output=True, text=True)
    print('해제했습니다.')

def _send_now(kind, head=''):
    """아침 한 장을 만들어 지금 보낸다. kind = '아침'(07:00) / '회의록'(회의록 들어온 뒤)"""
    n = meeting_count()
    top, mdp, blocks = DB.build(quiet=True)
    top = _morning_or(top)
    subj = '[KM] 아침 한 장 %s%s%s' % (today().isoformat(), head, SUBJ[0])
    ok = send(top, subject=subj, files=ATTACH)
    mark_sent(kind, n, subj, ok)
    log(TOOL, '%s %s (회의 %d건)' % (kind, '성공' if ok else '실패', n))
    return ok

def auto():
    """작업 스케줄러가 07:00 에 부르는 것.
    회의록이 아직 안 들어왔어도 나머지는 전부 보낸다 (프로님 지시 2026-09-18)."""
    import datetime as _dt
    n_new = 0
    try:
        import t44_meetingcheck as MC
        y = today() - _dt.timedelta(days=1)
        n_new = len([m for m in MC.unchecked() if m.get('day') and m['day'] >= y])
    except Exception:
        pass
    head = '' if n_new else ' · 어제 회의록 아직 안 들어옴'
    if split_on():
        return bool(send_parts(kind_meeting=bool(n_new)))
    return _send_now('아침', head)

def after_meeting(quiet=True):
    """36번(오늘 한 방에) 끝에서 부른다.
    07:00 발송 뒤에 회의록이 새로 들어왔으면 **그때 한 번 더** 보낸다. 같은 날 두 번은 안 보낸다."""
    try:
        if sent_today('회의록'):
            return False                      # 오늘 이미 회의록 편을 보냈다
        first = sent_today('아침')
        n = meeting_count()
        if first:
            try:
                n0 = int(first['회의건수'] or 0)
            except Exception:
                n0 = 0
            if n <= n0:
                return False                  # 7시 이후 새로 들어온 회의가 없다
            add = n - n0
        else:
            if not n:
                return False                  # 7시 메일도 안 갔고 회의록도 없다
            add = n
        if split_on():
            ok = bool(send_parts(kind_meeting=True))
        else:
            ok = _send_now('회의록', ' · 어제 회의록 포함(새 회의 %d건)' % add)
        if not quiet:
            print('회의록이 %d건 새로 들어와 메일을 다시 보냈습니다.' % add)
        return ok
    except Exception as e:
        if not quiet:
            print('[회의록 메일 실패] %s' % e)
        return False

def run():
    title('35. 아침 메일   (07:00 에 한 번 + 회의록 들어오면 한 번 더. 토큰 0)')
    c = conf()
    has = bool(c.get('메일', 'user', fallback=''))
    print('설정 : %s' % ('있음 (%s -> %s)' % (c.get('메일', 'user'), c.get('메일', 'to', fallback='')) if has else '없음'))
    print('')
    print(' 1. 설정 (계정·앱 비밀번호·받는 주소)')
    print(' 2. 지금 한 번 보내기 (시험)')
    print(' 3. 매일 %s 등록 (윈도우 작업 스케줄러)' % SEND_AT)
    print(' 4. 등록 해제')
    r = sent_today('아침'); r2 = sent_today('회의록')
    print(' 오늘 발송 : 아침 %s / 회의록 %s' % (('%s 보냄(회의 %s건)' % (r['보낸시각'], r['회의건수'])) if r else '아직',
                                             ('%s 보냄' % r2['보낸시각']) if r2 else '아직'))
    s = ask('번호 > ', '2' if has else '1')
    if s == '1':
        setup()
    elif s == '2':
        _send_now('시험', ' · 시험 발송')
    elif s == '3':
        register()
    elif s == '4':
        unregister()

if __name__ == '__main__':
    run(); pause()


# ---------------- 나눠 보내기 (v45) ----------------
# 프로님 (2026-09-18) : "아침에 메일을 꼭 한 메일에 몰아서 안 해도 돼.
#   따로따로 나누어서 니가 나중에 헛짓을 안 하게 하는 방향으로 해야 돼."
# 헛짓이 나는 지점은 「확인 안 된 제안」 과 「확정된 것」 이 한 덩어리로 섞이는 것이다.
# 그래서 성격으로 가른다 — ① 답이 필요한 것 ② 보기만 하면 되는 것 ③ 어제 회의록.
# 회신도 ① 번 메일에만 오므로 어느 줄에 대한 답인지 헷갈리지 않는다.

PARTS = (('제안', '① 답해 주십시오'), ('확정', '② 오늘 할 것 (답 안 하셔도 됩니다)'), ('회의록', '③ 어제 회의록'))
OLD_DAYS = 3      # 제안을 이만큼 답 없이 두면 「묵은 제안」 으로 맨 위에 따로 모은다

def split_on():
    c = conf()
    v = c.get('메일', '나눠보내기', fallback='예').strip()
    return not v.startswith(('아니', 'n', 'N', '0'))

def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _part_rows(kind):
    """메일 한 통에 들어갈 줄 + 제목 꼬리"""
    import facts, datetime
    rows, tail = [], ''
    if kind == '제안':
        try:
            import t46_plan as PL
            xs = [d for d in PL.rows() if d['등급'] != '확정']
        except Exception:
            xs = []
        old = []
        for d in xs:
            gap = None
            try:
                y, m, dd = [int(x) for x in d['일자'].split('-')]
                gap = (today() - datetime.date(y, m, dd)).days
            except Exception:
                pass
            (old if (gap is not None and gap >= OLD_DAYS) else rows).append((d, gap))
        rows = [(d, g, '묵은 제안 %d일째' % g) for d, g in old] + [(d, g, '') for d, g in rows]
        tail = ' · 제안 %d건%s' % (len(rows), (' (3일↑ %d)' % len(old)) if old else '')
    elif kind == '확정':
        try:
            import t46_plan as PL
            rows = [(d, None, '') for d in PL.rows() if d['등급'] == '확정']
        except Exception:
            rows = []
        tail = ' · 오늘 할 것 %d건' % len(rows)
    return rows, tail

def _part_html(kind, title_):
    import facts
    rows, tail = _part_rows(kind)
    to = ''
    try:
        import t42_morning as MO
        to = MO.mail_to()
    except Exception:
        pass
    H = ['<div style="font-family:\'맑은 고딕\',sans-serif;font-size:14px;line-height:1.6;color:#111;max-width:700px">',
         '<h2 style="margin:0 0 2px;font-size:18px">%s</h2>' % _esc(title_),
         '<p style="margin:0 0 12px;color:#666;font-size:12px">%s · %d건</p>' % (today().isoformat(), len(rows))]
    if kind == '제안':
        H.append('<div style="background:#f4f8f5;border:1px dashed #b8d8c6;border-radius:8px;padding:9px 12px;margin:0 0 12px;font-size:12.5px">'
                 '<b>이 메일에 그대로 회신해 주시면 반영됩니다.</b> 줄 앞 번호만 맞으면 됩니다 (번호는 끝날 때까지 안 바뀝니다)<br>'
                 '<span style="font-family:monospace">3 진행중 · 3 완료 · 3 맞아 · 3 아니야 1개 층 선납으로 · 3 만들어줘 · 3 취소 · 3 미뤄 22일</span><br>'
                 '<b>답을 못 받은 줄은 제가 진행하지 않습니다.</b> 3일이 지나면 맨 위 「묵은 제안」 으로 올려 다시 여쭙니다.</div>')
    if not rows:
        H.append('<p style="color:#666">없습니다.</p>')
    for d, gap, flag in rows:
        code = (d.get('코드') or '').replace('KM-', '')
        btn = ''
        try:
            import t42_morning as MO
            btn = MO.reply_links(code, to) if kind == '제안' else ''
        except Exception:
            pass
        H.append('<div style="border-top:1px solid #f0f1f3;padding:7px 0">'
                 '%s<b style="color:#2A6099">%s</b> %s · %s%s'
                 '<div style="color:#888;font-size:12px">%s%s</div>%s</div>'
                 % (('<span style="background:#C0392B;color:#fff;font-size:11px;padding:1px 7px;border-radius:99px;margin-right:6px">%s</span>' % _esc(flag)) if flag else '',
                    _esc(code), _esc(d.get('현장', '')), _esc(d.get('할일', '')),
                    (' <b style="color:#6B4FA8">· 제가 %s 만들까요?</b>' % _esc(d['만들기'])) if d.get('만들기') else '',
                    _esc(d.get('때', '')), (' · ' + _esc(d.get('왜', ''))) if d.get('왜') else '',
                    ('<div style="margin-top:4px">%s</div>' % btn) if btn else ''))
    # 못 알아들은 답은 ① 번 메일 맨 아래에 다시 여쭙는다
    if kind == '제안':
        try:
            bad = facts.talk_load(days=7, state='못알아들음')
        except Exception:
            bad = []
        if bad:
            H.append('<div style="background:#fff6f5;border:1px solid #f2d9d5;border-radius:8px;padding:9px 12px;margin-top:12px;font-size:12.5px">'
                     '<b style="color:#C0392B">제가 못 알아들은 답 %d건 — 한 줄만 다시 주십시오</b><ul style="margin:4px 0 0;padding-left:18px">' % len(bad))
            for x in bad:
                H.append('<li>%s 「%s」</li>' % (_esc(x['코드']), _esc(x['프로님 말'])))
            H.append('</ul></div>')
    H.append('</div>')
    return '\n'.join(H), tail, len(rows)

def send_parts(kind_meeting=False):
    """성격별로 나눠 보낸다. 보낸 편 목록 돌려줌"""
    sent = []
    for kind, title_ in PARTS:
        if kind == '회의록':
            if not kind_meeting:
                continue
            top, mdp, blocks = DB.build(quiet=True)
            top = _morning_or(top)            # 회의록 편은 아침 한 장 전체를 그대로
            subj = '[KM] ③ 어제 회의록 %s%s' % (today().isoformat(), SUBJ[0])
            ok = send(top, subject=subj, files=ATTACH)
            mark_sent('회의록', meeting_count(), subj, ok)
            sent.append(('회의록', ok)); continue
        html, tail, n = _part_html(kind, title_)
        if kind == '확정' and not n:
            continue
        p = os.path.join(outdir(TOOL), '메일_%s_%s.html' % (kind, ymd6()))
        import io as _io
        _io.open(p, 'w', encoding='utf-8').write(html)
        subj = '[KM] %s %s%s' % (title_.split(' ')[0] + ' ' + title_.split(' ', 1)[1], today().isoformat(), tail)
        ok = send(p, subject=subj)
        mark_sent(kind, meeting_count(), subj, ok)
        sent.append((kind, ok))
    log(TOOL, '나눠보내기 %s' % sent)
    return sent

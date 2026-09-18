# -*- coding: utf-8 -*-
"""35. 아침 메일 - 현황판을 매일 아침 내 메일로 보낸다 (PC가 켜져 있으면 5시에 저절로). 토큰 0.

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
TASK = 'KM_아침메일_0500'

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
    to = ask('받는 메일 주소 [%s] > ' % (g('to') or 'bsy@micronic.co.kr'), g('to') or 'bsy@micronic.co.kr')   # 프로님 지정 2026-09-17
    for k, v in (('smtp', smtp), ('port', port), ('user', user), ('password', pw), ('to', to)):
        c.set('메일', k, v)
    save(c)
    print('저장했습니다 : %s' % INI)

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
    cmd = ['schtasks', '/Create', '/F', '/SC', 'DAILY', '/ST', '05:00', '/TN', TASK, '/TR', tr]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print('등록했습니다 : 매일 05:00  「%s」' % TASK)
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

def auto():
    """스케줄러가 부르는 것 : 현황판 만들고 보내기"""
    top, mdp, blocks = DB.build(quiet=True)
    top = _morning_or(top)
    ok = send(top, subject='[KM] 아침 한 장 %s%s' % (today().isoformat(), SUBJ[0]), files=ATTACH)
    log(TOOL, '자동 %s' % ('성공' if ok else '실패'))

def run():
    title('35. 아침 메일   (현황판을 05:00 에 내 메일로. 토큰 0)')
    c = conf()
    has = bool(c.get('메일', 'user', fallback=''))
    print('설정 : %s' % ('있음 (%s -> %s)' % (c.get('메일', 'user'), c.get('메일', 'to', fallback='')) if has else '없음'))
    print('')
    print(' 1. 설정 (계정·앱 비밀번호·받는 주소)')
    print(' 2. 지금 한 번 보내기 (시험)')
    print(' 3. 매일 05:00 등록 (윈도우 작업 스케줄러)')
    print(' 4. 등록 해제')
    s = ask('번호 > ', '2' if has else '1')
    if s == '1':
        setup()
    elif s == '2':
        top, mdp, blocks = DB.build(quiet=True)
        top = _morning_or(top)
        send(top, subject='[KM] 아침 한 장 %s%s' % (today().isoformat(), SUBJ[0]), files=ATTACH)
    elif s == '3':
        register()
    elif s == '4':
        unregister()

if __name__ == '__main__':
    run(); pause()

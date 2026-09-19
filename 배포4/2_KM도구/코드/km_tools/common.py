# -*- coding: utf-8 -*-
"""KM 현장비서 도구모음 - 공통 유틸
한국마이크로닉(주) 배성윤 프로 전용. 토큰 0(로컬 파이썬)으로 도는 도구들의 공용 부품.
"""
import os, io, re, sys, configparser, datetime

# ---- 콘솔 한글 ----
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

VERSION = 'v47'
VERSION_DATE = '2026-09-17'

HERE = os.path.dirname(os.path.abspath(__file__))
INI = os.path.join(HERE, '설정.ini')

DEFAULTS = {
    'base':    r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더',
    'plaud':   r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\plaud\26년',
    'biseo':   r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\_현장비서',
    'template':r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\_원틀',
    'out':     r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\_도구결과',
    'handover':r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\KM_인수인계함',
    'drawing': r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\3_공통사용\도면',
    'price':   r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\3_공통사용\단가장',
}

# 폴더 이름이 바뀌어도 찾아내기 위한 후보들 (번호를 붙이셔도 됩니다)
ALIAS = {
    'plaud':    ('plaud', '회의록', '회의록결과'),
    'biseo':    ('_현장비서', '1_현장비서', '현장비서'),
    'template': ('_원틀', '4_원틀', '원틀'),
    'out':      ('_도구결과', '도구결과'),
    'handover': ('KM_인수인계함', '3_인수인계함', '인수인계함'),
    'drawing':  ('도면', '_도면', '도면검토'),
    'price':    ('단가장', '_단가장', '단가'),
}
# 공통 폴더 아래에 한 겹 더 들어가는 경우도 훑는다 (3_공통사용\산출물\회의록 등)
NEST = ('3_공통사용', '공통사용', '3_공통', '산출물', '5_산출물')

def _plain(s):
    return str(s).lstrip('0123456789_ .').strip()

def _look_in(folder, names):
    """folder 바로 아래에서 이름 후보와 맞는 폴더를 찾는다(번호 접두어 무시)."""
    if not os.path.isdir(folder):
        return None
    try:
        entries = os.listdir(folder)
    except Exception:
        return None
    for name in names:
        p = os.path.join(folder, name)
        if os.path.isdir(p):
            return p
    want = {_plain(n) for n in names}
    for d in entries:
        if os.path.isdir(os.path.join(folder, d)) and _plain(d) in want:
            return os.path.join(folder, d)
    return None

def _find_by_alias(key, depth=3):
    """base 아래 1~3단계를 훑어 실제 폴더를 찾는다.
    3_공통사용\\산출물\\회의록 처럼 깊어져도 잡아낸다."""
    base = cfg('base')
    names = ALIAS.get(key, ())
    if not names or not os.path.isdir(base):
        return None
    hit = _look_in(base, names)
    if hit:
        return hit
    # 공통 폴더로 한 겹 들어간 경우
    try:
        mids = [os.path.join(base, d) for d in os.listdir(base)
                if os.path.isdir(os.path.join(base, d))
                and (_plain(d) in {_plain(n) for n in NEST} or d in NEST)]
    except Exception:
        mids = []
    for m in mids:
        hit = _look_in(m, names)
        if hit:
            return hit
        if depth > 2:
            try:
                for d2 in os.listdir(m):
                    p2 = os.path.join(m, d2)
                    if os.path.isdir(p2):
                        hit = _look_in(p2, names)
                        if hit:
                            return hit
            except Exception:
                pass
    return None

def auto_base():
    """내 위치에서 base 폴더를 스스로 계산한다.
    ...\\{base}\\2_KM도구\\코드\\km_tools  이므로 3단계 위가 base.
    PC 가 바뀌어도(사용자 이름이 달라도) 그대로 돈다."""
    p = HERE
    for _ in range(4):
        p = os.path.dirname(p)
        if not p or len(p) < 4:
            break
        # base 로 보이는 표시 : 현장비서/원틀/plaud/공통사용 중 하나라도 있으면 base
        try:
            names = {_plain(d) for d in os.listdir(p)
                     if os.path.isdir(os.path.join(p, d))}
        except Exception:
            continue
        if names & {'현장비서', '원틀', 'plaud', '공통사용', '산출물'}:
            return p
    # 못 찾으면 코드\km_tools 의 두 단계 위(=도구 폴더의 부모)
    return os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

def cfg(key):
    """설정.ini 에서 경로를 읽는다. 없으면 스스로 찾는다."""
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        c.read(INI, encoding='utf-8')
        if c.has_option('경로', key):
            v = c.get('경로', key).strip()
            if v:
                return v
    d = DEFAULTS[key]
    if key == 'base':
        # 기본 경로가 이 PC 에 없으면(노트북 등) 내 위치에서 계산한다
        return d if os.path.isdir(d) else auto_base()
    if os.path.isdir(d):
        return d
    # 기본값에 없으면 이름이 바뀌었거나 다른 PC 다 - 후보로 찾아본다
    found = _find_by_alias(key)
    if found:
        return found
    # 그래도 없으면 지금 PC 의 base 아래 기본 이름으로 (없으면 만들어 쓰는 폴더)
    b = cfg('base')
    if os.path.isdir(b) and not d.startswith(b):
        names = ALIAS.get(key) or (os.path.basename(d),)
        return os.path.join(b, names[0])
    return d

SITE_DIRS = ('1.현장', '1_현장', '현장')
YEAR_DIRS = ('26년', '2026', '26')

def sites_root():
    """현장 폴더들이 실제로 들어 있는 곳.
    프로님 구조는 plaud\26년\1.현장\{현장명} 이다 (26년 아래는 1.현장/2.사내회의/3.할일... 분류 폴더).
    `1.현장` 이 있으면 그 아래를, 없으면 plaud 를 그대로 쓴다."""
    base = cfg('plaud')
    for d in SITE_DIRS:
        p = os.path.join(base, d)
        if os.path.isdir(p):
            return p
    # plaud 를 한 단계 위(26년 폴더가 그 아래)로 잡으신 경우도 찾아본다
    for y in YEAR_DIRS:
        for d in SITE_DIRS:
            p = os.path.join(base, y, d)
            if os.path.isdir(p):
                return p
    return base

def today():
    return datetime.date.today()

def ymd6(d=None):
    return (d or today()).strftime('%y%m%d')

BAD = r'\/:*?"<>|'
def safe_name(s, maxlen=80):
    """윈도우 금지문자 제거. 리눅스 통과 != 윈도우 통과 (km-30 규칙)"""
    s = str(s or '').strip()
    for ch in BAD:
        s = s.replace(ch, '_')
    s = re.sub(r'[\x00-\x1f]', '', s)
    s = s.rstrip(' .')
    return (s[:maxlen] or '_이름없음')

def outdir(toolname):
    """도구별 결과 폴더. _도구결과\\{도구}\\{YYMMDD}\\"""
    p = os.path.join(cfg('out'), safe_name(toolname), ymd6())
    os.makedirs(p, exist_ok=True)
    return p

def title(s):
    line = '=' * 56
    print(line); print(' ' + s); print(line)

AUTO = False   # True 면 묻지 않고 기본값으로 간다 (32번 「한 방에」 가 켠다)

def ask(msg, default=''):
    if AUTO:
        print('%s%s   [자동]' % (msg, default))
        return default
    try:
        v = input(msg).strip()
    except EOFError:
        v = ''
    return v or default

def pause():
    print('')
    try:
        input('엔터를 누르면 닫힙니다...')
    except EOFError:
        pass

def need(path, what):
    """경로가 없으면 무엇이 필요한지 알리고 False"""
    if not os.path.isdir(path) and not os.path.isfile(path):
        print('[없음] %s' % path)
        print('       -> %s' % what)
        return False
    return True

def walk_files(root, exts=None):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith('_삭제요망')]
        for f in fn:
            if exts and os.path.splitext(f)[1].lower() not in exts:
                continue
            yield os.path.join(dp, f)

def read_text(path):
    for enc in ('utf-8', 'cp949', 'utf-8-sig'):
        try:
            with io.open(path, 'r', encoding=enc) as fp:
                return fp.read()
        except Exception:
            continue
    return ''

def won(n):
    """금액 표기 #,##0 (km-operating-rules 6.8)"""
    try:
        return format(int(round(float(n))), ',')
    except Exception:
        return str(n)

def write_csv(path, rows, header=None):
    """엑셀에서 바로 열리게 cp949 우선(한글 깨짐 방지), 실패 시 utf-8-sig"""
    import csv
    enc = 'cp949'
    try:
        fp = io.open(path, 'w', encoding=enc, newline='', errors='strict')
        fp.close()
    except Exception:
        enc = 'utf-8-sig'
    with io.open(path, 'w', encoding=enc, newline='', errors='replace') as fp:
        w = csv.writer(fp)
        if header:
            w.writerow(header)
        for r in rows:
            w.writerow(r)
    return path

# ---- v2 추가분 (도구 13~23 공용) ----

def find_template(*keys):
    """_원틀 폴더에서 키워드가 든 파일을 찾는다. 없으면 None.
    원틀은 절대 새로 그리지 않는다 (km-operating-rules 6.6-1)."""
    root = cfg('template')
    if not os.path.isdir(root):
        return None
    cands = []
    for p in walk_files(root):
        b = os.path.basename(p)
        if b.startswith('~$'):
            continue
        if all(k.lower() in b.lower() for k in keys):
            cands.append(p)
    if not cands:
        return None
    cands.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return cands[0]

def no_template(what, *keys):
    print('[원틀 없음] %s' % what)
    print('  찾은 곳 : %s' % cfg('template'))
    print('  찾은 이름 조건 : %s' % ' + '.join(keys))
    print('  -> 원틀 파일을 그 폴더에 넣어주십시오. 서식은 새로 그리지 않습니다.')

def zip_replace(src, dst, mapping):
    """zip 기반 문서(pptx/hwpx/docx)의 본문 텍스트만 치환해 다른 이름으로 저장.
    서식(틀)은 전혀 건드리지 않는다."""
    import zipfile, shutil
    shutil.copy(src, dst)
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    tmp = dst + '.tmp'
    zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
    hit = 0
    for n in names:
        data = zin.read(n)
        if n.lower().endswith(('.xml', '.rels', '.txt')):
            try:
                t = data.decode('utf-8')
                for k, v in mapping.items():
                    if k in t:
                        t = t.replace(k, str(v)); hit += 1
                data = t.encode('utf-8')
            except Exception:
                pass
        zout.writestr(n, data)
    zout.close(); zin.close()
    os.replace(tmp, dst)
    return hit

def write_html(path, title_text, blocks, files=()):
    """블록 = [(제목, [(색, 줄)])]. 색 : red/yellow/green/gray
    files = 같이 만든 파일 경로들. 눌러서 바로 열 수 있게 링크로 붙는다."""
    C = {'red': '#C0392B', 'yellow': '#C77B2B', 'green': '#2E7D5B', 'gray': '#8E99A4',
         'blue': '#2A6099', 'purple': '#6B4FA8'}
    h = ['<!doctype html><meta charset="utf-8"><title>%s</title>' % title_text,
         '<style>body{font-family:"맑은 고딕",system-ui;margin:0;padding:16px;background:#fff;color:#111}',
         'h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:18px 0 6px;border-bottom:2px solid #eee;padding-bottom:4px}',
         '.r{display:flex;gap:8px;padding:7px 10px;border-left:5px solid #ccc;background:#fafafa;margin:4px 0;font-size:14px;line-height:1.45}',
         '.n{color:#8E99A4;font-size:12px;margin:2px 0 10px}</style>',
         '<h1>%s</h1><div class="n">%s 생성 · KM 현장비서</div>' % (title_text, today().isoformat())]
    if files:
        h.append('<h2>만든 파일 (누르면 열립니다)</h2>')
        for f in files:
            h.append('<div class="r" style="border-color:#2A6099">'
                     '<a href="%s" style="color:#2A6099">%s</a></div>'
                     % (file_url(f), os.path.basename(f)))
        h.append('<div class="r" style="border-color:#8E99A4">'
                 '<a href="%s" style="color:#8E99A4">폴더 열기</a></div>'
                 % file_url(os.path.dirname(os.path.abspath(path))))
    for name, rows in blocks:
        h.append('<h2>%s</h2>' % name)
        if not rows:
            h.append('<div class="r" style="border-color:%s">없음</div>' % C['gray'])
        for color, line in rows:
            h.append('<div class="r" style="border-color:%s">%s</div>' % (C.get(color, '#ccc'), line))
    io.open(path, 'w', encoding='utf-8').write('\n'.join(h))
    try:
        import shutil
        latest = os.path.join(cfg('out'), '_최신결과.html')
        os.makedirs(os.path.dirname(latest), exist_ok=True)
        shutil.copy(path, latest)
    except Exception:
        pass
    return path

def log(tool, msg):
    p = os.path.join(cfg('out'), '_실행기록.txt')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'a', encoding='utf-8') as fp:
        fp.write('%s\t%s\t%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), tool, msg))

def ensure_pkg(mod, pkg):
    """무거운 부품(도면 읽기 등)은 그 도구를 누르실 때만 받는다.
    받아지면 True. 인터넷이 막혀 있으면 False 를 돌려주고 도구가 스스로 안내한다."""
    import importlib, subprocess
    try:
        return importlib.import_module(mod)
    except ImportError:
        pass
    print('[부품 받는 중] %s  (처음 한 번만, 1~2분)' % pkg)
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet',
                        '--no-warn-script-location', pkg], check=False)
    except Exception as e:
        print('  실패 : %s' % e)
    try:
        importlib.invalidate_caches()
        return importlib.import_module(mod)
    except ImportError:
        print('  [못 받음] 인터넷이 막혀 있을 수 있습니다.')
        print('  직접 받기 : 명령 프롬프트에서  python -m pip install %s' % pkg)
        return None

def file_url(p):
    """HTML 안에서 눌러 열 수 있는 주소"""
    import urllib.parse
    return 'file:///' + urllib.parse.quote(os.path.abspath(p).replace('\\', '/'), safe='/:')

def open_file(p):
    """만든 파일을 바로 띄운다. 폴더를 뒤지지 않게."""
    try:
        if os.name == 'nt':
            os.startfile(p)
        else:
            os.system('xdg-open "%s" 2>/dev/null &' % p)
        return True
    except Exception:
        return False

def open_folder(p):
    try:
        os.makedirs(p, exist_ok=True)
        os.system(('start "" "%s"' if os.name == 'nt' else 'xdg-open "%s" 2>/dev/null &') % p)
    except Exception:
        pass


# ---------------- 엑셀 수식 결과를 파일에 미리 넣기 ----------------
def finish_xlsx(path):
    """openpyxl 로 만든 xlsx 는 수식만 있고 계산값이 없어, 인터넷에서 받은 파일(보호된 보기)이나 미리보기에서는
    금액 칸이 비어 보인다. 1) 윈도우+엑셀이 있으면 엑셀로 한 번 계산해 저장, 2) 아니면 파이썬이 계산한 값을 파일 안에 넣는다.
    -> '엑셀' / '파이썬 n칸' / '' """
    if os.name == 'nt':
        try:
            import win32com.client
            xl = win32com.client.DispatchEx('Excel.Application'); xl.Visible = False; xl.DisplayAlerts = False
            wb = xl.Workbooks.Open(os.path.abspath(path)); xl.CalculateFull(); wb.Save(); wb.Close(False); xl.Quit()
            return '엑셀'
        except Exception:
            pass
    try:
        import openpyxl, zipfile, re, shutil
        sys.path.insert(0, HERE)
        from t37_check import Calc
        wb = openpyxl.load_workbook(path)
        calc = Calc(wb)
        vals = {}
        for i, ws in enumerate(wb.worksheets, 1):
            d = {}
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith('='):
                        try:
                            v = calc.val(ws, c.coordinate)
                        except Exception:
                            v = None
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            d[c.coordinate] = v
            vals['xl/worksheets/sheet%d.xml' % i] = d
        tmp = path + '.tmp'
        n = 0
        with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                d = vals.get(item.filename)
                if d:
                    x = data.decode('utf-8')
                    def rep(m):
                        nonlocal n
                        ref = m.group(1)
                        if ref in d:
                            n += 1
                            v = d[ref]
                            return '<c r="%s"%s><f>%s</f><v>%s</v></c>' % (ref, m.group(2), m.group(3), repr(float(v)) if v != int(v) else int(v))
                        return m.group(0)
                    x = re.sub(r'<c r="([A-Z]+\d+)"([^>]*)><f>(.*?)</f><v></v></c>', rep, x)
                    data = x.encode('utf-8')
                zout.writestr(item, data)
        shutil.move(tmp, path)
        return '파이썬 %d칸' % n
    except Exception:
        return ''


# ---------------- 바로가기 (어디에 두어도 됨 : 시작.py 절대 경로가 안에 적혀 있다) ----------------
_SHORTCUT = """# -*- coding: utf-8 -*-
# KM 바로가기 - 더블클릭만 하십시오. 어디에 두어도 됩니다. (%(what)s)
import os, sys, subprocess
START = %(start)r
if not os.path.exists(START):
    # 폴더를 옮기셨으면 이 파일 위쪽 7단계에서 2_KM도구\\시작.py 를 찾아본다
    d = os.path.dirname(os.path.abspath(__file__)); START = None
    for _ in range(7):
        c = os.path.join(d, '2_KM도구', '시작.py')
        if os.path.exists(c):
            START = c; break
        d = os.path.dirname(d)
if not START:
    print('2_KM도구\\시작.py 를 못 찾았습니다. 시작.py 를 한 번 눌러 주시면 바로가기가 다시 만들어집니다.')
    input('엔터...'); sys.exit(1)
subprocess.call([sys.executable, START] + %(args)s)
"""

def start_py():
    return os.path.join(os.path.dirname(os.path.dirname(HERE)), '시작.py')

def desktop_dir():
    home = os.path.expanduser('~')
    for d in (os.path.join(home, 'OneDrive', 'Desktop'), os.path.join(home, 'OneDrive', '바탕 화면'),
              os.path.join(home, 'Desktop'), os.path.join(home, '바탕 화면')):
        if os.path.isdir(d):
            return d
    return None

def make_shortcuts(folder, refresh=False):
    """바로가기 2개를 folder 에 둔다 (도면 폴더·바탕화면 등 어디든). 안에 시작.py 절대 경로가 들어 있어
       「클로드가 저장하는 폴더」 밖에 두어도 된다. refresh=True 면 경로가 바뀐 경우 다시 쓴다.
       ★KM_도면넣고_여기클릭.py = 36 오늘 한 방에 (번호 미리 들어 있음)
       ★KM_번호입력.py          = 클로드가 알려준 번호 하나 넣고 실행"""
    made = []
    if not folder:
        return made
    try:
        os.makedirs(folder, exist_ok=True)
        for name, what, args in (('★KM_도면넣고_여기클릭.py', '「오늘 한 방에」 36번', "['36']"),
                                 ('★KM_번호입력.py', '번호 하나 넣고 그 도구 실행', "['--ask']")):
            pth = os.path.join(folder, name)
            body = _SHORTCUT % {'what': what, 'args': args, 'start': start_py()}
            if os.path.exists(pth) and not refresh:
                try:
                    if start_py() in io.open(pth, encoding='utf-8').read():
                        continue
                except Exception:
                    pass
            with io.open(pth, 'w', encoding='utf-8') as fp:
                fp.write(body)
            made.append(pth)
        # 옛 이름(★도면넣고_여기클릭.py 등)은 지우지 않고 둔다
    except Exception:
        pass
    return made

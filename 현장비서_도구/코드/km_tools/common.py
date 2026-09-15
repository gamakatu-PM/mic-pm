# -*- coding: utf-8 -*-
"""KM 현장비서 도구모음 - 공통 유틸
한국마이크로닉(주) 배성윤 프로 전용. 토큰 0(로컬 파이썬)으로 도는 도구들의 공용 부품.
"""
import os, re, sys, io, configparser, datetime

# ---- 콘솔 한글 ----
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
INI = os.path.join(HERE, '설정.ini')

DEFAULTS = {
    'base':    r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더',
    'plaud':   r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\plaud\26년',
    'biseo':   r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\_현장비서',
    'template':r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\_원틀',
    'out':     r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\_도구결과',
}

def cfg(key):
    """설정.ini 에서 경로를 읽는다. 없으면 기본값."""
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        c.read(INI, encoding='utf-8')
        if c.has_option('경로', key):
            v = c.get('경로', key).strip()
            if v:
                return v
    return DEFAULTS[key]

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

def ask(msg, default=''):
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

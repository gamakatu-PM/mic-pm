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
    'handover':r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\KM_인수인계함',
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

def write_html(path, title_text, blocks):
    """블록 = [(제목, [(색, 줄)])]. 색 : red/yellow/green/gray"""
    C = {'red': '#C0392B', 'yellow': '#C77B2B', 'green': '#2E7D5B', 'gray': '#8E99A4',
         'blue': '#2A6099', 'purple': '#6B4FA8'}
    h = ['<!doctype html><meta charset="utf-8"><title>%s</title>' % title_text,
         '<style>body{font-family:"맑은 고딕",system-ui;margin:0;padding:16px;background:#fff;color:#111}',
         'h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:18px 0 6px;border-bottom:2px solid #eee;padding-bottom:4px}',
         '.r{display:flex;gap:8px;padding:7px 10px;border-left:5px solid #ccc;background:#fafafa;margin:4px 0;font-size:14px;line-height:1.45}',
         '.n{color:#8E99A4;font-size:12px;margin:2px 0 10px}</style>',
         '<h1>%s</h1><div class="n">%s 생성 · KM 현장비서</div>' % (title_text, today().isoformat())]
    for name, rows in blocks:
        h.append('<h2>%s</h2>' % name)
        if not rows:
            h.append('<div class="r" style="border-color:%s">없음</div>' % C['gray'])
        for color, line in rows:
            h.append('<div class="r" style="border-color:%s">%s</div>' % (C.get(color, '#ccc'), line))
    io.open(path, 'w', encoding='utf-8').write('\n'.join(h))
    return path

def log(tool, msg):
    p = os.path.join(cfg('out'), '_실행기록.txt')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'a', encoding='utf-8') as fp:
        fp.write('%s\t%s\t%s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), tool, msg))

def open_folder(p):
    try:
        os.makedirs(p, exist_ok=True)
        os.system(('start "" "%s"' if os.name == 'nt' else 'xdg-open "%s" 2>/dev/null &') % p)
    except Exception:
        pass

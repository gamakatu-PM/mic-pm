# -*- coding: utf-8 -*-
"""27. 도면 수량 뽑기 - 도면 파일을 넣으면 기구물 수량을 센다. 토큰 0(내 PC 안에서만).

읽는 방식
  DXF  : 블록(INSERT) 이름별 개수 + 글자(TEXT/MTEXT/ATTRIB)  -> 가장 정확
  DWG  : 그대로는 못 읽는다. ODA File Converter 가 깔려 있으면 자동으로 DXF 로 바꿔 읽는다.
  PDF  : 글자가 살아 있는 PDF 면 글자를 뽑아 센다. 스캔 PDF 는 못 센다.
  사진/캡처 : 파이썬으로는 못 센다 -> 클로드에게 주실 목록으로 따로 뽑아 드린다.

수량은 제가 정하지 않습니다. 「블록 기준」과 「글자 기준」을 나란히 보여드리고,
어느 쪽을 채택했는지 표에 적어 둡니다. 사전에 없는 기호는 따로 모아 드립니다.
"""
import os, sys, re, glob, collections
from common import *

TOOL = '도면수량'
DXF_EXT = ('.dxf',)
DWG_EXT = ('.dwg',)
PDF_EXT = ('.pdf',)
IMG_EXT = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.gif', '.webp')
INBOX = '_여기에_넣으십시오'
DICT_NAME = '기호사전.csv'

DICT_HEAD = [
 '# 도면 기호 사전 - 이 파일만 고치시면 수량 뽑는 기준이 바뀝니다.',
 '# 맞추기 : 정확 = 글자가 이것과 똑같을 때만 / 포함 = 이 낱말이 들어 있으면',
 '# 쓸모 없는 줄은 앞에 # 을 붙이거나 지우시면 됩니다.',
 '기호,품목,맞추기',
]
DICT_ROWS = [
 ('CHIME', '챠임벨', '포함'), ('챠임', '챠임벨', '포함'), ('차임', '챠임벨', '포함'),
 ('BELL', '챠임벨', '포함'),
 ('KS', '키센서(K)', '정확'), ('K', '키센서(K)', '정확'),
 ('KEY', '키센서(K)', '포함'), ('키센서', '키센서(K)', '포함'),
 ('DM', '도어표시(DM)', '정확'), ('DOOR', '도어표시(DM)', '포함'),
 ('BSP', 'BSP(온도+조명+USB+유니버셜)', '포함'),
 ('TH', '온도조절기', '정확'), ('T', '온도조절기', '정확'),
 ('THERMO', '온도조절기', '포함'), ('온도', '온도조절기', '포함'),
 ('L', '조명스위치(L)', '정확'), ('LS', '조명스위치(L)', '정확'),
 ('LSW', '조명스위치(L)', '정확'), ('LIGHT', '조명스위치(L)', '포함'),
 ('MO', '멀티아울렛', '정확'), ('MULTI', '멀티아울렛', '포함'),
 ('멀티', '멀티아울렛', '포함'), ('OUTLET', '멀티아울렛', '포함'),
 ('FIP', 'FIP(린넨실)', '포함'),
 ('RCU', 'RCU', '포함'), ('MMO', 'MMO', '포함'),
 ('PC', 'OPERATION PC', '정확'),
 ('CB', 'CB 외함', '정확'),
]
# 품목을 「무시」로 두면 그 낱말은 아예 안 셉니다 (도면에 흔한 글자들)
IGNORE_ROWS = [
 ('ROOM', '무시', '정확'), ('TYPE', '무시', '정확'), ('SCALE', '무시', '정확'),
 ('PLAN', '무시', '정확'), ('NOTE', '무시', '정확'), ('NO', '무시', '정확'),
 ('EA', '무시', '정확'), ('SET', '무시', '정확'), ('MM', '무시', '정확'),
 ('THK', '무시', '정확'), ('FL', '무시', '정확'), ('FFL', '무시', '정확'),
 ('DN', '무시', '정확'), ('UP', '무시', '정확'), ('DIM', '무시', '정확'),
 ('DETAIL', '무시', '정확'), ('SECTION', '무시', '정확'), ('LEGEND', '무시', '정확'),
 ('객실', '무시', '포함'), ('평면', '무시', '포함'), ('도면', '무시', '포함'),
 ('범례', '무시', '포함'), ('축척', '무시', '포함'), ('비고', '무시', '포함'),
 ('에어컨', '무시', '포함'), ('AIRCON', '무시', '포함'), ('DIFF', '무시', '정확'),
]

# ---------------- 폴더 / 사전 ----------------

GUIDE = '''도면 보관소 - 현장별로 도면을 쌓아 두는 곳입니다.

[폴더 약속]
  {현장명}\\              현장마다 폴더 하나. 캐드(dwg/dxf)·PDF·수량표(xlsx)를 그냥 넣어 두십시오
  26년\\{현장명}\\        연도로 나누고 싶으시면 26년(또는 2026) 폴더를 만들고 그 안에 현장 폴더를 두십시오.
                          도구가 연도 폴더를 알아서 들여다봅니다. 새 도면은 가장 최신 연도 폴더로 들어갑니다.
                          같은 현장이 여러 연도에 있으면 최신 연도 것만 읽습니다 (옛 연도는 보관용)
      _도면대장.csv        31번이 스스로 씁니다 (어느 파일을 언제 몇 판으로 읽었나)
  _여기에_넣으십시오\\    현장이 정해지지 않은 도면 임시 자리 (판 비교는 안 됩니다)
  기호사전.csv            도면 기호 -> 우리 품목. 안 맞는 것만 한 줄 추가

[새 도면이 오면]
  그 현장 폴더에 넣고  32번(현장 한 방에) 을 누르십시오.
  31 접수·판 비교 -> 27 수량 -> 28 금액 -> 29 단가장 -> 30 부탁서  가 묻지 않고 돌아갑니다.
  이전 판이 있으면 품목별 증감이 같이 나옵니다.
  파일은 옮기거나 지우지 않습니다. 대장에 적기만 합니다.

[읽히는 것]
  DXF   가장 정확합니다. 블록 개수를 그대로 셉니다.
  DWG   ODA File Converter 가 깔려 있으면 자동 변환. 없으면 캐드에서 DXF 로 한 번 저장.
  PDF   NOTE(범례) 수량표가 있으면 그것을 그대로 옮깁니다. 글자가 살아 있어야 합니다.
  사진/캡처/스캔   파이썬으로는 못 읽습니다. 30번 부탁서에 목록으로 남으니 클로드에게 주십시오.

[수량·금액은 도구가 정하지 않습니다]
  도면에 적힌 값과 단가장 값을 옮길 뿐입니다. 못 찾으면 비워 두고 부탁서로 넘깁니다.
'''

def dwg_root():
    root = cfg('drawing')
    try:
        os.makedirs(os.path.join(root, INBOX), exist_ok=True)
        make_shortcuts(root); make_shortcuts(desktop_dir())
        g = os.path.join(root, '_읽어보세요.txt')
        if not os.path.exists(g):
            for enc in ('cp949', 'utf-8-sig'):
                try:
                    import io as _io
                    _io.open(g, 'w', encoding=enc, errors='strict').write(GUIDE)
                    break
                except Exception:
                    continue
    except Exception:
        pass
    return root

def dict_path():
    return os.path.join(dwg_root(), DICT_NAME)

def make_dict_file():
    p = dict_path()
    if os.path.exists(p):
        return p
    lines = (list(DICT_HEAD) + ['%s,%s,%s' % r for r in DICT_ROWS] +
             ['# ---- 아래는 셈에서 빼는 낱말입니다 (품목칸이 「무시」) ----'] +
             ['%s,%s,%s' % r for r in IGNORE_ROWS])
    txt = '\n'.join(lines) + '\n'
    for enc in ('cp949', 'utf-8-sig'):
        try:
            import io as _io
            _io.open(p, 'w', encoding=enc, errors='strict').write(txt)
            return p
        except Exception:
            continue
    return p

def load_dict():
    p = make_dict_file()
    rows, ign = [], []
    for line in read_text(p).splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = [c.strip() for c in line.split(',')]
        if len(parts) < 2 or parts[0] in ('기호',):
            continue
        mode = parts[2] if len(parts) > 2 and parts[2] in ('정확', '포함') else '포함'
        if parts[1] in ('무시', '제외', '버림'):
            ign.append((parts[0], mode))
        else:
            rows.append((parts[0], parts[1], mode))
    return rows, ign, p

def norm(s):
    return re.sub(r'\s+', '', str(s or '')).upper()

SPLIT = re.compile(r'[^0-9A-Z가-힣]+')

def is_ignored(sym, ign):
    s = norm(sym)
    for pat, mode in ign:
        if mode == '정확' and s == norm(pat):
            return True
    for pat, mode in ign:
        if mode == '포함' and norm(pat) in s:
            return True
    return False

def match_all(sym, dic, ign=()):
    """맞춘 품목들과 어떻게 맞췄는지.
      정확 = 글자가 사전과 똑같다        (가장 믿을 수 있음)
      포함 = 사전 낱말이 들어 있다
      쪼갬 = 이름을 - _ + 로 쪼개 보니 맞았다 (K+DM 같은 경우. 확인하셔야 합니다)
    맞은 게 없으면 ([], None)."""
    s = norm(sym)
    if not s:
        return [], None
    if ign and is_ignored(s, ign):
        return [], '무시'
    for pat, item, mode in dic:
        if mode == '정확' and s == norm(pat):
            return [item], '정확'
    for pat, item, mode in dic:
        if mode == '포함' and norm(pat) in s:
            return [item], '포함'
    parts = [x for x in SPLIT.split(s) if x]
    if len(parts) > 1:
        got = []
        for prt in parts:
            for pat, item, mode in dic:
                if mode == '정확' and prt == norm(pat) and item not in got:
                    got.append(item)
                    break
        if got:
            return got, '쪼갬'
    return [], None

def match_sym(sym, dic, ign=()):
    items, _ = match_all(sym, dic, ign)
    return items[0] if items else None

# ---------------- 파일 모으기 ----------------

def gather(root):
    out = []
    if os.path.isfile(root):
        return [root]
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(('_처리완료', '_삭제요망', '_이전판'))]
        for f in sorted(fn):
            if f.startswith('~') or f == DICT_NAME:
                continue
            e = os.path.splitext(f)[1].lower()
            if e in DXF_EXT + DWG_EXT + PDF_EXT + IMG_EXT:
                out.append(os.path.join(dp, f))
    return out

# ---------------- 읽기 ----------------

def oda_exe():
    pats = [r'C:\Program Files\ODA\*\ODAFileConverter.exe',
            r'C:\Program Files\ODA\ODAFileConverter*\ODAFileConverter.exe',
            r'C:\Program Files (x86)\ODA\*\ODAFileConverter.exe']
    for pat in pats:
        hit = glob.glob(pat)
        if hit:
            return hit[0]
    return None

def dwg_to_dxf(path):
    """ODA File Converter 가 있으면 DXF 로 바꿔 임시 폴더에 둔다. 없으면 None."""
    exe = oda_exe()
    if not exe:
        return None
    import tempfile, shutil, subprocess
    src = tempfile.mkdtemp(prefix='kmdwg_i')
    dst = tempfile.mkdtemp(prefix='kmdwg_o')
    shutil.copy(path, os.path.join(src, os.path.basename(path)))
    try:
        subprocess.run([exe, src, dst, 'ACAD2018', 'DXF', '0', '1'],
                       check=False, timeout=600)
    except Exception:
        return None
    hit = glob.glob(os.path.join(dst, '*.dxf')) + glob.glob(os.path.join(dst, '*.DXF'))
    return hit[0] if hit else None

def read_dxf(path):
    """블록 개수, 글자 목록, 레이어별 개수"""
    ezdxf = ensure_pkg('ezdxf', 'ezdxf')
    if not ezdxf:
        return None, '부품(ezdxf)이 없어 못 읽었습니다'
    try:
        doc = ezdxf.readfile(path)
    except Exception:
        try:
            from ezdxf import recover
            doc, aud = recover.readfile(path)
        except Exception as e:
            return None, '열다가 막혔습니다 : %s' % e
    blocks = collections.Counter()
    layers = collections.Counter()
    texts = []
    spaces = [doc.modelspace()]
    try:
        for lay in doc.layouts:
            if lay.name.lower() != 'model':
                spaces.append(lay)
    except Exception:
        pass
    for sp in spaces:
        for e in sp:
            t = e.dxftype()
            try:
                if t == 'INSERT':
                    blocks[e.dxf.name] += 1
                    layers[e.dxf.layer] += 1
                    try:
                        for a in e.attribs:
                            texts.append(a.dxf.text)
                    except Exception:
                        pass
                elif t == 'TEXT':
                    texts.append(e.dxf.text)
                elif t == 'MTEXT':
                    texts.append(e.text)
            except Exception:
                continue
    return {'blocks': blocks, 'layers': layers, 'texts': texts}, ''

XREF_PRE = ('xr_', 'xref', 'xr-')

def is_xref(path):
    """외부참조(xref) 도면은 본 도면이 아니라 부품이다. 세지 않는다."""
    return os.path.basename(path).lower().startswith(XREF_PRE)

NUMOK = re.compile(r'^[0-9][0-9,]{0,5}$')
HANGUL = re.compile(r'[가-힣A-Za-z]{2,}')

def read_pdf_table(path):
    """PDF 안의 「기호 / 내용 / 수량」 표(NOTE·범례)를 좌표로 복원해 그대로 읽는다.
    세는 것이 아니라 도면에 적힌 수량을 옮기는 것 - 이게 가장 정확하다."""
    fitz = ensure_pkg('pymupdf', 'pymupdf') or ensure_pkg('fitz', 'pymupdf')
    if not fitz:
        return []
    try:
        d = fitz.open(path)
    except Exception:
        return []
    out = []
    for pno, pg in enumerate(d, start=1):
        try:
            words = pg.get_text('words')
        except Exception:
            continue
        if not words:
            continue
        flat = ' '.join(w[4] for w in words)
        # 도면은 「N O T E」 「수 량」 처럼 글자를 벌려 쓰는 일이 많다. 공백을 지우고 본다
        flat_ns = re.sub(r'\s+', '', flat).upper()
        if not any(k in flat_ns for k in ('NOTE', '수량', 'QTY', 'QUANTITY', '기호', 'SYMBOL', '범례', 'LEGEND')):
            continue
        lines = {}
        for w in words:
            lines.setdefault(round(w[1] / 3.0), []).append(w)
        for key in sorted(lines):
            ws = sorted(lines[key], key=lambda w: w[0])
            toks = [w[4].strip() for w in ws if w[4].strip()]
            if len(toks) < 2:
                continue
            last = toks[-1]
            if not NUMOK.match(last):
                continue
            qty = int(last.replace(',', ''))
            if qty <= 0 or qty > 99999:
                continue
            body = toks[:-1]
            name = ' '.join(body[1:]) if len(body) > 1 else body[0]
            if not HANGUL.search(name):
                continue
            out.append({'page': pno, 'sym': body[0], 'name': name.strip(), 'qty': qty})
    d.close()
    # 같은 줄이 두 번 잡히는 것 제거
    seen, uniq = set(), []
    for r in out:
        k = (r['sym'], r['name'], r['qty'])
        if k in seen:
            continue
        seen.add(k); uniq.append(r)
    return uniq

def read_pdf(path):
    fitz = ensure_pkg('pymupdf', 'pymupdf') or ensure_pkg('fitz', 'pymupdf')
    if not fitz:
        return None, '부품(pymupdf)이 없어 못 읽었습니다'
    try:
        d = fitz.open(path)
    except Exception as e:
        return None, '열다가 막혔습니다 : %s' % e
    texts = []
    pages = 0
    for pg in d:
        pages += 1
        try:
            t = pg.get_text()
        except Exception:
            t = ''
        texts.extend([x for x in re.split(r'[\r\n]+', t) if x.strip()])
    d.close()
    chars = sum(len(x) for x in texts)
    if pages and chars / float(pages) < 40:
        return {'blocks': collections.Counter(), 'layers': collections.Counter(),
                'texts': texts, 'scan': True}, '글자가 거의 없습니다(스캔 PDF로 보입니다)'
    return {'blocks': collections.Counter(), 'layers': collections.Counter(),
            'texts': texts}, ''

# ---------------- 세기 ----------------

TOK = re.compile(r'[A-Za-z가-힣]{1,12}[0-9]{0,3}')

def tokens(texts):
    c = collections.Counter()
    for t in texts:
        s = str(t or '')
        s = re.sub(r'\\[A-Za-z][^;]*;', ' ', s)   # MTEXT 서식코드 제거
        for m in TOK.findall(s):
            c[m.upper()] += 1
    return c

def tally(blocks, toks, dic, ign=()):
    """품목별 (블록기준, 글자기준) 합계 + 모르는 기호 + 쪼개서 맞춘 것"""
    by_item = collections.defaultdict(lambda: [0, 0])
    unknown_b = collections.Counter()
    unknown_t = collections.Counter()
    split_log = []
    for name, n in sorted(blocks.items(), key=lambda kv: -kv[1]):
        items, how = match_all(name, dic, ign)
        if how == '무시':
            continue
        if not items:
            unknown_b[name] += n
            continue
        for it in items:
            by_item[it][0] += n
        if how == '쪼갬':
            split_log.append(['블록', name, ' + '.join(items), n])
    for tok, n in sorted(toks.items(), key=lambda kv: -kv[1]):
        items, how = match_all(tok, dic, ign)
        if how == '무시':
            continue
        if not items:
            if len(tok) <= 6 and n >= 3:
                unknown_t[tok] += n
            continue
        for it in items:
            by_item[it][1] += n
        if how == '쪼갬':
            split_log.append(['글자', tok, ' + '.join(items), n])
    return by_item, unknown_b, unknown_t, split_log

# ---------------- 실행 ----------------

def guess_site(files, inbox):
    """도면이 든 폴더 이름 또는 파일 이름에서 현장명을 짐작한다."""
    for f in files:
        d = os.path.basename(os.path.dirname(f))
        if d and d not in (INBOX, '도면', '_도면') and not d.startswith('_'):
            return d
    b = os.path.splitext(os.path.basename(files[0]))[0] if files else ''
    b = re.split(r'[_\-]', b)[0]
    return b or '현장미정'

DRAW_NO = re.compile(r'[A-Z]{1,3}-\d{3,5}')

def _rev_key(f):
    """판 순서 : Rev/R 숫자 > 앞머리 날짜(YYMMDD) > 수정시각"""
    b = os.path.basename(f)
    m = re.search(r'(?i)rev\.?\s*(\d+)', b) or re.search(r'(?i)\bR(\d+)\b', b)
    rev = int(m.group(1)) if m else -1
    m2 = re.match(r'(\d{6,8})', b)
    dt = int(m2.group(1)) if m2 else 0
    try:
        mt = os.path.getmtime(f)
    except Exception:
        mt = 0
    return (rev, dt, mt)

def latest_per_drawing(files):
    """같은 도면번호(T-1101 등)의 파일이 여러 판이면 최신 판 하나만 남긴다.
    -> (읽을 파일들, 건너뛴 이전 판들)  ※ 도면번호가 없는 파일은 이름에서 날짜·Rev 를 뗀 것으로 묶는다"""
    groups = {}
    for f in files:
        b = os.path.basename(f)
        m = DRAW_NO.search(b.upper())
        if m:
            key = (m.group(0), os.path.splitext(b)[1].lower())
        else:
            stem = re.sub(r'(?i)rev\.?\s*\d+|\bR\d+\b|^\d{6,8}[_\- ]*|\[[^\]]*\]', '', os.path.splitext(b)[0]).strip(' _-')
            key = (stem.upper(), os.path.splitext(b)[1].lower())
        groups.setdefault(key, []).append(f)
    keep, skipped = [], []
    for key, fs in groups.items():
        fs = sorted(fs, key=_rev_key)
        keep.append(fs[-1]); skipped.extend(fs[:-1])
    keep.sort(); skipped.sort()
    return keep, skipped

def read_all(files):
    """도면을 먼저 다 읽는다. 질문은 하지 않는다."""
    blocks = collections.Counter()
    toks = collections.Counter()
    per_file, scans, unread, table = [], [], [], []
    for f in files:
        if is_xref(f):
            per_file.append((os.path.basename(f), '외부참조(xref)', 0, 0, '본 도면이 아니라 건너뜀'))
            print(' [건너뜀] %-36s 외부참조(xref) 파일' % os.path.basename(f)[:36])
            continue
        e = os.path.splitext(f)[1].lower()
        nm = os.path.basename(f)
        if e in DXF_EXT:
            d, msg = read_dxf(f)
            nb = sum(d['blocks'].values()) if d else 0
            nt = len(d['texts']) if d else 0
            per_file.append((nm, 'DXF', nb, nt, msg))
            print(' [DXF] %-38s 블록 %6s / 글자 %5s %s' % (nm[:38], won(nb), won(nt), msg))
            if d:
                blocks.update(d['blocks']); toks.update(tokens(d['texts']))
            else:
                unread.append((nm, msg))
        elif e in DWG_EXT:
            conv = dwg_to_dxf(f)
            if conv:
                d, msg = read_dxf(conv)
                nb = sum(d['blocks'].values()) if d else 0
                nt = len(d['texts']) if d else 0
                per_file.append((nm, 'DWG(자동변환)', nb, nt, msg))
                print(' [DWG] %-38s 블록 %6s / 글자 %5s (자동변환)' % (nm[:38], won(nb), won(nt)))
                if d:
                    blocks.update(d['blocks']); toks.update(tokens(d['texts']))
                else:
                    unread.append((nm, msg))
            else:
                per_file.append((nm, 'DWG', 0, 0, 'DWG는 그대로 못 읽습니다'))
                print(' [DWG] %-38s 못 읽었습니다 (DXF로 저장해 주십시오)' % nm[:38])
                unread.append((nm, 'DWG - 캐드에서 「다른 이름으로 저장 -> DXF」'))
        elif e in PDF_EXT:
            d, msg = read_pdf(f)
            nt = len(d['texts']) if d else 0
            tb = read_pdf_table(f) if d and not d.get('scan') else []
            per_file.append((nm, 'PDF', 0, nt, msg or ('NOTE표 %d줄' % len(tb) if tb else '')))
            print(' [PDF] %-38s 글자 %6s  NOTE표 %s줄 %s'
                  % (nm[:38], won(nt), won(len(tb)), msg))
            if d:
                toks.update(tokens(d['texts']))
                if d.get('scan'):
                    scans.append(nm)
                    unread.append((nm, '스캔 PDF - 글자가 없습니다'))
            else:
                unread.append((nm, msg))
            for r in tb:
                r['file'] = nm
            table.extend(tb)
        else:
            per_file.append((nm, '사진/캡처', 0, 0, '파이썬으로는 못 셉니다'))
            print(' [사진] %-38s 파이썬으로는 못 셉니다' % nm[:38])
            unread.append((nm, '사진/캡처 - 클로드에게 주십시오'))
    return blocks, toks, per_file, scans, unread, table

def cant_read(unread, files):
    """한 장도 못 읽었을 때. 질문하지 않고 무엇을 해야 하는지만 알린다."""
    print('')
    print('=' * 70)
    print(' 읽을 수 있는 도면이 한 장도 없습니다. 현장명은 여쭙지 않겠습니다.')
    print('=' * 70)
    for nm, why in unread[:20]:
        print('  %-40s %s' % (nm[:40], why))
    print('')
    print(' 이렇게 주시면 셉니다')
    print('   1) DXF  - 캐드에서 「다른 이름으로 저장 -> DXF」. 가장 정확합니다.')
    print('   2) PDF  - 캐드에서 PDF로 인쇄(이미지로 인쇄 아님). 글자가 살아 있어야 합니다.')
    print('   3) 사진/캡처/스캔 - 파이썬으로는 못 셉니다. 저(클로드)에게 그 파일을 주십시오.')
    print('')
    od = outdir(TOOL)
    f = write_csv(os.path.join(od, '_클로드에게_주실파일_%s.csv' % ymd6()),
                  [[nm, why] for nm, why in unread], ['파일', '왜 못 셌나'])
    print(' 목록을 만들어 뒀습니다 : %s' % f)
    log(TOOL, '못읽음 %d개' % len(unread))

def run(folder=None, site_hint=None):
    title('27. 도면 수량 뽑기   (토큰 0 - 내 PC 안에서만 돕니다)')
    root = dwg_root()
    inbox = os.path.join(root, INBOX)
    if folder:
        files = gather(folder); where = folder
    else:
        files = gather(inbox)
        where = inbox
        if not files:
            files = gather(root); where = root
    if not files:
        print('도면 넣는 곳 : %s' % inbox)
        print('')
        print('[비어 있습니다] 이 폴더에 도면을 넣고 다시 27번을 누르시면 됩니다.')
        p = ask('\n또는 지금 도면이 있는 폴더/파일 경로를 붙여넣으십시오 (엔터=그만) > ').strip('"')
        if not p:
            print('')
            print('* 폴더를 열어 두겠습니다. 도면을 끌어다 넣으십시오.')
            open_folder(inbox)
            return
        if not os.path.exists(p):
            print('[없는 경로] %s' % p)
            return
        files = gather(p); where = p
        if not files:
            print('[도면 파일이 없습니다] dxf / dwg / pdf / 사진 만 봅니다.')
            return

    dic, ign, dpath = load_dict()
    dxf = [f for f in files if os.path.splitext(f)[1].lower() in DXF_EXT]
    dwg = [f for f in files if os.path.splitext(f)[1].lower() in DWG_EXT]
    pdf = [f for f in files if os.path.splitext(f)[1].lower() in PDF_EXT]
    img = [f for f in files if os.path.splitext(f)[1].lower() in IMG_EXT]

    print('본 곳   : %s' % where)
    print('찾은 것 : DXF %d / DWG %d / PDF %d / 사진 %d' % (len(dxf), len(dwg), len(pdf), len(img)))
    print('사전    : %s  (품목 %d줄 / 무시 %d줄)' % (os.path.basename(dpath), len(dic), len(ign)))
    print('-' * 70)
    print('먼저 도면을 읽습니다. (질문은 다 읽은 뒤에만 합니다)')
    print('')

    # 1) 먼저 읽는다
    files, older = latest_per_drawing(files)
    if older:
        print('이전 판이라 읽지 않은 파일 %d개 (같은 도면번호의 최신 판만 읽습니다) :' % len(older))
        for f in older:
            print('   (이전 판) %s' % os.path.basename(f))
    blocks, toks, per_file, scans, unread, table = read_all(files)

    # 2) 한 장도 못 읽었으면 여기서 끝. 아무것도 묻지 않는다
    if not blocks and not toks and not table:
        cant_read(unread, files)
        return

    # 2-1) 도면에 수량표(NOTE·범례)가 있으면 그게 정답이다. 세지 않고 그대로 옮긴다
    if table:
        print('')
        print('=' * 70)
        print(' 도면에 적힌 수량표를 찾았습니다. 세지 않고 그대로 옮깁니다. (가장 정확)')
        print('=' * 70)
        print('%-16s %-40s %8s  %s' % ('기호', '내용', '수량', '쪽'))
        print('-' * 74)
        for r in table:
            print('%-16s %-40s %8s  %s쪽' % (str(r['sym'])[:16], str(r['name'])[:40],
                                            won(r['qty']), r['page']))
        print('')
        print(' 합계 %s개 / 품목 %d줄' % (won(sum(r['qty'] for r in table)), len(table)))

    # 3) 센다
    by_item, unk_b, unk_t, split_log = tally(blocks, toks, dic, ign)
    if not by_item:
        print('')
        print('[읽기는 했는데 우리 품목이 하나도 없습니다]')
        print(' 이 도면은 객실관리 도면이 아닐 수도 있고, 기호가 우리 사전과 다를 수도 있습니다.')
        print(' 아래 「사전에 없는 기호」를 저에게 보여주시면 사전에 넣어 드리겠습니다.')

    print('')
    if table:
        print('-- 아래는 참고입니다. 위의 도면 수량표가 정답입니다 --')
    print('%-30s %10s %12s  %s' % ('품목', '블록으로센것', '글자나온횟수', '채택'))
    print('-' * 70)
    rows = []
    for it in sorted(by_item, key=lambda k: -max(by_item[k])):
        b, t = by_item[it]
        # 글자가 나온 횟수는 수량이 아니다. 절대 채택하지 않는다 (km 철칙: 수량을 도구가 정하지 않는다)
        take, why = (b, '블록') if b else (0, '-')
        print('%-30s %10s %12s  %s' % (it[:30], won(b), won(t), why))
        rows.append([it, b, t, take, why])
    if not table and not blocks:
        print('')
        print('[주의] 블록이 없어 채택할 수량이 없습니다.')
        print('  「글자 나온 횟수」는 도면 제목·범례·표제란에 그 낱말이 몇 번 나왔는지일 뿐,')
        print('  기구물 수량이 아닙니다. 그래서 채택하지 않습니다.')
        print('  -> DXF 로 주시거나, 도면의 NOTE(범례) 표 쪽을 보여주십시오.')

    if split_log:
        print('')
        print('-- 이름을 쪼개서 맞춘 것 (맞는지 봐 주십시오) --')
        for w, sym, items, n in split_log[:20]:
            print('  %s  %-24s -> %-28s %6s' % (w, str(sym)[:24], items[:28], won(n)))

    print('')
    print('-- 사전에 없는 기호 (여기가 클로드에게 보여주실 부분입니다) --')
    unk_rows = []
    for name, n in unk_b.most_common(40):
        print('  블록  %-40s %6s' % (str(name)[:40], won(n)))
        unk_rows.append(['블록', name, n])
    for tok, n in unk_t.most_common(30):
        print('  글자  %-40s %6s' % (str(tok)[:40], won(n)))
        unk_rows.append(['글자', tok, n])
    if not unk_rows:
        print('  없음')

    # 4) 현장명 - 폴더/파일 이름에서 짐작해 기본값으로 내민다 (엔터만 누르시면 됩니다)
    g = site_hint or guess_site(files, inbox)
    print('')
    site = ask('현장명 [%s] (엔터=그대로) > ' % g, g) or g

    # 5) 규칙 대조 - 현장대장에 있으면 묻지 않는다
    cmp_rows = []
    star = rooms = floors = 0
    resort = False
    got = None
    try:
        import sitebook
        for d in sitebook.load():
            if norm(d['site']) == norm(site) or norm(site) in norm(d['site']):
                got = d
                break
    except Exception:
        got = None
    if got and str(got.get('star', '')).strip().isdigit():
        star = int(got['star']); rooms = int(got.get('rooms') or 0)
        floors = int(got.get('floors') or 0)
        resort = str(got.get('resort', '')).lower().startswith('y')
        print('현장대장에서 가져왔습니다 : %d성급 / %s실 / %s층%s'
              % (star, won(rooms), won(floors), ' / 리조트' if resort else ''))
    else:
        v = ask('성급(1~5)을 아시면 한 글자만. 규칙값과 대조해 드립니다 (엔터=건너뜀) > ').strip()
        if v.isdigit():
            star = int(v)
            rooms = int(ask('총 객실 수 (모르시면 엔터) > ', '0') or 0)
            floors = int(ask('객실 층 수 (모르시면 엔터) > ', '0') or 0)
    if star:
        import t03_roomqty
        rule = t03_roomqty.calc(star, rooms, resort, 0, 0, 0, floors)
        rule_sum = collections.Counter()
        for r in rule:
            it = match_sym(re.split(r'[ (]', r[0])[0], dic, ign) or r[0]
            rule_sum[it] += int(r[1] or 0)
        print('')
        print('%-34s %10s %10s %10s' % ('품목', '도면', '규칙', '차이'))
        print('-' * 70)
        for it in sorted(set(rule_sum) | set(by_item)):
            b, t = by_item.get(it, [0, 0])
            dn = b or t
            rl = rule_sum.get(it, 0)
            print('%-34s %10s %10s %10s' % (it[:34], won(dn), won(rl), won(dn - rl)))
            cmp_rows.append([it, dn, rl, dn - rl])

    # 6) 파일로 낸다
    od = outdir(TOOL)
    base = '%s_도면수량_%s' % (safe_name(site), ymd6())
    body = [[r[0], r[1], r[2], r[3], r[4]] for r in rows]
    if cmp_rows:
        body += [['', '', '', '', ''], ['[규칙 대조]', '도면', '규칙', '차이', '']]
        body += [[c[0], c[1], c[2], c[3], ''] for c in cmp_rows]
    f1 = write_csv(os.path.join(od, base + '.csv'),
                   [['[현장]', site, '', '', ''], ['[읽은 파일]', len(files), '', '', ''],
                    ['', '', '', '', '']] + body,
                   ['품목', '블록으로센것', '글자나온횟수(수량아님)', '채택수량', '채택근거'])
    made = [f1]
    if table:
        f0 = write_csv(os.path.join(od, '%s_도면에적힌수량표_%s.csv' % (safe_name(site), ymd6())),
                       [[r['sym'], r['name'], r['qty'], '%s쪽' % r['page'], r.get('file', '')]
                        for r in table],
                       ['기호', '내용', '수량', '쪽', '파일'])
        made.insert(0, f0)
    f2 = write_csv(os.path.join(od, '%s_모르는기호_%s.csv' % (safe_name(site), ymd6())),
                   unk_rows, ['어디서', '기호', '횟수'])
    f3 = write_csv(os.path.join(od, '%s_읽은파일_%s.csv' % (safe_name(site), ymd6())),
                   [list(x) for x in per_file], ['파일', '종류', '블록수', '글자수', '비고'])
    made += [f2, f3]
    if split_log:
        write_csv(os.path.join(od, '%s_쪼개서맞춘것_%s.csv' % (safe_name(site), ymd6())),
                  split_log, ['어디서', '도면기호', '맞춘품목', '횟수'])

    hint = []
    if table:
        for r in table:
            hint.append(('green', '%s  %s : %s개 (도면 %s쪽에 적힌 값)'
                         % (r['sym'], r['name'], won(r['qty']), r['page'])))
    for it, b, t, tk, w in rows:
        if tk:
            hint.append(('yellow', '%s : %s (블록으로 센 것)' % (it, won(tk))))
    need_ai = []
    if not table:
        need_ai.append(('red', '계통도(도면)에 수량표가 없습니다. 파이썬이 센 값은 검토용입니다 -> 프로님 수량표를 30번 부탁서로 요청합니다.'))
    if img:
        need_ai.append(('red', '사진/캡처 %d장 - 파이썬으로는 못 셉니다. 클로드에게 주십시오.' % len(img)))
    if scans:
        need_ai.append(('red', '스캔 PDF %d개 - 글자가 없어 못 셉니다. 클로드에게 주십시오.' % len(scans)))
    real_dwg = [f for f in dwg if not is_xref(f)]
    if real_dwg and not oda_exe():
        need_ai.append(('yellow', 'DWG %d개 - 캐드에서 「다른 이름으로 저장 -> DXF」로 주시면 정확히 셉니다.' % len(real_dwg)))
    f4 = write_html(os.path.join(od, base + '.html'), '%s 도면 수량' % site,
                    [('뽑은 수량 (도면에 적힌 값이 있으면 그것이 정답)', hint),
                     ('이름을 쪼개서 맞춘 것 (확인 필요)',
                      [('yellow', '%s %s -> %s : %s개' % (a, b, c, won(d2)))
                       for a, b, c, d2 in split_log[:20]]),
                     ('사전에 없는 기호(클로드에게 보여주실 것)',
                      [('yellow', '%s %s : %s개' % (a, b, won(c))) for a, b, c in unk_rows[:30]]),
                     ('사람/클로드가 봐야 하는 것', need_ai),
                     ('읽은 파일', [('gray', '%s [%s] %s' % (a, b, e)) for a, b, c, d2, e in per_file])],
                    files=made)

    print('')
    print('파일을 만들었습니다. 결과 화면을 지금 띄웁니다.')
    for f in (f1, f2, f3, f4):
        print('  %s' % f)
    print('')
    if table:
        print('* 위 수량은 도면에 적힌 값을 그대로 옮긴 것입니다. 제가 계산하지 않았습니다.')
    else:
        print('* 수량은 제가 정하지 않습니다. 「글자 나온 횟수」는 수량이 아니라 참고입니다.')
    print('* 사전(%s)을 고치시면 다음부터 그 기준으로 셉니다.' % DICT_NAME)
    log(TOOL, '%s 파일%d 품목%d 모르는기호%d' % (site, len(files), len(rows), len(unk_rows)))
    if not open_file(f4):
        open_folder(od)

if __name__ == '__main__':
    run(); pause()

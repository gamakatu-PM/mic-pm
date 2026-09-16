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

GUIDE = '''도면을 여기에 넣으십시오.

[넣는 곳]  이 폴더 안의  _여기에_넣으십시오  폴더

[읽히는 것]
  DXF   가장 정확합니다. 블록 개수를 그대로 셉니다.
  DWG   그대로는 못 읽습니다.
        캐드에서 「다른 이름으로 저장 -> DXF」 로 한 번만 바꿔 주십시오.
        (ODA File Converter 가 깔려 있으면 자동으로 바꿔 읽습니다)
  PDF   글자가 살아 있는 PDF 면 글자를 셉니다.
  사진/캡처   파이썬으로는 못 셉니다. 클로드에게 주셔야 합니다.

[쓰는 법]
  1. 도면을 _여기에_넣으십시오 에 넣는다
  2. 시작.py 를 눌러 메뉴에서 27 을 누른다
  3. 결과는 _도구결과\\도면수량\\ 에 쌓입니다

[기호사전.csv]
  도면에 쓰는 기호와 우리 품목을 잇는 표입니다.
  현장마다 기호가 다르면 이 파일에 한 줄 추가하시면 다음부터 셉니다.
  품목칸에 「무시」 를 넣으면 그 낱말은 아예 안 셉니다.

[수량은 제가 정하지 않습니다]
  블록기준 / 글자기준을 나란히 보여드리고, 어느 쪽을 썼는지 적어 둡니다.
  쪼개서 맞춘 것과 사전에 없는 기호는 따로 뽑아 드리니 확인하고 쓰십시오.
'''

def dwg_root():
    root = cfg('drawing')
    try:
        os.makedirs(os.path.join(root, INBOX), exist_ok=True)
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

def run():
    title('27. 도면 수량 뽑기   (토큰 0 - 내 PC 안에서만 돕니다)')
    root = dwg_root()
    inbox = os.path.join(root, INBOX)
    print('도면 넣는 곳 : %s' % inbox)
    files = gather(inbox)
    if not files:
        files = gather(root)
    if not files:
        print('')
        print('[비어 있습니다] 위 폴더에 도면을 넣고 다시 27번을 누르시면 됩니다.')
        p = ask('\n또는 지금 도면이 있는 폴더/파일 경로를 붙여넣으십시오 (엔터=그만) > ').strip('"')
        if not p:
            print('')
            print('* 폴더를 열어 두겠습니다. 도면을 끌어다 넣으십시오.')
            open_folder(inbox)
            return
        if not os.path.exists(p):
            print('[없는 경로] %s' % p)
            return
        files = gather(p)
        if not files:
            print('[도면 파일이 없습니다] dxf / dwg / pdf / 사진 만 봅니다.')
            return

    dic, ign, dpath = load_dict()
    site = ask('현장명 > ', '현장미정')

    dxf = [f for f in files if os.path.splitext(f)[1].lower() in DXF_EXT]
    dwg = [f for f in files if os.path.splitext(f)[1].lower() in DWG_EXT]
    pdf = [f for f in files if os.path.splitext(f)[1].lower() in PDF_EXT]
    img = [f for f in files if os.path.splitext(f)[1].lower() in IMG_EXT]
    print('')
    print('찾은 파일 : DXF %d / DWG %d / PDF %d / 사진 %d' %
          (len(dxf), len(dwg), len(pdf), len(img)))
    print('기호 사전 : %s  (품목 %d줄 / 무시 %d줄)' % (dpath, len(dic), len(ign)))
    print('-' * 70)

    blocks = collections.Counter()
    toks = collections.Counter()
    per_file = []
    scans = []

    for f in dxf:
        d, msg = read_dxf(f)
        nb = sum(d['blocks'].values()) if d else 0
        nt = len(d['texts']) if d else 0
        per_file.append((os.path.basename(f), 'DXF', nb, nt, msg))
        print(' [DXF] %-40s 블록 %5s / 글자 %5s %s'
              % (os.path.basename(f)[:40], won(nb), won(nt), msg))
        if d:
            blocks.update(d['blocks']); toks.update(tokens(d['texts']))

    for f in dwg:
        conv = dwg_to_dxf(f)
        if conv:
            d, msg = read_dxf(conv)
            nb = sum(d['blocks'].values()) if d else 0
            nt = len(d['texts']) if d else 0
            per_file.append((os.path.basename(f), 'DWG(자동변환)', nb, nt, msg))
            print(' [DWG] %-40s 블록 %5s / 글자 %5s (ODA로 자동변환)'
                  % (os.path.basename(f)[:40], won(nb), won(nt)))
            if d:
                blocks.update(d['blocks']); toks.update(tokens(d['texts']))
        else:
            per_file.append((os.path.basename(f), 'DWG', 0, 0, 'DWG는 그대로 못 읽습니다'))
            print(' [DWG] %-40s 못 읽었습니다' % os.path.basename(f)[:40])

    for f in pdf:
        d, msg = read_pdf(f)
        nt = len(d['texts']) if d else 0
        per_file.append((os.path.basename(f), 'PDF', 0, nt, msg))
        print(' [PDF] %-40s 글자 %5s %s' % (os.path.basename(f)[:40], won(nt), msg))
        if d:
            toks.update(tokens(d['texts']))
            if d.get('scan'):
                scans.append(f)

    for f in img:
        per_file.append((os.path.basename(f), '사진/캡처', 0, 0, '파이썬으로는 못 셉니다'))

    by_item, unk_b, unk_t, split_log = tally(blocks, toks, dic, ign)

    print('')
    print('%-34s %10s %10s  %s' % ('품목', '블록기준', '글자기준', '채택'))
    print('-' * 70)
    rows = []
    for it in sorted(by_item, key=lambda k: -max(by_item[k])):
        b, t = by_item[it]
        take, why = (b, '블록') if b else ((t, '글자') if t else (0, '-'))
        print('%-34s %10s %10s  %s' % (it[:34], won(b), won(t), why))
        rows.append([it, b, t, take, why])
    if not rows:
        print('(사전에 맞는 기호를 하나도 못 찾았습니다. 아래 「모르는 기호」를 보십시오.)')

    if split_log:
        print('')
        print('-- 이름을 쪼개서 맞춘 것 (맞는지 봐 주십시오) --')
        for where, sym, items, n in split_log[:20]:
            print('  %s  %-24s -> %-28s %6s' % (where, str(sym)[:24], items[:28], won(n)))

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

    # 성급 규칙과 대조 (알고 계시면)
    cmp_rows = []
    s = ask('\n성급(1~5)을 아시면 넣으십시오. 규칙 계산값과 대조해 드립니다 (엔터=건너뜀) > ').strip()
    if s.isdigit():
        star = int(s)
        rooms = int(ask('총 객실 수 > ', '0') or 0)
        floors = int(ask('객실 층 수 (모르시면 0) > ', '0') or 0)
        resort = ask('리조트입니까? (y/n) > ', 'n').lower().startswith('y')
        import t03_roomqty
        rule = t03_roomqty.calc(star, rooms, resort, 0, 0, 0, floors)
        rule_sum = collections.Counter()
        for r in rule:
            it = match_sym(re.split(r'[ (]', r[0])[0], dic, ign) or r[0]
            rule_sum[it] += int(r[1] or 0)
        print('')
        print('%-34s %10s %10s %10s' % ('품목', '도면', '규칙', '차이'))
        print('-' * 70)
        keys = set(rule_sum) | set(by_item)
        for it in sorted(keys):
            b, t = by_item.get(it, [0, 0])
            dwgn = b or t
            rl = rule_sum.get(it, 0)
            print('%-34s %10s %10s %10s' % (it[:34], won(dwgn), won(rl), won(dwgn - rl)))
            cmp_rows.append([it, dwgn, rl, dwgn - rl])

    od = outdir(TOOL)
    base = '%s_도면수량_%s' % (safe_name(site), ymd6())
    f1 = write_csv(os.path.join(od, base + '.csv'),
                   [['[현장]', site, '', '', ''],
                    ['[읽은 파일]', len(files), '', '', ''], ['', '', '', '', '']] +
                   [[r[0], r[1], r[2], r[3], r[4]] for r in rows] +
                   ([['', '', '', '', ''], ['[규칙 대조]', '도면', '규칙', '차이', '']] +
                    [[c[0], c[1], c[2], c[3], ''] for c in cmp_rows] if cmp_rows else []),
                   ['품목', '블록기준', '글자기준', '채택수량', '채택근거'])
    f2 = write_csv(os.path.join(od, '%s_모르는기호_%s.csv' % (safe_name(site), ymd6())),
                   unk_rows, ['어디서', '기호', '횟수'])
    f3 = write_csv(os.path.join(od, '%s_읽은파일_%s.csv' % (safe_name(site), ymd6())),
                   [list(x) for x in per_file], ['파일', '종류', '블록수', '글자수', '비고'])
    if split_log:
        write_csv(os.path.join(od, '%s_쪼개서맞춘것_%s.csv' % (safe_name(site), ymd6())),
                  split_log, ['어디서', '도면기호', '맞춘품목', '횟수'])

    blocks_hint = []
    for it, b, t, take, why in rows:
        blocks_hint.append(('green' if why == '블록' else 'yellow',
                            '%s : %s (%s기준)' % (it, won(take), why)))
    need_ai = [('red', '사진/캡처 %d장 - 파이썬으로는 못 셉니다. 클로드에게 주십시오.' % len(img))] if img else []
    if scans:
        need_ai.append(('red', '스캔 PDF %d개 - 글자가 없어 못 셉니다. 클로드에게 주십시오.' % len(scans)))
    if dwg and not oda_exe():
        need_ai.append(('yellow', 'DWG %d개 - 캐드에서 「다른 이름으로 저장 → DXF」로 주시면 정확히 셉니다.' % len(dwg)))
    f4 = write_html(os.path.join(od, base + '.html'),
                    '%s 도면 수량' % site,
                    [('뽑은 수량', blocks_hint),
                     ('이름을 쪼개서 맞춘 것 (확인 필요)',
                      [('yellow', '%s %s -> %s : %s개' % (a, b, c, won(d2)))
                       for a, b, c, d2 in split_log[:20]]),
                     ('사전에 없는 기호(클로드에게 보여주실 것)',
                      [('yellow', '%s %s : %s개' % (a, b, won(c))) for a, b, c in unk_rows[:30]]),
                     ('사람/클로드가 봐야 하는 것', need_ai),
                     ('읽은 파일', [('gray', '%s [%s] %s' % (a, b, e)) for a, b, c, d2, e in per_file])])

    print('')
    print('파일 4개를 만들었습니다.')
    for f in (f1, f2, f3, f4):
        print('  %s' % f)
    print('')
    print('* 수량은 제가 정하지 않습니다. 블록기준/글자기준을 나란히 두었으니 확인하고 쓰십시오.')
    print('* 사전(%s)을 고치시면 다음부터 그 기준으로 셉니다.' % DICT_NAME)
    log(TOOL, '%s 파일%d 품목%d 모르는기호%d' % (site, len(files), len(rows), len(unk_rows)))
    open_folder(od)

if __name__ == '__main__':
    run(); pause()

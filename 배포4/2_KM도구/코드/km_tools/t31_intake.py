# -*- coding: utf-8 -*-
"""31. 도면 접수·판 비교 - 현장별 도면 폴더를 지켜보다가 새 도면이 오면 읽고, 이전 판과 증감을 뽑는다. 토큰 0.

폴더 약속 (3_공통사용\\도면\\ 안)
  {현장명}\\            <- 현장마다 폴더 하나. 캐드·PDF·수량표를 그냥 넣어 두시면 됩니다
     _도면대장.csv       <- 31번이 스스로 씁니다 (어느 파일을 언제 몇 판으로 읽었나)
  _여기에_넣으십시오\\   <- 현장 미정인 도면 임시 자리 (판 비교는 안 됩니다)

하는 일
  1) 현장 폴더의 도면 파일을 해시로 기억한다. 못 본 파일 = 새 판
  2) 새 판을 27번 방식으로 읽어 수량표 r{n} 을 낸다 (NOTE 표 > 블록)
  3) 이전 판 r{n-1} 이 있으면 품목별 증감을 뽑는다
  4) 현장마다 「지금 몇 판이고 무엇이 바뀌었나」 한 장을 낸다

파일은 옮기거나 지우지 않습니다. 대장에 적기만 합니다.
"""
import os, re, csv, hashlib, glob, collections, io as _io
from common import *
import t27_drawing as D

TOOL = '도면접수'
LEDGER = '_도면대장.csv'
LHEAD = ['파일', '크기', '해시', '받은날', '판', '읽은날', '비고']
SKIP_DIRS = (D.INBOX, '_처리완료', '_삭제요망', '_이전판')

def sites():
    root = D.dwg_root()
    out = []
    try:
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if os.path.isdir(p) and d not in SKIP_DIRS and not d.startswith(('_', '.')):
                out.append((d, p))
    except Exception:
        pass
    return out

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:12]

def load_ledger(site_dir):
    p = os.path.join(site_dir, LEDGER)
    rows = []
    if os.path.exists(p):
        for i, line in enumerate(read_text(p).splitlines()):
            if not line.strip() or i == 0 or line.startswith('#'):
                continue
            try:
                r = [c.strip() for c in next(csv.reader([line]))]
                rows.append(dict(zip(LHEAD, (r + [''] * 7)[:7])))
            except Exception:
                pass
    return rows

def save_ledger(site_dir, rows):
    p = os.path.join(site_dir, LEDGER)
    write_csv(p, [[r.get(k, '') for k in LHEAD] for r in rows], LHEAD)

def drawing_files(site_dir):
    return [f for f in D.gather(site_dir)
            if not os.path.basename(f).startswith('_')]

def qty_files(site_dir):
    """설계사가 준 수량표(xlsx/csv)가 있으면 같이 읽는다"""
    out = []
    for f in walk_files(site_dir, {'.xlsx', '.csv'}):
        b = os.path.basename(f)
        if b.startswith(('_', '~$')):
            continue
        if any(k in b for k in ('수량', 'BOM', 'bom', '물량')):
            out.append(f)
    return out

# ---------------- 읽기 ----------------

def extract(files):
    """새 판 파일들 -> {품목: 수량}. NOTE 표가 있으면 그것, 없으면 블록."""
    dic, ign, _ = D.load_dict()
    blocks, toks, per_file, scans, unread, table = D.read_all(files)
    q = collections.OrderedDict()
    src = ''
    if table:
        for r in table:
            k = '%s %s' % (r['sym'], r['name']) if r['sym'] else r['name']
            q[k] = q.get(k, 0) + r['qty']
        src = 'NOTE표'
    elif blocks:
        by_item, unk_b, unk_t, split_log = D.tally(blocks, toks, dic, ign)
        for it, (b, t) in by_item.items():
            if b:
                q[it] = b
        src = '블록'
    return q, src, per_file, unread

def read_qty_file(path):
    """설계사 수량표(xlsx/csv) : 첫 글자칸=품목, 뒤쪽 숫자칸=수량"""
    q = collections.OrderedDict()
    rows = []
    if path.lower().endswith('.csv'):
        for line in read_text(path).splitlines():
            try:
                rows.append([c.strip() for c in next(csv.reader([line]))])
            except Exception:
                pass
    else:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
            for ws in wb.worksheets:
                for r in ws.iter_rows(values_only=True):
                    rows.append(['' if c is None else str(c).strip() for c in r])
            wb.close()
        except Exception:
            return q
    for r in rows:
        nm, qty = '', None
        for c in r:
            try:
                v = float(str(c).replace(',', ''))
                if v > 0 and v.is_integer():
                    qty = int(v)
            except Exception:
                if len(c) >= 2 and not nm:
                    nm = c
        if nm and qty:
            q[nm] = q.get(nm, 0) + qty
    return q

# ---------------- 비교 ----------------

def diff(prev, cur):
    keys = list(cur.keys()) + [k for k in prev if k not in cur]
    out = []
    for k in keys:
        a, b = prev.get(k, 0), cur.get(k, 0)
        if a != b:
            out.append([k, a, b, b - a, '추가' if a == 0 else ('삭제' if b == 0 else ('증' if b > a else '감'))])
    return out

def prev_rev_file(site, rev):
    od = os.path.join(cfg('out'), TOOL, safe_name(site))
    for r in range(rev - 1, 0, -1):
        hit = glob.glob(os.path.join(od, '%s_수량_r%d_*.csv' % (safe_name(site), r)))
        if hit:
            return r, hit[0]
    return None, None

def load_rev(path):
    q = collections.OrderedDict()
    for i, line in enumerate(read_text(path).splitlines()):
        if i == 0 or not line.strip():
            continue
        try:
            r = [c.strip() for c in next(csv.reader([line]))]
            q[r[0]] = int(float(r[1]))
        except Exception:
            pass
    return q

# ---------------- 받은함 자동 분류 ----------------

SITE_PAT = re.compile(r'\[(.{2,20}?)\]')

def guess_site_from_name(name):
    """파일명의 [현장명] 을 읽는다. 없으면 현장대장 이름이 파일명에 들어 있는지 본다."""
    m = SITE_PAT.search(name)
    if m:
        return m.group(1).strip()
    try:
        import sitebook
        for d in sitebook.load():
            if d['site'] and norm_(d['site']) in norm_(name):
                return d['site']
    except Exception:
        pass
    return None

def sort_inbox():
    """_여기에_넣으십시오 의 도면을 현장 폴더로 옮긴다. 현장을 못 알아보면 그대로 둔다.
    옮기는 것은 C등급이라 묻는다 (32번 자동 모드에서는 알리고 옮긴다)."""
    root = D.dwg_root()
    inbox = os.path.join(root, D.INBOX)
    files = D.gather(inbox)
    if not files:
        return []
    plan, unknown = [], []
    for f in files:
        site = guess_site_from_name(os.path.basename(f))
        (plan if site else unknown).append((f, site))
    if unknown:
        print('받은함에 현장을 못 알아본 도면 %d개 (파일명에 [현장명] 을 넣어 주십시오)' % len(unknown))
        for f, _ in unknown[:8]:
            print('   %s' % os.path.basename(f))
    if not plan:
        return []
    print('받은함 -> 현장 폴더로 옮길 도면 %d개' % len(plan))
    for f, site in plan:
        print('   %-44s -> %s\\' % (os.path.basename(f)[:44], site))
    if not ask('옮길까요? (y=엔터 / n) > ', 'y').lower().startswith('y'):
        return []
    import shutil
    moved = []
    for f, site in plan:
        dst_dir = os.path.join(root, safe_name(site))
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(f))
        if os.path.exists(dst):
            stem, ext = os.path.splitext(os.path.basename(f))
            dst = os.path.join(dst_dir, '%s_%s%s' % (stem, ymd6(), ext))
        try:
            shutil.move(f, dst)
            moved.append((site, dst))
        except Exception as e:
            print('   [못 옮김] %s : %s' % (os.path.basename(f), e))
    if moved:
        log(TOOL, '받은함 분류 %d개' % len(moved))
    return moved

# ---------------- 현장 하나 ----------------

def process_site(site, site_dir, force=False):
    led = load_ledger(site_dir)
    known = {r['해시'] for r in led}
    files = drawing_files(site_dir)
    new = []
    for f in files:
        try:
            h = md5(f)
        except Exception:
            continue
        if h not in known or force:
            new.append((f, h))
    revs = [int(r['판']) for r in led if str(r['판']).isdigit()]
    cur_rev = max(revs) if revs else 0
    print('')
    print('[%s]  도면 %d개 / 지금까지 %d판 / 새 파일 %d개' % (site, len(files), cur_rev, len(new)))
    if not new:
        return None
    rev = cur_rev + 1
    q, src, per_file, unread = extract([f for f, h in new])
    # 설계사 수량표가 있으면 같이 (도면에서 못 뽑았을 때 대신 쓴다)
    qf = qty_files(site_dir)
    q2 = collections.OrderedDict()
    for f in qf:
        q2.update(read_qty_file(f))
    if not q and q2:
        q, src = q2, '설계사 수량표'
    od = os.path.join(cfg('out'), TOOL, safe_name(site))
    os.makedirs(od, exist_ok=True)
    made = []
    for f, h in new:
        led.append({'파일': os.path.basename(f), '크기': os.path.getsize(f), '해시': h,
                    '받은날': datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat(),
                    '판': rev, '읽은날': today().isoformat(),
                    '비고': src or '못 읽음'})
    save_ledger(site_dir, led)
    for f, kind, nb, nt, msg in per_file:
        print('   [%s] %-40s %s' % (kind, f[:40], msg))
    if not q:
        print('   -> 읽을 수 있는 수량이 없습니다 (사진·스캔·DWG). 클로드에게 넘길 목록으로 남깁니다.')
        write_csv(os.path.join(od, '%s_r%d_못읽음_%s.csv' % (safe_name(site), rev, ymd6())),
                  [[a, b] for a, b in unread], ['파일', '왜'])
        return {'site': site, 'rev': rev, 'src': '', 'items': 0, 'diff': [], 'made': made, 'unread': unread}
    p = os.path.join(od, '%s_수량_r%d_%s.csv' % (safe_name(site), rev, ymd6()))
    write_csv(p, [[k, v] for k, v in q.items()], ['품목', '수량'])
    made.append(p)
    print('   -> r%d 수량표 %d품목 (%s에서)' % (rev, len(q), src))
    d = []
    pr, pf = prev_rev_file(site, rev)
    if pf:
        prev = load_rev(pf)
        d = diff(prev, q)
        p2 = os.path.join(od, '%s_증감_r%d_r%d_%s.csv' % (safe_name(site), pr, rev, ymd6()))
        write_csv(p2, d, ['품목', 'r%d' % pr, 'r%d' % rev, '증감', '구분'])
        made.append(p2)
        print('   -> r%d 대비 바뀐 품목 %d개' % (pr, len(d)))
        for k, a, b, c, g in d[:12]:
            print('      %-36s %6s -> %6s  (%+d) %s' % (k[:36], won(a), won(b), c, g))
    return {'site': site, 'rev': rev, 'prev': pr, 'src': src, 'items': len(q),
            'diff': d, 'made': made, 'unread': unread, 'q': q}

# ---------------- 실행 ----------------

def run(site_hint=None):
    title('31. 도면 접수 · 판 비교   (현장 폴더에 새 도면이 오면 읽고 증감. 토큰 0)')
    root = D.dwg_root()
    sort_inbox()
    ss = sites()
    print('도면 폴더 : %s' % root)
    if not ss:
        print('')
        print('[현장 폴더가 없습니다] 도면 폴더 안에 현장 이름으로 폴더를 만들고 도면을 넣어주십시오.')
        print('   예)  %s' % os.path.join(root, '앵커호텔'))
        print('   그 안에 캐드·PDF·수량표를 그냥 넣어 두시면, 31번이 새 파일을 알아서 찾습니다.')
        open_folder(root)
        return
    if site_hint:
        ss = [(n, p) for n, p in ss if norm_(n) == norm_(site_hint)] or ss
    print('현장 %d개 : %s' % (len(ss), ', '.join(n for n, p in ss)))
    results = []
    for name, p in ss:
        r = process_site(name, p)
        if r:
            results.append(r)
    od = outdir(TOOL)
    if not results:
        print('')
        print('새 도면이 없습니다. 지난번에 읽은 것과 같습니다.')
    blocks = []
    for r in results:
        rows = [('green', 'r%d 수량표 %d품목 (%s)' % (r['rev'], r['items'], r['src'] or '못 읽음'))]
        for k, a, b, c, g in r['diff'][:30]:
            rows.append(('red' if c < 0 else 'blue', '%s : %s -> %s (%+d) %s' % (k, won(a), won(b), c, g)))
        if r.get('prev') and not r['diff']:
            rows.append(('gray', 'r%d 와 수량이 같습니다' % r['prev']))
        for a, b in r['unread'][:10]:
            rows.append(('yellow', '못 읽음 : %s (%s)' % (a, b)))
        blocks.append(('%s  (새 판 r%d)' % (r['site'], r['rev']), rows))
    if not blocks:
        blocks = [('새 도면', [('gray', '없음')])]
    allmade = [m for r in results for m in r['made']]
    f9 = write_html(os.path.join(od, '도면접수_%s.html' % ymd6()), '도면 접수 · 판 비교', blocks, files=allmade)
    print('')
    print('  %s' % f9)
    log(TOOL, '현장%d 새판%d' % (len(ss), len(results)))
    if results and not open_file(f9):
        open_folder(od)
    return results

def norm_(s):
    return re.sub(r'[^0-9A-Za-z가-힣]', '', str(s or '')).upper()

if __name__ == '__main__':
    run(); pause()

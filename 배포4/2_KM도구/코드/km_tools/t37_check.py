# -*- coding: utf-8 -*-
"""37. 검수 - 클로드(또는 도구)가 만든 엑셀 산출물이 정답본대로 됐는지 파이썬이 검사한다. 토큰 0.

순서 (프로님 지시 2026-09-16)
  1) 간단 검수  : 시트 이름·순서, 머리글, 깨진 참조, 합계 하드코딩, 노란칸 규칙, 검산 셀
  2) 이상하면 제대로 검수 : 고정 라벨 전수 대조, 수식 독립 재계산(합계·검산), 수량 원본(CSV) 대조
  3) 잘못됐으면 「고쳐도 될까요?」 를 묻는다. y 면 스스로 고칠 수 있는 것(시트 이름·순서, 빈 단가칸 노랑, 검산 행)만
     새 버전 파일로 고치고, 나머지는 「_클로드부탁서_검수_*.md」 로 클로드에게 넘긴다. 원본은 덮어쓰지 않는다.

정답본 : 3_공통사용\\원틀\\정답본\\_정답본.csv  (종류, 정답본 파일, 필수 시트, 검산 셀)
         정답본 파일(주일능 v7 실행산출 등)을 그 폴더에 넣어두면 종류를 스스로 고른다.
"""
import os, re, csv, glob, shutil, collections, io as _io
from common import *

TOOL = '검수'
GDIR = '정답본'
GREG = '_정답본.csv'
YELLOWS = ('FFF2A8', 'FFF2CC', 'FFF7CC', 'FFFF00', 'FFFFCC')
GREG_DEFAULT = [
 ['# 정답본 등록부. 종류별로 「이 모양이어야 한다」 는 파일을 적습니다. 파일은 이 폴더에 넣으십시오.', '', '', ''],
 ['종류', '정답본파일(포함되면)', '필수시트(|로 구분, 비우면 정답본 시트 그대로)', '검산셀(시트!열 - 비우면 「검산」 글자로 찾음)'],
 ['실행산출', '주일능_실행산출_v5', '', '3.견적↔실행 대조!I'],
 ['견적서', '광희동1가_견적서', '갑지|내역서', ''],
 ['통합견적', '양양쏠비치', '', ''],
]

# ---------------- 정답본 ----------------

def gdir():
    p = os.path.join(cfg('template'), GDIR)
    os.makedirs(p, exist_ok=True)
    reg = os.path.join(p, GREG)
    if os.path.exists(reg):
        # v21 이전 기본값(주일능_실행산출 → v7 도 잡힘)을 프로님 기준(v5_260828)으로 승격
        try:
            t = read_text(reg)
            if '주일능_실행산출_v5' not in t and '주일능_실행산출,' in t:
                t2 = t.replace('주일능_실행산출,', '주일능_실행산출_v5,')
                for enc in ('cp949', 'utf-8-sig'):
                    try:
                        with _io.open(reg, 'w', encoding=enc, newline='', errors='strict') as fp: fp.write(t2)
                        break
                    except Exception:
                        continue
        except Exception:
            pass
    if not os.path.exists(reg):
        for enc in ('cp949', 'utf-8-sig'):
            try:
                with _io.open(reg, 'w', encoding=enc, newline='', errors='strict') as fp:
                    w = csv.writer(fp)
                    for r in GREG_DEFAULT: w.writerow(r)
                break
            except Exception:
                continue
    return p

def registry():
    out = []
    for line in read_text(os.path.join(gdir(), GREG)).splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        r = [c.strip() for c in next(csv.reader([line]))]
        if len(r) >= 2 and r[0] != '종류':
            out.append({'kind': r[0], 'file': r[1], 'sheets': [s for s in (r[2] if len(r) > 2 else '').split('|') if s],
                        'check': r[3] if len(r) > 3 else ''})
    return out

def find_golden(entry):
    """등록부 이름이 들어간 파일. 여러 개면(v5·v7 같이 있을 때) 등록부에 적힌 글자와 더 길게 맞는 것 > 최신 수정."""
    hits = [p for p in glob.glob(os.path.join(gdir(), '*.xlsx'))
            if entry['file'] and entry['file'] in os.path.basename(p) and not os.path.basename(p).startswith('~$')]
    if not hits:
        return None
    hits.sort(key=lambda p: (-len(os.path.commonprefix([os.path.basename(p), entry['file']])), -os.path.getmtime(p)))
    return hits[0]

def sheet_norm(n):
    return re.sub(r'\s+', '', str(n))

def pick_kind(target_wb):
    """대상 파일의 시트 이름이 어느 정답본과 가장 닮았나"""
    best = None
    tn = {sheet_norm(s) for s in target_wb.sheetnames}
    for e in registry():
        g = find_golden(e)
        if not g:
            continue
        import openpyxl
        gw = openpyxl.load_workbook(g, read_only=True)
        gn = {sheet_norm(s) for s in gw.sheetnames}
        gw.close()
        score = len(tn & gn) / float(max(len(gn), 1))
        if best is None or score > best[0]:
            best = (score, e, g)
    return best

# ---------------- 수식 계산기 (부분집합) ----------------

class Calc:
    """=A1*B2, SUM(범위), ROUND(x,0), +,-,*,/, 다른 시트 참조 만 계산한다. 나머지는 None(확인불가)."""
    REF = re.compile(r"(?:'([^']+)'|([A-Za-z0-9가-힣._↔ ]+))?!?\$?([A-Z]{1,3})\$?(\d+)")
    def __init__(self, wb):
        self.wb = wb; self.cache = {}
    def val(self, ws, ref):
        key = (ws.title, ref)
        if key in self.cache:
            return self.cache[key]
        self.cache[key] = None
        try:
            v = ws[ref].value
        except Exception:
            return None
        if isinstance(v, str) and v.startswith('='):
            v = self.eval(ws, v[1:])
        elif isinstance(v, str):
            try: v = float(v.replace(',', ''))
            except Exception: v = 0 if v.strip() == '' else None
        elif v is None:
            v = 0
        self.cache[key] = v
        return v
    def rng(self, ws, a, b):
        from openpyxl.utils import range_boundaries
        c1, r1, c2, r2 = range_boundaries('%s:%s' % (a, b))
        out = []
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                from openpyxl.utils import get_column_letter
                out.append(self.val(ws, '%s%d' % (get_column_letter(c), r)))
        return out
    def eval(self, ws, expr):
        e = expr.strip()
        if any(k in e.upper() for k in ('IF(', 'CONCATENATE', 'TEXT(', 'COUNTBLANK', 'N(')):
            return None
        # 시트 참조 치환
        def sub_ref(m):
            sheet = m.group(1) or m.group(2)
            col, row = m.group(3), m.group(4)
            w = ws
            if sheet:
                nm = None
                for s in self.wb.sheetnames:
                    if sheet_norm(s) == sheet_norm(sheet):
                        nm = s; break
                if nm is None:
                    raise ValueError('없는 시트 ' + sheet)
                w = self.wb[nm]
            v = self.val(w, '%s%s' % (col, row))
            if v is None:
                raise ValueError('확인불가')
            return '(%r)' % float(v)
        def sub_sum(m):
            body = m.group(1)
            parts = [p.strip() for p in body.split(',')]
            tot = 0.0
            for p in parts:
                if ':' in p:
                    sheet, cells = (p.split('!') + [None])[:2] if '!' in p else (None, p)
                    if sheet is not None and cells is None:
                        cells = sheet; sheet = None
                    w = ws
                    if sheet:
                        sheet = sheet.strip("'")
                        w = next((self.wb[s] for s in self.wb.sheetnames if sheet_norm(s) == sheet_norm(sheet)), None)
                        if w is None: raise ValueError('없는 시트')
                    a, b = cells.replace('$', '').split(':')
                    vs = self.rng(w, a, b)
                    if any(v is None for v in vs): raise ValueError('확인불가')
                    tot += sum(v for v in vs if isinstance(v, (int, float)))
                else:
                    tot += float(self.eval(ws, p) or 0)
            return '(%r)' % tot
        try:
            e2 = re.sub(r'SUM\(([^()]*)\)', sub_sum, e, flags=re.I)
            e2 = re.sub(r'ROUND\(', 'round(', e2)
            e2 = self.REF.sub(sub_ref, e2)
            e2 = e2.replace('^', '**')
            if not re.match(r'^[\d\s\.\+\-\*/\(\),roundeE]+$', e2):
                return None
            return eval(e2, {'__builtins__': {}}, {'round': round})
        except Exception:
            return None

# ---------------- 검수 ----------------

def load(p):
    import openpyxl
    return openpyxl.load_workbook(p)

def headers(ws, n=6):
    """앞 n행 중 글자 칸이 4개 이상인 첫 행 = 머리글"""
    for r in range(1, min(ws.max_row or 1, n) + 1):
        cells = [str(ws.cell(r, c).value or '').strip() for c in range(1, min(ws.max_column or 1, 16) + 1)]
        if sum(1 for c in cells if c) >= 4:
            return r, [sheet_norm(c) for c in cells]
    return None, []

def is_yellow(cell):
    try:
        rgb = str(cell.fill.fgColor.rgb)
        return any(rgb.endswith(y) for y in YELLOWS)
    except Exception:
        return False

def label_cells(ws):
    out = []
    for r in range(1, (ws.max_row or 0) + 1):
        for c in (1, 2):
            v = ws.cell(r, c).value
            if isinstance(v, str) and (v[:1] in '▣■◆▷★' or any(k in v for k in ('소계', '합계', 'TOTAL', '검산', '대수'))):
                out.append((sheet_norm(v)[:24], r))
    return out

def quick(tp, gp):
    """간단 검수 -> (판정, 발견목록). 판정 : 통과 / 이상 / 잘못"""
    tw, gw = load(tp), load(gp)
    finds = []
    # 1 시트
    ts, gs = [sheet_norm(s) for s in tw.sheetnames], [sheet_norm(s) for s in gw.sheetnames]
    if ts != gs:
        miss = [s for s in gs if s not in ts]; extra = [s for s in ts if s not in gs]
        finds.append(('잘못' if miss else '이상', '시트', '정답본 %s / 대상 %s%s%s' % (gs, ts, ' 빠짐:%s' % miss if miss else '', ' 남음:%s' % extra if extra else '')))
    # 2 머리글
    for gname in gw.sheetnames:
        tname = next((s for s in tw.sheetnames if sheet_norm(s) == sheet_norm(gname)), None)
        if not tname:
            continue
        gr, gh = headers(gw[gname]); tr, th = headers(tw[tname])
        if gh and th:
            gset = [x for x in gh if x]; tset = [x for x in th if x]
            def has(h):
                return any(t.startswith(h[:6]) or h.startswith(t[:6]) for t in tset)
            miss = [h for h in gset if not has(h)]
            if len(miss) > max(0, len(gset) // 5):
                finds.append(('잘못', '머리글', '「%s」 정답본 머리글 중 대상에 없는 것 %s' % (gname, miss[:6])))
            elif miss:
                finds.append(('이상', '머리글', '「%s」 머리글 %s 이(가) 대상에 없음 (열 추가는 허용)' % (gname, miss)))
    # 3 깨진 참조 / 없는 시트 참조
    names = {sheet_norm(s) for s in tw.sheetnames}
    for ws in tw.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and v.startswith('='):
                    if '#REF' in v:
                        finds.append(('잘못', '참조', '%s!%s #REF' % (ws.title, c.coordinate)))
                    for m in re.finditer(r"'([^']+)'!", v):
                        if sheet_norm(m.group(1)) not in names:
                            finds.append(('잘못', '참조', '%s!%s -> 없는 시트 %s' % (ws.title, c.coordinate, m.group(1))))
    # 4 합계·소계·TOTAL 하드코딩
    for ws in tw.worksheets:
        for r in range(1, (ws.max_row or 0) + 1):
            lab = ' '.join(str(ws.cell(r, c).value or '') for c in (1, 2))
            if any(k in lab for k in ('소계', '합계', 'TOTAL')) and '표기' not in lab:
                nums = [ws.cell(r, c) for c in range(3, (ws.max_column or 0) + 1)
                        if isinstance(ws.cell(r, c).value, (int, float))]
                if nums:
                    finds.append(('이상', '하드코딩', '%s %d행 「%s」 에 수식 아닌 숫자 %d칸' % (ws.title, r, lab[:20], len(nums))))
    # 5 노란칸 규칙 : 노랑인데 숫자 (허용되지만 목록) / 단가 빈칸인데 노랑 아님
    for ws in tw.worksheets:
        gr, gh = headers(ws)
        if not gh:
            continue
        price_cols = [i + 1 for i, h in enumerate(gh) if '단가' in h or '실행가' in h]
        for r in range((gr or 1) + 1, (ws.max_row or 0) + 1):
            for c in price_cols:
                cell = ws.cell(r, c)
                lab = str(ws.cell(r, 1).value or ws.cell(r, 2).value or '')
                if not lab or any(k in lab for k in ('소계', '합계', 'TOTAL', '검산', '대수', '참고')):
                    continue
                if cell.value in (None, '') and not is_yellow(cell) and any(isinstance(ws.cell(r, k).value, (int, float, str)) for k in (4, 5)):
                    finds.append(('이상', '노란칸', '%s!%s 단가 빈칸인데 노랑 아님 (%s)' % (ws.title, cell.coordinate, lab[:18])))
    # 5-2 노란 빈칸(단가 미입력) 개수 — 남아 있으면 통과가 아니다
    blanks = []
    for ws in tw.worksheets:
        gr, gh = headers(ws)
        ans_cols = {i + 1 for i, h in enumerate(gh or []) if '답' in str(h)}   # 「차장님 답」 칸은 단가가 아니다
        for row in ws.iter_rows():
            for cell in row:
                if cell.column in ans_cols:
                    continue
                if cell.value in (None, '') and is_yellow(cell):
                    lab = str(ws.cell(cell.row, 1).value or ws.cell(cell.row, 2).value or '')[:24]
                    blanks.append('%s!%s %s' % (ws.title, cell.coordinate, lab))
    if blanks:
        finds.append(('이상', '빈칸', '단가 미입력 노란칸 %d개 : %s' % (len(blanks), ' / '.join(blanks[:6]))))
    # 6 검산 셀
    has_chk = any(any('검산' in str(ws.cell(r, c).value or '') for c in (1, 2)) for ws in tw.worksheets for r in range(1, (ws.max_row or 0) + 1))
    g_chk = any(any('검산' in str(ws.cell(r, c).value or '') for c in (1, 2)) for ws in gw.worksheets for r in range(1, (ws.max_row or 0) + 1))
    if g_chk and not has_chk:
        finds.append(('잘못', '검산', '정답본에는 「검산」 행이 있는데 대상에는 없음'))
    verdict = '통과'
    if any(f[0] == '잘못' for f in finds): verdict = '잘못'
    elif finds: verdict = '이상'
    return verdict, finds

def deep(tp, gp, qty_csv=None):
    tw, gw = load(tp), load(gp)
    finds = []
    # A 고정 라벨 전수 (정답본 라벨이 대상에 있는가, 순서 유지)
    for gname in gw.sheetnames:
        tname = next((s for s in tw.sheetnames if sheet_norm(s) == sheet_norm(gname)), None)
        if not tname:
            continue
        gl = [l for l, r in label_cells(gw[gname])]
        tl = [l for l, r in label_cells(tw[tname])]
        miss = [l for l in gl if not any(l[:8] == t[:8] for t in tl)]
        if miss:
            finds.append(('이상', '라벨', '「%s」 정답본에 있는 고정 줄이 대상에 없음: %s' % (gname, miss[:6])))
    # B 수식 독립 재계산 : 합계/소계/TOTAL/검산 행
    calc = Calc(tw)
    for ws in tw.worksheets:
        for r in range(1, (ws.max_row or 0) + 1):
            lab = ' '.join(str(ws.cell(r, c).value or '') for c in (1, 2))
            if not any(k in lab for k in ('소계', '합계', 'TOTAL', '검산')):
                continue
            for c in range(3, (ws.max_column or 0) + 1):
                v = ws.cell(r, c).value
                if isinstance(v, str) and v.startswith('='):
                    got = calc.eval(ws, v[1:])
                    if got is None:
                        continue
                    if '검산' in lab and abs(got) > 0.5:
                        finds.append(('잘못', '검산', '%s!%s 검산 = %s (0 이어야 함)' % (ws.title, ws.cell(r, c).coordinate, won(got))))
                    elif 'TOTAL' in lab or '합계' in lab:
                        # 합계 수식이 순번 있는 줄을 다 더하는가 (참조 3개 이상인 진짜 합계 수식만)
                        m = re.findall(r'([A-Z]+)(\d+)', v)
                        if len(m) < 3:
                            continue
                        rows_in = {int(x[1]) for x in m}
                        numbered = {rr for rr in range(1, r) if isinstance(ws.cell(rr, 1).value, (int, float))}
                        if numbered and 'SUM(' not in v.upper() and not numbered <= rows_in:
                            finds.append(('잘못', '누락', '%s %d행 합계 수식이 순번 줄 %s 을 안 더함' % (ws.title, r, sorted(numbered - rows_in)[:8])))
    # C 수량 원본 대조
    if qty_csv and os.path.exists(qty_csv):
        src = {}
        for i, line in enumerate(read_text(qty_csv).splitlines()):
            if i == 0 or not line.strip(): continue
            try:
                cells = [x.strip() for x in next(csv.reader([line]))]
            except Exception:
                continue
            nm = max((x for x in cells if not re.match(r'^[\d,\.]+$', x or '0')), key=len, default='')
            q = next((float(x.replace(',', '')) for x in cells if re.match(r'^[\d,]+$', x or '')), None)
            if nm and q: src[sheet_norm(nm).upper()] = q
        for ws in tw.worksheets:
            gr, gh = headers(ws)
            if not gh or '수량' not in gh: continue
            qc = gh.index('수량') + 1
            for r in range((gr or 1) + 1, (ws.max_row or 0) + 1):
                nm = sheet_norm(str(ws.cell(r, 2).value or '')).upper()
                q = ws.cell(r, qc).value
                if not nm or not isinstance(q, (int, float)): continue
                hit = next((k for k in src if k in nm or nm in k), None)
                if hit and abs(src[hit] - q) > 0.5:
                    finds.append(('잘못', '수량', '%s %d행 %s : 원본 %s / 대상 %s' % (ws.title, r, nm[:20], won(src[hit]), won(q))))
    verdict = '통과'
    if any(f[0] == '잘못' for f in finds): verdict = '잘못'
    elif finds: verdict = '이상'
    return verdict, finds

# ---------------- 고치기 (할 수 있는 것만) ----------------

def autofix(tp, gp, finds):
    """시트 이름·순서 / 빈 단가칸 노랑 / 검산 행 만 스스로 고친다. 새 파일로."""
    from openpyxl.styles import PatternFill
    tw, gw = load(tp), load(gp)
    done = []
    gs = gw.sheetnames
    for gname in gs:
        for s in tw.sheetnames:
            if sheet_norm(s) == sheet_norm(gname) and s != gname:
                tw[s].title = gname; done.append('시트 이름 %s -> %s' % (s, gname))
    order = [s for s in gs if s in tw.sheetnames] + [s for s in tw.sheetnames if s not in gs]
    if order != tw.sheetnames:
        tw._sheets = [tw[s] for s in order]; done.append('시트 순서 정답본대로')
    for f in finds:
        if f[1] == '노란칸':
            m = re.match(r'(.+?)!([A-Z]+\d+)', f[2])
            if m and m.group(1) in tw.sheetnames:
                tw[m.group(1)][m.group(2)].fill = PatternFill('solid', fgColor='FFF2CC'); done.append('노랑 %s' % f[2][:20])
    if not done:
        return None, []
    d, b = os.path.split(tp); stem, ext = os.path.splitext(b)
    stem = re.sub(r'(_검수고침\d*)$', '', stem)
    out = os.path.join(d, '%s_검수고침_%s%s' % (stem, ymd6(), ext))
    tw.save(out)
    return out, done

# ---------------- 실행 ----------------

def latest_xlsx():
    cands = []
    for root in (cfg('out'), os.path.join(cfg('base'), '4_받은파일'), cfg('handover')):
        if os.path.isdir(root):
            cands += [p for p in walk_files(root, {'.xlsx'}) if not os.path.basename(p).startswith('~$') and '정답본' not in p]
    cands.sort(key=os.path.getmtime, reverse=True)
    return cands[:8]

def inspect(tp, qty_csv=None, ask_fix=True, quiet=False):
    """한 파일 검수. 돌아오는 값 : (판정, 발견, 고친파일)"""
    import openpyxl
    tw = openpyxl.load_workbook(tp, read_only=True)
    best = pick_kind(tw); tw.close()
    if not best:
        print('[정답본 없음] %s 에 정답본 xlsx 가 없습니다.' % gdir())
        return '정답본없음', [], None
    score, entry, gp = best
    if score < 0.5:
        print('대상   : %s' % os.path.basename(tp))
        print('정답본 : 어느 것과도 시트가 안 닮음 (가장 가까운 %s 와 %d%%)' % (entry['kind'], int(score * 100)))
        print('')
        print('✖ 서식 자체가 다릅니다. 이 파일은 %s 정답본 모양이 아닙니다.' % entry['kind'])
        print('  (오늘 낸 「견적서 서식 실행산출」「자체 서식 v2」 가 이 경우였습니다)')
        od = outdir(TOOL)
        tag = '%s_%s' % (safe_name(os.path.splitext(os.path.basename(tp))[0])[:40], ymd6())
        write_csv(os.path.join(od, '검수_%s.csv' % tag), [['잘못', '서식', '정답본과 시트가 안 닮음']], ['수준', '항목', '내용'])
        pth = os.path.join(od, '_클로드부탁서_검수_%s.md' % tag)
        _io.open(pth, 'w', encoding='utf-8').write('# 검수 부탁서 - %s\n\n서식 자체가 정답본(%s)과 다릅니다. 정답본 파일을 복사해 내용만 바꿔 새 버전으로 다시 내 주십시오.\n' % (os.path.basename(tp), os.path.basename(gp)))
        print('  클로드 부탁서 : %s' % pth)
        log(TOOL, '%s 잘못(서식)' % os.path.basename(tp)[:30])
        return '잘못', [('잘못', '서식', '정답본과 시트가 안 닮음')], None
    print('대상   : %s' % os.path.basename(tp))
    print('정답본 : %s  (종류 %s, 시트 닮음 %d%%)' % (os.path.basename(gp), entry['kind'], int(score * 100)))
    v1, f1 = quick(tp, gp)
    print('')
    print('[1] 간단 검수 : %s  (%d건)' % (v1, len(f1)))
    for lv, kind, msg in f1:
        print('    %s %-6s %s' % ('✖' if lv == '잘못' else '△', kind, msg[:110]))
    finds = list(f1)
    if v1 != '통과':
        v2, f2 = deep(tp, gp, qty_csv)
        print('')
        print('[2] 제대로 검수 : %s  (%d건)' % (v2, len(f2)))
        for lv, kind, msg in f2:
            print('    %s %-6s %s' % ('✖' if lv == '잘못' else '△', kind, msg[:110]))
        finds += f2
        if v2 == '잘못': v1 = '잘못'
        elif v1 == '통과': v1 = v2
    else:
        # 통과여도 검산·합계 재계산은 한 번 더 (값 오류는 서식이 맞아도 난다)
        v2, f2 = deep(tp, gp, qty_csv)
        bad = [f for f in f2 if f[0] == '잘못']
        if bad:
            print('')
            print('[2] 서식은 맞는데 값이 이상합니다 (%d건)' % len(bad))
            for lv, kind, msg in bad:
                print('    ✖ %-6s %s' % (kind, msg[:110]))
            finds += bad; v1 = '잘못'
    od = outdir(TOOL)
    tag = '%s_%s' % (safe_name(os.path.splitext(os.path.basename(tp))[0])[:40], ymd6())
    rep = write_csv(os.path.join(od, '검수_%s.csv' % tag), [[a, b, c] for a, b, c in finds] or [['통과', '', '']],
                    ['수준', '항목', '내용'])
    fixed = None
    if v1 == '잘못' and ask_fix:
        print('')
        print('=' * 70)
        print(' 잘못된 곳이 있습니다. 제가 고칠 수 있는 것(시트 이름·순서, 빈 단가칸 노랑)은 새 파일로 고치고,')
        print(' 나머지는 클로드 부탁서로 넘깁니다. 원본은 그대로 둡니다.')
        print('=' * 70)
        if ask('고쳐도 될까요? (y=엔터 / n) > ', 'y').lower().startswith('y'):
            fixed, done = autofix(tp, gp, finds)
            if fixed:
                print('고친 파일 : %s' % fixed)
                for d in done: print('   + %s' % d)
            rest = [f for f in finds if f[1] not in ('노란칸', '시트')]
            if rest:
                p = os.path.join(od, '_클로드부탁서_검수_%s.md' % tag)
                L = ['# 검수 부탁서 - %s (%s)' % (os.path.basename(tp), today().isoformat()), '',
                     '파이썬 37번 검수에서 걸렸는데 파이썬이 못 고치는 것입니다. 정답본 = %s' % os.path.basename(gp), '']
                for a, b, c in rest: L.append('- [%s] %s : %s' % (a, b, c))
                L += ['', '-> 고친 파일을 새 버전으로 내 주십시오. 원본은 덮어쓰지 마십시오.']
                _io.open(p, 'w', encoding='utf-8').write('\n'.join(L))
                print('클로드 부탁서 : %s' % p)
    print('')
    print('검수 판정 : %s   (보고 %s)' % (v1, rep))
    log(TOOL, '%s %s %d건' % (os.path.basename(tp)[:30], v1, len(finds)))
    return v1, finds, fixed

def run(path=None):
    title('37. 검수   (정답본대로 됐나 파이썬이 본다. 토큰 0)')
    print('정답본 폴더 : %s' % gdir())
    regs = registry(); have = [(e['kind'], find_golden(e)) for e in regs]
    for k, g in have:
        print('   %-8s %s' % (k, os.path.basename(g) if g else '(파일 없음 - 폴더에 넣어주십시오)'))
    if not any(g for k, g in have):
        print('')
        print('[정답본이 하나도 없습니다] 위 폴더에 정답본 xlsx 를 넣으십시오 (주일능_실행산출_v7 등).')
        open_folder(gdir()); return
    if not path:
        cands = latest_xlsx()
        if not cands:
            path = ask('검수할 xlsx 경로 > ').strip('"')
        else:
            print('')
            print('최근 엑셀 (엔터=1번)')
            for i, p in enumerate(cands, 1): print('  %d. %s' % (i, os.path.basename(p)))
            s = ask('번호 또는 경로 > ', '1')
            path = cands[int(s) - 1] if s.isdigit() and 1 <= int(s) <= len(cands) else s.strip('"')
    if not path or not os.path.exists(path):
        print('[없는 파일]'); return
    print('')
    v, finds, fixed = inspect(path)
    if fixed and not open_file(fixed):
        open_folder(os.path.dirname(fixed))

if __name__ == '__main__':
    run(); pause()

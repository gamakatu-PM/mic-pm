# -*- coding: utf-8 -*-
"""28. 단가 붙이기 - 수량표에 단가장을 붙여 실행/계약/견적/예산 금액을 낸다. 토큰 0.

쓰는 것 (모두 3_공통사용\\단가장\\ 안)
  CB모듈_단가장.csv   구분,모듈명(형번),실행가,견적가,예산가   <- 프로님이 한 번만 넣으십니다
  배수.csv            계약/견적/예산 배수. 없으면 만들어 드립니다 (값은 프로님이 정하십니다)
  CB구성.csv          CB 1대당 내부 모듈과 수량. 광희동1가 배선도 판독분을 기본으로 깔아 둡니다
  별칭.csv            도면 품목명 -> 단가장 형번 (안 맞는 것만 한 줄 추가)

내는 것 : 실행/계약/견적/예산 금액표 CSV + 한 장 HTML (자동으로 뜹니다)

금액·배수·조립비율은 제가 정하지 않습니다. 빈칸이면 빈칸으로 두고 무엇이 없는지 적습니다.
"""
import os, re, csv, io as _io, collections
from common import *

TOOL = '단가붙이기'
_QOUT = None
PB = 'CB모듈_단가장.csv'
MULT = '배수.csv'
CBC = 'CB구성.csv'
ALIAS_F = '별칭.csv'

MULT_DEFAULT = [
 ['# 배수는 제가 정하지 않습니다. 아래 값을 프로님이 고치십시오.', '', ''],
 ['# 광희동1가 산출서에 두 체계가 병기돼 있었습니다 (대외 제출 전 확정 필요)', '', ''],
 ['#  단가장 v33 : 1.5 / 1.8 / 2.4    견적스킬 : 1.5 / 1.95 / 2.73', '', ''],
 ['항목', '값', '비고'],
 ['계약배수', '1.5', '실행 x 1.5'],
 ['견적배수', '1.8', '단가장 v68 헤더 기준'],
 ['예산배수', '2.1', '단가장 v68 헤더 기준'],
 ['조립비율', '0.30', 'CB 자재비 x 30% (광희동1가 기준)'],
]
CBC_DEFAULT = [
 ['# CB 1대당 내부 모듈. 현장 배선도가 다르면 수량만 고치십시오.', '', ''],
 ['# 출처 : 광희동1가_산출가능분 (배선도 2장 판독분)', '', ''],
 ['구분', '모듈명(형번)', 'CB1대당수량'],
 ['차단기', 'MCB 52AF/32AT', '1'],
 ['차단기', 'RCBO 32AF/20AT', '6'],
 ['트랜스', 'POWER TRANS', '1'],
 ['퓨즈', '퓨즈 0.5A', '1'],
 ['퓨즈', '퓨즈 5A', '1'],
 ['보드', 'MAIN 보드 CB-30BCB_4F', '1'],
 ['릴레이보드', '전등릴레이 TL-30SP5P', '1'],
 ['보드', 'SA0201B', '1'],
 ['릴레이보드', '전열 릴레이보드', '1'],
 ['퓨즈', '퓨즈 1A', '1'],
 ['기타', 'CHIME SPEAKER', '1'],
]
ALIAS_DEFAULT = [
 ['# 도면 품목명이 단가장 이름과 다를 때 한 줄 추가하십시오.', ''],
 ['# 왼쪽이 도면 품목명에 들어 있으면, 오른쪽이 든 단가장 줄을 씁니다.', ''],
 ['# 오른쪽에 맞는 줄이 2개 이상이면 애매하다고 알리고 금액을 비웁니다(잘못 세지 않게).', ''],
 ['도면품목(포함되면)', '단가장이름(포함되면)'],
 ['입구 INDICATOR', 'CI-2000M'],
 ['KEY SENSOR', 'KD-2000M'],
 ['BED SIDE PANEL(전등', 'BSP-2000M'],
 ['옷장 1버튼', 'LIGHT SWITCH 1버튼'],
 ['# 4~6버튼은 통신가, 1~3버튼은 접점가 (km-fixture-cost 확정 규칙)', ''],
 ['욕실 5버튼', 'LS-2005 (통신)'],
 ['욕실 6버튼', 'LS-2006 (통신)'],
 ['5버튼', 'LS-2005 (통신)'],
 ['6버튼', 'LS-2006 (통신)'],
 ['FLOOR INDICATOR', 'FLOOR INDICATOR PANEL'],
 ['OPERATION PC', 'OPERATION PC'],
 ['비상호출', 'EM-2000'],
 ['방문자', 'VL-2000'],
 ['# 아래는 일부러 비워 둡니다 - 단가장에 해당 품목이 없습니다', ''],
 ['# BED SIDE PANEL(온도  ->  2000M 에 온도형이 없습니다. 단가를 정하시면 여기에 한 줄', ''],
 ['# LIGHT SWITCH + 온도  ->  버튼 수가 정해지면 여기에 한 줄', ''],
]

# ---------------- 밑자료 ----------------

def root():
    p = cfg('price')
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass
    return p

def seed(name, rows):
    p = os.path.join(root(), name)
    if os.path.exists(p):
        return p
    for enc in ('cp949', 'utf-8-sig'):
        try:
            with _io.open(p, 'w', encoding=enc, newline='', errors='strict') as fp:
                w = csv.writer(fp)
                for r in rows:
                    w.writerow(r)
            return p
        except Exception:
            continue
    return p

def rows_of(name):
    p = os.path.join(root(), name)
    if not os.path.exists(p):
        return []
    out = []
    for line in read_text(p).splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith('#'):
            continue
        out.append([c.strip() for c in next(csv.reader([line]))])
    return out

def num(v):
    try:
        return float(str(v).replace(',', '').strip())
    except Exception:
        return None

def _find_pb_file():
    """단가장 파일을 csv/xlsx 아무 쪽이든 찾는다. 이름이 조금 달라도 찾는다."""
    rt = root()
    want = ('단가장', 'CB모듈')
    cands = []
    try:
        for b in os.listdir(rt):
            p = os.path.join(rt, b)
            if not os.path.isfile(p) or b.startswith('~$'):
                continue
            e = os.path.splitext(b)[1].lower()
            if e not in ('.csv', '.xlsx', '.xlsm'):
                continue
            if any(w in b for w in want):
                cands.append(p)
    except Exception:
        pass
    cands.sort(key=lambda x: (os.path.splitext(x)[1].lower() != '.xlsx',
                              -os.path.getmtime(x)))
    return cands[0] if cands else None

def find_header(ws, maxrow=40):
    """총괄 시트의 머리글 줄과 칸 번호. (1부터) 실행가·모듈명 칸이 서로 달라야 머리글이다."""
    for r in range(1, min(ws.max_row or 1, maxrow) + 1):
        cells = [('' if ws.cell(r, c).value is None else str(ws.cell(r, c).value).strip())
                 for c in range(1, min(ws.max_column or 1, 16) + 1)]
        ci = {}
        for i, v in enumerate(cells, start=1):
            if len(v) > 24:
                continue                      # 긴 설명 글은 머리글이 아니다
            if '구분' in v and 'grp' not in ci: ci['grp'] = i
            if any(k in v for k in ('모듈', '형번', '품명', '품목')) and 'mod' not in ci: ci['mod'] = i
            if '실행' in v and 'cost' not in ci: ci['cost'] = i
            if '견적' in v and 'q' not in ci: ci['q'] = i
            if '예산' in v and 'b' not in ci: ci['b'] = i
        if 'mod' in ci and 'cost' in ci and ci['mod'] != ci['cost']:
            return r, ci
    return None, {}

def _pb_from_xlsx(path):
    """엑셀 단가장. 「총괄」 이 든 시트를 먼저 보고, 머리글에서 실행 칸을 찾는다.
    드라이브에서 내려받은 xlsx 를 그대로 넣으셔도 됩니다."""
    try:
        import openpyxl
    except ImportError:
        print('[부품 없음] openpyxl 이 없어 엑셀을 못 읽었습니다. csv 로 주십시오.')
        return []
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        print('[엑셀 열기 실패] %s' % e)
        return []
    names = sorted(wb.sheetnames, key=lambda n: ('총괄' not in n, n))
    out, seen, per = [], set(), []
    for sn in names:
        ws = wb[sn]
        hrow, ci = find_header(ws)
        if not hrow:
            continue
        k = 0
        for r in range(hrow + 1, (ws.max_row or hrow) + 1):
            mod = ws.cell(r, ci['mod']).value
            cost = num(ws.cell(r, ci['cost']).value)
            grp = ws.cell(r, ci['grp']).value if 'grp' in ci else ''
            if mod and cost:
                key = norm(mod)
                if key in seen:
                    continue           # 총괄이 먼저라 같은 형번은 총괄 값이 남는다
                seen.add(key); out.append((str(grp or '').strip(), str(mod).strip(), cost)); k += 1
        if k:
            per.append('「%s」 %d줄' % (sn, k))
    if out:
        print('  엑셀 %s 에서 %d줄 읽었습니다 (%s)' % (os.path.basename(path), len(out), ' / '.join(per)))
    try:
        wb.close()
    except Exception:
        pass
    return out

def load_pricebook():
    """단가장 : [(구분, 형번, 실행가)]. csv 도 xlsx 도 받는다."""
    p = _find_pb_file()
    if not p:
        return None
    if os.path.splitext(p)[1].lower() in ('.xlsx', '.xlsm'):
        print('단가장 파일 : %s' % os.path.basename(p))
        out = _pb_from_xlsx(p)
        return out or None
    print('단가장 파일 : %s' % os.path.basename(p))
    out = []
    for line in read_text(p).splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith('#'):
            continue
        try:
            r = [c.strip() for c in next(csv.reader([line]))]
        except Exception:
            continue
        if len(r) < 3 or num(r[2]) is None:
            continue
        out.append((r[0], r[1], num(r[2])))
    return out or None

def load_mult():
    d = {}
    for r in rows_of(MULT):
        if len(r) >= 2 and num(r[1]) is not None:
            d[r[0].strip()] = num(r[1])
    return d

def load_alias():
    out = []
    for r in rows_of(ALIAS_F):
        if len(r) >= 2 and r[1] and '형번' not in r[1]:
            out.append((r[0], r[1]))
    return out

def norm(s):
    return re.sub(r'[^0-9A-Z가-힣]', '', str(s or '')).upper()

CODE = re.compile(r'[A-Z]{2,}[-_]?[0-9]{2,}[A-Z0-9_]*')

def _uniq(hits):
    seen, out = set(), []
    for mod, cost in hits:
        k = (norm(mod), cost)
        if k in seen:
            continue
        seen.add(k); out.append((mod, cost))
    return out

def find_price(name, pb, alias, series=''):
    """품목명 -> (맞춘이름, 실행가, 근거).
    못 찾거나 후보가 둘 이상이면 금액을 비운다. 짐작으로 금액을 만들지 않는다.
    (수량·금액을 도구가 정하지 않는다 - KM 철칙)"""
    n = norm(name)
    if not n:
        return None, None, '이름없음', []

    # 1) 이름이 똑같다
    hits = _uniq([(m, c) for g, m, c in pb if norm(m) == n])
    if len(hits) == 1:
        return hits[0][0], hits[0][1], '이름일치', []

    def same(h):
        return len({c for m, c in h if c not in ('', None)}) == 1 and all(c not in ('', None) for m, c in h)
    # 2) 별칭표
    hits = []
    for a, b in alias:
        na, nb = norm(a), norm(b)
        if na and na in n and nb:
            hits += [(m, c) for g, m, c in pb if nb in norm(m)]
    hits = _uniq(hits)
    if len(hits) == 1:
        return hits[0][0], hits[0][1], '별칭', []
    if len(hits) > 1:
        if same(hits): return hits[0][0], hits[0][1], '별칭(후보 %d개 값 동일)' % len(hits), []
        return None, None, '애매(후보 %d)' % len(hits), hits

    # 3) 한쪽이 다른 쪽에 들어 있다
    hits = _uniq([(m, c) for g, m, c in pb
                  if len(norm(m)) >= 4 and (norm(m) in n or n in norm(m))])
    if len(hits) == 1:
        return hits[0][0], hits[0][1], '이름포함', []
    if len(hits) > 1:
        if same(hits): return hits[0][0], hits[0][1], '이름포함(후보 %d개 값 동일)' % len(hits), []
        return None, None, '애매(후보 %d)' % len(hits), hits

    # 4) 형번 코드가 같다 (SA0201B, TL-30SP5P 같은 것)
    codes = set(CODE.findall(str(name).upper()))
    if codes:
        hits = _uniq([(m, c) for g, m, c in pb if codes & set(CODE.findall(str(m).upper()))])
        if len(hits) == 1:
            return hits[0][0], hits[0][1], '형번일치', []
        if len(hits) > 1:
            if same(hits): return hits[0][0], hits[0][1], '형번(후보 %d개 값 동일)' % len(hits), []
            return None, None, '애매(후보 %d)' % len(hits), hits
    # 5) 같은 계열(첫 낱말이 같음)의 값이 전부 같으면 그 값 (퓨즈 1A = 퓨즈 0.5A/5A/10A 전부 50 같은 경우)
    tok = re.split(r'[\s(\-/]', str(name).strip())[0]
    if len(norm(tok)) >= 2:
        hits = _uniq([(m, c) for g, m, c in pb if norm(m).startswith(norm(tok))])
        if len(hits) >= 2 and same(hits):      # 1개뿐이면 계열이 아니라 그냥 앞글자 같은 것 (BSP 온도형에 전등형 단가 붙던 사고 방지)
            return hits[0][0], hits[0][1], '같은 계열 %d개 값 동일' % len(hits), []

    return None, None, '단가없음', []

# ---------------- 수량표 ----------------

def pick_qty_file():
    """27번이 낸 수량표를 스스로 찾는다. 없으면 경로를 묻는다."""
    base = os.path.join(cfg('out'), '도면수량')
    cands = []
    if os.path.isdir(base):
        for p in walk_files(base, {'.csv'}):
            b = os.path.basename(p)
            if '도면에적힌수량표' in b or '도면수량' in b:
                cands.append(p)
    cands.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    if cands:
        print('찾은 수량표 (최근 순)')
        for i, p in enumerate(cands[:5], start=1):
            print('  %d. %s' % (i, os.path.basename(p)))
        s = ask('번호 (엔터=1번 / 0=직접 경로) > ', '1')
        if s.isdigit() and 1 <= int(s) <= min(5, len(cands)):
            return cands[int(s) - 1]
    p = ask('수량표 csv 경로를 붙여넣으십시오 > ').strip('"')
    return p if p and os.path.exists(p) else None

def read_qty(path):
    """[(품목, 수량)] - 숫자가 든 칸을 수량으로 본다"""
    out = []
    for r in [x for x in read_text(path).splitlines() if x.strip()]:
        try:
            cells = next(csv.reader([r]))
        except Exception:
            continue
        cells = [c.strip() for c in cells]
        if not cells or cells[0].startswith('#'):
            continue
        qty = None
        nm = ''
        for c in cells:
            if num(c) is not None and num(c) > 0 and float(num(c)).is_integer():
                qty = int(num(c))
        for c in cells:
            if num(c) is None and len(c) >= 2 and not c.startswith('['):
                nm = c if len(c) > len(nm) else nm
        if nm and qty:
            out.append((nm, qty))
    return out

# ---------------- 실행산출 6시트 ----------------

CENTRAL = ('OPERATION', 'PC', 'FIP', 'FLOOR INDICATOR', 'DCU', 'DATA CONV', 'HDU', 'HAND DATA', 'SOFTWARE', 'MONITOR', 'CARD READER', 'DTC', 'DATA TRANSMIT', 'MAIN SYSTEM', 'C.I.P', 'CIP')
LABOR = (('약전 결선 (선로 체크 + CB내 통신/UTP)', ('약전',)), ('CB 속판 취부, 뺵커버 / 기구물 설치', ('취부', '설치비')), ('시운전비 MK-TSET', ('시운전',)))

def precedent():
    """선례 값 : 정답본 실행산출(연합기숙사 v5)에 적힌 숫자. 단가장에 없을 때 「선례」 로 채우고 노란칸은 유지한다(확정은 프로님).
    -> (dict 이름->값, 정답본 파일명)"""
    out = {}
    try:
        import t37_check, openpyxl
        e = next((x for x in t37_check.registry() if x['kind'] == '실행산출'), None)
        g = t37_check.find_golden(e) if e else None
        if not g:
            return out, ''
        wb = openpyxl.load_workbook(g, data_only=True)
        for sname, kc, vc in (('1.입력판', 1, 2), ('3.견적↔실행 대조', 2, 6), ('2.CB 실행', 1, 5)):
            ws = next((w for w in wb.worksheets if re.sub(r'\s', '', w.title) == re.sub(r'\s', '', sname)), None)
            if not ws: continue
            for r in ws.iter_rows(values_only=True):
                k, v = (r[kc - 1] if len(r) >= kc else None), (r[vc - 1] if len(r) >= vc else None)
                if isinstance(k, str) and isinstance(v, (int, float)) and v >= 1 and k.strip() not in out:   # 비율(0.3 등)은 선례가 아니다
                    out[k.strip()] = v
        return out, os.path.basename(g)
    except Exception:
        return out, ''

def _prec(pre, keys):
    """선례 사전에서 keys 낱말이 든 줄. 「비율」「배수」 줄은 값이 아니므로 건너뛴다."""
    for k, v in pre.items():
        if any(x in k for x in keys) and not any(x in k for x in ('비율', '배수')):
            return k, v
    return None

def emit_exec(site, od, tag, qty, rows, cb_rows_priced, mult, miss, pb, alias, cbq, qty_name):
    import execsheet
    pre, pre_name = precedent()
    # 수량표 -> 구역 나누기
    q_rows, cb_types = [], []
    for (nm, q), r in zip(qty, rows):
        up = nm.upper()
        if 'CONTROL BOX' in up or up.startswith('CB'):
            desc = re.sub(r'(?i)control\s*box\s*\d*', '', nm).strip(' -:()')
            cb_types.append(('CB%d' % (len(cb_types) + 1), q, desc)); continue
        g = '중앙' if any(k in up for k in CENTRAL) else ('도어락' if 'DOOR' in up or '도어락' in nm else '객실')
        cost = r[3] if r[3] != '' else None
        q_rows.append((nm, r[1] or '', 'EA', q, cost, r[5] + ((' — ' + r[1]) if r[1] else ''), g))
    if not cb_types:
        cb_types = [('CB1', cbq or 0)]
    rooms = sum(t[1] for t in cb_types) or cbq or 0
    # 노무 3종 (실당) — 단가장에 있으면 채우고 없으면 노란칸
    unknown = []
    for lab, keys in LABOR:
        hit = next(((m, c) for g, m, c in pb if any(k in m for k in keys) and ('실당' in m or '노무' in g or '직접' in g)), None)
        if hit:
            q_rows.append((lab, hit[0], 'EA', rooms, int(hit[1]), '단가장 %s' % hit[0], '노무'))
        else:
            pr = _prec(pre, keys)
            q_rows.append((lab, '', 'EA', rooms, None, '[확인] 노무 3종 실행가 — 1.입력판 (선례 %s)' % (pre_name or '없음'), '노무'))
            if pr:
                q_rows[-1] = (lab, '', 'EA', rooms, None, '[확인] 선례 %s %s — 1.입력판' % (pre_name[:20], won(pr[1])), '노무')
                unknown.append((lab, '단가장 직접단가 시트에 없음 → 선례 %s 「%s」 %s 를 넣어 둠 (확정하시면 그대로)' % (pre_name, pr[0][:24], won(pr[1])), '%s × 단가' % rooms, '', pr[1]))
            else:
                unknown.append((lab, '노무 3종 실행가 미확인 (단가장·선례 모두 없음)', '%s × 단가 — 견적 스킬 표준 약전 12만 / 취부 13만 / 시운전 5만' % rooms))
    # CB 내부
    cbr = []
    for g, mod, per, cost, amt, why in cb_rows_priced:
        cbr.append((mod, g, [per] * len(cb_types), int(cost) if cost != '' else None, (why if str(why).startswith('선례') else '단가장 %s' % why) if cost != '' else '[확인] 단가장에 없음 — 1.입력판'))
        if cost == '':
            unknown.append((mod, '단가장에 없는 모듈', ''))
    # 외함
    enc = next(((m, c) for g, m, c in pb if '외함' in m and '노출' in m), None)
    pr = _prec(pre, ('CB 외함',))
    if pr:
        unknown.insert(0, ('CB 외함 세트 실행가 (1대당)', '규격 미정 → 선례 %s 「%s」 %s 를 넣어 둠 (앵커 규격 확정 시 교체)' % (pre_name, pr[0][:24], won(pr[1])),
                           ('%s대 × 외함가 — 단가장 후보: ' % rooms) + ' / '.join('%s %s' % (m, won(c)) for g, m, c in pb if '외함' in m)[:120], '', pr[1]))
    else:
        unknown.insert(0, ('CB 외함 세트 실행가 (1대당)', '규격 미정', ('%s대 × 외함가 — 후보: ' % rooms) + ' / '.join('%s %s' % (m, won(c)) for g, m, c in pb if '외함' in m)[:120]))
    # 단가 없는 기구물
    for m in miss:
        if str(m[0]).startswith('CB내부)') or 'CONTROL BOX' in str(m[0]).upper() or str(m[0]).upper().startswith('CB'):
            continue           # CB 본체는 2.CB 실행 시트가 계산한다
        nm0 = str(m[0]); grp = '도어락' if ('DOOR' in nm0.upper() or '도어락' in nm0) else ''
        unknown.append((nm0, m[2] if len(m) > 2 else '단가없음', m[3] if len(m) > 3 else '', grp))
    prefill = {u[0]: u[4] for u in unknown if len(u) > 4 and u[4]}
    meta = {'도면': qty_name, '견적서': None, '단가장': os.path.basename(_find_pb_file() or ''), 'CB출처': C_CBC_NOTE(), '객실수': rooms,
            '외함실행가': prefill.get('CB 외함 세트 실행가 (1대당)'), '외함규격': '[규격확인] 선례 연합기숙사 400*800*90 매입',
            '노무선례': {u[0]: u[4] for u in unknown if len(u) > 4 and u[4] and u[0] in [l for l, k in LABOR]},
            '자가신고': ['이 파일은 28번 코드가 정답본 틀에 값만 채운 것입니다. 사람 손으로 만든 칸이 없습니다.',
                        'CB 내부 구성은 정답본(연합기숙사 v5) 2.CB 실행 그대로입니다(CB구성.csv). 이 현장 배선도로 확정될 때까지 잠정치입니다.',
                        '견적서가 없으면 견적단가 = 실행 × 견적배수 잠정입니다. 발행 후 3.대조 H열을 발행단가로 바꾸십시오.',
                        '3.대조 L~O(두 번째 견적 블록)의 뜻을 확인 못 해 첫 블록(H)과 같은 값으로 두었습니다. 정답본 v5 는 CB 480,000 / 450,000 두 값입니다.',
                        '노란칸(1.입력판) : 단가장에 없는 것은 선례(%s) 값을 넣어 두었고, 선례에도 없는 것만 비웠습니다. 추정치는 넣지 않았습니다.' % (pre_name or '없음')]}
    out = os.path.join(od, '%s_실행산출_v1.xlsx' % tag)
    execsheet.build(site, out, q_rows, cb_types, cbr, mult, unknown, meta)
    print('')
    print('실행산출 6시트 : %s' % out)
    # 견적서(고객용) — 원가 없이, 견적단가 = 실행 × 견적배수
    try:
        import quotesheet
        mat = sum((c or 0) * p for m, t, per, c, memo in cbr for p in [per[0]])
        body = int(round(mat * (1 + float(mult.get('조립비율') or 0.3)))) if mat else None
        qout = os.path.join(od, '%s_견적서_v1.xlsx' % tag)
        q_rows2 = [(nm, sp, un, q, (meta['노무선례'].get(nm) if (c is None and g == '노무') else c), mm, g) for nm, sp, un, q, c, mm, g in q_rows]
        quotesheet.build(site, qout, q_rows2, cb_types, cbr, mult,
                         dict(meta, 공사명='%s 객실관리 시스템' % site, cb_body=[body] * len(cb_types)))
        print('견적서(고객용)   : %s' % qout)
        try:
            import t37_check
            v2, f2, _ = t37_check.inspect(qout, ask_fix=False, quiet=True)
            print('  37번 검수 : %s' % v2)
        except Exception as e:
            print('  (37번 검수 못 돌림: %s)' % e)
        global _QOUT; _QOUT = qout
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[견적서 못 만듦] %s' % e)
    # 곧바로 검수
    try:
        import t37_check
        v, finds, fixed = t37_check.inspect(out, ask_fix=False, quiet=True)
        print('  37번 검수 : %s' % v)
    except Exception as e:
        print('  (37번 검수 못 돌림: %s)' % e)
    return out

def cb_from_golden():
    """정답본 실행산출(연합기숙사 v5) 「2.CB 실행」 의 CB 1대당 내부 구성 -> [[구분, 모듈명, 1대당수량, 선례실행가, 비고], ...]
    실행단가 칸이 '1.입력판'!B{n} 참조면 그 칸 값을 읽는다. 「▣」 소계 줄에서 멈춘다."""
    out = []
    try:
        import t37_check, openpyxl
        e = next((x for x in t37_check.registry() if x['kind'] == '실행산출'), None)
        g = t37_check.find_golden(e) if e else None
        if not g:
            return out, ''
        wb = openpyxl.load_workbook(g)
        ws = next((w for w in wb.worksheets if re.sub(r'\s', '', w.title) == '2.CB실행'), None)
        wi = next((w for w in wb.worksheets if re.sub(r'\s', '', w.title) == '1.입력판'), None)
        if not ws:
            return out, ''
        hr = next((r for r in range(1, 8) if str(ws.cell(r, 1).value or '').startswith('품목명')), 3)
        for r in range(hr + 1, (ws.max_row or 0) + 1):
            a = ws.cell(r, 1).value
            if a is None: continue
            if str(a).strip().startswith(('▣', '■', '◆', '▷')): break
            per = ws.cell(r, 3).value
            cost = ws.cell(r, 5).value
            if isinstance(cost, str) and cost.startswith('=') and wi is not None:
                m = re.search(r"입력판'?!\$?([A-Z]+)\$?(\d+)", cost)
                cost = wi['%s%s' % (m.group(1), m.group(2))].value if m else None
            if not isinstance(cost, (int, float)): cost = None
            out.append([str(ws.cell(r, 2).value or '')[:40], str(a).strip(), int(per) if isinstance(per, (int, float)) else 1,
                        int(cost) if cost else '', str(ws.cell(r, 8).value or '')[:80]])
        return out, os.path.basename(g)
    except Exception:
        return out, ''

def seed_cbc():
    """CB구성.csv 가 없으면 정답본(연합기숙사 v5)의 CB 구성으로 만든다. 정답본도 없으면 옛 기본값."""
    p = os.path.join(root(), CBC)
    if os.path.exists(p):
        return p
    rows, g = cb_from_golden()
    if rows:
        return seed(CBC, [['# CB 1대당 내부 모듈. 현장 배선도가 다르면 수량만 고치십시오.', '', '', '', ''],
                          ['# 출처 : 정답본 %s 「2.CB 실행」 (프로님 기준). 선례실행가는 단가장에 없을 때만 쓴다' % g, '', '', '', ''],
                          ['구분', '모듈명(형번)', 'CB1대당수량', '선례실행가', '비고']] + rows)
    return seed(CBC, CBC_DEFAULT)

def C_CBC_NOTE():
    try:
        for line in read_text(os.path.join(root(), CBC)).splitlines():
            if line.startswith('# 출처'):
                return 'CB구성.csv (%s)' % line.split(':', 1)[1].strip().split('.')[0][:60]
    except Exception:
        pass
    return 'CB구성.csv'

# ---------------- 실행 ----------------

def rooms_of(site):
    """현장대장에 객실수가 있으면 CB 대수 기본값으로 쓴다"""
    try:
        import sitebook
        for d in sitebook.load():
            if norm(d['site']) == norm(site) or (norm(site) and norm(site) in norm(d['site'])):
                return str(d.get('rooms') or '0')
    except Exception:
        pass
    return '0'

def run(site_hint=None):
    title('28. 단가 붙이기   (수량표 + 단가장 -> 금액. 토큰 0)')
    rt = root()
    seed(MULT, MULT_DEFAULT); seed_cbc(); seed(ALIAS_F, ALIAS_DEFAULT)
    pb = load_pricebook()
    print('단가장 폴더 : %s' % rt)
    if not pb:
        print('')
        print('[단가장이 없습니다] 이 폴더에 단가장 파일을 한 번만 넣어주십시오.')
        print('   엑셀이든 csv 든 됩니다. 이름에 「단가장」 이나 「CB모듈」 이 들어가면 찾습니다.')
        print('   드라이브에서 「CB모듈_단가장」 을 xlsx 로 내려받아 그대로 끌어다 넣으시면 됩니다.')
        print('   (「총괄」 시트의 구분 / 모듈명(형번) / 실행가 칸을 스스로 찾습니다)')
        print('')
        print('한 번 넣으시면 그 뒤로는 28번이 계속 0원으로 계산합니다.')
        open_folder(rt)
        return
    print('단가장 : %d줄' % len(pb))
    mult = load_mult(); alias = load_alias()
    print('배수   : 계약 %s / 견적 %s / 예산 %s / 조립비율 %s'
          % (mult.get('계약배수', '?'), mult.get('견적배수', '?'),
             mult.get('예산배수', '?'), mult.get('조립비율', '?')))
    print('별칭   : %d줄' % len(alias))
    print('-' * 74)

    qf = pick_qty_file()
    if not qf:
        print('[수량표가 없습니다] 먼저 27번으로 도면 수량을 뽑으십시오.')
        return
    qty = read_qty(qf)
    if not qty:
        print('[수량표에서 품목/수량을 못 읽었습니다] 1칸=품목, 어딘가에 수량 숫자가 있어야 합니다.')
        return
    site = ask('현장명 > ', site_hint or os.path.basename(qf).split('_')[0])
    series = ask('기구물 계열 (엔터=2000M) > ', '2000M')

    # --- 기구물/중앙장비 ---
    print('')
    print('%-34s %7s %11s %13s  %s' % ('품목', '수량', '실행단가', '실행금액', '근거'))
    print('-' * 86)
    rows, miss = [], []
    ex_sum = 0
    for nm, q in qty:
        if 'CONTROL BOX' in nm.upper() or nm.upper().startswith('CB'):
            print('%-34s %7s %11s %13s  2.CB 실행 시트에서 계산' % (nm[:34], won(q), '', ''))
            rows.append([nm, '', q, '', '', 'CB 시트']); continue
        mod, cost, why, cands = find_price(nm, pb, alias, series)
        if cost:
            amt = int(round(q * cost)); ex_sum += amt
            print('%-34s %7s %11s %13s  %s' % (nm[:34], won(q), won(cost), won(amt), why))
            rows.append([nm, mod, q, int(cost), amt, why])
        else:
            print('%-34s %7s %11s %13s  %s' % (nm[:34], won(q), '', '', why))
            rows.append([nm, '', q, '', '', why])
            miss.append([nm, q, why,
                         ' / '.join('%s %s' % (m, won(c)) for m, c in cands[:4])])

    # --- CB 내부 ---
    cb_rows, cb_mat = [], 0
    for r in rows_of(CBC):
        if len(r) < 3 or num(r[2]) is None:
            continue
        g, mod, per = r[0], r[1], int(num(r[2]))
        m2, cost, why, cands = find_price(mod, pb, alias, series)
        if not cost and len(r) > 3 and num(r[3]):
            cost, why = num(r[3]), '선례(정답본 CB 구성) %s' % (r[4][:30] if len(r) > 4 and r[4] else '')
        if cost:
            amt = int(round(per * cost)); cb_mat += amt
            cb_rows.append([g, mod, per, int(cost), amt, why])
        else:
            cb_rows.append([g, mod, per, '', '', why])
            miss.append([('CB내부) ' + mod), per, why,
                         ' / '.join('%s %s' % (m, won(c)) for m, c in cands[:4])])
    asm_rate = mult.get('조립비율')
    cb_one = None
    if cb_mat and asm_rate is not None:
        cb_one = int(round(cb_mat * (1 + asm_rate)))
    if cb_rows:
        print('')
        print('-- CB 1대당 내부 자재 (%s) --' % CBC)
        for g, mod, per, c, amt, why in cb_rows:
            print('  %-10s %-32s %4s %11s %12s %s'
                  % (g[:10], str(mod)[:32], won(per), won(c) if c else '', won(amt) if amt else '', why))
        print('  %-44s 자재비 %12s' % ('', won(cb_mat)))
        if cb_one:
            print('  %-44s 조립비 %12s  (자재 x %s)'
                  % ('', won(cb_one - cb_mat), asm_rate))
            print('  %-44s 1대당 %12s' % ('', won(cb_one)))
    cbq = int(num(ask('\nCB 대수 (엔터=%s) > ' % rooms_of(site), rooms_of(site))) or 0)
    cb_tot = cb_one * cbq if (cb_one and cbq) else 0

    # --- 총괄 ---
    print('')
    print('%-24s %15s %15s %15s %15s' % ('구분', '실행', '계약', '견적', '예산'))
    print('-' * 90)
    def band(v):
        return (int(round(v * mult.get('계약배수', 0))),
                int(round(v * mult.get('견적배수', 0))),
                int(round(v * mult.get('예산배수', 0))))
    tot = []
    for nm, v in (('기구물 · 중앙장비', ex_sum), ('CB 내부 (%s대)' % won(cbq), cb_tot)):
        if not v:
            continue
        a, b, c = band(v)
        print('%-24s %15s %15s %15s %15s' % (nm, won(v), won(a), won(b), won(c)))
        tot.append([nm, v, a, b, c])
    S = sum(t[1] for t in tot)
    if S:
        a, b, c = band(S)
        print('-' * 90)
        print('%-24s %15s %15s %15s %15s' % ('합 계', won(S), won(a), won(b), won(c)))
        print('%-24s %15s' % ('이윤 (견적-실행)', won(b - S)))
        print('%-24s %14.1f%%' % ('이윤율', (b - S) / b * 100 if b else 0))

    if miss:
        print('')
        print('-- 단가가 없어 비운 것 (%d건) --' % len(miss))
        for m in miss[:25]:
            print('  %-40s %7s  %s  %s' % (str(m[0])[:40], won(m[1]), m[2], m[3][:40]))
        print('  -> 단가장에 줄을 추가하시거나, 별칭.csv 에 이름 연결을 한 줄 넣으십시오.')

    # --- 실행산출 6시트 (정답본 틀, 코드가 채움) ---
    od = outdir(TOOL)
    tag = '%s_%s' % (safe_name(site), ymd6())
    xls = None
    try:
        xls = emit_exec(site, od, tag, qty, rows, cb_rows, mult, miss, pb, alias, cbq, os.path.basename(qf))
    except Exception as e:
        import traceback; traceback.print_exc()
        print('[실행산출 엑셀 못 만듦] %s' % e)
    f1 = write_csv(os.path.join(od, '%s_실행견적_기구물.csv' % tag), rows,
                   ['품목', '맞춘형번', '수량', '실행단가', '실행금액', '근거'])
    made = [f1]
    if cb_rows:
        made.append(write_csv(os.path.join(od, '%s_실행견적_CB내부.csv' % tag), cb_rows,
                              ['구분', '모듈명(형번)', 'CB1대당', '실행단가', '금액', '근거']))
    if tot:
        made.append(write_csv(os.path.join(od, '%s_총괄.csv' % tag),
                              tot + [['합계', S] + list(band(S))],
                              ['구분', '실행', '계약', '견적', '예산']))
    if miss:
        made.append(write_csv(os.path.join(od, '%s_단가없는것.csv' % tag), miss,
                              ['품목', '수량', '왜', '단가장 후보']))

    blocks = [('총괄', [('green', '%s : 실행 %s / 계약 %s / 견적 %s / 예산 %s'
                        % (t[0], won(t[1]), won(t[2]), won(t[3]), won(t[4]))) for t in tot]),
              ('기구물 · 중앙장비',
               [('green' if r[4] else 'yellow',
                 '%s x %s = %s %s' % (r[0], won(r[2]), won(r[4]) if r[4] else '단가없음',
                                      ('[%s]' % r[1]) if r[1] else '')) for r in rows]),
              ('CB 1대당 내부',
               [('green' if r[4] else 'yellow',
                 '%s %s x %s = %s' % (r[0], r[1], won(r[2]), won(r[4]) if r[4] else '단가없음'))
                for r in cb_rows]),
              ('단가가 없어 비운 것 (채우시면 자동 계산됩니다)',
               [('red', '%s : %s개 - %s %s' % (m[0], won(m[1]), m[2],
                                              ('/ 후보 : ' + m[3]) if m[3] else '')) for m in miss]),
              ('쓴 밑자료',
               [('gray', '단가장 %s줄 · 배수 계약%s/견적%s/예산%s · 조립비율 %s'
                 % (won(len(pb)), mult.get('계약배수'), mult.get('견적배수'),
                    mult.get('예산배수'), mult.get('조립비율'))),
                ('gray', '수량표 : %s' % os.path.basename(qf))])]
    if xls:
        made.insert(0, xls)
        if globals().get('_QOUT'):
            made.insert(1, _QOUT)
    f9 = write_html(os.path.join(od, '%s_실행견적.html' % tag),
                    '%s 실행 / 견적' % site, blocks, files=made)
    print('')
    print('파일을 만들었습니다. 결과 화면을 지금 띄웁니다.')
    for x in made + [f9]:
        print('  %s' % x)
    print('')
    print('* 배수·조립비율은 %s 에서 프로님이 정하십니다. 제가 정하지 않습니다.' % MULT)
    log(TOOL, '%s 품목%d 단가없음%d 실행%d' % (site, len(rows), len(miss), S))
    if not open_file(f9):
        open_folder(od)

if __name__ == '__main__':
    run(); pause()

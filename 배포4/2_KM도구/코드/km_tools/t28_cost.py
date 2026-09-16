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
 ['욕실 5버튼', 'LS-2005'],
 ['욕실 6버튼', 'LS-2006'],
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

def _pb_from_xlsx(path):
    """엑셀 단가장. 「총괄」 이 든 시트를 먼저 보고, 머리글에서 실행 칸을 찾는다.
    드라이브에서 내려받은 xlsx 를 그대로 넣으셔도 됩니다."""
    try:
        import openpyxl
    except ImportError:
        print('[부품 없음] openpyxl 이 없어 엑셀을 못 읽었습니다. csv 로 주십시오.')
        return []
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    except Exception as e:
        print('[엑셀 열기 실패] %s' % e)
        return []
    names = sorted(wb.sheetnames, key=lambda n: ('총괄' not in n, n))
    out = []
    for sn in names:
        ws = wb[sn]
        head, ci = None, {}
        for row in ws.iter_rows(values_only=True):
            cells = ['' if c is None else str(c).strip() for c in row]
            if head is None:
                joined = ' '.join(cells)
                if ('실행' in joined) and any(k in joined for k in ('모듈', '형번', '품명', '품목')):
                    for i, c in enumerate(cells):
                        if '실행' in c and 'cost' not in ci:
                            ci['cost'] = i
                        if any(k in c for k in ('모듈', '형번', '품명', '품목')) and 'mod' not in ci:
                            ci['mod'] = i
                        if '구분' in c and 'grp' not in ci:
                            ci['grp'] = i
                    if 'cost' in ci and 'mod' in ci:
                        head = True
                continue
            mod = cells[ci['mod']] if ci['mod'] < len(cells) else ''
            cost = num(cells[ci['cost']]) if ci['cost'] < len(cells) else None
            grp = cells[ci.get('grp', 0)] if ci.get('grp', 0) < len(cells) else ''
            if mod and cost:
                out.append((grp, mod, cost))
        if out:
            print('  엑셀 시트 「%s」 에서 %d줄 읽었습니다.' % (sn, len(out)))
            break
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
        return None, None, '애매(후보 %d)' % len(hits), hits

    # 3) 한쪽이 다른 쪽에 들어 있다
    hits = _uniq([(m, c) for g, m, c in pb
                  if len(norm(m)) >= 4 and (norm(m) in n or n in norm(m))])
    if len(hits) == 1:
        return hits[0][0], hits[0][1], '이름포함', []
    if len(hits) > 1:
        return None, None, '애매(후보 %d)' % len(hits), hits

    # 4) 형번 코드가 같다 (SA0201B, TL-30SP5P 같은 것)
    codes = set(CODE.findall(str(name).upper()))
    if codes:
        hits = _uniq([(m, c) for g, m, c in pb if codes & set(CODE.findall(str(m).upper()))])
        if len(hits) == 1:
            return hits[0][0], hits[0][1], '형번일치', []
        if len(hits) > 1:
            return None, None, '애매(후보 %d)' % len(hits), hits

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

# ---------------- 실행 ----------------

def run():
    title('28. 단가 붙이기   (수량표 + 단가장 -> 금액. 토큰 0)')
    rt = root()
    seed(MULT, MULT_DEFAULT); seed(CBC, CBC_DEFAULT); seed(ALIAS_F, ALIAS_DEFAULT)
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
    site = ask('현장명 > ', os.path.basename(qf).split('_')[0])
    series = ask('기구물 계열 (엔터=2000M) > ', '2000M')

    # --- 기구물/중앙장비 ---
    print('')
    print('%-34s %7s %11s %13s  %s' % ('품목', '수량', '실행단가', '실행금액', '근거'))
    print('-' * 86)
    rows, miss = [], []
    ex_sum = 0
    for nm, q in qty:
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
    cbq = int(num(ask('\nCB 대수 (엔터=건너뜀) > ', '0')) or 0)
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

    # --- 파일 ---
    od = outdir(TOOL)
    tag = '%s_%s' % (safe_name(site), ymd6())
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

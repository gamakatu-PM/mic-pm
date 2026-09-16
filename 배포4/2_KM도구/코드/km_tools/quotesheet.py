# -*- coding: utf-8 -*-
"""견적서(고객용) 만들기 - 회사 원틀(광희동1가_견적서_Rev1: 갑지+내역서)을 복사해 값만 채운다. 원가는 절대 넣지 않는다.
28번이 부른다. 견적단가 = 실행 × 견적배수(1.입력판) 잠정. 단가 없는 줄은 비우고 [단가확인].
"""
import os, re, copy, shutil, glob
from common import *

def template():
    d = os.path.join(cfg('template'), '정답본')
    for p in sorted(glob.glob(os.path.join(d, '*.xlsx')), key=os.path.getmtime, reverse=True):
        if '견적서' in os.path.basename(p) and not os.path.basename(p).startswith('~$'):
            return p
    for p in glob.glob(os.path.join(cfg('template'), '*견적*.xlsx')):
        if not os.path.basename(p).startswith('~$'):
            return p
    return None

DIG = '영일이삼사오육칠팔구'; UNIT4 = ['', '만', '억', '조']; UNIT1 = ['', '십', '백', '천']
def hangul(n):
    n = int(round(n))
    if n == 0: return '영'
    out = []; i = 0
    while n > 0:
        blk = n % 10000; n //= 10000
        s = ''
        for j in range(4):
            d = blk % 10; blk //= 10
            if d: s = DIG[d] + UNIT1[j] + s
        if s: out.insert(0, s + UNIT4[i])
        i += 1
    return ''.join(out)

def _fill(c):
    from openpyxl.styles import PatternFill
    return PatternFill('solid', fgColor=c)

def build(site, out_path, qty, cb_types, cb_rows, mult, meta):
    """
    qty      : [(품명, 규격, 단위, 수량, 실행단가 or None, 비고, 구역)]   구역 중앙|객실|노무|도어락
    cb_types : [(CB1, 대수, 설명)]
    cb_rows  : [(모듈명, 도면표기, [1대당 per 타입], 실행단가 or None, 비고)]
    mult     : 배수 dict
    meta     : 도면/수신/비고 등. meta['cb_body'] = 타입별 본체 실행가(외함 제외, 1대) 리스트 (없으면 계산)
    """
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter as L
    tpl = template()
    qm = float(mult.get('견적배수') or 1.8)
    asm = float(mult.get('조립비율') or 0.3)
    if tpl:
        shutil.copy(tpl, out_path); wb = openpyxl.load_workbook(out_path)
        g = next(wb[s] for s in wb.sheetnames if '갑지' in s); ws = next(wb[s] for s in wb.sheetnames if '내역서' in s)
        S = {'sec': copy.copy(ws['A4']._style), 'item': [copy.copy(ws.cell(5, c)._style) for c in range(1, 13)],
             'sub': [copy.copy(ws.cell(27, c)._style) for c in range(1, 13)], 'subtot': [copy.copy(ws.cell(24, c)._style) for c in range(1, 13)],
             'note': copy.copy(ws['A70']._style), 'total': [copy.copy(ws.cell(78, c)._style) for c in range(1, 13)]}
        for m in [m for m in ws.merged_cells.ranges if m.min_row >= 4]: ws.unmerge_cells(str(m))
        for r in range(4, (ws.max_row or 4) + 1):
            for c in range(1, 15): ws.cell(r, c).value = None; ws.cell(r, c).fill = PatternFill(fill_type=None)
    else:
        wb = openpyxl.Workbook(); g = wb.active; g.title = '갑지 '; ws = wb.create_sheet('내역서 ')
        S = None
        for c, h in enumerate(['명   칭', '규   격', '단위', '수량', '재료비', '', '노무비', '', '경 비', '', '계', '비고'], 1):
            ws.cell(2, c, h).font = Font(name='맑은 고딕', bold=True)
        for c, h in enumerate(['', '', '', '', '단가', '금액', '단가', '금액', '단가', '금액', '', ''], 1): ws.cell(3, c, h)
        for i, w in enumerate([31, 10, 6, 6, 13, 14, 10, 12, 9, 10, 13, 30], 1): ws.column_dimensions[L(i)].width = w
    def put(r, c, v, st=None, num=None, h=None):
        cell = ws.cell(r, c, v)
        if st is not None: cell._style = copy.copy(st)
        if num: cell.number_format = num
        return cell
    def item(r, name, spec, unit, q, uprice, memo, labor=False):
        st = S['item'] if S else [None] * 12
        put(r, 1, name, st[0]); put(r, 2, spec, st[1]); put(r, 3, unit, st[2]); put(r, 4, q, st[3], '#,##0')
        col = 7 if labor else 5
        put(r, col, uprice, st[col - 1], '#,##0'); put(r, col + 1, '=D%d*%s%d' % (r, L(col), r) if uprice is not None else None, st[col], '#,##0')
        put(r, 11, '=SUM(F%d,H%d,J%d)' % (r, r, r), st[10], '#,##0'); put(r, 12, memo, st[11])
        if uprice is None: ws.cell(r, col).fill = _fill('FFF2CC')
        ws.row_dimensions[r].height = 21
    def sub(r, text):
        st = S['sub'] if S else [None] * 12
        put(r, 1, text, st[0]); ws.row_dimensions[r].height = 18.75
    def subtotal(r, a, b):
        st = S['subtot'] if S else [None] * 12
        put(r, 1, '소   계', st[0])
        for c in (6, 8, 10, 11): put(r, c, '=SUM(%s%d:%s%d)' % (L(c), a, L(c), b), st[c - 1], '#,##0')
        for c in range(1, 13):
            if ws.cell(r, c)._style is None or not S: ws.cell(r, c).fill = _fill('D8D8D8')
    ws['A1'] = '공 사 명 : %s' % meta.get('공사명', site)
    r = 4
    put(r, 1, ' 1. 중앙관리 시스템', S['sec'] if S else None); r += 1
    a = r
    def qprice(cost):
        return int(round(cost * qm)) if cost not in (None, '') else None
    for name, spec, unit, q, cost, memo, gk in [x for x in qty if x[6] == '중앙']:
        item(r, name, spec, unit, q, qprice(cost), '' if cost not in (None, '') else '[단가확인]'); r += 1
    subtotal(r, a, r - 1); SUB1 = r; r += 1
    put(r, 1, '2. 객실관리 시스템', S['sec'] if S else None); r += 1
    a = r
    bodies = meta.get('cb_body') or []
    for i, t in enumerate(cb_types):
        name, n = t[0], t[1]; desc = t[2] if len(t) > 2 else ''
        body = bodies[i] if i < len(bodies) else None
        item(r, 'CONTROL BOX%s%s' % (name[2:] if name.startswith('CB') else name, (' (%s)' % desc) if desc else ''), meta.get('CB형번', 'CB-30BCB_4F 계열'), 'EA', n,
             qprice(body) if body else None, '' if body else '[단가확인] 내부 구성 확정 후'); r += 1
        for line in ('-제조사 : 한국마이크로닉㈜', '-제  질 : SPC-1 냉간압연강판', '-기  능 : 객실제어 및 FIP간 통신중계'):
            sub(r, line); r += 1
        for mod, txt, per, cost, memo in cb_rows:
            k = per[i] if i < len(per) else per[0]
            if not k: continue
            sub(r, '-%s%s' % (mod, (' × %d' % k) if k > 1 else '')); r += 1
    enc_cost = meta.get('외함실행가')
    item(r, 'CONTROL BOX 외함', meta.get('외함규격', '[규격확인]'), 'EA', sum(t[1] for t in cb_types), qprice(enc_cost) if enc_cost else None, '' if enc_cost else '[단가확인]'); r += 1
    for name, spec, unit, q, cost, memo, gk in [x for x in qty if x[6] in ('객실', '도어락')]:
        item(r, name, spec, unit, q, qprice(cost), '' if cost not in (None, '') else '[단가확인]'); r += 1
    for name, spec, unit, q, cost, memo, gk in [x for x in qty if x[6] == '노무']:
        item(r, name, spec, unit, q, qprice(cost), '' if cost not in (None, '') else '[단가확인] 노무단가 미확정', labor=True); r += 1
    subtotal(r, a, r - 1); SUB2 = r; r += 1
    st_note = S['note'] if S else None
    for t in ['  * V A T 별도',
              '  * 공사관계 : 1) CONTROL BOX 약전 접속은 객실관리 업체 공사분',
              '               2) CONTROL BOX 내 강전 접속 제외 (220V접속은 전기공사 업체 공사분)',
              '               3) 유럽형 전기 접속용 매입박스 납품 및 설치, 타공 제외 ',
              '               4) 전기 배관,배선 공사 제외',
              '  * 계약시 선수금 30%, 중도금 40% 현금 지급 조건',
              '  * 유효기간: 견적일로부터 60일']:
        put(r, 1, t, st_note); ws.merge_cells('A%d:F%d' % (r, r)); r += 1
    r += 1; TOT = r
    st = S['total'] if S else [None] * 12
    put(r, 1, '합        계', st[0])
    for c in (6, 8, 10, 11): put(r, c, '=%s%d+%s%d' % (L(c), SUB1, L(c), SUB2), st[c - 1], '#,##0')
    for c in range(1, 13):
        if not S: ws.cell(r, c).fill = _fill('FBE4D5')
    ws.print_area = 'A1:L%d' % r
    # ---------- 갑지 ----------
    g['A5'] = '날    짜 : %s' % today().strftime('%Y. %m. %d')
    g['A6'] = '공 사 명 : %s' % meta.get('공사명', site)
    g['A7'] = '공 종 명 : 객실관리 시스템'
    g['A8'] = '수    신 : %s' % meta.get('수신', '[수신처 확인]')
    g['A12'] = "=CONCATENATE(\"一金 \",\"[한글금액은 총액 확정 후]\",\"(\\\",TEXT('내역서 '!K%d,\"#,##0\"),\"원)VAT별도 — 견적가(실행×%s) 초안(Rev.1)\")" % (TOT, qm)
    g['F14'] = "='내역서 '!F%d" % TOT; g['G14'] = "='내역서 '!H%d" % TOT; g['H14'] = "='내역서 '!K%d" % TOT; g['H17'] = '=H14'
    g['B14'] = '객실관리 시스템'; g['D14'] = '식'; g['E14'] = 1; g['A14'] = 1
    wb.active = 0
    try:
        from openpyxl.workbook.properties import CalcProperties
        wb.calculation = CalcProperties(fullCalcOnLoad=True)
    except Exception:
        pass
    wb.save(out_path)
    try:
        finish_xlsx(out_path)   # 수식 결과를 파일에 넣어 미리보기·보호된 보기에서도 금액이 보이게
    except Exception:
        pass
    return out_path, TOT

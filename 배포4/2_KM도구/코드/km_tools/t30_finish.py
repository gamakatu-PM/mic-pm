# -*- coding: utf-8 -*-
"""30. 완성품 만들기 - 파이썬이 할 수 있는 데까지 하고, 못 한 것만 클로드에게 넘긴다.

두 가지 모드
  [1] 점검 + 부탁서 만들기
      27·28·29번 결과를 모아 「다 됐는지」 점검하고,
      안 된 것만 모아 「_클로드부탁서_{현장}.md」 한 장을 만든다.
      그 파일 하나만 대화창에 끌어다 넣으시면 됩니다.
  [2] 받은 답 반영하기
      클로드가 준 답 csv 를 3_공통사용\\단가장\\받은답\\ 에 넣고 30번을 다시 누르면
      단가장·별칭·기호사전·배수·CB구성에 자동 반영하고 완성품을 다시 냅니다.

완성품 = 견적서 원틀에 부어넣은 엑셀. 원틀이 없으면 자체 서식으로 내고 원틀을 요청합니다.
금액·배수는 제가 정하지 않습니다.
"""
import os, re, csv, glob, shutil, collections
from common import *
import t27_drawing as D
import t28_cost as C

TOOL = '완성품'
ANS_DIR = '받은답'
ANS_HEAD = ['종류', '이름', '값', '비고']
ANS_KIND = ('단가', '별칭', '기호', '배수', 'CB구성', '수량', '확정', '회의확인', '앞으로', '앞으로완료', '견적발송', '방문', '회신')

# ---------------- 모아 읽기 ----------------

def latest(pat):
    xs = glob.glob(pat)
    xs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return xs[0] if xs else None

def gather_state(site=''):
    """27·28·29번이 낸 것을 모아 무엇이 비었는지 본다."""
    out = {'수량표': None, '금액표': None, '모르는기호': [], '단가없음': [],
           '없는모듈': [], '못읽은도면': [], '원틀': None}
    o = cfg('out')
    out['수량표'] = latest(os.path.join(o, '도면수량', '*', '*도면에적힌수량표*.csv')) \
        or latest(os.path.join(o, '도면수량', '*', '*도면수량*.csv'))
    out['금액표'] = latest(os.path.join(o, '단가붙이기', '*', '*실행견적_기구물.csv'))
    for key, pat in (('모르는기호', os.path.join(o, '도면수량', '*', '*모르는기호*.csv')),
                     ('단가없음', os.path.join(o, '단가붙이기', '*', '*단가없는것*.csv')),
                     ('없는모듈', os.path.join(o, '단가장채우기', '*', '*단가장에없는모듈*.csv')),
                     ('못읽은도면', os.path.join(o, '도면수량', '*', '_클로드에게_주실파일*.csv'))):
        p = latest(pat)
        if not p:
            continue
        rows = []
        for i, line in enumerate(read_text(p).splitlines()):
            if not line.strip() or i == 0:
                continue
            try:
                rows.append([c.strip() for c in next(csv.reader([line]))])
            except Exception:
                pass
        out[key] = rows
    out['수량출처'] = 'NOTE' if (out['수량표'] and '도면에적힌수량표' in out['수량표']) else ('블록' if out['수량표'] else '')
    out['채택수량'] = []
    if out['수량출처'] == '블록':
        for i, line in enumerate(read_text(out['수량표']).splitlines()):
            if i == 0 or not line.strip() or line.startswith('['):
                continue
            try:
                r = [c.strip() for c in next(csv.reader([line]))]
                if len(r) >= 4 and r[0] and r[3]:
                    out['채택수량'].append(r)
            except Exception:
                pass
    out['원틀'] = find_template('견적')
    try:
        import t40_meeting
        out['회의변경'] = t40_meeting.changes_for(site)
    except Exception:
        out['회의변경'] = []
    return out

# ---------------- 부탁서 ----------------

def make_request(site, st):
    """클로드에게 넘길 한 장. 이 파일만 대화창에 끌어다 넣으면 된다."""
    L = []
    a = L.append
    a('# 클로드 부탁서 - %s  (%s)' % (site, today().isoformat()))
    a('')
    a('파이썬(KM 도구)이 할 수 있는 데까지 했습니다. 아래만 채워 주십시오.')
    a('답은 아래 「답 서식」 그대로 csv 한 장으로 주시면 30번이 자동 반영합니다.')
    a('')
    a('## 지금까지 된 것')
    a('- 수량표 : %s' % (os.path.basename(st['수량표']) if st['수량표'] else '없음 (27번을 먼저 돌려야 합니다)'))
    a('- 금액표 : %s' % (os.path.basename(st['금액표']) if st['금액표'] else '없음 (28번을 먼저 돌려야 합니다)'))
    a('- 견적서 원틀 : %s' % (os.path.basename(st['원틀']) if st['원틀'] else '없음 -> 원틀을 _원틀 폴더에 넣어야 완성품이 나옵니다'))
    a('')
    n = 0
    if st.get('수량출처') == '블록':
        n += 1
        a('## %d. 수량표 확인 요청 (계통도에 수량이 없었습니다)' % n)
        a('도면에 NOTE 수량표가 없어 파이썬이 블록·글자로 센 값입니다. **검토용이지 확정 수량이 아닙니다.**')
        a('프로님이 가진 수량표(엑셀/사진)를 주시면 아래 값과 대조해 틀린 줄만 알려드립니다.')
        a('')
        a('| 품목 | 파이썬이 센 값 | 근거 |')
        a('|---|---|---|')
        for r in st['채택수량'][:60]:
            a('| %s | %s | %s |' % (r[0], r[3], r[4] if len(r) > 4 else ''))
        a('')
        a('-> 답 서식 : `수량,<품목명>,<맞는 수량>,<근거>`  (틀린 줄만)')
        a('')
    if st.get('회의변경'):
        n += 1
        a('## %d. 회의에서 바뀐 수량·규격 (PLAUD 회의록에서 자동 수집)' % n)
        a('회의록 「■ 수량·규격 변경」에 적힌 줄입니다. 수량표·도면에 반영됐는지 프로님이 확인해 주십시오. 도구는 수량을 바꾸지 않았습니다.')
        a('')
        a('| 회의일 | 협의자 | 내용 |')
        a('|---|---|---|')
        for r in st['회의변경'][:40]:
            a('| %s | %s | %s |' % (r[1], r[2], r[4].replace('|', '/')))
        a('')
        a('-> 반영할 줄만 답 서식 : `수량,<품목명>,<맞는 수량>,회의 YYMMDD`')
        a('')
    if st['단가없음']:
        n += 1
        a('## %d. 단가가 없어 금액을 비운 것' % n)
        a('| 품목 | 수량 | 왜 | 단가장 후보 |')
        a('|---|---|---|---|')
        for r in st['단가없음'][:40]:
            r = (r + ['', '', '', ''])[:4]
            a('| %s | %s | %s | %s |' % tuple(r))
        a('')
        a('-> 답 서식 : `단가,<품목 또는 형번>,<실행가 숫자>,근거`')
        a('')
    if st['없는모듈']:
        n += 1
        a('## %d. 단가장에 없는 CB 내부 모듈' % n)
        for r in st['없는모듈'][:40]:
            a('- %s  (배선도에 %s회)' % (r[0], r[1] if len(r) > 1 else ''))
        a('')
        a('-> 답 서식 : `단가,<모듈 형번>,<실행가 숫자>,근거`')
        a('')
    if st['모르는기호']:
        n += 1
        a('## %d. 도면에서 못 알아본 기호' % n)
        for r in st['모르는기호'][:40]:
            a('- [%s] %s : %s회' % tuple((r + ['', '', ''])[:3]))
        a('')
        a('-> 답 서식 : `기호,<도면기호>,<우리 품목명>,정확 또는 포함`')
        a('')
    if st['못읽은도면']:
        n += 1
        a('## %d. 파이썬이 못 읽은 도면 (이 파일들을 같이 주셔야 합니다)' % n)
        for r in st['못읽은도면'][:20]:
            a('- %s  (%s)' % tuple((r + ['', ''])[:2]))
        a('')
    if not st['원틀']:
        n += 1
        a('## %d. 견적서 원틀이 없습니다' % n)
        a('`_원틀` 폴더에 회사 견적서 원틀(갑지+내역서)을 넣어야 완성품이 나옵니다.')
        a('드라이브의 「광희동1가_견적서_Rev1」(일반형) 또는 「양양쏠비치_동별내역_통합견적」(층별형)을')
        a('xlsx 로 내려받아 넣으시면 됩니다.')
        a('')
    n += 1
    a('## %d. 배수 확인' % n)
    m = C.load_mult()
    a('- 지금 값 : 계약 %s / 견적 %s / 예산 %s / 조립비율 %s'
      % (m.get('계약배수'), m.get('견적배수'), m.get('예산배수'), m.get('조립비율')))
    a('- 광희동1가 산출서에 두 체계가 병기되어 있고 「배수 확정 전 대외 제출 금지」로 적혀 있습니다.')
    a('-> 답 서식 : `배수,예산배수,2.1,확정`')
    a('')
    a('## 답 서식 (이대로 csv 한 장)')
    a('```')
    a(','.join(ANS_HEAD))
    a('단가,EXIO MK-EX101A,15000,구매팀 확인')
    a('기호,L-SW,조명스위치(L),정확')
    a('별칭,BED SIDE PANEL(온도,BSP-2000M-T,')
    a('배수,예산배수,2.1,확정')
    a('CB구성,SMPS FLS30-12,1,CB1대당')
    a('확정,연합기숙사,공정단계,외함,외함만 납품 중')
    a('회의확인,260910_일능_홍승조부장_부분납품,확인,읽었음')
    a('앞으로,조선호텔,9/17,확정,중도금 신청서+세금계산서+사진대지 묶어 제출,배성윤 → 진현창 대리,이번 달 넘기면 잔금과 같이 밀린다,중도금 신청서 초안')
    a('앞으로완료,조선호텔,중도금 신청서')
    a('견적발송,앵커호텔,더힐이앤씨,이요한 선임,,네고 견적 9/17 발송')
    a('방문,앵커호텔,다녀옴 — 최종본 기준 확인')
    a('회신,KM-003,아니야 1개 층 선납으로')
    a('회신,KM-004,완료')
    a('```')
    a('')
    a('넣는 곳 : `3_공통사용\\단가장\\%s\\` 에 아무 이름으로 저장 -> 30번 다시 누르기' % ANS_DIR)
    od = outdir(TOOL)
    p = os.path.join(od, '_클로드부탁서_%s_%s.md' % (safe_name(site), ymd6()))
    import io as _io
    _io.open(p, 'w', encoding='utf-8').write('\n'.join(L))
    return p, n

# ---------------- 받은 답 반영 ----------------

def apply_answers(site=''):
    """받은답 폴더의 csv 를 단가장·별칭·기호사전·배수·CB구성에 반영한다.
    원본은 덮어쓰지 않는다 - 단가장은 새 버전, 나머지는 줄 추가."""
    ad = os.path.join(C.root(), ANS_DIR)
    os.makedirs(ad, exist_ok=True)
    files = [p for p in glob.glob(os.path.join(ad, '*.csv'))
             if not os.path.basename(p).startswith('_처리')]
    if not files:
        return 0, [], ad
    got = collections.defaultdict(list)
    for p in files:
        for i, line in enumerate(read_text(p).splitlines()):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            try:
                r = [c.strip() for c in next(csv.reader([line]))]
            except Exception:
                continue
            if len(r) < 3 or r[0] not in ANS_KIND:
                continue
            got[r[0]].append(r)
    log_lines = []

    # 수량 (프로님 수량표 = 도면 NOTE 와 같은 정답 취급 -> 28번이 그것을 읽는다)
    if got['수량']:
        od = outdir('도면수량')
        nm = safe_name(site or '현장')
        rows = [[ '', r[1], r[2], '프로님 답', (r[3] if len(r) > 3 else '')] for r in got['수량'] if len(r) >= 3]
        f = write_csv(os.path.join(od, '%s_도면에적힌수량표_%s_프로님답.csv' % (nm, ymd6())), rows,
                      ['기호', '내용', '수량', '쪽', '파일'])
        log_lines.append('수량표 %d줄 (프로님 답) -> %s' % (len(rows), os.path.basename(f)))

    # 확정 (프로님이 정한 값 -> 확정 대장. 추정보다 항상 우선)
    if got['확정']:
        import facts
        n_ok = 0
        for r in got['확정']:
            r = (r + ['', '', ''])[:5]
            if r[1] and r[2] and r[3]:
                facts.add(r[1], r[2], r[3], r[4] or '받은답'); n_ok += 1
        log_lines.append('확정 대장 %d줄 추가 (%s)' % (n_ok, os.path.basename(facts.path())))

    # 회의확인 (읽은 회의록 표시 -> 아침 한 장 0층에서 사라진다)
    if got['회의확인']:
        import facts
        n_ok = 0
        for r in got['회의확인']:
            r = (r + ['', '', ''])[:4]
            if r[1] and facts.check_meeting(r[1], '', r[3] or '받은답'):
                n_ok += 1
        log_lines.append('회의록 확인 %d건 표시' % n_ok)

    # 앞으로 (클로드가 회의록을 읽고 쓴 「앞으로 해야 될 것」 -> 대장 -> 42 아침 한 장·35 메일에 매일)
    if got['앞으로']:
        import facts
        n_ok = 0
        for r in got['앞으로']:
            r = (r + [''] * 8)[:8]
            if r[1] and r[4] and facts.plan_add(r[1], r[2], r[3], r[4], r[5], r[6], r[7]):
                n_ok += 1
        log_lines.append('앞으로 해야 될 것 %d줄 추가 (%s)' % (n_ok, os.path.basename(facts.plan_path())))
    if got['앞으로완료']:
        import facts
        n_ok = 0
        for r in got['앞으로완료']:
            r = (r + ['', ''])[:3]
            n_ok += facts.plan_done(r[1], r[2])
        log_lines.append('앞으로 해야 될 것 %d줄 완료' % n_ok)

    # 회신 (C안 : 클로드에게 말씀하신 것을 그대로 대장에 반영)
    if got['회신']:
        import t48_reply as RP
        n_ok = 0
        for r in got['회신']:
            r = (r + ['', ''])[:3]
            line = '%s %s' % (r[1], r[2])
            for c, cmd, out, st in RP.apply_text(line, '대화'):
                n_ok += (st == '반영')
        log_lines.append('회신 %d줄 반영' % n_ok)

    # 견적발송 / 방문 (견적을 보낸 곳을 찾아가시게 — 42·35 에 매일 뜬다)
    if got['견적발송']:
        import facts
        n_ok = 0
        for r in got['견적발송']:
            r = (r + [''] * 6)[:6]
            if r[1]:
                facts.quote_add(r[1], r[2], r[3], r[4], r[5]); n_ok += 1
        log_lines.append('견적 보낸 곳 %d줄 (%s)' % (n_ok, os.path.basename(facts.quote_path())))
    if got['방문']:
        import facts
        n_ok = 0
        for r in got['방문']:
            r = (r + ['', ''])[:3]
            n_ok += facts.quote_visit(r[1], r[2])
        log_lines.append('방문 %d곳 표시' % n_ok)

    # 배수
    if got['배수']:
        rows = C.rows_of(C.MULT)
        d = {r[0]: r for r in rows if len(r) >= 2}
        for _, k, v, *rest in [(x + [''])[:4] for x in got['배수']]:
            if k in d:
                old = d[k][1]; d[k][1] = v
                log_lines.append('배수 %s : %s -> %s' % (k, old, v))
            else:
                rows.append([k, v, '추가'])
                log_lines.append('배수 %s 추가 = %s' % (k, v))
        C.seed(C.MULT, C.MULT_DEFAULT)
        p = os.path.join(C.root(), C.MULT)
        import io as _io
        for enc in ('cp949', 'utf-8-sig'):
            try:
                with _io.open(p, 'w', encoding=enc, newline='', errors='strict') as fp:
                    w = csv.writer(fp)
                    w.writerow(['# 30번이 클로드 답을 반영했습니다 (%s)' % today().isoformat(), '', ''])
                    w.writerow(['항목', '값', '비고'])
                    for r in rows:
                        if len(r) >= 2 and r[0] != '항목':
                            w.writerow((r + ['', '', ''])[:3])
                break
            except Exception:
                continue

    # 기호사전 (27번)
    if got['기호']:
        p = D.dict_path()
        import io as _io
        add = []
        cur = read_text(p)
        for _, sym, item, *rest in [(x + [''])[:4] for x in got['기호']]:
            mode = (rest[0] if rest and rest[0] in ('정확', '포함', '무시') else '포함')
            if sym and (',' + sym + ',') not in cur:
                add.append('%s,%s,%s' % (sym, item, mode))
        if add:
            for enc in ('cp949', 'utf-8-sig'):
                try:
                    with _io.open(p, 'a', encoding=enc, errors='strict') as fp:
                        fp.write('\n# 클로드 답 반영 %s\n' % today().isoformat())
                        fp.write('\n'.join(add) + '\n')
                    break
                except Exception:
                    continue
            log_lines.append('기호사전 %d줄 추가' % len(add))

    # 별칭 (28번)
    if got['별칭']:
        p = os.path.join(C.root(), C.ALIAS_F)
        C.seed(C.ALIAS_F, C.ALIAS_DEFAULT)
        import io as _io
        add = ['%s,%s' % (r[1], r[2]) for r in got['별칭'] if len(r) >= 3 and r[1] and r[2]]
        if add:
            for enc in ('cp949', 'utf-8-sig'):
                try:
                    with _io.open(p, 'a', encoding=enc, errors='strict') as fp:
                        fp.write('\n# 클로드 답 반영 %s\n' % today().isoformat())
                        fp.write('\n'.join(add) + '\n')
                    break
                except Exception:
                    continue
            log_lines.append('별칭 %d줄 추가' % len(add))

    # CB구성
    if got['CB구성']:
        p = os.path.join(C.root(), C.CBC)
        C.seed(C.CBC, C.CBC_DEFAULT)
        import io as _io
        add = ['%s,%s,%s' % ('확인', r[1], r[2]) for r in got['CB구성'] if len(r) >= 3]
        if add:
            for enc in ('cp949', 'utf-8-sig'):
                try:
                    with _io.open(p, 'a', encoding=enc, errors='strict') as fp:
                        fp.write('\n# 클로드 답 반영 %s\n' % today().isoformat())
                        fp.write('\n'.join(add) + '\n')
                    break
                except Exception:
                    continue
            log_lines.append('CB구성 %d줄 추가' % len(add))

    # 단가 -> 단가장 새 버전
    if got['단가']:
        src = C._find_pb_file()
        rows = [(r[1], r[2]) for r in got['단가'] if len(r) >= 3 and num_ok(r[2])]
        if src and rows and os.path.splitext(src)[1].lower() in ('.xlsx', '.xlsm'):
            import t29_pricebook as P
            newp = fill_prices_xlsx(src, rows, C.load_mult())
            if newp:
                log_lines.append('단가장 새 버전 : %s (%d줄 단가 채움)'
                                 % (os.path.basename(newp), len(rows)))
        elif rows:
            p = os.path.join(C.root(), '단가_클로드답_%s.csv' % ymd6())
            write_csv(p, [[a, b] for a, b in rows], ['모듈명(형번)', '실행가'])
            log_lines.append('단가장이 엑셀이 아니라 따로 뽑았습니다 : %s' % os.path.basename(p))

    # 처리한 답 파일 표시 (지우지 않는다)
    for p in files:
        d, b = os.path.split(p)
        try:
            os.rename(p, os.path.join(d, '_처리완료_%s_%s' % (ymd6(), b)))
        except Exception:
            pass
    return sum(len(v) for v in got.values()), log_lines, ad

def num_ok(v):
    return C.num(v) is not None

def fill_prices_xlsx(src, rows, mult):
    """단가장 새 버전을 만들고, 이름이 맞는 줄의 실행가를 채운다. 없으면 주황 줄로 추가."""
    try:
        import openpyxl
        from openpyxl.styles import PatternFill
    except ImportError:
        return None
    import t29_pricebook as P
    dst = P.next_version(src)
    shutil.copy(src, dst)
    wb = openpyxl.load_workbook(dst)
    names = sorted(wb.sheetnames, key=lambda n: ('총괄' not in n, n))
    ws = wb[names[0]]
    hrow, ci = C.find_header(ws)
    if not hrow:
        return None
    green = PatternFill('solid', fgColor='D9EAD3')
    qm = mult.get('견적배수'); bm = mult.get('예산배수')
    done = set()
    for r in range(hrow + 1, ws.max_row + 1):
        mv = ws.cell(r, ci['mod']).value
        if not mv:
            continue
        nm = C.norm(mv)
        for name, cost in rows:
            if C.norm(name) and (C.norm(name) in nm or nm in C.norm(name)):
                ws.cell(r, ci['cost'], int(round(float(C.num(cost)))))
                cl = ws.cell(r, ci['cost']).column_letter
                if 'q' in ci and qm:
                    ws.cell(r, ci['q'], '=ROUND(%s%d*%s,0)' % (cl, r, qm))
                if 'b' in ci and bm:
                    ws.cell(r, ci['b'], '=ROUND(%s%d*%s,0)' % (cl, r, bm))
                for c in range(1, max(ci.values()) + 1):
                    ws.cell(r, c).fill = green
                done.add(C.norm(name))
                break
    r = ws.max_row + 1
    for name, cost in rows:
        if C.norm(name) in done:
            continue
        if 'grp' in ci: ws.cell(r, ci['grp'], '클로드답')
        ws.cell(r, ci['mod'], name)
        ws.cell(r, ci['cost'], int(round(float(C.num(cost)))))
        cl = ws.cell(r, ci['cost']).column_letter
        if 'q' in ci and qm: ws.cell(r, ci['q'], '=ROUND(%s%d*%s,0)' % (cl, r, qm))
        if 'b' in ci and bm: ws.cell(r, ci['b'], '=ROUND(%s%d*%s,0)' % (cl, r, bm))
        for c in range(1, max(ci.values()) + 1):
            ws.cell(r, c).fill = green
        r += 1
    wb.save(dst)
    return dst

# ---------------- 실행 ----------------

def run(site_hint=None):
    title('30. 완성품 만들기   (되는 건 파이썬 / 안 되는 것만 클로드)')
    C.root(); C.seed(C.MULT, C.MULT_DEFAULT); C.seed(C.CBC, C.CBC_DEFAULT)
    C.seed(C.ALIAS_F, C.ALIAS_DEFAULT)
    # 받은 답이 있으면 먼저 반영
    n, lines, ad = apply_answers(site_hint or '')
    if n:
        print('[받은 답 %d줄을 반영했습니다]' % n)
        for x in lines:
            print('  + %s' % x)
        print('')
        print('  >> 반영이 끝났습니다. 28번(금액)과 29번(단가장)을 한 번 더 돌리시면')
        print('     아래 「빈 곳」 숫자가 줄어듭니다. 아래 숫자는 지난번 결과를 본 것입니다.')
        print('')
    st = gather_state()
    site = ask('현장명 > ', site_hint or (os.path.basename(st['수량표'] or '현장미정').split('_')[0]))
    print('')
    print('%-16s %s' % ('27 수량표', os.path.basename(st['수량표']) if st['수량표'] else '없음'))
    print('%-16s %s' % ('28 금액표', os.path.basename(st['금액표']) if st['금액표'] else '없음'))
    print('%-16s %s' % ('견적서 원틀', os.path.basename(st['원틀']) if st['원틀'] else '없음'))
    print('%-16s %d건' % ('단가 비운 것', len(st['단가없음'])))
    print('%-16s %d건' % ('없는 모듈', len(st['없는모듈'])))
    print('%-16s %d건' % ('모르는 기호', len(st['모르는기호'])))
    print('%-16s %d건' % ('못 읽은 도면', len(st['못읽은도면'])))

    blank = (len(st['단가없음']) + len(st['없는모듈']) + len(st['모르는기호'])
             + len(st['못읽은도면']) + (0 if st['원틀'] else 1))
    od = outdir(TOOL)
    made = []
    if blank:
        p, cnt = make_request(site, st)
        made.append(p)
        print('')
        print('=' * 74)
        print(' 아직 %d군데가 비어 있습니다. 부탁서를 만들었습니다.' % blank)
        print(' 이 파일 하나만 클로드 대화창에 끌어다 넣으십시오.')
        print('   %s' % p)
        print('=' * 74)
        print(' 클로드 답(csv)을 받으시면 아래에 넣고 30번을 다시 누르십시오.')
        print('   %s' % ad)
    else:
        print('')
        print('빈 곳이 없습니다. 완성품을 만들 수 있습니다.')
        if st['원틀']:
            print('원틀에 부어넣기는 12번(견적서 채우기)이 합니다 -> 12번을 누르십시오.')
        made.append(write_csv(os.path.join(od, '%s_완성점검_%s.csv' % (safe_name(site), ymd6())),
                              [['수량표', os.path.basename(st['수량표'] or '')],
                               ['금액표', os.path.basename(st['금액표'] or '')],
                               ['원틀', os.path.basename(st['원틀'] or '')],
                               ['빈 곳', 0]], ['항목', '값']))

    blocks = [('지금 상태',
               [('green' if st['수량표'] else 'red', '27 수량표 : %s' % (os.path.basename(st['수량표']) if st['수량표'] else '없음')),
                ('green' if st['금액표'] else 'red', '28 금액표 : %s' % (os.path.basename(st['금액표']) if st['금액표'] else '없음')),
                ('green' if st['원틀'] else 'red', '견적서 원틀 : %s' % (os.path.basename(st['원틀']) if st['원틀'] else '없음'))]),
              ('클로드에게 넘길 것',
               [('yellow', '단가 비운 것 %d건' % len(st['단가없음'])),
                ('yellow', '단가장에 없는 모듈 %d건' % len(st['없는모듈'])),
                ('yellow', '모르는 기호 %d건' % len(st['모르는기호'])),
                ('red', '못 읽은 도면 %d건 (파일도 같이 주셔야 합니다)' % len(st['못읽은도면']))]),
              ('다음에 할 일',
               [('blue', '부탁서를 대화창에 끌어다 넣기'),
                ('blue', '답 csv 를 %s 에 넣고 30번 다시 누르기' % ANS_DIR),
                ('blue', '빈 곳이 0 이 되면 12번으로 견적서 원틀에 부어넣기')])]
    f9 = write_html(os.path.join(od, '%s_완성품점검_%s.html' % (safe_name(site), ymd6())),
                    '%s 완성품 점검' % site, blocks, files=made)
    print('')
    for x in made + [f9]:
        print('  %s' % x)
    log(TOOL, '%s 빈곳%d 반영%d' % (site, blank, n))
    if not open_file(f9):
        open_folder(od)

if __name__ == '__main__':
    run(); pause()

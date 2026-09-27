# -*- coding: utf-8 -*-
"""★작업의뢰서 초안 — 회의록에서 「→ 작업의뢰서」 줄을 골라 회사 원틀에 값만 넣어 둡니다.  (v1, 2026-09-27)

누르면 먼저 사용법이 보이고, 그다음 물어봅니다. 외울 것이 없습니다.

    어떻게 고르시겠습니까 ?
      1  하루        예) 260921
      2  기간        예) 260915 ~ 260922
      3  한 달       예) 2609  (또는 9)
      엔터  =  최근 7일

그러면 파이썬이 (AI 사용량 0)
    드라이브\회의록\incoming 의 meta.json 중 그 기간 회의만 골라
    「타부서 전달 사항」 끝이 「→ 작업의뢰서」 인 줄을 회사 원틀(MB-004)에 넣은 초안을 만듭니다.
      · 회의 × 부서 한 장.  현장명은 넣으신 이름 그대로
      · 비워 두는 것 : 납기일(노란칸) · 업체명 · 객실수 · 체크박스 · 수량 · 규격  ← 차장님이 넣으십니다
      · 이미 만든 파일은 덮어쓰지 않습니다
    끝나면 폴더와 「모음」 메모장이 열립니다. 모음은 그룹웨어에 붙여 넣을 본문입니다.

원틀(작업의뢰서 엑셀)은 _원틀 폴더에서 찾습니다. 없으면 엑셀은 안 만들고 본문 메모장만 만듭니다.
54번(t54_workorder)이 없거나 옛것이면 이 파일이 새것을 넣습니다.
"""
import os, sys, io, re, datetime, traceback

VERSION = 'v2 2026-09-27'   # v2 : t54 v2 (독립 감사 지적 고침)
HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = []

T54_SRC = '# -*- coding: utf-8 -*-\n"""\n54. 회의록 → 작업의뢰서 초안  (km_tools / t54_workorder)\n\n회의록(meta.json)의 「타부서 전달 사항」 중 줄 끝이 「→ 작업의뢰서」 인 것만 골라\n회사 원틀(MB-004)에 값만 넣은 작업의뢰서 초안을 만든다. 클로드(AI)를 쓰지 않는다 → 사용량 0.\n\n    python t54_workorder.py <meta폴더> [--day 260921 | --from 260915 --to 260922] [--out 폴더] [--template 원틀.xlsx]\n\n왜 (2026-09-27 차장님 「가장 하고 싶었던 것 세 가지」 중 2번)\n    회의 → 할 일 까지는 07:00 메일·「26년 회의록2」 가 한다. 그런데 부서는 작업의뢰서가 없으면 움직이지 않는다.\n    PLAUD 회의록은 이미 「→ 작업의뢰서」 라고 표시해 두는데, 그 뒤가 끊겨 있었다 (15번 부서메일도\n    「작업의뢰서를 별도로 발행하셔야 합니다」 로 끝났다 = 「만드세요」). 이 도구가 그 고리를 잇는다.\n\n지키는 것 (km-30 확정 규칙 · km-work-order)\n    · 원틀을 복사해 값만 넣는다. 새로 그리지 않는다. 원틀이 없으면 xlsx 는 안 만들고 복사용 txt 만 낸다\n    · 자동 : C4 기안일자(회의한 날) · G4 배성윤 · 현장명(E12, G6=E12) · D16 상대 회사·이름직함(전화)\n             · O5/O16 =IF($O$4="","",$O$4) · 본문(회의록 글 그대로)\n    · 비워 둠(차장님이 채움) : 납기일(O4 노란칸) · 업체명 · 객실수 · 계약No · 체크박스 전부 · 수량·규격 [   ]\n    · 현장명은 meta.site 그대로. 「복합회의」 처럼 현장이 아닌 것은 현장명 칸을 비우고 「현장 확인」 으로 표시\n    · 같은 회의 · 같은 부서는 한 장(순번으로 나눔), 부서가 다르면 장을 나눈다\n    · 덮어쓰지 않는다. 같은 이름 파일이 있으면 건너뛰고 「이미 있음」 으로 적는다\n    · 본문은 회의록 글에서 옮긴다. 없는 말을 지어내지 않는다 (요지 첫 줄과 「수고하세요.」 만 정해진 틀)\n\n만드는 것 (out 폴더)\n    작업의뢰서초안_<현장>_<회의날>_<부서>.xlsx   한 장씩 (원틀이 있을 때)\n    작업의뢰서초안_모음_<오늘>.txt                전부의 본문 (그룹웨어에 붙여 넣기용)\n    작업의뢰서초안_대장_<오늘>.csv                날짜|현장|부서|요청|상대|회의록|파일|상태\n"""\nfrom __future__ import print_function\nimport os, sys, io, re, json, csv, glob, shutil, datetime\nfrom copy import copy\n\nVERSION = \'v2 2026-09-27\'   # v2 : 독립 감사 지적 고침 (부서 글자 · 태그 변형 · 현장 아님 0 · 이름 충돌 · 행 높이 · 날짜 폴더)\n# v1 2026-09-27\n\n# 줄 끝 「→ 작업의뢰서」. v2 : 「-> 작업의뢰서」 「→ 작업의뢰서 필요」 「(→ 작업의뢰서)」 「→ 작업의뢰서.」 도 받는다 (감사 지적)\nTAG_RE = re.compile(r\'\\(?\\s*(?:→|->|=>|⇒)\\s*작업\\s*의뢰서\\s*(?:필요|요청|발행|작성)?\\s*[.)\\]]*\\s*$\')\n# 「1. 설계 / 내용」 「2. 제작 — 내용」 「3. 설계 · 내용」 「4. 설계: 내용」 「1. 설비(난방) — 내용」\n# v2 : 구분자 뒤에 빈칸이 있어야 자른다 → 「설계/개발 · 매핑」 은 부서 「설계/개발」, 「전기·통신 — 확인」 은 「전기·통신」,\n#      「설비(난방/급수) — 확인」 은 「설비(난방/급수)」 (감사 지적 : 부서 글자가 잘려 다른 부서 요청이 섞였다)\nLINE_RE = re.compile(r\'^\\s*[-·•]?\\s*(?:\\d+\\s*[.)]\\s*)?(?P<dept>[^\\s:][^:]{0,19}?)\\s*(?:(?:—|–|/|·|-|\\|)\\s+|\\s(?:—|–|/|·|-|\\|)|:\\s*)(?P<what>.+?)\\s*$\')\n\n# 회사 서식 수신부서 칸에 있는 부서 (체크는 차장님이 하신다. 여기서는 「사내 부서인가」 표시만)\nINHOUSE = {\'설계\': \'디자인&설계\', \'디자인\': \'디자인&설계\', \'개발\': \'개발\', \'구매\': \'구매\', \'제작\': \'제작\',\n           \'시공\': \'시공\', \'영업\': \'영업\', \'AS\': \'고객지원\', \'고객지원\': \'고객지원\'}\n\nNOT_A_SITE = (\'복합회의\', \'확인필요\', \'확인 필요\', \'현장미정\', \'미정\', \'수금채크\', \'수금체크\', \'삭제요망\')\nNOT_A_SITE_IN = (\'복합회의\', \'확인필요\', \'현장미정\', \'삭제요망\', \'수금채크\', \'수금체크\')   # v2 : 「복합회의 (앵커·연합)」 처럼 붙어 있어도\n\nCHECK_CELLS = (\'F5\', \'C7\', \'C8\', \'C9\', \'C10\', \'C14\')\nLINE_LIMIT = 116          # km-work-order : 실작성 최대 폭. 132 넘으면 인쇄에서 잘린다\nYELLOW = \'FFFFFF00\'\n\n\n# ── 회의록 읽기 ─────────────────────────────────────────────\ndef _txt(v):\n    return re.sub(r\'^\\s*[-·•]\\s*\', \'\', str(v or \'\')).strip()\n\n\ndef _list(v):\n    if v is None:\n        return []\n    if isinstance(v, str):\n        return [x for x in (_txt(s) for s in v.split(\'\\n\')) if x]\n    out = []\n    for it in v:\n        if isinstance(it, (list, tuple)):\n            s = \' | \'.join(_txt(c) for c in it if _txt(c))\n        else:\n            s = _txt(it)\n        if s:\n            out.append(s)\n    return out\n\n\ndef clear_checks(s):\n    """「( V )선투입자재」 「(V )  디자인&설계」 → 괄호 안 V 만 빈칸으로. 괄호 폭은 그대로."""\n    return re.sub(r\'\\((\\s*)[Vv✓](\\s*)\\)\', lambda m: \'(%s %s)\' % (m.group(1), m.group(2)), s)\n\n\ndef is_site(name):\n    n = re.sub(r\'\\s+\', \'\', name or \'\')\n    if not n or any(x in n for x in NOT_A_SITE_IN):\n        return False\n    return all(n != re.sub(r\'\\s+\', \'\', x) for x in NOT_A_SITE)\n\n\ndef parse_line(line):\n    """타부서 한 줄 → (부서, 요청) 또는 None (작업의뢰서 표시가 없는 줄)"""\n    s = _txt(line)\n    if not TAG_RE.search(s):\n        return None\n    body = TAG_RE.sub(\'\', s).strip()\n    m = LINE_RE.match(body)\n    if not m:\n        return (\'확인필요\', re.sub(r\'^\\d+\\s*[.)]\\s*\', \'\', body))\n    dept = m.group(\'dept\').strip()\n    return (dept, m.group(\'what\').strip())\n\n\ndef dept_key(dept):\n    """묶는 데만 쓴다 (글자는 원문대로 남긴다). 괄호 안과 빈칸만 뗀다.\n    「설비(난방)」 → 「설비」 / 「설계/개발」 → 「설계/개발」 (v2 : 설계 장에 개발 요청이 섞이지 않게)"""\n    k = re.sub(r\'\\s+\', \'\', re.sub(r\'\\(.*?\\)\', \'\', dept or \'\'))\n    return k or (dept or \'\').strip()\n\n\ndef inhouse(dept):\n    k = dept_key(dept)\n    for a, b in INHOUSE.items():\n        if k.startswith(a):\n            return b\n    return \'\'\n\n\ndef phone_fmt(p):\n    d = re.sub(r\'\\D\', \'\', p or \'\')\n    if len(d) == 11:\n        return \'%s-%s-%s\' % (d[:3], d[3:7], d[7:])\n    if len(d) == 10:\n        return \'%s-%s-%s\' % (d[:3], d[3:6], d[6:])\n    return p or \'\'\n\n\ndef counterpart(m):\n    """D16 업체담당자/연락처. 회사 칸에 안건이 통째로 들어온 자료는 버린다 (t52 who 와 같은 기준)."""\n    comp = (m.get(\'company\') or \'\').strip()\n    if len(comp) > 20 or \',\' in comp:\n        comp = \'\'\n    name = (m.get(\'name\') or \'\').strip()\n    rank = (m.get(\'rank\') or \'\').strip()\n    base = (name + \' \' + rank).strip() if name else (m.get(\'person\') or \'\').strip()\n    if comp and comp == base:\n        comp = \'\'\n    who = \' \'.join(x for x in (comp, base) if x).strip()\n    ph = phone_fmt(m.get(\'phone\'))\n    return (who + (\' (%s)\' % ph if ph else \'\')).strip()\n\n\ndef read_one(path):\n    with io.open(path, \'r\', encoding=\'utf-8\') as f:\n        d = json.load(f)\n    m = d.get(\'meta\') or {}\n    s1 = (d.get(\'sec\') or {}).get(\'1\') or {}\n    s2 = (d.get(\'sec\') or {}).get(\'2\') or {}\n    site = (m.get(\'site\') or s1.get(\'현장\') or \'\').strip()\n    reqs, odd = [], []\n    for ln in _list(s2.get(\'타부서 전달 사항\')):\n        p = parse_line(ln)\n        if p:\n            reqs.append(p)\n        elif \'의뢰서\' in ln:\n            odd.append(ln)          # v2 : 「의뢰서」 는 있는데 표시 모양이 달라 못 읽은 줄 — 조용히 버리지 않고 모음·대장에 알린다\n    todos = []\n    for ln in _list(s2.get(\'할 일\')):\n        parts = [x.strip() for x in ln.split(\'|\')]\n        if len(parts) >= 2:\n            todos.append((parts[0], parts[1], parts[2] if len(parts) > 2 else \'\'))\n    decisions = []\n    for it in (s1.get(\'안건목록\') or []):\n        if isinstance(it, dict):\n            dc = _txt(it.get(\'decision\'))\n            if dc and not re.match(r\'^(없음|해당\\s*없음|미정)(\\s*[—\\-–:]|$)\', dc):\n                decisions.append(dc)\n    return {\'file\': os.path.basename(path), \'site\': site, \'ymd\': (m.get(\'ymd\') or \'\').strip(),\n            \'hm\': (m.get(\'hm\') or \'\').strip(), \'who\': counterpart(m), \'who_short\': counterpart(dict(m, phone=\'\')),\n            \'person\': (m.get(\'person\') or \'\').strip(), \'name\': (m.get(\'name\') or \'\').strip(),\n            \'reqs\': reqs, \'odd\': odd, \'todos\': todos, \'decisions\': decisions}\n\n\ndef collect(meta_dir, d_from=None, d_to=None):\n    recs, skipped = [], []\n    for root, _d, files in os.walk(meta_dir):\n        for fn in sorted(files):\n            if not fn.endswith(\'meta.json\'):\n                continue\n            if fn.startswith(\'_삭제요망\'):\n                skipped.append((fn, \'삭제요망\'))\n                continue\n            try:\n                r = read_one(os.path.join(root, fn))\n            except Exception as e:\n                skipped.append((fn, \'읽기실패 %s\' % e))\n                continue\n            if (d_from and (not r[\'ymd\'] or r[\'ymd\'] < d_from)) or (d_to and (not r[\'ymd\'] or r[\'ymd\'] > d_to)):\n                continue\n            recs.append(r)\n    recs.sort(key=lambda r: (r[\'ymd\'], r[\'hm\'], r[\'site\']))\n    return recs, skipped\n\n\n# ── 의뢰서 한 장 계획 ───────────────────────────────────────\ndef _md(ymd):\n    return \'%d월 %d일\' % (int(ymd[2:4]), int(ymd[4:6])) if re.match(r\'^\\d{6}$\', ymd or \'\') else \'\'\n\n\ndef plan(recs):\n    """회의 × 부서 → 한 장. 순서는 회의 날·시각, 부서는 회의록에 처음 나온 순서."""\n    out = []\n    for r in recs:\n        if not r[\'reqs\']:\n            continue\n        order, bag = [], {}\n        for dept, what in r[\'reqs\']:\n            k = dept_key(dept)\n            if k not in bag:\n                order.append(k)\n                bag[k] = {\'dept\': dept, \'items\': []}\n            bag[k][\'items\'].append(what)\n        for k in order:\n            g = bag[k]\n            # 같은 부서 할 일만. 「작업의뢰서 작성」 같은 이 문서 자체를 가리키는 할 일은 뺀다\n            rel = [t for t in r[\'todos\'] if k and k in t[2] and \'의뢰서\' not in t[1]]\n            out.append({\'rec\': r, \'dept\': g[\'dept\'], \'key\': k, \'items\': g[\'items\'], \'todos\': rel,\n                        \'site_ok\': is_site(r[\'site\']), \'inhouse\': inhouse(g[\'dept\'])})\n    return out\n\n\ndef body_lines(p):\n    """[(순번 or None, 한 줄)] . 회의록 글을 옮기고, 수량·규격은 [   ] 로 비운다."""\n    r = p[\'rec\']\n    site = r[\'site\'] if p[\'site_ok\'] else \'[현장 확인]\'\n    head = \'%s 현장 %s %s 협의 결과, 아래 작업을 요청 드립니다.\' % (site, _md(r[\'ymd\']), r[\'person\'] or r[\'who\'] or \'\')\n    lines = [(1, re.sub(r\'\\s+\', \' \', head).strip())]\n    n = 1\n    for what in p[\'items\']:\n        n += 1\n        lines.append((n, \'%s : %s\' % (p[\'dept\'], what)))\n    lines.append((None, \' -수량 : [   ]    -규격·사양 : [   ]\'))\n    if p[\'todos\']:\n        lines.append((None, \'관련 할 일 (회의록)\'))\n        for due, what, _who in p[\'todos\']:\n            d = \'\' if due in (\'\', \'미정\') else \'  (기한 %s)\' % due\n            lines.append((None, \' -%s%s\' % (what, d)))\n    if r[\'decisions\']:\n        lines.append((None, \'협의 결정 (회의록)\'))\n        for dc in r[\'decisions\'][:5]:\n            lines.append((None, \' -%s\' % dc))\n    lines.append((None, \'근거 : %s 협의록\' % \' \'.join(x for x in (r[\'ymd\'], r[\'hm\'], r[\'who_short\'] or r[\'person\']) if x)))\n    lines.append((None, \'수고하세요.\'))\n    return lines\n\n\ndef _w(s):\n    return sum(2 if ord(c) > 0x1100 else 1 for c in str(s))\n\n\ndef split_line(text, limit=LINE_LIMIT):\n    """km-work-order fill_workorder.split_line 과 같은 규칙 (폭 116, 이어지는 줄은 두 칸 들여쓰기)."""\n    text = str(text).rstrip()\n    if _w(text) <= limit:\n        return [text]\n    out, rest = [], text\n    while _w(rest) > limit:\n        cut = len(rest)\n        while _w(rest[:cut]) > limit:\n            cut -= 1\n        seg = rest[:cut]\n        for sep in (\' // \', \', \', \',\', \' \'):\n            q = seg.rfind(sep)\n            if q > cut * 0.45:\n                cut = q + (len(sep) if sep != \' \' else 1)\n                break\n        out.append(rest[:cut].rstrip())\n        rest = \'  \' + rest[cut:].lstrip()\n    if rest.strip():\n        out.append(rest)\n    return out\n\n\n# ── 원틀 찾기 · 채우기 ─────────────────────────────────────\ndef find_template(explicit=None):\n    """1) --template 2) 환경변수 KM_WO_TEMPLATE 3) _원틀 폴더(설정.ini) 4) km-work-order 스킬 자산.\n    없으면 None → xlsx 를 만들지 않는다 (원틀을 새로 그리지 않는다)."""\n    cands = [explicit, os.environ.get(\'KM_WO_TEMPLATE\')]\n    try:\n        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n        import common as C\n        root = C.cfg(\'template\')\n        if root and os.path.isdir(root):\n            for p in sorted(glob.glob(os.path.join(root, \'**\', \'*.xlsx\'), recursive=True)):\n                b = os.path.basename(p)\n                if (\'작업의뢰서\' in b or \'MB-004\' in b or \'workorder\' in b) and not b.startswith(\'~$\'):\n                    cands.append(p)\n    except Exception:\n        pass\n    cands += sorted(glob.glob(os.path.expanduser(\'~/.claude/skills/**/km-work-order/assets/workorder_template.xlsx\'),\n                              recursive=True))\n    cands += sorted(glob.glob(\'/root/.claude/skills/**/km-work-order/assets/workorder_template.xlsx\', recursive=True))\n    for c in cands:\n        if c and os.path.isfile(c):\n            return c\n    return None\n\n\ndef _sheet(wb):\n    for n in wb.sheetnames:\n        if \'그룹웨어\' in n:\n            return wb[n]\n    for ws in wb.worksheets:\n        if \'작\' in str(ws[\'A1\'].value or \'\') and \'서\' in str(ws[\'A1\'].value or \'\'):\n            return ws\n    return wb.worksheets[0]\n\n\ndef _safe(s, n=40):\n    s = re.sub(r\'[\\\\/:*?"<>|\\[\\]\\s]+\', \'_\', s or \'\').strip(\'_\')\n    return s[:n] or \'미정\'\n\n\ndef fill_xlsx(tpl, out_path, p, lines):\n    import openpyxl\n    from openpyxl.styles import Alignment, PatternFill\n    from openpyxl.worksheet.properties import PageSetupProperties\n    shutil.copy(tpl, out_path)\n    wb = openpyxl.load_workbook(out_path)\n    ws = _sheet(wb)\n    for n in list(wb.sheetnames):             # 작성예시 등 다른 시트는 뺀다 (원틀 시트는 그대로)\n        if wb[n] is not ws:\n            del wb[n]\n    r = p[\'rec\']\n    ws.title = _safe(\'%s(%s)\' % (r[\'site\'] if p[\'site_ok\'] else \'현장확인\', p[\'dept\']), 31)\n    if re.match(r\'^\\d{6}$\', r[\'ymd\']):\n        ws[\'C4\'] = datetime.datetime(2000 + int(r[\'ymd\'][:2]), int(r[\'ymd\'][2:4]), int(r[\'ymd\'][4:6]))\n    ws[\'G4\'] = \'배성윤\'\n    ws[\'O4\'] = None\n    ws[\'O4\'].fill = PatternFill(\'solid\', fgColor=YELLOW)      # 납기일 = 차장님이 넣는다\n    ws[\'O5\'] = \'=IF($O$4="","",$O$4)\'\n    ws[\'O16\'] = \'=IF($O$4="","",$O$4)\'\n    ws[\'E12\'] = r[\'site\'] if p[\'site_ok\'] else None\n    ws[\'G6\'] = \'=E12\' if p[\'site_ok\'] else None     # v2 : 현장이 아닐 때 =E12 는 「0」 으로 보인다 (감사 지적)\n    if r[\'who\']:\n        ws[\'D16\'] = r[\'who\']\n    # 체크박스(F5·C7·C8·C9·C10·C14) : 전부 빈 괄호로. 차장님이 V 를 넣으신다 (km-30)\n    #   ★ 원틀 파일에 예전 작성분의 V 가 남아 있다 (2026-09-27 렌더 검수에서 발견 : 기타·선발행·계약·유상·개발·구매·택배).\n    #     그대로 두면 차장님이 정하지 않은 체크가 결재에 올라간다 → 괄호 안 V 만 지운다 (글자 배치는 그대로)\n    for k in CHECK_CELLS:\n        v = ws[k].value\n        if isinstance(v, str):\n            ws[k] = clear_checks(v)\n\n    flat = []\n    for no, txt in lines:\n        parts = split_line(txt)\n        flat.append((no, parts[0]))\n        flat.extend((None, x) for x in parts[1:])\n\n    last_body = 35\n    if len(flat) > 15:                        # km-work-order make_workorder 와 같은 순서 (병합 → 삽입 → 서식 → 로고)\n        extra = len(flat) - 15                # v2 : 본문 뒤 빈 줄 2개도 남게 (감사 지적)\n        for mg in [mg for mg in ws.merged_cells.ranges if mg.min_row >= 19]:\n            ws.unmerge_cells(str(mg))\n        # v2 : insert_rows 는 행 높이를 안 옮긴다 → 35행부터 아래 높이를 적어 두었다가 밀린 자리에 다시 준다\n        below = dict((rr, ws.row_dimensions[rr].height) for rr in range(35, ws.max_row + 1))\n        ws.insert_rows(35, extra)\n        for rr, hgt in sorted(below.items(), reverse=True):\n            ws.row_dimensions[rr + extra].height = hgt\n        src = 34\n        for rr in range(35, 35 + extra):\n            ws.row_dimensions[rr].height = ws.row_dimensions[src].height or 25.2\n            for col in range(1, 19):\n                s, d = ws.cell(src, col), ws.cell(rr, col)\n                d.font = copy(s.font); d.border = copy(s.border)\n                d.fill = copy(s.fill); d.alignment = copy(s.alignment)\n        for img in ws._images:\n            img.anchor._from.row += extra; img.anchor.to.row += extra\n        last_body = 35 + extra\n        for rr in range(19, last_body + 1):\n            ws.merge_cells(\'B%d:R%d\' % (rr, rr))\n\n    row = 19\n    for no, txt in flat:\n        if no:\n            ws[\'A%d\' % row] = no\n        ws[\'B%d\' % row] = txt\n        ws[\'B%d\' % row].alignment = Alignment(horizontal=\'left\', vertical=\'center\')\n        if \'[   ]\' in txt:\n            ws[\'B%d\' % row].fill = PatternFill(\'solid\', fgColor=YELLOW)\n        row += 1\n\n    first_del = row + 2\n    if first_del <= last_body:\n        n_del = last_body - first_del + 1\n        for mg in [mg for mg in ws.merged_cells.ranges if mg.min_row >= first_del]:\n            ws.unmerge_cells(str(mg))\n        ws.delete_rows(first_del, n_del)\n        for img in ws._images:\n            img.anchor._from.row -= n_del\n            img.anchor.to.row -= n_del\n        tail = first_del\n    else:\n        tail = last_body + 1\n    ws.print_area = \'A1:R%d\' % tail\n    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)\n    ws.page_setup.fitToWidth = 1\n    ws.page_setup.fitToHeight = 1\n    wb.save(out_path)\n    return tail\n\n\n# ── 실행 ───────────────────────────────────────────────────\ndef run(meta_dir, d_from=None, d_to=None, out=None, template=None, today=None):\n    today = today or datetime.date.today().strftime(\'%y%m%d\')\n    out = out or os.path.join(os.getcwd(), \'작업의뢰서초안\', today)\n    os.makedirs(out, exist_ok=True)\n    recs, skipped = collect(meta_dir, d_from, d_to)\n    plans = plan(recs)\n    tpl = find_template(template)\n    try:\n        import openpyxl  # noqa\n    except Exception:\n        tpl = None\n    rows, txt = [], []\n    made = skipped_same = 0\n    used = set()\n    for p in plans:\n        r = p[\'rec\']\n        lines = body_lines(p)\n        site_lbl = r[\'site\'] if p[\'site_ok\'] else \'현장확인\'\n        # 같은 현장·같은 날·같은 부서 회의가 여러 건일 수 있다 (2026-09-21 앵커호텔 설계 3건) → 시각·상대로 가른다\n        # v2 : 이름이 회의마다 늘 같게 (감사 지적 : -2·-3 을 순서로 붙이면 회의가 늘 때 다른 회의 파일을 「이미 있음」 으로 봤다)\n        #      시각이 있으면 시각, 없으면 상대 이름 + 회의록 파일 표식 4자리(회의록 파일 이름에서 나옴 → 늘 같다)\n        fid = \'%04x\' % (sum(ord(c) * (i + 1) for i, c in enumerate(r[\'file\'])) % 65536)\n        hm = re.sub(r\'\\D\', \'\', r[\'hm\'])\n        tag = hm or \'%s_%s\' % (_safe(r[\'name\'] or r[\'person\'].split(\' \')[0], 10), fid)\n        name = \'작업의뢰서초안_%s_%s_%s_%s\' % (_safe(site_lbl, 20), r[\'ymd\'], tag, _safe(p[\'key\'], 10))\n        if name in used:                       # 같은 시각·같은 부서 회의 두 건 (중복 올림 등) → 표식을 붙인다\n            name = \'%s_%s\' % (name, fid)\n        used.add(name)\n        xp = os.path.join(out, name + \'.xlsx\')\n        # v2 : 결과 폴더가 날짜별이라 다음 날 다시 돌리면 같은 초안을 또 만들었다 → 옆 날짜 폴더도 본다\n        before = [q for q in glob.glob(os.path.join(os.path.dirname(os.path.abspath(out)), \'*\', name + \'.xlsx\'))\n                  if os.path.dirname(os.path.abspath(q)) != os.path.abspath(out)]\n        state = \'\'\n        if tpl:\n            if os.path.exists(xp) or before:\n                state = \'이미 있음\'\n                skipped_same += 1\n            else:\n                fill_xlsx(tpl, xp, p, lines)\n                state = \'만듦\'\n                made += 1\n        else:\n            state = \'원틀 없음 (본문만)\'\n        flags = []\n        if not p[\'site_ok\']:\n            flags.append(\'현장 확인 (%s)\' % (r[\'site\'] or \'빈칸\'))\n        if not p[\'inhouse\']:\n            flags.append(\'받는 부서 확인 (「%s」 — 서식 수신부서 칸에 없는 이름)\' % p[\'dept\'])\n        rows.append([r[\'ymd\'], r[\'site\'], p[\'dept\'], \' / \'.join(p[\'items\']), r[\'who\'], r[\'file\'],\n                     os.path.basename(xp) if tpl else \'\', state, \'; \'.join(flags)])\n        txt.append(\'━━ %s · %s · %s  (%s)\' % (site_lbl, _md(r[\'ymd\']), p[\'dept\'], state))\n        if flags:\n            txt.append(\'   ※ \' + \' / \'.join(flags))\n        txt.append(\'   납기일 : [   ]   업체명 : [   ]   객실수 : [   ]   체크박스 : 차장님\')\n        txt.append(\'   업체담당자 : %s\' % (r[\'who\'] or \'[   ]\'))\n        for no, t in lines:\n            for i, part in enumerate(split_line(t)):\n                txt.append(\'%3s  %s\' % (no if (no and i == 0) else \'\', part))\n        txt.append(\'\')\n    odd = [(r, ln) for r in recs for ln in r.get(\'odd\', [])]\n    if odd:\n        txt.append(\'━━ 「의뢰서」 는 있는데 표시 모양이 달라 초안을 안 만든 줄 %d개 — 보시고 필요하면 말씀해 주십시오\' % len(odd))\n        for r, ln in odd:\n            txt.append(\'   %s %s : %s\' % (r[\'ymd\'], r[\'site\'], ln))\n            rows.append([r[\'ymd\'], r[\'site\'], \'\', ln, r[\'who\'], r[\'file\'], \'\', \'못 읽음 (표시 모양)\', \'「→ 작업의뢰서」 모양이 아님\'])\n        txt.append(\'\')\n    head = [\'[KM] 작업의뢰서 초안 %s  —  회의 %d건 중 「→ 작업의뢰서」 %d장\' % (today, len(recs), len(plans)),\n            \'원틀 : %s\' % (os.path.basename(tpl) if tpl else \'없음 → xlsx 안 만듦. 아래 본문을 그룹웨어 원틀에 붙여 넣으십시오\'),\n            \'넣으실 것 : 납기일(O4 노란칸 하나만 치면 출고요청일·현장납기일이 따라옵니다) · 업체명 · 객실수 · 체크박스 V · 수량·규격 [   ]\',\n            \'\']\n    tp = os.path.join(out, \'작업의뢰서초안_모음_%s.txt\' % today)\n    io.open(tp, \'w\', encoding=\'utf-8\').write(\'\\n\'.join(head + txt) + \'\\n\')\n    cp = os.path.join(out, \'작업의뢰서초안_대장_%s.csv\' % today)\n    with io.open(cp, \'w\', encoding=\'utf-8-sig\', newline=\'\') as f:\n        w = csv.writer(f)\n        w.writerow([\'회의날\', \'현장\', \'부서\', \'요청\', \'상대\', \'회의록\', \'파일\', \'상태\', \'확인할 것\'])\n        w.writerows(rows)\n    rep = {\'version\': VERSION, \'today\': today, \'meetings\': len(recs), \'sheets\': len(plans), \'made\': made, \'odd\': len(odd),\n           \'same\': skipped_same, \'template\': tpl or \'\', \'skipped\': skipped, \'out\': out, \'txt\': tp, \'csv\': cp}\n    io.open(os.path.join(out, \'작업의뢰서초안_자가진단_%s.json\' % today), \'w\', encoding=\'utf-8\').write(\n        json.dumps(rep, ensure_ascii=False, indent=1))\n    return rep\n\n\ndef main(argv):\n    if not argv or argv[0] in (\'-h\', \'--help\'):\n        print(__doc__)\n        return 0\n    meta_dir = argv[0]\n    opt = {}\n    i = 1\n    while i < len(argv):\n        if argv[i].startswith(\'--\') and i + 1 < len(argv):\n            opt[argv[i][2:]] = argv[i + 1]\n            i += 2\n        else:\n            i += 1\n    d_from, d_to = opt.get(\'from\'), opt.get(\'to\')\n    if opt.get(\'day\'):\n        d_from = d_to = opt[\'day\']\n    rep = run(meta_dir, d_from, d_to, opt.get(\'out\'), opt.get(\'template\'), opt.get(\'today\'))\n    print(\'54. 작업의뢰서 초안 %s\' % VERSION)\n    print(\'회의 %d건 → 의뢰서 %d장 (새로 만듦 %d · 이미 있음 %d)\' % (rep[\'meetings\'], rep[\'sheets\'], rep[\'made\'], rep[\'same\']))\n    print(\'원틀 : %s\' % (rep[\'template\'] or \'없음 (본문 txt 만)\'))\n    print(\'모음 : %s\' % rep[\'txt\'])\n    print(\'대장 : %s\' % rep[\'csv\'])\n    return 0\n\n\nif __name__ == \'__main__\':\n    sys.exit(main(sys.argv[1:]))\n'
NEED = {'t54_workorder': ('v2', T54_SRC)}


def say(s=''):
    print(s)
    NOTE.append(s)


def _ver_num(v):
    m = re.match(r'v(\d+)', str(v or ''))
    return int(m.group(1)) if m else 0


def find_tools():
    for p in (os.path.join(HERE, '코드', 'km_tools'),
              os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
              os.path.join(HERE, 'km_tools')):
        if os.path.isdir(p):
            return p
    return ''


def ensure_tool(tools, name):
    """도구가 없거나 옛 판이면 이 파일 안의 새것을 써 넣는다."""
    need_v, src = NEED[name]
    p = os.path.join(tools, name + '.py')
    old = ''
    if os.path.isfile(p):
        try:
            with io.open(p, 'r', encoding='utf-8') as f:
                m = re.search(r"VERSION\s*=\s*'(v\d+)", f.read())
            old = m.group(1) if m else 'v0'
        except Exception:
            old = 'v0'
    if not old or _ver_num(old) < _ver_num(need_v):
        with io.open(p, 'w', encoding='utf-8') as f:
            f.write(src)
        return '%s 를 새로 넣었습니다 (%s → %s)' % (name, old or '없음', need_v)
    return ''


def load_tools():
    tools = find_tools()
    if not tools:
        tools = os.path.join(HERE, '코드', 'km_tools')
        os.makedirs(tools)
    notes = [n for n in [ensure_tool(tools, 't54_workorder')] if n]
    if tools not in sys.path:
        sys.path.insert(0, tools)
    if 't54_workorder' in sys.modules:
        del sys.modules['t54_workorder']
    import t54_workorder as W
    return W, tools, notes


def ask(q, default=''):
    try:
        v = input(q).strip()
    except Exception:
        v = ''
    return v or default


def norm_ymd(v, fallback):
    """260901 / 26-09-01 / 2026-09-01 / 2026.9.1 을 다 받아 260901 로."""
    s = str(v or '').strip()
    m = re.match(r'^(\d{2}|\d{4})\D+(\d{1,2})\D+(\d{1,2})$', s)
    if m:
        return '%s%02d%02d' % (m.group(1)[-2:], int(m.group(2)), int(m.group(3)))
    d = re.sub(r'\D', '', s)
    if len(d) == 8:
        d = d[2:]
    if len(d) == 6 and d.isdigit():
        return d
    return fallback


def norm_month(v, today):
    """2609 / 26-09 / 2026-09 / 9 / 9월 → ('260901','260930')"""
    s = str(v or '').strip().replace('월', '')
    d = re.sub(r'\D', '', s)
    if len(d) == 6:
        d = d[2:]
    if len(d) == 4 and d.isdigit():
        yymm = d
    elif 1 <= len(d) <= 2 and d.isdigit() and 1 <= int(d) <= 12:
        yymm = '%s%02d' % (today.strftime('%y'), int(d))
    else:
        yymm = today.strftime('%y%m')
    y, m = 2000 + int(yymm[:2]), int(yymm[2:4])
    last = (datetime.date(y + (m == 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)).day
    return '%s01' % yymm, '%s%02d' % (yymm, last)


def choose(today=None):
    today = today or datetime.date.today()
    ty = today.strftime('%y%m%d')
    say(' 어떻게 고르시겠습니까 ?')
    say('   1  하루        예) 260921')
    say('   2  기간        예) 260915 ~ 260922')
    say('   3  한 달       예) 2609  (또는 9)')
    say('   엔터  =  최근 7일')
    c = ask(' 번호 : ', '')
    if c == '1':
        d = norm_ymd(ask('   어느 날 ? (예 260921) : ', ty), ty)
        return d, d, '하루 %s' % d
    if c == '2':
        d7 = (today - datetime.timedelta(days=7)).strftime('%y%m%d')
        a = norm_ymd(ask('   언제부터 ? (엔터=%s) : ' % d7, d7), d7)
        b = norm_ymd(ask('   언제까지 ? (엔터=오늘 %s) : ' % ty, ty), ty)
        if a > b:
            a, b = b, a
        return a, b, '기간 %s ~ %s' % (a, b)
    if c == '3':
        a, b = norm_month(ask('   몇 월 ? (예 2609 또는 9, 엔터=이번 달) : ', ''), today)
        return a, b, '한 달 %s ~ %s' % (a, b)
    d7 = (today - datetime.timedelta(days=7)).strftime('%y%m%d')
    return d7, ty, '최근 7일 %s ~ %s' % (d7, ty)


def out_folder(tools, today):
    """결과 자리 : 도구모음의 표준 결과 폴더(설정.ini out) 아래 작업의뢰서초안\\YYMMDD. 못 찾으면 이 폴더 옆."""
    try:
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import common as C
        return C.outdir('작업의뢰서초안')
    except Exception:
        return os.path.join(HERE, '_작업의뢰서초안', today.strftime('%y%m%d'))


def open_it(p):
    try:
        os.startfile(p)
    except Exception:
        pass


def run(d_from, d_to, drive=None, out=None, today=None, template=None, opener=open_it):
    """시험에서도 부를 수 있게 물어보는 부분과 떼어 놓았다."""
    today = today or datetime.date.today()
    W, tools, notes = load_tools()
    for n in notes:
        say(' ' + n)
    if drive is None:
        try:
            import t51_driveup as DU
            drive = DU.drive_root()
        except Exception:
            drive = ''
    if not drive:
        say('★ 구글 드라이브 폴더를 못 찾았습니다. 드라이브 데스크톱이 켜져 있는지 보십시오.')
        return None
    meta_dir = os.path.join(drive, '회의록', 'incoming')
    if not os.path.isdir(meta_dir):
        say('★ %s 가 없습니다. 먼저 ★회의록_한방에 로 회의록을 올리십시오.' % meta_dir)
        return None
    out = out or out_folder(tools, today)
    rep = W.run(meta_dir, d_from, d_to, out=out, template=template, today=today.strftime('%y%m%d'))
    say(' 기간 : %s ~ %s' % (d_from, d_to))
    say(' 회의 %d건 → 작업의뢰서 초안 %d장 (새로 %d · 이미 있음 %d)' % (rep['meetings'], rep['sheets'], rep['made'], rep['same']))
    if not rep['template']:
        say(' ★ 작업의뢰서 원틀을 못 찾아 엑셀은 안 만들었습니다. 본문 메모장만 있습니다.')
        say('   _원틀 폴더에 「작업의뢰서」 가 이름에 든 엑셀을 한 번만 넣어 주십시오.')
    else:
        say(' 원틀 : %s' % os.path.basename(rep['template']))
    if not rep['sheets']:
        say('')
        say(' 그 기간 회의록에 「→ 작업의뢰서」 줄이 없습니다. 날짜를 넓혀 보십시오.')
        return rep
    say('')
    say(' 넣으실 것 : 납기일(O4 노란칸) · 업체명 · 객실수 · 체크박스 V · 수량·규격 [   ]')
    say(' 결과 폴더 : %s' % rep['out'])
    opener(rep['out'])
    opener(rep['txt'])
    return rep


def main():
    say('=' * 60)
    say(' 작업의뢰서 초안  %s        %s' % (VERSION, datetime.datetime.now().strftime('%Y-%m-%d %H:%M')))
    say('=' * 60)
    for ln in (__doc__ or '').strip().split('\n')[2:]:
        say(' ' + ln)
    say('-' * 60)
    d_from, d_to, what = choose()
    say('')
    say(' → %s' % what)
    say('-' * 60)
    try:
        run(d_from, d_to)
    except Exception:
        say('★ 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        for ln in traceback.format_exc().split('\n'):
            say('  ' + ln)
    say('=' * 60)


def save_note():
    p = os.path.join(HERE, '작업의뢰서_초안_결과.txt')
    try:
        with io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n') as f:
            f.write('\n'.join(NOTE))
    except Exception:
        pass


if __name__ == '__main__':
    try:
        main()
    finally:
        save_note()
        try:
            input('\n엔터를 누르면 닫힙니다... ')
        except Exception:
            pass

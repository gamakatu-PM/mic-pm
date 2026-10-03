# -*- coding: utf-8 -*-
r"""★엑셀책 — 회의록 txt 나 도면 pdf 를 이 파일 위에 끌어다 놓으면, 그 현장의 엑셀책이 한 번에 만들어집니다.  (v1, 2026-10-03)

쓰는 법 (셋 중 하나)
    1) 탐색기에서 파일(여러 개도 됨)을 「★엑셀책.py」 아이콘 위에 끌어다 놓는다
    2) 더블클릭 → 파일 경로를 붙여 넣고 엔터
    3) 명령줄 :  python ★엑셀책.py  파일1 [파일2 ...]  [--현장 현장명]

파일 종류로 갈래가 정해집니다
    .txt .md             → 회의록 갈래 : PLAUD v10 txt 를 읽어
                              회의록.xlsx(협의록·할 일·변경·타부서 전달) → 회의 변경수량(40번) → 작업의뢰서 초안(55번)
                              → 납기 역산(일정에 준공일이 있으면, 10번) → 앞으로 할 것(46번) → 현황판(33번)
    .pdf .dxf .dwg .xlsx → 도면 갈래 : 도면을 현장 폴더에 넣고 32번 「현장 한 방에」 그대로
                              도면 접수·판 비교(31) → 수량표(27) → 단가 붙이기·실행(28) → 단가장 채우기(29) → 완성품 점검·부탁서(30) → 현황판(33)
    둘 다 넣으면 둘 다 돕니다.

결과
    _도구결과\엑셀책\{현장}_{YYMMDD}_{시각}\   한 폴더에 이번에 만든 파일을 전부 복사해 모읍니다
       00_목차.xlsx   맨 위 한 장 : 만든 파일 · 종류 · 시각 · 빈칸([ ]) 개수 · 확인할 것 · 자가진단
       00_결과.txt    화면에 찍힌 글 그대로 (꺼져도 다시 볼 수 있게)

지키는 것
    · 기존 파일은 고치지 않습니다. 넣으신 파일은 복사만 하고(옮기지 않음), 같은 이름이 있으면 날짜를 붙입니다
    · 금액·요율·배수·수량은 정하지 않습니다. 단가장에 없는 것은 비워 두고(부탁서로) 목차 「확인할 것」 에 적습니다
    · 묻지 않습니다 (32번과 같은 자동 모드). 판단이 갈리는 것은 안전한 쪽으로 하고 목차에 적습니다
    · 클로드(AI)를 부르지 않습니다 → 사용량 0.  현장 판정·도면 심볼 판독처럼 코드가 못 하는 것은 부탁서(30번)로 남습니다
    · 코드\km_tools 안의 파일은 건드리지 않습니다 (98번 갱신이 지우는 자리). 이 파일은 2_KM도구 바로 아래에 둡니다
"""
import os, sys, io, re, csv, json, glob, time, shutil, datetime, traceback

VERSION = 'v2 2026-10-03'   # v2 : 낱개 파일을 엑셀 한 권(시트별)으로도 묶는다 「0_엑셀책_현장_날짜.xlsx」
HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = '엑셀책'
NOTE = []
CHECKS = []          # 목차 「확인할 것」
STEPS = []           # (갈래, 단계, 결과)


def say(s=''):
    print(s)
    NOTE.append(s)


def check(what):
    CHECKS.append(what)
    say('   ※ 확인 : %s' % what)


# ── km_tools 찾기 ──────────────────────────────────────────
def find_tools():
    for p in (os.path.join(HERE, '코드', 'km_tools'), os.path.join(HERE, 'km_tools')):
        if os.path.isfile(os.path.join(p, 'common.py')):
            return p
    for root, _d, files in os.walk(HERE):
        if 'common.py' in files and 't32_oneshot.py' in files:
            return root
    return ''


TOOLS = find_tools()
if TOOLS and TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


# ── 입력 받기 ──────────────────────────────────────────────
MEET_EXT = ('.txt', '.md')
DWG_EXT = ('.pdf', '.dxf', '.dwg', '.xlsx', '.xls', '.csv')


def parse_args(argv):
    files, site = [], ''
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('--현장', '--site') and i + 1 < len(argv):
            site = argv[i + 1].strip(); i += 2; continue
        a = a.strip().strip('"')
        if a:
            files.append(a)
        i += 1
    return files, site


def ask_files():
    say('파일을 이 창에 끌어다 놓거나 경로를 붙여 넣고 엔터를 치십시오 (여러 개면 줄마다 하나, 빈 줄로 끝).')
    out = []
    while True:
        try:
            s = input('  파일 > ').strip().strip('"')
        except Exception:
            s = ''
        if not s:
            break
        out.append(s)
    return out


# ── 회의록 txt 읽기 (PLAUD v10 모양) ──────────────────────
SEC_RE = re.compile(r'^\s*■\s*(?P<key>[^:：\n]+?)\s*(?:[:：]\s*(?P<val>.*))?$')
PART_RE = re.compile(r'^\s*【\s*(\d)\s*부')
NONE = ('없음', '해당 없음', '해당없음', '-', '', '확인 예정')


def _clean(s):
    return re.sub(r'^[-·•ㆍ]\s*', '', str(s or '').strip()).strip()


def read_v10(path):
    """txt → {'meta':{...}, 'sec':{'1':{...}, '2':{...}}}  (55번 t55_workorder 가 읽는 meta.json 모양)"""
    with io.open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        text = f.read()
    part = '1'
    sec = {'1': {}, '2': {}}
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith('━'):
            continue
        pm = PART_RE.match(line)
        if pm:
            part = pm.group(1); cur = None
            continue
        m = SEC_RE.match(line)
        if m:
            key = re.sub(r'^[★☆]\s*', '', m.group('key').strip())
            val = (m.group('val') or '').strip()
            sec[part].setdefault(key, [])
            if val:
                sec[part][key].append(val)
            cur = key
            continue
        if cur:
            sec[part][cur].append(line.strip())
    s1, s2 = sec['1'], sec['2']

    def one(key):
        v = s1.get(key) or s2.get(key) or []
        v = [x for x in v if x]
        return v[0] if v else ''

    site = one('현장')
    ymd = re.sub(r'\D', '', one('일자'))
    ymd6 = ymd[2:8] if len(ymd) >= 8 else ymd[:6]
    who = one('협의자')
    comp, name, rank = '', '', ''
    wm = re.match(r'^(\S+)\s+(\S+?)(과장|부장|차장|대리|사원|소장|팀장|이사|대표|실장|주임|기사|님)?$', who)
    if wm:
        comp, name, rank = wm.group(1), wm.group(2), wm.group(3) or ''
    # 안건 목록 : 「1. 제목」 줄로 쪼갠다
    items, title, bul, dec, act = [], '', [], '', []

    def flush():
        if title or bul or dec or act:
            items.append({'title': title, 'bullets': bul, 'decision': dec, 'actions': act})
    for ln in s1.get('안건', [])[1:] if len(s1.get('안건', [])) > 1 else []:
        nm = re.match(r'^(\d+)\s*[.)]\s*(.+)$', ln)
        if nm:
            flush(); title, bul, dec, act = nm.group(2).strip(), [], '', []
        elif ln.startswith('결정사항'):
            dec = _clean(ln.split(':', 1)[1] if ':' in ln else ln.replace('결정사항', ''))
        elif ln.startswith('조치사항'):
            act.append(_clean(ln.split(':', 1)[1] if ':' in ln else ln.replace('조치사항', '')))
        elif ln.startswith('협의내용'):
            continue
        else:
            bul.append(_clean(ln))
    flush()
    meta = {'site': site, 'ymd': ymd6, 'hm': '', 'name': name, 'rank': rank, 'person': who, 'company': comp,
            'src': os.path.basename(path), 'made_by': '★엑셀책 ' + VERSION}
    s1out = {'현장': site, '안건': one('안건'), '안건목록': items,
             '일정': [_clean(x) for x in s1.get('일정', []) if _clean(x) not in NONE],
             '수량·규격 변경': [_clean(x) for x in s1.get('수량·규격 변경', s1.get('수량 · 규격 변경', [])) if _clean(x) not in NONE],
             '확인·회신 요청 사항': [_clean(x) for x in s1.get('확인·회신 요청 사항', []) if _clean(x) not in NONE]}
    s2out = {k: [_clean(x) for x in v if _clean(x) not in NONE] for k, v in s2.items()}
    return {'meta': meta, 'sec': {'1': s1out, '2': s2out}, 'text': text}


DATE_IN = re.compile(r'(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})')


def find_due(d):
    """일정·할 일 글에서 「준공」 과 함께 적힌 날짜. 없으면 None (추정하지 않는다)"""
    hay = d['sec']['1'].get('일정', []) + d['sec']['2'].get('할 일', [])
    for ln in hay:
        if '준공' in ln:
            m = DATE_IN.search(ln)
            if m:
                try:
                    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except Exception:
                    pass
    return None


# ── 엑셀 쓰기 ───────────────────────────────────────────────
def _wb():
    import openpyxl
    return openpyxl


def write_sheet(ws, head, rows, widths=None):
    from openpyxl.styles import Font, Alignment, PatternFill
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True); c.fill = PatternFill('solid', fgColor='FFEFEFEF')
    for r in rows:
        ws.append([('' if v is None else v) for v in r])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
    for i, w in enumerate(widths or [], start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    ws.freeze_panes = 'A2'


def meeting_xlsx(d, out_path):
    """회의록 한 권 : 협의록 / 할 일 / 변경 / 타부서 전달 / 원문"""
    op = _wb()
    wb = op.Workbook()
    m, s1, s2 = d['meta'], d['sec']['1'], d['sec']['2']
    ws = wb.active; ws.title = '협의록'
    rows = [['현장', m['site']], ['일자', m['ymd']], ['협의자', m['person']], ['안건', s1.get('안건', '')], []]
    for i, it in enumerate(s1.get('안건목록', []), 1):
        rows.append(['%d. %s' % (i, it['title']), ''])
        for b in it['bullets']:
            rows.append(['  협의', b])
        if it['decision']:
            rows.append(['  결정', it['decision']])
        for a in it['actions']:
            rows.append(['  조치', a])
    for k in ('일정', '확인·회신 요청 사항'):
        if s1.get(k):
            rows.append([]); rows.append([k, ''])
            rows += [['', x] for x in s1[k]]
    write_sheet(ws, ['항목', '내용'], rows, [26, 90])
    ws2 = wb.create_sheet('할 일')
    todo = []
    for ln in s2.get('할 일', []):
        p = [x.strip() for x in ln.split('|')]
        todo.append([p[0] if len(p) > 0 else '', p[1] if len(p) > 1 else ln, p[2] if len(p) > 2 else '', ''])
    write_sheet(ws2, ['기한', '할 일', '누가 → 누구', '완료'], todo, [14, 70, 24, 8])
    ws3 = wb.create_sheet('수량·규격 변경')
    write_sheet(ws3, ['현장', '일자', '변경 내용', '수량표 반영'], [[m['site'], m['ymd'], x, '[ ]'] for x in s1.get('수량·규격 변경', [])], [14, 12, 80, 12])
    ws4 = wb.create_sheet('타부서 전달')
    write_sheet(ws4, ['전달 사항', '작업의뢰서'], [[x, 'O' if '의뢰서' in x else ''] for x in s2.get('타부서 전달 사항', [])], [90, 12])
    ws5 = wb.create_sheet('원문')
    write_sheet(ws5, ['원문'], [[ln] for ln in d['text'].splitlines()], [120])
    wb.save(out_path)
    return out_path


def schedule_xlsx(site, due, out_path):
    import t05_schedule as S
    rows = S.back(due, 7)
    t0 = datetime.date.today()
    op = _wb(); wb = op.Workbook(); ws = wb.active; ws.title = '납기역산'
    body = []
    for name, dt, why in rows:
        dd = (dt - t0).days
        body.append([name, dt.isoformat(), dd, why, '지남' if dd < 0 else ('급함' if dd <= 14 else '')])
    body.append(['준공', due.isoformat(), (due - t0).days, '기준일 (회의록 일정에 적힌 날)', ''])
    write_sheet(ws, ['단계', '기한', 'D-day', '근거', '경보'], body, [42, 12, 8, 30, 8])
    ws['A%d' % (len(body) + 3)] = '※ 소요일은 10번(납기 역산)의 확정값. 외함 계열은 참고치. 준공일이 바뀌면 43번 확정 대장이 이깁니다.'
    wb.save(out_path)
    return out_path


def count_blanks(path):
    """엑셀·csv·txt 의 빈칸 표시 개수 ([ ] · [   ] · 비어있음)"""
    pat = re.compile(r'\[\s*\]|비어\s*있음|\(없음\)')
    n = 0
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == '.xlsx':
            wb = _wb().load_workbook(path, read_only=True, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    for v in row:
                        if isinstance(v, str) and pat.search(v):
                            n += 1
        elif ext in ('.csv', '.txt', '.md', '.html'):
            n = len(pat.findall(io.open(path, 'r', encoding='utf-8', errors='ignore').read()))
    except Exception:
        return ''
    return n


# ── 갈래 1 : 도면 ───────────────────────────────────────────
def site_dir_for(site):
    import t31_intake as I, t27_drawing as D
    from common import safe_name
    for n, p, y in I.sites(with_year=True):
        if I.norm_(n) == I.norm_(site):
            return p, False
    p = os.path.join(I.newest_site_root(), safe_name(site))
    os.makedirs(p, exist_ok=True)
    return p, True


def put_file(src, dst_dir):
    """복사만. 같은 이름이 있으면 _YYMMDD_HHMM 을 붙인다 (덮어쓰지 않음)"""
    dst = os.path.join(dst_dir, os.path.basename(src))
    if os.path.exists(dst):
        stem, ext = os.path.splitext(os.path.basename(src))
        dst = os.path.join(dst_dir, '%s_%s%s' % (stem, time.strftime('%y%m%d_%H%M'), ext))
    shutil.copy2(src, dst)
    return dst


def run_drawing(files, site):
    import common, t32_oneshot as O, t31_intake as I
    sd, new = site_dir_for(site)
    say('  현장 폴더 : %s%s' % (sd, '  (새로 만듦)' if new else ''))
    if new:
        check('「%s」 현장 폴더를 새로 만들었습니다. 현장 이름이 맞는지 보십시오 (다르면 폴더 이름만 바꾸시면 됩니다)' % site)
    for f in files:
        d = put_file(f, sd)
        say('  넣음 : %s' % os.path.basename(d))
    common.AUTO = True
    done = O.run_site(site, sd, with_intake=True, with_dash=True)
    for n, r in done:
        STEPS.append(('도면', n, r))
        if r.startswith('오류'):
            check('도면 갈래 「%s」 : %s' % (n, r))
    return done


# ── 갈래 2 : 회의록 ─────────────────────────────────────────
def meeting_folder(d, src):
    """plaud\26년\1.현장\{현장}\회의록\{YYMMDD}_{상대}_{안건}\  (40·44·55 번이 읽는 자리)"""
    from common import sites_root, safe_name, ymd6
    m = d['meta']
    site = m['site'] or '현장확인'
    tag = re.sub(r'\s+', '', (m['company'] + '_' + m['name']) if m['name'] else (m['person'] or '상대미상'))
    topic = safe_name(d['sec']['1'].get('안건', '') or os.path.splitext(os.path.basename(src))[0], 20)
    name = '%s_%s_%s' % (m['ymd'] or ymd6(), tag, topic)
    folder = os.path.join(sites_root(), safe_name(site), '회의록', safe_name(name, 60))
    if os.path.isdir(folder) and os.path.exists(os.path.join(folder, '원문.txt')):
        folder = folder + '_' + time.strftime('%H%M')
    os.makedirs(folder, exist_ok=True)
    shutil.copy2(src, os.path.join(folder, '원문.txt'))
    with io.open(os.path.join(folder, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump({'meta': m, 'sec': d['sec']}, f, ensure_ascii=False, indent=1)
    return folder


def run_meeting(files, site_hint, book_dir):
    import common
    from common import cfg, outdir, ymd6, safe_name
    common.AUTO = True
    folders, sites = [], []
    for f in files:
        d = read_v10(f)
        if site_hint and not d['meta']['site']:
            d['meta']['site'] = site_hint
        site = d['meta']['site'] or '현장확인'
        if site == '현장확인':
            check('「%s」 에 ■ 현장: 줄이 없습니다. 현장확인 폴더에 두었습니다' % os.path.basename(f))
        sites.append(site)
        folder = meeting_folder(d, f)
        folders.append(folder)
        say('  회의 폴더 : %s' % folder)
        # 1) 회의록 한 권
        xp = os.path.join(book_dir, '회의록_%s_%s.xlsx' % (safe_name(site), d['meta']['ymd'] or ymd6()))
        if os.path.exists(xp):
            xp = xp[:-5] + '_' + time.strftime('%H%M') + '.xlsx'
        try:
            meeting_xlsx(d, xp); STEPS.append(('회의록', '회의록.xlsx', '완료'))
            say('  회의록.xlsx : %s' % os.path.basename(xp))
        except Exception as e:
            STEPS.append(('회의록', '회의록.xlsx', '오류 : %s' % e)); check('회의록.xlsx 못 만듦 : %s' % e)
        # 2) 납기 역산 (일정에 「준공」 + 날짜가 있을 때만)
        due = find_due(d)
        if due:
            try:
                sp = os.path.join(book_dir, '납기역산_%s_%s.xlsx' % (safe_name(site), due.strftime('%y%m%d')))
                schedule_xlsx(site, due, sp); STEPS.append(('회의록', '10 납기 역산', '완료 (준공 %s)' % due))
                check('준공일 %s 은 회의록 글에서 읽은 것입니다. 확정이면 43번(확정 입력)에 넣어 주십시오' % due)
            except Exception as e:
                STEPS.append(('회의록', '10 납기 역산', '오류 : %s' % e))
        else:
            STEPS.append(('회의록', '10 납기 역산', '건너뜀 (회의록에 「준공 + 날짜」 가 없음)'))
        # 받는함 → _현장비서 대기함에도 한 부 (워드 회의록은 기존 시작.bat 이 만든다)
        try:
            b = cfg('biseo'); inbox = os.path.join(b, '1.여기에_v10결과_넣기')
            if os.path.isdir(inbox):
                put_file(f, inbox); say('  _현장비서 대기함에도 넣음 (워드 회의록은 시작.bat → 1 로)')
        except Exception:
            pass
    # 3) 40번 회의 변경수량 (원문.txt 전부 → 현장별 csv)
    try:
        import t40_meeting as M
        rows = M.collect_changes()
        allp, per = M.write_changes(rows)
        STEPS.append(('회의록', '40 회의 변경수량', '완료 (%d줄)' % len(rows)))
        if rows:
            check('수량·규격 변경 %d줄 → 수량표(27번)·견적 Rev 에 반영됐는지 보십시오' % len([r for r in rows if r[0] in sites]))
    except Exception as e:
        STEPS.append(('회의록', '40 회의 변경수량', '오류 : %s' % e)); check('40번 오류 : %s' % e)
    # 4) 55번 작업의뢰서 초안 (이번 회의 폴더만)
    try:
        import t55_workorder as W
        out = os.path.join(book_dir, '작업의뢰서초안')
        rep = None
        for folder in folders:
            rep = W.run(folder, out=out, today=ymd6())
        if rep:
            STEPS.append(('회의록', '55 작업의뢰서 초안', '완료 (「→ 작업의뢰서」 %d장, 원틀 %s)' % (rep['sheets'], '있음' if rep['template'] else '없음')))
            if rep['sheets'] and not rep['template']:
                check('작업의뢰서 원틀(MB-004)이 _원틀 에 없어 xlsx 는 안 만들고 본문 txt 만 만들었습니다')
            if rep['sheets']:
                check('작업의뢰서 초안 %d장 : 납기일·업체명·객실수·체크박스는 비워 두었습니다' % rep['sheets'])
    except Exception as e:
        STEPS.append(('회의록', '55 작업의뢰서 초안', '오류 : %s' % e)); check('55번 오류 : %s' % e)
    # 5) 46 앞으로 할 것 · 33 현황판
    for name, fn in (('46 앞으로 할 것', lambda: __import__('t46_plan').build_xlsx()),
                     ('33 현황판', lambda: __import__('t33_dashboard').run(quiet=True))):
        try:
            fn(); STEPS.append(('회의록', name, '완료'))
        except Exception as e:
            STEPS.append(('회의록', name, '오류 : %s' % e))
    return sites


# ── 모으기 · 목차 ───────────────────────────────────────────
def gather(book_dir, since, site):
    """_도구결과 아래에서 이번 실행 뒤에 생긴 파일을 엑셀책 폴더로 복사 (엑셀책 폴더 자신은 뺀다)"""
    from common import cfg, ymd6
    out = cfg('out')
    got = []
    for dp, dn, fn in os.walk(out):
        if os.path.abspath(dp).startswith(os.path.abspath(book_dir)):
            continue
        dn[:] = [d for d in dn if d != TOOL and not d.startswith('_')]      # _대장 · 엑셀책 자신은 뺀다
        if os.path.basename(dp) != ymd6():                                   # 도구별 「오늘」 폴더만
            continue
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if os.path.getmtime(p) >= since - 1 and os.path.splitext(f)[1].lower() in ('.xlsx', '.csv', '.html', '.md', '.txt', '.json'):
                    sub = os.path.relpath(dp, out).split(os.sep)[0]
                    dst_dir = os.path.join(book_dir, sub)
                    os.makedirs(dst_dir, exist_ok=True)
                    dst = os.path.join(dst_dir, f)
                    if not os.path.exists(dst):
                        shutil.copy2(p, dst)
                    got.append((sub, dst, p))
            except Exception:
                pass
    return got



def _sheet_name(used, name):
    name = re.sub(r'[\\/*?:\[\]]', '_', name)[:28] or '시트'
    base, i = name, 2
    while name in used:
        name = '%s_%d' % (base[:25], i); i += 1
    used.add(name)
    return name


def one_book(book_dir, site, rows):
    """목차 + 이번에 만든 csv·xlsx 전부를 시트 하나씩으로 묶은 엑셀 한 권 (값만. 원본 파일은 그대로 둔다)"""
    from openpyxl.styles import Font, Alignment, PatternFill
    op = _wb(); wb = op.Workbook(); used = set()
    ws = wb.active; ws.title = '목차'; used.add('목차')
    toc_rows = []
    sheets = []
    for i, r in enumerate(rows, 1):
        p = os.path.join(book_dir, r[1]); ext = os.path.splitext(p)[1].lower()
        stem = os.path.splitext(os.path.basename(p))[0]
        stem = re.sub(r'_?\d{6}(_\d{4})?', '', stem).strip('_') or stem
        if ext == '.csv':
            try:
                with io.open(p, 'r', encoding='utf-8-sig', errors='replace', newline='') as f:
                    data = list(csv.reader(f))
            except Exception:
                data = []
            nm = _sheet_name(used, stem)
            sheets.append((nm, data, r[1]))
            toc_rows.append([i, r[1], nm, r[4]])
        elif ext == '.xlsx':
            try:
                src = _wb().load_workbook(p, data_only=True)
                for sws in src.worksheets:
                    data = [list(x) for x in sws.iter_rows(values_only=True)]
                    nm = _sheet_name(used, '%s·%s' % (stem[:14], sws.title))
                    sheets.append((nm, data, r[1]))
                    toc_rows.append([i, r[1], nm, r[4]])
            except Exception as e:
                toc_rows.append([i, r[1], '(못 읽음 %s)' % e, r[4]])
        else:
            toc_rows.append([i, r[1], '(엑셀 아님 - 폴더에서 여십시오)', r[4]])
    write_sheet(ws, ['번호', '파일', '시트', '빈칸 [ ] 개수'], toc_rows, [6, 64, 34, 14])
    for nm, data, src in sheets:
        w = wb.create_sheet(nm)
        w.append(['출처 : %s' % src])
        w['A1'].font = Font(italic=True, color='FF808080')
        for row in data:
            w.append([('' if v is None else v) for v in row])
        if len(data) >= 1:
            for c in w[2]:
                c.font = Font(bold=True); c.fill = PatternFill('solid', fgColor='FFEFEFEF')
            w.freeze_panes = 'A3'
        for col in w.columns:
            width = max((len(str(c.value)) for c in col if c.value is not None), default=8)
            w.column_dimensions[col[0].column_letter].width = min(max(8, width * 1.2), 60)
    p = os.path.join(book_dir, '0_엑셀책_%s_%s.xlsx' % (safe_name_(site), time.strftime('%y%m%d')))
    wb.save(p)
    return p, len(sheets)


def safe_name_(s):
    return re.sub(r'[\\/:*?"<>|]', '_', str(s))[:40]

def toc_xlsx(book_dir, site, inputs, got, t0):
    op = _wb(); wb = op.Workbook()
    ws = wb.active; ws.title = '목차'
    rows = []
    allfiles = []
    for dp, dn, fn in os.walk(book_dir):
        for f in sorted(fn):
            if f.startswith('00_'):
                continue
            allfiles.append(os.path.join(dp, f))
    for i, p in enumerate(sorted(allfiles), 1):
        rel = os.path.relpath(p, book_dir)
        kind = rel.split(os.sep)[0] if os.sep in rel else ('회의록' if rel.startswith(('회의록', '납기역산')) else '')
        rows.append([i, rel, kind, time.strftime('%H:%M', time.localtime(os.path.getmtime(p))), count_blanks(p), ''])
    write_sheet(ws, ['번호', '파일', '어느 도구', '만든 시각', '빈칸 [ ] 개수', '보셨음'], rows, [6, 70, 16, 10, 14, 8])
    ws2 = wb.create_sheet('확인할 것')
    write_sheet(ws2, ['번호', '확인할 것', '답'], [[i, c, ''] for i, c in enumerate(CHECKS, 1)] or [[1, '없음', '']], [6, 100, 20])
    ws3 = wb.create_sheet('단계')
    write_sheet(ws3, ['갈래', '단계', '결과'], STEPS, [10, 34, 70])
    ws4 = wb.create_sheet('자가진단')
    diag = [['도구', '★엑셀책 ' + VERSION], ['현장', site], ['실행', time.strftime('%Y-%m-%d %H:%M', time.localtime(t0))],
            ['걸린 시간', '%d초' % int(time.time() - t0)], ['넣은 파일', '\n'.join(os.path.basename(x) for x in inputs)],
            ['만든 파일', len(rows)], ['빈칸 합계', sum(r[4] for r in rows if isinstance(r[4], int))],
            ['확인할 것', len(CHECKS)], ['오류 단계', len([s for s in STEPS if s[2].startswith('오류')])],
            ['AI 사용량', '0 (파이썬만)'], ['규칙', '기존 파일 안 고침 · 금액/수량 안 정함 · 묻지 않음']]
    write_sheet(ws4, ['항목', '값'], diag, [14, 90])
    p = os.path.join(book_dir, '00_목차.xlsx')
    wb.save(p)
    return p, rows


# ── 본체 ───────────────────────────────────────────────────
def main(argv):
    t0 = time.time()
    say('=' * 70)
    say(' ★엑셀책 %s        %s' % (VERSION, time.strftime('%Y-%m-%d %H:%M')))
    say('=' * 70)
    if not TOOLS:
        say('★ 도구 폴더(코드\\km_tools)를 못 찾았습니다. 이 파일은 「2_KM도구」 폴더 바로 아래에 있어야 합니다.')
        return 2
    import common
    from common import cfg, safe_name, ymd6, log
    files, site = parse_args(argv)
    if not files:
        files = ask_files()
    files = [os.path.abspath(f) for f in files if os.path.isfile(f)]
    if not files:
        say('넣은 파일이 없습니다.'); return 1
    meet = [f for f in files if os.path.splitext(f)[1].lower() in MEET_EXT]
    dwg = [f for f in files if os.path.splitext(f)[1].lower() in DWG_EXT]
    other = [f for f in files if f not in meet and f not in dwg]
    for f in other:
        check('모르는 종류라 건너뜀 : %s' % os.path.basename(f))
    # 현장 이름 정하기 : --현장 > txt 의 ■ 현장: > 파일명 [현장명] > 현장확인
    if not site:
        for f in meet:
            s = read_v10(f)['meta']['site']
            if s:
                site = s; break
    if not site and dwg:
        try:
            import t31_intake as I
            for f in dwg:
                s = I.guess_site_from_name(os.path.basename(f))
                if s:
                    site = s; break
        except Exception:
            pass
    if not site:
        site = '현장확인'
        check('현장 이름을 못 알아봤습니다. 파일명에 [현장명] 을 넣거나 --현장 으로 주십시오. 결과는 「현장확인」 폴더에 있습니다')
    say(' 현장 : %s   /   회의록 %d개 · 도면 %d개' % (site, len(meet), len(dwg)))
    book_dir = os.path.join(cfg('out'), TOOL, '%s_%s_%s' % (safe_name(site), ymd6(), time.strftime('%H%M')))
    os.makedirs(book_dir, exist_ok=True)
    common.AUTO = True
    try:
        common.open_file = lambda *a, **k: False
        common.open_folder = lambda *a, **k: False
    except Exception:
        pass
    since = time.time()
    if meet:
        say(''); say('-' * 70); say(' [회의록 갈래]'); say('-' * 70)
        try:
            run_meeting(meet, site, book_dir)
        except Exception as e:
            STEPS.append(('회의록', '전체', '오류 : %s' % e)); check('회의록 갈래 오류 : %s' % e)
            traceback.print_exc()
    if dwg:
        say(''); say('-' * 70); say(' [도면 갈래]  32번 「현장 한 방에」 그대로'); say('-' * 70)
        try:
            run_drawing(dwg, site)
        except Exception as e:
            STEPS.append(('도면', '전체', '오류 : %s' % e)); check('도면 갈래 오류 : %s' % e)
            traceback.print_exc()
    got = gather(book_dir, since, site)
    # 30번 부탁서(클로드에게 줄 것)가 있으면 맨 앞에 알린다
    asks = [g for g in got if '부탁서' in os.path.basename(g[1])]
    if asks:
        check('클로드에게 줄 부탁서 %d개가 있습니다 (코드가 못 읽은 심볼·없는 단가). 그 파일만 대화창에 주시면 됩니다' % len(asks))
    toc, rows = toc_xlsx(book_dir, site, files, got, t0)
    try:
        bookp, nsheet = one_book(book_dir, site, rows)
        STEPS.append(('묶기', '엑셀 한 권', '완료 (시트 %d장)' % nsheet))
    except Exception as e:
        bookp, nsheet = '', 0
        STEPS.append(('묶기', '엑셀 한 권', '오류 : %s' % e)); check('엑셀 한 권으로 못 묶음 : %s' % e)
    say('')
    say('=' * 70)
    say(' 끝. 엑셀 한 권(시트 %d장) : %s' % (nsheet, os.path.basename(bookp)))
    say('     낱개 파일 %d개 → %s' % (len(rows), book_dir))
    for g, n, r in STEPS:
        say('   %-5s %-26s %s' % (g, n, r))
    if CHECKS:
        say('')
        say(' 확인하실 것 %d개 (00_목차.xlsx 「확인할 것」 탭)' % len(CHECKS))
        for i, c in enumerate(CHECKS, 1):
            say('   %d. %s' % (i, c))
    say('=' * 70)
    try:
        log(TOOL, '%s 회의%d 도면%d 파일%d 확인%d' % (site, len(meet), len(dwg), len(rows), len(CHECKS)))
    except Exception:
        pass
    with io.open(os.path.join(book_dir, '00_결과.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(NOTE))
    try:
        if os.name == 'nt':
            os.startfile(book_dir)
            os.startfile(bookp or toc)
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    try:
        rc = main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception:
        say('★ 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        say(traceback.format_exc())
        rc = 9
    if os.name == 'nt' and sys.stdin and sys.stdin.isatty():
        try:
            input('\n엔터를 치면 닫힙니다 > ')
        except Exception:
            pass
    sys.exit(rc)

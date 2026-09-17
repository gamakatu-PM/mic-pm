# -*- coding: utf-8 -*-
"""41. 총괄 점검 - 한 번에 전부 확인한다. 토큰 0.
프로님이 "다 제대로 되어 있나?" 를 번호 하나로 보는 표. 클로드도 이 표(md)를 읽고 PC 상태를 안다.

  A 판·갱신   : 지금 판 / GitHub 정본 판 / 다운로드의 새 zip / 파이썬·부품
  B 폴더·경로 : 8개 경로, _현장비서 안 구조, 정답본 2개, 단가장, 견적 원틀, 바로가기 2개, 받는함
  C 회의록    : PLAUD 대기함·처리완료·회의록 폴더 수, 마지막 회의, 회의 변경 줄, 코드 백업
  D 도면→돈   : 현장마다 도면 수·판·수량표·실행산출·견적서·37 검수 판정·부탁서·받은답
  E 자가 시험 : 39번을 돌려 n/n (quick=True 면 건너뜀)
  F 자동 실행 : 38번 등록 상태 (참고)
결과 : _도구결과\\총괄점검\\{날짜}\\총괄점검.html + base\\_총괄점검.html + 인수인계함\\_총괄점검.md (클로드용)
판정 : 통과(초록) / 주의(노랑) / 실패(빨강) / 미확인(회색). 실패·주의마다 「조치」 한 줄이 붙는다.
"""
import os, sys, re, io, glob, importlib, datetime, traceback
import common
from common import *

TOOL = '총괄점검'
R = []   # (등급, 구역, 항목, 상태, 조치)

def add(level, sec, item, state, fix=''):
    R.append((level, sec, item, state, fix))

def _try(sec, item, fn, fix=''):
    """검사 하나. 예외가 나면 미확인으로 남기고 다음으로 간다 (하나 고장나도 표는 나온다)"""
    try:
        return fn()
    except Exception as e:
        add('gray', sec, item, '점검 중 오류 : %s' % str(e)[:80], fix or '이 항목만 클로드에게')
        return None

def _latest(pat):
    xs = glob.glob(pat)
    xs.sort(key=os.path.getmtime, reverse=True)
    return xs[0] if xs else None

def _ver(p):
    m = re.search(r'_(\d{6})_(?:실행산출|견적서)_v(\d+)', os.path.basename(p))
    return 'v%s (%s)' % (m.group(2), m.group(1)) if m else os.path.basename(p)[:20]

def _age(p):
    try:
        return (today() - datetime.date.fromtimestamp(os.path.getmtime(p))).days
    except Exception:
        return None

# ---------------- A 판·갱신 ----------------

def sec_a(quick):
    S = 'A 판·갱신'
    add('green', S, '지금 판', '%s (%s)' % (VERSION, VERSION_DATE))
    if not quick:
        def f():
            import t98_update as U
            rv = U.remote_version(timeout=6)
            cur = int(re.sub(r'\D', '', VERSION) or 0)
            if rv is None:
                add('gray', S, 'GitHub 정본 판', '인터넷/정본에 못 닿음', '인터넷 연결 후 다시. 계속 그러면 설정.ini [갱신] url 확인')
            elif rv > cur:
                add('yellow', S, 'GitHub 정본 판', 'v%d (지금 %s 보다 새 판)' % (rv, VERSION), '★KM_도면넣고_여기클릭 을 누르면 스스로 받아 갈아끼웁니다')
            else:
                add('green', S, 'GitHub 정본 판', 'v%d = 지금 판' % rv)
            z = U.newer_zip()
            if z:
                add('yellow', S, '다운로드의 새 zip', os.path.basename(z), '98번 또는 ★KM_도면넣고_여기클릭')
            else:
                add('green', S, '다운로드의 새 zip', '없음 (지금 판이 최신)')
        _try(S, 'GitHub 정본 판', f)
    import platform
    add('green', S, '파이썬', '%s (%s)' % (sys.version.split()[0], platform.node()))
    for mod, why, need in (('openpyxl', '엑셀 (28·30·37)', True), ('PIL', '사진대지', False), ('pptx', '이미지 PPT', False),
                           ('ezdxf', 'DXF 도면 (27, 누를 때 자동 설치)', False), ('fitz', 'PDF 도면 (27, 누를 때 자동 설치)', False)):
        try:
            importlib.import_module(mod)
            add('green', S, '부품 ' + mod, '있음 (%s)' % why)
        except Exception:
            add('red' if need else 'gray', S, '부품 ' + mod, '없음 (%s)' % why,
                '_처음_한번만_설치.bat' if need else '그 도구를 누르면 스스로 받습니다')

# ---------------- B 폴더·경로 ----------------

def sec_b():
    S = 'B 폴더·경로'
    for k, must in (('base', True), ('plaud', True), ('biseo', True), ('template', True), ('out', False),
                    ('handover', False), ('drawing', True), ('price', True)):
        p = cfg(k)
        if os.path.isdir(p):
            add('green', S, '경로 ' + k, p)
        else:
            add('red' if must else 'yellow', S, '경로 ' + k, '없음 : ' + p,
                '폴더를 만들거나 설정.ini [경로] %s= 에 실제 위치를 적으십시오' % k)
    sr = sites_root()
    n = len([d for d in os.listdir(sr) if os.path.isdir(os.path.join(sr, d)) and not d.startswith(('_', '.'))]) if os.path.isdir(sr) else 0
    add('green' if n else 'yellow', S, '회의록 현장 폴더', '%s (현장 %d개)' % (sr, n), '' if n else 'plaud\\26년\\1.현장 아래에 현장 폴더가 없습니다')
    b = cfg('biseo')
    for sub, must in (('시작.bat', True), ('1.여기에_v10결과_넣기', True), ('3.처리완료', False), ('코드', True)):
        p = os.path.join(b, sub)
        ok = os.path.exists(p)
        add('green' if ok else ('red' if must else 'yellow'), S, '_현장비서\\' + sub, '있음' if ok else '없음',
            '' if ok else '_현장비서 구조가 다릅니다. 실제 폴더 이름을 알려 주십시오 (40번이 이 이름을 씁니다)')
    if os.path.isdir(os.path.join(b, '코드')):
        py = glob.glob(os.path.join(b, '코드', '*.py'))
        add('green' if py else 'red', S, '회의록 코드 파일', ', '.join(os.path.basename(x) for x in py)[:120] or '없음',
            '' if py else '회의록 코드가 없습니다. 인수인계함\\회의록코드_백업 에서 복구')
    g = os.path.join(cfg('template'), '정답본')
    gx = glob.glob(os.path.join(g, '*.xlsx'))
    names = ' / '.join(os.path.basename(x) for x in gx)
    has_exec = any('실행산출' in x for x in names.split(' / '))
    has_quote = any('견적서' in x for x in names.split(' / '))
    add('green' if (has_exec and has_quote) else 'red', S, '정답본 2개 (실행산출·견적서)', names or '없음',
        '' if (has_exec and has_quote) else '주일능_실행산출_v5_260828.xlsx 와 광희동1가_견적서_Rev1.xlsx 를 3_공통사용\\원틀\\정답본\\ 에')
    def f():
        import t28_cost as C
        p = C._find_pb_file()
        if p:
            add('green', S, '단가장', '%s (%d일 전 파일)' % (os.path.basename(p), _age(p) or 0))
        else:
            add('red', S, '단가장', '없음', '드라이브 CB모듈_단가장 xlsx 를 3_공통사용\\단가장\\ 에')
    _try(S, '단가장', f)
    t = find_template('견적')
    add('green' if t else 'yellow', S, '견적서 원틀', os.path.basename(t) if t else '없음', '' if t else '_원틀 에 광희동1가_견적서_Rev1 (정답본과 같은 파일이어도 됨)')
    try:
        import t27_drawing as D
        dr = D.dwg_root()
    except Exception:
        dr = cfg('drawing')
    for where, name in ((dr, '도면 폴더'), (desktop_dir(), '바탕화면')):
        if not where:
            add('gray', S, '바로가기 (%s)' % name, '폴더를 못 찾음'); continue
        sc = [f for f in ('★KM_도면넣고_여기클릭.py', '★KM_번호입력.py') if os.path.exists(os.path.join(where, f))]
        add('green' if len(sc) == 2 else 'yellow', S, '바로가기 (%s)' % name, '%d/2' % len(sc), '' if len(sc) == 2 else '시작.py 를 한 번 열면 다시 만듭니다')
    def f3():
        import t31_intake as I
        root = I.D.dwg_root()
        yr = I.year_dirs(root)
        add('green', S, '도면 폴더 구조', '%s%s' % (root, ('  ·  연도 폴더 %d개 : %s (새 도면은 %s\\ 로)' % (len(yr), ', '.join(n for y, n, p in yr), yr[0][1])) if yr else '  ·  연도 폴더 없음 (현장 폴더가 바로 아래)'))
        sw = I.sites(with_year=True)
        if not sw:
            add('red', S, '도면 현장 폴더', '없음', '3_공통사용\\도면\\{현장명}\\ 또는 3_공통사용\\도면\\26년\\{현장명}\\ 에 도면을 넣으십시오')
            return
        for n, p, y in sw:
            nf = len(I.drawing_files(p))
            sk = I.skipped_years(p)
            inner = I.site_year_dirs(p)
            where = ('%s\\%s\\' % (y, n)) if y else ('%s\\' % n)
            if inner:
                where += '%s\\ (안쪽 연도 폴더, 최신만 읽음)' % inner[0][1]
            add('green' if nf else 'yellow', S, '도면 [%s]' % n,
                '%s · 읽는 도면 %d개%s' % (where, nf, ('  ·  보관용으로 건너뜀 : ' + ', '.join(sk)) if sk else ''),
                '' if nf else '이 폴더에 도면(dxf·pdf)이 없습니다')
    _try(S, '도면 폴더 구조', f3)
    def f2():
        import t40_meeting as M
        p = M.inbox_dir()
        n = len([x for x in os.listdir(p) if x.lower().endswith('.txt') and not x.startswith('여기에_')])
        add('green' if not n else 'yellow', S, '회의 받는함', '%s (대기 %d개)' % (p, n), '' if not n else '★KM_도면넣고_여기클릭 을 누르면 _현장비서로 옮깁니다')
    _try(S, '회의 받는함', f2)

# ---------------- C 회의록 ----------------

def sec_c():
    S = 'C 회의록'
    def f():
        import t11_plaudgap as G
        b = cfg('biseo')
        inbox = os.path.join(b, '1.여기에_v10결과_넣기'); done = os.path.join(b, '3.처리완료')
        wn, wf = G.count_parts(inbox) if os.path.isdir(inbox) else (0, 0)
        dn, df = G.count_parts(done) if os.path.isdir(done) else (0, 0)
        made = G.count_meetings(cfg('plaud')) if os.path.isdir(cfg('plaud')) else 0
        add('yellow' if wn else 'green', S, 'PLAUD 대기함', '회의 %d건 (파일 %d개)' % (wn, wf), '_현장비서\\시작.bat 1번' if wn else '')
        add('green', S, '처리완료 / 회의록 폴더', '%d건 / %d개' % (dn, made), '' if made >= dn else '회의록이 %d건 모자랍니다 (11번으로 누락 확인)' % (dn - made))
        if dn and made < dn:
            R[-1] = ('yellow',) + R[-1][1:]
    _try(S, 'PLAUD 대기함', f)
    def f2():
        import t40_meeting as M
        files = M.meeting_files()
        if not files:
            add('yellow', S, '마지막 회의', '회의록 원문.txt 를 하나도 못 찾음', 'plaud\\26년 아래 회의 폴더 위치를 알려 주십시오'); return
        last = max(files, key=os.path.getmtime)
        d = _age(last)
        add('green' if d is not None and d <= 7 else 'yellow', S, '마지막 회의', '%d일 전 · %s' % (d or 0, os.path.basename(os.path.dirname(last))[:60]),
            '' if d is not None and d <= 7 else '일주일 넘게 회의록이 없습니다. PLAUD 가져와 → 받는함')
        rows = M.changes_for('', days=30)
        add('green', S, '회의 수량·규격 변경 (30일)', '%d줄' % len(rows), '' if not rows else '부탁서·현황판 ⑦ 에서 수량표 반영 여부 확인')
    _try(S, '마지막 회의', f2)
    bk = glob.glob(os.path.join(cfg('handover'), '회의록코드_백업', '*'))
    if bk:
        b = max(bk, key=os.path.getmtime)
        add('green', S, '회의록 코드 백업', '%s (%d일 전)' % (os.path.basename(b), _age(b) or 0))
    else:
        add('yellow', S, '회의록 코드 백업', '없음', '★KM_도면넣고_여기클릭 한 번 (40번이 만듭니다)')

# ---------------- D 도면 → 돈 ----------------

def sec_d(quiet):
    S = 'D 도면→돈'
    try:
        import t31_intake as I
        sites = I.sites(with_year=True)
    except Exception as e:
        add('gray', S, '현장 목록', '못 읽음 %s' % e); return
    if not sites:
        add('yellow', S, '현장 목록', '도면 폴더에 현장이 없습니다', '3_공통사용\\도면\\{현장명}\\ 에 도면을 넣으십시오'); return
    o = cfg('out')
    ins = None
    try:
        import t37_check as K
        ins = K
    except Exception:
        pass
    for name, p, yr in sites:
        nf = len(I.drawing_files(p))
        led = I.load_ledger(p)
        revs = [int(r['판']) for r in led if str(r['판']).isdigit()]
        rev = max(revs) if revs else 0
        q = _latest(os.path.join(o, '도면수량', '*', '%s_도면에적힌수량표_*.csv' % safe_name(name))) \
            or _latest(os.path.join(o, '도면수량', '*', '%s_도면수량_*.csv' % safe_name(name)))
        ex = _latest(os.path.join(o, '단가붙이기', '*', '%s_*_실행산출_v*.xlsx' % safe_name(name)))
        qu = _latest(os.path.join(o, '단가붙이기', '*', '%s_*_견적서_v*.xlsx' % safe_name(name)))
        rq = _latest(os.path.join(o, '완성품', '*', '_클로드부탁서_%s_*.md' % safe_name(name)))
        inner = I.site_year_dirs(p)
        where = ('%s\\' % yr) if yr else ''
        if inner:
            where += '%s\\' % inner[0][1]
        parts = [('%s 도면 %d개' % (where, nf)) if where else ('도면 %d개' % nf), 'r%d' % rev, '수량표 %s' % ('있음' if q else '없음'),
                 '실행산출 %s' % (_ver(ex) if ex else '없음'), '견적서 %s' % (_ver(qu) if qu else '없음')]
        lv = 'green' if (nf and q and ex and qu) else ('yellow' if nf else 'gray')
        fix = '' if lv == 'green' else ('★KM_도면넣고_여기클릭 (36번) 을 누르십시오' if nf else '도면이 없습니다')
        add(lv, S, '[%s]' % name, ' · '.join(parts), fix)
        # 37 검수 (정답본이 있을 때만, 묻지 않음)
        if ins and glob.glob(os.path.join(cfg('template'), '정답본', '*.xlsx')):
            for kind, fp in (('실행산출', ex), ('견적서', qu)):
                if not fp:
                    continue
                def f(fp=fp, kind=kind):
                    common.AUTO = True
                    try:
                        import contextlib
                        buf = io.StringIO()
                        with contextlib.redirect_stdout(buf):
                            v, finds, _ = ins.inspect(fp, ask_fix=False, quiet=True)
                    finally:
                        common.AUTO = False
                    bad = [x for x in finds if x[0] == '잘못']
                    add('green' if v == '통과' else ('red' if v == '잘못' else 'yellow'), S, '[%s] 37 검수 %s' % (name, kind),
                        '%s (%d건)' % (v, len(finds)), '' if v == '통과' else ('; '.join('%s %s' % (b[1], b[2][:50]) for b in bad[:2]) or '노란 빈칸을 채우십시오 (부탁서 참고)'))
                _try(S, '[%s] 37 검수 %s' % (name, kind), f)
        if rq:
            n = len(re.findall(r'^## \d+\.', read_text(rq), re.M))
            add('yellow' if n else 'green', S, '[%s] 부탁서' % name, '%d항목 (%d일 전)' % (n, _age(rq) or 0), '대화창에 던지십시오' if n else '')
    try:
        import t28_cost as C
        ad = os.path.join(C.root(), '받은답')
        pend = [f for f in glob.glob(os.path.join(ad, '*.csv')) if not os.path.basename(f).startswith('_처리')]
        add('yellow' if pend else 'green', S, '받은답 반영 대기', '%d개' % len(pend), '30번을 누르십시오' if pend else '')
    except Exception:
        pass

# ---------------- E 자가 시험 / F 자동 실행 ----------------

def sec_e(quick):
    S = 'E 자가 시험'
    if quick:
        add('gray', S, '39 자가 시험', '건너뜀 (빠른 점검)', '41번을 따로 누르면 같이 돕니다'); return
    def f():
        import t39_selftest as T
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = T.run()
        m = re.search(r'(전부 통과 \(\d+/\d+\)|실패 \d+개 / \d+)', buf.getvalue())
        add('green' if ok else 'red', S, '39 자가 시험', m.group(1) if m else ('통과' if ok else '실패'),
            '' if ok else '이 판을 쓰지 마시고 _도구결과\\자가시험 의 로그를 클로드에게')
    _try(S, '39 자가 시험', f)

def sec_f():
    S = 'F 자동 실행 (참고)'
    try:
        import t38_autorun as A
        st = A.status()
        if not st:
            add('gray', S, '작업 스케줄러', '윈도우가 아니어서 확인 안 함'); return
        on = [k for k, v in st.items() if v]
        add('green', S, '작업 스케줄러', ('등록됨 : ' + ', '.join(on)) if on else '등록 안 됨 (기본. 바로가기 클릭 방식)')
    except Exception as e:
        add('gray', S, '작업 스케줄러', '확인 못 함 %s' % e)

# ---------------- 표 만들기 ----------------

def build(quick=False, quiet=False):
    del R[:]
    sec_a(quick); sec_b(); sec_c(); sec_d(quiet); sec_e(quick); sec_f()
    cnt = {'green': 0, 'yellow': 0, 'red': 0, 'gray': 0}
    for lv, *_ in R:
        cnt[lv] = cnt.get(lv, 0) + 1
    verdict = '전부 통과' if not cnt['red'] and not cnt['yellow'] else ('실패 %d · 주의 %d' % (cnt['red'], cnt['yellow']))
    todo = [(lv, sec, item, fix) for lv, sec, item, st, fix in R if lv in ('red', 'yellow') and fix]
    todo.sort(key=lambda x: 0 if x[0] == 'red' else 1)
    # HTML
    blocks = [('지금 할 것 (실패 → 주의 순)', [(lv, '%s · %s → %s' % (sec, item, fix)) for lv, sec, item, fix in todo] or [('green', '할 것 없음')])]
    for sec in ('A 판·갱신', 'B 폴더·경로', 'C 회의록', 'D 도면→돈', 'E 자가 시험', 'F 자동 실행 (참고)'):
        rows = [(lv, '%s : %s%s' % (item, st, (' → ' + fix) if fix and lv != 'green' else '')) for lv, s, item, st, fix in R if s == sec]
        blocks.append((sec, rows))
    od = outdir(TOOL)
    hp = write_html(os.path.join(od, '총괄점검_%s.html' % ymd6()),
                    'KM 총괄 점검  %s  (통과 %d · 주의 %d · 실패 %d · 미확인 %d)' % (verdict, cnt['green'], cnt['yellow'], cnt['red'], cnt['gray']), blocks)
    top = os.path.join(cfg('base'), '_총괄점검.html')
    try:
        import shutil; shutil.copy(hp, top)
    except Exception:
        top = hp
    # 클로드용 md
    md = ['# KM 총괄 점검  (%s · 도구 %s · %s)' % (today().isoformat(), VERSION, verdict), '',
          '새 창의 클로드는 현황판과 함께 이 파일을 읽는다. 프로님 PC 도구가 방금 낸 것이다.', '',
          '| 등급 | 구역 | 항목 | 상태 | 조치 |', '|---|---|---|---|---|']
    for lv, sec, item, st, fix in R:
        md.append('| %s | %s | %s | %s | %s |' % ({'green': '통과', 'yellow': '주의', 'red': '실패', 'gray': '미확인'}[lv], sec, item, st.replace('|', '/'), fix.replace('|', '/')))
    csv_p = write_csv(os.path.join(od, '총괄점검_%s.csv' % ymd6()), [[{'green': '통과', 'yellow': '주의', 'red': '실패', 'gray': '미확인'}[lv], s, i, st, f] for lv, s, i, st, f in R],
                      ['등급', '구역', '항목', '상태', '조치'])
    hd = cfg('handover')
    mdp = os.path.join(hd if os.path.isdir(hd) else od, '_총괄점검.md')
    io.open(mdp, 'w', encoding='utf-8').write('\n'.join(md))
    if not quiet:
        print('')
        print('%-4s %-14s %-34s %s' % ('등급', '구역', '항목', '상태'))
        print('-' * 100)
        for lv, sec, item, st, fix in R:
            print('%-4s %-14s %-34s %s%s' % ({'green': '통과', 'yellow': '주의', 'red': '실패', 'gray': '미확인'}[lv], sec[:14], item[:34], st[:60],
                                            ('  -> ' + fix[:50]) if fix and lv != 'green' else ''))
        print('-' * 100)
        print('판정 : %s   (통과 %d · 주의 %d · 실패 %d · 미확인 %d)' % (verdict, cnt['green'], cnt['yellow'], cnt['red'], cnt['gray']))
        print('표   : %s' % top)
        print('클로드용 : %s' % mdp)
    log(TOOL, '%s' % verdict)
    return top, mdp, verdict, R

def run(quick=False):
    title('41. 총괄 점검   (판·폴더·회의록·도면→돈·자가 시험·자동 실행을 한 번에)')
    if not quick:
        print('39 자가 시험까지 같이 돌립니다 (1분 안팎)...')
    top, mdp, verdict, _ = build(quick=quick)
    if not common.AUTO:
        open_file(top)
    return top

if __name__ == '__main__':
    run('--quick' in sys.argv); pause()

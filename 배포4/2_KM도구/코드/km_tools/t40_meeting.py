# -*- coding: utf-8 -*-
"""40. 회의 연결 - PLAUD 회의록(_현장비서 산출)과 도면 흐름(36)을 잇는다. 토큰 0.
36번(오늘 한 방에)이 시작할 때 조용히 같이 돈다. 따로 눌러도 된다.

  1) 받는함의 txt 를 _현장비서\\1.여기에_v10결과_넣기 로 옮긴다
     받는함 = 다운로드\\KM_회의록받는함 (설정.ini [회의] 받는함 으로 바꿀 수 있음)
     클로드가 PLAUD 에서 v10 결과를 가져와 txt 로 주면(파일명 = PLAUD 제목) 여기에 저장만 하시면 된다.
     앱에서 텍스트를 복사해 저장하던 손이 없어진다.
  2) 옮긴 것이 있으면 _현장비서\\시작.bat 을 띄운다 (설정.ini [회의] 실행명령 이 있으면 그것을 조용히 돌린다)
  3) 회의록 폴더(plaud\\26년\\...\\원문.txt)의 「■ 수량·규격 변경」을 현장별 csv 로 모은다
     -> 30번 부탁서 「회의에서 바뀐 수량·규격」 절 + 현황판 ⑦. 수량은 도구가 정하지 않는다(프로님 확인용).
  4) _현장비서\\코드 의 .py 와 시작.bat 을 인수인계함\\회의록코드_백업\\ 에 복사하고 zip 한 개로 묶는다
     (PC 가 바뀌어도 회의록 코드가 살아남게. 바뀐 것이 있을 때만 새로 묶는다)
"""
import os, re, io, csv, glob, json, hashlib, shutil, zipfile, subprocess, configparser, datetime
import common
from common import *

TOOL = '회의연결'
INBOX_NAME = 'KM_회의록받는함'
SEC_CHANGE = re.compile(r'^\s*■\s*수량\s*[·ㆍ・,/]?\s*규격\s*변경', re.M)
SEC_ANY = re.compile(r'^\s*(■|━|【)', re.M)
SITE_RE = re.compile(r'^\s*■\s*현장\s*[:：]\s*(.+?)\s*$', re.M)
DATE_RE = re.compile(r'^\s*■\s*일자\s*[:：]\s*(.+?)\s*$', re.M)
WHO_RE = re.compile(r'^\s*■\s*협의자\s*[:：]\s*(.+?)\s*$', re.M)
NONE_WORDS = ('없음', '해당 없음', '해당없음', '-', '')

def _ini(section, key):
    try:
        c = configparser.ConfigParser(); c.read(common.INI, encoding='utf-8')
        if c.has_option(section, key):
            return c.get(section, key).strip()
    except Exception:
        pass
    return ''

def downloads():
    home = os.path.expanduser('~')
    for d in (os.path.join(home, 'Downloads'), os.path.join(home, '다운로드')):
        if os.path.isdir(d):
            return d
    return home

def inbox_dir():
    """클로드가 준 v10 txt 를 저장하는 곳. 없으면 만든다."""
    p = common.DEFAULTS.get('meeting_inbox') or _ini('회의', '받는함') or os.path.join(downloads(), INBOX_NAME)
    try:
        os.makedirs(p, exist_ok=True)
        tip = os.path.join(p, '여기에_클로드가_준_회의txt를_넣으십시오.txt')
        if not os.path.exists(tip):
            io.open(tip, 'w', encoding='utf-8').write(
                '클로드가 PLAUD 에서 가져온 v10 결과 txt 를 이 폴더에 저장하시면\n'
                '36번(★KM_도면넣고_여기클릭)이 _현장비서 대기함으로 옮기고 시작.bat 을 띄웁니다.\n'
                '이 안내 파일은 옮기지 않습니다.\n')
    except Exception:
        pass
    return p

def biseo_inbox():
    b = cfg('biseo')
    return os.path.join(b, '1.여기에_v10결과_넣기'), b

# ---------------- 1) 받는함 -> 대기함 ----------------

def move_inbox(quiet=False):
    src = inbox_dir()
    dst, b = biseo_inbox()
    moved, skipped = [], []
    files = [f for f in sorted(os.listdir(src)) if f.lower().endswith(('.txt', '.md')) and not f.startswith('여기에_')]
    if not files:
        return moved, skipped
    if not os.path.isdir(b):
        if not quiet:
            print('[받는함] _현장비서 폴더가 없어 옮기지 못했습니다 : %s' % b)
        return moved, files
    os.makedirs(dst, exist_ok=True)
    for f in files:
        s, d = os.path.join(src, f), os.path.join(dst, f)
        try:
            if os.path.exists(d):
                # 같은 이름이 이미 대기함에 있으면 뒤에 번호를 붙인다 (덮어쓰지 않는다)
                stem, ext = os.path.splitext(f)
                k = 2
                while os.path.exists(os.path.join(dst, '%s_%d%s' % (stem, k, ext))):
                    k += 1
                d = os.path.join(dst, '%s_%d%s' % (stem, k, ext))
            shutil.move(s, d)
            moved.append(os.path.basename(d))
        except Exception as e:
            skipped.append('%s (%s)' % (f, e))
    return moved, skipped

def launch_biseo(quiet=False):
    """_현장비서 시작.bat 을 띄운다. 설정.ini [회의] 실행명령 이 있으면 그것을 조용히 돌린다."""
    _, b = biseo_inbox()
    cmd = _ini('회의', '실행명령')
    if cmd:
        try:
            subprocess.Popen(cmd, cwd=b, shell=True)
            return '실행명령 : %s' % cmd
        except Exception as e:
            return '[실행명령 실패] %s' % e
    bat = os.path.join(b, '시작.bat')
    if not os.path.exists(bat):
        return '[시작.bat 없음] %s' % bat
    try:
        if os.name == 'nt':
            os.startfile(bat)
            return '시작.bat 을 띄웠습니다 -> 그 창에서 1 을 누르십시오'
        return '(윈도우가 아니라 시작.bat 을 띄우지 않았습니다)'
    except Exception as e:
        return '[시작.bat 실패] %s' % e

# ---------------- 3) 회의록 -> 수량·규격 변경 모으기 ----------------

def _section(text, head_re):
    m = head_re.search(text)
    if not m:
        return []
    rest = text[m.end():]
    n = SEC_ANY.search(rest)
    body = rest[:n.start()] if n else rest
    out = []
    for line in body.splitlines():
        s = line.strip().lstrip('-•·ㆍ*').strip()
        if s and s not in NONE_WORDS and not s.startswith('('):
            out.append(s)
    return out

def _first(rx, text, default=''):
    m = rx.search(text)
    return m.group(1).strip() if m else default

def meeting_files():
    """회의 폴더의 원문.txt 전부 (삭제요망 폴더 제외)"""
    root = cfg('plaud')
    out = []
    if not os.path.isdir(root):
        return out
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(('_삭제요망', '.'))]
        for f in fn:
            if f.startswith('원문') and f.lower().endswith(('.txt', '.md')):
                out.append(os.path.join(dp, f))
    return out

def _meta_changes(folder):
    """meta.json 에 변경 목록이 있으면 그것도 본다 (열쇠 이름은 코드마다 달라 '변경' 이 들어간 목록만)"""
    p = os.path.join(folder, 'meta.json')
    if not os.path.exists(p):
        return []
    try:
        d = json.load(io.open(p, 'r', encoding='utf-8'))
    except Exception:
        return []
    out = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if ('변경' in str(k) or 'change' in str(k).lower()) and isinstance(v, list):
                    for it in v:
                        if isinstance(it, dict):
                            out.append(' / '.join('%s=%s' % (a, b) for a, b in it.items() if b not in (None, '')))
                        elif it:
                            out.append(str(it))
                else:
                    walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)
    walk(d)
    return [x for x in out if x.strip() not in NONE_WORDS]

def collect_changes():
    """[현장, 회의일, 협의자, 회의폴더, 내용] 줄 목록"""
    rows = []
    for p in meeting_files():
        folder = os.path.dirname(p)
        text = read_text(p)
        site = _first(SITE_RE, text) or os.path.basename(os.path.dirname(os.path.dirname(folder)))
        day = _first(DATE_RE, text)
        who = _first(WHO_RE, text)
        fname = os.path.basename(folder)
        if not day:
            m = re.match(r'(\d{6})', fname)
            day = ('20%s-%s-%s' % (m.group(1)[:2], m.group(1)[2:4], m.group(1)[4:6])) if m else ''
        lines = _section(text, SEC_CHANGE)
        seen = set(lines)
        for x in _meta_changes(folder):
            if x not in seen:
                lines.append(x); seen.add(x)
        for ln in lines:
            rows.append([site, day, who, fname, ln])
    rows.sort(key=lambda r: (r[0], r[1]), reverse=False)
    return rows

def write_changes(rows):
    od = outdir(TOOL)
    allp = write_csv(os.path.join(od, '회의변경수량_전체_%s.csv' % ymd6()), rows, ['현장', '회의일', '협의자', '회의폴더', '내용'])
    per = {}
    for r in rows:
        per.setdefault(r[0], []).append(r)
    files = {}
    for site, rs in per.items():
        files[site] = write_csv(os.path.join(od, '%s_회의변경수량_%s.csv' % (safe_name(site), ymd6())), rs,
                                ['현장', '회의일', '협의자', '회의폴더', '내용'])
    return allp, files

def _norm(s):
    return re.sub(r'[\s_\-\[\]\(\)]', '', str(s or '')).lower()

def changes_for(site, days=None):
    """30번·33번이 부른다 : 이 현장의 회의 변경 줄 (가장 최근 csv 에서)"""
    xs = glob.glob(os.path.join(cfg('out'), safe_name(TOOL), '*', '회의변경수량_전체_*.csv'))
    if not xs:
        return []
    xs.sort(key=os.path.getmtime)
    rows = []
    for i, line in enumerate(read_text(xs[-1]).splitlines()):
        if i == 0 or not line.strip():
            continue
        try:
            r = [c.strip() for c in next(csv.reader([line]))]
        except Exception:
            continue
        if len(r) < 5:
            continue
        a, b = _norm(r[0]), _norm(site)
        if site and not (a == b or (a and b and (a in b or b in a))):
            continue
        rows.append(r)
    if days:
        cut = (today() - datetime.timedelta(days=days)).isoformat()
        rows = [r for r in rows if not r[1] or r[1] >= cut]
    return rows

# ---------------- 4) 회의록 코드 백업 ----------------

def _hash_dir(files):
    h = hashlib.md5()
    for p in sorted(files):
        h.update(os.path.basename(p).encode('utf-8'))
        try:
            h.update(open(p, 'rb').read())
        except Exception:
            pass
    return h.hexdigest()[:10]

def backup_code():
    """_현장비서 코드를 인수인계함\\회의록코드_백업\\{ymd}_{hash}\\ 에 복사 + 다운로드\\KM_회의록코드_{ymd}.zip"""
    _, b = biseo_inbox()
    if not os.path.isdir(b):
        return None, '_현장비서 폴더 없음'
    files = []
    for pat in ('*.bat', '*.txt', os.path.join('코드', '*.py'), os.path.join('코드', '*.txt'), os.path.join('코드', '*.ini')):
        files += glob.glob(os.path.join(b, pat))
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None, '복사할 코드 없음'
    hp = cfg('handover')
    root = os.path.join(hp, '회의록코드_백업')
    os.makedirs(root, exist_ok=True)
    tag = _hash_dir(files)
    for d in glob.glob(os.path.join(root, '*_' + tag)):
        if os.path.isdir(d):
            return d, '바뀐 것 없음 (이미 %s)' % os.path.basename(d)
    dst = os.path.join(root, '%s_%s' % (ymd6(), tag))
    os.makedirs(dst, exist_ok=True)
    for f in files:
        rel = os.path.relpath(f, b)
        t = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(t), exist_ok=True)
        shutil.copy2(f, t)
    z = os.path.join(downloads(), 'KM_회의록코드_%s.zip' % ymd6())
    try:
        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, os.path.relpath(f, b))
    except Exception:
        z = None
    return dst, '새로 백업 %d개 -> %s%s' % (len(files), dst, (' / zip %s' % z) if z else '')

# ---------------- 실행 ----------------

def run(quiet=False):
    if not quiet:
        title('40. 회의 연결   (받는함 -> _현장비서 / 회의록의 수량·규격 변경 모으기 / 회의록 코드 백업)')
    info = {'moved': [], 'skipped': [], 'launch': '', 'changes': 0, 'sites': {}, 'backup': ''}
    try:
        moved, skipped = move_inbox(quiet=quiet)
        info['moved'], info['skipped'] = moved, skipped
        if moved:
            print('받는함 -> 대기함 %d개 : %s' % (len(moved), ', '.join(moved)[:120]))
            info['launch'] = launch_biseo(quiet=quiet)
            print(info['launch'])
        elif not quiet:
            print('받는함에 새 회의 txt 없음 : %s' % inbox_dir())
        for s in skipped:
            print('[못 옮김] %s' % s)
    except Exception as e:
        print('[받는함 오류] %s' % e)
    try:
        rows = collect_changes()
        allp, files = write_changes(rows)
        info['changes'], info['sites'] = len(rows), files
        print('회의록 %d개 파일에서 수량·규격 변경 %d줄 -> %s' % (len(meeting_files()), len(rows), allp))
        for site, p in files.items():
            print('   [%s] %d줄' % (site, sum(1 for r in rows if r[0] == site)))
    except Exception as e:
        print('[회의 변경 모으기 오류] %s' % e)
    try:
        d, msg = backup_code()
        info['backup'] = msg
        print('회의록 코드 백업 : %s' % msg)
        if d and '새로' in msg:
            print('   -> 다운로드 폴더의 KM_회의록코드_*.zip 을 대화창에 첨부하시면 저장소에 넣어 98번 갱신 대상이 됩니다.')
    except Exception as e:
        print('[코드 백업 오류] %s' % e)
    log(TOOL, '옮김%d 변경%d %s' % (len(info['moved']), info['changes'], '자동' if quiet else ''))
    return info

if __name__ == '__main__':
    run(); pause()

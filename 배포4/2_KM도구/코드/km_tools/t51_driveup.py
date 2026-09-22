# -*- coding: utf-8 -*-
"""51. 회의록 드라이브로 올리기 - 프로님 손 0.

프로님은 하던 대로 회의록을 저장만 하십니다. 이 도구가 그것을 찾아
구글 드라이브의 「회의록\\incoming」 으로 복사하고, 클로드가 읽어 아침 메일에 싣습니다.

  프로님 -> (저장만) -> [51번이 복사] -> 드라이브 -> [클로드가 읽음] -> 아침 메일

v2 (2026-09-22) 고친 것
  · 회의록을 한 군데(_도구결과)만 보다가 못 찾았다. 이제 아래 네 곳을 다 뒤진다
      _도구결과 / _현장비서 / plaud(26년\\1.현장) / 저장 폴더(base) 아래 「회의록」 폴더 전부
  · 무엇을 어디서 찾았는지 「드라이브올림_결과.txt」 에 남긴다 (한 개도 못 찾으면 그 이유까지)
  · 회의록 폴더가 아니어도 파일 이름·경로에 날짜가 있으면 집는다

두 번 올리지 않는다
  올린 것은 _도구결과\\_대장\\드라이브올림.csv 에 남는다. 같은 파일은 다시 올리지 않는다
  (파일을 고치면 크기·수정시각이 달라지므로 다시 올린다)
"""
import os, io, csv, shutil, configparser, datetime
from common import *

TOOL = '드라이브올림'
INCOMING = os.path.join('회의록', 'incoming')
TAKE_EXT = ('.json', '.docx', '.txt', '.md', '.hwp', '.hwpx')
SKIP_NAMES = ('여기로_plaud를_옮기십시오.txt', '여기에_PLAUD결과를_넣으세요.txt', '읽어보세요.txt')
LOG_HEAD = ['올린날', '현장', '회의폴더', '파일', '크기', '수정시각', '올린이름']
MAX_DEPTH = 5

DRIVE_GUESS = (
    r'G:\내 드라이브', r'G:\My Drive', r'H:\내 드라이브', r'H:\My Drive',
    os.path.expanduser(r'~\Google Drive'), os.path.expanduser(r'~\My Drive'),
    os.path.expanduser(r'~\내 드라이브'),
)


def _ini(sec, key):
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        try:
            c.read(INI, encoding='utf-8')
            if c.has_option(sec, key):
                return c.get(sec, key).strip()
        except Exception:
            pass
    return ''


def drive_root():
    """구글 드라이브 폴더. 설정.ini 가 먼저, 없으면 스스로 찾는다. 못 찾으면 ''"""
    v = _ini('드라이브', '경로')
    if v and os.path.isdir(v):
        return v
    for p in DRIVE_GUESS:
        if os.path.isdir(p):
            return p
    return ''


def roots():
    """회의록이 있을 수 있는 곳 전부. 있는 것만 돌려준다"""
    out = []
    for key in ('out', 'biseo', 'plaud', 'base'):
        try:
            p = cfg(key)
        except Exception:
            continue
        if p and os.path.isdir(p) and p not in out:
            out.append(p)
    try:
        sr = sites_root()
        if sr and os.path.isdir(sr) and sr not in out:
            out.append(sr)
    except Exception:
        pass
    return out


def log_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '드라이브올림.csv')


def _read_log():
    p, done = log_path(), {}
    if not os.path.exists(p):
        return done
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                for r in list(csv.reader(fp))[1:]:
                    r = (r + [''] * 7)[:7]
                    if r[6].strip():
                        done[r[6].strip()] = (r[4].strip(), r[5].strip())
            return done
        except Exception:
            continue
    return done


def _append_log(rows):
    """덮어쓰지 않는다. 있으면 뒤에 붙인다"""
    p, old = log_path(), []
    if os.path.exists(p):
        for enc in ('cp949', 'utf-8-sig', 'utf-8'):
            try:
                with io.open(p, 'r', encoding=enc, newline='') as fp:
                    old = list(csv.reader(fp))[1:]
                break
            except Exception:
                continue
    write_csv(p, old + rows, LOG_HEAD)


def _under(path, parent):
    """path 가 parent 안에 있나"""
    if not parent:
        return False
    a = os.path.normcase(os.path.abspath(path))
    b = os.path.normcase(os.path.abspath(parent))
    return a == b or a.startswith(b + os.sep)


def find_meetings(note=None, skip_under=''):
    """[(현장, 회의폴더, 파일경로)] — 여러 뿌리 아래 「회의록」 폴더를 전부 찾는다.
    skip_under : 이 폴더 아래는 보지 않는다 (내가 올려 놓은 드라이브 폴더를 다시 집지 않게)"""
    found, seen = [], set()
    for root in roots():
        if skip_under and _under(root, skip_under):
            if note is not None:
                note.append('  건너뜀 : %s   (드라이브 안이라 제외)' % root)
            continue
        cnt0 = len(found)
        base_depth = root.count(os.sep)
        for dp, dirs, files in os.walk(root):
            if skip_under and _under(dp, skip_under):
                dirs[:] = []
                continue
            if dp.count(os.sep) - base_depth > MAX_DEPTH:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not d.startswith(('.', '~$', '__'))]
            parts = dp.split(os.sep)
            if '회의록' not in parts:
                continue
            i = parts.index('회의록')
            현장 = parts[i - 1] if i >= 1 else '현장미상'
            회의폴더 = os.sep.join(parts[i + 1:]) or '(회의록 바로 아래)'
            for fn in sorted(files):
                if fn in SKIP_NAMES or fn.startswith('~$'):
                    continue
                if os.path.splitext(fn)[1].lower() not in TAKE_EXT:
                    continue
                full = os.path.join(dp, fn)
                key = os.path.normcase(full)
                if key in seen:
                    continue
                seen.add(key)
                found.append((현장, 회의폴더, full))
        if note is not None:
            note.append('  본 곳 : %s   -> 회의록 파일 %d개' % (root, len(found) - cnt0))
    return found


def flat_name(site, meet, fn):
    """드라이브에서는 한 폴더에 평평하게 놓는다. 어느 현장·어느 회의인지 이름에 남긴다"""
    meet = meet.replace(os.sep, '_')
    return safe_name('%s__%s__%s' % (site, meet, fn), 150)


def run(quiet=False):
    if not quiet:
        title('51. 회의록 드라이브로 올리기')

    note = ['=' * 64,
            ' 51번 회의록 드라이브 올리기   %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            '=' * 64]

    root = drive_root()
    if not root:
        note.append('')
        note.append('★ 구글 드라이브 폴더를 못 찾았습니다.')
        note.append('  · 구글 드라이브 데스크톱이 깔려 있는지 보시고')
        note.append('  · 깔려 있는데 못 찾으면 설정.ini 에 이렇게 적어 주십시오')
        note.append('        [드라이브]')
        note.append('        경로 = G:\\내 드라이브')
        note.append('  찾아본 곳 : ' + ' / '.join(DRIVE_GUESS))
        _save_note(note, quiet)
        log(TOOL, '드라이브 폴더 못 찾음')
        return {'올림': 0, '이유': '드라이브 폴더 없음'}

    dest = os.path.join(root, INCOMING)
    try:
        os.makedirs(dest, exist_ok=True)
    except Exception as err:
        note.append('★ 드라이브 폴더를 만들지 못했습니다 : %s' % err)
        _save_note(note, quiet)
        return {'올림': 0, '이유': '드라이브 폴더 만들기 실패'}

    note.append(' 드라이브 : %s' % dest)
    note.append('')
    note.append('[회의록을 찾은 곳]')
    hits = find_meetings(note, skip_under=os.path.join(root, '회의록'))
    note.append('  합계 : 회의록 파일 %d개' % len(hits))
    note.append('')

    done, rows, sent, skip, fail = _read_log(), [], 0, 0, 0
    for site, meet, src in hits:
        fn = os.path.basename(src)
        name = flat_name(site, meet, fn)
        try:
            st = os.stat(src)
            size, mtime = str(st.st_size), str(int(st.st_mtime))
        except Exception:
            continue
        if done.get(name) == (size, mtime):
            skip += 1
            continue
        try:
            shutil.copy2(src, os.path.join(dest, name))
        except Exception as err:
            fail += 1
            note.append('  못 올림 : %s  (%s)' % (name, err))
            continue
        rows.append([today(), site, meet, fn, size, mtime, name])
        sent += 1
        note.append('  올림 : %s' % name)

    if rows:
        _append_log(rows)

    note.append('')
    note.append('[결과]  새로 올림 %d개 · 이미 올린 것 %d개 · 실패 %d개' % (sent, skip, fail))
    if sent:
        note.append('  → 클로드 대화창에 「올렸어」 라고만 하시면 읽어서 메일로 보냅니다.')
    elif not hits:
        note.append('  ★ 회의록을 한 개도 못 찾았습니다.')
        note.append('     「회의록」 이라는 이름의 폴더 안에 파일이 있어야 찾습니다.')
        note.append('     회의록을 저장하시는 폴더 주소를 클로드에게 알려 주십시오.')
    else:
        note.append('  전부 전에 올린 것입니다. 새로 저장하신 회의록이 없습니다.')
    note.append('')
    note.append('이 글은 아래 파일에도 저장했습니다. 클로드에게 그대로 보여 주시면 됩니다.')

    _save_note(note, quiet)
    log(TOOL, '올림 %d · 건너뜀 %d · 실패 %d · 찾음 %d' % (sent, skip, fail, len(hits)))
    if not quiet:
        pause()
    return {'올림': sent, '건너뜀': skip, '실패': fail, '찾음': len(hits), '대상': dest}


def _save_note(note, quiet):
    """결과를 _도구결과 와 도구 폴더 두 군데에 남기고, 조용한 모드가 아니면 띄운다"""
    txt = '\n'.join(note) + '\n'
    paths = []
    try:
        p = os.path.join(cfg('out'), '드라이브올림_결과.txt')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        paths.append(p)
    except Exception:
        pass
    paths.append(os.path.join(HERE, '드라이브올림_결과.txt'))
    for p in paths:
        try:
            io.open(p, 'w', encoding='utf-8', newline='\r\n').write(txt + '  ' + p + '\n')
        except Exception:
            pass
    if not quiet:
        print(txt)
        if paths:
            print('  ' + paths[0])
            try:
                if os.name == 'nt':
                    os.startfile(paths[0])
            except Exception:
                pass


if __name__ == '__main__':
    run()

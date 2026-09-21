# -*- coding: utf-8 -*-
"""51. 회의록 드라이브로 올리기 - 프로님 손 0.

무엇을 하나
  프로님은 하던 대로 「!!클로드가 저장하는 폴더」 에 회의록을 저장만 하십니다.
  이 도구가 그 폴더를 훑어서, 새로 생긴 회의록을 구글 드라이브의
  「회의록 / incoming」 으로 **복사**합니다. 클로드는 드라이브를 읽어 아침 메일에 싣습니다.

  프로님 -> (저장만) -> [이 도구가 복사] -> 드라이브 -> [클로드가 읽음] -> 아침 메일
                          ^^^^^^^^^^^^^ 여기가 이 파일

왜 복사인가 (인증이 필요 없다)
  구글 드라이브 데스크톱(Google Drive for desktop)을 깔면 드라이브가 PC 의 한 폴더로 잡힙니다.
  그래서 이 도구는 구글 로그인·API 키 없이 **그냥 파일 복사**만 합니다. 0원, 설정 없음.

  드라이브 폴더를 못 찾으면 설정.ini 에 적어 주시면 됩니다.
      [드라이브]
      경로 = G:\\내 드라이브

두 번 올리지 않는다
  올린 것은 _도구결과\\_대장\\드라이브올림.csv 에 남습니다. 같은 파일은 다시 올리지 않습니다.
  (파일이 고쳐지면 크기·수정시각이 달라지므로 다시 올립니다)
"""
import os, io, csv, shutil, configparser
from common import *

TOOL = '드라이브올림'
INCOMING = os.path.join('회의록', 'incoming')     # 드라이브 안에서의 위치
MEET_DIRS = ('회의록',)
TAKE_EXT = ('.json', '.docx', '.txt', '.md')      # 올릴 확장자 (meta.json 이 제일 쓸모 있다)
SKIP_NAMES = ('여기로_plaud를_옮기십시오.txt',)
LOG_HEAD = ['올린날', '현장', '회의폴더', '파일', '크기', '수정시각', '올린이름']

# 구글 드라이브 데스크톱이 흔히 잡히는 자리
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


def log_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '드라이브올림.csv')


def _read_log():
    """{올린이름: (크기, 수정시각)}"""
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
    p = log_path()
    old = []
    if os.path.exists(p):
        for enc in ('cp949', 'utf-8-sig', 'utf-8'):
            try:
                with io.open(p, 'r', encoding=enc, newline='') as fp:
                    old = list(csv.reader(fp))[1:]
                break
            except Exception:
                continue
    write_csv(p, old + rows, LOG_HEAD)


def find_meetings():
    """[(현장, 회의폴더명, 파일경로)] - {out}\\{현장}\\회의록\\{폴더}\\* 를 훑는다"""
    out, found = cfg('out'), []
    if not os.path.isdir(out):
        return found
    for site in sorted(os.listdir(out)):
        sp = os.path.join(out, site)
        if not os.path.isdir(sp) or site.startswith('_') or site.startswith('00'):
            continue
        for md in MEET_DIRS:
            mp = os.path.join(sp, md)
            if not os.path.isdir(mp):
                continue
            for meet in sorted(os.listdir(mp)):
                dp = os.path.join(mp, meet)
                if not os.path.isdir(dp):
                    continue
                for fn in sorted(os.listdir(dp)):
                    if fn in SKIP_NAMES or fn.startswith('~$'):
                        continue
                    if os.path.splitext(fn)[1].lower() not in TAKE_EXT:
                        continue
                    found.append((site, meet, os.path.join(dp, fn)))
    return found


def flat_name(site, meet, fn):
    """드라이브에서는 한 폴더에 평평하게 놓는다. 어느 현장·어느 회의인지 이름에 남긴다"""
    return safe_name('%s__%s__%s' % (site, meet, fn), 150)


def run(quiet=False):
    if not quiet:
        title('51. 회의록 드라이브로 올리기')

    root = drive_root()
    if not root:
        msg = ('구글 드라이브 폴더를 못 찾았습니다.\n'
               '  · 구글 드라이브 데스크톱이 깔려 있는지 보시고\n'
               '  · 깔려 있는데 못 찾으면 설정.ini 에 이렇게 적어 주십시오\n'
               '        [드라이브]\n        경로 = G:\\내 드라이브')
        if not quiet:
            print(msg)
            pause()
        log(TOOL, '드라이브 폴더 못 찾음')
        return {'올림': 0, '이유': '드라이브 폴더 없음'}

    dest = os.path.join(root, INCOMING)
    os.makedirs(dest, exist_ok=True)

    done, rows, sent, skip = _read_log(), [], 0, 0
    for site, meet, src in find_meetings():
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
            if not quiet:
                print('  못 올림 : %s (%s)' % (name, err))
            continue
        rows.append([today(), site, meet, fn, size, mtime, name])
        sent += 1
        if not quiet:
            print('  올림 : %s' % name)

    if rows:
        _append_log(rows)
    log(TOOL, '올림 %d · 건너뜀 %d · 대상 %s' % (sent, skip, dest))

    if not quiet:
        print()
        print('  드라이브 : %s' % dest)
        print('  새로 올린 것 %d개 · 이미 올린 것 %d개' % (sent, skip))
        if sent:
            print('  내일 아침 메일에 이 회의들이 실립니다.')
        pause()
    return {'올림': sent, '건너뜀': skip, '대상': dest}


if __name__ == '__main__':
    run()

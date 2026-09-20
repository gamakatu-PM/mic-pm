# -*- coding: utf-8 -*-
"""KM 산군 도구 설치 — 더블클릭 한 번으로 제자리에 넣어 드립니다. (2026-09-20)

하는 일
  1) 「!!클로드가 저장하는 폴더」 를 스스로 찾습니다 (못 찾으면 여쭙니다)
  2) 파이썬 도구 3개를 2_KM도구\\코드\\km_tools 에 넣습니다 (기존 파일은 백업)
  3) 시작.py 메뉴에 49·50번 두 줄을 넣습니다 (이미 있으면 건너뜁니다)
  4) 산군 엑셀을 두실 「산군」 폴더를 만듭니다
  5) 구글시트 코드 2개와 인수인계 문서를 제자리에 둡니다
아무것도 지우지 않습니다. 바꾼 파일은 전부 백업을 남깁니다.
"""
import os
import sys
import shutil
import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '파일')
STAMP = datetime.date.today().strftime('%y%m%d')
MARK = ['클로드가 저장하는', '!!클로드가']
INSIDE = ('2_KM도구', '_현장비서', '_원틀', '4_원틀', '3_공통사용', 'plaud')

MENU49 = ("   ('산군 관심현장 정리  산군 파일 → 새 현장만 판정·중복제거 (토큰 0)', 't49_sangun'),")
MENU50 = ("   ('산군 흔적 찾기·메일  인터넷에서 찾아 빨리 갈 곳/물어볼 곳으로 갈라 메일 · 주1회 자동 (토큰 0)', 't50_sangun_trace')")

log = []


def say(s):
    print(s)
    log.append(s)


def looks_like_base(d):
    try:
        names = set(os.listdir(d))
    except Exception:
        return False
    return sum(1 for k in INSIDE if k in names) >= 1


def find_base():
    home = os.path.expanduser('~')
    cand = []
    for od in (os.path.join(home, 'OneDrive'), home, 'C:\\', 'D:\\'):
        if not os.path.isdir(od):
            continue
        for root, dirs, _ in os.walk(od):
            # 너무 깊이 들어가지 않는다
            if root.count(os.sep) - od.count(os.sep) > 3:
                dirs[:] = []
                continue
            for d in list(dirs):
                if any(m in d for m in MARK):
                    p = os.path.join(root, d)
                    cand.append((0 if looks_like_base(p) else 1, p))
            if len(cand) > 30:
                break
        if cand:
            break
    cand.sort()
    return [p for _, p in cand]


def backup(path):
    if not os.path.exists(path):
        return ''
    bak = '%s.백업_%s' % (path, STAMP)
    n = 1
    while os.path.exists(bak):
        bak = '%s.백업_%s_%d' % (path, STAMP, n)
        n += 1
    shutil.copy2(path, bak)
    return bak


def put(src, dstdir, name=None):
    os.makedirs(dstdir, exist_ok=True)
    dst = os.path.join(dstdir, name or os.path.basename(src))
    b = backup(dst)
    shutil.copy2(src, dst)
    return dst, b


def fix_menu(tools):
    """시작.py 메뉴(menu.py)에 49·50번 두 줄을 넣는다. 이미 있으면 건드리지 않는다."""
    mp = os.path.join(tools, 'menu.py')
    if not os.path.exists(mp):
        return '메뉴 파일(menu.py)을 못 찾아 건너뜁니다 — 49·50 은 번호 대신 파일을 직접 실행하셔도 됩니다.'
    import io
    s = io.open(mp, encoding='utf-8').read()
    if 't49_sangun' in s and 't50_sangun_trace' in s:
        return '메뉴에 이미 들어 있습니다 (건드리지 않았습니다).'
    anchor = "'t48_reply')]),"
    if anchor not in s:
        return '메뉴 모양이 달라 자동으로 못 넣었습니다 — 이 창 내용을 클로드에게 보여 주십시오.'
    backup(mp)
    s = s.replace(anchor, "'t48_reply'),\n%s\n%s]),"  % (MENU49, MENU50), 1)
    io.open(mp, 'w', encoding='utf-8').write(s)
    return '메뉴에 49·50번을 넣었습니다 (원래 파일은 menu.py.백업_%s).' % STAMP


def main():
    print('=' * 60)
    print(' KM 산군 도구 설치  (2026-09-20)')
    print('=' * 60)
    if not os.path.isdir(SRC):
        print('[오류] 「파일」 폴더가 없습니다. zip 을 폴더째 풀고 다시 실행해 주십시오.')
        return

    base = ''
    cands = find_base()
    if cands:
        print('찾은 폴더')
        for i, p in enumerate(cands[:5], 1):
            print('  %d) %s' % (i, p))
        v = input('번호 (엔터=1번, 다르면 경로를 붙여넣기) > ').strip()
        base = cands[int(v) - 1] if (v.isdigit() and 1 <= int(v) <= len(cands[:5])) else (v or cands[0])
    else:
        print('「!!클로드가 저장하는 폴더」 를 못 찾았습니다.')
        base = input('그 폴더 경로를 붙여넣어 주십시오 > ').strip().strip('"')
    if not base or not os.path.isdir(base):
        print('[멈춤] 폴더를 못 찾았습니다 : %s' % base)
        return
    say('폴더 : %s' % base)
    print('')

    tools = os.path.join(base, '2_KM도구', '코드', 'km_tools')
    if not os.path.isdir(tools):
        alt = os.path.join(base, '현장비서_도구', '코드', 'km_tools')
        tools = alt if os.path.isdir(alt) else tools
    os.makedirs(tools, exist_ok=True)

    n = 0
    for f in sorted(os.listdir(os.path.join(SRC, 'km_tools'))):
        if not f.endswith('.py'):
            continue
        dst, b = put(os.path.join(SRC, 'km_tools', f), tools)
        n += 1
        say('  넣음 : %s%s' % (f, '  (기존 것은 백업)' if b else ''))
    say('1) 파이썬 도구 %d개를 넣었습니다 → %s' % (n, tools))

    say('2) ' + fix_menu(tools))

    sg = os.path.join(base, '산군')
    os.makedirs(sg, exist_ok=True)
    say('3) 산군 엑셀을 두실 폴더를 만들었습니다 → %s' % sg)

    gs = os.path.join(base, '3_공통사용', '구글시트코드')
    for f in sorted(os.listdir(os.path.join(SRC, '구글시트코드'))):
        put(os.path.join(SRC, '구글시트코드', f), gs)
    say('4) 구글시트 코드를 두었습니다 → %s' % gs)

    hd = os.path.join(base, 'KM_인수인계함')
    if not os.path.isdir(hd):
        hd = os.path.join(base, '3_공통사용', '인수인계함')
    for f in sorted(os.listdir(os.path.join(SRC, '인수인계함'))):
        put(os.path.join(SRC, '인수인계함', f), hd)
    say('5) 인수인계 문서를 두었습니다 → %s' % hd)

    appsrc = os.path.join(SRC, '앱', 'index.html')
    if os.path.exists(appsrc):
        appdir = os.path.join(base, '5_산출물', '앱')
        put(appsrc, appdir)
        say('6) 앱 파일을 두었습니다 → %s\\index.html  (쓰시던 자리에 덮어쓰셔도 됩니다)' % appdir)

    try:
        import io
        io.open(os.path.join(HERE, '설치결과_%s.txt' % STAMP), 'w', encoding='utf-8').write('\n'.join(log))
    except Exception:
        pass

    print('')
    print('=' * 60)
    print(' 끝났습니다. 이제 이렇게 하십시오')
    print('=' * 60)
    print(' ① 산군에서 고르신 엑셀(300건)을 이 폴더에 넣으십시오')
    print('    %s' % sg)
    print(' ② 2_KM도구\\시작.py(또는 시작.bat)를 켜고 49번을 누르십시오')
    print(' ③ 49번이 끝나면 엔터 — 50번이 인터넷에서 흔적을 찾아 메일을 보냅니다')
    print('')
    print(' 메일이 안 가면 35번(아침 메일)에서 보내는 계정을 먼저 넣으십시오.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('')
        print('[멈췄습니다] %s' % e)
        print('이 창을 캡처해서 클로드에게 보여 주십시오.')
    try:
        input('\n엔터를 누르면 닫힙니다...')
    except Exception:
        pass

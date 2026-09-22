# -*- coding: utf-8 -*-
"""51번 설치 - 이 파일과 t51_driveup.py 두 개를 km_tools 폴더에 넣고, 이 파일을 더블클릭하면 끝.

★ 결과는 같은 폴더의 「설치_51번_결과.txt」 에 남고, 끝나면 그 파일이 저절로 열립니다.
   창이 순식간에 닫혀도 그 txt 를 보시면 됩니다.

하는 일 (있는 것은 건드리지 않는다. 없는 줄만 끼워 넣는다)
  1. menu.py        「총괄」 맨 뒤에 51번 한 줄 추가   (49·50번 등 기존 줄은 그대로)
  2. t36_today.py   40번(회의 연결) 뒤에 51번 호출 추가 (오늘 한 방에 가 저절로 돌림)
  3. 설정.ini       [드라이브] 칸 추가 (비워 두면 스스로 찾음)
  4. 구글 드라이브 폴더를 찾아서 결과를 보여 준다
고치기 전 원본은 같은 폴더에 *.bak_51 로 남긴다.
"""
import os, io, sys, shutil, datetime, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
LOG = os.path.join(HERE, '설치_51번_결과.txt')
_lines = []

def say(s=''):
    _lines.append(s)
    try:
        print(s)
    except Exception:
        pass

def read(p):
    raw = io.open(p, 'rb').read()
    for enc in ('utf-8-sig', 'utf-8', 'cp949'):
        try:
            return raw.decode(enc), ('utf-8' if enc == 'utf-8-sig' else enc), raw[:3] == b'\xef\xbb\xbf'
        except Exception:
            continue
    raise RuntimeError('읽지 못함 : %s' % p)

def write(p, s, enc, bom):
    shutil.copy2(p, p + '.bak_51')
    with io.open(p, 'w', encoding=('utf-8-sig' if bom else enc), newline='') as fp:
        fp.write(s)

done, skipped, bad = [], [], []
drive = ''

try:
    # ── 0. t51 파일이 옆에 있나
    if not os.path.exists('t51_driveup.py'):
        bad.append('t51_driveup.py 가 이 폴더에 없습니다. 같이 받은 파일을 여기에 넣어 주십시오')

    # ── 1. menu.py
    try:
        s, enc, bom = read('menu.py')
        if 't51_driveup' in s:
            skipped.append('menu.py 에 51번이 이미 있음')
        else:
            # 48번이 있는 「총괄」 묶음의 맨 끝( )]), )을 찾아 그 앞에 끼운다 -> 49·50번이 뒤에 있어도 맨 뒤로 들어간다
            i = s.find("'t48_reply'")
            j = s.find(")]),", i) if i >= 0 else -1
            if j < 0:
                bad.append('menu.py 에서 48번 묶음의 끝을 못 찾음 (구조가 다름). 손대지 않았습니다')
            else:
                item = ",\n   ('회의록 드라이브로 올리기  저장만 해 두시면 구글 드라이브로 복사 → 클로드가 읽어 아침 메일에 실음 (36번이 저절로 돌림)', 't51_driveup')"
                write('menu.py', s[:j + 1] + item + s[j + 1:], enc, bom)
                done.append('menu.py 「총괄」 맨 뒤에 51번 추가')
    except Exception as e:
        bad.append('menu.py : %s' % e)

    # ── 2. t36_today.py
    try:
        s, enc, bom = read('t36_today.py')
        if 't51_driveup' in s:
            skipped.append('t36_today.py 에 51번 호출이 이미 있음')
        else:
            anchor = "print('-' * 74); print(' >> 31 도면 접수"
            i = s.find(anchor)
            if i < 0:
                bad.append('t36_today.py 에서 31번 자리를 못 찾음. 손대지 않았습니다 (51번은 메뉴에서 직접 누르시면 됩니다)')
            else:
                ls = s.rfind('\n', 0, i) + 1
                indent = s[ls:i]
                block = (indent + "try:\n" +
                         indent + "    import t51_driveup as DU     # 51 회의록을 구글 드라이브로 (클로드가 읽어 아침 메일에 싣는다)\n" +
                         indent + "    _d = DU.run(quiet=True)\n" +
                         indent + "    if _d.get('올림'):\n" +
                         indent + "        print('   회의록 %d개를 드라이브로 올림' % _d['올림'])\n" +
                         indent + "    elif _d.get('이유'):\n" +
                         indent + "        print('   회의록 드라이브 올리기 건너뜀 : %s' % _d['이유'])\n" +
                         indent + "except Exception:\n" +
                         indent + "    traceback.print_exc()\n")
                write('t36_today.py', s[:ls] + block + s[ls:], enc, bom)
                done.append('t36_today.py 에 51번 호출 추가 (40번 뒤)')
    except Exception as e:
        bad.append('t36_today.py : %s' % e)

    # ── 3. 설정.ini
    try:
        if os.path.exists('설정.ini'):
            s, enc, bom = read('설정.ini')
            if '[드라이브]' in s:
                skipped.append('설정.ini 에 [드라이브] 칸이 이미 있음')
            else:
                s = s.rstrip() + "\n\n[드라이브]\n; 구글 드라이브 데스크톱이 잡아 놓은 폴더. 비우면 스스로 찾습니다 (G:\\내 드라이브 등)\n; 51번이 여기 아래 「회의록\\incoming」 으로 회의록을 복사합니다\n경로 =\n"
                write('설정.ini', s, enc, bom)
                done.append('설정.ini 에 [드라이브] 칸 추가')
        else:
            skipped.append('설정.ini 없음 (없어도 됩니다)')
    except Exception as e:
        bad.append('설정.ini : %s' % e)

    # ── 4. 문법·드라이브 확인
    try:
        import py_compile
        for f in ('menu.py', 't36_today.py', 't51_driveup.py'):
            if os.path.exists(f):
                py_compile.compile(f, doraise=True)
        sys.path.insert(0, HERE)
        import t51_driveup as T
        drive = T.drive_root()
    except Exception as e:
        bad.append('확인 중 오류 : %s' % e)

except Exception:
    bad.append('뜻밖의 오류 :\n' + traceback.format_exc())

# ── 결과
say('=' * 64)
say(' 51번 설치 결과   %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
say(' 자리 : %s' % HERE)
say('=' * 64)
for d in done:    say('  했음   : ' + d)
for d in skipped: say('  건너뜀 : ' + d)
for d in bad:     say('  ★문제  : ' + d)
if not (done or skipped or bad):
    say('  아무것도 하지 못했습니다')
say('')
if drive:
    say('  구글 드라이브 폴더 : ' + drive)
    say('  회의록이 갈 곳     : ' + os.path.join(drive, '회의록', 'incoming'))
    say('')
    say('  → 여기까지 나왔으면 설치는 끝입니다.')
    say('  → 시작.py 를 열고 번호 없이 엔터를 한 번 치시면 지금까지의 회의록이 올라갑니다.')
    say('  → 그 뒤 클로드 대화창에 「올렸어」 라고만 하시면 됩니다.')
else:
    say('  구글 드라이브 폴더를 못 찾았습니다.')
    say('')
    say('  → 구글 드라이브 데스크톱이 안 깔려 있으면 설치해 주십시오 (무료)')
    say('  → 깔려 있는데 못 찾으면, 탐색기에서 드라이브 폴더 주소를 복사해')
    say('     설정.ini 의 [드라이브] 경로 = 뒤에 붙여 주십시오')
    say('     예)  경로 = G:\\내 드라이브')
say('')
say('  이 글은 아래 파일에도 저장했습니다. 클로드에게 그대로 보여 주시면 됩니다.')
say('  ' + LOG)

# 파일로 남기고, 그 파일을 열어 준다 (창이 닫혀도 볼 수 있게)
try:
    io.open(LOG, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(_lines) + '\n')
except Exception:
    pass
try:
    if os.name == 'nt':
        os.startfile(LOG)
except Exception:
    pass
try:
    input('\n아무 키나 누르면 닫힙니다 ')
except Exception:
    pass

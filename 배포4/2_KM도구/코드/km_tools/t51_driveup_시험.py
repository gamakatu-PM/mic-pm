# -*- coding: utf-8 -*-
"""t51 자가시험 - 가짜 폴더를 만들어 실제로 돌려 본다"""
import os, sys, io, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath('.')) )
sys.path.insert(0, '.')
import common, t51_driveup as T

tmp = tempfile.mkdtemp()
OUT   = os.path.join(tmp, '_도구결과')
DRIVE = os.path.join(tmp, '내드라이브')
os.makedirs(DRIVE)

def mk(site, meet, fn, body):
    d = os.path.join(OUT, site, '회의록', meet); os.makedirs(d, exist_ok=True)
    io.open(os.path.join(d, fn), 'w', encoding='utf-8').write(body)
    return os.path.join(d, fn)

mk('연합기숙사', '260910_일능_홍승조부장_부분납품', 'meta.json', '{"현장":"연합기숙사"}')
mk('연합기숙사', '260910_일능_홍승조부장_부분납품', '연합기숙사_회의록.docx', 'x'*50)
mk('앵커호텔',   '260912_삼우MEP_김과장_수량변경',   'meta.json', '{"현장":"앵커호텔"}')
mk('앵커호텔',   '260912_삼우MEP_김과장_수량변경',   '~$임시.docx', 'skip')
mk('앵커호텔',   '260912_삼우MEP_김과장_수량변경',   '사진.png',    'skip')
os.makedirs(os.path.join(OUT, '_대장'), exist_ok=True)
os.makedirs(os.path.join(OUT, '00_업무판'), exist_ok=True)   # _ 00 으로 시작 -> 현장 아님

common.DEFAULTS['out'] = OUT
T._ini = lambda s, k: DRIVE if (s, k) == ('드라이브', '경로') else ''

bad = 0
def chk(name, cond, extra=''):
    global bad
    print(('  OK  ' if cond else '  FAIL') + ' ' + name + (' ' + str(extra) if extra else ''))
    if not cond: bad += 1

print('[1] 처음 올리기')
r = T.run(quiet=True)
inc = os.path.join(DRIVE, '회의록', 'incoming')
files = sorted(os.listdir(inc))
chk('3개 올림 (meta 2 + docx 1)', r['올림'] == 3, r)
chk('임시파일 ~$ 안 올림', not any('~$' in f for f in files))
chk('png 안 올림', not any(f.endswith('.png') for f in files))
chk('현장 이름이 파일명에', any('연합기숙사' in f for f in files), files[:1])
chk('회의폴더명이 파일명에', any('260912' in f for f in files))
chk('00_ 폴더는 현장으로 안 봄', not any('업무판' in f for f in files))

print('[2] 다시 돌리면 두 번 안 올림')
r2 = T.run(quiet=True)
chk('올림 0', r2['올림'] == 0, r2)
chk('건너뜀 3', r2['건너뜀'] == 3, r2)

print('[3] 파일이 바뀌면 다시 올림')
p = mk('앵커호텔', '260912_삼우MEP_김과장_수량변경', 'meta.json', '{"현장":"앵커호텔","객실":330}')
os.utime(p, (9e8, 9e8))
r3 = T.run(quiet=True)
chk('바뀐 것 1개만 다시 올림', r3['올림'] == 1, r3)

print('[4] 새 회의가 생기면 그것만 올림')
mk('제천워케이션', '260921_시공사_박부장_일정', 'meta.json', '{}')
r4 = T.run(quiet=True)
chk('새 것 1개만', r4['올림'] == 1, r4)

print('[5] 대장이 덮어써지지 않는다')
import csv
lp = T.log_path()
rows = []
for enc in ('cp949','utf-8-sig','utf-8'):
    try:
        with io.open(lp,'r',encoding=enc,newline='') as fp: rows = list(csv.reader(fp))
        break
    except Exception: continue
chk('머리 1줄 + 기록 5줄', len(rows) == 6, len(rows))
chk('머리가 올린이름으로 끝남', rows[0][-1] == '올린이름', rows[0])

print('[6] 드라이브 폴더를 못 찾을 때')
T._ini = lambda s, k: ''
save = T.DRIVE_GUESS; T.DRIVE_GUESS = ()
r6 = T.run(quiet=True)
chk('멈추지 않고 이유를 준다', r6['올림'] == 0 and '드라이브' in r6.get('이유',''), r6)
T.DRIVE_GUESS = save

shutil.rmtree(tmp, ignore_errors=True)
print()
print(('FAIL %d' % bad) if bad else 'ALL PASS (13/13)')
sys.exit(1 if bad else 0)

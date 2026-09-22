# -*- coding: utf-8 -*-
"""t51 자가시험 v2 - 가짜 폴더를 만들어 실제로 돌려 본다"""
import os, sys, io, tempfile, shutil, csv
sys.path.insert(0, '.')
import common, t51_driveup as T

tmp = tempfile.mkdtemp()
OUT   = os.path.join(tmp, '_도구결과')
BISEO = os.path.join(tmp, '_현장비서')
PLAUD = os.path.join(tmp, 'plaud', '26년')
BASE  = tmp
DRIVE = os.path.join(tmp, '내드라이브'); os.makedirs(DRIVE)

def mk(root, site, meet, fn, body, subdir='회의록'):
    d = os.path.join(root, site, subdir, meet) if meet else os.path.join(root, site, subdir)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, fn)
    io.open(p, 'w', encoding='utf-8').write(body)
    return p

# ① _도구결과 구조
mk(OUT, '연합기숙사', '260910_일능_홍승조부장_부분납품', 'meta.json', '{}')
mk(OUT, '연합기숙사', '260910_일능_홍승조부장_부분납품', '연합기숙사_회의록.docx', 'x'*50)
# ② _현장비서 구조
mk(BISEO, '앵커호텔', '260912_삼우MEP_김과장', 'meta.json', '{}')
# ③ plaud\26년\1.현장 구조 (시험자료와 같은 모양)
mk(os.path.join(PLAUD, '1.현장'), '양양쏠비치', '260915_권진희과장', '원문.txt', 'hello')
# ④ 회의록 폴더 바로 아래 (회의폴더 없음)
mk(OUT, '제천워케이션', '', '260921_메모.txt', 'memo')
# ⑤ 걸러야 하는 것
mk(OUT, '앵커호텔', '260912_삼우MEP_김과장', '~$임시.docx', 'skip')
mk(OUT, '앵커호텔', '260912_삼우MEP_김과장', '사진.png', 'skip')
mk(OUT, '앵커호텔', '260912_삼우MEP_김과장', '읽어보세요.txt', 'skip')
# ⑥ 회의록 폴더가 아닌 곳 (집지 말아야 함)
os.makedirs(os.path.join(OUT, '연합기숙사', '도면'), exist_ok=True)
io.open(os.path.join(OUT, '연합기숙사', '도면', '도면메모.txt'), 'w', encoding='utf-8').write('no')
os.makedirs(os.path.join(OUT, '_대장'), exist_ok=True)

common.DEFAULTS.update({'out': OUT, 'biseo': BISEO, 'plaud': PLAUD, 'base': BASE})
T._ini = lambda s, k: DRIVE if (s, k) == ('드라이브', '경로') else ''

bad = 0
def chk(name, cond, extra=''):
    global bad
    print(('  OK  ' if cond else '  FAIL') + ' ' + name + (' ' + str(extra) if extra else ''))
    if not cond: bad += 1

inc = os.path.join(DRIVE, '회의록', 'incoming')

print('[1] 네 곳을 다 뒤진다')
r = T.run(quiet=True)
files = sorted(os.listdir(inc))
chk('5개 올림 (도구결과3 + 현장비서1 + plaud1)', r['올림'] == 5, r)
chk('_도구결과 것', any('연합기숙사__260910' in f for f in files))
chk('_현장비서 것', any('앵커호텔__260912' in f and 'meta' in f for f in files))
chk('plaud 것', any('양양쏠비치' in f for f in files), [f for f in files if '양양' in f])
chk('회의록 바로 아래 것', any('제천워케이션' in f for f in files))
chk('~$ 안 올림', not any('~$' in f for f in files))
chk('png 안 올림', not any(f.endswith('.png') for f in files))
chk('읽어보세요 안 올림', not any('읽어보세요' in f for f in files))
chk('회의록 아닌 폴더 안 올림', not any('도면메모' in f for f in files))
chk('결과 txt 생김', os.path.exists(os.path.join(OUT, '드라이브올림_결과.txt')))
t = io.open(os.path.join(OUT, '드라이브올림_결과.txt'), encoding='utf-8').read()
chk('txt 에 본 곳 목록', t.count('본 곳 :') >= 3, t.count('본 곳 :'))
chk('txt 에 합계', '합계 : 회의록 파일 5개' in t)

print('[2] 두 번 돌려도 안 올림')
r2 = T.run(quiet=True)
chk('올림 0 · 건너뜀 5', r2['올림'] == 0 and r2['건너뜀'] == 5, r2)

print('[3] 고치면 다시 올림')
p = mk(OUT, '연합기숙사', '260910_일능_홍승조부장_부분납품', 'meta.json', '{"객실":330}')
os.utime(p, (9e8, 9e8))
r3 = T.run(quiet=True)
chk('1개만 다시', r3['올림'] == 1, r3)

print('[4] 대장이 덮어써지지 않는다')
rows = []
for enc in ('cp949','utf-8-sig','utf-8'):
    try:
        with io.open(T.log_path(),'r',encoding=enc,newline='') as fp: rows = list(csv.reader(fp))
        break
    except Exception: continue
chk('머리 1 + 기록 6줄', len(rows) == 7, len(rows))

print('[5] 회의록이 하나도 없을 때')
tmp2 = tempfile.mkdtemp(); O2 = os.path.join(tmp2, '_도구결과'); os.makedirs(os.path.join(O2, '_대장'))
common.DEFAULTS.update({'out': O2, 'biseo': O2, 'plaud': O2, 'base': tmp2})
r5 = T.run(quiet=True)
chk('올림 0 · 찾음 0', r5['올림'] == 0 and r5['찾음'] == 0, r5)
t5 = io.open(os.path.join(O2, '드라이브올림_결과.txt'), encoding='utf-8').read()
chk('txt 가 이유를 말함', '한 개도 못 찾았습니다' in t5)

print('[6] 드라이브를 못 찾을 때')
T._ini = lambda s, k: ''
save = T.DRIVE_GUESS; T.DRIVE_GUESS = ()
r6 = T.run(quiet=True)
chk('멈추지 않고 이유를 준다', r6['올림'] == 0 and '드라이브' in r6.get('이유',''), r6)
T.DRIVE_GUESS = save

shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(tmp2, ignore_errors=True)
print()
print(('FAIL %d' % bad) if bad else 'ALL PASS (19/19)')
sys.exit(1 if bad else 0)

# -*- coding: utf-8 -*-
"""★회의록 한 방에 — 자가시험. 가짜 드라이브·가짜 도구로 네 걸음이 이어지는지 본다."""
from __future__ import print_function
import os, io, sys, json, shutil, tempfile, datetime, importlib.util

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

ROOT = tempfile.mkdtemp(prefix='km한방에_')
KM = os.path.join(ROOT, '2_KM도구')
TOOLS = os.path.join(KM, '코드', 'km_tools')
DRIVE = os.path.join(ROOT, 'G드라이브')
os.makedirs(TOOLS); os.makedirs(os.path.join(DRIVE, '회의록', 'incoming'))

SRC = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(SRC, '코드', 'km_tools', 't52_mailbuild.py'), TOOLS)
shutil.copy(os.path.join(SRC, '★회의록_한방에.py'), KM)

# 가짜 51번 : 드라이브 폴더만 알려 주고 「올렸다」고 답한다
io.open(os.path.join(TOOLS, 't51_driveup.py'), 'w', encoding='utf-8').write(
    u"DRIVE = %r\n"
    u"def drive_root(): return DRIVE\n"
    u"def run(quiet=False): return {'찾음': 2, '올림': 2}\n" % DRIVE)
# 가짜 40번 : 돌았다는 표시만 남긴다
io.open(os.path.join(TOOLS, 't40_meeting.py'), 'w', encoding='utf-8').write(
    u"import io,os\n"
    u"def run():\n"
    u"    io.open(os.path.join(%r,'40번_돌았음.txt'),'w',encoding='utf-8').write(u'ok')\n"
    u"    return {'옮김':1}\n" % ROOT)

# 어제·오늘 meta.json 2건 + 기간 밖 1건
def meta(site, ymd, topic, decision=''):
    return {'meta': {'site': site, 'ymd': ymd, 'hm': '10:00', 'person': '홍길동 부장',
                     'company': '일능', 'name': '홍길동', 'rank': '부장'},
            'sec': {'1': {'현장': site, '안건': topic,
                          '안건목록': [{'title': topic, 'bullets': ['내용 한 줄'],
                                      'decision': decision, 'actions': ['조치 한 줄']}]},
                    '2': {'할 일': ['- %s | 할 일 한 줄' % ymd]}}}

TODAY = datetime.date.today()
Y = (TODAY - datetime.timedelta(days=1)).strftime('%y%m%d')
T = TODAY.strftime('%y%m%d')
INC = os.path.join(DRIVE, '회의록', 'incoming')
for fn, obj in (('a__meta.json', meta('앵커호텔', Y, '전등회로', '차단기 30A')),
                ('b__meta.json', meta('양양 쏠비치', T, '방문일정')),
                ('c__meta.json', meta('옛날현장', '260101', '지난것'))):
    io.open(os.path.join(INC, fn), 'w', encoding='utf-8').write(
        json.dumps(obj, ensure_ascii=False))

# 돌린다 (엔터 기다리지 않게 stdin 막기)
sys.path.insert(0, KM)
import builtins
builtins.input = lambda *a, **k: ''
spec = importlib.util.spec_from_file_location('한방에', os.path.join(KM, '★회의록_한방에.py'))
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)      # __main__ 이 아니라 main() 은 안 돈다
    mod.main()
except SystemExit:
    pass
mod.save_note()

note = '\n'.join(mod.NOTE)
OUT = os.path.join(KM, '_회의록정리')
MAIL = os.path.join(DRIVE, 'KM_아침메일')

chk('1) 40번이 돌았다', os.path.isfile(os.path.join(ROOT, '40번_돌았음.txt')))
chk('2) 51번이 돌았다', '찾음 2개' in note, note[-300:])
chk('3) 메일 원고를 만들었다', os.path.isfile(os.path.join(OUT, '회의록정리_%s.txt' % T)))
chk('3) 현장별 파일도 만들었다', os.path.isdir(os.path.join(OUT, '현장별_%s' % T)))
chk('4) 원고를 드라이브에 올렸다', os.path.isfile(os.path.join(MAIL, '회의록정리_%s.txt' % T)))
chk('어제~오늘만 담았다(기간 밖 제외)', '옛날현장' not in note and
    '옛날현장' not in io.open(os.path.join(OUT, '회의록정리_%s.txt' % T), encoding='utf-8').read())
chk('현장 2개를 잡았다', '현장 2개' in note, note[-300:])
chk('화면 기록을 파일로 남겼다', os.path.isfile(os.path.join(KM, '한방에_결과.txt')))
chk('걸음마다 제목이 찍힌다', all(x in note for x in ('1) 회의록 만들기', '2) 구글 드라이브로',
                                                   '3) 메일 원고', '4) 메일 원고를 드라이브로')))
chk('끝 인사가 나온다', '끝났습니다' in note)

# 40번이 없을 때도 안 죽는가
os.remove(os.path.join(TOOLS, 't40_meeting.py'))
sys.modules.pop('t40_meeting', None)
for d in (OUT, MAIL):
    shutil.rmtree(d, ignore_errors=True)
mod.NOTE[:] = []
mod.main()
n2 = '\n'.join(mod.NOTE)
chk('40번이 없어도 나머지가 돈다', os.path.isfile(os.path.join(MAIL, '회의록정리_%s.txt' % T)), n2[-300:])
chk('40번 없음을 알려 준다', '40번이 없어 건너뜁니다' in n2)

# 드라이브를 못 찾을 때
io.open(os.path.join(TOOLS, 't51_driveup.py'), 'w', encoding='utf-8').write(
    u"def drive_root(): return ''\n"
    u"def run(quiet=False): return {'올림':0,'이유':'드라이브 폴더 없음'}\n")
for m in ('t51_driveup', 't52_mailbuild'):
    sys.modules.pop(m, None)
mod.NOTE[:] = []
mod.main()
n3 = '\n'.join(mod.NOTE)
chk('드라이브가 없어도 안 죽는다', '드라이브 폴더 없음' in n3, n3[-300:])
chk('드라이브 없음을 끝 인사에서도 말한다', '멈춘 까닭' in n3, n3[-200:])
chk('드라이브 없을 때 이유를 말한다', '건너뜁니다' in n3)

shutil.rmtree(ROOT, ignore_errors=True)
print('\n통과 %d / 실패 %d' % (OK[0], len(NG)))
if NG:
    print('실패:', NG); sys.exit(1)

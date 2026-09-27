# -*- coding: utf-8 -*-
"""★지난 회의록 메일로 — 자가시험."""
from __future__ import print_function
import os, io, sys, json, shutil, tempfile, datetime, importlib.util

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

ROOT = tempfile.mkdtemp(prefix='km지난_')
KM = os.path.join(ROOT, '2_KM도구'); TOOLS = os.path.join(KM, '코드', 'km_tools')
DRIVE = os.path.join(ROOT, 'G드라이브'); INC = os.path.join(DRIVE, '회의록', 'incoming')
MAIL = os.path.join(DRIVE, 'KM_아침메일')
os.makedirs(TOOLS); os.makedirs(INC)
SRC = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(SRC, '코드', 'km_tools', 't52_mailbuild.py'), TOOLS)
shutil.copy(os.path.join(SRC, '★지난회의록_메일로.py'), KM)
io.open(os.path.join(TOOLS, 't51_driveup.py'), 'w', encoding='utf-8').write(
    u"def drive_root(): return %r\n" % DRIVE)

def meta(site, ymd, topic, decision=''):
    return {'meta': {'site': site, 'ymd': ymd, 'hm': '10:00', 'person': '홍길동 부장',
                     'company': '일능', 'name': '홍길동', 'rank': '부장'},
            'sec': {'1': {'현장': site, '안건': topic,
                          '안건목록': [{'title': topic, 'bullets': ['내용'],
                                      'decision': decision, 'actions': ['조치']}]},
                    '2': {'할 일': ['- %s | 할 일' % ymd]}}}

for fn, o in (('a__meta.json', meta('조선호텔', '260901', '일정', '10월 오픈')),
              ('b__meta.json', meta('조선호텔', '260910', '제작')),
              ('c__meta.json', meta('앵커호텔', '260915', '전등회로')),
              ('d__meta.json', meta('먼과거현장', '260501', '아주 옛날'))):
    io.open(os.path.join(INC, fn), 'w', encoding='utf-8').write(json.dumps(o, ensure_ascii=False))

sys.path.insert(0, KM)
spec = importlib.util.spec_from_file_location('지난', os.path.join(KM, '★지난회의록_메일로.py'))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

chk('날짜를 260901 로 고친다', M.norm_ymd('2026-09-01', 'x') == '260901')
chk('26-09-01 도 받는다', M.norm_ymd('26-09-01', 'x') == '260901')
chk('엉뚱한 값이면 기본값', M.norm_ymd('아무거나', '260101') == '260101')
chk('빈칸이면 기본값', M.norm_ymd('', '260101') == '260101')

OUT = os.path.join(KM, '_지난회의록')
st = M.run('260901', '260920', per_site=False, drive=DRIVE, out=OUT)
T = datetime.date.today().strftime('%y%m%d')

chk('기간 안 3건만 담는다', st['회의수'] == 3, str(st['회의수']))
chk('기간 밖(260501) 제외', '먼과거현장' not in io.open(
    os.path.join(OUT, '회의록정리_%s.txt' % T), encoding='utf-8').read())
chk('현장 2개', st['현장수'] == 2, str(st['현장목록']))
chk('드라이브에 1개 올렸다', len(st['올린파일']) == 1)
chk('파일 이름에 기간이 들어간다', '260901-260920' in os.path.basename(st['올린파일'][0]),
    os.path.basename(st['올린파일'][0]))
chk('즉시발송이 집는 이름이다', os.path.basename(st['올린파일'][0]).startswith('회의록정리_'))
chk('올린 파일이 실제로 있다', os.path.isfile(st['올린파일'][0]))

# 현장당 따로
shutil.rmtree(MAIL, ignore_errors=True)
M.NOTE[:] = []
st2 = M.run('260901', '260920', per_site=True, drive=DRIVE, out=OUT)
chk('현장당 따로 = 2개 올린다', len(st2['올린파일']) == 2, str(len(st2['올린파일'])))
chk('파일 이름에 현장명이 들어간다',
    any('조선호텔' in os.path.basename(p) for p in st2['올린파일']),
    str([os.path.basename(p) for p in st2['올린파일']]))
chk('현장당 파일도 즉시발송이 집는다',
    all(os.path.basename(p).startswith('회의록정리_') for p in st2['올린파일']))

# 회의록이 없는 기간
M.NOTE[:] = []
st3 = M.run('250101', '250131', per_site=False, drive=DRIVE, out=OUT)
chk('없는 기간이면 안 죽고 알려 준다', st3['회의수'] == 0 and '회의록이 없습니다' in '\n'.join(M.NOTE))
chk('없으면 드라이브에 안 올린다', '올린파일' not in st3)

# 드라이브가 없을 때
M.NOTE[:] = []
chk('드라이브 없으면 이유를 말한다',
    M.run('260901', '260920', drive=os.path.join(ROOT, '없는곳'), out=OUT) is None
    and '없습니다' in '\n'.join(M.NOTE))

shutil.rmtree(ROOT, ignore_errors=True)
print('\n통과 %d / 실패 %d' % (OK[0], len(NG)))
if NG: print('실패:', NG); sys.exit(1)

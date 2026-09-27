# -*- coding: utf-8 -*-
"""★회의록 한 방에 — v2 에서 고친 것만 따로 본다.
   ① 52번이 없어도 스스로 만들어 넣는가   ② 51번이 드라이브를 못 찾을 때 내가 찾는가"""
from __future__ import print_function
import os, io, sys, json, shutil, tempfile, datetime, importlib.util
import builtins

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = tempfile.mkdtemp(prefix='km한방에2_')
KM = os.path.join(ROOT, '2_KM도구'); TOOLS = os.path.join(KM, '코드', 'km_tools')
DRIVE = os.path.join(ROOT, 'G드라이브'); INC = os.path.join(DRIVE, '회의록', 'incoming')
os.makedirs(TOOLS); os.makedirs(INC)
shutil.copy(os.path.join(SRC, '★회의록_한방에.py'), KM)
# ★ 일부러 t52_mailbuild.py 를 넣지 않는다 — 차장님 PC 와 같은 상황
io.open(os.path.join(TOOLS, 't51_driveup.py'), 'w', encoding='utf-8').write(
    u"def drive_root(): return ''\n"          # ★ 51번이 못 찾는 상황
    u"def run(quiet=False): return {'찾음': 1, '올림': 1}\n")

def meta(site, ymd):
    return {'meta': {'site': site, 'ymd': ymd, 'hm': '10:00', 'person': '홍길동 부장',
                     'company': '일능', 'name': '홍길동', 'rank': '부장'},
            'sec': {'1': {'현장': site, '안건': '안건',
                          '안건목록': [{'title': '항목', 'bullets': ['내용'],
                                      'decision': '결정된 것', 'actions': ['조치']}]},
                    '2': {'할 일': ['- %s | 할 일' % ymd]}}}
T = datetime.date.today().strftime('%y%m%d')
io.open(os.path.join(INC, 'a__meta.json'), 'w', encoding='utf-8').write(
    json.dumps(meta('앵커호텔', T), ensure_ascii=False))

builtins.input = lambda *a, **k: ''
sys.path.insert(0, KM)
spec = importlib.util.spec_from_file_location('한방에2', os.path.join(KM, '★회의록_한방에.py'))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

chk('52번 소스를 품고 있다', 'def build_text' in mod.T52_SRC and len(mod.T52_SRC) > 10000,
    '%d자' % len(mod.T52_SRC))

# ── 드라이브를 스스로 찾는가 : 설정.ini 에 적어 두고 시험 ──
io.open(os.path.join(KM, '설정.ini'), 'w', encoding='utf-8').write(
    u'[드라이브]\n경로 = %s\n' % DRIVE)
mod.NOTE[:] = []
mod.main()
note = '\n'.join(mod.NOTE)

chk('51번이 못 찾아도 내가 찾는다', '찾았습니다' in note or DRIVE in note, note[-400:])
chk('52번을 스스로 만들어 넣었다', os.path.isfile(os.path.join(TOOLS, 't52_mailbuild.py')))
chk('「새로 넣었습니다」 라고 알려 준다', '새로 넣었습니다' in note, note[-400:])
chk('그래서 메일 원고가 만들어졌다',
    os.path.isfile(os.path.join(KM, '_회의록정리', '회의록정리_%s.txt' % T)), note[-400:])
chk('드라이브에도 올렸다',
    os.path.isfile(os.path.join(DRIVE, 'KM_아침메일', '회의록정리_%s.txt' % T)))
chk('끝 인사가 정상으로 나온다', '끝났습니다' in note, note[-300:])

# ── 두 번째로 돌리면 52번이 이미 있으니 「새로 넣었다」 소리가 없어야 ──
for m in ('t52_mailbuild',):
    sys.modules.pop(m, None)
mod.NOTE[:] = []
mod.main()
n2 = '\n'.join(mod.NOTE)
chk('두 번째부터는 조용히 쓴다', '새로 넣었습니다' not in n2, n2[-300:])

# ── 설정.ini 가 없고 아무 데도 없으면 : 안 죽고 물어본다 ──
os.remove(os.path.join(KM, '설정.ini'))
shutil.rmtree(os.path.join(DRIVE, 'KM_아침메일'), ignore_errors=True)
mod.NOTE[:] = []
mod.main()
n3 = '\n'.join(mod.NOTE)
chk('못 찾으면 본 곳을 보여 준다', '본 곳 :' in n3, n3[-500:])
chk('못 찾으면 어떻게 하라고 알려 준다', '주소줄' in n3 or '못 찾았습니다' in n3, n3[-500:])
chk('못 찾아도 안 죽는다', '멈춘 까닭' in n3 or '드라이브' in n3)

# ── 설정.ini 에 BOM 을 붙이지 않는가 (예전 사고) ──
mod._ini_put(DRIVE)
raw = open(mod._ini_path(), 'rb').read()
chk('설정.ini 에 BOM 을 붙이지 않는다', not raw.startswith(b'\xef\xbb\xbf'), repr(raw[:6]))
chk('설정.ini 를 다시 읽을 수 있다', mod._ini_get() == DRIVE, mod._ini_get())

# ── 기존 절을 지우지 않는가 ──
io.open(mod._ini_path(), 'w', encoding='utf-8').write(u'[경로]\nout = C:\\어딘가\n\n[회의]\n받는함 = D:\\받는함\n')
mod._ini_put(DRIVE)
txt = io.open(mod._ini_path(), encoding='utf-8').read()
chk('설정.ini 의 다른 절을 지우지 않는다',
    '[경로]' in txt and '[회의]' in txt and '[드라이브]' in txt, txt[:200])

shutil.rmtree(ROOT, ignore_errors=True)
print('\n통과 %d / 실패 %d' % (OK[0], len(NG)))
if NG: print('실패:', NG); sys.exit(1)

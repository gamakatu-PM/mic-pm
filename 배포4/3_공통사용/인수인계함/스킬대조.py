# -*- coding: utf-8 -*-
"""스킬 대조 - 새 창이 채팅 시작 때 가장 먼저 돌린다 (km-00-first-read 31번).
저장대기(3_스킬_저장대기\*.skill = 최신)와 프로님이 실제로 저장하신 설치본을 비교해
「아직 저장 안 된 스킬」 을 먼저 말씀드린다. 프로님이 잊으셔도 새 창이 알려 드리는 것이 목적.
  python3 스킬대조.py            -> 표 출력 + 0 (전부 같음) / 1 (저장 안 된 것 있음)
설치본 위치는 환경마다 다르다 : ~/.claude/skills/synced/*/ 아래 또는 ~/.claude/skills/ 아래."""
import os, sys, re, glob, zipfile, io, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, '3_스킬_저장대기')

def installed_dirs():
    home = os.path.expanduser('~')
    out = []
    for pat in (os.path.join(home, '.claude', 'skills', 'synced', '*'), os.path.join(home, '.claude', 'skills')):
        out += [p for p in glob.glob(pat) if os.path.isdir(p)]
    return out

def find_installed(name):
    for d in installed_dirs():
        p = os.path.join(d, name, 'SKILL.md')
        if os.path.exists(p):
            return p
    return None

def ver(t):
    m = re.search(r'\(v(\d+(?:\.\d+)?),\s*(\d{4}-\d{2}-\d{2})\)', t) or re.search(r'\bv(\d+(?:\.\d+)?)\s*\((\d{4}-\d{2}-\d{2})\)', t)
    return ('v%s %s' % (m.group(1), m.group(2))) if m else '?'

def main():
    rows, bad = [], 0
    for f in sorted(glob.glob(os.path.join(STAGE, '*.skill'))):
        name = os.path.basename(f)[:-6]
        try:
            with zipfile.ZipFile(f) as z:
                staged = z.read('%s/SKILL.md' % name).decode('utf-8')
        except Exception as e:
            rows.append((name, '?', '?', '읽기 실패 %s' % e)); bad += 1; continue
        ip = find_installed(name)
        if not ip:
            rows.append((name, '없음', ver(staged), '★ 아직 저장 안 됨 (새 스킬)')); bad += 1; continue
        inst = io.open(ip, encoding='utf-8').read()
        same = hashlib.md5(inst.encode('utf-8')).hexdigest() == hashlib.md5(staged.encode('utf-8')).hexdigest()
        rows.append((name, ver(inst), ver(staged), '같음' if same else '★ 저장 안 됨 (설치본이 옛 판)'))
        bad += (not same)
    print('%-26s %-18s %-18s %s' % ('스킬', '설치본(프로님 저장)', '저장대기(최신)', '판정'))
    for r in rows:
        print('%-26s %-18s %-18s %s' % r)
    print('')
    if bad:
        print('★ 저장 안 된 스킬 %d개. 프로님께 먼저 말씀드리고, 파일을 다시 보내 드린다 (3_스킬_저장대기\\ 의 .skill).' % bad)
    else:
        print('전부 저장되어 있습니다.')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())

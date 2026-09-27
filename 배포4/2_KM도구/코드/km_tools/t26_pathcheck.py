# -*- coding: utf-8 -*-
"""26. 경로 검사 - 회의록 프로그램(시작.bat·km_*.py)이 어느 폴더 이름을 쓰는지 전부 찾아낸다.
폴더 이름에 번호를 붙여도 되는지, 붙이면 무엇이 깨지는지 판정한다."""
import os, re, sys
from common import *

# 이름을 바꿀지 검토 중인 폴더들
WATCH = ['plaud', '_원틀', '_코드', '_현장비서', 'Claude outputs',
         '26년', '1.현장', '_도구결과', '!!클로드가 저장하는 폴더']
ABS = re.compile(r'[A-Za-z]:\\[^\'"\n]+|%USERPROFILE%[^\'"\n]*|%~dp0[^\'"\n]*')

def scan_file(path):
    """(절대경로들, 걸린 폴더이름들, 상대경로 사용여부)"""
    t = read_text(path)
    if not t:
        return [], [], False
    abses = [m.group(0)[:120] for m in ABS.finditer(t)]
    hits = sorted({w for w in WATCH if w in t})
    rel = ('%~dp0' in t) or ('__file__' in t) or ('dirname' in t)
    return abses, hits, rel

def run():
    title('26. 경로 검사 (이름 바꿔도 되나)')
    roots = []
    b = cfg('biseo')
    if os.path.isdir(b):
        roots.append(('회의록 프로그램', b))
    c = os.path.join(cfg('base'), '_코드')
    if not os.path.isdir(c):
        for d in ('6_코드보관', '코드'):
            p = os.path.join(cfg('base'), d)
            if os.path.isdir(p):
                c = p; break
    if os.path.isdir(c):
        roots.append(('코드 보관소', c))
    if not roots:
        print('회의록 프로그램 폴더를 못 찾았습니다.')
        print('  찾은 곳 : %s' % b)
        return

    rows, folder_used = [], {}
    nfile = 0
    for label, root in roots:
        for p in walk_files(root, {'.py', '.bat', '.cmd', '.txt'}):
            nfile += 1
            abses, hits, rel = scan_file(p)
            for h in hits:
                folder_used.setdefault(h, set()).add(os.path.basename(p))
            if abses or hits:
                rows.append([label, os.path.basename(p),
                             ' / '.join(hits), '있음' if rel else '',
                             ' | '.join(abses[:3])[:150], p])
    print('훑은 파일 %s개' % won(nfile))
    print('')
    print('%-22s %-30s %s' % ('폴더 이름', '이 이름을 쓰는 파일', '판정'))
    print('-' * 92)
    safe, risky = [], []
    for name in WATCH:
        users = sorted(folder_used.get(name, []))
        if not users:
            print('%-22s %-30s 아무도 안 씀 -> 이름 바꿔도 안전' % (name, '-'))
            safe.append(name)
        else:
            u = ', '.join(users[:3]) + (' 외 %d개' % (len(users) - 3) if len(users) > 3 else '')
            print('%-22s %-30s [주의] 이 파일들을 고쳐야 함' % (name, u[:30]))
            risky.append((name, users))
    print('')
    print('[요약]')
    print('  이름 바꿔도 되는 폴더 : %s' % (', '.join(safe) if safe else '없음'))
    for name, users in risky:
        print('  %s 을 바꾸려면 -> %s 안의 그 글자를 같이 고쳐야 합니다' % (name, ', '.join(users[:5])))
    o = os.path.join(outdir('경로검사'), '경로검사_%s.csv' % ymd6())
    write_csv(o, rows, ['구분', '파일', '걸린 폴더이름', '상대경로', '절대경로(앞부분)', '전체경로'])
    log('경로검사', '%d파일 / 위험 %d' % (nfile, len(risky)))
    print('')
    print('파일 : %s' % o)
    print('* 이 화면을 그대로 클로드에게 보여주시면 무엇을 고쳐야 하는지 알려드립니다.')

if __name__ == '__main__':
    run(); pause()

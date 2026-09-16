# -*- coding: utf-8 -*-
"""25. PLAUD 미처리 감지 - 넣은 회의 수와 만들어진 회의록 수를 대조해 누락을 잡는다.
정답 기준 : 원본 메모장의 '[1부' 줄 수 = 만들어진 회의 폴더 수 (km-30 규칙)."""
import os, re
from common import *

MARK = re.compile(r'【\s*1부|\[\s*1부')

def count_parts(root):
    n, files = 0, 0
    for p in walk_files(root, {'.txt', '.md'}):
        files += 1
        n += len(MARK.findall(read_text(p)))
    return n, files

def count_meetings(root):
    """plaud\\26년 아래 회의 폴더(원문.txt 를 가진 폴더) 수"""
    n = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith('_삭제요망')]
        if any(f.startswith('원문') for f in fn):
            n += 1
    return n

def run():
    title('25. PLAUD 미처리 감지')
    biseo, plaud = cfg('biseo'), sites_root()
    inbox = os.path.join(biseo, '1.여기에_v10결과_넣기')
    done = os.path.join(biseo, '3.처리완료')
    rows = []
    for name, path in (('대기함(1.여기에 넣기)', inbox), ('처리완료(3.처리완료)', done)):
        if os.path.isdir(path):
            n, f = count_parts(path)
            print('%-24s 파일 %3s개 / 회의 %3s건' % (name, won(f), won(n)))
            rows.append([name, f, n])
        else:
            print('%-24s [폴더 없음] %s' % (name, path))
            rows.append([name, 0, 0])
    made = count_meetings(plaud) if os.path.isdir(plaud) else 0
    print('%-24s 회의록 폴더 %s개' % ('산출(1.현장)', won(made)))
    waiting = rows[0][2]
    print('-' * 56)
    if waiting:
        print('[경보] 대기함에 아직 처리 안 된 회의가 %s건 있습니다. 시작.bat 을 돌리십시오.' % won(waiting))
    else:
        print('대기함은 비어 있습니다.')
    print('* 처리완료 회의 %s건 대비 회의록 폴더 %s개' % (won(rows[1][2]), won(made)))
    if rows[1][2] and made < rows[1][2]:
        print('[경보] 회의록이 %s건 모자랍니다. 누락 확인이 필요합니다.' % won(rows[1][2] - made))
    o = os.path.join(outdir('PLAUD감지'), 'PLAUD감지_%s.csv' % ymd6())
    write_csv(o, rows + [['산출 회의록 폴더', made, '']], ['구분', '파일수', '회의건수'])
    print('파일 : %s' % o)

if __name__ == '__main__':
    run(); pause()

# -*- coding: utf-8 -*-
"""15. 부서 전달 메일 초안 - 회의록의 '타부서 전달 사항'을 부서별 메일 초안으로 쪼갠다.
문장은 회의록에서 그대로 가져옵니다. 없는 말을 지어내지 않습니다. 발송은 프로님이 하십니다."""
import os, re
from common import *

DEPT = [('설계팀', ('설계', '도면', '평면', '배치')),
        ('개발팀', ('개발', '프로그램', '펌웨어', '연동', 'PMS', '수정')),
        ('구매팀', ('구매', '자재', '발주', '선구매', '차단기')),
        ('제작팀', ('제작', '외함', '속판', '기구물', '조립')),
        ('시공팀', ('시공', '설치', '결선', '시운전', '현장')),
        ('영업/대외', ('견적', '계약', '증감', '발주처', '감리'))]
PART2 = re.compile(r'【\s*2부[^\n]*\n(.*?)(?=【|\Z)', re.S)

def split_lines(text):
    out = []
    for m in PART2.finditer(text):
        for ln in m.group(1).splitlines():
            s = ln.strip(' -*.\t')
            if len(s) >= 6:
                out.append(s)
    return out

def dept_of(line):
    hits = [d for d, keys in DEPT if any(k in line for k in keys)]
    return hits or ['확인필요']

def run():
    title('15. 부서 전달 메일 초안')
    root = sites_root()
    if not need(root, 'plaud\\26년 폴더를 설정.ini 에 넣어주십시오'):
        return
    days = int(ask('최근 며칠분? (기본 7) > ', '7') or 7)
    import datetime
    cut = datetime.datetime.now().timestamp() - days * 86400
    bag = {}
    for p in walk_files(root, {'.txt', '.md'}):
        if os.path.getmtime(p) < cut:
            continue
        rel = os.path.relpath(p, root)
        site = rel.split(os.sep)[0]
        for ln in split_lines(read_text(p)):
            for d in dept_of(ln):
                bag.setdefault(d, []).append((site, ln))
    if not bag:
        print('최근 %d일 회의록에서 타부서 전달 사항을 못 찾았습니다.' % days); return
    od = outdir('부서메일')
    made = []
    for dept, items in bag.items():
        lines = ['제목: [한국마이크로닉] %s 전달 사항 (%s)' % (dept, today().isoformat()), '',
                 '%s 담당자님께,' % dept, '',
                 '아래와 같이 현장 협의 내용을 전달드립니다. 확인 부탁드립니다.', '']
        cur = None
        for site, ln in items:
            if site != cur:
                lines.append('[%s]' % site); cur = site
            lines.append('  - %s' % ln)
        lines += ['', '※ 이 초안은 회의록 원문에서 그대로 옮긴 것입니다. 보내시기 전에 확인해 주십시오.',
                  '※ 작업 착수가 필요한 건은 작업의뢰서(MB-004)를 별도로 발행하셔야 합니다.', '',
                  '한국마이크로닉(주) 배성윤 드림']
        f = os.path.join(od, '%s_전달초안_%s.txt' % (safe_name(dept), ymd6()))
        import io as _io
        _io.open(f, 'w', encoding='utf-8').write('\n'.join(lines))
        made.append((dept, len(items), f))
    print('%-12s %6s  파일' % ('부서', '건수'))
    print('-' * 70)
    for d, n, f in made:
        print('%-12s %6s  %s' % (d, won(n), os.path.basename(f)))
    log('부서메일', '%d부서' % len(made))
    print('')
    print('저장 폴더 : %s' % od)
    print('* 발송은 하지 않았습니다. 초안만 만들었습니다.')

if __name__ == '__main__':
    run(); pause()

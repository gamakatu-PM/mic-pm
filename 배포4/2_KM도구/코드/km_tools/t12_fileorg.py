# -*- coding: utf-8 -*-
"""16. 파일 정리 - 어느 현장 파일인지 분류해 '옮길 계획'만 낸다. 실제 이동/삭제는 하지 않는다.
삭제는 사람이 한다 (km-30 규칙). 이 도구는 계획 CSV 와 _삭제요망 후보만 뽑는다."""
import os, re, datetime
from common import *

KIND = [('견적', ('견적', 'Rev', '내역')), ('작업의뢰서', ('작업의뢰', 'MB-004')),
        ('도면', ('도면', '배선도', '계통도', '평면도', '.dwg', '.dxf')),
        ('사진', ('.jpg', '.jpeg', '.png')), ('회의록', ('회의', '협의', '통화')),
        ('시방서', ('시방', '사양')), ('계약', ('계약', '계산서', '세금'))]

def kind_of(name):
    low = name.lower()
    for k, keys in KIND:
        if any(x.lower() in low for x in keys):
            return k
    return '기타'

def sites_from(root):
    try:
        return sorted([d for d in os.listdir(root)
                       if os.path.isdir(os.path.join(root, d)) and not d.startswith(('_', '.'))])
    except Exception:
        return []

def run():
    title('16. 파일 정리 (계획만, 실제로 옮기지 않습니다)')
    src = ask('정리할 폴더 경로 > ')
    if not os.path.isdir(src):
        print('폴더를 찾지 못했습니다.'); return
    sites = sites_from(sites_root())
    print('아는 현장 %s개' % won(len(sites)))
    rows, dup = [], {}
    for p in walk_files(src):
        b = os.path.basename(p)
        site = next((s for s in sites if s and s in b), '_현장미정')
        k = kind_of(b)
        d = datetime.date.fromtimestamp(os.path.getmtime(p))
        newname = '%s_%s' % (ymd6(d), safe_name(b))
        plan = os.path.join(site, k, newname)
        rows.append([b, site, k, plan, p])
        key = (site, k, re.sub(r'[\d]', '', b))
        dup.setdefault(key, []).append(p)
    print('파일 %s개 분류 완료' % won(len(rows)))
    o = os.path.join(outdir('파일정리'), '정리계획_%s.csv' % ymd6())
    write_csv(o, rows, ['지금 이름', '현장', '종류', '옮길 위치(계획)', '원래 경로'])
    print('계획 파일 : %s' % o)
    cand = [v for v in dup.values() if len(v) >= 4]
    if cand:
        print('')
        print('[버전 4개 이상] 문서명 폴더로 몰아넣을 후보 %s묶음' % won(len(cand)))
        for v in cand[:10]:
            print('  %s 외 %d개' % (os.path.basename(v[0]), len(v) - 1))
    print('')
    print('* 이 도구는 읽기만 합니다. 옮기거나 지우지 않았습니다.')

if __name__ == '__main__':
    run(); pause()

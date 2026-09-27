# -*- coding: utf-8 -*-
"""22. 시방서 현장 갈아끼우기 - 특기시방서 원틀(hwpx/docx)에서 현장명/객실수/발주처만 바꾼다."""
import os
from common import *

def run():
    title('22. 시방서 현장 갈아끼우기')
    tpl = find_template('시방')
    if not tpl:
        no_template('특기시방서 원틀(hwpx/docx)', '시방')
        return
    print('쓸 원틀 : %s' % os.path.basename(tpl))
    site = ask('현장명 > ', '현장미정')
    rooms = ask('객실수 (모르면 엔터) > ')
    owner = ask('발주처 (모르면 엔터) > ')
    old = ask('원틀에 들어있는 옛 현장명 (자리표시 쓰면 엔터) > ')
    mp = {'{{현장}}': site, '{{현장명}}': site, '{{객실수}}': rooms, '{{발주처}}': owner,
          '{{날짜}}': today().isoformat()}
    if old:
        mp[old] = site
    mp = {k: v for k, v in mp.items() if v}
    ext = os.path.splitext(tpl)[1]
    out = os.path.join(outdir('시방서'), '%s_특기시방서_%s%s' % (safe_name(site), ymd6(), ext))
    n = zip_replace(tpl, out, mp)
    print('바꾼 자리 %s곳' % won(n))
    if n == 0:
        print('[주의] 바뀐 곳이 없습니다. hwp(구형)는 zip 이 아니라 못 바꿉니다 - hwpx 로 저장해 주십시오.')
    print('파일 : %s' % out)
    log('시방서', '%s %d곳' % (site, n))

if __name__ == '__main__':
    run(); pause()

# -*- coding: utf-8 -*-
"""21. 자재사양서 - 회사 표준 pptx 원틀을 복사해 현장명/품목만 갈아끼운다.
원틀에 {{현장}} {{날짜}} 같은 자리표시가 있으면 그것을 바꿉니다. 없으면 기존 현장명을 찾아 바꿉니다."""
import os
from common import *

def run():
    title('21. 자재사양서 (원틀 값 채우기)')
    tpl = find_template('자재')
    if not tpl:
        no_template('자재사양서 원틀(pptx)', '자재')
        return
    print('쓸 원틀 : %s' % os.path.basename(tpl))
    site = ask('현장명 > ', '현장미정')
    old = ask('원틀에 들어있는 옛 현장명 (자리표시 쓰면 엔터) > ')
    mp = {'{{현장}}': site, '{{현장명}}': site, '{{날짜}}': today().isoformat()}
    if old:
        mp[old] = site
    ext = os.path.splitext(tpl)[1]
    out = os.path.join(outdir('자재사양서'), '%s_자재사양서_%s%s' % (safe_name(site), ymd6(), ext))
    n = zip_replace(tpl, out, mp)
    print('바꾼 자리 %s곳' % won(n))
    if n == 0:
        print('[주의] 바뀐 곳이 없습니다. 옛 현장명을 정확히 적어주시거나 원틀에 {{현장}} 을 넣어주십시오.')
    print('파일 : %s' % out)
    print('* 서식(틀)은 건드리지 않았습니다. 글자만 바꿨습니다.')
    log('자재사양서', '%s %d곳' % (site, n))

if __name__ == '__main__':
    run(); pause()

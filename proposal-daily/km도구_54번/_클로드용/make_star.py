# -*- coding: utf-8 -*-
"""★제안서_PPT.py 를 만든다. km_tools 의 54번 파일 4개 + 제안서_내용 json 을 통째로 품게 한다.
   python make_star.py [나갈곳]"""
import os, io, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
KT = os.path.join(HERE, '..', '코드', 'km_tools')
FILES = ['t54_deck.py', 'deck_core.py', 'site_index.py', 'errata_apply.py']
src = {f: io.open(os.path.join(KT, f), encoding='utf-8').read() for f in FILES}
specs = {os.path.basename(p): io.open(p, encoding='utf-8').read()
         for p in sorted(glob.glob(os.path.join(KT, '제안서_내용', '*.json')))}
def lit(d):
    return '{\n' + ''.join('    %r: %r,\n' % (k, v) for k, v in d.items()) + '}'
t = io.open(os.path.join(HERE, 'star_template.py'), encoding='utf-8').read()
t = t.replace('__SRC__', lit(src), 1).replace('__SPECS__', lit(specs), 1)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '★제안서_PPT.py')
io.open(out, 'w', encoding='utf-8', newline='\n').write(t)
compile(t, out, 'exec')
print(out, len(t), 'bytes', len(src), 'files', len(specs), 'specs')

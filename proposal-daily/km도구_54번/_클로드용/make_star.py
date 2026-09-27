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
# 전에 내보낸 제안서 json 의 지문 - PC 파일이 이것과 같으면 프로님이 안 고친 것이라 새 판으로 바꿔도 된다
import hashlib, subprocess
old = set()
try:
    SD = os.path.normpath(os.path.join(KT, '제안서_내용'))
    top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=SD).decode().strip()
    rel = os.path.relpath(SD, top).replace(os.sep, '/')
    for r in subprocess.check_output(['git', 'log', '--format=%H', '--', rel], cwd=top).decode().split():
        ls = subprocess.check_output(['git', '-c', 'core.quotepath=off', 'ls-tree', '--name-only', r, rel + '/'], cwd=top).decode('utf-8')
        for n in ls.split('\n'):
            if n.endswith('.json'):
                blob = subprocess.check_output(['git', 'show', '%s:%s' % (r, n)], cwd=top)
                old.add(hashlib.sha1(blob.replace(b'\r\n', b'\n')).hexdigest())
except Exception as e:
    print('지문 모으기 실패 (json 은 없을 때만 넣음):', e)
old -= {hashlib.sha1(v.encode('utf-8')).hexdigest() for v in specs.values()}
t = t.replace('__SRC__', lit(src), 1).replace('__SPECS__', lit(specs), 1).replace('__OLDSPEC__', repr(sorted(old)), 1)
print('old spec hashes', len(old))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '★제안서_PPT.py')
io.open(out, 'w', encoding='utf-8', newline='\n').write(t)
compile(t, out, 'exec')
print(out, len(t), 'bytes', len(src), 'files', len(specs), 'specs')

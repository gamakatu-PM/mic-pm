# -*- coding: utf-8 -*-
"""17. 회의록 전문 검색기 - 전 현장 회의록에서 한 단어가 나온 곳을 전부 찾는다."""
import os, sys, re
from common import *

EXTS = {'.txt', '.md', '.docx'}

def docx_text(path):
    try:
        import zipfile, xml.etree.ElementTree as ET
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml').decode('utf-8', 'ignore')
        xml = re.sub(r'</w:p>', '\n', xml)
        return re.sub(r'<[^>]+>', '', xml)
    except Exception:
        return ''

def load(path):
    return docx_text(path) if path.lower().endswith('.docx') else read_text(path)

def run(word=None):
    title('17. 회의록 검색기')
    root = cfg('plaud')
    if not need(root, 'plaud\\26년 폴더 경로를 설정.ini 에 넣어주십시오'):
        return
    word = word or ask('찾을 말 (예: 방화문 타공) > ')
    if not word:
        print('찾을 말이 없습니다.'); return
    keys = [k for k in word.split() if k]
    hits, files = [], 0
    for p in walk_files(root, EXTS):
        files += 1
        t = load(p)
        if not t:
            continue
        for ln, line in enumerate(t.splitlines(), 1):
            if all(k in line for k in keys):
                rel = os.path.relpath(p, root)
                site = rel.split(os.sep)[0]
                hits.append([site, os.path.basename(p), ln, line.strip()[:200], p])
    print('')
    print('훑은 파일 %s개 / 찾은 줄 %s개' % (won(files), won(len(hits))))
    print('-' * 56)
    for h in hits[:40]:
        print('[%s] %s' % (h[0], h[3]))
    if len(hits) > 40:
        print('... 외 %s줄 (CSV 참조)' % won(len(hits) - 40))
    if hits:
        out = os.path.join(outdir('회의록검색'), '검색_%s_%s.csv' % (safe_name(word, 20), ymd6()))
        write_csv(out, hits, ['현장', '파일', '줄', '내용', '전체경로'])
        print('')
        print('결과 파일 : %s' % out)

if __name__ == '__main__':
    run(' '.join(sys.argv[1:]) or None)
    pause()

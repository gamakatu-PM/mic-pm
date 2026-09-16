# -*- coding: utf-8 -*-
"""98. 업데이트 - 받으신 zip 을 도구가 스스로 적용한다.
프로님은 zip 을 받기만 하시면 됩니다. 압축 풀기·복사·덮어쓰기는 이 도구가 합니다."""
import os, sys, zipfile, shutil, datetime, glob
from common import *

def search_dirs():
    """zip 을 찾아볼 곳들"""
    home = os.path.expanduser('~')
    out = [os.path.join(home, 'Downloads'),
           os.path.join(home, 'Downloads', 'KM'),
           os.path.join(home, 'Desktop'),
           os.path.join(home, 'OneDrive', 'Desktop'),
           os.path.join(home, 'OneDrive', '바탕 화면'),
           os.path.join(home, '바탕 화면'),
           cfg('base')]
    seen, res = set(), []
    for d in out:
        if d and os.path.isdir(d) and d not in seen:
            seen.add(d); res.append(d)
    return res

def find_zips():
    found = []
    for d in search_dirs():
        for p in glob.glob(os.path.join(d, '*.zip')):
            b = os.path.basename(p)
            if b.upper().startswith('KM') or 'km_tools' in b.lower() or '도구' in b:
                found.append((os.path.getmtime(p), p))
    found.sort(reverse=True)
    return [p for _, p in found]

def tools_in_zip(z):
    """zip 안에서 km_tools 폴더의 위치(접두어)를 찾는다"""
    for n in z.namelist():
        n2 = n.replace('\\', '/')
        i = n2.find('km_tools/')
        if i >= 0:
            return n2[:i + len('km_tools/')]
    return None

def apply(zip_path):
    dest = HERE                      # 지금 돌고 있는 km_tools 폴더
    parent = os.path.dirname(dest)   # ...\코드
    with zipfile.ZipFile(zip_path) as z:
        pref = tools_in_zip(z)
        if not pref:
            return None, 'zip 안에 km_tools 폴더가 없습니다. 도구 갱신본이 아닌 것 같습니다.'
        names = [n for n in z.namelist()
                 if n.replace('\\', '/').startswith(pref) and not n.endswith('/')]
        if not names:
            return None, 'zip 안이 비어 있습니다.'
        # 1) 지금 것을 백업
        stamp = datetime.datetime.now().strftime('%y%m%d_%H%M')
        backup = os.path.join(parent, '_이전판_%s' % stamp)
        shutil.copytree(dest, backup)
        # 2) 새 파일 덮어쓰기
        n = 0
        for name in names:
            rel = name.replace('\\', '/')[len(pref):]
            if not rel or rel.startswith('__pycache__'):
                continue
            target = os.path.join(dest, *rel.split('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(name) as src, open(target, 'wb') as fp:
                shutil.copyfileobj(src, fp)
            n += 1
    return (n, backup), None

def run():
    title('98. 업데이트 (받으신 zip 을 그대로 적용)')
    print('지금 판 : %s (%s)' % (VERSION, VERSION_DATE))
    print('설치 위치 : %s' % HERE)
    print('')
    zips = find_zips()
    if not zips:
        print('zip 을 못 찾았습니다. 아래 폴더를 훑었습니다 :')
        for d in search_dirs():
            print('   %s' % d)
        print('')
        print('-> 받으신 zip 을 「다운로드」 폴더나 바탕화면에 두고 다시 눌러주십시오.')
        return
    print('찾은 zip (최근 순)')
    for i, p in enumerate(zips[:8], 1):
        t = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d %H:%M')
        print(' %2d. %-44s %s' % (i, os.path.basename(p)[:44], t))
    s = ask('\n번호 (엔터=1번) > ', '1')
    try:
        pick = zips[int(s) - 1]
    except Exception:
        print('번호가 잘못됐습니다.'); return
    print('')
    print('적용할 파일 : %s' % os.path.basename(pick))
    if not ask('진행할까요? (y=엔터 / n) > ', 'y').lower().startswith('y'):
        print('취소했습니다.'); return
    res, err = apply(pick)
    if err:
        print('[실패] %s' % err); return
    n, backup = res
    print('')
    print('파일 %s개를 갈아끼웠습니다.' % won(n))
    print('이전 판은 여기에 보관했습니다 : %s' % backup)
    print('')
    print('=' * 56)
    print(' 끝났습니다. 이 창을 닫고 시작.py 를 다시 눌러주십시오.')
    print(' 메뉴 맨 위 판 번호가 바뀌어 있으면 성공입니다.')
    print('=' * 56)
    log('업데이트', '%s / %d파일' % (os.path.basename(pick), n))

if __name__ == '__main__':
    run(); pause()

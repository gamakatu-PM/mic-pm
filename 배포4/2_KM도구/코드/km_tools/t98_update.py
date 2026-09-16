# -*- coding: utf-8 -*-
"""98. 업데이트 - 받으신 zip 을 도구가 스스로 적용한다.
프로님은 zip 을 받기만 하시면 됩니다. 압축 풀기·복사·덮어쓰기는 이 도구가 합니다."""
import os, sys, re, zipfile, shutil, datetime, glob
from common import *

RAW = 'https://raw.githubusercontent.com/gamakatu-PM/mic-pm/claude/cowork-suggestions-bohllt/'
VER_FILE = '배포4/2_KM도구/코드/km_tools/common.py'
LATEST = 'KM_latest.zip'

def _raw_url(rel):
    import urllib.parse
    base = RAW
    try:
        import configparser
        c = configparser.ConfigParser(); c.read(INI, encoding='utf-8')
        if c.has_option('갱신', 'url') and c.get('갱신', 'url').strip():
            base = c.get('갱신', 'url').strip().rstrip('/') + '/'
    except Exception:
        pass
    return base + urllib.parse.quote(rel)

def remote_version(timeout=8):
    """GitHub 정본의 판 번호. 인터넷이 막히면 None"""
    try:
        import urllib.request
        with urllib.request.urlopen(_raw_url(VER_FILE), timeout=timeout) as r:
            t = r.read(4000).decode('utf-8', 'ignore')
        m = re.search(r"VERSION\s*=\s*'v(\d+)'", t)
        return int(m.group(1)) if m else None
    except Exception:
        return None

def fetch_latest(quiet=True):
    """정본이 지금 판보다 새면 KM_latest.zip 을 다운로드\KM 에 받아 그 경로를 준다. 아니면 None"""
    cur = int(re.sub(r'\D', '', VERSION) or 0)
    rv = remote_version()
    if not rv or rv <= cur:
        return None
    try:
        import urllib.request
        home = os.path.expanduser('~')
        d = os.path.join(home, 'Downloads', 'KM'); os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, 'KM_v%d_받아두고_98번.zip' % rv)
        if os.path.exists(dst) and zip_version(dst) == rv:
            return dst
        if not quiet:
            print('정본에 새 판 v%d 이 있습니다. 받는 중...' % rv)
        urllib.request.urlretrieve(_raw_url(LATEST), dst)
        with zipfile.ZipFile(dst) as z:
            if not tools_in_zip(z):
                os.remove(dst); return None
        return dst
    except Exception:
        return None

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

def zip_version(path):
    m = re.search(r'_v(\d+)_', os.path.basename(path))
    return int(m.group(1)) if m else 0

def newer_zip():
    """지금 판보다 번호가 큰 zip 이 다운로드/바탕화면에 있으면 그 경로"""
    cur = int(re.sub(r'\D', '', VERSION) or 0)
    best = None
    for z in find_zips():
        v = zip_version(z)
        if v > cur and (best is None or v > zip_version(best)):
            best = z
    return best

def find_prefix(z, folder):
    """zip 안에서 어떤 폴더의 위치(접두어)를 찾는다"""
    key = folder + '/'
    for n in z.namelist():
        n2 = n.replace('\\', '/')
        i = n2.find(key)
        if i >= 0:
            return n2[:i + len(key)]
    return None

def tools_in_zip(z):
    return find_prefix(z, 'km_tools')

def extract_to(z, pref, dest, skip=()):
    """zip 의 pref 아래를 dest 에 덮어쓴다. skip 에 든 폴더는 건너뛴다."""
    n = 0
    for name in z.namelist():
        n2 = name.replace('\\', '/')
        if not n2.startswith(pref) or n2.endswith('/'):
            continue
        rel = n2[len(pref):]
        if not rel or rel.startswith('__pycache__'):
            continue
        if any(rel.startswith(s2 + '/') for s2 in skip):
            continue
        target = os.path.join(dest, *rel.split('/'))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with z.open(name) as src, open(target, 'wb') as fp:
            shutil.copyfileobj(src, fp)
        n += 1
    return n

def apply(zip_path):
    dest = HERE                      # 지금 돌고 있는 km_tools 폴더
    parent = os.path.dirname(dest)   # ...\코드
    with zipfile.ZipFile(zip_path) as z:
        pref = tools_in_zip(z)
        if not pref:
            return None, 'zip 안에 km_tools 폴더가 없습니다. 도구 갱신본이 아닌 것 같습니다.'
        if not any(n.replace('\\', '/').startswith(pref) and not n.endswith('/')
                   for n in z.namelist()):
            return None, 'zip 안이 비어 있습니다.'
        # 1) 지금 것을 백업
        stamp = datetime.datetime.now().strftime('%y%m%d_%H%M')
        backup = os.path.join(parent, '_이전판_%s' % stamp)
        shutil.copytree(dest, backup)
        # 2) 코드 덮어쓰기
        n = extract_to(z, pref, dest)
        extra = []
        # 3) 인수인계함(결정대기 엑셀 등)도 있으면 제자리에 갱신. 프로님의 「버전」 폴더는 손대지 않는다
        hp = find_prefix(z, '인수인계함')
        if hp:
            hd = cfg('handover')
            if os.path.isdir(hd):
                k = extract_to(z, hp, hd, skip=('버전',))
                if k:
                    extra.append('인수인계함 %d개' % k)
        # 4) 지도와 안내문
        for fname, where in (('0_여기부터_보세요.html', cfg('base')),
                             ('사용법.txt', os.path.dirname(parent))):
            for name in z.namelist():
                if name.replace('\\', '/').endswith(fname) and os.path.isdir(where):
                    with z.open(name) as src, open(os.path.join(where, fname), 'wb') as fp:
                        shutil.copyfileobj(src, fp)
                    extra.append(fname)
                    break
    return (n, backup, extra), None

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
    n, backup, extra = res
    print('')
    print('도구 %s개를 갈아끼웠습니다.' % won(n))
    for e in extra:
        print('  + %s 도 갱신했습니다.' % e)
    print('이전 판은 여기에 보관했습니다 : %s' % backup)
    print('')
    print('=' * 56)
    print(' 끝났습니다. 이 창을 닫고 시작.py 를 다시 눌러주십시오.')
    print(' 메뉴 맨 위 판 번호가 바뀌어 있으면 성공입니다.')
    print('=' * 56)
    log('업데이트', '%s / %d파일' % (os.path.basename(pick), n))

if __name__ == '__main__':
    run(); pause()

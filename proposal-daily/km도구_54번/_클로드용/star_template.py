# -*- coding: utf-8 -*-
r"""★제안서 PPT — 이 파일만 더블클릭하십시오. (2026-09-27)

누르면 번호 세 개가 나옵니다.

    1) 제안서 PPT 만들기      54번 : 미리 써 둔 제안서 25건 중 골라 회사 서식 pptx 로
                              (27번 도면수량을 먼저 돌려 두면 그 현장 물량표가 자동으로 들어감)
    2) 점유율 80% 로 고치기   회사 제안서 pptx 의 5성급 점유율을 「해외스펙 제외 80% 이상」 으로
    3) 현장별 한 곳에 보기    흩어진 결과(산출·견적·실행·단가장·제안서·회의록)를 현장별 한 장으로

AI 사용량 0. 인터넷도 쓰지 않습니다.

왜 시작.py 메뉴가 아니라 이 파일인가
    메뉴 번호는 목록 순서로 매겨져 있어(49번 = 51번 도구) 54번을 넣으면 번호가 어긋납니다.
    또 새 zip 이 자동 적용되면 도구 폴더의 파일이 옛 판으로 덮일 수 있습니다.
    이 파일은 2_KM도구 폴더 바로 아래에 있어 zip 이 건드리지 않고,
    누를 때마다 km_tools 에 54번 파일이 빠졌거나 옛 판이면 스스로 새 판을 넣습니다.
    33번 현황판에 「⑧ 현장별 한 곳에」 칸이 빠져 있으면 그것도 다시 넣습니다(원본은 .bak_54 로 남김).

제안서 내용(제안서_내용\*.json)은 없을 때만 넣습니다. 고쳐 쓰신 것은 덮지 않습니다.
"""
import os, sys, io, re, shutil, datetime, traceback

PKG = 6          # 이 파일이 품은 54번 판. 파일 둘째 줄 「# 54판 v6」 과 맞춘다
SRC = __SRC__
SPECS = __SPECS__

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = []


def say(s=''):
    print(s)
    NOTE.append(s)


def find_tools():
    """km_tools 폴더를 스스로 찾는다."""
    cands = [os.path.join(HERE, '코드', 'km_tools'),
             os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
             os.path.join(HERE, 'km_tools')]
    for p in cands:
        if os.path.isfile(os.path.join(p, 'common.py')):
            return p
    for root, _dirs, files in os.walk(HERE):
        if 'common.py' in files and 'menu.py' in files and root.count(os.sep) - HERE.count(os.sep) <= 3:
            return root
    return ''


def _ver(text):
    m = re.search(r'#\s*54판\s*v(\d+)', text[:400])
    return int(m.group(1)) if m else 0


def install(tools):
    """54번 파일을 넣는다. 없거나 옛 판일 때만. 더 새 판이 있으면 그대로 둔다."""
    did = []
    for name, text in SRC.items():
        p = os.path.join(tools, name)
        old = ''
        if os.path.isfile(p):
            try:
                old = io.open(p, 'r', encoding='utf-8').read()
            except Exception:
                old = ''
            if _ver(old) >= PKG:
                continue
            bak = os.path.join(tools, '_54번_이전판')
            os.makedirs(bak, exist_ok=True)
            shutil.copy2(p, os.path.join(bak, '%s.%s' % (name, datetime.datetime.now().strftime('%y%m%d_%H%M'))))
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        did.append('%s %s' % (name, '새 판으로' if old else '새로'))
    sd = os.path.join(tools, '제안서_내용')
    os.makedirs(sd, exist_ok=True)
    n = 0
    for name, text in SPECS.items():
        p = os.path.join(sd, name)
        if not os.path.isfile(p):
            with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            n += 1
    if n:
        did.append('제안서 내용 %d건 새로' % n)
    return did


# ── 33번 현황판 ⑧ 칸 (zip 이 옛 t33 으로 덮어도 다시 넣는다) ──────────
T33_B8 = '''    # ⑧ 현장별 한 곳에 - 흩어진 결과를 현장 이름으로 묶는다 (파일은 옮기지 않는다)
    #    site_index.py 가 없거나 실패해도 현황판은 그대로 나간다
    B8, si_path = [], None
    try:
        import site_index
        si_path = site_index.build(quiet=True)
        found, _loose, _root = site_index.scan()
        for sname in sorted(found):
            B8.append(('blue', '%s : %s' % (sname, ' · '.join(
                '%s %d' % (k, len(v)) for k, v in found[sname].items()))))
        if _loose:
            B8.append(('gray', '현장을 못 읽은 파일 %d개' % sum(len(v) for v in _loose.values())))
    except Exception:
        pass
    if not B8:
        B8 = [('gray', '현장별로 묶을 결과가 아직 없습니다')]

'''
T33_B7 = "('⑦ 회의에서 바뀐 수량·규격 (최근 30일, PLAUD 회의록)', B7)]"
T33_B7_NEW = ("('⑦ 회의에서 바뀐 수량·규격 (최근 30일, PLAUD 회의록)', B7),\n"
              "              ('⑧ 현장별 한 곳에 (산출·견적·실행·단가장·제안서·회의록)', B8)]")
T33_LINK = "[d for *_, d in srows if d] + [pbf] if x]"
T33_LINK_NEW = "[d for *_, d in srows if d] + [pbf, si_path] if x]"


def patch_t33(tools):
    p = os.path.join(tools, 't33_dashboard.py')
    if not os.path.isfile(p):
        return '33번이 없어 ⑧ 칸은 건너뜀'
    s = io.open(p, 'r', encoding='utf-8').read()
    if 'import site_index' in s:
        return ''
    anchor = '    blocks = [('
    if s.count(anchor) != 1 or s.count(T33_B7) != 1 or s.count(T33_LINK) != 1:
        return '33번 모양이 달라져 ⑧ 칸을 넣지 않았습니다 (현황판은 그대로 돕니다)'
    s2 = s.replace(anchor, T33_B8 + anchor).replace(T33_B7, T33_B7_NEW).replace(T33_LINK, T33_LINK_NEW)
    try:
        compile(s2, p, 'exec')
    except Exception:
        return '33번에 ⑧ 칸을 넣으면 문법이 깨져 넣지 않았습니다'
    shutil.copy2(p, p + '.bak_54')
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s2)
    return '33번 현황판에 ⑧ 현장별 한 곳에 칸을 다시 넣음 (원본 t33_dashboard.py.bak_54)'


def main():
    say('=' * 60)
    say(' ★제안서 PPT   (54번 v%d · AI 사용량 0)' % PKG)
    say('=' * 60)
    tools = find_tools()
    if not tools:
        say('★ 도구 폴더(km_tools)를 못 찾았습니다. 이 파일을 2_KM도구 폴더 바로 아래에 두십시오.')
        return
    for x in install(tools) + [patch_t33(tools)]:
        if x:
            say(' 정비 : ' + x)
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        import pptx  # noqa
    except Exception:
        say('')
        say('★ 파워포인트 부품(python-pptx)이 없습니다. 명령창에 아래 한 줄을 넣고 다시 누르십시오.')
        say('    pip install python-pptx')
        return
    say('')
    say('  1. 제안서 PPT 만들기      (27번 도면수량 먼저 돌려 두면 물량표 자동)')
    say('  2. 점유율 80% 로 고치기   (회사 제안서 pptx 를 새 파일로, 원본 그대로)')
    say('  3. 현장별 한 곳에 보기    (파일은 옮기지 않고 화면만)')
    say('  0. 닫기')
    try:
        s = input('\n번호 (엔터 = 1) > ').strip() or '1'
    except EOFError:
        s = '1'
    if s == '1':
        import t54_deck
        t54_deck.run()
    elif s == '2':
        import errata_apply
        errata_apply.run()
    elif s == '3':
        import site_index
        p = site_index.build()
        try:
            os.startfile(p)
        except Exception:
            pass


def save_note():
    p = os.path.join(HERE, '제안서PPT_결과.txt')
    try:
        with io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n') as f:
            f.write('\n'.join(NOTE))
    except Exception:
        pass


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        pass
    except Exception:
        say('')
        say('★ 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        for ln in traceback.format_exc().split('\n'):
            say('  ' + ln)
    finally:
        save_note()
        try:
            input('\n엔터를 누르면 닫힙니다... ')
        except Exception:
            pass

# -*- coding: utf-8 -*-
"""★회의록 한 방에 — 이 파일만 더블클릭하십시오. (2026-09-22)

PLAUD 메모장을 넣어 두시고 이것 하나만 누르시면, 아래가 저절로 다 됩니다.

    1) 회의록 만들기          40번 : 받는함 txt -> _현장비서 -> 회의록(docx + meta.json)
    2) 구글 드라이브로 올리기  51번 : 회의록 -> 드라이브\회의록\incoming
    3) 메일 원고 만들기        52번 : meta.json -> 「회의록정리_YYMMDD.txt」  (AI 사용량 0)
    4) 메일 원고를 드라이브로   드라이브\KM_아침메일\ 에 올려 둔다
                               -> 내일 07:00 앱스 스크립트가 읽어서 메일로 보냅니다

차장님 손은 두 번뿐입니다 : PLAUD 메모장 저장 -> 이 파일 누르기. 그다음은 전부 저절로.

왜 시작.py 가 아니라 이 파일인가
    시작.py 엔터는 「오늘 한 방에」 가 돌면서 새 zip 을 자동 적용합니다.
    그 zip 이 51번 연결을 지워 버리는 일이 3번 있었습니다(2026-09-22).
    이 파일은 2_KM도구 폴더 바로 아래에 있어 zip 이 건드리지 않습니다.

※ 전에 드린 「★회의록_드라이브로.py」 는 위 2)번만 하던 것입니다.
  이 파일이 그것을 품고 있으니 앞으로는 이것만 누르시면 됩니다. (그 파일은 지우지 않았습니다)
"""
import os, sys, io, shutil, datetime, traceback

# ── 52번(메일 원고 만들기) 소스를 이 파일이 통째로 품고 있습니다 ──────────
#    km_tools 에 t52_mailbuild.py 가 없으면 이 파일이 스스로 만들어 넣습니다.
#    그래서 차장님은 이 파일 하나만 넣으시면 됩니다.
T52_SRC = '# -*- coding: utf-8 -*-\n"""\n52. 회의록 정리 메일 원고 만들기  (km_tools / t52_mailbuild)\n\nmeta.json 만 읽어서 「현장별 회의록 정리」 메일 원고를 만든다.\n클로드(AI)를 전혀 쓰지 않는다 → 사용량 0.\n\n    python t52_mailbuild.py <meta폴더> [--from 260921] [--to 260922] [--out 폴더]\n\n만드는 것\n    회의록정리_YYMMDD.txt    메일 본문(글자)\n    회의록정리_YYMMDD.html   메일 본문(서식)\n    회의록정리_YYMMDD.json   몇 건을 어디서 뽑았는지 (자가진단용)\n\n규칙 (배성윤 프로 확정)\n    · 줄 수 제한 없음 - 있는 것은 다 적는다\n    · 빈 칸은 아예 찍지 않는다 ("없음"도 안 찍는다)\n    · 1) 회의록을 위에, 2) 그 아래 현장별 중요 사항\n    · 현장 이름이 달리 적혀도 (앵커호텔 / 앵커 호텔) 한 현장으로 묶는다\n"""\nfrom __future__ import print_function\nimport os, sys, io, json, re, datetime\n\nVERSION = \'v1 2026-09-22\'\n\n# ── 빈 값으로 볼 것 ─────────────────────────────────────────\nEMPTY = (\'\', \'-\', \'없음\', \'- 없음\', \'해당 없음\', \'- 해당 없음\', \'미정\', \'N/A\', \'n/a\')\nJUNK_RE = re.compile(r\'^[=\\-_\\s]+$\')\n\n\ndef _is_empty(v):\n    if v is None:\n        return True\n    s = str(v).strip()\n    s = re.sub(r\'^[-·•]\\s*\', \'\', s).strip()\n    if not s or s in EMPTY:\n        return True\n    # 「없음 — 무엇 확인 후 재협의 예정」 은 결정이 안 난 것이다. 찍지 않는다.\n    if re.match(r\'^(없음|해당\\s*없음|미정)\\s*[—\\-–:]\', s):\n        return True\n    return bool(JUNK_RE.match(s))\n\n\ndef _clean(v):\n    s = str(v).strip()\n    return re.sub(r\'^[-·•]\\s*\', \'\', s).strip()\n\n\ndef _lines(v):\n    """문자열 / 리스트 / 표(리스트의 리스트) 를 모두 줄 목록으로."""\n    out = []\n    if v is None:\n        return out\n    if isinstance(v, (str, bytes)):\n        for ln in str(v).split(\'\\n\'):\n            if not _is_empty(ln):\n                out.append(_clean(ln))\n        return out\n    if isinstance(v, dict):\n        v = list(v.values())\n    if isinstance(v, (list, tuple)):\n        for it in v:\n            if isinstance(it, (list, tuple)):\n                cells = [_clean(c) for c in it if not _is_empty(c)]\n                if cells:\n                    out.append(\' | \'.join(cells))\n            elif isinstance(it, dict):\n                out.extend(_lines(list(it.values())))\n            elif not _is_empty(it):\n                out.append(_clean(it))\n    return out\n\n\n# ── 현장 이름 묶기 ──────────────────────────────────────────\ndef norm_site(s):\n    s = (s or \'\').strip()\n    s = re.sub(r\'^[_\\s]+\', \'\', s)\n    s = re.sub(r\'\\s+\', \'\', s)\n    return s\n\n\ndef merge_sites(names):\n    """짧은 이름이 긴 이름의 앞머리이면 한 현장으로 본다(동구로초 ⊂ 동구로초등학교)."""\n    uniq = sorted(set(n for n in names if n), key=len)\n    rep = {}\n    for n in uniq:\n        hit = None\n        for r in rep.values():\n            if len(r) >= 3 and (n.startswith(r) or r.startswith(n)):\n                hit = r\n                break\n        rep[n] = hit or n\n    return rep\n\n\n# ── meta.json 한 건 읽기 ────────────────────────────────────\ndef who(m):\n    """협의자 한 줄. company 칸에 안건이 통째로 들어온 자료가 많아 걸러낸다."""\n    name = (m.get(\'name\') or \'\').strip()\n    rank = (m.get(\'rank\') or \'\').strip()\n    person = (m.get(\'person\') or \'\').strip()\n    comp = (m.get(\'company\') or \'\').strip()\n    # 안건이 섞여 들어온 회사칸은 버린다\n    if len(comp) > 20 or \',\' in comp:\n        comp = \'\'\n    base = (name + \' \' + rank).strip() if name else person\n    if not base:\n        base = person or comp\n    # person 이 name 을 되풀이하면 짧은 쪽만\n    if base and person and base in person and len(person) > len(base) * 2:\n        pass\n    out = \' \'.join(x for x in [comp, base] if x and x not in (comp if x is base else base))\n    out = re.sub(r\'\\s+\', \' \', out).strip()\n    return out[:40] or \'상대 미상\'\n\n\nSEC1_KEYS = [\'확인·회신 요청 사항\', \'일정\', \'수량·규격 변경\']\nSEC2_KEYS = [\'할 일\', \'리스크와 대처\', \'타부서 전달 사항\', \'대외 언급 금지 사항\']\n\n\ndef read_meta(path):\n    with io.open(path, \'r\', encoding=\'utf-8\') as f:\n        d = json.load(f)\n    m = d.get(\'meta\', {}) or {}\n    sec = d.get(\'sec\', {}) or {}\n    s1 = sec.get(\'1\', {}) or {}\n    s2 = sec.get(\'2\', {}) or {}\n\n    site = m.get(\'site\') or s1.get(\'현장\') or \'\'\n    rec = {\n        \'file\': os.path.basename(path),\n        \'site_raw\': site,\n        \'site\': norm_site(site),\n        \'ymd\': m.get(\'ymd\') or \'\',\n        \'hm\': m.get(\'hm\') or \'\',\n        \'person\': who(m),\n        \'company\': \'\',\n        \'topic\': _clean(s1.get(\'안건\') or \'\'),\n        \'items\': [],\n        \'blocks\': [],\n        \'dates\': [],\n    }\n\n    for it in (s1.get(\'안건목록\') or []):\n        if not isinstance(it, dict):\n            continue\n        one = {\n            \'title\': _clean(it.get(\'title\') or \'\'),\n            \'bullets\': _lines(it.get(\'bullets\')),\n            \'decision\': \'\' if _is_empty(it.get(\'decision\')) else _clean(it.get(\'decision\')),\n            \'actions\': _lines(it.get(\'actions\')),\n        }\n        if one[\'title\'] or one[\'bullets\'] or one[\'decision\'] or one[\'actions\']:\n            rec[\'items\'].append(one)\n\n    for k in SEC1_KEYS:\n        v = _lines(s1.get(k))\n        if v:\n            rec[\'blocks\'].append((k, v))\n    for k in SEC2_KEYS:\n        v = _lines(s2.get(k))\n        if v:\n            rec[\'blocks\'].append((k, v))\n\n    # 날짜 뽑기 : 일정표 + 할 일 + 일정 에 박힌 YYMMDD\n    hay = json.dumps({\'a\': s1.get(\'일정표\'), \'b\': s1.get(\'일정\'), \'c\': s2.get(\'할 일\')},\n                     ensure_ascii=False)\n    for d8 in re.findall(r\'(?<!\\d)(2[0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12]\\d|3[01]))(?!\\d)\', hay):\n        rec[\'dates\'].append(d8)\n    rec[\'dates\'] = sorted(set(rec[\'dates\']))\n    return rec\n\n\ndef collect(meta_dir, d_from=None, d_to=None):\n    recs, skipped = [], []\n    for root, _dirs, files in os.walk(meta_dir):\n        for fn in files:\n            if not fn.endswith(\'meta.json\'):\n                continue\n            if fn.startswith(\'_삭제요망\'):\n                skipped.append((fn, \'삭제요망\'))\n                continue\n            p = os.path.join(root, fn)\n            try:\n                r = read_meta(p)\n            except Exception as e:\n                skipped.append((fn, \'읽기실패 %s\' % e))\n                continue\n            if d_from and (not r[\'ymd\'] or r[\'ymd\'] < d_from):\n                skipped.append((fn, \'기간밖 %s\' % r[\'ymd\']))\n                continue\n            if d_to and (not r[\'ymd\'] or r[\'ymd\'] > d_to):\n                skipped.append((fn, \'기간밖 %s\' % r[\'ymd\']))\n                continue\n            recs.append(r)\n    return recs, skipped\n\n\n# ── 중복 지우기 (글자가 똑같은 것만) ────────────────────────\ndef _key(s):\n    return re.sub(r\'[\\s·,.\\-()]+\', \'\', s)\n\n\ndef dedupe(recs):\n    """같은 현장 안에서 글자가 같은 줄은 한 번만 남긴다. 몇 줄을 지웠는지 돌려준다."""\n    seen, cut = {}, 0\n    for r in recs:\n        bag = seen.setdefault(r[\'site\'], set())\n        for it in r[\'items\']:\n            keep = []\n            for b in it[\'bullets\']:\n                k = _key(b)\n                if k in bag:\n                    cut += 1\n                else:\n                    bag.add(k)\n                    keep.append(b)\n            it[\'bullets\'] = keep\n        nb = []\n        for name, vals in r[\'blocks\']:\n            keep = []\n            for v in vals:\n                k = (name, _key(v))\n                if k in bag:\n                    cut += 1\n                else:\n                    bag.add(k)\n                    keep.append(v)\n            if keep:\n                nb.append((name, keep))\n        r[\'blocks\'] = nb\n    return cut\n\n\n# ── 원고 만들기 ────────────────────────────────────────────\nWD = [\'월\', \'화\', \'수\', \'목\', \'금\', \'토\', \'일\']\n\n\ndef _d(ymd):\n    if not ymd or len(ymd) != 6:\n        return ymd or \'\'\n    return \'%s/%s\' % (int(ymd[2:4]), int(ymd[4:6]))\n\n\ndef build_text(recs, today=None):\n    today = today or datetime.date.today()\n    ty = today.strftime(\'%y%m%d\')\n    tm = (today + datetime.timedelta(days=1)).strftime(\'%y%m%d\')\n\n    rep = merge_sites([r[\'site\'] for r in recs])\n    sites = {}\n    for r in recs:\n        sites.setdefault(rep.get(r[\'site\'], r[\'site\']), []).append(r)\n    for k in sites:\n        sites[k].sort(key=lambda r: (r[\'ymd\'], r[\'hm\']))\n    order = sorted(sites, key=lambda k: (-len(sites[k]), k))\n\n    L = []\n    L.append(\'회의록 정리 %s (%s)\' % (today.strftime(\'%Y-%m-%d\'), WD[today.weekday()]))\n    L.append(\'협의 %d건 · %d개 현장\' % (len(recs), len(sites)))\n    L.append(\'이 메일은 파이썬이 meta.json 만 읽어 만들었습니다. (AI 사용량 0)\')\n    L.append(\'\')\n\n    # 날짜가 박힌 것\n    urgent = []\n    for r in recs:\n        for d8 in r[\'dates\']:\n            if d8 >= ty:\n                urgent.append((d8, rep.get(r[\'site\'], r[\'site\']), r))\n    if urgent:\n        L.append(\'=\' * 56)\n        L.append(\'[ 날짜가 박힌 것 ]\')\n        L.append(\'=\' * 56)\n        for d8, site, r in sorted(set((u[0], u[1], u[2][\'file\']) for u in urgent)):\n            mark = \'  <-- 오늘\' if d8 == ty else (\'  <-- 내일\' if d8 == tm else \'\')\n            L.append(\'  %s  %s%s\' % (_d(d8), site, mark))\n        L.append(\'\')\n\n    # 1) 회의록\n    L.append(\'=\' * 56)\n    L.append(\'[ 1. 회의록 ] - 현장별, 빠짐없이\')\n    L.append(\'=\' * 56)\n    for i, site in enumerate(order, 1):\n        rs = sites[site]\n        L.append(\'\')\n        L.append(\'-\' * 56)\n        L.append(\'%d. %s   (협의 %d건)\' % (i, site, len(rs)))\n        L.append(\'-\' * 56)\n        for r in rs:\n            who = \' \'.join(x for x in [r[\'company\'], r[\'person\']] if x)\n            head = \'  [%s %s] %s\' % (_d(r[\'ymd\']), r[\'hm\'], who or \'상대 미상\')\n            L.append(head)\n            if r[\'topic\']:\n                L.append(\'    안건> %s\' % r[\'topic\'])\n            for it in r[\'items\']:\n                if it[\'title\']:\n                    L.append(\'    · %s\' % it[\'title\'])\n                for b in it[\'bullets\']:\n                    L.append(\'        %s\' % b)\n                if it[\'decision\']:\n                    L.append(\'      결정> %s\' % it[\'decision\'])\n                for a in it[\'actions\']:\n                    L.append(\'      조치> %s\' % a)\n            for name, vals in r[\'blocks\']:\n                L.append(\'    %s>\' % name)\n                for v in vals:\n                    L.append(\'        %s\' % v)\n            L.append(\'\')\n\n    # 2) 현장별 중요 사항\n    L.append(\'=\' * 56)\n    L.append(\'[ 2. 현장별 중요 사항 ] - 위 회의록에서 결정·변경만 추림\')\n    L.append(\'=\' * 56)\n    for site in order:\n        picked = []\n        for r in sites[site]:\n            for it in r[\'items\']:\n                if it[\'decision\']:\n                    picked.append(\'%s  %s\' % (_d(r[\'ymd\']), it[\'decision\']))\n            for name, vals in r[\'blocks\']:\n                if name in (\'수량·규격 변경\', \'확인·회신 요청 사항\'):\n                    for v in vals:\n                        picked.append(\'%s  [%s] %s\' % (_d(r[\'ymd\']), name, v))\n        if not picked:\n            continue\n        L.append(\'\')\n        L.append(\'* %s\' % site)\n        for p in picked:\n            L.append(\'    %s\' % p)\n\n    L.append(\'\')\n    L.append(\'-\' * 56)\n    L.append(\'t52_mailbuild %s · meta.json %d건\' % (VERSION, len(recs)))\n    return \'\\n\'.join(L)\n\n\ndef build_html(text):\n    esc = (text.replace(\'&\', \'&amp;\').replace(\'<\', \'&lt;\').replace(\'>\', \'&gt;\'))\n    return (\'<div style="font-family:맑은 고딕,Malgun Gothic,sans-serif;font-size:13px;\'\n            \'line-height:1.55;white-space:pre-wrap">%s</div>\' % esc)\n\n\ndef run(meta_dir, d_from=None, d_to=None, out=None, today=None):\n    recs, skipped = collect(meta_dir, d_from, d_to)\n    before = sum(len(b) for r in recs for _n, b in r[\'blocks\']) + \\\n             sum(len(i[\'bullets\']) for r in recs for i in r[\'items\'])\n    cut = dedupe(recs)\n    text = build_text(recs, today)\n    out = out or meta_dir\n    if not os.path.isdir(out):\n        os.makedirs(out)\n    stamp = (today or datetime.date.today()).strftime(\'%y%m%d\')\n    base = os.path.join(out, \'회의록정리_%s\' % stamp)\n    with io.open(base + \'.txt\', \'w\', encoding=\'utf-8\') as f:\n        f.write(text)\n    with io.open(base + \'.html\', \'w\', encoding=\'utf-8\') as f:\n        f.write(build_html(text))\n    rep = merge_sites([r[\'site\'] for r in recs])\n    stat = {\n        \'version\': VERSION,\n        \'회의수\': len(recs),\n        \'현장수\': len(set(rep.get(r[\'site\'], r[\'site\']) for r in recs)),\n        \'현장목록\': sorted(set(rep.get(r[\'site\'], r[\'site\']) for r in recs)),\n        \'줄수\': len(text.split(\'\\n\')),\n        \'글자수\': len(text),\n        \'중복지운줄\': cut,\n        \'중복전줄\': before,\n        \'건너뜀\': len(skipped),\n    }\n    with io.open(base + \'.json\', \'w\', encoding=\'utf-8\') as f:\n        f.write(json.dumps(stat, ensure_ascii=False, indent=1))\n\n    # 현장당 1통용 : 현장별로 따로 저장한다\n    per = os.path.join(out, \'현장별_%s\' % stamp)\n    if not os.path.isdir(per):\n        os.makedirs(per)\n    rep2 = merge_sites([r[\'site\'] for r in recs])\n    by = {}\n    for r in recs:\n        by.setdefault(rep2.get(r[\'site\'], r[\'site\']), []).append(r)\n    stat[\'현장별\'] = {}\n    for site, rs in by.items():\n        t = build_text(rs, today)\n        fn = os.path.join(per, \'%s.txt\' % re.sub(r\'[\\\\/:*?"<>|]\', \'_\', site))\n        with io.open(fn, \'w\', encoding=\'utf-8\') as f:\n            f.write(t)\n        stat[\'현장별\'][site] = {\'회의\': len(rs), \'줄\': len(t.split(\'\\n\')), \'글자\': len(t)}\n    with io.open(base + \'.json\', \'w\', encoding=\'utf-8\') as f:\n        f.write(json.dumps(stat, ensure_ascii=False, indent=1))\n    return text, stat\n\n\ndef main(argv):\n    if len(argv) < 2:\n        print(__doc__)\n        return 1\n    meta_dir = argv[1]\n    d_from = d_to = out = None\n    i = 2\n    while i < len(argv):\n        if argv[i] == \'--from\':\n            d_from = argv[i + 1]; i += 2\n        elif argv[i] == \'--to\':\n            d_to = argv[i + 1]; i += 2\n        elif argv[i] == \'--out\':\n            out = argv[i + 1]; i += 2\n        else:\n            i += 1\n    _t, stat = run(meta_dir, d_from, d_to, out)\n    print(json.dumps(stat, ensure_ascii=False, indent=1))\n    return 0\n\n\nif __name__ == \'__main__\':\n    sys.exit(main(sys.argv))\n'


def load_t52(tools):
    """52번을 불러온다. 없으면 내가 만들어 넣고 불러온다."""
    try:
        import t52_mailbuild as MB
        return MB, ''
    except Exception:
        pass
    for where in (tools, HERE):
        if not where:
            continue
        p = os.path.join(where, 't52_mailbuild.py')
        try:
            with io.open(p, 'w', encoding='utf-8') as f:
                f.write(T52_SRC)
            if where not in sys.path:
                sys.path.insert(0, where)
            import t52_mailbuild as MB
            return MB, '52번이 없어서 새로 넣었습니다 : %s' % p
        except Exception:
            continue
    return None, '52번을 만들어 넣지 못했습니다(폴더에 쓸 수 없음).'


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
        if os.path.isfile(os.path.join(p, 't51_driveup.py')):
            return p
    for root, _dirs, files in os.walk(HERE):
        if 't51_driveup.py' in files and root.count(os.sep) - HERE.count(os.sep) <= 3:
            return root
    return ''



# ── 구글 드라이브 폴더 찾기 (51번이 못 찾을 때 더 뒤진다) ──────────────
DRIVE_NAMES = ('내 드라이브', 'My Drive', 'GoogleDrive', 'Google Drive')


def _ini_path():
    for c in (os.path.join(HERE, '설정.ini'),
              os.path.join(HERE, '코드', '설정.ini'),
              os.path.join(os.path.dirname(HERE), '설정.ini')):
        if os.path.isfile(c):
            return c
    return os.path.join(HERE, '설정.ini')


def _ini_get():
    try:
        import configparser
        c = configparser.ConfigParser()
        c.read(_ini_path(), encoding='utf-8')
        v = c.get('드라이브', '경로')
        return v.strip() if v else ''
    except Exception:
        return ''


def _ini_put(path):
    """[드라이브] 경로 를 저장한다. 다른 절은 건드리지 않는다. BOM 을 붙이지 않는다."""
    try:
        import configparser
        p = _ini_path()
        c = configparser.ConfigParser()
        if os.path.isfile(p):
            c.read(p, encoding='utf-8')
        if not c.has_section('드라이브'):
            c.add_section('드라이브')
        c.set('드라이브', '경로', path)
        with io.open(p, 'w', encoding='utf-8') as f:
            c.write(f)
        return p
    except Exception:
        return ''


def hunt_drive():
    """구글 드라이브 폴더를 스스로 찾는다. 찾은 곳들을 함께 돌려준다."""
    seen, looked = [], []

    def take(p):
        if p and os.path.isdir(p) and p not in seen:
            seen.append(p)

    v = _ini_get()
    looked.append('설정.ini [드라이브] 경로 = %s' % (v or '(비어 있음)'))
    take(v)

    # 드라이브 문자 전부. 어느 문자가 살아 있는지도 남긴다(원인을 보시라고).
    alive = []
    for i in range(ord('C'), ord('Z') + 1):
        d = '%s:\\' % chr(i)
        if not os.path.isdir(d):
            continue
        try:
            inside = os.listdir(d)[:6]
        except Exception:
            inside = ['(못 읽음)']
        alive.append('%s  ->  %s' % (d, ', '.join(inside) if inside else '(비어 있음)'))
        for n in DRIVE_NAMES:
            take(os.path.join(d, n))
    looked.append('살아 있는 드라이브 문자 %d개' % len(alive))
    for a in alive:
        looked.append('    %s' % a)

    # 사용자 폴더 아래
    home = os.path.expanduser('~')
    for n in DRIVE_NAMES:
        take(os.path.join(home, n))
        take(os.path.join(home, 'Google Drive', n))
    looked.append('사용자 폴더 : %s' % home)

    return seen, looked


def gdrive_installed():
    """구글 드라이브 데스크톱이 깔려는 있는지. 꺼진 것과 안 깔린 것을 가른다."""
    spots = [
        r'C:\Program Files\Google\Drive File Stream',
        r'C:\Program Files (x86)\Google\Drive File Stream',
        os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'DriveFS'),
    ]
    for p in spots:
        if os.path.isdir(p):
            return True
    return False


def fix_drive(found_by_51):
    """51번이 못 찾았으면 내가 더 찾고, 그래도 없으면 여쭙는다."""
    if found_by_51:
        return found_by_51
    seen, looked = hunt_drive()
    for ln in looked:
        say('  본 곳 : %s' % ln)
    if seen:
        say('  찾았습니다 : %s' % seen[0])
        p = _ini_put(seen[0])
        if p:
            say('  설정.ini 에 적어 두었습니다 (%s). 다음부터는 안 물어봅니다.' % p)
        return seen[0]
    say('')
    say('  ★ 구글 드라이브 폴더를 못 찾았습니다.')
    if gdrive_installed():
        say('')
        say('    ※ 구글 드라이브 데스크톱은 깔려 있습니다. 지금 꺼져 있을 뿐입니다.')
        say('      시작 메뉴에서 「Google Drive」 를 찾아 켜 주십시오.')
        say('      켜고 1~2분 기다리면 G: 가 생깁니다. 그다음 이 파일을 다시 누르시면 됩니다.')
        say('      (매번 저절로 켜지게 하려면 : 구글 드라이브 설정 -> 「시스템 시작 시 실행」 켜기)')
        say('')
        say('    그래도 안 되면 아래에 자리를 넣어 주십시오.')
    else:
        say('')
        say('    ※ 구글 드라이브 데스크톱이 안 깔려 있는 것 같습니다.')
        say('      google.com/drive/download 에서 받아 까시면 됩니다. 무료·5분.')
        say('')
    say('    윈도 탐색기에서 「내 드라이브」 폴더를 여시고,')
    say('    맨 위 주소줄을 눌러 나오는 글자를 그대로 붙여 넣어 주십시오.')
    say('    (예 : G:\\내 드라이브)   그냥 엔터를 치시면 건너뜁니다.')
    try:
        v = input('    내 드라이브 자리 : ').strip().strip('"')
    except Exception:
        v = ''
    if v and os.path.isdir(v):
        p = _ini_put(v)
        say('  고맙습니다. 설정.ini 에 적어 두었습니다 (%s).' % p)
        return v
    if v:
        say('  그 자리에 폴더가 없습니다 : %s' % v)
    return ''


def step(n, title, fn):
    """한 걸음. 넘어져도 다음 걸음으로 간다."""
    say('')
    say('-' * 60)
    say(' %d) %s' % (n, title))
    say('-' * 60)
    try:
        return fn()
    except Exception:
        say('  ★ 여기서 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        for ln in traceback.format_exc().split('\n'):
            say('    ' + ln)
        return None


def main():
    say('=' * 60)
    say(' 회의록 한 방에        %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
    say('=' * 60)

    tools = find_tools()
    if not tools:
        say('')
        say('★ 도구 폴더(km_tools)를 못 찾았습니다.')
        say('  이 파일이 「2_KM도구」 폴더 바로 아래에 있어야 합니다.')
        say('  지금 자리 : %s' % HERE)
        return
    sys.path.insert(0, tools)
    say(' 도구 자리 : %s' % tools)

    # ── 1) 회의록 만들기 (40번) ───────────────────────────
    def s1():
        try:
            import t40_meeting as MT
        except Exception:
            say('  40번이 없어 건너뜁니다. (회의록을 이미 만들어 두셨다면 그대로 진행됩니다)')
            return None
        r = MT.run() if hasattr(MT, 'run') else None
        say('  회의록 만들기 끝.')
        return r
    step(1, '회의록 만들기  (PLAUD 메모장 -> 회의록)', s1)

    # ── 2) 드라이브로 올리기 (51번) ───────────────────────
    drive = ['']

    def s2():
        import t51_driveup as DU
        drive[0] = fix_drive(DU.drive_root())
        if not drive[0]:
            return {'올림': 0, '이유': '드라이브 폴더 없음'}
        r = DU.run(quiet=True)
        if r.get('이유'):
            say('  못 올렸습니다 : %s' % r['이유'])
        else:
            say('  찾음 %s개 / 새로 올림 %s개' % (r.get('찾음', 0), r.get('올림', 0)))
        return r
    r2 = step(2, '구글 드라이브로 올리기', s2)

    # ── 3) 메일 원고 만들기 (52번) ────────────────────────
    made = ['']

    def s3():
        MB, msg = load_t52(tools)
        if msg:
            say('  %s' % msg)
        if MB is None:
            return None
        root = drive[0]
        if not root:
            say('  드라이브 폴더를 못 찾아 건너뜁니다.')
            return None
        meta_dir = os.path.join(root, '회의록', 'incoming')
        if not os.path.isdir(meta_dir):
            say('  %s 가 없어 건너뜁니다.' % meta_dir)
            return None
        today = datetime.date.today()
        frm = (today - datetime.timedelta(days=1)).strftime('%y%m%d')   # 어제부터
        to = today.strftime('%y%m%d')
        out = os.path.join(HERE, '_회의록정리')
        text, stat = MB.run(meta_dir, frm, to, out=out, today=today)
        made[0] = os.path.join(out, '회의록정리_%s.txt' % to)
        say('  기간 : %s ~ %s' % (frm, to))
        say('  회의 %s건 / 현장 %s개 / %s줄' % (stat['회의수'], stat['현장수'], stat['줄수']))
        if stat.get('현장별'):
            for k, v in sorted(stat['현장별'].items(), key=lambda x: -x[1]['회의']):
                say('      %-14s 협의 %d건' % (k, v['회의']))
        say('  만든 곳 : %s' % out)
        return stat
    r3 = step(3, '메일 원고 만들기  (AI 사용량 0)', s3)

    # ── 4) 메일 원고를 드라이브로 ─────────────────────────
    def s4():
        if not made[0] or not os.path.isfile(made[0]):
            say('  올릴 원고가 없어 건너뜁니다.')
            return None
        root = drive[0]
        if not root:
            say('  드라이브 폴더를 못 찾아 건너뜁니다.')
            return None
        dest = os.path.join(root, 'KM_아침메일')
        if not os.path.isdir(dest):
            os.makedirs(dest)
        tgt = os.path.join(dest, os.path.basename(made[0]))
        shutil.copy2(made[0], tgt)
        say('  올렸습니다 : %s' % tgt)
        say('  5분 안에 bsy 메일로 갑니다. (KM_즉시발송 이 지켜보고 있습니다)')
        return tgt
    step(4, '메일 원고를 드라이브로 올리기', s4)

    # ── 마무리 ────────────────────────────────────────────
    say('')
    say('=' * 60)
    if r3 and r3.get('회의수'):
        say(' 끝났습니다. 회의 %d건 / 현장 %d개 가 메일로 나갑니다.' % (r3['회의수'], r3['현장수']))
        say(' 지금 바로 보시려면 「_회의록정리」 폴더의 html 을 여십시오.')
        say(' 메일은 5분 안에 bsy@micronic.co.kr 로 갑니다.')
    elif r2 and r2.get('이유'):
        say(' 멈춘 까닭 : %s' % r2['이유'])
        say(' 위 화면을 클로드에게 보여 주십시오.')
    elif r2 and not r2.get('찾음'):
        say(' 새 회의록을 못 찾았습니다. 위 목록을 클로드에게 보여 주십시오.')
    else:
        say(' 새로 정리할 회의록이 없습니다 (전부 전에 처리한 것).')
    say('=' * 60)


def save_note():
    """화면이 꺼져도 볼 수 있게 남긴다."""
    p = os.path.join(HERE, '한방에_결과.txt')
    try:
        with io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n') as f:
            f.write('\n'.join(NOTE))
        try:
            os.startfile(p)
        except Exception:
            pass
    except Exception:
        pass


if __name__ == '__main__':
    try:
        main()
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

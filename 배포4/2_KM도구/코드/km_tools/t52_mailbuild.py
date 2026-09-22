# -*- coding: utf-8 -*-
"""
52. 회의록 정리 메일 원고 만들기  (km_tools / t52_mailbuild)

meta.json 만 읽어서 「현장별 회의록 정리」 메일 원고를 만든다.
클로드(AI)를 전혀 쓰지 않는다 → 사용량 0.

    python t52_mailbuild.py <meta폴더> [--from 260921] [--to 260922] [--out 폴더]

만드는 것
    회의록정리_YYMMDD.txt    메일 본문(글자)
    회의록정리_YYMMDD.html   메일 본문(서식)
    회의록정리_YYMMDD.json   몇 건을 어디서 뽑았는지 (자가진단용)

규칙 (배성윤 프로 확정)
    · 줄 수 제한 없음 - 있는 것은 다 적는다
    · 빈 칸은 아예 찍지 않는다 ("없음"도 안 찍는다)
    · 1) 회의록을 위에, 2) 그 아래 현장별 중요 사항
    · 현장 이름이 달리 적혀도 (앵커호텔 / 앵커 호텔) 한 현장으로 묶는다
"""
from __future__ import print_function
import os, sys, io, json, re, datetime

VERSION = 'v1 2026-09-22'

# ── 빈 값으로 볼 것 ─────────────────────────────────────────
EMPTY = ('', '-', '없음', '- 없음', '해당 없음', '- 해당 없음', '미정', 'N/A', 'n/a')
JUNK_RE = re.compile(r'^[=\-_\s]+$')


def _is_empty(v):
    if v is None:
        return True
    s = str(v).strip()
    s = re.sub(r'^[-·•]\s*', '', s).strip()
    if not s or s in EMPTY:
        return True
    # 「없음 — 무엇 확인 후 재협의 예정」 은 결정이 안 난 것이다. 찍지 않는다.
    if re.match(r'^(없음|해당\s*없음|미정)\s*[—\-–:]', s):
        return True
    return bool(JUNK_RE.match(s))


def _clean(v):
    s = str(v).strip()
    return re.sub(r'^[-·•]\s*', '', s).strip()


def _lines(v):
    """문자열 / 리스트 / 표(리스트의 리스트) 를 모두 줄 목록으로."""
    out = []
    if v is None:
        return out
    if isinstance(v, (str, bytes)):
        for ln in str(v).split('\n'):
            if not _is_empty(ln):
                out.append(_clean(ln))
        return out
    if isinstance(v, dict):
        v = list(v.values())
    if isinstance(v, (list, tuple)):
        for it in v:
            if isinstance(it, (list, tuple)):
                cells = [_clean(c) for c in it if not _is_empty(c)]
                if cells:
                    out.append(' | '.join(cells))
            elif isinstance(it, dict):
                out.extend(_lines(list(it.values())))
            elif not _is_empty(it):
                out.append(_clean(it))
    return out


# ── 현장 이름 묶기 ──────────────────────────────────────────
def norm_site(s):
    s = (s or '').strip()
    s = re.sub(r'^[_\s]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s


def merge_sites(names):
    """짧은 이름이 긴 이름의 앞머리이면 한 현장으로 본다(동구로초 ⊂ 동구로초등학교)."""
    uniq = sorted(set(n for n in names if n), key=len)
    rep = {}
    for n in uniq:
        hit = None
        for r in rep.values():
            if len(r) >= 3 and (n.startswith(r) or r.startswith(n)):
                hit = r
                break
        rep[n] = hit or n
    return rep


# ── meta.json 한 건 읽기 ────────────────────────────────────
def who(m):
    """협의자 한 줄. company 칸에 안건이 통째로 들어온 자료가 많아 걸러낸다."""
    name = (m.get('name') or '').strip()
    rank = (m.get('rank') or '').strip()
    person = (m.get('person') or '').strip()
    comp = (m.get('company') or '').strip()
    # 안건이 섞여 들어온 회사칸은 버린다
    if len(comp) > 20 or ',' in comp:
        comp = ''
    base = (name + ' ' + rank).strip() if name else person
    if not base:
        base = person or comp
    # person 이 name 을 되풀이하면 짧은 쪽만
    if base and person and base in person and len(person) > len(base) * 2:
        pass
    out = ' '.join(x for x in [comp, base] if x and x not in (comp if x is base else base))
    out = re.sub(r'\s+', ' ', out).strip()
    return out[:40] or '상대 미상'


SEC1_KEYS = ['확인·회신 요청 사항', '일정', '수량·규격 변경']
SEC2_KEYS = ['할 일', '리스크와 대처', '타부서 전달 사항', '대외 언급 금지 사항']


def read_meta(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    m = d.get('meta', {}) or {}
    sec = d.get('sec', {}) or {}
    s1 = sec.get('1', {}) or {}
    s2 = sec.get('2', {}) or {}

    site = m.get('site') or s1.get('현장') or ''
    rec = {
        'file': os.path.basename(path),
        'site_raw': site,
        'site': norm_site(site),
        'ymd': m.get('ymd') or '',
        'hm': m.get('hm') or '',
        'person': who(m),
        'company': '',
        'topic': _clean(s1.get('안건') or ''),
        'items': [],
        'blocks': [],
        'dates': [],
    }

    for it in (s1.get('안건목록') or []):
        if not isinstance(it, dict):
            continue
        one = {
            'title': _clean(it.get('title') or ''),
            'bullets': _lines(it.get('bullets')),
            'decision': '' if _is_empty(it.get('decision')) else _clean(it.get('decision')),
            'actions': _lines(it.get('actions')),
        }
        if one['title'] or one['bullets'] or one['decision'] or one['actions']:
            rec['items'].append(one)

    for k in SEC1_KEYS:
        v = _lines(s1.get(k))
        if v:
            rec['blocks'].append((k, v))
    for k in SEC2_KEYS:
        v = _lines(s2.get(k))
        if v:
            rec['blocks'].append((k, v))

    # 날짜 뽑기 : 일정표 + 할 일 + 일정 에 박힌 YYMMDD
    hay = json.dumps({'a': s1.get('일정표'), 'b': s1.get('일정'), 'c': s2.get('할 일')},
                     ensure_ascii=False)
    for d8 in re.findall(r'(?<!\d)(2[0-9](?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))(?!\d)', hay):
        rec['dates'].append(d8)
    rec['dates'] = sorted(set(rec['dates']))
    return rec


def collect(meta_dir, d_from=None, d_to=None):
    recs, skipped = [], []
    for root, _dirs, files in os.walk(meta_dir):
        for fn in files:
            if not fn.endswith('meta.json'):
                continue
            if fn.startswith('_삭제요망'):
                skipped.append((fn, '삭제요망'))
                continue
            p = os.path.join(root, fn)
            try:
                r = read_meta(p)
            except Exception as e:
                skipped.append((fn, '읽기실패 %s' % e))
                continue
            if d_from and (not r['ymd'] or r['ymd'] < d_from):
                skipped.append((fn, '기간밖 %s' % r['ymd']))
                continue
            if d_to and (not r['ymd'] or r['ymd'] > d_to):
                skipped.append((fn, '기간밖 %s' % r['ymd']))
                continue
            recs.append(r)
    return recs, skipped


# ── 중복 지우기 (글자가 똑같은 것만) ────────────────────────
def _key(s):
    return re.sub(r'[\s·,.\-()]+', '', s)


def dedupe(recs):
    """같은 현장 안에서 글자가 같은 줄은 한 번만 남긴다. 몇 줄을 지웠는지 돌려준다."""
    seen, cut = {}, 0
    for r in recs:
        bag = seen.setdefault(r['site'], set())
        for it in r['items']:
            keep = []
            for b in it['bullets']:
                k = _key(b)
                if k in bag:
                    cut += 1
                else:
                    bag.add(k)
                    keep.append(b)
            it['bullets'] = keep
        nb = []
        for name, vals in r['blocks']:
            keep = []
            for v in vals:
                k = (name, _key(v))
                if k in bag:
                    cut += 1
                else:
                    bag.add(k)
                    keep.append(v)
            if keep:
                nb.append((name, keep))
        r['blocks'] = nb
    return cut


# ── 원고 만들기 ────────────────────────────────────────────
WD = ['월', '화', '수', '목', '금', '토', '일']


def _d(ymd):
    if not ymd or len(ymd) != 6:
        return ymd or ''
    return '%s/%s' % (int(ymd[2:4]), int(ymd[4:6]))


def build_text(recs, today=None):
    today = today or datetime.date.today()
    ty = today.strftime('%y%m%d')
    tm = (today + datetime.timedelta(days=1)).strftime('%y%m%d')

    rep = merge_sites([r['site'] for r in recs])
    sites = {}
    for r in recs:
        sites.setdefault(rep.get(r['site'], r['site']), []).append(r)
    for k in sites:
        sites[k].sort(key=lambda r: (r['ymd'], r['hm']))
    order = sorted(sites, key=lambda k: (-len(sites[k]), k))

    L = []
    L.append('회의록 정리 %s (%s)' % (today.strftime('%Y-%m-%d'), WD[today.weekday()]))
    L.append('협의 %d건 · %d개 현장' % (len(recs), len(sites)))
    L.append('이 메일은 파이썬이 meta.json 만 읽어 만들었습니다. (AI 사용량 0)')
    L.append('')

    # 날짜가 박힌 것
    urgent = []
    for r in recs:
        for d8 in r['dates']:
            if d8 >= ty:
                urgent.append((d8, rep.get(r['site'], r['site']), r))
    if urgent:
        L.append('=' * 56)
        L.append('[ 날짜가 박힌 것 ]')
        L.append('=' * 56)
        for d8, site, r in sorted(set((u[0], u[1], u[2]['file']) for u in urgent)):
            mark = '  <-- 오늘' if d8 == ty else ('  <-- 내일' if d8 == tm else '')
            L.append('  %s  %s%s' % (_d(d8), site, mark))
        L.append('')

    # 1) 회의록
    L.append('=' * 56)
    L.append('[ 1. 회의록 ] - 현장별, 빠짐없이')
    L.append('=' * 56)
    for i, site in enumerate(order, 1):
        rs = sites[site]
        L.append('')
        L.append('-' * 56)
        L.append('%d. %s   (협의 %d건)' % (i, site, len(rs)))
        L.append('-' * 56)
        for r in rs:
            who = ' '.join(x for x in [r['company'], r['person']] if x)
            head = '  [%s %s] %s' % (_d(r['ymd']), r['hm'], who or '상대 미상')
            L.append(head)
            if r['topic']:
                L.append('    안건> %s' % r['topic'])
            for it in r['items']:
                if it['title']:
                    L.append('    · %s' % it['title'])
                for b in it['bullets']:
                    L.append('        %s' % b)
                if it['decision']:
                    L.append('      결정> %s' % it['decision'])
                for a in it['actions']:
                    L.append('      조치> %s' % a)
            for name, vals in r['blocks']:
                L.append('    %s>' % name)
                for v in vals:
                    L.append('        %s' % v)
            L.append('')

    # 2) 현장별 중요 사항
    L.append('=' * 56)
    L.append('[ 2. 현장별 중요 사항 ] - 위 회의록에서 결정·변경만 추림')
    L.append('=' * 56)
    for site in order:
        picked = []
        for r in sites[site]:
            for it in r['items']:
                if it['decision']:
                    picked.append('%s  %s' % (_d(r['ymd']), it['decision']))
            for name, vals in r['blocks']:
                if name in ('수량·규격 변경', '확인·회신 요청 사항'):
                    for v in vals:
                        picked.append('%s  [%s] %s' % (_d(r['ymd']), name, v))
        if not picked:
            continue
        L.append('')
        L.append('* %s' % site)
        for p in picked:
            L.append('    %s' % p)

    L.append('')
    L.append('-' * 56)
    L.append('t52_mailbuild %s · meta.json %d건' % (VERSION, len(recs)))
    return '\n'.join(L)


def build_html(text):
    esc = (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    return ('<div style="font-family:맑은 고딕,Malgun Gothic,sans-serif;font-size:13px;'
            'line-height:1.55;white-space:pre-wrap">%s</div>' % esc)


def run(meta_dir, d_from=None, d_to=None, out=None, today=None):
    recs, skipped = collect(meta_dir, d_from, d_to)
    before = sum(len(b) for r in recs for _n, b in r['blocks']) + \
             sum(len(i['bullets']) for r in recs for i in r['items'])
    cut = dedupe(recs)
    text = build_text(recs, today)
    out = out or meta_dir
    if not os.path.isdir(out):
        os.makedirs(out)
    stamp = (today or datetime.date.today()).strftime('%y%m%d')
    base = os.path.join(out, '회의록정리_%s' % stamp)
    with io.open(base + '.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    with io.open(base + '.html', 'w', encoding='utf-8') as f:
        f.write(build_html(text))
    rep = merge_sites([r['site'] for r in recs])
    stat = {
        'version': VERSION,
        '회의수': len(recs),
        '현장수': len(set(rep.get(r['site'], r['site']) for r in recs)),
        '현장목록': sorted(set(rep.get(r['site'], r['site']) for r in recs)),
        '줄수': len(text.split('\n')),
        '글자수': len(text),
        '중복지운줄': cut,
        '중복전줄': before,
        '건너뜀': len(skipped),
    }
    with io.open(base + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(stat, ensure_ascii=False, indent=1))

    # 현장당 1통용 : 현장별로 따로 저장한다
    per = os.path.join(out, '현장별_%s' % stamp)
    if not os.path.isdir(per):
        os.makedirs(per)
    rep2 = merge_sites([r['site'] for r in recs])
    by = {}
    for r in recs:
        by.setdefault(rep2.get(r['site'], r['site']), []).append(r)
    stat['현장별'] = {}
    for site, rs in by.items():
        t = build_text(rs, today)
        fn = os.path.join(per, '%s.txt' % re.sub(r'[\\/:*?"<>|]', '_', site))
        with io.open(fn, 'w', encoding='utf-8') as f:
            f.write(t)
        stat['현장별'][site] = {'회의': len(rs), '줄': len(t.split('\n')), '글자': len(t)}
    with io.open(base + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(stat, ensure_ascii=False, indent=1))
    return text, stat


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    meta_dir = argv[1]
    d_from = d_to = out = None
    i = 2
    while i < len(argv):
        if argv[i] == '--from':
            d_from = argv[i + 1]; i += 2
        elif argv[i] == '--to':
            d_to = argv[i + 1]; i += 2
        elif argv[i] == '--out':
            out = argv[i + 1]; i += 2
        else:
            i += 1
    _t, stat = run(meta_dir, d_from, d_to, out)
    print(json.dumps(stat, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

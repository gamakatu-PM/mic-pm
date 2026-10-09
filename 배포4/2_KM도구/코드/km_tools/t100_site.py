# -*- coding: utf-8 -*-
"""
t100_site.py v1 (2026-10-09) — 「정리해」 한마디에 현장별로 짧게 (AI 사용량 0)

차장님 2026-10-09 : 「현장별 정리가 되는 것도 만들어서, 내가 새 창을 열고 정리하라고 하면 내가 궁금한 것을 정리해줘야 돼」
「26년 회의록2」 시트(웹 앱 read new2 결과 json)만 읽는다. 차장님 PC 파일이 없는 클라우드 창에서도 돈다.

    python t100_site.py <시트.json> [현장 검색어] [--today YYMMDD]
      검색어 없음 → 급한 현장 10곳 한 줄씩 (기한 지난 것 많은 순)
      검색어 있음 → 그 이름이 들어간 현장마다 : 마지막 회의 · 기한 지난 것 · 다음 할 것 · 답 안 한 것

현장명은 시트 B·G열 그대로(meta.site). 이름이 비슷한 현장을 하나로 합치지 않는다(CLAUDE.md 3-1).
"""
from __future__ import print_function
import io, re, sys, json, datetime

VERSION = 'v1 2026-10-09'
DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
TODO_TABS = ('답요청', '오늘 할일', '앞으로 할일')


def _d(s):
    m = DATE_RE.match((s or '').strip())
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _tab(rng):
    m = re.match(r"^'?([^'!]+)'?!", rng or '')
    return m.group(1) if m else ''


def _row(r, n=10):
    return [('' if x is None else str(x)) for x in r] + [''] * n


def _done(v):
    return v.strip().upper() in ('TRUE', '완료')


def _clean(t):
    t = t.strip()
    return t[2:].strip() if t.startswith('- ') else t


def _key(s):
    return re.sub(r'\s+', '', s).lower()


def load(data):
    todos, meets = [], []
    for vr in data.get('valueRanges', []):
        tab, vals = _tab(vr.get('range')), vr.get('values') or []
        if tab in TODO_TABS:
            date, site = None, ''
            for r in vals[1:]:
                r = _row(r)
                if r[0].strip():
                    date = _d(r[0]) or date
                site = r[6].strip() or r[1].strip() or site
                if not r[2].strip() or not site or _done(r[3]):
                    continue
                todos.append({'tab': tab, 'date': date, 'site': site, 'text': _clean(r[2]), 'pick': r[4].strip()})
        elif tab == '회의록':
            date, site = None, ''
            for r in vals[1:]:
                r = _row(r)
                if len([x for x in r if x.strip()]) <= 1:
                    continue
                if r[0].strip():
                    date = _d(r[0]) or date
                site = r[1].strip() or site
                if not site:
                    continue
                meets.append({'date': date, 'site': site, 'who': r[2].strip(), 'topic': r[3].strip(),
                              'decision': r[5].strip(), 'action': r[6].strip()})
    # 같은 현장·같은 할 일이 여러 탭에 있으면 기한이 있는 쪽(오늘·앞으로)을 남긴다
    seen, uniq = {}, []
    for t in todos:
        k = (t['site'], t['text'])
        if k in seen:
            if t['tab'] != '답요청' and seen[k]['tab'] == '답요청':
                uniq[uniq.index(seen[k])] = t
                seen[k] = t
            continue
        seen[k] = t
        uniq.append(t)
    return uniq, meets


def _due(t):
    return t['date'] if t['tab'] != '답요청' else None


def _md(d):
    return '%d/%d' % (d.month, d.day) if d else '날짜 미상'


def _cut(s, n=46):
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n - 1] + '…'


def overview(todos, meets, today, top=10):
    sites = {}
    for t in todos:
        s = sites.setdefault(t['site'], {'n': 0, 'late': 0, 'next': None, 'meet': None})
        s['n'] += 1
        d = _due(t)
        if d and d < today:
            s['late'] += 1
        elif d and (s['next'] is None or d < s['next']):
            s['next'] = d
    for m in meets:
        s = sites.setdefault(m['site'], {'n': 0, 'late': 0, 'next': None, 'meet': None})
        if m['date'] and (s['meet'] is None or m['date'] > s['meet']):
            s['meet'] = m['date']
    order = sorted(sites.items(), key=lambda kv: (-kv[1]['late'], -(kv[1]['meet'] or datetime.date.min).toordinal(), kv[0]))
    order = [kv for kv in order if kv[1]['n']]
    out = ['현장별 정리 %s · 안 끝난 할 일이 있는 현장 %d곳 (기한 지난 것 많은 순)' % (today.isoformat(), len(order)), '']
    for name, s in order[:top]:
        bits = ['할 일 %d' % s['n']]
        if s['late']:
            bits.append('기한 지남 %d' % s['late'])
        if s['next']:
            bits.append('다음 %s' % _md(s['next']))
        if s['meet']:
            bits.append('회의 %s' % _md(s['meet']))
        out.append('· %s — %s' % (name, ' · '.join(bits)))
    if len(order) > top:
        out.append('(그 밖 %d곳 — 「OO 정리해」 로 물어보세요)' % (len(order) - top))
    return '\n'.join(out) + '\n'


def one(site, todos, meets, today):
    mine = [t for t in todos if t['site'] == site]
    ms = [m for m in meets if m['site'] == site and m['date']]
    out = ['■ %s' % site]
    if ms:
        last = max(m['date'] for m in ms)
        lm = [m for m in ms if m['date'] == last]
        who = next((m['who'] for m in lm if m['who'] and m['who'] != site), '')
        out.append('마지막 회의 %s%s' % (_md(last), (' · ' + _cut(who, 24)) if who else ''))
        shown = 0
        for m in lm:
            dec = m['decision']
            if dec and not dec.startswith('없음'):
                out.append('  · %s — %s' % (_cut(m['topic'], 14), _cut(dec)))
                shown += 1
            if shown == 3:
                break
        if not shown:
            out.append('  · 결정된 것 없음 (안건 : %s)' % _cut(' / '.join(m['topic'] for m in lm[:3]), 40))
    else:
        out.append('회의록 없음')
    late = sorted([t for t in mine if _due(t) and _due(t) < today], key=_due)
    nxt = sorted([t for t in mine if _due(t) and _due(t) >= today], key=_due)
    ask = sorted([t for t in mine if not _due(t)], key=lambda t: t['date'] or datetime.date.min, reverse=True)
    if late:
        out.append('기한 지난 것 %d건' % len(late))
        out += ['  · %s %s' % (_md(_due(t)), _cut(t['text'])) for t in late[:3]]
    if nxt:
        out.append('다음 할 것 %d건' % len(nxt))
        out += ['  · %s %s' % (_md(_due(t)), _cut(t['text'])) for t in nxt[:3]]
    if ask:
        out.append('답 안 한 것 %d건 (최근 회의 것부터)' % len(ask))
        out += ['  · %s %s' % (_md(t['date']), _cut(t['text'])) for t in ask[:3]]
    if not mine:
        out.append('안 끝난 할 일 없음')
    return '\n'.join(out) + '\n'


def by_name(q, todos, meets, today, limit=3):
    names = sorted({t['site'] for t in todos} | {m['site'] for m in meets})
    hit = [n for n in names if _key(q) in _key(n)]
    if not hit:
        return '「%s」 이 들어간 현장이 시트에 없습니다.\n' % q
    out = []
    if len(hit) > 1:
        out.append('「%s」 이 들어간 현장 %d곳 — 따로 보여드립니다 (같은 현장인지는 차장님이 정하세요)' % (q, len(hit)))
        out.append('')
    for n in hit[:limit]:
        out.append(one(n, todos, meets, today))
    if len(hit) > limit:
        out.append('(그 밖 : %s)' % ' · '.join(hit[limit:]))
    return '\n'.join(out).rstrip('\n') + '\n'


def main(argv):
    args, today = [], datetime.date.today()
    i = 1
    while i < len(argv):
        if argv[i] == '--today' and i + 1 < len(argv):
            s = argv[i + 1]
            today = datetime.date(2000 + int(s[:2]), int(s[2:4]), int(s[4:6]))
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if not args:
        print(__doc__)
        return 2
    with io.open(args[0], encoding='utf-8') as f:
        todos, meets = load(json.load(f))
    q = ' '.join(args[1:]).strip()
    sys.stdout.write(by_name(q, todos, meets, today) if q else overview(todos, meets, today))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

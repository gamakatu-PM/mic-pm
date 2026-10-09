# -*- coding: utf-8 -*-
"""
t99_short.py v1 (2026-10-09) — 아침 메일 10줄 요약판 (AI 사용량 0)

차장님 2026-10-09 「니가 보내준 것이 내가 읽기 싫은 타입일 수 있어 — 해결해」 → 「10줄 요약판」 고르심.
t53_daily 가 만든 오늘의정리_<오늘>.txt 와 아침3통_<오늘>.json 을 읽어 짧은 본문만 새로 만든다.
t53_daily 는 건드리지 않는다(전체판은 그대로 만들어지고, 시트도 그대로 쓰인다).

    python t99_short.py <W/out> <오늘YYMMDD>   → W/out/오늘의정리_짧게_<오늘>.txt 를 쓰고 그 경로를 출력
"""
from __future__ import print_function
import io, os, re, sys, json

VERSION = 'v1 2026-10-09'
SHEET = 'https://docs.google.com/spreadsheets/d/1S02QcwHnRNiJJbq3qfSPs9sRtR1UDtTMSUPhLy4_Ckk/edit'
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
HEAD_RE = re.compile(r'^━━ (.+?) ━━')


def sections(text):
    out, name = {}, None
    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if m:
            name = m.group(1).strip()
            out[name] = []
            continue
        if name is not None:
            out[name].append(line)
    return out


def find(secs, prefix):
    for k, v in secs.items():
        if k.startswith(prefix):
            return v
    return []


def items(lines, only_date=None):
    """날짜 줄 → 현장 줄 → '  - 할일' 구조를 (날짜, 현장, 할일) 로 편다. 이어지는 줄(들여쓰기 없는 번호 줄 등)은 버린다."""
    date, site, got, after_blank = '', '', [], True
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            after_blank = True
            continue
        s = line.strip()
        was_blank, after_blank = after_blank, False
        if DATE_RE.match(s) or s == '날짜 미상':
            date, site = s, ''
            continue
        if line.startswith('  - '):
            if site and (only_date is None or date == only_date):
                got.append((date, site, line[4:].strip()))
            continue
        # t53 은 현장 줄 앞에 늘 빈 줄을 둔다 — 빈 줄 없이 붙은 줄은 앞 할 일의 이어지는 줄
        if was_blank and not line.startswith(' ') and not s.startswith('(') and not s.startswith('※'):
            site = s
    return got


def cut(s, n=48):
    return s if len(s) <= n else s[:n - 1] + '…'


def build(txt, meta, today):
    secs = sections(txt)
    iso = '20%s-%s-%s' % (today[:2], today[2:4], today[4:])
    lines = [meta.get('제목', '[KM] 오늘의 정리'), '']
    lines.append('어제 회의 %s건 · 답 안 한 할 일 %s건 · 기한 지난 것 %s건 · 제안서 대기 %s건' % (
        meta.get('어제회의', 0), meta.get('①지난것', 0) + meta.get('①할일', 0),
        meta.get('②기한지난것', 0), meta.get('제안서대기', 0)))
    lines.append('')

    today_items = items(find(secs, '2. 오늘 할 것'), only_date=iso)
    lines.append('■ 오늘 할 것')
    if today_items:
        for _, site, t in today_items[:3]:
            lines.append('  · %s — %s' % (site, cut(t)))
        if len(today_items) > 3:
            lines.append('  (그 밖 %d건은 시트)' % (len(today_items) - 3))
    else:
        lines.append('  · 오늘 기한인 할 일 없음')

    urgent = items(find(secs, '급한 것'))
    lines.append('■ 제일 오래 밀린 것')
    for d, site, t in urgent[:3]:
        lines.append('  · %s %s — %s' % (d[5:].replace('-', '/'), site, cut(t)))
    if not urgent:
        lines.append('  · 없음')

    sites = meta.get('어제_현장별') or {}
    if sites:
        lines.append('■ 어제 회의 : ' + ' · '.join('%s %s' % (k, v) for k, v in sites.items()))

    lines.append('')
    lines.append('전체 목록·체크 : ' + SHEET)
    return '\n'.join(lines) + '\n'


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    out_dir, today = argv[1], argv[2]
    with io.open(os.path.join(out_dir, '오늘의정리_%s.txt' % today), encoding='utf-8') as f:
        txt = f.read()
    with io.open(os.path.join(out_dir, '아침3통_%s.json' % today), encoding='utf-8') as f:
        meta = json.load(f)
    body = build(txt, meta, today)
    path = os.path.join(out_dir, '오늘의정리_짧게_%s.txt' % today)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(body)
    print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

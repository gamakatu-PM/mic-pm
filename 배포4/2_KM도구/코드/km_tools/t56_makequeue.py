# -*- coding: utf-8 -*-
"""
56. 「만들 차례」 탭 → 실제 문서  (km_tools / t56_makequeue)   AI 사용량 0 (제안서는 안 만들고 대기만 남김)

시트 답요청·오늘 할일·앞으로 할일 E열 ▼에서 제안서·보고서·메일·작업의뢰서 를 고르면
웹앱(KM_시트쓰기.gs v7) sweep 이 「만들 차례」 탭으로 옮겨 놓는다. 1시간마다 도는 Routine 이
이 탭을 읽어(t53_webapp.py read) 이 도구를 부르고, 만든 것은 웹앱 markQueue(v8) 로 J열에
적어 다음 시간에 또 안 만든다.

    python t56_makequeue.py <만들차례_읽은결과.json> [--out 폴더] [--template 원틀.xlsx] [--today YYMMDD]
    → 표준출력에 결과 json {made:[...], marks:[...], 제안서대기:N} — marks 를 웹앱 markQueue 로 보낸다

만드는 것 (차장님 확정 2026-09-28 「내가 몰라서 질문하는 경우 말고는 그냥 만들어라」) :
    작업의뢰서 → _도구결과\\작업의뢰서초안\\YYMMDD\\작업의뢰서_대기_{현장}_{날짜}_{n}.xlsx
                 회사 원틀(MB-004, t55 와 같은 것)에 현장·날짜·본문(할일 그대로)만 채운다.
                 부서·업체명·객실수·계약No·체크박스·수량·규격은 비워 둔다 (km-30 확정 : 차장님이 채움)
    메일       → _도구결과\\메일초안\\YYMMDD\\메일초안_{현장}_{n}.txt   보내지 않는다. 초안만
    보고서     → _도구결과\\보고서\\YYMMDD\\보고서_{현장}_{n}.txt       자유 형식
    제안서     → 만들지 않는다 — 범위·장수 등은 판단이 필요해서 대화창에서 직접 여쭤야 한다.
                 「만들 차례」 탭에 그대로 남는다(J열 안 채움). 07:00 메일이나 대화에서 처리.

덮어쓰지 않는다 — 같은 이름 파일이 있으면 「이미 있음」 으로 건너뛰고 그 줄도 markQueue 로 표시한다(또 안 만듦).
없는 말을 지어내지 않는다 — 본문은 시트의 할일 글 그대로 옮긴다.
"""
from __future__ import print_function
import os, sys, io, re, json, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t55_workorder as T55
import common as C

VERSION = 'v1 2026-09-28'


def rows_of(payload):
    """t53_webapp read 결과 {ok, valueRanges:[{range, values}]} 에서 「만들 차례」 값만 꺼낸다."""
    for vr in (payload.get('valueRanges') or []):
        return vr.get('values') or []
    return []


def parse(values):
    """머리줄 빼고 (row번호, 날짜, 현장, 할일, 고르기, 원본탭) 만. J열(10번째)에 이미 값이 있으면(이미 만듦) 건너뛴다."""
    out = []
    for i, r in enumerate(values[1:], start=2):
        r = list(r) + [''] * (10 - len(r))
        date, site, task, _done, pick, _memo, _filt, fromtab, _madeon, markcol = r[:10]
        if str(markcol).strip():
            continue
        pick = str(pick).strip()
        if pick not in ('제안서', '보고서', '메일', '작업의뢰서'):
            continue
        out.append({'row': i, 'ymd10': str(date).strip(), 'site': str(site).strip(),
                     'task': re.sub(r'^\s*-\s*', '', str(task).strip()), 'pick': pick, 'from': str(fromtab).strip()})
    return out


def _ymd6(ymd10):
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', ymd10 or '')
    return (m.group(1)[2:] + m.group(2) + m.group(3)) if m else ''


def _safe(s, n=20):
    s = re.sub(r'[\\/:*?"<>|\s]+', '_', s or '').strip('_')
    return s[:n] or '현장확인'


def make_workorder(item, out_dir, tpl, idx, today6):
    if not tpl:
        return None, '원틀 없음 — 만들지 않음'
    site, task = item['site'], item['task']
    ymd6 = _ymd6(item['ymd10']) or today6
    site_ok = T55.is_site(site)
    name = '작업의뢰서_대기_%s_%s_%d.xlsx' % (_safe(site), ymd6, idx)
    xp = os.path.join(out_dir, name)
    if os.path.exists(xp):
        return xp, '이미 있음'
    lines = [(1, ('%s 현장 아래 작업을 요청 드립니다.' % site) if site_ok else '아래 작업을 요청 드립니다. (현장 확인 필요)'),
             (2, task),
             (None, ' -수량 : [   ]    -규격·사양 : [   ]'),
             (None, '근거 : 26년 회의록2 %s' % (item['from'] or '답요청')),
             (None, '수고하세요.')]
    p = {'rec': {'site': site, 'ymd': ymd6, 'who': ''}, 'site_ok': site_ok, 'dept': '요청', 'key': ''}
    T55.fill_xlsx(tpl, xp, p, lines)
    return xp, '만듦'


def make_text(kind, item, out_dir, idx):
    site, task = item['site'] or '현장 확인', item['task']
    name = '%s_%s_%d.txt' % (kind, _safe(site), idx)
    xp = os.path.join(out_dir, name)
    if os.path.exists(xp):
        return xp, '이미 있음'
    if kind == '메일초안':
        body = '%s 관련 안내드립니다.\n\n%s\n\n감사합니다.\n' % (site, task)
    else:  # 보고서
        body = '%s 보고\n\n일자 : %s\n내용 : %s\n' % (site, item['ymd10'] or datetime.date.today().isoformat(), task)
    with io.open(xp, 'w', encoding='utf-8') as f:
        f.write(body)
    return xp, '만듦'


def run(payload, out_root=None, template=None, today=None):
    today = today or datetime.date.today().strftime('%y%m%d')
    out_root = out_root or C.cfg('out')
    items = parse(rows_of(payload))
    tpl = T55.find_template(template)
    made, marks, skip_prop = [], [], 0
    n = {'작업의뢰서': 0, '메일': 0, '보고서': 0}
    for it in items:
        pick = it['pick']
        if pick == '제안서':
            skip_prop += 1
            continue
        n[pick] += 1
        if pick == '작업의뢰서':
            d = os.path.join(out_root, '작업의뢰서초안', today)
            os.makedirs(d, exist_ok=True)
            path, state = make_workorder(it, d, tpl, n[pick], today)
        elif pick == '메일':
            d = os.path.join(out_root, '메일초안', today)
            os.makedirs(d, exist_ok=True)
            path, state = make_text('메일초안', it, d, n[pick])
        else:
            d = os.path.join(out_root, '보고서', today)
            os.makedirs(d, exist_ok=True)
            path, state = make_text('보고서', it, d, n[pick])
        made.append({'row': it['row'], 'pick': pick, 'site': it['site'], 'task': it['task'],
                      'path': path, 'state': state})
        if path:
            marks.append({'row': it['row'], 'text': '%s · %s' % (state, os.path.basename(path))})
    return {'ok': True, 'tab': '만들 차례', 'made': made, 'marks': marks, '제안서대기': skip_prop, 'out': out_root,
            'today': today, 'template': tpl or ''}   # tab 을 넣어둬서 이 결과 json 을 그대로 t53_webapp.py markqueue 에 먹일 수 있게


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    payload = json.load(io.open(argv[0], encoding='utf-8'))
    opt = {}
    i = 1
    while i < len(argv):
        if argv[i].startswith('--') and i + 1 < len(argv):
            opt[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            i += 1
    rep = run(payload, opt.get('out'), opt.get('template'), opt.get('today'))
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

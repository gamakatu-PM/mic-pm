# -*- coding: utf-8 -*-
"""
56. 「만들 차례」 탭 → 실제 문서·시트  (km_tools / t56_makequeue)   AI 사용량 0 (제안서는 안 만들고 대기만 남김)

시트 답요청·오늘 할일·앞으로 할일 E열 ▼에서 제안서·보고서·메일·작업의뢰서·캘린더 를 고르면
웹앱(KM_시트쓰기.gs v9) sweep 이 「만들 차례」 탭으로 옮겨 놓는다. 1시간마다 도는 Routine 이
이 탭을 읽어(t53_webapp.py read) 이 도구를 부르고, 만든 것은 웹앱 markQueue(v8)·appendDoc(v9) 로
표시해 다음 시간에 또 안 만든다.

    python t56_makequeue.py <만들차례_읽은결과.json> [--out 폴더] [--template 원틀.xlsx] [--today YYMMDD]
    → 표준출력에 결과 json {made, marks, 제안서대기, 캘린더항목, 메일추가, 보고서추가, ...}

만드는 것 (차장님 확정 2026-09-28 「내가 몰라서 질문하는 경우 말고는 그냥 만들어라」) :
    작업의뢰서 → _도구결과\\작업의뢰서초안\\YYMMDD\\작업의뢰서_대기_{현장}_{날짜}_{n}.xlsx
                 회사 원틀(MB-004, t55 와 같은 것)에 현장·날짜·본문(할일 그대로)만 채운다.
                 부서·업체명·객실수·계약No·체크박스·수량·규격은 비워 둔다 (km-30 확정 : 차장님이 채움)
                 결과의 marks 에 바로 들어간다 — 로컬 파일이라 쓰는 순간 끝났기 때문.
    메일       → 파일이 아니라 결과의 「메일추가」 로 — {tab:'메일', rows:[[날짜,현장,할일,본문]], markTab:'만들 차례', marks:[...]}
                 (차장님 2026-09-28 밤 「내가 메일에서 담당을 직접 고를테니 범용으로 정중하게, 구글시트에 메일 탭 만들어서 날짜별 누적」)
                 이 스크립트는 네트워크를 안 쓴다 — Routine 이 그대로 t53_webapp.py appenddoc 에 먹여야 실제로 시트에 들어가고,
                 그때 성공한 것만 원자적으로 「만들 차례」 J열도 같이 표시된다(그래서 marks 에는 안 넣는다 — 넣었는데 시트엔 안 들어가는 사고 방지)
    보고서     → 메일과 같은 방식, 결과의 「보고서추가」 로 (탭 이름만 「보고서」)
    제안서     → 만들지 않는다 — 범위·장수 등은 판단이 필요해서 대화창에서 직접 여쭤야 한다.
                 「만들 차례」 탭에 그대로 남는다(J열 안 채움). 07:00 메일이나 대화에서 처리.
    캘린더     → 이 스크립트가 아니라 Routine(대화창 도구)이 만든다 — 구글캘린더 API 는 MCP 도구라 파이썬에서 못 부른다.
                 결과의 「캘린더항목」 에 {row, site, task, due} 로만 넘긴다. Routine 이 mcp Google_Calendar create_event 를 직접 부르고,
                 성공한 것만 markqueue 로 표시한다(이 스크립트는 등록 성공 여부를 모른다 — marks 에 안 넣는다)
                 (차장님 2026-09-28 밤 「구글캘린더 1개 더 만들어서 "현장관리" 로, 고르기에서 캘린더 고르면 거기 넣어」)

덮어쓰지 않는다 — 작업의뢰서는 같은 이름 파일이 있으면 「이미 있음」. 메일·보고서는 시트에 날짜별로 누적만(겹치는 줄을 지우거나 바꾸지 않는다).
없는 말을 지어내지 않는다 — 본문은 시트의 할일 글 그대로 옮긴다. 메일 본문은 담당을 특정하지 않고 범용·정중체로만 쓴다(받는 사람은 차장님이 고른다).
"""
from __future__ import print_function
import os, sys, io, re, json, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t55_workorder as T55
import common as C

VERSION = 'v2 2026-09-28'  # v2 : 메일·보고서는 로컬 파일 대신 시트 「메일」·「보고서」 탭 누적(메일추가·보고서추가) / 캘린더항목 추가(Routine 이 직접 구글캘린더 등록)


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
        if pick not in ('제안서', '보고서', '메일', '작업의뢰서', '캘린더'):
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


def mail_body(site, task):
    """범용·정중체 — 받는 사람을 특정하지 않는다(차장님이 메일에서 직접 고른다, 2026-09-28 밤 확정). 없는 말은 안 붙인다."""
    return '안녕하십니까,\n\n%s 관련하여 아래와 같이 안내드립니다.\n\n%s\n\n확인 부탁드립니다.\n\n감사합니다.' % (site or '현장 확인', task)


def report_body(site, task, ymd10, today_iso):
    return '%s 보고\n\n일자 : %s\n내용 : %s' % (site or '현장 확인', ymd10 or today_iso, task)


def run(payload, out_root=None, template=None, today=None):
    today = today or datetime.date.today().strftime('%y%m%d')
    today_iso = ('20%s-%s-%s' % (today[:2], today[2:4], today[4:6])) if re.match(r'^\d{6}$', today) else datetime.date.today().isoformat()
    out_root = out_root or C.cfg('out')
    items = parse(rows_of(payload))
    tpl = T55.find_template(template)
    made, marks, skip_prop = [], [], 0
    mail_rows, report_rows, cal_items = [], [], []
    n_wo = 0
    for it in items:
        pick = it['pick']
        if pick == '제안서':
            skip_prop += 1
            continue
        if pick == '캘린더':
            cal_items.append({'row': it['row'], 'site': it['site'], 'task': it['task'], 'due': it['ymd10']})
            continue
        if pick == '작업의뢰서':
            n_wo += 1
            d = os.path.join(out_root, '작업의뢰서초안', today)
            os.makedirs(d, exist_ok=True)
            path, state = make_workorder(it, d, tpl, n_wo, today)
            made.append({'row': it['row'], 'pick': pick, 'site': it['site'], 'task': it['task'],
                         'path': path, 'state': state})
            if path:
                marks.append({'row': it['row'], 'text': '%s · %s' % (state, os.path.basename(path))})
        elif pick == '메일':
            row = [today_iso, it['site'], it['task'], mail_body(it['site'], it['task'])]
            mail_rows.append(row)
            made.append({'row': it['row'], 'pick': pick, 'site': it['site'], 'task': it['task'],
                         'path': '', 'state': '만들 준비(시트 「메일」 탭)'})
        else:  # 보고서
            row = [today_iso, it['site'], it['task'], report_body(it['site'], it['task'], it['ymd10'], today_iso)]
            report_rows.append(row)
            made.append({'row': it['row'], 'pick': pick, 'site': it['site'], 'task': it['task'],
                         'path': '', 'state': '만들 준비(시트 「보고서」 탭)'})

    def _doc_addon(tab, rows, pick_name):
        if not rows:
            return None
        rmarks = [{'row': it['row'], 'text': '만듦(시트) · %s 탭' % tab}
                  for it in items if it['pick'] == pick_name]
        return {'tab': tab, 'rows': rows, 'markTab': '만들 차례', 'marks': rmarks}

    return {'ok': True, 'tab': '만들 차례', 'made': made, 'marks': marks, '제안서대기': skip_prop,
            '캘린더항목': cal_items,
            '메일추가': _doc_addon('메일', mail_rows, '메일'),
            '보고서추가': _doc_addon('보고서', report_rows, '보고서'),
            'out': out_root, 'today': today, 'template': tpl or ''}
    # tab 을 넣어둬서 marks 부분은 그대로 t53_webapp.py markqueue 에, 메일추가·보고서추가 는 그대로 appenddoc 에 먹일 수 있게


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

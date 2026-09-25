# -*- coding: utf-8 -*-
"""
53-4. KM_시트쓰기.gs (앱스 스크립트 웹 앱) 부르기  (km_tools / t53_webapp)  Zapier 0·Make 0

주소·암호는 코드에 넣지 않는다 (공개 저장소). 순서대로 찾는다 :
   1) 환경변수 KM_WEBAPP_URL · KM_TOKEN
   2) 파일 ~/.km_webapp.json  {"url": "...", "token": "..."}   (작업 환경 비밀 칸에 넣어 두면 1)로 온다)

    python t53_webapp.py ping
    python t53_webapp.py read  new2  "'답요청'!A1:G2000" "'오늘 할일'!A1:G2000" "'앞으로 할일'!A1:G2000"  > 시트.json
    python t53_webapp.py read  radar "'구글AI_실행로그'!A1:G1000" "'구글AI_백필_확정'!A1:M1000" "'구글AI_백필_재검토필요'!A1:F1000" > 레이더.json
    python t53_webapp.py batch <시트쓰기_YYMMDD.json>          (t53_daily --write 가 만든 본문 그대로)
    python t53_webapp.py old26 <옛시트_YYMMDD.json>            (t53_old26 가 만든 본문 그대로)
    python t53_webapp.py merge <옛시트_탭이름.json>            (그 안의 "_합치기" [{from,to},…] 를 순서대로 — 차장님 표 그대로, C급 : 차장님 지시 뒤에만)

read 결과는 Zapier batchGet 과 같은 {valueRanges:[{range, values}]} — t53_sheetmd 가 아니라 t53_daily --done/--radar 가 바로 읽는다.
   (values:batchGet 은 셀 「값」을 주므로 병합 아래 칸은 빈칸 → load_board 가 위 값을 내려 쓴다. 체크박스는 TRUE/FALSE 또는 「완료」)
실패하면 종료코드 1 + {"ok": false, "error": …}. 다시 시도하지 않는다 — 07:00 은 「시트 쓰기 못 함」 으로 보고.
"""
from __future__ import print_function
import os, sys, io, json

VERSION = 'v2 2026-09-25'

try:
    from urllib.request import Request, urlopen
except ImportError:                      # py2
    from urllib2 import Request, urlopen


def config():
    url = os.environ.get('KM_WEBAPP_URL', '').strip()
    tok = os.environ.get('KM_TOKEN', '').strip()
    if url and tok:
        return url, tok
    p = os.path.expanduser('~/.km_webapp.json')
    if os.path.isfile(p):
        with io.open(p, 'r', encoding='utf-8') as f:
            d = json.load(f)
        return (d.get('url') or url).strip(), (d.get('token') or tok).strip()
    return url, tok


def call(action, body=None, timeout=120):
    url, tok = config()
    if not url or not tok:
        return {'ok': False, 'error': '웹 앱 주소·암호 없음 (KM_WEBAPP_URL·KM_TOKEN 또는 ~/.km_webapp.json)'}
    payload = dict(body or {})
    payload['action'] = action
    payload['token'] = tok
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        res = urlopen(req, timeout=timeout)          # 웹 앱은 302 → googleusercontent 로 넘어간다 (urllib 가 따라간다)
        txt = res.read().decode('utf-8', 'replace')
    except Exception as e:
        return {'ok': False, 'error': '연결 실패 : %s' % e}
    try:
        return json.loads(txt)
    except ValueError:
        return {'ok': False, 'error': '응답이 JSON 이 아님 (배포 주소·액세스 「모든 사용자」 확인) : ' + txt[:300]}


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    act = argv[1]
    if act == 'ping':
        out = call('ping')
    elif act == 'read':
        out = call('read', {'which': argv[2], 'ranges': argv[3:]})
    elif act in ('batch', 'old26'):
        with io.open(argv[2], 'r', encoding='utf-8') as f:
            body = json.load(f)
        out = call(act, body)
    elif act == 'merge':
        with io.open(argv[2], 'r', encoding='utf-8') as f:
            d = json.load(f)
        merges = [m for m in (d.get('_합치기') or []) if m.get('from') and m.get('to')]
        out = call('oldMerge', {'merges': merges}) if merges else {'ok': False, 'error': '_합치기 가 비어 있음'}
    else:
        out = {'ok': False, 'error': '모르는 명령 : ' + act}
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))

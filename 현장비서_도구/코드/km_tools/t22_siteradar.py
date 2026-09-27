# -*- coding: utf-8 -*-
"""4. 신규 현장 레이더 (수집) - 건축HUB 건축인허가 API 로 객실이 들어가는 신규 허가를 긁는다.
조사(뉴스/발주처)는 사람이나 클로드가 하고, 이 도구는 '수집과 1차 판정'까지만 한다.
API 키는 data.go.kr 에서 받으십시오. 키는 설정.ini 에 넣습니다."""
import os, json, configparser
from common import *

URL = 'https://apis.data.go.kr/1613000/ArchPmsHubService/getApBasisOulnInfo'
KEEP = ('호텔', '리조트', '숙박', '모텔', '관광', '기숙사', '연수원', '생활숙박',
        '산후조리', '실버', '요양', '클럽하우스', '콘도')
SIZE = {'숙박': 1500.0, '단독': 496.0, '클럽하우스': 1000.0, '기타': 500.0}

def apikey():
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        c.read(INI, encoding='utf-8')
        if c.has_option('레이더', 'apikey'):
            return c.get('레이더', 'apikey').strip()
    return ''

def grade(name, use, area):
    txt = '%s %s' % (name or '', use or '')
    if not any(k in txt for k in KEEP):
        return '제외', '객실 용도 아님'
    try:
        a = float(area or 0)
    except Exception:
        a = 0
    lim = SIZE['숙박'] if any(k in txt for k in ('호텔', '리조트', '숙박', '모텔', '관광', '콘도')) else SIZE['기타']
    if a >= lim * 2:
        return '최우선', '%s㎡' % won(a)
    if a >= lim:
        return '검토', '%s㎡' % won(a)
    return '제외', '규모 미달 %s㎡' % won(a)

def fetch(sigungu, ymd, key, rows=100):
    import urllib.request, urllib.parse
    q = urllib.parse.urlencode({'serviceKey': key, 'sigunguCd': sigungu,
                                'startDate': ymd, 'endDate': ymd,
                                'numOfRows': rows, 'pageNo': 1, '_type': 'json'}, safe='%')
    with urllib.request.urlopen(URL + '?' + q, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def run():
    title('4. 신규 현장 레이더 (수집)')
    key = apikey()
    if not key:
        print('API 키가 없습니다.')
        print('1) data.go.kr 에서 "건축HUB 건축인허가" 활용신청 -> 키 발급')
        print('2) 코드\\km_tools\\설정.ini 에 아래를 넣어주십시오')
        print('')
        print('   [레이더]')
        print('   apikey = 여기에_키')
        return
    sig = ask('시군구 코드 (예: 41135 성남분당) > ')
    ymd = ask('허가일자 YYYYMMDD (엔터=어제) > ') or (today().replace(day=max(1, today().day - 1))).strftime('%Y%m%d')
    try:
        js = fetch(sig, ymd, key)
    except Exception as e:
        print('[통신 실패] %s' % e); return
    items = js.get('response', {}).get('body', {}).get('items', {})
    items = items.get('item', []) if isinstance(items, dict) else items
    if isinstance(items, dict):
        items = [items]
    rows = []
    for it in items or []:
        name = it.get('bldNm') or it.get('platPlc') or ''
        use = it.get('mainPurpsCdNm') or ''
        area = it.get('totArea') or 0
        g, why = grade(name, use, area)
        rows.append([g, name, use, area, it.get('platPlc', ''), it.get('archPmsDay', ''), why])
    rows.sort(key=lambda r: {'최우선': 0, '검토': 1, '제외': 2}.get(r[0], 3))
    keep = [r for r in rows if r[0] != '제외']
    print('받은 건수 %s / 볼 것 %s' % (won(len(rows)), won(len(keep))))
    for r in keep[:20]:
        print('  [%s] %s | %s | %s' % (r[0], r[1][:24], r[2][:16], r[6]))
    o = os.path.join(outdir('신규현장레이더'), '레이더_%s_%s.csv' % (sig, ymd))
    write_csv(o, rows, ['판정', '건물명', '용도', '연면적', '주소', '허가일', '근거'])
    log('레이더', '%s %s건' % (sig, len(rows)))
    print('파일 : %s' % o)
    print('* 발주처/시공사/객실수 조사는 이 도구가 하지 않습니다. 목록만 냅니다.')

if __name__ == '__main__':
    run(); pause()

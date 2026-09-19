# -*- coding: utf-8 -*-
"""대장·통화기록 → 앱(공유 저장소) 로 흘려 넣는 연동 스크립트.
   규칙 : 제가 넣는 것은 전부 「추정·진행중」 + 근거에 출처. 확정은 프로님만.
   현장 판정은 이름에 현장명이 들어 있을 때만. 짐작으로 옮기지 않는다."""
import json,csv,io,os,re,hashlib,datetime
F='feed'
def rd(p):
    b=open(os.path.join(F,p),'rb').read()
    for e in ('utf-8-sig','cp949','utf-8'):
        try:return b.decode(e)
        except:pass
    return b.decode('utf-8','replace')
def h36(s):
    v=5381
    for c in s: v=((v<<5)+v+ord(c))&0xffffffff
    d='0123456789abcdefghijklmnopqrstuvwxyz';o=''
    while v: o=d[v%36]+o; v//=36
    return o or '0'
def sid(name): return 's_'+h36(re.sub(r'\s','',name))
TODAY=datetime.date.today().isoformat()

# ── 현장 사전 : 이름 안에 이 말이 있으면 그 현장 (프로님이 고칠 수 있게 근거를 남긴다)
SITES={'연합기숙사':['연합기숙사','일능'],'조선호텔':['조선호텔'],'유한대':['유한대'],
 '양양쏠비치':['쏠비치','권진희'],'전북연수원':['전북연수원'],'앵커호텔':['앵커'],
 '청담PJ':['청담'],'염곡동':['염곡동'],'해운대':['해운대'],'워케이션':['워케이션'],
 '지경리':['지경리'],'고급주택':['고급주택']}
ROLE=[('감리',['감리']),('통신',['통신']),('전기',['전기','파워텍','계전']),('설비',['설비']),
 ('시공사',['건설','이앤씨','E&C','이엔씨']),('인테리어',['디자인','인테리어']),
 ('발주처',['시설팀','호텔']),('협력업체',['도어락','루테크','산와','아이시에스']),
 ('내부',['객실관리','시공팀','부산사무소'])]
def role_of(n):
    for r,ws in ROLE:
        if any(w in n for w in ws):return r
    return '미정'
def site_of(n):
    for s,ws in SITES.items():
        if any(w in n for w in ws):return s
    return ''
def split_name(raw):
    """통화 이름에서 사람 이름·회사를 대충 가른다. 못 가르면 통째로 이름."""
    n=raw.strip()
    m=re.search(r'([가-힣]{2,4})\s*(차장|부장|과장|팀장|소장|대표|이사|전무|상무|프로|파트너|님)',n)
    if m:return m.group(1)+' '+m.group(2).replace('님',''),n
    return n[:12],n

sites={}   # name -> doc
def ensure(name):
    if name not in sites:
        sites[name]={'id':sid(name),'name':name,'rooms':'','due':'','stages':{},'people':[],'facts':[],'req':{},
                     'created':TODAY,'updated':datetime.datetime.utcnow().isoformat()+'Z','from':'클로드 연동'}
    return sites[name]

# 1) 통화 기록 → 현장 · 담당자 (전화번호 포함)
book=json.load(open(os.path.join(F,'book.json'),encoding='utf-8'))
unassigned=[]
for cnt,sec,raw,tel,first,last in book:
    if not raw or raw.startswith('(이름'):continue
    sn=site_of(raw)
    nm,full=split_name(raw)
    p={'role':role_of(raw),'name':nm,'org':full,'phone':tel,'calls':cnt,'last':last[:10],'from':'녹취 통화기록 260918'}
    if sn: ensure(sn)['people'].append(p)
    else: unassigned.append(p)

# 2) 확정 대장 → 확정값(facts). 상태는 「확정」 이지만 프로님이 이미 확정하신 값이므로 그대로.
rows=list(csv.DictReader(io.StringIO(rd('확정사항.csv'))))
FACT2REQ={'CB외함 최단 납품일':('외함/외함납기','추정'),'CB외함 출고 조건':('계약/계약완료','진행중'),
 '계약 형태':('계약/계약형태','확정'),'타공도 송부 이력':('외함설치/타공도','진행중'),
 '도어락 인증':('기구물제작/기구물수량','진행중'),'전력계량기 설치비':('계약/수량표','진행중'),
 '온도조절기 삭제 대상':('계약/수량표','진행중'),'별동 신축 구성':('설계/등급객실','추정'),
 '32실 기존 구성':('설계/등급객실','추정'),'바닥난방 운용':('결선/강전일정','추정'),
 '32실 온도조절기':('계약/수량표','진행중')}
for r in rows:
    sn=(r.get('현장') or '').strip()
    if not sn:continue
    s=ensure(sn)
    f={'date':r.get('일자',''),'item':r.get('항목',''),'value':r.get('값',''),'basis':r.get('근거','')}
    if not any(x['item']==f['item'] for x in s['facts']):s['facts'].append(f)
    m=FACT2REQ.get(f['item'])
    if m:
        k,st=m
        cur=s['req'].get(k)
        if not cur or cur.get('state')!='확정':
            s['req'][k]={'state':st,'value':f['value'][:90],'basis':f['basis']+' · 확정대장',
                         'date':f['date'],'ts':datetime.datetime.utcnow().isoformat()+'Z','from':'클로드 연동'}

# 3) 견적 발송 → 견적 열쇠 (예시 줄은 건너뜀)
try:
    for r in csv.DictReader(io.StringIO(rd('견적발송.csv'))):
        sn=(r.get('현장') or '').strip()
        if not sn or sn.startswith('예)'):continue
        s=ensure(sn);s['req']['계약/견적발송']={'state':'진행중','value':r.get('보낸날',''),'basis':'견적발송 대장','date':TODAY,'from':'클로드 연동'}
except Exception as e:pass

out={'sites':sites,'unassigned':unassigned}
json.dump(out,open('feed_out.json','w',encoding='utf-8'),ensure_ascii=False)
print('현장',len(sites),'곳')
for n,s in sorted(sites.items(),key=lambda x:-len(x[1]['people'])):
    print(f"  {n:<10} 담당자 {len(s['people']):>2} · 확정값 {len(s['facts']):>2} · 열쇠 {len(s['req']):>2}")
print('현장 미배정 연락처',len(unassigned),'명')

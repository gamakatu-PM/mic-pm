# -*- coding: utf-8 -*-
"""회의록 기준 연동 2판 : 현장 32곳 · 조용한 현장 · 후속 끊긴 분 · 할 일↔단계 연결"""
import json,re,html,os,datetime,glob
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
def sid(n): return 's_'+h36(re.sub(r'\s','',n))
NOW=datetime.datetime.utcnow().isoformat()+'Z'; TODAY=datetime.date.today()
H=rd('뽑은것.html')
def sect(n):
    m=re.search(r'<h2[^>]*>\s*'+n+r'(.*?)(?=<h2|</body)',H,re.S);return m.group(1) if m else ''
def rows(s):
    out=[]
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',s,re.S):
        c=[html.unescape(re.sub(r'<[^>]*>','',x)).strip() for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',tr,re.S)]
        if c: out.append(c)
    return out

# ── 현장 32곳 (통화 건수·마지막·안 한 지)
sites={}
for r in rows(sect(r'2\. 현장 32곳'))[1:]:
    if len(r)<6: continue
    raw=r[0]
    if '·' in raw and len(raw)>30:            # 「각 1건씩」 묶음 줄 → 하나씩 쪼갠다
        for nm in re.split(r'\s*·\s*',raw):
            nm=nm.strip()
            if nm: sites[nm]={'calls':1,'mins':'','last':'','idle':'','who':'신규·검토 단계','group':1}
        continue
    if '/' in raw and len(raw)>20:
        for nm in re.split(r'\s*/\s*',raw):
            nm=nm.strip()
            if nm: sites[nm]={'calls':'','mins':'','last':r[3],'idle':r[4],'who':r[5],'group':1}
        continue
    nm=re.sub(r'\s*\([^)]*\)','',raw).strip()
    sites[nm]={'calls':r[1],'mins':r[2],'last':r[3],'idle':r[4],'who':r[5],'alias':raw}
# ── 후속 끊긴 분 14명
drops=[]
for r in rows(sect(r'5\. 놓치고 계신 것'))[1:]:
    if len(r)>=4: drops.append({'idle':r[0],'name':r[1],'history':r[2],'about':r[3]})
# ── 할 일 ↔ 공정 단계 연결 (회의록에서 나온 할 일이 어느 단계의 것인가)
QMAP=[
 (r'타공도|외함 설치|설치 업체','외함설치'),
 (r'CB\s*외함|외함|석고','외함'),
 (r'도어락|승인원|인증서|자재승인','기구물제작'),
 (r'수량|계량기|감액|증감|견적|계약|네고','계약'),
 (r'도면|설계|카톡본|메일본|Rev','설계'),
 (r'속판|배선도|모듈','속판'),
 (r'결선|강전|약전|커버','결선'),
 (r'벽지|빽커버|기구물 설치','설치'),
 (r'시운전|하자|계산서|수금|중도금','시운전'),
]
def quest_of(t):
    for pat,q in QMAP:
        if re.search(pat,t): return q
    return ''
items={}
for f in glob.glob('seed/items__*.json'):
    d=json.load(open(f,encoding='utf-8'))
    q=quest_of((d.get('text','')+' '+d.get('makeq','')+' '+d.get('memo','')))
    if q: d['quest']=q
    d['updated']=NOW
    items[d['id']]=d
# ── 기존 현장 문서(담당자·열쇠) 이어받기
old={}
for f in glob.glob('seed3/sites__*.json'):
    d=json.load(open(f,encoding='utf-8'));old[d['name']]=d
EXIST={'연합기숙사':'s_ywy8dv','양양쏠비치':'s_uqoaw3'}
out={}
for name,info in sites.items():
    o=old.get(name,{})
    _id=EXIST.get(name) or o.get('id') or sid(name)
    doc={'id':_id,'name':name,'rooms':o.get('rooms',''),'due':o.get('due',''),
         'people':o.get('people',[]),'facts':o.get('facts',[]),'req':o.get('req',{}),
         'calls':info.get('calls',''),'lastCall':info.get('last',''),'idleDays':info.get('idle',''),
         'mainWho':info.get('who',''),'alias':info.get('alias',''),
         'updated':NOW,'created':o.get('created',str(TODAY)),'from':'녹취 분석 260918 · 현장 32곳'}
    out[name]=doc
for name,o in old.items():                    # 32곳 표에 없는 기존 현장도 유지
    if name not in out: out[name]=o
print('현장',len(out),'곳 / 할 일',len(items),'중 단계 연결',sum(1 for i in items.values() if i.get('quest')))
os.makedirs('seed4',exist_ok=True)
writes=[]
for name,d in out.items():
    fn=f"seed4/sites__{d['id']}.json";json.dump(d,open(fn,'w',encoding='utf-8'),ensure_ascii=False)
    writes.append({'op':'set','collection':'sites','doc_id':d['id'],'file_path':os.path.abspath(fn)})
for i in items.values():
    fn=f"seed4/items__{i['id']}.json";json.dump(i,open(fn,'w',encoding='utf-8'),ensure_ascii=False)
    writes.append({'op':'set','collection':'items','doc_id':i['id'],'file_path':os.path.abspath(fn)})
json.dump({'lines':drops,'ts':NOW},open('seed4/meta__drops.json','w',encoding='utf-8'),ensure_ascii=False)
writes.append({'op':'set','collection':'meta','doc_id':'drops','file_path':os.path.abspath('seed4/meta__drops.json')})
json.dump(writes,open('writes4.json','w',encoding='utf-8'),ensure_ascii=False)
print('문서',len(writes),'개 / 끊긴 분',len(drops))
for n,d in list(out.items())[:12]:
    print(f"  {n:<14} 통화 {str(d['calls']):>3} · 마지막 {d['lastCall'] or '—':<6} · 쉰 {d['idleDays'] or '—':<5} · 담당 {len(d['people'])}")

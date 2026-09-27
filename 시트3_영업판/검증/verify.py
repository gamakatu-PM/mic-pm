import json, openpyxl, datetime as dt, re
J=json.load(open("stress.json")); rows=J["rows"]
TODAY=dt.date(2026,9,27); MINA=1500; REV=14; REG="경기도"
kw=["숙박","호텔","리조트","콘도","기숙사","수련","연수","노유자","실버","스테이"]
stg=[("착공전","설계사"),("설계","설계사"),("인허가","설계사"),("허가","설계사"),("착공","시공사"),("골조","시공사"),("마감","늦음"),("준공","늦음")]
def area(x):
    x=str(x).replace(",","").replace("㎡","")
    try: return float(x)
    except: return None
def pdate(x):
    x=str(x)
    if not x: return None
    if len(x)==8 and x.isdigit(): return dt.date(int(x[:4]),int(x[4:6]),int(x[6:]))
    return dt.date.fromisoformat(x.replace(".","-"))
recs=[]
for r in rows:
    _,name,addr,use,ar,_,st,pd,cd,_,d,_,_=r
    recs.append(dict(key=addr+"|"+name,name=name,addr=addr,use=use,area=area(ar),st=st,pd=pdate(pd),cd=cd,d=re.sub(" ","",d.replace("(주)","").replace("㈜","").replace("주식회사",""))))
tgt=[]
for i,x in enumerate(recs):
    if any(y["key"]==x["key"] for y in recs[i+1:]): continue
    if not any(k in x["use"]+" "+x["name"] for k in kw): continue
    if x["area"] is not None and x["area"]<MINA: continue
    dest=None
    for k,v in stg:
        if k in x["st"]: dest=v; break
    if dest is None: dest="설계사" if x["cd"]=="" else "시공사"
    x["dest"]=dest; tgt.append(x)
names=[]
for x in tgt:
    if x["d"] and x["d"] not in names: names.append(x["d"])
visits=[(dt.date.fromisoformat(a),b,h,dt.date.fromisoformat(f) if f else None) for a,b,h,f in J["visits"]]
exp={}
for n in names:
    xs=[x for x in tgt if x["d"]==n]
    D=sum(x["dest"]=="설계사" for x in xs); E=sum(x["dest"]=="시공사" for x in xs)
    F=max([x["area"] or 0 for x in xs])
    rep=next((x for dd in("설계사","시공사","늦음") for x in xs if x["dest"]==dd),None)
    sido=rep["addr"].split(" ")[0]
    vs=[v for v in visits if v[1]==n]
    L=max(v[0] for v in vs) if vs else None
    N=max([v[3] for v in vs if v[3]],default=None)
    O=next(v[2] for v in vs if v[0]==L) if vs else None
    M=(TODAY-L).days if L else None
    P="제외" if O=="관심 없음" else ("안 가봄" if not L else (f"{M}일 지남" if M>=REV else "최근 방문"))
    Q=None
    if P!="제외" and sido==REG:
        if N and N>L and N<=TODAY+dt.timedelta(7): Q=100+7-(N-TODAY).days
        elif D>0 and (P=="안 가봄" or P.endswith("지남")): Q=D*10+(30 if not L else min(M,60)/2)+min(F/1000,20)
    exp[n]=(len(xs),D,E,F,rep["name"],sido,P,Q)
wb=openpyxl.load_workbook("out/big.xlsx",data_only=True); g=wb["3.설계사"]
got={}; order=[]
for r in range(4,304):
    n=g.cell(r,2).value
    if not n: continue
    order.append(n)
    c=[g.cell(r,k).value for k in range(3,19)]
    got[n]=(c[0],c[1],c[2],c[3],c[5],c[6],c[13],c[14] if c[14] not in("",None) else None)
bad=0
for n in names:
    e=exp[n]; a=got.get(n)
    if a is None or any((abs(x-y)>1e-9 if isinstance(x,(int,float)) and isinstance(y,(int,float)) else x!=y) for x,y in zip(e,a)):
        bad+=1; print("DIFF",n,e,a)
print("설계사 수 기대",len(names),"시트",len(got),"순서일치",order==names,"불일치",bad)
ranked=sorted([(q,-names.index(n),n) for n,(*_,q) in exp.items() if q is not None],reverse=True)
exp5=[n for *_,n in ranked][:30]
w=wb["5.이번주_갈곳"]; got5=[w.cell(r,2).value for r in range(4,34) if w.cell(r,2).value]
print("5번 탭 기대",len(exp5),"시트",len(got5),"순서일치",exp5==got5)
print(w["A1"].value); print(w["C4"].value if got5 else "")
d=wb["0.자가진단"]
for r in range(4,14): print(d.cell(r,1).value,d.cell(r,2).value,d.cell(r,3).value,d.cell(r,4).value)

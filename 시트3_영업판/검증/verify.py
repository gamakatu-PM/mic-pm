# v2 : 시트 계산값 ↔ 파이썬 독립 계산 대조. 사용 : python3 verify.py 재계산된.xlsx 원본.xlsx.json
import json, openpyxl, datetime as dt, re, sys
X, JS = sys.argv[1], sys.argv[2]
J = json.load(open(JS)); rows = J["rows"]
TODAY = dt.date.today(); MINA = 1500; REV = 14; REG = "경기도"; STAR = 4000; DRIFT = 1200; RECENT = 6
W = dict(design=10, recent=6, old=2, late=0, star=5, new=30, day=0.5, area=1, appt=100)
kw = ["숙박", "호텔", "리조트", "콘도", "기숙사", "수련", "연수", "노유자", "실버", "스테이"]
stg = [("착공전", "설계사"), ("설계", "설계사"), ("인허가", "설계사"), ("허가", "설계사"), ("착공", "시공사"), ("골조", "시공사"), ("마감", "늦음"), ("준공", "늦음")]
def area(x):
    try: return float(str(x).replace(",", "").replace("㎡", ""))
    except: return None
def pdate(x):
    x = str(x)
    if not x: return None
    if len(x) == 8 and x.isdigit(): return dt.date(int(x[:4]), int(x[4:6]), int(x[6:]))
    return dt.date.fromisoformat(x.replace(".", "-"))
norm = lambda s: re.sub(" ", "", s.replace("(주)", "").replace("㈜", "").replace("주식회사", ""))
recs = []
for r in rows:
    _, name, addr, use, ar, _, st, pd, cd, _, d, c, _ = r
    recs.append(dict(key=addr + "|" + name, name=name, addr=addr, use=use, area=area(ar), st=st, pd=pdate(pd), cd=pdate(cd), d=norm(d), c=norm(c)))
tgt = []; judge = {"★": 0, "△": 0, "✕": 0}
for i, x in enumerate(recs):
    if any(y["key"] == x["key"] for y in recs[i + 1:]): continue
    ok = any(k in x["use"] + " " + x["name"] for k in kw) and not (x["area"] is not None and x["area"] < MINA)
    if not ok: judge["✕"] += 1; continue
    drift = (x["pd"] and x["cd"] and (x["cd"] - x["pd"]).days > DRIFT) or (x["pd"] and not x["cd"] and (TODAY - x["pd"]).days > DRIFT)
    x["j"] = "△" if drift or (x["area"] is not None and x["area"] < STAR) else "★"; judge[x["j"]] += 1
    dest = next((v for k, v in stg if k in x["st"]), None) or ("설계사" if not x["cd"] else "시공사")
    x["dest"] = dest
    sc = {"설계사": W["design"], "늦음": W["late"]}.get(dest)
    if sc is None: sc = W["recent"] if (not x["cd"] or (TODAY - x["cd"]).days <= RECENT * 30.4) else W["old"]
    x["score"] = sc + (W["star"] if x["j"] == "★" else 0)
    tgt.append(x)
names = []
for x in tgt:
    if x["d"] and x["d"] not in names: names.append(x["d"])
visits = [(dt.date.fromisoformat(a), b, h, dt.date.fromisoformat(f) if f else None) for a, b, h, f in J["visits"]]
exp = {}
for n in names:
    xs = [x for x in tgt if x["d"] == n]
    D = sum(x["dest"] == "설계사" for x in xs); E = sum(x["dest"] == "시공사" for x in xs); F = sum(x["j"] == "★" for x in xs)
    G = sum(x["score"] for x in xs); H = max([x["area"] or 0 for x in xs])
    rep = next((x for dd in ("설계사", "시공사", "늦음") for x in xs if x["dest"] == dd))
    sido = rep["addr"].split(" ")[0]
    vs = [v for v in visits if v[1] == n]
    L = max(v[0] for v in vs) if vs else None
    Nn = max([v[3] for v in vs if v[3]], default=None)
    O = next(v[2] for v in vs if v[0] == L) if vs else None
    M = (TODAY - L).days if L else None
    P = "제외" if O == "관심 없음" else ("안 가봄" if not L else (f"{M}일 지남" if M >= REV else "최근 방문"))
    Q = None
    if P != "제외" and sido == REG:
        if Nn and Nn > L and Nn <= TODAY + dt.timedelta(7): Q = W["appt"] + 7 - (Nn - TODAY).days
        elif G > 0 and (P == "안 가봄" or P.endswith("지남")): Q = G + (W["new"] if not L else min(M, 60) * W["day"]) + min(H / 1000 * W["area"], 20)
    exp[n] = (len(xs), D, E, F, G, H, rep["name"], sido, P, Q)
wb = openpyxl.load_workbook(X, data_only=True); g = wb["3.설계사"]
got = {}; order = []
for r in range(4, 304):
    n = g.cell(r, 2).value
    if not n: continue
    order.append(n); c = [g.cell(r, k).value for k in range(1, 22)]
    got[n] = (c[2], c[3], c[4], c[5], c[6], c[7], c[10], c[11], c[18], c[19] if c[19] not in ("", None) else None)
def neq(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)): return abs(a - b) > 1e-6
    return a != b
bad = [n for n in names if got.get(n) is None or any(neq(a, b) for a, b in zip(exp[n], got[n]))]
for n in bad[:5]: print("DIFF", n, exp[n], got.get(n))
print(f"설계사 기대 {len(names)} / 시트 {len(got)} / 순서일치 {order == names} / 불일치 {len(bad)}")
ranked = sorted([(q, -names.index(n), n) for n, (*_, q) in exp.items() if q is not None], reverse=True)
exp5 = [n for *_, n in ranked][:30]
w = wb["5.이번주_갈곳"]; got5 = [w.cell(r, 2).value for r in range(4, 34) if w.cell(r, 2).value]
print(f"5번 기대 {len(exp5)} / 시트 {len(got5)} / 순서일치 {exp5 == got5}")
h = wb["2.현장"]; gj = {"★": 0, "△": 0, "✕": 0}
for r in range(2, 1002):
    vv = h.cell(r, 27).value
    if vv in gj: gj[vv] += 1
print(f"판정 기대 {judge} / 시트 {gj} / 일치 {judge == gj}")
cs = []
for x in tgt:
    if x["c"] and x["c"] not in cs: cs.append(x["c"])
c3 = wb["3b.시공사"]; gc = [c3.cell(r, 2).value for r in range(4, 204) if c3.cell(r, 2).value]
cnt_ok = all(c3.cell(4 + i, 3).value == sum(1 for x in tgt if x["c"] == n) for i, n in enumerate(gc))
print(f"시공사 기대 {len(cs)} / 시트 {len(gc)} / 순서일치 {cs == gc} / 현장수일치 {cnt_ok}")
d = wb["0.자가진단"]
print("자가진단:", [(d.cell(r, 1).value, d.cell(r, 4).value) for r in range(4, 17)])
ok = not bad and order == names and exp5 == got5 and judge == gj and cs == gc and cnt_ok
print("종합:", "통과" if ok else "실패")

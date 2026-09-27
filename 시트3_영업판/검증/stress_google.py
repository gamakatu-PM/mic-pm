# 구글판 시험 : 합성 데이터 + 방문기록 + 검증 탭을 넣은 xlsx 를 만든다 (구글에 올려 검증 탭 CSV 를 받아 verify_google.py 로 대조)
import random, openpyxl, datetime as dt, subprocess, json, sys
OUT = sys.argv[1]; NROW = int(sys.argv[2]) if len(sys.argv) > 2 else 120
random.seed(23)
subprocess.run(["python3", "/home/user/mic-pm/시트3_영업판/build_sheet3_google.py", OUT, "--no-seed", "--verify-tab"], check=True)
wb = openpyxl.load_workbook(OUT)
p = wb["1.산군_붙여넣기"]
for c in range(1, 20): p.cell(1, c).value = None
hdr = ["번호", "건축물명", "현장 주소", "주용도", "연면적(㎡)", "허가구분", "공사단계", "허가일자", "착공일자", "건축주", "설계사무소", "시공사", "감리"]
for i, h in enumerate(hdr): p.cell(1, i + 1, h)
s = wb["설정"]
for r, v in zip(range(4, 16), ["현장 주소", "건축물명", "연면적(㎡)", "주용도", "허가구분", "설계사무소", "시공사", "감리", "건축주", "공사단계", "허가일자", "착공일자"]): s.cell(r, 2, v)
s["B21"] = "경기도"
sido = ["서울특별시", "경기도", "부산광역시", "강원특별자치도"]
uses = ["숙박시설", "업무시설", "교육연구시설(기숙사)", "공동주택", "숙박시설(생활숙박시설)", "수련시설"]
stages = ["건축허가", "착공", "골조공사", "설계", "준공", "마감공사", ""]
des = [f"테스트{i}건축" for i in range(25)]; cons = [f"시공{i}" for i in range(10)]
rows = []
for i in range(NROW):
    st = random.choice(stages)
    pd = dt.date(random.choice([2021, 2023, 2025, 2026]), random.randint(1, 9), random.randint(1, 28))
    cdd = None if st in ("건축허가", "설계", "") and random.random() < 0.8 else dt.date(2026, random.randint(1, 9), 15)
    cd = "" if cdd is None else cdd.strftime("%Y.%m.%d")
    d = random.choice(des)
    if random.random() < 0.2: d = "(주)" + d
    if random.random() < 0.05: d = ""
    c = random.choice(cons) if cd and random.random() < 0.7 else ""
    rows.append([i + 1, f"T현장{random.randint(1,60)}", f"{random.choice(sido)} 테스트구 {random.randint(1,40)}", random.choice(uses),
                 random.choice([800, 1500, 2400, "3,100", 5200, 12000, "45,000㎡", ""]), "신축", st,
                 pd.strftime("%Y%m%d") if i % 3 == 0 else pd.isoformat(), cd, "주", d, c, "감리"])
for r, row in enumerate(rows):
    for c, v in enumerate(row): p.cell(r + 2, c + 1, v)
v = wb["4.방문기록"]
visits = [(dt.date(2026, 9, 25), "테스트3건축", "재방문", None), (dt.date(2026, 8, 1), "테스트5건축", "부재", None),
          (dt.date(2026, 9, 1), "테스트7건축", "관심 없음", None), (dt.date(2026, 9, 20), "테스트9건축", "재방문", dt.date(2026, 9, 30)),
          (dt.date(2026, 9, 2), "시공3", "재방문", None)]
for i, (a, b, h, f) in enumerate(visits):
    v.cell(3 + i, 1, a); v.cell(3 + i, 2, b); v.cell(3 + i, 8, h)
    if f: v.cell(3 + i, 6, f)
wb.save(OUT)
json.dump({"rows": rows, "visits": [[a.isoformat(), b, h, f.isoformat() if f else None] for a, b, h, f in visits]}, open(OUT + ".json", "w"), ensure_ascii=False)

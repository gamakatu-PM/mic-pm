# 시트3 영업판 빌더 — 산군 엑셀 → 설계사별 집계 → 이번 주 갈 곳 (수식만, 매크로 없음)
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

VER = "v1"; TODAY = "2026-09-27"
N = 1000            # 붙여넣기 최대 줄 수
R2 = N + 1          # 2.현장 마지막 행
DS = 300            # 설계사 최대 수
VR = 500            # 방문기록 줄 수
WITH_EXAMPLE = "--no-example" not in sys.argv
OUT = sys.argv[1]

HF = PatternFill("solid", fgColor="1F3864"); HFont = Font(bold=True, color="FFFFFF")
IN = PatternFill("solid", fgColor="FFF2CC")   # 입력칸 노랑
AUTO = PatternFill("solid", fgColor="E2EFDA") # 자동 초록
GR = PatternFill("solid", fgColor="EDEDED")
T = Font(bold=True, size=14); B = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical="top")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
DATE = "yyyy-mm-dd"

wb = Workbook()
def sheet(name, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = name; return ws
def hdr(ws, row, labels, col=1):
    for i, l in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=l); c.fill = HF; c.font = HFont
        c.alignment = Alignment(wrap_text=True, vertical="center"); c.border = BOX
def widths(ws, ws_w):
    for k, v in ws_w.items(): ws.column_dimensions[k].width = v

P1 = "'1.산군_붙여넣기'"; P2 = "'2.현장'"; P3 = "'3.설계사'"; P4 = "'4.방문기록'"; ST = "설정"; MEMO = "설계사_메모"

# ---------------- 사용법 ----------------
u = sheet("사용법", first=True)
u["A1"] = f"시트 3번 「영업판」 {VER} ({TODAY}) — 산군 + 설계사 영업 전용"; u["A1"].font = T
lines = [
 "■ 프로님 손은 1번 : 매주 월요일 산군 엑셀을 받아 「1.산군_붙여넣기」 탭 A1 칸을 누르고 통째로 붙여넣기(전체 덮어쓰기).",
 "   → 2.현장 · 3.설계사 · 5.이번주_갈곳 · 7.문안 · 6.본전계산 이 저절로 바뀝니다.",
 "■ 처음 한 번만 : 「설정」 탭 B4~B15 에 산군 엑셀 1행의 열 이름을 똑같이 적기(지금은 짐작값). 「0.자가진단」 1번이 「통과」 면 끝.",
 "■ 다녀오시면 : 「4.방문기록」 에 한 줄(날짜·설계사무소·결과). 결과를 「관심 없음」 으로 고르면 그 사무소는 갈 곳 목록에서 빠집니다.",
 "■ 담당자·전화를 알게 되면 : 「설계사_메모」 에 한 줄. 3·5·7번 탭에 저절로 붙습니다.",
 "■ 전화·메일 문안 : 「7.문안」 B3 에서 설계사무소를 고르면 전화 첫마디·문자·메일 제목·본문이 채워집니다. 복사해서 쓰시면 됩니다.",
 "■ 노란 칸 = 프로님 입력칸 / 초록 칸 = 자동(건드리지 않음).",
 "■ 누구를 만나나 : 산군 공사단계가 허가·설계 단계 → 설계사무소(객실관리를 설계에 넣게) / 착공 이후 → 시공사 / 마감·준공 → 늦음.",
 "■ 예시 줄 : [예시] 가 붙은 줄은 동작을 보여 드리려고 넣은 가짜입니다. 산군 엑셀을 붙여넣으면 자동으로 사라집니다(방문기록 예시 1줄은 직접 지우기).",
 "■ 이 시트는 회의록·견적·공정·수금과 섞지 않습니다. 기존 레이더·도구 47번과도 따로입니다(계획서 9절).",
 "■ 바꿀 때는 덮어쓰지 않고 새 판(v2)으로 냅니다. 변경 이력은 「0.자가진단」 아래에 있습니다.",
]
for i, l in enumerate(lines): u.cell(row=3 + i, column=1, value=l).alignment = WRAP
widths(u, {"A": 120})

# ---------------- 0.자가진단 ----------------
d = sheet("0.자가진단")

# ---------------- 1.산군_붙여넣기 ----------------
p = sheet("1.산군_붙여넣기")
raw_hdr = ["현장주소", "건물명", "연면적", "주용도", "허가구분", "공사단계", "허가일", "착공일", "건축주", "설계사", "시공사", "감리"]
for i, h in enumerate(raw_hdr): p.cell(row=1, column=i + 1, value=h).font = B
if WITH_EXAMPLE:
    ex = [
     ["서울특별시 중구 예시동 1", "[예시]가나호텔", "12,500", "숙박시설(관광호텔)", "신축", "건축허가", "2026-08-12", "", "[예시]가나개발", "[예시]가나건축사사무소", "", ""],
     ["서울특별시 강남구 예시동 2", "[예시]다라호텔", "8400", "숙박시설", "신축", "착공", "2026-03-02", "2026-07-01", "[예시]다라산업", "(주)[예시]가나건축사사무소", "[예시]마바건설", "[예시]감리"],
     ["강원특별자치도 양양군 예시리 3", "[예시]사아리조트", "31,000", "숙박시설(콘도)", "신축", "설계", "2026-09-01", "", "[예시]사아레저", "[예시]사아종합건축사사무소", "", ""],
     ["경기도 이천시 예시동 4", "[예시]자차기숙사", "22000", "교육연구시설(기숙사)", "신축", "건축허가", "2026-07-20", "", "[예시]자차", "[예시]카타건축", "", ""],
     ["경기도 성남시 예시동 5", "[예시]파하오피스", "40000", "업무시설", "신축", "건축허가", "2026-06-01", "", "[예시]파하", "[예시]가나건축사사무소", "", ""],
     ["부산광역시 해운대구 예시동 6", "[예시]거너호텔", "900", "숙박시설", "신축", "건축허가", "2026-05-01", "", "[예시]거너", "[예시]거너건축", "", ""],
     ["서울특별시 중구 예시동 1", "[예시]가나호텔", "12,500", "숙박시설(관광호텔)", "신축", "건축허가", "2026-08-12", "", "[예시]가나개발", "[예시]가나건축사사무소", "", ""],
    ]
    for r, row in enumerate(ex):
        for c, v in enumerate(row): p.cell(row=2 + r, column=c + 1, value=v)
widths(p, {chr(65 + i): 16 for i in range(12)})

# ---------------- 설정 ----------------
s = sheet(ST)
s["A1"] = "설정 — 노란 칸만 고치십시오"; s["A1"].font = T
hdr(s, 3, ["항목", "산군 엑셀의 열 이름(1행 글자 그대로)", "찾은 열 번호", "상태"])
fields = ["주소", "건물명", "연면적", "주용도", "허가구분", "설계사", "시공사", "감리", "건축주", "공사단계", "허가일", "착공일"]
guess = {"주소": "현장주소", "건물명": "건물명", "연면적": "연면적", "주용도": "주용도", "허가구분": "허가구분", "설계사": "설계사",
         "시공사": "시공사", "감리": "감리", "건축주": "건축주", "공사단계": "공사단계", "허가일": "허가일", "착공일": "착공일"}
FROW = {}
for i, f in enumerate(fields):
    r = 4 + i; FROW[f] = r
    s.cell(row=r, column=1, value=f)
    c = s.cell(row=r, column=2, value=guess[f]); c.fill = IN
    s.cell(row=r, column=3, value=f'=IFERROR(MATCH(B{r},{P1}!$1:$1,0),"")').fill = AUTO
    s.cell(row=r, column=4, value=f'=IF(C{r}="","못 찾음 — B칸을 산군 엑셀 1행 글자와 똑같이","정상")').fill = AUTO
s["A18"] = "숫자 입력칸"; s["A18"].font = B
nums = [("연면적 최소(㎡) — 이보다 작으면 제외", 1500, "신규 현장 레이더 숙박 기준(프로님 확정값)을 기본값으로"),
        ("재방문 간격(일)", 14, "0번 목록 32 「다녀오신 지 14일」"),
        ("이번 주 지역(비우면 전국) — 시·도 첫 단어, 예: 서울특별시", None, "5번 탭을 이 지역만 보기"),
        ("산군 월 요금(원)", 90000, "2026-09-27 검색 확인"),
        ("산군 사용 시작일", None, "넣으시면 6.본전계산이 누적 비용을 냅니다"),
        ("오늘 날짜", "=TODAY()", "자동"),
        ("산군 연결제 금액(원)", 864000, "2026-09-27 검색 확인(연 20% 할인)")]
for i, (k, v, note) in enumerate(nums):
    r = 19 + i
    s.cell(row=r, column=1, value=k); c = s.cell(row=r, column=2, value=v)
    c.fill = AUTO if k == "오늘 날짜" else IN
    s.cell(row=r, column=3, value=note).font = Font(italic=True, color="808080")
s["B23"].number_format = DATE; s["B24"].number_format = DATE
s["B22"].number_format = "#,##0"; s["B25"].number_format = "#,##0"
s["A27"] = "대상 용도 키워드(주용도·건물명에 이 글자가 있으면 대상) — 10칸"; s["A27"].font = B
kw = ["숙박", "호텔", "리조트", "콘도", "기숙사", "수련", "연수", "노유자", "실버", "스테이"]
for i, k in enumerate(kw): s.cell(row=28 + i, column=1, value=k).fill = IN
s["A40"] = "공사단계 키워드 → 누구를 만나나(위에서부터 먼저 맞는 것) — 8칸. 안 맞으면 착공일 없음=설계사 / 있음=시공사"; s["A40"].font = B
stg = [("착공전", "설계사"), ("설계", "설계사"), ("인허가", "설계사"), ("허가", "설계사"), ("착공", "시공사"), ("골조", "시공사"), ("마감", "늦음"), ("준공", "늦음")]
for i, (k, v) in enumerate(stg):
    s.cell(row=41 + i, column=1, value=k).fill = IN; s.cell(row=41 + i, column=2, value=v).fill = IN
widths(s, {"A": 52, "B": 30, "C": 44, "D": 40})
dv_stage = DataValidation(type="list", formula1='"설계사,시공사,늦음"', allow_blank=True); s.add_data_validation(dv_stage); dv_stage.add("B41:B48")

# ---------------- 2.현장 ----------------
h = sheet("2.현장")
cols = ["원본행", "주소", "건물명", "연면적(㎡)", "주용도", "허가구분", "설계사", "시공사", "감리", "건축주", "공사단계", "허가일", "착공일",
        "시·도", "유효", "키", "최신", "용도맞음", "면적맞음", "대상", "누구를 만나나", "설계사(정리)", "설계사번호", "허가일원문", "착공일원문", "대상키"]
hdr(h, 1, cols)
def raw(f, r, text=True):
    fr = FROW[f]
    core = f"INDEX({P1}!$A$1:$AZ${N+1},ROW(),{ST}!$C${fr})"
    return f'IFERROR({core}&"","")' if text else core
def parse_date(ref):
    t = f'SUBSTITUTE(SUBSTITUTE({ref},".","-"),"/","-")'
    return (f'=IF({ref}="","",IF(AND(LEN({ref})=8,ISNUMBER({ref}*1)),DATE(LEFT({ref},4),MID({ref},5,2),RIGHT({ref},2)),'
            f'IFERROR(DATEVALUE({t}),IFERROR({ref}*1,""))))')
kwor = ",".join(f'AND({ST}!$A${28+i}<>"",ISNUMBER(SEARCH({ST}!$A${28+i},E{{r}}&" "&C{{r}})))' for i in range(10))
def stage(r):
    f = f'IF(M{r}="","설계사","시공사")'
    for i in reversed(range(8)):
        a = f"{ST}!$A${41+i}"; b = f"{ST}!$B${41+i}"
        f = f'IF(AND({a}<>"",ISNUMBER(SEARCH({a},K{r}))),{b},{f})'
    return f'=IF(T{r},{f},"")'
for r in range(2, R2 + 1):
    row = {
     "A": "=ROW()",
     "B": "=" + raw("주소", r), "C": "=" + raw("건물명", r),
     "D": f'=IFERROR(VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({raw("연면적", r)},",",""),"㎡",""),"m2","")),"")',
     "E": "=" + raw("주용도", r), "F": "=" + raw("허가구분", r), "G": "=" + raw("설계사", r), "H": "=" + raw("시공사", r),
     "I": "=" + raw("감리", r), "J": "=" + raw("건축주", r), "K": "=" + raw("공사단계", r),
     "L": parse_date(f"X{r}"), "M": parse_date(f"Y{r}"),
     "N": f'=IFERROR(LEFT(B{r},FIND(" ",B{r})-1),B{r})',
     "O": f'=AND(B{r}<>"",B{r}<>{ST}!$B$4,C{r}<>{ST}!$B$5)',
     "P": f'=IF(O{r},B{r}&"|"&C{r},"")',
     "Q": f'=AND(O{r},COUNTIF(P{r+1}:P${R2+1},P{r})=0)',
     "R": "=OR(" + kwor.format(r=r) + ")",
     "S": f'=OR(D{r}="",D{r}>={ST}!$B$19)',
     "T": f"=AND(Q{r},R{r},S{r})",
     "U": stage(r),
     "V": f'=SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(G{r},"(주)",""),"㈜",""),"주식회사","")," ","")',
     "W": f'=IF(AND(T{r},V{r}<>""),IF(COUNTIFS(V$2:V{r},V{r},T$2:T{r},TRUE)=1,MAX(W$1:W{r-1})+1,""),"")',
     "X": "=" + raw("허가일", r), "Y": "=" + raw("착공일", r),
     "Z": f'=IF(T{r},V{r}&"|"&U{r},"")',
    }
    for k, v in row.items(): h[f"{k}{r}"] = v
    h[f"L{r}"].number_format = DATE; h[f"M{r}"].number_format = DATE; h[f"D{r}"].number_format = "#,##0"
h.freeze_panes = "C2"
widths(h, {"A": 6, "B": 26, "C": 20, "D": 10, "E": 16, "F": 8, "G": 20, "H": 16, "I": 10, "J": 12, "K": 10, "L": 11, "M": 11,
           "N": 12, "U": 12, "V": 18})
for c in "OPQRSTWXYZ": h.column_dimensions[c].hidden = True
h.auto_filter.ref = f"A1:Z{R2}"

# ---------------- 설계사_메모 ----------------
m = sheet(MEMO)
m["A1"] = "설계사무소 담당자 메모 — 알게 되면 한 줄. 이름은 드롭다운(3.설계사 목록)에서 고르면 자동으로 붙습니다"; m["A1"].font = B
hdr(m, 2, ["설계사무소", "담당자", "직함", "전화", "이메일", "주소·지역", "메모"])
for r in range(3, 303):
    for c in range(1, 8): m.cell(row=r, column=c).fill = IN
widths(m, {"A": 26, "B": 12, "C": 10, "D": 16, "E": 24, "F": 24, "G": 40})

# ---------------- 4.방문기록 ----------------
v = sheet("4.방문기록")
v["A1"] = "방문·통화 기록 — 다녀오시면 한 줄 (날짜·설계사무소·결과만 넣어도 됩니다)"; v["A1"].font = B
hdr(v, 2, ["날짜", "설계사무소", "관련 현장", "만난 사람", "들은 것", "다음 약속일", "다음 할 것", "결과", "키(자동)", "목록에없음(자동)"])
for r in range(3, 3 + VR):
    for c in range(1, 9): v.cell(row=r, column=c).fill = IN
    v[f"A{r}"].number_format = DATE; v[f"F{r}"].number_format = DATE
    v[f"I{r}"] = f'=IF(A{r}="","",B{r}&"|"&(A{r}*1))'
    v[f"J{r}"] = f'=IF(B{r}="",0,IF(COUNTIF({P3}!$B$4:$B${3+DS},B{r})=0,1,0))'
if WITH_EXAMPLE:
    v["A3"] = "2026-09-10"; v["B3"] = "[예시]사아종합건축사사무소"; v["C3"] = "[예시]사아리조트"; v["D3"] = "[예시]김소장"
    v["E3"] = "[예시] 객실관리 도면 10월 중 요청 예정"; v["F3"] = "2026-10-01"; v["G3"] = "[예시] 평면도 받기"; v["H3"] = "재방문"
    from datetime import date
    v["A3"] = date(2026, 9, 10); v["F3"] = date(2026, 10, 1)
res = ["설계의뢰 받음", "도면 받음", "자료 요청받음", "재방문", "부재", "관심 없음"]
dv_res = DataValidation(type="list", formula1='"' + ",".join(res) + '"', allow_blank=True); v.add_data_validation(dv_res); dv_res.add(f"H3:H{2+VR}")
dv_name = DataValidation(type="list", formula1=f"={P3}!$B$4:$B${3+DS}", allow_blank=True, showErrorMessage=False)
v.add_data_validation(dv_name); dv_name.add(f"B3:B{2+VR}")
dv_name2 = DataValidation(type="list", formula1=f"={P3}!$B$4:$B${3+DS}", allow_blank=True, showErrorMessage=False)
m.add_data_validation(dv_name2); dv_name2.add("A3:A302")
v.freeze_panes = "A3"
widths(v, {"A": 11, "B": 26, "C": 20, "D": 12, "E": 40, "F": 11, "G": 24, "H": 14})
v.column_dimensions["I"].hidden = True; v.column_dimensions["J"].hidden = True

# ---------------- 3.설계사 ----------------
g = sheet("3.설계사")
g["A1"] = "설계사무소별 모음 (자동) — 산군 대상 현장을 설계사무소 이름으로 묶음"; g["A1"].font = T
g["A2"] = "=\"설계사무소 \"&COUNTIF(B4:B" + str(3 + DS) + ",\"?*\")&\"곳 · 대상 현장 \"&COUNTIF(" + P2 + "!T2:T" + str(R2) + ",TRUE)&\"건\""
hdr(g, 3, ["번호", "설계사무소", "대상 현장", "설계단계", "시공단계", "최대 연면적", "최근 허가일", "대표 현장", "지역", "담당자", "전화",
           "마지막 방문", "경과일", "다음 약속", "최근 결과", "상태", "우선점수", "순위"])
V2 = f"{P2}!$V$2:$V${R2}"; T2 = f"{P2}!$T$2:$T${R2}"; U2 = f"{P2}!$U$2:$U${R2}"; Z2 = f"{P2}!$Z$2:$Z${R2}"
for r in range(4, 4 + DS):
    k = r - 3
    g[f"A{r}"] = f'=IF(B{r}="","",{k})'
    g[f"B{r}"] = f'=IFERROR(INDEX({V2},MATCH({k},{P2}!$W$2:$W${R2},0)),"")'
    g[f"C{r}"] = f'=IF(B{r}="","",COUNTIFS({V2},B{r},{T2},TRUE))'
    g[f"D{r}"] = f'=IF(B{r}="","",COUNTIFS({V2},B{r},{U2},"설계사"))'
    g[f"E{r}"] = f'=IF(B{r}="","",COUNTIFS({V2},B{r},{U2},"시공사"))'
    g[f"F{r}"] = f'=IF(B{r}="","",_xlfn.MAXIFS({P2}!$D$2:$D${R2},{V2},B{r},{T2},TRUE))'
    g[f"G{r}"] = f'=IF(B{r}="","",IF(_xlfn.MAXIFS({P2}!$L$2:$L${R2},{V2},B{r},{T2},TRUE)=0,"",_xlfn.MAXIFS({P2}!$L$2:$L${R2},{V2},B{r},{T2},TRUE)))'
    mi = f'IFERROR(MATCH(B{r}&"|설계사",{Z2},0),IFERROR(MATCH(B{r}&"|시공사",{Z2},0),MATCH(B{r}&"|늦음",{Z2},0)))'
    g[f"H{r}"] = f'=IF(B{r}="","",IFERROR(INDEX({P2}!$C$2:$C${R2},{mi}),""))'
    g[f"I{r}"] = f'=IF(B{r}="","",IFERROR(INDEX({P2}!$N$2:$N${R2},{mi}),""))'
    g[f"J{r}"] = f'=IF(B{r}="","",IFERROR(VLOOKUP(B{r},{MEMO}!$A$3:$G$302,2,FALSE)&"",""))'
    g[f"K{r}"] = f'=IF(B{r}="","",IFERROR(VLOOKUP(B{r},{MEMO}!$A$3:$G$302,4,FALSE)&"",""))'
    g[f"L{r}"] = f'=IF(B{r}="","",IF(COUNTIF({P4}!$B$3:$B${2+VR},B{r})=0,"",_xlfn.MAXIFS({P4}!$A$3:$A${2+VR},{P4}!$B$3:$B${2+VR},B{r})))'
    g[f"M{r}"] = f'=IF(L{r}="","",{ST}!$B$24-L{r})'
    g[f"N{r}"] = f'=IF(B{r}="","",IF(_xlfn.MAXIFS({P4}!$F$3:$F${2+VR},{P4}!$B$3:$B${2+VR},B{r})=0,"",_xlfn.MAXIFS({P4}!$F$3:$F${2+VR},{P4}!$B$3:$B${2+VR},B{r})))'
    g[f"O{r}"] = f'=IF(L{r}="","",IFERROR(INDEX({P4}!$H$3:$H${2+VR},MATCH(B{r}&"|"&(L{r}*1),{P4}!$I$3:$I${2+VR},0))&"",""))'
    g[f"P{r}"] = f'=IF(B{r}="","",IF(O{r}="관심 없음","제외",IF(L{r}="","안 가봄",IF(M{r}>={ST}!$B$20,M{r}&"일 지남","최근 방문"))))'
    appt = f'AND(N{r}<>"",N{r}>N(L{r}),N{r}<={ST}!$B$24+7)'
    g[f"Q{r}"] = (f'=IF(B{r}="","",IF(P{r}="제외","",IF(AND({ST}!$B$21<>"",I{r}<>{ST}!$B$21),"",'
                  f'IF({appt},100+7-(N{r}-{ST}!$B$24),IF(AND(D{r}>0,OR(P{r}="안 가봄",RIGHT(P{r},2)="지남")),'
                  f'D{r}*10+IF(L{r}="",30,MIN(M{r},60)/2)+MIN(N(F{r})/1000,20),"")))))')
    g[f"R{r}"] = f'=IF(Q{r}="","",COUNTIF(Q$4:Q${3+DS},">"&Q{r})+COUNTIF(Q$4:Q{r},Q{r}))'
    for c in "GLN": g[f"{c}{r}"].number_format = DATE
    g[f"F{r}"].number_format = "#,##0"; g[f"Q{r}"].number_format = "0.0"
g.freeze_panes = "C4"
widths(g, {"A": 5, "B": 26, "C": 8, "D": 8, "E": 8, "F": 11, "G": 11, "H": 20, "I": 12, "J": 10, "K": 14, "L": 11, "M": 7, "N": 11, "O": 12, "P": 11, "Q": 8, "R": 6})

# ---------------- 5.이번주_갈곳 ----------------
w = sheet("5.이번주_갈곳")
w["A1"] = "=\"이번 주 찾아갈 설계사무소 \"&COUNT(" + P3 + "!R4:R" + str(3 + DS) + ")&\"곳 · 지역: \"&IF(설정!B21=\"\",\"전국\",설정!B21)&\" · 기준일 \"&TEXT(설정!B24,\"yyyy-mm-dd\")"
w["A1"].font = T
w["A2"] = "순서 : ①7일 안 약속 ②설계단계 현장이 많고 안 가본 곳 ③오래 안 간 곳. 관심 없음·최근 방문(재방문 간격 안)은 빠짐. 지역은 설정 B21."
hdr(w, 3, ["순위", "설계사무소", "왜 가야 하나", "대표 현장", "지역", "최대 연면적", "담당자", "전화", "전화 첫마디(복사)", "_행"])
for r in range(4, 34):
    k = r - 3
    w[f"J{r}"] = f'=IFERROR(MATCH({k},{P3}!$R$4:$R${3+DS},0),"")'
    def G(col): return f'INDEX({P3}!${col}$4:${col}${3+DS},J{r})'
    w[f"A{r}"] = f'=IF(J{r}="","",{k})'
    w[f"B{r}"] = f'=IF(J{r}="","",{G("B")})'
    w[f"C{r}"] = (f'=IF(J{r}="","",IF({G("Q")}>=100,"약속 "&TEXT({G("N")},"m/d")&" · ",IF({G("L")}="","아직 안 가봄 · ","마지막 방문 "&{G("M")}&"일 전 · "))'
                  f'&"설계단계 "&{G("D")}&"건"&IF({G("E")}>0," · 시공단계 "&{G("E")}&"건",""))')
    w[f"D{r}"] = f'=IF(J{r}="","",{G("H")})'
    w[f"E{r}"] = f'=IF(J{r}="","",{G("I")})'
    w[f"F{r}"] = f'=IF(J{r}="","",{G("F")})'
    w[f"G{r}"] = f'=IF(J{r}="","",{G("J")})'
    w[f"H{r}"] = f'=IF(J{r}="","",{G("K")})'
    w[f"I{r}"] = (f'=IF(J{r}="","","한국마이크로닉 배성윤 차장입니다. "&{G("H")}&" 설계 진행하고 계신 걸로 알고 연락드렸습니다. '
                  f'호텔 객실관리(키센서·온도조절기·조명 제어) 도면과 특기시방서를 무상으로 지원해 드리고 있어서, 이번 주에 10분만 찾아뵈어도 될까요?")')
    w[f"F{r}"].number_format = "#,##0"; w[f"I{r}"].alignment = WRAP; w[f"C{r}"].alignment = WRAP
w.column_dimensions["J"].hidden = True
w.freeze_panes = "C4"
widths(w, {"A": 5, "B": 26, "C": 30, "D": 20, "E": 12, "F": 11, "G": 10, "H": 14, "I": 70})

# ---------------- 6.본전계산 ----------------
b = sheet("6.본전계산")
b["A1"] = "산군 본전 계산 — 기준 숫자는 프로님이 넣으십시오(노란 칸)"; b["A1"].font = T
hdr(b, 3, ["항목", "값", "메모"])
rows6 = [
 ("산군 사용 시작일", f'=IF({ST}!B23="","",{ST}!B23)', "설정 B23"),
 ("쓴 개월 수", f'=IF({ST}!B23="","시작일을 넣으십시오",DATEDIF({ST}!B23,{ST}!B24,"m")+1)', ""),
 ("누적 비용(원)", f'=IF(ISNUMBER(B5),B5*{ST}!B22,"")', "월 요금 × 개월"),
 ("월결제 1년 vs 연결제 차액(원)", f"={ST}!B22*12-{ST}!B25", "연결제로 바꾸면 아끼는 돈"),
 ("산군으로 잡힌 설계사무소(곳)", f'=COUNTIF({P3}!B4:B{3+DS},"?*")', "자동"),
 ("그중 한 번이라도 간 곳", f'=COUNTIF({P3}!L4:L{3+DS},">0")', "자동"),
 ("방문·통화 건수", f"=COUNT({P4}!A3:A{2+VR})", "자동"),
 ("설계의뢰 받음", f'=COUNTIF({P4}!H3:H{2+VR},"설계의뢰 받음")', "자동"),
 ("도면 받음", f'=COUNTIF({P4}!H3:H{2+VR},"도면 받음")', "자동"),
 ("방문 1건당 산군 비용(원)", f'=IF(AND(ISNUMBER(B6),B10>0),B6/B10,"")', ""),
]
for i, (a, f, note) in enumerate(rows6):
    r = 4 + i; b[f"A{r}"] = a; b[f"B{r}"] = f; b[f"B{r}"].fill = AUTO; b[f"C{r}"] = note
b["B4"].number_format = DATE
for r in (6, 7, 13): b[f"B{r}"].number_format = "#,##0"
b["A16"] = "유지 판단 기준(3개월 기준 권장)"; b["A16"].font = B
hdr(b, 17, ["기준", "넣으실 숫자", "실제", "통과"])
crit = [("간 설계사무소 최소(곳)", "B9"), ("설계의뢰 받음 최소(건)", "B11"), ("도면 받음 최소(건)", "B12")]
for i, (a, ref) in enumerate(crit):
    r = 18 + i; b[f"A{r}"] = a; b[f"B{r}"].fill = IN; b[f"C{r}"] = f"={ref}"
    b[f"D{r}"] = f'=IF(B{r}="","",IF(C{r}>=B{r},"통과","미달"))'
b["A22"] = "판정"; b["A22"].font = B
b["B22"] = '=IF(COUNTA(B18:B20)=0,"기준 숫자를 넣으시면 판정합니다",IF(COUNTIF(D18:D20,"미달")=0,"유지","미달 있음 — 해지 또는 조건 변경 검토"))'
widths(b, {"A": 34, "B": 30, "C": 26, "D": 10})

# ---------------- 7.문안 ----------------
t = sheet("7.문안")
t["A1"] = "보낼 문안 — B3 에서 설계사무소를 고르면 채워집니다. [ ] 칸만 고쳐서 복사"; t["A1"].font = T
t["A3"] = "설계사무소"; t["B3"].fill = IN
dv_t = DataValidation(type="list", formula1=f"={P3}!$B$4:$B${3+DS}", allow_blank=True, showErrorMessage=False); t.add_data_validation(dv_t); dv_t.add("B3")
t["A4"] = "(비우면 5번 1순위)"; t["A4"].font = Font(italic=True, color="808080")
t["A5"] = "쓰는 이름"; t["B5"] = "=IF(B3<>\"\",B3,IFERROR('5.이번주_갈곳'!B4&\"\",\"\"))"
rowi = f"MATCH(B5,{P3}!$B$4:$B${3+DS},0)"
t["A6"] = "대표 현장"; t["B6"] = f'=IFERROR(INDEX({P3}!$H$4:$H${3+DS},{rowi})&"","[현장명]")'
t["A7"] = "담당자"; t["B7"] = f'=IFERROR(IF(INDEX({P3}!$J$4:$J${3+DS},{rowi})="","[담당자]",INDEX({P3}!$J$4:$J${3+DS},{rowi})),"[담당자]")'
t["A8"] = "연면적"; t["B8"] = f'=IFERROR(INDEX({P3}!$F$4:$F${3+DS},{rowi}),"")'; t["B8"].number_format = "#,##0"
for r in range(5, 9): t[f"B{r}"].fill = AUTO
NL = "CHAR(10)"
t["A10"] = "전화 첫마디"
t["B10"] = '="한국마이크로닉 배성윤 차장입니다. "&B6&" 설계 진행하고 계신 걸로 알고 연락드렸습니다. 호텔 객실관리(키센서·온도조절기·조명 제어) 도면과 특기시방서를 무상으로 지원해 드리고 있어서, [날짜]에 10분만 찾아뵈어도 될까요?"'
t["A11"] = "문자(짧게)"
t["B11"] = '="[한국마이크로닉 배성윤 차장] "&B7&"님, "&B6&" 객실관리시스템 설계(도면·특기시방서)를 무상 지원해 드립니다. [날짜] 잠시 찾아뵈어도 될지 여쭙습니다. [전화]"'
t["A12"] = "메일 제목"
t["B12"] = '=B6&" 객실관리시스템 설계 지원 안내 — 한국마이크로닉(주)"'
t["A13"] = "메일 본문"
t["B13"] = ('=B5&" "&B7&"님께"&' + NL + '&' + NL +
            '&"한국마이크로닉(주) 배성윤 차장입니다."&' + NL +
            '&"진행 중이신 "&B6&"([객실 수]실)의 객실관리시스템(RCU·CB함·키센서·온도조절기·조명스위치) 설계를 무상으로 지원해 드립니다."&' + NL + '&' + NL +
            '&"- 단위세대 평면도를 주시면 성급 기준으로 기구물 배치와 예상 수량표를 드립니다."&' + NL +
            '&"- 특기시방서(한글 파일)를 현장에 맞춰 드립니다."&' + NL +
            '&"- 전기설계업체용 설계 요청서도 함께 드립니다."&' + NL + '&' + NL +
            '&"[날짜] 중 편하신 시간에 찾아뵙겠습니다."&' + NL + '&' + NL +
            '&"한국마이크로닉(주) 배성윤 드림 / [전화]"')
t["A14"] = "방문 후 감사 문자"
t["B14"] = '="[한국마이크로닉 배성윤] 오늘 시간 내주셔서 감사합니다. 말씀하신 "&B6&" 자료는 [날짜]까지 보내 드리겠습니다."'
for r in range(10, 15): t[f"B{r}"].alignment = WRAP; t[f"B{r}"].fill = AUTO; t[f"A{r}"].font = B
t.row_dimensions[13].height = 230; t.row_dimensions[10].height = 60; t.row_dimensions[11].height = 45
widths(t, {"A": 18, "B": 100})

# ---------------- 0.자가진단 (내용) ----------------
d["A1"] = f"자가진단 — 전부 「통과」 면 정상 ({VER})"; d["A1"].font = T
hdr(d, 3, ["번호", "검사", "값", "판정"])
chk = [
 ("산군 열 이름 12개 중 찾은 수", f"=COUNT({ST}!C4:C15)", f'IF(C{{r}}=12,"통과",IF(AND({ST}!C4<>"",{ST}!C5<>"",{ST}!C9<>""),"통과(일부 열 없음 — 설정 확인)","실패 — 설정 B4~B15"))'),
 ("붙여넣은 줄 수(1행 제외)", f"=MAX(COUNTA({P1}!A:A)-1,0)", f'IF(C{{r}}<={N},"통과","실패 — {N}줄 넘음, 아래는 안 읽힘")'),
 ("읽은 현장 줄", f"=COUNTIF({P2}!O2:O{R2},TRUE)", 'IF(C{r}=C5,"통과","확인 — 빈 줄·제목줄 섞임")'),
 ("중복 뺀 현장", f"=COUNTIF({P2}!Q2:Q{R2},TRUE)", '"참고"'),
 ("대상(용도·면적 맞음)", f"=COUNTIF({P2}!T2:T{R2},TRUE)", '"참고"'),
 ("설계사행 + 시공사행 + 늦음 = 대상", f'=COUNTIF({P2}!U2:U{R2},"설계사")+COUNTIF({P2}!U2:U{R2},"시공사")+COUNTIF({P2}!U2:U{R2},"늦음")', 'IF(C{r}=C8,"통과","실패 — 설정 단계 행선지 확인")'),
 ("설계사무소 수 = 번호 최댓값", f'=COUNTIF({P3}!B4:B{3+DS},"?*")', f'IF(C{{r}}=MAX({P2}!W2:W{R2}),IF(C{{r}}<{DS},"통과","실패 — {DS}곳 넘음"),"실패")'),
 ("설계사 이름 빈 대상 현장", f'=COUNTIFS({P2}!T2:T{R2},TRUE,{P2}!V2:V{R2},"")', 'IF(C{r}=0,"통과","확인 — 산군에 설계사 없는 현장(2.현장 필터)")'),
 ("방문기록 중 목록에 없는 사무소", f"=SUM({P4}!J3:J{2+VR})", 'IF(C{r}=0,"통과","확인 — 이름이 3.설계사와 다름(드롭다운으로 고르기)")'),
 ("예시 줄 남음", f'=COUNTIF({P1}!B:B,"[예시]*")+COUNTIF({P4}!B:B,"[예시]*")', 'IF(C{r}=0,"통과","알림 — [예시] 줄이 있음. 산군 붙여넣기 후 방문기록 예시 줄 지우기")'),
]
for i, (name, val, judge) in enumerate(chk):
    r = 4 + i
    d[f"A{r}"] = i + 1; d[f"B{r}"] = name; d[f"C{r}"] = val; d[f"D{r}"] = "=" + judge.format(r=r)
d["A16"] = "변경 이력"; d["A16"].font = B
hdr(d, 17, ["날짜", "판", "내용", "이전 값"])
d["A18"] = TODAY; d["B18"] = VER; d["C18"] = "최초 작성 — 11개 탭(사용법·0~7·설정·설계사_메모). 계획서 v1 구조 그대로."; d["D18"] = "없음"
widths(d, {"A": 12, "B": 40, "C": 60, "D": 50})
d.conditional_formatting.add("D4:D13", FormulaRule(formula=['LEFT(D4,2)="통과"'], fill=PatternFill("solid", fgColor="C6EFCE")))
d.conditional_formatting.add("D4:D13", FormulaRule(formula=['LEFT(D4,2)="실패"'], fill=PatternFill("solid", fgColor="FFC7CE")))

order = ["사용법", "0.자가진단", "1.산군_붙여넣기", "5.이번주_갈곳", "3.설계사", "4.방문기록", "7.문안", "2.현장", "6.본전계산", "설계사_메모", "설정"]
wb._sheets = [wb[n] for n in order]
wb.active = 3
from openpyxl.workbook.properties import CalcProperties
wb.calculation = CalcProperties(fullCalcOnLoad=True)
wb.save(OUT); print("saved", OUT)

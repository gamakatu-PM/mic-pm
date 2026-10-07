# -*- coding: utf-8 -*-
"""그랜드 하얏트 인천 단위세대 배치 — 타입별 번호판 이미지 + 수정 가능한 표(xlsx/csv) 생성.
번호 체계(프로님 확정 2026-10-07): 1 챠임벨 / 2 키센서 DM / 3 BSP / 4 거실(회의실) 스위치, 거실 없으면 드레스룸이 4 /
5 화장실 스위치 / 6 드레스룸 스위치(거실 있을 때) / 비상호출은 맨 끝 번호. MMO는 이 현장에서 삭제.
"""
import os, csv
from PIL import Image, ImageDraw, ImageFont
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE='/tmp/claude-0/-home-user-mic-pm/8403231e-3d6f-5abe-9a01-3ffcda68154f'
OUT=os.path.join(BASE,'scratchpad','deliver'); os.makedirs(OUT,exist_ok=True)
FONT='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
G=(46,125,91); B=(42,96,153); O=(199,123,43); W=(255,255,255); LINE=(90,100,115)
SITE='46.그랜드 하얏트 인천(희림 박성철)'; DATE='251007'

# 타입 정의: (파일, 제목, 상태, [룸...])  룸 = (룸이름, 색, [(번호,품목,x,y,위치설명)])
T=[
 ('13.png','GOVERNOR SUITE (GS)','확정(프로님 검토 v4)',[('',G,[
   ('1','챠임벨',585,95,'출입문 복도 쪽'),('2','키센서 DM',545,115,'출입문 안쪽'),('3','BSP',175,455,'침대 옆'),
   ('4','거실 스위치',370,250,'거실 들어가는 문 옆'),('5','화장실 스위치',430,400,'욕실 문 옆')])]),
 ('1.png','4~12F 타입(첫 도면)','확정(프로님 검토 v4)',[('',G,[
   ('1','챠임벨',478,72,'출입문 복도 쪽'),('2','키센서 DM',440,108,'출입문 안쪽'),('3','BSP',238,362,'침대 옆'),
   ('4','드레스룸 스위치',468,165,'출입문과 욕실 사이 옷장 통로'),('5','화장실 스위치',436,252,'욕실 문 옆 벽, 손잡이 쪽')])]),
 ('3.png','SUITE KING (K-3) 3~12F','미검토',[('',G,[
   ('1','챠임벨',552,418,'우측 하단 출입문 복도 쪽'),('2','키센서 DM',515,395,'출입문 안쪽'),('3','BSP',203,253,'침대 옆'),
   ('4','드레스룸 스위치',372,185,'상단 옷장(CB 옆)'),('5','화장실 스위치',468,335,'욕실 문 옆 벽')])]),
 ('9.png','AMBASSADOR SUITE (AS) — 커넥팅','확정(프로님 검토 v4)',[
   ('룸1 = 좌측 침실 + 거실',G,[
   ('1','챠임벨',265,332,'중앙 하단 출입문 복도 쪽'),('2','키센서 DM',275,302,'출입문 안쪽'),('3','BSP',72,140,'킹 침대 옆'),
   ('4','거실 스위치',340,222,'현관에서 거실 들어가는 입구 옆 벽'),('5','화장실 스위치',143,248,'욕실 문 옆 벽'),
   ('6','드레스룸 스위치',108,268,'침실과 욕실 사이 옷장 통로')]),
   ('룸2 = 우측 침실',B,[
   ('1','챠임벨',466,332,'우측 하단 출입문 복도 쪽'),('2','키센서 DM',452,302,'출입문 안쪽'),('3','BSP',392,95,'트윈 침대 옆'),
   ('4','화장실 스위치',440,268,'욕실 문 옆 벽 (현관은 통로라 스위치 없음)')])]),
 ('10.png',"MANAGER'S SUITE (GM)",'확정(프로님 검토 v2)',[('',G,[
   ('1','챠임벨',150,110,'좌측 상단 출입문 복도 쪽'),('2','키센서 DM',185,140,'출입문 안쪽'),
   ('3','BSP',195,285,'좌 침실 침대 옆'),('3','BSP',580,290,'우 침실 침대 옆'),
   ('4','거실 스위치',235,215,'현관 복도에서 거실 들어가는 입구 옆 벽'),
   ('5','화장실 스위치',150,222,'좌 욕실 문 옆 벽'),('5','화장실 스위치',568,205,'우 욕실 문 옆 벽'),
   ('6','드레스룸 스위치',195,165,'출입문 옆 드레스룸(옷걸이)'),('6','드레스룸 스위치',500,150,'우 침실 드레스룸')])]),
 ('4.png',"OWNER'S SUITE (OS)",'미검토',[('',G,[
   ('1','챠임벨',120,292,'좌측 하단 출입문 복도 쪽'),('2','키센서 DM',150,272,'출입문 안쪽'),('3','BSP',698,186,'마스터 침대 옆'),
   ('4','거실 스위치',515,200,'거실 입구 옆 벽'),('4','거실 스위치',150,205,'회의·식당실 입구 옆 벽'),
   ('5','화장실 스위치',560,235,'마스터 욕실 문 옆'),('5','화장실 스위치',450,250,'파우더룸 문 옆'),
   ('6','드레스룸 스위치',520,120,'거실·침실 사이 드레스룸')])]),
 ('5.png','PRESIDENTIAL SUITE (PS)','미검토',[('',G,[
   ('1','챠임벨',470,335,'중앙 ENTRY FOYER 출입문 복도 쪽'),('2','키센서 DM',470,300,'출입문 안쪽'),
   ('3','BSP',997,202,'마스터 침대 옆'),('3','BSP',152,197,'더블퀸 침대 옆'),
   ('4','거실 스위치',600,235,'LIVING 입구 옆 벽'),('4','거실 스위치',290,230,'DINING 입구 옆 벽'),('4','거실 스위치',790,205,'LIBRARY 입구 옆 벽'),
   ('5','화장실 스위치',150,290,'더블퀸 욕실 문 옆'),('5','화장실 스위치',600,300,'POWDER ROOM 문 옆'),
   ('5','화장실 스위치',670,300,'TOILET 문 옆'),('5','화장실 스위치',820,310,'MASTER BATH 문 옆'),
   ('6','드레스룸 스위치',990,275,'마스터 옷장(옷걸이)'),('6','드레스룸 스위치',75,250,'더블퀸 옷장')])]),
 ('6.png','HOSPITALITY SUITE-1 (HS-1)','미검토',[('',G,[
   ('1','챠임벨',525,440,'하단 FOYER 출입문 복도 쪽'),('2','키센서 DM',490,430,'출입문 안쪽'),
   ('4','회의실 스위치',330,440,'회의실 입구 옆 벽 (온도+L+디밍+커튼)'),('5','화장실 스위치',470,200,'욕실 문 옆'),
   ('6','드레스룸 스위치',430,140,'BATHROOM FOYER 옷장')])]),
 ('7.png','HOSPITALITY SUITE-3 (HS-3)','미검토',[('',G,[
   ('1','챠임벨',95,432,'좌측 하단 FOYER 출입문 복도 쪽'),('2','키센서 DM',120,400,'출입문 안쪽'),
   ('4','회의실 스위치',255,395,'회의실 입구 옆 벽'),('5','화장실 스위치',175,335,'욕실 문 옆')])]),
 ('8.png','HOSPITALITY SUITE-5 (HS-5)','미검토',[('',G,[
   ('1','챠임벨',35,400,'좌측 하단 FOYER 출입문 복도 쪽'),('2','키센서 DM',75,395,'출입문 안쪽'),
   ('4','회의실 스위치',225,420,'회의실 입구 옆 벽'),('4','거실 스위치',150,115,'LIBRARY 입구 옆 벽'),
   ('5','화장실 스위치',150,170,'욕실 문 옆')])]),
 ('11.png','HANDICAP (DD-2) 3~12F 주거약자실','미검토',[('',G,[
   ('1','챠임벨',62,383,'좌측 하단 출입문 복도 쪽'),('2','키센서 DM',85,350,'출입문 안쪽'),('3','BSP',242,160,'트윈 침대 사이'),
   ('4','드레스룸 스위치',100,300,'현관 옷장(옷걸이)'),('5','화장실 스위치',140,310,'욕실 문 옆'),
   ('6','비상호출',118,350,'욕실 변기·욕조 옆')])]),
 ('12.png','KING & DD TYPE — 2실','미검토',[
   ('상 = KING',G,[
   ('1','챠임벨',372,165,'우측 출입문 복도 쪽'),('2','키센서 DM',335,175,'출입문 안쪽'),('3','BSP',255,235,'침대 옆(침대 미도시)'),
   ('4','드레스룸 스위치',280,183,'현관 옷장(옷걸이)'),('5','화장실 스위치',330,215,'욕실 문 옆')]),
   ('하 = DD',B,[
   ('1','챠임벨',372,345,'우측 출입문 복도 쪽'),('2','키센서 DM',335,335,'출입문 안쪽'),('3','BSP',255,270,'침대 옆(침대 미도시)'),
   ('4','드레스룸 스위치',280,325,'현관 옷장(옷걸이)'),('5','화장실 스위치',330,295,'욕실 문 옆')])]),
]

RULES=[
 ('번호 체계','1 챠임벨 / 2 키센서 DM / 3 BSP / 4 거실·회의실 스위치(없으면 드레스룸이 4) / 5 화장실 스위치 / 6 드레스룸 스위치(거실 있을 때) / 비상호출은 맨 끝. 같은 품목이 여러 개면 같은 번호 반복.'),
 ('MMO','이 현장은 MMO 삭제(데스크·화장대 구분 어려움). 다른 현장은 책상 있으면 MMO 1 규칙 유지.'),
 ('BSP 내장','온도조절기·L·디밍·커튼스위치는 BSP 안에 내장. 침실만 있는 타입은 별도 없음.'),
 ('거실 스위치','별도 거실이 있을 때만 거실 입구 옆 벽에 1개(온도+L+디밍+커튼). 회의실도 같은 구성.'),
 ('화장실 스위치','화장실 들어가는 문 옆 벽, 손잡이 쪽(경첩 반대), 문 바깥. 공간 한가운데 찍지 않는다.'),
 ('드레스룸','옷걸이 기호가 있는 옷장방이면 스위치 1. 옷걸이 없이 지나가는 통로형 현관은 스위치 없음.'),
 ('비상호출','주거약자실(장애인실)만 욕실 1. 일반실 없음.'),
 ('미니바·수납','거실과 한 공간인 미니바 콘솔·붙박이 옷장은 기구물 없음.'),
 ('커넥팅룸','룸1·룸2로 나눠 표를 따로 만든다. 같이 팔 때는 합산.'),
 ('책상 판독','창가에 의자 1 + 작은 탁자 = 책상. 양면 긴 장(TV장·콘솔)·화장대는 책상 아님. (이 현장은 MMO 삭제라 참고만)'),
 ('산출 방식','한 타입씩 그림+표 한 장으로 내고 프로님 확인 후 다음 타입. 한꺼번에 내지 않는다.'),
]

def render(src,title,status,rooms,outname):
    im=Image.open(os.path.join(BASE,'images',src)).convert('RGB'); S=2
    im=im.resize((im.width*S,im.height*S),Image.LANCZOS); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(FONT,22); fs=ImageFont.truetype(FONT,18); fb=ImageFont.truetype(FONT,19)
    for rn,col,items in rooms:
        for n,_,x,y,_ in items:
            x*=S;y*=S;r=16
            d.ellipse((x-r,y-r,x+r,y+r),fill=col,outline=W,width=2)
            w=d.textlength(n,font=f); d.text((x-w/2,y-14),n,font=f,fill=W)
    rh=30; n=sum(len(r[2])+2 for r in rooms)+1
    cv=Image.new('RGB',(im.width,im.height+rh*n+80),(24,29,37)); cv.paste(im,(0,0)); d=ImageDraw.Draw(cv)
    y=im.height+10; d.text((12,y),f'{title}   [{status}]',font=f,fill=W if status.startswith('확정') else (255,200,120)); y+=36
    for rn,col,items in rooms:
        agg={}
        for n,name,_,_,loc in items: agg.setdefault((n,name),[]).append(loc)
        if rn: d.ellipse((12,y+6,30,y+24),fill=col); d.text((38,y),f'{rn}  {len(items)}개',font=fb,fill=W); y+=30
        for c,t in zip([12,90,330,420],('번호','품목','수량','위치')): d.text((c,y+5),t,font=fb,fill=W)
        y+=rh
        for (n,name),locs in agg.items():
            for c,t in zip([12,90,330,420],(n,name,str(len(locs)),' / '.join(locs))): d.text((c,y+5),t,font=fs,fill=W)
            d.line((12,y+rh-2,im.width-12,y+rh-2),fill=LINE,width=1); y+=rh
        y+=8
    cv.save(os.path.join(OUT,outname)); return outname

# ---- 이미지 ----
imgs=[]
for i,(src,title,status,rooms) in enumerate(T,1):
    short=title.split('(')[1].split(')')[0] if '(' in title else title.split(' ')[0]
    name=f'{i:02d}_{short}_{DATE}.png'.replace('/','-').replace(' ','')
    imgs.append(render(src,title,status,rooms,name))

# ---- 표 ----
wb=Workbook(); ws=wb.active; ws.title='1.타입별 수량'
head=['타입','룸','번호','품목','수량','위치','상태','비고(프로님 수정칸)']
ws.append(head)
rows=[]
for src,title,status,rooms in T:
    for rn,col,items in rooms:
        agg={}
        for n,name,_,_,loc in items: agg.setdefault((n,name),[]).append(loc)
        for (n,name),locs in agg.items():
            r=[title,rn or '-',int(n),name,len(locs),' / '.join(locs),status,'']
            ws.append(r); rows.append(r)
yellow=PatternFill('solid',fgColor='FFF2CC'); bold=Font(name='맑은 고딕',bold=True); norm=Font(name='맑은 고딕')
thin=Side(style='thin',color='BBBBBB'); bd=Border(left=thin,right=thin,top=thin,bottom=thin)
for row in ws.iter_rows():
    for c in row: c.font=norm; c.border=bd; c.alignment=Alignment(vertical='center',wrap_text=True)
for c in ws[1]: c.font=bold; c.fill=PatternFill('solid',fgColor='DDEBF7')
for r in ws.iter_rows(min_row=2):
    r[4].number_format='#,##0'; r[4].fill=yellow; r[7].fill=yellow
    if r[6].value.startswith('미검토'): r[6].font=Font(name='맑은 고딕',color='C00000')
for i,wd in enumerate([30,18,6,16,6,60,20,30],1): ws.column_dimensions[get_column_letter(i)].width=wd
ws.freeze_panes='A2'

# 집계
ws2=wb.create_sheet('2.집계(실 수 입력)')
ws2.append(['타입','룸','기구물 종','1실당 개수','실 수(입력)','총 개수','상태'])
types={}
for src,title,status,rooms in T:
    for rn,col,items in rooms:
        key=(title,rn or '-'); types.setdefault(key,[status,set(),0]); types[key][1].update(n for n,*_ in items); types[key][2]+=len(items)
r=2
for (title,rn),(status,kinds,cnt) in types.items():
    ws2.append([title,rn,len(kinds),cnt,None,f'=D{r}*E{r}',status]); r+=1
ws2.append(['합계','','',f'=SUM(D2:D{r-1})','',f'=SUM(F2:F{r-1})',''])
for row in ws2.iter_rows():
    for c in row: c.font=norm; c.border=bd
for c in ws2[1]: c.font=bold; c.fill=PatternFill('solid',fgColor='DDEBF7')
for rr in ws2.iter_rows(min_row=2):
    rr[4].fill=yellow
    for c in rr[2:6]: c.number_format='#,##0'
for c in ws2[r]: c.font=bold
for i,wd in enumerate([30,18,10,10,12,10,20],1): ws2.column_dimensions[get_column_letter(i)].width=wd
ws2['I1']='노란칸(실 수)에 숫자를 넣으면 총 개수가 자동 계산됩니다. 중앙장비(PC 1, FIP 층당 1)는 층별 평면도 확정 후 추가.'

# 규칙
ws3=wb.create_sheet('3.정정 기준(프로님 확정)')
ws3.append(['항목','기준 (2026-10-07 프로님 정정 기준)'])
for k,v in RULES: ws3.append([k,v])
for row in ws3.iter_rows():
    for c in row: c.font=norm; c.border=bd; c.alignment=Alignment(wrap_text=True,vertical='top')
for c in ws3[1]: c.font=bold; c.fill=PatternFill('solid',fgColor='DDEBF7')
ws3.column_dimensions['A'].width=14; ws3.column_dimensions['B'].width=110

# 자가진단·이력
ws4=wb.create_sheet('0.자가진단·변경이력')
log=[('2026-10-07','v1','13타입 번호판·표 최초 생성. 확정 4타입(GS·4~12F·AS·GM), 미검토 9타입.'),
     ('2026-10-07','-','④ 확신 없이 넣은 것: 미검토 9타입의 출입문·욕실 문·드레스룸 판정은 Claude 판독. OS 파우더룸·PS 응접(개방형이라 스위치 제외)·HS-5 라이브러리는 확인 필요.'),
     ('2026-10-07','-','MMO 삭제(이 현장만). 드레스룸은 옷걸이 기호 있을 때만.'),
     ('2026-10-07','-','저장 위치: PC 폴더는 이 창에서 미연결이라 드라이브 「_컴퓨터로 옮길 것」에 임시 저장. PC 연결된 창에서 46.그랜드 하얏트 인천 → 3.단위세대배치 해봄 으로 옮길 것.')]
ws4.append(['날짜','버전','내용'])
for l in log: ws4.append(list(l))
for row in ws4.iter_rows():
    for c in row: c.font=norm; c.border=bd; c.alignment=Alignment(wrap_text=True,vertical='top')
for c in ws4[1]: c.font=bold
ws4.column_dimensions['C'].width=110
wb.move_sheet(ws4, offset=-3)
xlsx=os.path.join(OUT,f'그랜드하얏트인천_단위세대_기구물수량_v1_{DATE}.xlsx'); wb.save(xlsx)

# CSV 조회본
csvp=os.path.join(OUT,f'그랜드하얏트인천_단위세대_기구물수량_v1_{DATE}_조회본.csv')
with open(csvp,'w',newline='',encoding='utf-8-sig') as fp:
    w=csv.writer(fp); w.writerow(head); w.writerows(rows)
# 규칙 md (이중 저장)
with open(os.path.join(OUT,f'정정기준_그랜드하얏트인천_{DATE}.md'),'w',encoding='utf-8') as fp:
    fp.write('# 단위세대 배치 정정 기준 (프로님 확정, 2026-10-07)\n\n')
    for k,v in RULES: fp.write(f'- **{k}**: {v}\n')
print(imgs); print(xlsx)

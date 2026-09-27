# -*- coding: utf-8 -*-
"""★작업의뢰서_초안 자가시험. 가짜 드라이브 · 가짜 회의록 (실제 현장·사람 아님)."""
import os, io, sys, json, shutil, tempfile, datetime, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('wo', os.path.join(HERE, '★작업의뢰서_초안.py'))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

OK = [0]; NG = []
def chk(name, cond, why=''):
    if cond: OK[0] += 1; print('  OK   %s' % name)
    else: NG.append(name); print('  NG   %s  %s' % (name, why))

T = datetime.date(2026, 9, 27)
print('--- 입력 풀기')
chk('260921', G.norm_ymd('260921', 'x') == '260921')
chk('2026-09-21', G.norm_ymd('2026-09-21', 'x') == '260921')
chk('엉터리는 기본값', G.norm_ymd('abc', '260101') == '260101')
chk('월 9', G.norm_month('9', T) == ('260901', '260930'))
chk('월 2026-02', G.norm_month('2026-02', T) == ('260201', '260228'))

print('--- 품은 54번')
chk('버튼 안 54번이 저장소 54번과 같다',
    G.T54_SRC == io.open(os.path.join(HERE, '코드', 'km_tools', 't54_workorder.py'), encoding='utf-8').read(),
    '저장소 t54 를 고쳤으면 버튼을 다시 지어야 합니다')

d = tempfile.mkdtemp()
try:
    print('--- 도구 넣기 (없는 폴더 · 옛 판)')
    tools = os.path.join(d, '코드', 'km_tools'); os.makedirs(tools)
    io.open(os.path.join(tools, 't54_workorder.py'), 'w', encoding='utf-8').write("VERSION = 'v0 옛것'\n")
    n1 = G.ensure_tool(tools, 't54_workorder')
    chk('옛 54번 덮어씀', 'v0 → v3' in n1, n1)
    chk('다시 하면 안 건드림', G.ensure_tool(tools, 't54_workorder') == '')

    print('--- 통째로 돌리기 (가짜 드라이브)')
    drive = os.path.join(d, 'drive'); meta = os.path.join(drive, '회의록', 'incoming'); os.makedirs(meta)
    def mj(fn, site, ymd, lines):
        o = {'meta': {'site': site, 'ymd': ymd, 'hm': '10:00', 'person': '홍길동 소장', 'company': '가나건설', 'name': '홍길동', 'rank': '소장'},
             'sec': {'1': {'현장': site, '안건목록': []}, '2': {'타부서 전달 사항': lines, '할 일': []}}}
        io.open(os.path.join(meta, fn), 'w', encoding='utf-8').write(json.dumps(o, ensure_ascii=False))
    mj('a__meta.json', '가나호텔', '260921', ['1. 설계 — 회로 비교 → 작업의뢰서', '2. 전기 — 차단기 확인'])
    mj('b__meta.json', '다라기숙사', '260801', ['1. 제작 — 외함 → 작업의뢰서'])
    G.HERE = d
    opened = []
    tpl = os.path.join(d, 'tpl.xlsx')
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = '작업의뢰서 (그룹웨어)'
    for r in range(19, 36):
        ws.merge_cells('B%d:R%d' % (r, r))
    wb.save(tpl)
    rep = G.run('260901', '260930', drive=drive, out=os.path.join(d, 'out'), today=T, template=tpl, opener=opened.append)
    chk('9월 회의 1건 (8월 제외) → 1장', rep and rep['meetings'] == 1 and rep['sheets'] == 1 and rep['made'] == 1, rep)
    chk('엑셀 1개', sorted(f for f in os.listdir(os.path.join(d, 'out')) if f.endswith('.xlsx')) == ['작업의뢰서초안_가나호텔_260921_1000_설계.xlsx'])
    chk('폴더와 모음을 연다', len(opened) == 2 and opened[1].endswith('작업의뢰서초안_모음_260927.txt'), opened)
    chk('안내에 넣으실 것', any('납기일(O4 노란칸)' in n for n in G.NOTE))
    G.NOTE[:] = []
    rep2 = G.run('260901', '260930', drive=drive, out=os.path.join(d, 'out'), today=T, template=tpl, opener=opened.append)
    chk('두 번 눌러도 덮어쓰지 않음', rep2['made'] == 0 and rep2['same'] == 1, rep2)
    G.NOTE[:] = []
    rep3 = G.run('260101', '260131', drive=drive, out=os.path.join(d, 'out2'), today=T, template=tpl, opener=opened.append)
    chk('그 기간에 없으면 넓혀 보라고', rep3['sheets'] == 0 and any('날짜를 넓혀' in n for n in G.NOTE))
    G.NOTE[:] = []
    chk('드라이브 없으면 멈추고 알림', G.run('260901', '260930', drive='', today=T) is None and any('드라이브 폴더를 못 찾았' in n for n in G.NOTE))
finally:
    shutil.rmtree(d, ignore_errors=True)

print('')
print('통과 %d / 실패 %d' % (OK[0], len(NG)))
sys.exit(1 if NG else 0)

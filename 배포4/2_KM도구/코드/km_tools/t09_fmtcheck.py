# -*- coding: utf-8 -*-
"""23. 엑셀 서식 검사기 - 숫자 표시형식이 3종 규칙에서 벗어난 칸을 잡는다.
규칙(km-operating-rules 6.8) : 정수/금액 = #,##0  |  배수(소수 10 미만) = 0.0#  |  이윤율 = 0.0"%"
판정은 '값 자체'로 한다. 행 텍스트로 판정하면 옆 표의 '이윤율' 글자가 수량까지 물들인다(실제 사고)."""
import os, sys
from common import *

MONEY, RATE, PCT = '#,##0', '0.0#', '0.0"%"'
PCT_WORDS = ('이윤율', '율(%)')

def want(v, left_texts):
    if isinstance(v, bool) or v is None:
        return None
    if not isinstance(v, (int, float)):
        return None
    if float(v) == int(v):
        return MONEY
    a = abs(float(v))
    if a < 10:
        return RATE
    if 10 <= a < 100 and any(w in t for t in left_texts for w in PCT_WORDS):
        return PCT
    return MONEY

def check(path):
    try:
        import openpyxl
    except ImportError:
        print('openpyxl 이 필요합니다 : pip install openpyxl'); return []
    wb = openpyxl.load_workbook(path, data_only=True)
    bad = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for i, c in enumerate(row):
                lefts = [str(row[j].value) for j in range(max(0, i - 2), i) if row[j].value is not None]
                w = want(c.value, lefts)
                if not w:
                    continue
                got = (c.number_format or '').replace('_-', '').replace('* ', '').strip()
                ok = (w == MONEY and '#,##0' in got) or (w == RATE and '0.0' in got) or (w == PCT and '%' in got)
                if not ok:
                    bad.append([ws.title, c.coordinate, c.value, c.number_format, w])
    return bad

def run(path=None):
    title('23. 엑셀 서식 검사기')
    path = path or ask('검사할 xlsx 경로 > ')
    if not os.path.isfile(path):
        print('파일을 찾지 못했습니다.'); return
    bad = check(path)
    if not bad:
        print('위반 0칸. 통과입니다.'); return
    print('위반 %s칸' % won(len(bad)))
    print('%-14s %-8s %14s %-22s %s' % ('시트', '칸', '값', '지금 서식', '있어야 할 서식'))
    print('-' * 80)
    for b in bad[:50]:
        print('%-14s %-8s %14s %-22s %s' % (b[0][:14], b[1], b[2], str(b[3])[:22], b[4]))
    if len(bad) > 50:
        print('... 외 %s칸' % won(len(bad) - 50))
    o = os.path.join(outdir('서식검사'), '서식위반_%s.csv' % ymd6())
    write_csv(o, bad, ['시트', '칸', '값', '지금서식', '있어야할서식'])
    print('파일 : %s' % o)

if __name__ == '__main__':
    a = sys.argv[1:]
    run(a[0] if a else None); pause()

# -*- coding: utf-8 -*-
# 54판 v11 2026-09-27  (★제안서_PPT.py 가 이 줄의 v숫자로 새 판인지 가린다)
"""deck_core - 회사 표준 서식으로 슬라이드를 그리는 부품. 메뉴 번호 없음.

54번(t54_deck)이 이것을 불러 쓴다. 단독으로 실행하지 않는다.

10번(t15 제안서 후보+초안)과 역할이 다르다.
  10번 = 회의록에서 "자료 달라"는 말을 찾아 무엇을 만들지 고르는 것 (txt 초안)
  26번 = 고른 것을 실제 제출 가능한 pptx 로 뽑는 것

내용은 이미 json 안에 다 들어 있으므로 이 도구는 인터넷도 AI 도 쓰지 않는다. 토큰 0.
현장명을 물어 {{현장}} 자리에 넣으므로, 같은 내용으로 범용본과 현장 맞춤본 둘 다 나온다.
"""
import os, io, json, datetime
from common import *

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -- 회사 표준 디자인 (km-proposal 빌더와 같은 값. 바꾸지 말 것) --
NAVY = RGBColor(0x1F, 0x38, 0x64)
NAVY_D = RGBColor(0x17, 0x28, 0x4A)
BLUE = RGBColor(0x2E, 0x74, 0xB5)
RED = RGBColor(0xC0, 0x00, 0x00)
GREEN_BG = RGBColor(0xE2, 0xEF, 0xD9)
GREEN_TX = RGBColor(0x37, 0x56, 0x23)
GRAY_BG = RGBColor(0xF2, 0xF2, 0xF2)
GRAY_TX = RGBColor(0x59, 0x59, 0x59)
LINE = RGBColor(0xD9, 0xD9, 0xD9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BODY = RGBColor(0x33, 0x33, 0x33)
SKY = RGBColor(0xDE, 0xEA, 0xF6)
FONT = '맑은 고딕'

ML, MW, MTOP = 0.5, 9.0, 0.45
SLIDE_W, SLIDE_H = 10.0, 5.625

SPECS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '제안서_내용')


# ---------- 기본 그리기 ----------
def _tb(slide, x, y, w, h, text, size=11, color=BODY, bold=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=2):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = str(text).split('\n')
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = ln
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
    return box


def _rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, lw=1.0):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    if s.has_text_frame:
        s.text_frame.text = ''
    return s


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _footer(slide, note, page=None):
    _tb(slide, ML, 5.22, MW - 0.6, 0.25, note or '한국마이크로닉(주)', size=8, color=GRAY_TX)
    if page:
        _tb(slide, ML + MW - 0.6, 5.22, 0.6, 0.25, str(page), size=8.5, color=NAVY,
            bold=True, align=PP_ALIGN.RIGHT)


def _fit(text, w, h, size, bold=True, min_size=12, space=2):
    """상자(w×h 인치)에 들어갈 때까지 글자 크기를 1pt 씩 줄인다. 현장명이 길 때 표지·제목이 넘치지 않게.
    재는 법은 deck_check(맑은 고딕 폭)와 같다. deck_check 가 없으면 원래 크기 그대로."""
    try:
        import deck_check as dc
        s = float(size)
        paras = str(text).split('\n')
        while s > min_size:
            n = sum(len(dc._wrap(pp, w, s, bold)) for pp in paras)
            if n * dc._lh(s, bold) + (len(paras) - 1) * space / 72.0 <= h + 0.01:
                return s
            s -= 1
        return float(min_size)
    except Exception:
        return size          # 재지 못하면 원래 크기 그대로 (제안서 만들기는 멈추지 않는다)


def _page_title(slide, title_text, eyebrow=None, pill=None):
    y = MTOP
    if eyebrow:
        _tb(slide, ML, y, 6.0, 0.22, eyebrow, size=9, color=GRAY_TX)
        y += 0.24
    pw = min(3.2, 0.14 * len(pill) + 0.5) if pill else 0.0
    tw = min(7.0, MW - pw - 0.15) if pill else 7.0
    _tb(slide, ML, y, tw, 0.42, title_text, size=_fit(title_text, tw, 0.42, 19, True, 13), color=NAVY, bold=True)
    if pill:
        w = pw
        _rect(slide, ML + MW - w, y + 0.04, w, 0.3, fill=SKY, line=None,
              shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        _tb(slide, ML + MW - w, y + 0.08, w, 0.24, pill, size=9, color=NAVY,
            bold=True, align=PP_ALIGN.CENTER)
    y += 0.5
    _rect(slide, ML, y, MW, 0.02, fill=NAVY)
    return y + 0.18


# ---------- 슬라이드 종류 ----------
def s_cover(slide, d):
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=NAVY)
    _rect(slide, 0, 0, 0.18, SLIDE_H, fill=BLUE)
    _tb(slide, 1.0, 1.55, 8.2, 0.3, d.get('eyebrow', ''), size=11, color=SKY, bold=True)
    t = d.get('title', '')
    _tb(slide, 1.0, 1.95, 8.2, 1.1, t, size=_fit(t, 8.2, 1.1, 30, True, 18, space=4), color=WHITE, bold=True, space=4)
    if d.get('subtitle'):
        _tb(slide, 1.0, 3.15, 8.2, 0.5, d['subtitle'], size=14, color=SKY)
    _rect(slide, 1.0, 3.85, 1.4, 0.03, fill=BLUE)
    _tb(slide, 1.0, 4.1, 8.2, 0.4, d.get('meta', ''), size=10.5, color=LINE)


def s_conclusion(slide, d):
    y = _page_title(slide, d.get('title', '결론'), d.get('eyebrow'), d.get('pill'))
    if d.get('headline'):
        h = 0.62 if len(d['headline']) < 60 else 0.85
        _rect(slide, ML, y, MW, h, fill=GREEN_BG)
        _tb(slide, ML + 0.18, y + 0.1, MW - 0.36, h - 0.2, d['headline'], size=12.5,
            color=GREEN_TX, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        y += h + 0.22
    cards = d.get('cards', [])
    if cards:
        n = len(cards)
        gap = 0.18
        cw = (MW - gap * (n - 1)) / n
        ch = 1.55
        for i, c in enumerate(cards):
            x = ML + i * (cw + gap)
            _rect(slide, x, y, cw, ch, fill=GRAY_BG, line=LINE)
            _rect(slide, x, y, cw, 0.05, fill=BLUE)
            _tb(slide, x + 0.14, y + 0.16, cw - 0.28, 0.24, c.get('label', ''), size=9.5,
                color=GRAY_TX, bold=True)
            _tb(slide, x + 0.14, y + 0.44, cw - 0.28, 0.42, c.get('big', ''), size=14,
                color=NAVY, bold=True)
            _tb(slide, x + 0.14, y + 0.92, cw - 0.28, ch - 1.02, c.get('body', ''), size=9.5,
                color=BODY)
        y += ch + 0.2
    if d.get('banner'):
        _rect(slide, ML, y, MW, 0.52, fill=None, line=RED, lw=1.25)
        _tb(slide, ML + 0.16, y + 0.1, MW - 0.32, 0.34, d['banner'], size=10,
            color=RED, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def s_table(slide, d):
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    headers = d.get('headers', [])
    rows = d.get('rows', [])
    colw = d.get('colW') or [MW / max(1, len(headers))] * len(headers)
    note_h = 0.34 if d.get('note') else 0.0
    avail = 5.05 - y - note_h
    nrow = len(rows) + 1
    rh = max(0.24, min(0.80, avail / nrow))
    shape = slide.shapes.add_table(nrow, len(headers), Inches(ML), Inches(y),
                                   Inches(sum(colw)), Inches(rh * nrow))
    tbl = shape.table
    tbl.first_row = True
    for j, w in enumerate(colw):
        tbl.columns[j].width = Inches(w)
    for i in range(nrow):
        tbl.rows[i].height = Inches(rh)
    data = [headers] + rows
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (
                WHITE if i % 2 else RGBColor(0xF7, 0xF9, 0xFC))
            tf = cell.text_frame
            tf.word_wrap = True
            for k, ln in enumerate(str(val).split('\n')):
                p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                p.space_after = Pt(0)
                r = p.add_run()
                r.text = ln
                r.font.name = FONT
                r.font.size = Pt(9 if i == 0 else 8.5)
                r.font.bold = (i == 0)
                r.font.color.rgb = WHITE if i == 0 else BODY
    if d.get('note'):
        _tb(slide, ML, y + rh * nrow + 0.08, MW, 0.3, '※ ' + d['note'], size=8.5, color=GRAY_TX)


def s_items(slide, d):
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    if d.get('lead'):
        _tb(slide, ML, y, MW, 0.3, d['lead'], size=10.5, color=GRAY_TX)
        y += 0.36
    items = d.get('items', [])
    box = d.get('box')
    box_h = 0.0
    if box:
        box_h = 0.42 + 0.26 * len(box.get('lines', []))
    avail = 5.05 - y - (box_h + 0.18 if box else 0)
    ih = min(0.62, max(0.34, avail / max(1, len(items))))
    for i, it in enumerate(items):
        yy = y + i * ih
        _rect(slide, ML, yy + 0.03, 0.26, 0.26, fill=BLUE, shape=MSO_SHAPE.OVAL)
        _tb(slide, ML, yy + 0.06, 0.26, 0.2, str(i + 1), size=9.5, color=WHITE,
            bold=True, align=PP_ALIGN.CENTER)
        _tb(slide, ML + 0.38, yy + 0.02, MW - 2.5, 0.28, it.get('text', ''), size=11,
            color=BODY, bold=True)
        if it.get('desc'):
            _tb(slide, ML + MW - 2.0, yy + 0.04, 2.0, 0.26, '[ %s ]' % it['desc'],
                size=9.5, color=BLUE, bold=True, align=PP_ALIGN.RIGHT)
    if box:
        by = 5.05 - box_h
        _rect(slide, ML, by, MW, box_h, fill=GRAY_BG, line=LINE)
        _tb(slide, ML + 0.16, by + 0.08, MW - 0.32, 0.24,
            box.get('title', '확인 · 협의 사항'), size=10, color=NAVY, bold=True)
        for i, ln in enumerate(box.get('lines', [])):
            _tb(slide, ML + 0.28, by + 0.36 + i * 0.26, MW - 0.5, 0.24, '· ' + ln,
                size=9.5, color=BODY)


def s_diagram(slide, d):
    """구성도를 그림이 아니라 도형으로 그린다 - 파워포인트에서 직접 고칠 수 있다."""
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    if d.get('lead'):
        _tb(slide, ML, y, MW, 0.3, d['lead'], size=10, color=GRAY_TX)
        y += 0.34
    STYLE = {'main': (NAVY, WHITE), 'device': (SKY, NAVY), 'sub': (GRAY_BG, GRAY_TX),
             'alert': (RED, WHITE)}                      # alert = 법적 의무 등 빠지면 안 되는 것
    canvas = d.get('canvas', [10.0, 3.0])
    steps = d.get('steps', [])
    ch = (1.55 if steps else 2.9)
    sx, sy = MW / canvas[0], ch / canvas[1]
    pos = {}
    boxes = d.get('boxes', [])

    def _holds(o, i):                                     # o 가 i 를 품는가 (방 안의 표시)
        return (o is not i and o['x'] <= i['x'] and o['y'] <= i['y']
                and i['x'] + i['w'] <= o['x'] + o['w'] + 1e-6 and i['y'] + i['h'] <= o['y'] + o['h'] + 1e-6)
    for b in boxes:
        x = ML + b['x'] * sx
        yy = y + b['y'] * sy
        w, h = b['w'] * sx, b['h'] * sy
        pos[b['id']] = (x, yy, w, h)
        fill, tx = STYLE.get(b.get('style', 'sub'), STYLE['sub'])
        _rect(slide, x, yy, w, h, fill=fill, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        body = b.get('title', '')
        for ln in b.get('lines', []):
            body += '\n' + ln
        if any(_holds(b, o) for o in boxes):
            # 방처럼 다른 표시를 품은 상자 : 이름을 오른쪽 아래 구석으로 (가운데 두면 표시와 겹친다)
            _tb(slide, x + 0.06, yy + h - 0.3, w - 0.14, 0.26, body, size=b.get('fs', 9),
                color=tx, bold=True, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.BOTTOM, space=0)
            continue
        _tb(slide, x + 0.06, yy + 0.05, w - 0.12, h - 0.1, body, size=b.get('fs', 9),
            color=tx, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
    for lk in d.get('links', []):
        a, b = pos.get(lk['from']), pos.get(lk['to'])
        if not a or not b:
            continue
        col = BLUE if lk.get('style', 'comm') == 'comm' else (
            RED if lk['style'] == 'power' else GRAY_TX)
        ac, bc = a[0] + a[2] / 2, b[0] + b[2] / 2
        y_over = max(a[1], b[1]) < min(a[1] + a[3], b[1] + b[3])
        x_over = max(a[0], b[0]) < min(a[0] + a[2], b[0] + b[2])
        if abs(a[1] - b[1]) < 0.05 or (y_over and not x_over):   # 가로
            x1 = (a[0] + a[2]) if a[0] < b[0] else (b[0] + b[2])
            x2 = b[0] if a[0] < b[0] else a[0]
            if abs(a[1] - b[1]) < 0.05:
                yy = a[1] + a[3] / 2
            else:
                yy = (max(a[1], b[1]) + min(a[1] + a[3], b[1] + b[3])) / 2
            _rect(slide, x1, yy - 0.01, max(0.02, x2 - x1), 0.025, fill=col)
            if lk.get('label'):
                _tb(slide, x1, yy - 0.28, max(0.5, x2 - x1), 0.24, lk['label'], size=8,
                    color=col, bold=True, align=PP_ALIGN.CENTER)
        elif x_over:                                      # 세로
            if b[0] <= ac <= b[0] + b[2]:
                xx = ac
            elif a[0] <= bc <= a[0] + a[2]:
                xx = bc
            else:
                xx = (max(a[0], b[0]) + min(a[0] + a[2], b[0] + b[2])) / 2
            y1 = (a[1] + a[3]) if a[1] < b[1] else (b[1] + b[3])
            y2 = b[1] if a[1] < b[1] else a[1]
            _rect(slide, xx - 0.01, y1, 0.025, max(0.02, y2 - y1), fill=col)
            if lk.get('label'):
                _tb(slide, xx + 0.08, y1, 2.4, 0.22, lk['label'], size=8, color=col, bold=True)
        else:                                             # 대각 자리 -> ㄱ자로 꺾는다
            top, low = (a, b) if a[1] < b[1] else (b, a)
            tx = top[0] + top[2] / 2                      # 위 상자 아래 가운데에서 내려와
            my = low[1] + low[3] / 2                      # 아래 상자 가운데 높이에서 꺾는다
            _rect(slide, tx - 0.01, top[1] + top[3], 0.025, max(0.02, my - top[1] - top[3]), fill=col)
            if low[0] > tx:
                x1, x2 = tx, low[0]
            else:
                x1, x2 = low[0] + low[2], tx
            _rect(slide, x1 - 0.01, my - 0.01, max(0.02, x2 - x1) + 0.02, 0.025, fill=col)
            if lk.get('label'):
                _tb(slide, x1, my - 0.28, max(0.5, x2 - x1), 0.24, lk['label'], size=8,
                    color=col, bold=True, align=PP_ALIGN.CENTER)
    if steps:
        by = 5.05 - 1.15
        n = len(steps)
        gap = 0.14
        cw = (MW - gap * (n - 1)) / n
        for i, st in enumerate(steps):
            x = ML + i * (cw + gap)
            _rect(slide, x, by, cw, 1.1, fill=GRAY_BG, line=LINE)
            _rect(slide, x + 0.1, by + 0.1, 0.24, 0.24, fill=BLUE, shape=MSO_SHAPE.OVAL)
            _tb(slide, x + 0.1, by + 0.13, 0.24, 0.2, st.get('num', str(i + 1)), size=9,
                color=WHITE, bold=True, align=PP_ALIGN.CENTER)
            _tb(slide, x + 0.42, by + 0.12, cw - 0.52, 0.24, st.get('text', ''), size=9.5,
                color=NAVY, bold=True)
            _tb(slide, x + 0.1, by + 0.42, cw - 0.2, 0.22, '[ %s ]' % st.get('who', ''),
                size=8.5, color=BLUE, bold=True)
            _tb(slide, x + 0.1, by + 0.66, cw - 0.2, 0.4, st.get('desc', ''), size=8, color=BODY)


def s_split(slide, d):
    """좌우 비교. 박스 높이는 줄 수에 맞춘다 (빈 박스가 아래로 길게 남지 않게)."""
    y = _page_title(slide, d.get('title', ''), d.get('eyebrow'), d.get('pill'))
    cw = (MW - 0.24) / 2
    n = max([len(d.get(sd, {}).get('lines', [])) for sd in ('left', 'right')] + [1])
    step = 0.42
    h = min(5.0 - y, 0.66 + n * step + 0.18)
    for i, side in enumerate(('left', 'right')):
        blk = d.get(side, {})
        x = ML + i * (cw + 0.24)
        _rect(slide, x, y, cw, h, fill=(GRAY_BG if i == 0 else SKY), line=LINE)
        _rect(slide, x, y, cw, 0.05, fill=(GRAY_TX if i == 0 else BLUE))
        _tb(slide, x + 0.18, y + 0.16, cw - 0.36, 0.32, blk.get('label', ''), size=12.5,
            color=(GRAY_TX if i == 0 else NAVY), bold=True)
        for j, ln in enumerate(blk.get('lines', [])):
            _tb(slide, x + 0.3, y + 0.66 + j * step, cw - 0.5, 0.34, '· ' + ln, size=11,
                color=BODY)
    if d.get('note') and y + h + 0.7 <= 5.05:
        _rect(slide, ML, y + h + 0.2, MW, 0.5, fill=GREEN_BG)
        _tb(slide, ML + 0.2, y + h + 0.2, MW - 0.4, 0.5, d['note'], size=11, color=NAVY,
            bold=True, anchor=MSO_ANCHOR.MIDDLE)


def s_request(slide, d):
    _rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=NAVY)
    _rect(slide, 0, 0, 0.18, SLIDE_H, fill=BLUE)
    _tb(slide, 0.9, 0.55, 8.4, 0.45, d.get('title', '요청드리는 사항'), size=22,
        color=WHITE, bold=True)
    if d.get('lead'):
        _tb(slide, 0.9, 1.08, 8.4, 0.3, d['lead'], size=11, color=SKY)
    y = 1.6
    for i, it in enumerate(d.get('items', [])):
        _rect(slide, 0.9, y + 0.02, 0.26, 0.26, fill=BLUE, shape=MSO_SHAPE.OVAL)
        _tb(slide, 0.9, y + 0.05, 0.26, 0.2, str(i + 1), size=9.5, color=WHITE,
            bold=True, align=PP_ALIGN.CENTER)
        _tb(slide, 1.3, y, 8.0, 0.28, it.get('text', ''), size=12, color=WHITE, bold=True)
        if it.get('desc'):
            _tb(slide, 1.3, y + 0.3, 8.0, 0.26, it['desc'], size=9.5, color=LINE)
        y += 0.72
    if d.get('contact'):
        _rect(slide, 0.9, 4.75, 8.4, 0.02, fill=BLUE)
        _tb(slide, 0.9, 4.9, 8.4, 0.3, d['contact'], size=10, color=SKY)




def s_toc(slide, d):
    """목차. 항목이 많아 한 줄 높이가 낮아지면(현장 물량 장이 끼면 6~7개) 글자를 줄여
    설명 글이 구분선을 넘지 않게 한다 (2026-09-27 실제 엔진 렌더에서 찾음)."""
    y = _page_title(slide, d.get('title', '목차'), d.get('eyebrow', 'CONTENTS'))
    items = d.get('items', [])
    n = max(1, len(items))
    h = min(0.72, (5.0 - y) / n)
    tight = h < 0.62
    ts, ds = (11.5, 8.5) if tight else (12.5, 9.5)
    ty, dy = (0.03, 0.26) if tight else (0.06, 0.34)
    for i, it in enumerate(items):
        yy = y + i * h
        _rect(slide, ML, yy + 0.04, 0.42, h - 0.14, fill=NAVY)
        _tb(slide, ML, yy + 0.08, 0.42, h - 0.22, '%02d' % (i + 1), size=11,
            color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        _tb(slide, ML + 0.58, yy + ty, 5.4, 0.26, it.get('text', ''), size=ts,
            color=NAVY, bold=True)
        if it.get('desc'):
            _tb(slide, ML + 0.58, yy + dy, 5.4, 0.2, it['desc'], size=ds, color=GRAY_TX, space=0)
        if it.get('page'):
            _tb(slide, ML + MW - 1.2, yy + ty + 0.02, 1.2, 0.28, str(it['page']), size=10.5,
                color=BLUE, bold=True, align=PP_ALIGN.RIGHT)
        _rect(slide, ML, yy + h - 0.06, MW, 0.01, fill=LINE)


YELLOW = RGBColor(0xFF, 0xF8, 0xDC)


def s_reply(slide, d):
    """질의 · 당사 답변 · 귀사 회신란(빈칸). 협의서는 답이 돌아와야 완성이다."""
    y = _page_title(slide, d.get('title', '질의 · 답변'), d.get('eyebrow'), d.get('pill'))
    rows = d.get('rows', [])
    heads = ['No', '질의 · 협의 항목', '당사 답변', '귀사 회신']
    colw = [0.45, 2.55, 3.4, 2.6]
    nrow = len(rows) + 1
    avail = 5.0 - y - (0.32 if d.get('note') else 0)
    rh = max(0.3, min(0.78, avail / nrow))
    tbl = slide.shapes.add_table(nrow, 4, Inches(ML), Inches(y), Inches(sum(colw)),
                                 Inches(rh * nrow)).table
    for j, w in enumerate(colw):
        tbl.columns[j].width = Inches(w)
    for i in range(nrow):
        tbl.rows[i].height = Inches(rh)
    data = [heads] + [[str(k + 1), r.get('item', ''), r.get('ours', ''), r.get('theirs', '')]
                      for k, r in enumerate(rows)]
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.07)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = NAVY
            elif j == 3:
                c.fill.fore_color.rgb = YELLOW
            else:
                c.fill.fore_color.rgb = WHITE if i % 2 else RGBColor(0xF7, 0xF9, 0xFC)
            tf = c.text_frame
            tf.word_wrap = True
            for k, ln in enumerate(str(val).split('\n')):
                para = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                r = para.add_run()
                r.text = ln
                r.font.name = FONT
                r.font.size = Pt(9 if i == 0 else 8.5)
                r.font.bold = (i == 0 or j == 0)
                r.font.color.rgb = WHITE if i == 0 else BODY
                if j == 0:
                    para.alignment = PP_ALIGN.CENTER
    if d.get('note'):
        _tb(slide, ML, y + rh * nrow + 0.08, MW, 0.3, '※ ' + d['note'], size=8.5, color=GRAY_TX)

KIND = {'cover': s_cover, 'toc': s_toc, 'reply': s_reply, 'conclusion': s_conclusion, 'table': s_table, 'items': s_items,
        'diagram': s_diagram, 'split': s_split, 'request': s_request}


# ---------- 조립 ----------
def fill(obj, mapping):
    if isinstance(obj, str):
        for k, v in mapping.items():
            obj = obj.replace(k, v)
        return obj
    if isinstance(obj, list):
        return [fill(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return dict((k, fill(v, mapping)) for k, v in obj.items())
    return obj


def resolve_toc(slides):
    """목차 쪽번호를 손으로 적지 않고 만들 때 센다 (2026-09-27 : 손으로 적은 번호가 3건에서 틀려 있었다).
    목차 항목의 goto 와 제목이 같은 장(없으면 goto 가 제목에 든 장)의 쪽번호를 넣는다.
    못 찾으면 번호를 비운다 - 틀린 번호보다 없는 것이 낫다. 못 찾은 항목 목록을 돌려준다."""
    pages, n = [], 0
    for sl in slides:
        if sl.get('type') in ('cover', 'request'):
            pages.append(None)
        else:
            n += 1
            pages.append(n)
    miss = []
    for ti, sl in enumerate(slides):
        if sl.get('type') != 'toc':
            continue
        for it in sl.get('items', []):
            key = (it.get('goto') or '').strip()
            if not key:
                continue                                  # goto 없는 옛 형식은 적힌 번호 그대로
            hit = None
            for want_exact in (True, False):
                for j in range(ti + 1, len(slides)):
                    t = (slides[j].get('title') or '').strip()
                    if pages[j] and ((t == key) if want_exact else (key in t)):
                        hit = pages[j]
                        break
                if hit:
                    break
            it['page'] = hit
            if not hit:
                miss.append(it.get('text', key))
    return miss


def build(spec, out_path):
    resolve_toc(spec.get('slides', []))
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    foot = spec.get('footer', '한국마이크로닉(주)')
    page = 0
    for i, sl in enumerate(spec.get('slides', [])):
        fn = KIND.get(sl.get('type'))
        if not fn:
            raise ValueError('모르는 슬라이드 종류: %s (%d번째 장)' % (sl.get('type'), i + 1))
        slide = _blank(prs)
        fn(slide, sl)
        if sl.get('type') not in ('cover', 'request'):
            page += 1
            _footer(slide, foot, page)
    prs.save(out_path)
    return len(spec.get('slides', []))


def load_specs():
    out = []
    if not os.path.isdir(SPECS):
        return out
    for name in sorted(os.listdir(SPECS)):
        if not name.lower().endswith('.json'):
            continue
        p = os.path.join(SPECS, name)
        try:
            d = json.loads(io.open(p, encoding='utf-8-sig').read())   # 메모장이 붙이는 BOM 도 읽는다
            out.append((p, d))
        except Exception as e:
            print('  건너뜀 : %s (%s)' % (name, e))
    return out


def run():
    """부품이라 단독으로 돌리지 않는다. 옛 「26번」 길로 들어와도 54번(t54_deck)으로 보낸다
    - 만드는 길이 둘이면 한쪽만 고쳐지는 일이 생긴다 (2026-09-27 감사)."""
    import t54_deck
    t54_deck.run()


def next_free(folder, stem, ext='.pptx'):
    """덮어쓰지 않는다 (프로님 규칙). 같은 이름이 있으면 _r2, _r3 ...
    파워포인트가 잡고 있는 파일(~$ 잠금 파일이 있는 것)도 피한다."""
    n = 1
    while True:
        f = os.path.join(folder, '%s_r%d%s' % (stem, n, ext))
        if not os.path.exists(f) and not os.path.exists(os.path.join(folder, '~$' + os.path.basename(f))):
            return f
        n += 1


if __name__ == '__main__':
    run(); pause()

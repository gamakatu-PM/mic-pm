#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
km_docx_fix_v2_260916.py  (v2.0 / 2026-09-16)
km_meeting_v1.py 가 만든 회의록 .docx 완성본의 1부 서식만 고쳐 쓰는 후처리기.

고치는 것 4가지 (2026-09-16 배성윤 프로 지시):
  A1. 「안건별 협의 내용」 4칸 표(안건|협의내용|결정사항|조치사항)를
      → 협의 1건 = 세로 블록표(협의 N / 안건 / 협의내용 / 결정 사항 / 조치 사항)로 바꿔
        협의내용 칸이 좁아 글이 뭉치는 문제를 없앤다.
  B1. 제목 「안건별 협의 내용 (협의 순서대로)」 → 괄호 삭제 → 「안건별 협의 내용」
  C1. 「협의 건수 N건」 줄·행 삭제 (문단·머리표 양쪽 다)
  B2. 「확인·회신 요청 사항」 항목: " — " 앞은 빨강 굵게, " — " 뒤는 검정

덤: 중요 일정 브리핑 메일 본문을 같이 만든다 (기본 수신: bsy@micronic.co.kr).
    파일만 만들고 보내지는 않는다 — 발송은 Claude(Gmail) 또는 --smtp 옵션.

사용:
  python3 km_docx_fix_v2_260916.py <회의록.docx> [--out 새파일.docx] [--mailto bsy@micronic.co.kr]
  python3 km_docx_fix_v2_260916.py --dir <출력폴더 루트>      # 폴더 전수 처리

원본은 덮어쓰지 않는다. 기본 출력은 같은 폴더의 "<원래이름>_v2.docx".
"""
import argparse, copy, glob, json, os, re, sys

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RED = RGBColor(0xC0, 0x00, 0x00)
BLACK = RGBColor(0x00, 0x00, 0x00)
LABEL_FILL = "F2F2F2"
HEAD_FILL = "DCE6F1"

AGENDA_HEAD = "안건별 협의 내용"
REQ_HEAD = "확인·회신 요청 사항"
SCHED_HEAD = "일정"
COUNT_RE = re.compile(r"^협의\s*건수\s*[:：]?\s*\d+\s*건\.?$")
DASH_RE = re.compile(r"\s+[—–-]\s+")          # " — " / " – " / " - "
LABELS = ("안건", "협의내용", "결정 사항", "조치 사항")


# ---------------- 공통 유틸 ----------------
def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def fix_widths(table, widths):
    table.autofit = False
    tblPr = table._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = table._tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w.twips)))
    for row in table.rows:
        for c, w in zip(row.cells, widths):
            c.width = w


def is_heading(par):
    """_h1()로 찍힌 소제목인가 — 굵게+밑줄."""
    runs = par.runs
    return bool(runs) and bool(runs[0].bold) and bool(runs[0].underline)


def cell_lines(cell):
    """셀 안의 줄들을 문단·수동 줄바꿈까지 살려서 뽑는다."""
    out = []
    for p in cell.paragraphs:
        buf = ""
        for r in p.runs:
            for i, chunk in enumerate(r.text.split("\n")):
                if i:
                    out.append(buf); buf = ""
                buf += chunk
            if r._r.findall(qn("w:br")):
                out.append(buf); buf = ""
        out.append(buf)
    return [x.strip() for x in out if x.strip()]


def set_cell(cell, lines, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    for i, ln in enumerate(lines or [""]):
        if i:
            p.add_run().add_break()
        r = p.add_run(ln)
        r.bold = bold
        if color is not None:
            r.font.color.rgb = color


def body_items(doc):
    """본문 자식 요소를 순서대로 (kind, obj)로 돌려준다."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield "p", Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield "t", Table(child, doc)


# ---------------- A1. 협의 표 → 세로 블록 ----------------
def is_agenda_table(table):
    if len(table.columns) != 4:
        return False
    head = [c.text.strip().replace(" ", "") for c in table.rows[0].cells]
    return head[:4] == ["안건", "협의내용", "결정사항", "조치사항"]


def build_block(doc, idx, values):
    """협의 1건짜리 세로 블록표를 만들어 element만 돌려준다."""
    t = doc.add_table(rows=1 + len(LABELS), cols=2)
    t.style = "Table Grid"

    head = t.rows[0].cells
    head[0].merge(head[1])
    set_cell(t.rows[0].cells[0], [f"협의 {idx}"], bold=True)
    shade(t.rows[0].cells[0], HEAD_FILL)

    for i, label in enumerate(LABELS, start=1):
        a, b = t.rows[i].cells
        set_cell(a, [label], bold=True)
        shade(a, LABEL_FILL)
        set_cell(b, values[i - 1] or ["없음"])

    fix_widths(t, (Cm(2.6), Cm(14.0)))
    el = t._tbl
    el.getparent().remove(el)          # 문서 끝에 붙은 것을 떼어낸다
    return el


def rebuild_agenda(doc, table):
    """4칸 표를 협의별 세로 블록표 묶음으로 갈아끼운다. 바꾼 건수를 돌려준다."""
    rows = []
    for row in table.rows[1:]:
        cells = row.cells
        vals = [cell_lines(c) for c in cells[:4]]
        if not any(vals):
            continue
        if len(vals[0]) == 1 and vals[0][0] == "없음" and not any(vals[1:]):
            continue
        rows.append(vals)
    if not rows:
        return 0

    anchor = table._tbl
    for i, vals in enumerate(rows, start=1):
        anchor.addprevious(build_block(doc, i, vals))
        spacer = doc.add_paragraph()
        sp = spacer._p; sp.getparent().remove(sp)
        anchor.addprevious(sp)
    anchor.getparent().remove(anchor)
    return len(rows)


# ---------------- B2. 확인·회신 색 ----------------
def color_request(par):
    text = "".join(r.text for r in par.runs) or par.text
    text = text.strip()
    if not text or text == "없음":
        return False
    m = DASH_RE.search(text)
    if not m:
        return False
    front, rear = text[:m.start()].strip(), text[m.end():].strip()
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    r1 = par.add_run(front); r1.bold = True; r1.font.color.rgb = RED
    r2 = par.add_run(f" — {rear}"); r2.bold = False; r2.font.color.rgb = BLACK
    return True


# ---------------- 브리핑 ----------------
def collect_brief(doc):
    """머리표·일정표·확인회신·결정사항을 긁어 브리핑 재료를 만든다."""
    info, sched, reqs, decisions = {}, [], [], []
    section = None
    for kind, obj in body_items(doc):
        if kind == "p":
            if is_heading(obj):
                t = obj.text.strip()
                section = ("req" if t.startswith(REQ_HEAD)
                           else "sched" if t.startswith(SCHED_HEAD)
                           else "agenda" if t.startswith(AGENDA_HEAD) else None)
            elif section == "req":
                t = obj.text.strip()
                if t and t != "없음":
                    reqs.append(t)
            continue
        # 표
        if len(obj.columns) == 2:
            for row in obj.rows:
                k = row.cells[0].text.strip()
                v = row.cells[1].text.strip()
                if k in ("현장", "일자", "협의자", "안건") and k not in info:
                    info[k] = v
                if k == "결정 사항" and v and v != "없음":
                    decisions.append(v)
        if section == "sched" and len(obj.columns) == 3 and obj.rows[0].cells[0].text.strip() == "구분":
            for row in obj.rows[1:]:
                cells = [c.text.strip() for c in row.cells[:3]]
                if any(cells) and cells[0] != "없음":
                    sched.append(cells)
            section = None
    return info, sched, reqs, decisions


def brief_text(info, sched, reqs, decisions):
    L = []
    L.append(f"[{info.get('현장', '현장미상')}] 회의 일정 브리핑 ({info.get('일자', '')})")
    L.append("")
    L.append(f"협의자 : {info.get('협의자', '')}")
    if info.get("안건"):
        L.append(f"안건   : {info['안건']}")
    L.append("")
    L.append("■ 일정")
    if sched:
        for g, d, note in sched:
            L.append(f"  - {g} : {d}" + (f"  ({note})" if note else ""))
    else:
        L.append("  - 없음")
    L.append("")
    L.append("■ 확인·회신 요청")
    for x in reqs or ["없음"]:
        L.append(f"  - {x}")
    L.append("")
    L.append("■ 결정 사항")
    for x in decisions or ["없음"]:
        L.append(f"  - {x}")
    L.append("")
    L.append("※ 본 브리핑은 회의록 문서(1부 협의록)에서 자동 추출한 것입니다.")
    return "\n".join(L)


# ---------------- main ----------------
def process(path, out_path=None, mailto="bsy@micronic.co.kr"):
    doc = Document(path)
    stat = {"A": 0, "B": 0, "C": 0}

    # B1 / C1 — 제목 괄호 삭제, 협의 건수 삭제
    for kind, obj in list(body_items(doc)):
        if kind != "p":
            continue
        t = obj.text.strip()
        if COUNT_RE.match(t):
            obj._p.getparent().remove(obj._p); stat["C"] += 1
            continue
        if t.startswith(AGENDA_HEAD) and "(" in t:
            new = re.sub(r"\s*\(.*?\)\s*$", "", t)
            for r in list(obj.runs)[1:]:
                r._r.getparent().remove(r._r)
            obj.runs[0].text = new
            stat["B"] += 1

    # C1 — 머리표 안의 "협의 건수" 행도 삭제
    for kind, obj in list(body_items(doc)):
        if kind != "t" or len(obj.columns) != 2:
            continue
        for row in list(obj.rows):
            if row.cells[0].text.strip().replace(" ", "") == "협의건수":
                row._tr.getparent().remove(row._tr); stat["C"] += 1

    # A1 — 협의 표 갈아끼우기
    for kind, obj in list(body_items(doc)):
        if kind == "t" and is_agenda_table(obj):
            stat["A"] += rebuild_agenda(doc, obj)

    # B2 — 확인·회신 색
    section = None
    for kind, obj in body_items(doc):
        if kind != "p":
            section = None if section == "req" else section
            continue
        if is_heading(obj):
            section = "req" if obj.text.strip().startswith(REQ_HEAD) else None
            continue
        if section == "req" and color_request(obj):
            stat["B"] += 1

    out_path = out_path or re.sub(r"\.docx$", "_v2.docx", path)
    doc.save(out_path)

    info, sched, reqs, decisions = collect_brief(Document(out_path))
    body = brief_text(info, sched, reqs, decisions)
    folder = os.path.dirname(os.path.abspath(out_path))
    subject = f"[회의 일정 브리핑] {info.get('현장', '현장미상')} {info.get('일자', '')}"
    with open(os.path.join(folder, "00_브리핑_메일.txt"), "w", encoding="utf-8") as f:
        f.write(f"To: {mailto}\nSubject: {subject}\n\n{body}\n")
    json.dump({"to": mailto, "subject": subject, "body": body, "docx": out_path},
              open(os.path.join(folder, "00_브리핑_메일.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return {"in": path, "out": out_path, "changed": stat, "mail": os.path.join(folder, "00_브리핑_메일.json")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="?")
    ap.add_argument("--dir")
    ap.add_argument("--out")
    ap.add_argument("--mailto", default="bsy@micronic.co.kr")
    a = ap.parse_args()
    targets = []
    if a.dir:
        targets = [p for p in glob.glob(os.path.join(a.dir, "**", "*.docx"), recursive=True)
                   if "_v2.docx" not in p and "회의록_" in os.path.basename(p)]
    elif a.docx:
        targets = [a.docx]
    else:
        raise SystemExit("회의록 .docx 경로 또는 --dir 를 주십시오.")
    res = [process(p, a.out if len(targets) == 1 else None, a.mailto) for p in targets]
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

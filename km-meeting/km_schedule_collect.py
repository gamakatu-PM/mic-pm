#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
km_schedule_collect.py  (v1.0 / 2026-09-16)
「1.현장」 폴더 전체를 훑어 날짜별 일정 브리핑을 만든다. 토큰 0 — 클로드 없이 PC에서 돈다.

읽는 것 (회의 폴더마다 있으면 있는 대로):
  - calendar_jobs.json           ← km_meeting_v1.py 가 만든 할 일 (date-only)
  - *회의록*.docx 의 「일정」 표   ← 구분 | 일자 | 비고   (YYMMDD 가 있으면 날짜, 없으면 '날짜 미정')
  - 회의록 docx 수정시각          ← "어제 이후 새로 생긴 회의록" 판정

만드는 것 (--out 폴더, 매번 새로 씀):
  00_일정브리핑.txt    ← 메일 본문 그대로 (날짜별, 1. 날짜/현장명/일정)
  00_일정브리핑.json   ← 클로드(아침 5시 루틴)가 읽어 메일·캘린더에 쓰는 원천
  00_중요키워드.txt    ← 없으면 기본값으로 만들어 줌. 여기 있는 낱말이 들어간 일정 = 중요(빨강)

사용:
  python km_schedule_collect.py --root "C:\\Users\\gamak\\OneDrive\\26년도 현장\\!!클로드가 저장하는 폴더\\plaud\\26년\\1.현장"
        [--out <보고 폴더>] [--days 14] [--today 2026-09-16]
  --out 을 구글 드라이브 데스크탑 폴더로 주면 클로드가 그 파일을 읽는다.
"""
import argparse, datetime as dt, glob, json, os, re, sys

DEFAULT_KEYWORDS = ["납품", "납기", "입고", "출고", "계약", "선급금", "수금", "계산서", "시운전", "준공"]
WEEK = "월화수목금토일"
DATE6 = re.compile(r"(?<!\d)(\d{6})(?!\d)")
STAGE_SKIP = ("없음",)


def ymd6(s):
    m = DATE6.search(s or "")
    if not m:
        return None
    d6 = m.group(1)
    try:
        return dt.date(2000 + int(d6[:2]), int(d6[2:4]), int(d6[4:6]))
    except ValueError:
        return None


def k_date(d):
    return f"{d.month}월 {d.day}일({WEEK[d.weekday()]})"


def load_keywords(out):
    p = os.path.join(out, "00_중요키워드.txt")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write("# 한 줄에 낱말 하나. 이 낱말이 들어간 일정은 중요(빨강)로 표시되고 구글 캘린더에도 올라간다.\n")
            f.write("\n".join(DEFAULT_KEYWORDS) + "\n")
    kws = []
    for ln in open(p, encoding="utf-8"):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            kws.append(ln)
    return kws


def site_of(path, root):
    rel = os.path.relpath(path, root)
    return rel.split(os.sep)[0]


def meeting_label(folder):
    """회의 폴더명 YYMMDD_회사_이름직함_핵심 → '260915 연합기술사 김이사'"""
    parts = os.path.basename(folder).split("_")
    return " ".join(parts[:3]) if len(parts) >= 3 else os.path.basename(folder)


def read_docx_schedule(path):
    """docx 「일정」표(구분|일자|비고)를 [(구분, 일자문구, 비고)]로. python-docx 없으면 빈 목록."""
    try:
        from docx import Document
        from docx.oxml.ns import qn
    except ImportError:
        return []
    rows = []
    try:
        doc = Document(path)
    except Exception:
        return []
    for t in doc.tables:
        if len(t.columns) != 3:
            continue
        head = [c.text.strip() for c in t.rows[0].cells]
        if head[:3] != ["구분", "일자", "비고"]:
            continue
        for r in t.rows[1:]:
            c = [x.text.strip() for x in r.cells[:3]]
            if c[0] and c[0] not in STAGE_SKIP:
                rows.append(tuple(c))
        break
    return rows


def collect(root, today, days, keywords):
    items = []          # {"date": iso|None, "site", "what", "note", "src", "important", "meeting"}
    new_docs = []       # 어제 이후 생긴 회의록
    since = dt.datetime.combine(today - dt.timedelta(days=1), dt.time(5, 0))
    seen = set()

    for cj in glob.glob(os.path.join(root, "**", "calendar_jobs.json"), recursive=True):
        folder = os.path.dirname(cj)
        site = site_of(cj, root)
        try:
            jobs = json.load(open(cj, encoding="utf-8"))
        except Exception:
            continue
        for j in jobs:
            what = re.sub(r"^\[.*?\]\s*", "", j.get("summary", "")).strip()
            what = re.sub(r"^\[미정\]\s*", "", what)
            what = re.sub(r"^\[.*?\]\s*", "", what)
            undated = "[미정]" in j.get("summary", "")
            key = (site, what)
            if key in seen:
                continue
            seen.add(key)
            items.append({"date": None if undated else j.get("date"), "site": site, "what": what,
                          "note": "", "src": "calendar_jobs", "meeting": meeting_label(folder)})

    for dx in glob.glob(os.path.join(root, "**", "*회의록*.docx"), recursive=True):
        if "_v2.docx" in dx or os.path.basename(dx).startswith("~$"):
            continue
        site = site_of(dx, root)
        folder = os.path.dirname(dx)
        mtime = dt.datetime.fromtimestamp(os.path.getmtime(dx))
        if mtime >= since:
            new_docs.append({"site": site, "meeting": meeting_label(folder), "file": os.path.basename(dx),
                             "time": mtime.strftime("%m-%d %H:%M")})
        for stage, when, note in read_docx_schedule(dx):
            d = ymd6(when)
            key = (site, stage, when)
            if key in seen:
                continue
            seen.add(key)
            items.append({"date": d.isoformat() if d else None, "site": site, "what": stage,
                          "note": " · ".join(x for x in (when if not d else "", note) if x),
                          "src": "일정표", "meeting": meeting_label(folder)})

    for it in items:
        text = f"{it['what']} {it['note']}"
        it["important"] = any(k in text for k in keywords)

    horizon = today + dt.timedelta(days=days)
    overdue = sorted([i for i in items if i["date"] and dt.date.fromisoformat(i["date"]) < today], key=lambda x: x["date"])
    upcoming = sorted([i for i in items if i["date"] and today <= dt.date.fromisoformat(i["date"]) <= horizon], key=lambda x: x["date"])
    undated = [i for i in items if not i["date"]]
    return overdue, upcoming, undated, new_docs


def render(today, days, overdue, upcoming, undated, new_docs):
    L = [f"[KM 일정 브리핑] {today.isoformat()}({WEEK[today.weekday()]}) 05:00 기준", ""]
    L.append(f"■ 어제 이후 새로 만들어진 회의록 : {len(new_docs)}건")
    for n in new_docs or []:
        L.append(f"  - {n['site']} / {n['meeting']}  ({n['time']})")
    if not new_docs:
        L.append("  - 없음")
    L.append("")

    def block(title, lst, mark_all_important=False):
        L.append(f"■ {title}")
        if not lst:
            L.append("  - 없음"); L.append(""); return
        n = 0
        cur = None
        for it in lst:
            if it["date"] != cur:
                cur = it["date"]
                L.append("")
                L.append(f"● {k_date(dt.date.fromisoformat(cur))} 일정" if cur else "● 날짜 미정")
            n += 1
            flag = "★" if (it["important"] or mark_all_important) else ""
            L.append(f"{n}.")
            L.append(f"날짜 : {cur or '미정'}")
            L.append(f"현장명 : {it['site']}")
            L.append(f"일정 : {flag}{it['what']}" + (f" ({it['note']})" if it['note'] else ""))
            L.append(f"출처 : {it['meeting']}")
        L.append("")

    block("지난 일정인데 아직 남아 있는 것 (전부 빨강)", overdue, mark_all_important=True)
    block(f"오늘부터 {days}일 안 일정", upcoming)
    block("날짜 미정", undated)
    L.append("★ = 중요(빨강). 00_중요키워드.txt 의 낱말 기준. 빨강은 구글 캘린더에도 올라간다.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--today")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    out = a.out or os.path.join(a.root, "_보고")
    os.makedirs(out, exist_ok=True)
    kws = load_keywords(out)
    overdue, upcoming, undated, new_docs = collect(a.root, today, a.days, kws)
    text = render(today, a.days, overdue, upcoming, undated, new_docs)
    with open(os.path.join(out, "00_일정브리핑.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    payload = {"generated": dt.datetime.now().isoformat(timespec="minutes"), "today": today.isoformat(),
               "days": a.days, "mailto": "bsy@micronic.co.kr", "keywords": kws,
               "new_docs": new_docs, "overdue": overdue, "upcoming": upcoming, "undated": undated, "text": text}
    json.dump(payload, open(os.path.join(out, "00_일정브리핑.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"out": out, "new_docs": len(new_docs), "overdue": len(overdue), "upcoming": len(upcoming),
                      "undated": len(undated), "important": sum(i["important"] for i in overdue + upcoming + undated)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()

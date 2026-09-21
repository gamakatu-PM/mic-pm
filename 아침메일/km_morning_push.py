# -*- coding: utf-8 -*-
"""
KM 아침메일 밀어넣기  (v1, 2026-09-21)

무엇을 하나
  PC 안의 `_아침한장.md` (36번이 돌 때마다 갱신되는 정본)를 읽어
  아침 메일 3통(① 답해 주십시오 / ② 오늘 할 것 / ③ 어제 회의록)의 HTML을 만들고,
  구글 앱스 스크립트 웹앱으로 올려 둔다.

왜 이렇게 하나
  메일을 "보내는 것"은 구글이 한다. 그래야 PC가 꺼져 있어도 07:00에 메일이 간다.
  PC는 "자료를 올려 두는 것"까지만 한다.

무엇을 안 하나
  기존 KM 도구(t35 등)를 고치지 않는다. 이 파일은 옆에 얹는 것이다.
  금액·수량·기한을 채우지 않는다. md 에 있는 것만 옮긴다.

쓰는 법
  python km_morning_push.py                 설정.ini 읽어서 올린다
  python km_morning_push.py --dry           올리지 않고 미리보기 html 만 만든다
  python km_morning_push.py --md "경로"     md 위치를 직접 준다
  python km_morning_push.py --now           올리면서 "지금 ③번만 한 번 더" 를 같이 청한다

표준 라이브러리만 쓴다(설치할 것 없음).
"""

import argparse
import configparser
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime

여기 = os.path.dirname(os.path.abspath(__file__))
설정파일 = os.path.join(여기, "아침메일_설정.ini")

# md 의 절 이름 → 어느 편에 담는가
편성 = [
    {
        "key": "ask",
        "제목": "① 답해 주십시오",
        "절": ["제가 만들까요?", "답을 못 받아 진행하지 않은 것", "제가 못 알아들은 답", "묵은 제안"],
        "머리말": "이 메일에 그대로 회신해 주시면 반영됩니다. 줄 앞 번호만 맞으면 됩니다.",
    },
    {
        "key": "todo",
        "제목": "② 오늘 할 것",
        "절": ["앞으로 해야 될 것", "찾아갈 곳", "늦으면 안 되는 것", "오늘 할 것"],
        "머리말": "이미 정해진 것만 모았습니다. 답하지 않으셔도 됩니다.",
    },
    {
        "key": "meet",
        "제목": "③ 어제 회의록",
        "절": ["미확인 회의록", "회의록", "어제 회의"],
        "머리말": "아직 안 읽으신 회의입니다. 읽으셨으면 44번 또는 회신 `회의확인,<회의폴더>,확인`.",
    },
]

찾을곳 = [
    r"C:\Users\{user}\Desktop\!!클로드가 저장하는 폴더\KM_인수인계함\_아침한장.md",
    r"C:\Users\{user}\Desktop\KM_인수인계함\_아침한장.md",
    r"C:\Users\{user}\Documents\KM_인수인계함\_아침한장.md",
    r"D:\KM_인수인계함\_아침한장.md",
]


# ────────────────────────────────── md 읽기

def md_찾기(직접=None):
    """_아침한장.md 의 위치를 찾는다. 못 찾으면 None."""
    if 직접:
        return 직접 if os.path.exists(직접) else None

    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    후보 = [p.replace("{user}", user) for p in 찾을곳]

    # 이 파일 기준 위아래로도 훑는다 (도구 폴더 안에 같이 두셨을 때)
    뿌리 = 여기
    for _ in range(4):
        후보.append(os.path.join(뿌리, "KM_인수인계함", "_아침한장.md"))
        후보.append(os.path.join(뿌리, "_아침한장.md"))
        뿌리 = os.path.dirname(뿌리)

    for p in 후보:
        if p and os.path.exists(p):
            return p
    return None


def 절나누기(글):
    """`## 제목` 으로 갈라 {제목: 본문} 으로 돌려준다. 순서를 지킨다."""
    결과 = []
    이름, 담을것 = None, []
    for 줄 in 글.splitlines():
        m = re.match(r"^\s{0,3}##\s+(.*?)\s*$", 줄)
        if m:
            if 이름 is not None:
                결과.append((이름, "\n".join(담을것).strip()))
            이름, 담을것 = m.group(1).strip(), []
        else:
            if 이름 is None:
                continue  # 맨 앞 머리말은 버린다
            담을것.append(줄)
    if 이름 is not None:
        결과.append((이름, "\n".join(담을것).strip()))
    return 결과


def 절고르기(절들, 이름들):
    """이름이 비슷한 절을 순서대로 모은다(부분 일치)."""
    담긴것, 쓴것 = [], set()
    for 원하는 in 이름들:
        for i, (이름, 본문) in enumerate(절들):
            if i in 쓴것:
                continue
            납작 = 이름.replace(" ", "")
            if 원하는.replace(" ", "") in 납작:
                담긴것.append((이름, 본문))
                쓴것.add(i)
    return 담긴것


# ────────────────────────────────── md → html (표·목록·굵게만)

def 글자(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r'<code style="background:#f4f5f7;padding:1px 4px;border-radius:3px">\1</code>', s)
    return s


def 표인가(줄):
    return 줄.strip().startswith("|") and 줄.strip().endswith("|")


def 표칸(줄):
    return [c.strip() for c in 줄.strip().strip("|").split("|")]


def md_to_html(본문):
    밖 = []
    줄들 = 본문.splitlines()
    i = 0
    while i < len(줄들):
        줄 = 줄들[i]

        if 표인가(줄):
            표 = []
            while i < len(줄들) and 표인가(줄들[i]):
                표.append(표칸(줄들[i]))
                i += 1
            # 두 번째 줄이 --- 구분선이면 버린다
            if len(표) >= 2 and all(re.fullmatch(r":?-{2,}:?", c) for c in 표[1] if c):
                머리, 몸 = 표[0], 표[2:]
            else:
                머리, 몸 = None, 표
            밖.append('<table style="border-collapse:collapse;width:100%;font-size:13px;margin:6px 0">')
            if 머리:
                밖.append("<tr>" + "".join(
                    '<th style="text-align:left;border-bottom:1px solid #ddd;padding:5px 6px;color:#555;'
                    'font-weight:600">%s</th>' % 글자(c) for c in 머리) + "</tr>")
            for 행 in 몸:
                밖.append("<tr>" + "".join(
                    '<td style="border-bottom:1px solid #f0f1f3;padding:5px 6px;vertical-align:top">%s</td>'
                    % 글자(c) for c in 행) + "</tr>")
            밖.append("</table>")
            continue

        m = re.match(r"^\s*[-*]\s+(.*)$", 줄)
        if m:
            항목 = []
            while i < len(줄들):
                m2 = re.match(r"^\s*[-*]\s+(.*)$", 줄들[i])
                if not m2:
                    break
                항목.append(m2.group(1))
                i += 1
            밖.append('<ul style="margin:4px 0 8px;padding-left:18px">' +
                      "".join('<li style="margin:2px 0">%s</li>' % 글자(a) for a in 항목) + "</ul>")
            continue

        m = re.match(r"^\s{0,3}###\s+(.*)$", 줄)
        if m:
            밖.append('<div style="font-weight:700;margin:10px 0 4px;font-size:14px">%s</div>' % 글자(m.group(1)))
            i += 1
            continue

        if 줄.strip() == "":
            i += 1
            continue

        밖.append('<div style="margin:3px 0">%s</div>' % 글자(줄))
        i += 1

    return "\n".join(밖)


# ────────────────────────────────── 편 만들기

틀 = """<div style="font-family:'맑은 고딕',sans-serif;font-size:14px;line-height:1.6;color:#111;max-width:700px">
<div style="border:1px solid #e6e8eb;border-radius:8px;padding:9px 12px;margin:0 0 14px;font-size:12.5px;color:#444">
{머리말}</div>
<h2 style="margin:0 0 2px;font-size:18px">{제목}</h2>
<p style="margin:0 0 12px;color:#666;font-size:12px">{날짜}{덧}</p>
{몸}
<div style="border-top:1px solid #f0f1f3;margin-top:16px;padding-top:8px;color:#999;font-size:11.5px">
자료 기준 : {기준} (PC 마지막 갱신) · 보내는 것은 구글이 합니다(PC 꺼져 있어도 옵니다)</div>
</div>"""


def 편만들기(절들, 오늘, 기준):
    편들 = []
    for 틀정보 in 편성:
        고른것 = 절고르기(절들, 틀정보["절"])
        if not 고른것:
            continue
        몸 = []
        for 이름, 본문 in 고른것:
            if len(고른것) > 1:
                몸.append('<div style="font-weight:700;margin:12px 0 4px;color:#2a6099">%s</div>' % 글자(이름))
            몸.append(md_to_html(본문))
        줄수 = sum(len(b.splitlines()) for _, b in 고른것)
        편들.append({
            "key": 틀정보["key"],
            "subject": "[KM] %s %s" % (틀정보["제목"], 오늘),
            "html": 틀.format(머리말=글자(틀정보["머리말"]), 제목=글자(틀정보["제목"]),
                              날짜=오늘, 덧=" · %d줄" % 줄수 if 줄수 else "",
                              몸="\n".join(몸), 기준=기준),
        })
    return 편들


# ────────────────────────────────── 올리기

def 올리기(주소, 암호, 짐, 확인만=False):
    자료 = json.dumps(짐, ensure_ascii=False).encode("utf-8")
    청 = urllib.request.Request(주소, data=자료,
                                headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(청, timeout=60) as 답:
        return 답.read().decode("utf-8", "replace")


def 설정읽기():
    c = configparser.ConfigParser()
    if os.path.exists(설정파일):
        c.read(설정파일, encoding="utf-8")
    return c


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--md", default=None, help="_아침한장.md 경로")
    p.add_argument("--url", default=None, help="앱스 스크립트 웹앱 주소")
    p.add_argument("--secret", default=None, help="암호")
    p.add_argument("--dry", action="store_true", help="올리지 않고 미리보기 html 만 만든다")
    p.add_argument("--now", action="store_true", help="새 회의록이 있으니 지금 한 번 더 보내 달라고 청한다")
    p.add_argument("--out", default=None, help="미리보기를 둘 폴더")
    args = p.parse_args()

    설정 = 설정읽기()
    주소 = args.url or 설정.get("웹앱", "url", fallback="").strip()
    암호 = args.secret or 설정.get("웹앱", "secret", fallback="").strip()
    md길 = md_찾기(args.md or 설정.get("경로", "md", fallback="").strip() or None)

    if not md길:
        print("[멈춤] _아침한장.md 를 못 찾았습니다.")
        print("       36번(★KM_도면넣고_여기클릭)을 한 번 누르신 뒤 다시 실행하시거나,")
        print("       아침메일_설정.ini 의 [경로] md= 에 전체 경로를 적어 주십시오.")
        return 2

    글 = open(md길, encoding="utf-8", errors="replace").read()
    절들 = 절나누기(글)
    if not 절들:
        print("[멈춤] md 안에 `## 절` 이 하나도 없습니다 : %s" % md길)
        return 2

    바뀐때 = datetime.fromtimestamp(os.path.getmtime(md길))
    오늘 = datetime.now().strftime("%Y-%m-%d")
    기준 = 바뀐때.strftime("%Y-%m-%d %H:%M")
    편들 = 편만들기(절들, 오늘, 기준)

    if not 편들:
        print("[멈춤] 담을 절을 못 찾았습니다. md 의 절 이름 : %s" % ", ".join(n for n, _ in 절들))
        return 2

    print("md      : %s" % md길)
    print("자료기준: %s" % 기준)
    print("절      : %d개 / 편 : %s" % (len(절들), " ".join(e["key"] for e in 편들)))

    둘곳 = args.out or os.path.join(여기, "_미리보기")
    os.makedirs(둘곳, exist_ok=True)
    for e in 편들:
        길 = os.path.join(둘곳, "%s_%s.html" % (오늘, e["key"]))
        open(길, "w", encoding="utf-8").write(e["html"])
    print("미리보기: %s" % 둘곳)

    if args.dry:
        print("[--dry] 올리지 않았습니다.")
        return 0

    if not 주소 or not 암호:
        print("[멈춤] 아침메일_설정.ini 의 [웹앱] url / secret 이 비어 있습니다.")
        print("       설치하는법.md 3단계를 보십시오.")
        return 2

    짐 = {"secret": 암호, "builtAt": 바뀐때.strftime("%Y-%m-%d %H:%M:%S"),
          "pushedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "sendNow": bool(args.now), "parts": 편들}
    try:
        답 = 올리기(주소, 암호, 짐)
    except urllib.error.URLError as e:
        print("[멈춤] 올리다 막혔습니다 : %s" % e)
        return 3
    print("구글 답 : %s" % 답.strip()[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())

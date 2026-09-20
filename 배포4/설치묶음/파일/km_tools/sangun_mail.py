# -*- coding: utf-8 -*-
"""산군 메일 서식 v2 — 휴대폰에서 읽기 쉽게 (50번이 쓰는 부품). 토큰 0.

프로님 (2026-09-20) : "지금 만든 게 넘버 원이라고 하면 가독성을 높인 넘버 2를 만들어."

v1 과 무엇이 다른가
  · 글자를 키웠습니다 (본문 16px, 현장명 19px). 휴대폰에서 확대 안 하셔도 읽힙니다.
  · 맨 위에 **큰 숫자 타일** — 빨리 갈 곳 몇 곳인지 한눈에.
  · 카드 한 장에 한 가지씩 줄을 나눴습니다. 「위치 · 단계 · 연면적」 을 한 줄에 몰지 않습니다.
  · 역산을 표가 아니라 **세로 목록**으로 — 휴대폰에서 표는 깨집니다.
  · 전화 문안을 **큰 상자**에 따로 담았습니다. 길게 눌러 복사하시면 됩니다.
  · 기사 링크를 **버튼**으로 키웠습니다. 손가락으로 누르기 쉽게.
  · 등급마다 색 띠를 굵게 넣어 눈으로 먼저 갈라지게 했습니다.

v1 을 지우지 않았습니다. 설정.ini [산군메일] 서식 = v1 로 두시면 예전 서식이 갑니다.

────────────────────────────────────────────────────────────
v3 (2026-09-20) — 프로님 「스크롤이 길고 그런 거는 단점이 아니야. 장단점을 보고 개선해서 V3를 만들어」

v2 를 재 보니 진짜 단점이 셋이었습니다. 길이는 손대지 않고 그 셋만 고쳤습니다.

  ① PC 에서 화면을 안 썼다 — 폭이 680px 로 묶여 큰 화면이 놀았습니다(PC 스크롤이 v1 의 2.2배).
     → 폭을 **920px** 로 넓히고, 카드 속 「어디·규모·때·설계·시공」 을 **표 2열**로 놓았습니다.
        넓은 화면에서는 두 칸이 나란히, 좁은 화면에서는 저절로 아래로 떨어집니다.
  ② 메일이 잘릴 수 있었다 — 73KB. 지메일은 용량이 크면 「메시지 전체 보기」 로 접습니다.
     → 스타일을 <style> 한 곳에 모으고 반복을 지웠습니다. 같은 내용이 **절반 아래**로 줄었습니다.
  ③ 훑어보기가 느렸다 — v1 의 표는 한눈에 들어왔는데 v2 는 카드를 계속 내려야 했습니다.
     → 맨 위에 **한눈 목록**(번호·등급·현장명·가장 급한 것)을 넣고, 아래 카드에 **같은 번호**를 붙였습니다.
        목록에서 번호를 보고 그 번호 카드만 찾아보시면 됩니다.

설정.ini [산군메일] 서식 = v3(기본) / v2 / v1
"""

C = {
    '🔴': ('#C0392B', '#FDECEA'),
    '🟠': ('#C77B2B', '#FEF3E2'),
    '🟡': ('#8A6E00', '#FFF7DC'),   # 이모지가 노란데 파랑이라 어긋나 있었습니다 (v3에서 고침)
    '⚪': ('#8E99A4', '#F5F6F7'),
    '⚫': ('#6B4FA8', '#F1ECFA'),
    '⛔': ('#8E99A4', '#F5F6F7'),
}
BODY = 'font-family:-apple-system,"맑은 고딕",system-ui,sans-serif'


def esc(s):
    return (str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def color(grade):
    return C.get(str(grade)[:1], ('#555', '#F5F6F7'))


def tile(n, label, grade):
    fg, bg = color(grade)
    return ('<td width="25%%" align="center" style="padding:10px 4px;background:%s;'
            'border:1px solid %s;border-radius:10px">'
            '<div style="font-size:26px;font-weight:800;color:%s;line-height:1.1">%d</div>'
            '<div style="font-size:12px;color:#333;margin-top:3px">%s</div></td>'
            % (bg, fg, fg, n, esc(label)))


def row(label, value, big=False):
    if not value:
        return ''
    return ('<div style="margin:5px 0;font-size:%dpx;line-height:1.5">'
            '<span style="color:#8a8a8a">%s</span> <b>%s</b></div>'
            % (17 if big else 16, esc(label), esc(value)))


def button(url, text, fg='#2A6099'):
    return ('<a href="%s" style="display:inline-block;margin:4px 6px 4px 0;padding:10px 16px;'
            'background:#fff;border:2px solid %s;border-radius:8px;color:%s;'
            'font-size:15px;font-weight:700;text-decoration:none">%s</a>'
            % (esc(url), fg, fg, esc(text)))


def card(rec, res):
    g = str(res.get('등급', ''))
    cd = res.get('카드') or {}
    fg, bg = color(g)
    h = []
    h.append('<div style="border:2px solid %s;border-radius:12px;margin:14px 0;overflow:hidden">' % fg)
    h.append('<div style="background:%s;padding:10px 14px">'
             '<div style="font-size:14px;font-weight:800;color:%s">%s</div>'
             '<div style="font-size:19px;font-weight:800;color:#111;margin-top:3px;line-height:1.35">%s</div>'
             '</div>' % (bg, fg, esc(g), esc(rec.get('현장명'))))
    h.append('<div style="padding:12px 14px">')

    h.append(row('어디', rec.get('소재지'), big=True))
    size = []
    if rec.get('연면적'):
        size.append(rec['연면적'] + '㎡')
    if cd.get('객실') or rec.get('객실추정'):
        size.append(cd.get('객실') or rec.get('객실추정'))
    h.append(row('규모', ' · '.join(size)))
    if cd.get('규모금액'):
        h.append('<div style="margin:5px 0;font-size:16px;color:#1a7a4c;font-weight:700">%s</div>'
                 % esc(cd['규모금액']))
    when = []
    if rec.get('허가일'):
        when.append('허가 ' + rec['허가일'])
    if rec.get('착공일'):
        when.append('착공 ' + rec['착공일'])
    if cd.get('준공예정'):
        when.append('준공 예정 ' + cd['준공예정'])
    h.append(row('때', ' / '.join(when)))
    h.append(row('설계', rec.get('건축설계') or '안 나옴'))
    h.append(row('시공', rec.get('시공사') or '안 나옴'))
    h.append(row('건축주', rec.get('건축주')))

    h.append('<div style="margin:10px 0 0;padding:10px 12px;background:#FAFAFA;border-radius:8px;'
             'font-size:15px;line-height:1.6;color:#333">%s</div>' % esc(res.get('한줄')))

    if cd.get('급한것'):
        h.append('<div style="margin:10px 0 0;padding:11px 13px;background:#FFF4F2;'
                 'border-left:5px solid #C0392B;border-radius:6px">'
                 '<div style="font-size:13px;color:#C0392B;font-weight:800">가장 급한 것</div>'
                 '<div style="font-size:16px;margin-top:4px;line-height:1.5">%s</div></div>'
                 % esc(cd['급한것']))

    if cd.get('역산'):
        h.append('<div style="margin:12px 0 0">'
                 '<div style="font-size:13px;color:#8a8a8a;font-weight:700">언제까지 무엇을 '
                 '<span style="font-weight:400">(준공 %s 에서 거꾸로 · 추정)</span></div>'
                 % esc(cd.get('준공예정')))
        for x in cd['역산']:
            late = x['D'] < 0
            h.append('<div style="margin:6px 0;padding:8px 10px;background:%s;border-radius:6px;font-size:15px">'
                     '<div style="line-height:1.45">%s</div>'
                     '<div style="margin-top:2px;font-weight:800;color:%s">%s <span style="font-weight:400;color:#777">%s</span></div>'
                     '</div>'
                     % ('#FFF4F2' if late else '#F7F9FC', esc(x['무엇']),
                        '#C0392B' if late else '#111', esc(x['언제까지']),
                        esc(('이미 %d일 지남' % -x['D']) if late else ('D-%d' % x['D']))))
        if cd.get('외함의뢰'):
            h.append('<div style="margin:6px 0;padding:8px 10px;background:#F7F9FC;border-radius:6px;font-size:15px">'
                     '<div>CB외함 작업의뢰서</div>'
                     '<div style="margin-top:2px;font-weight:800">%s <span style="font-weight:400;color:#777">착공 기준 어림</span></div>'
                     '</div>' % esc(cd['외함의뢰']))
        h.append('</div>')
    elif cd.get('외함의뢰'):
        h.append('<div style="margin:12px 0 0;padding:8px 10px;background:#F7F9FC;border-radius:6px;font-size:15px">'
                 '<div style="color:#8a8a8a;font-size:13px">CB외함 작업의뢰서 (착공 기준 어림)</div>'
                 '<div style="font-weight:800;margin-top:2px">%s</div></div>' % esc(cd['외함의뢰']))

    arts = res.get('기사') or []
    if arts:
        h.append('<div style="margin:12px 0 0"><div style="font-size:13px;color:#8a8a8a;font-weight:700">'
                 '기사 %d건</div>' % len(arts))
        for a in arts[:4]:
            h.append('<div style="margin:7px 0;font-size:15px;line-height:1.5">%s'
                     '<div style="color:#8a8a8a;font-size:13px;margin-top:2px">%s %s</div>%s</div>'
                     % (esc(a.get('제목')), esc(a.get('날짜')), esc(a.get('언론사')),
                        button(a['링크'], '기사 보기') if a.get('링크') else ''))
        h.append('</div>')

    if res.get('지도'):
        h.append('<div style="margin:12px 0 0">')
        if res.get('소요'):
            h.append('<div style="font-size:15px;margin-bottom:4px">가는 길 : <b>%s</b></div>' % esc(res['소요']))
        for k, u in res['지도'].items():
            h.append(button(u, k, '#1a7a4c'))
        h.append('</div>')

    if res.get('행동'):
        h.append('<div style="margin:14px 0 0;padding:12px 13px;background:#FFFDF2;'
                 'border:2px dashed #D9C77E;border-radius:8px">'
                 '<div style="font-size:13px;color:#8a6d00;font-weight:800">이렇게 말씀하시면 됩니다 '
                 '<span style="font-weight:400">(길게 눌러 복사)</span></div>'
                 '<div style="font-size:16px;line-height:1.65;margin-top:6px;color:#222">%s</div></div>'
                 % esc(res['행동']))

    h.append('</div></div>')
    return ''.join(h)


def build_v2(groups, cards, src, err_n, jsonname, today_s, wide=25, top3=None, routes=None,
             basename=lambda p: p):
    """v2 본문(보존). groups={등급:[(rec,res)]}, cards=영업카드 목록"""
    n = {k: len(v) for k, v in groups.items()}
    G = ['🔴 지금 가십시오', '🟠 상황을 물어보십시오', '🟡 아직 이릅니다',
         '⚪ 흔적 없음', '⚫ 이미 끝남', '⛔ 검색 못 함']

    h = ['<div style="%s;background:#fff;color:#111;max-width:680px;margin:0 auto;padding:16px">' % BODY]
    h.append('<div style="font-size:13px;color:#8a8a8a">%s · 산군 + 뉴스</div>' % esc(today_s))
    h.append('<div style="font-size:23px;font-weight:800;margin:2px 0 14px">오늘의 현장</div>')

    # ── 큰 숫자 타일 ──
    h.append('<table width="100%" cellpadding="0" cellspacing="6" style="border-collapse:separate"><tr>')
    h.append(tile(n.get(G[0], 0), '빨리 갈 곳', '🔴'))
    h.append(tile(n.get(G[1], 0), '물어볼 곳', '🟠'))
    h.append(tile(n.get(G[2], 0), '아직 이른 곳', '🟡'))
    h.append(tile(n.get(G[3], 0) + n.get(G[4], 0) + n.get(G[5], 0), '그 밖', '⚪'))
    h.append('</tr></table>')

    # ── 오늘 이것만 ──
    if top3:
        h.append('<div style="margin:16px 0;border:3px solid #E8B93B;border-radius:12px;overflow:hidden">')
        h.append('<div style="background:#FFF7DF;padding:11px 14px;font-size:18px;font-weight:800">'
                 '오늘 이것만 하십시오</div><div style="padding:6px 14px 12px">')
        for t in top3:
            h.append('<div style="margin:9px 0;font-size:16px;line-height:1.6">%s</div>' % esc(t))
        h.append('</div></div>')

    # ── 하루 동선 ──
    if routes:
        h.append('<div style="margin:16px 0;padding:12px 14px;background:#F2F7FF;'
                 'border:1px solid #C6D8FF;border-radius:10px">')
        h.append('<div style="font-size:16px;font-weight:800;margin-bottom:6px">한 번 나가실 때 같이 보실 곳</div>')
        for sido, xs in routes:
            names = '  /  '.join('%s %s' % (str(c['등급'])[:1], c['현장명']) for c in xs)
            h.append('<div style="margin:6px 0;font-size:15px;line-height:1.55">'
                     '<b>%s</b> %d곳<br><span style="color:#444">%s</span></div>'
                     % (esc(sido), len(xs), esc(names)))
        h.append('</div>')

    # ── 납기 급한 순서 ──
    due = [c for c in (cards or []) if c.get('급한것')]
    due.sort(key=lambda c: c.get('급한D', 9999))
    if due:
        h.append('<div style="margin:16px 0"><div style="font-size:16px;font-weight:800;margin-bottom:6px">'
                 '작업의뢰서 — 급한 순서</div>')
        for c in due[:8]:
            late = c.get('급한D', 9999) < 0
            h.append('<div style="margin:7px 0;padding:10px 12px;border-left:5px solid %s;'
                     'background:%s;border-radius:6px;font-size:15px;line-height:1.5">'
                     '<b>%s</b><br><span style="color:#444">%s</span></div>'
                     % ('#C0392B' if late else '#8E99A4', '#FFF4F2' if late else '#F7F8FA',
                        esc(c['현장명']), esc(c['급한것'])))
        h.append('<div style="font-size:13px;color:#8a8a8a;margin-top:4px">'
                 '기사에 적힌 준공 예정에서 거꾸로 계산한 추정입니다. 현장에 확인하시고 쓰십시오.</div></div>')

    # ── 현장 카드 (🔴🟠🟡 만 펼침) ──
    left = wide
    for g in G[:3]:
        xs = groups.get(g) or []
        if not xs:
            continue
        fg, _ = color(g)
        h.append('<div style="margin:22px 0 8px;font-size:18px;font-weight:800;color:%s;'
                 'border-bottom:3px solid %s;padding-bottom:5px">%s <span style="color:#8a8a8a">%d곳</span></div>'
                 % (fg, fg, esc(g), len(xs)))
        for rec, res in xs[:max(left, 0)]:
            h.append(card(rec, res))
        if len(xs) > max(left, 0):
            h.append('<div style="font-size:14px;color:#8a8a8a">이 등급의 나머지 %d곳은 붙임 파일에 있습니다.</div>'
                     % (len(xs) - max(left, 0)))
        left -= len(xs)

    # ── 나머지는 접어서 ──
    for g in G[3:]:
        xs = groups.get(g) or []
        if not xs:
            continue
        h.append('<div style="margin:22px 0 6px;font-size:16px;font-weight:800;color:#8a8a8a">'
                 '%s <span style="font-weight:400">%d곳</span></div>' % (esc(g), len(xs)))
        for rec, res in xs[:40]:
            cd = res.get('카드') or {}
            tail = cd.get('급한것') or (res.get('한줄') or '')[:38]
            h.append('<div style="margin:5px 0;padding:9px 11px;background:#F7F8FA;border-radius:6px;'
                     'font-size:15px;line-height:1.5"><b>%s</b>'
                     '<div style="color:#666;font-size:13px;margin-top:2px">%s%s</div></div>'
                     % (esc(rec.get('현장명')), esc(rec.get('소재지')),
                        (' · ' + esc(tail)) if tail else ''))
        if len(xs) > 40:
            h.append('<div style="font-size:13px;color:#8a8a8a">그 밖 %d곳은 붙임 파일에</div>' % (len(xs) - 40))

    # ── 앱에 넣기 ──
    if jsonname:
        h.append('<div style="margin:22px 0;padding:14px;background:#F1FBF5;border:2px solid #A8DCC0;'
                 'border-radius:12px">'
                 '<div style="font-size:17px;font-weight:800;margin-bottom:5px">앱에 넣으시려면</div>'
                 '<div style="font-size:15px;line-height:1.65">이 메일에 붙은 <b>%s</b> 를 저장하시고,<br>'
                 '앱 &gt; <b>영업 파이프라인</b> &gt; <b>📡 산군 불러오기</b> 에서 고르십시오.<br>'
                 '<span style="color:#555">이미 있는 현장은 건너뜁니다. 금액·단계는 직접 정하십시오.</span></div></div>'
                 % esc(jsonname))

    h.append('<div style="margin-top:20px;padding-top:12px;border-top:1px solid #E5E7EB;'
             'font-size:13px;color:#9aa0a6;line-height:1.7">'
             '산군 파일 : %s<br>'
             'PC 도구 50번이 산군 자료와 구글 뉴스를 합쳐 만들었습니다 (클로드·Gemini 안 씀, 0원).%s<br>'
             '알리미 메일·구글AI 레이더 메일은 따로 옵니다.<br>'
             '예상 금액·소요 시간이 비어 있으면 설정.ini 의 [역산] 실당단가 · [소요시간] 을 채워 주십시오.<br>'
             '예전 서식으로 받으시려면 설정.ini [산군메일] 서식 = v1</div></div>'
             % (esc(basename(src)),
                (' 검색이 막힌 곳 %d곳은 따로 모았습니다.' % err_n) if err_n else ''))
    return ''.join(h)


# ====================== v3 ======================

CSS = """<style>
.km{font-family:-apple-system,"맑은 고딕",system-ui,sans-serif;background:#fff;color:#111;
max-width:920px;margin:0 auto;padding:16px}
.km .h1{font-size:23px;font-weight:800;margin:2px 0 14px}
.km .dim{color:#8a8a8a}
.km .sm{font-size:13px}
.km .tile{padding:10px 4px;border-radius:10px;text-align:center}
.km .tile b{display:block;font-size:26px;line-height:1.1}
.km .box{border-radius:12px;margin:13px 0;overflow:hidden}
.km .hd{padding:11px 14px;font-size:18px;font-weight:800}
.km .pad{padding:9px 13px}
.km .line{margin:9px 0;font-size:16px;line-height:1.6}
.km .idx{display:inline-block;min-width:26px;height:26px;line-height:26px;text-align:center;
border-radius:13px;background:#111;color:#fff;font-size:14px;font-weight:800;margin-right:7px}
.km .card{border:2px solid #ddd;border-radius:12px;margin:11px 0;overflow:hidden}
.km .ct{padding:9px 13px}
.km .cn{font-size:19px;font-weight:800;color:#111;margin-top:3px;line-height:1.35}
.km .cg{font-size:14px;font-weight:800}
.km td.k{color:#8a8a8a;font-size:15px;padding:2px 10px 2px 0;white-space:nowrap;vertical-align:top}
.km td.v{font-size:16px;font-weight:700;padding:2px 0;line-height:1.45}
.km .note{margin:8px 0 0;padding:8px 11px;background:#FAFAFA;border-radius:8px;
font-size:15px;line-height:1.55;color:#333}
.km .urg{margin:8px 0 0;padding:9px 12px;background:#FFF4F2;border-left:5px solid #C0392B;border-radius:6px}
.km .due{margin:5px 0;padding:6px 10px;background:#F7F9FC;border-radius:6px;font-size:15px}
.km .due.late{background:#FFF4F2}
.km .say{margin:10px 0 0;padding:10px 12px;background:#FFFDF2;border:2px dashed #D9C77E;border-radius:8px}
.km .btn{display:inline-block;margin:4px 6px 4px 0;padding:8px 14px;background:#fff;
border:2px solid #2A6099;border-radius:8px;color:#2A6099;font-size:15px;font-weight:700;text-decoration:none}
.km .btn.g{border-color:#1a7a4c;color:#1a7a4c}
.km .row{margin:5px 0;padding:9px 11px;background:#F7F8FA;border-radius:6px;font-size:15px;line-height:1.5}
.km .chip{display:inline-block;padding:3px 9px;border-radius:12px;font-size:14px;font-weight:800;white-space:nowrap}
.km .none{color:#9aa0a6;font-weight:400}
.km td.d{text-align:right;vertical-align:top;padding:6px 0 6px 8px;white-space:nowrap}
.km .foot{margin-top:20px;padding-top:12px;border-top:1px solid #E5E7EB;font-size:13px;color:#9aa0a6;line-height:1.7}
</style>"""


def kv(label, value, none=''):
    """값이 없으면 회색 보통 글씨로 「확인 필요」 라고 적는다 (규칙 12.3 : 빈 항목도 이름을 불러 준다)"""
    if not value:
        if not none:
            return ''
        return '<tr><td class="k">%s</td><td class="v none">%s</td></tr>' % (esc(label), esc(none))
    return '<tr><td class="k">%s</td><td class="v">%s</td></tr>' % (esc(label), esc(value))


def chip(D):
    """납기까지 남은 날을 색 칩 하나로. 지난 것은 빨강, 석 달 안은 주황, 그 밖은 회색"""
    if D is None or D >= 9999:
        return ''
    if D < 0:
        return '<span class="chip" style="background:#FDECEA;color:#C0392B">%d일 지남</span>' % -D
    if D <= 30:
        return '<span class="chip" style="background:#FDECEA;color:#C0392B">D-%d</span>' % D
    if D <= 90:
        return '<span class="chip" style="background:#FEF3E2;color:#C77B2B">D-%d</span>' % D
    return '<span class="chip" style="background:#F1F3F5;color:#5F6B76">D-%d</span>' % D


def card3(i, rec, res):
    g = str(res.get('등급', ''))
    cd = res.get('카드') or {}
    fg, bg = color(g)
    h = ['<div class="card" style="border-color:%s">' % fg]
    h.append('<div class="ct" style="background:%s"><div class="cg" style="color:%s">%s</div>'
             '<div class="cn"><span class="idx" style="background:%s">%d</span>%s</div></div>'
             % (bg, fg, esc(g), fg, i, esc(rec.get('현장명'))))
    h.append('<div class="pad"><table cellpadding="0" cellspacing="0" style="width:100%">')
    size = []
    if rec.get('연면적'):
        size.append(rec['연면적'] + '㎡')
    if cd.get('객실') or rec.get('객실추정'):
        size.append(cd.get('객실') or rec.get('객실추정'))
    when = []
    if rec.get('허가일'):
        when.append('허가 ' + rec['허가일'])
    if rec.get('착공일'):
        when.append('착공 ' + rec['착공일'])
    if cd.get('준공예정'):
        when.append('준공 예정 ' + cd['준공예정'])
    h.append(kv('어디', rec.get('소재지')))
    h.append(kv('규모', ' · '.join(size)))
    h.append(kv('예상', cd.get('규모금액')))
    h.append(kv('때', ' / '.join(when)))
    h.append(kv('설계', rec.get('건축설계'), '확인 필요 — 산군에 설계사가 안 나옵니다'))
    h.append(kv('시공', rec.get('시공사'), '확인 필요 — 아직 시공사가 안 정해졌을 수 있습니다'))
    h.append(kv('건축주', rec.get('건축주')))
    h.append('</table>')

    h.append('<div class="note">%s</div>' % esc(res.get('한줄')))
    if cd.get('급한것'):
        h.append('<div class="urg"><div class="sm" style="color:#C0392B;font-weight:800">가장 급한 것</div>'
                 '<div style="font-size:16px;margin-top:4px;line-height:1.5">%s %s <b>%s</b></div></div>'
                 % (chip(cd.get('급한D')), esc(cd.get('급한무엇') or cd['급한것']),
                    esc(cd.get('급한날') or '')))
    if cd.get('역산'):
        h.append('<div style="margin:12px 0 0"><div class="sm dim" style="font-weight:700">'
                 '언제까지 무엇을 <span style="font-weight:400">(준공 %s 에서 거꾸로 · 추정)</span></div>'
                 % esc(cd.get('준공예정')))
        for x in sorted(cd['역산'], key=lambda x: x['D']):   # 날짜 빠른 것부터 (v3)
            h.append('<div class="due%s">%s<div style="margin-top:2px"><b>%s</b> %s</div></div>'
                     % (' late' if x['D'] < 0 else '', esc(x['무엇']), esc(x['언제까지']), chip(x['D'])))
        if cd.get('외함의뢰'):
            h.append('<div class="due">CB외함 작업의뢰서<div style="margin-top:2px"><b>%s</b> %s '
                     '<span class="sm dim">착공 기준 어림</span></div></div>'
                     % (esc(cd['외함의뢰']), chip(cd.get('급한D') if cd.get('급한무엇', '').startswith('CB외함') else None)))
        h.append('</div>')
    elif cd.get('외함의뢰'):
        h.append('<div class="due"><span class="dim sm">CB외함 작업의뢰서 (착공 기준 어림)</span>'
                 '<div style="font-weight:800;margin-top:2px">%s</div></div>' % esc(cd['외함의뢰']))

    arts = res.get('기사') or []
    if arts:
        h.append('<div style="margin:12px 0 0"><div class="sm dim" style="font-weight:700">기사 %d건</div>' % len(arts))
        for a in arts[:3]:
            h.append('<div style="margin:7px 0;font-size:15px;line-height:1.5">%s<div class="sm dim" '
                     'style="margin-top:2px">%s %s</div>%s</div>'
                     % (esc(a.get('제목')), esc(a.get('날짜')), esc(a.get('언론사')),
                        ('<a class="btn" href="%s">기사 보기</a>' % esc(a['링크'])) if a.get('링크') else ''))
        h.append('</div>')
    if res.get('지도'):
        h.append('<div style="margin:12px 0 0">')
        if res.get('소요'):
            h.append('<div style="font-size:15px;margin-bottom:4px">가는 길 : <b>%s</b></div>' % esc(res['소요']))
        for k, u in res['지도'].items():
            h.append('<a class="btn g" href="%s">%s</a>' % (esc(u), esc(k)))
        h.append('</div>')
    if res.get('행동'):
        h.append('<div class="say"><div class="sm" style="color:#8a6d00;font-weight:800">이렇게 말씀하시면 됩니다 '
                 '<span style="font-weight:400">(길게 눌러 복사)</span></div>'
                 '<div style="font-size:16px;line-height:1.65;margin-top:6px;color:#222">%s</div></div>' % esc(res['행동']))
    h.append('</div></div>')
    return ''.join(h)


def build(groups, cards, src, err_n, jsonname, today_s, wide=25, top3=None, routes=None,
          basename=lambda p: p):
    """v3 본문 — 한눈 목록 + 넓은 화면 활용 + 용량 다이어트"""
    n = {k: len(v) for k, v in groups.items()}
    G = ['🔴 지금 가십시오', '🟠 상황을 물어보십시오', '🟡 아직 이릅니다',
         '⚪ 흔적 없음', '⚫ 이미 끝남', '⛔ 검색 못 함']
    h = [CSS, '<div class="km">']
    h.append('<div class="sm dim">%s · 산군 + 뉴스</div><div class="h1">오늘의 현장</div>' % esc(today_s))

    h.append('<table width="100%" cellpadding="0" cellspacing="6" style="border-collapse:separate"><tr>')
    for cnt, lab, gg in ((n.get(G[0], 0), '빨리 갈 곳', '🔴'), (n.get(G[1], 0), '물어볼 곳', '🟠'),
                         (n.get(G[2], 0), '아직 이른 곳', '🟡'),
                         (n.get(G[3], 0) + n.get(G[4], 0) + n.get(G[5], 0), '흔적 없음·끝남', '⚪')):
        fg, bg = color(gg)
        h.append('<td width="25%%" class="tile" style="background:%s;border:1px solid %s">'
                 '<b style="color:%s">%d</b><span class="sm">%s</span></td>' % (bg, fg, fg, cnt, esc(lab)))
    h.append('</tr></table>')

    # ── 한눈 목록을 먼저 만듭니다. 「오늘 이것만」 에 카드 번호를 붙여야 해서입니다 ──
    wide_list = []
    for g in G[:3]:
        wide_list += [(g, rec, res) for rec, res in (groups.get(g) or [])]
    shown = wide_list[:wide]
    no = {}
    for i, (g, rec, res) in enumerate(shown, 1):
        no.setdefault(rec.get('현장명'), (i, color(g)[0]))

    if top3:
        h.append('<div class="box" style="border:3px solid #E8B93B">'
                 '<div class="hd" style="background:#FFF7DF">오늘 이것만 하십시오</div><div class="pad">')
        for t in top3:
            name, text = t if isinstance(t, (tuple, list)) else ('', t)
            mark = ''
            if name:
                if name in no:
                    i, fg = no[name]
                    mark = ('<span class="idx" style="background:%s;margin-left:6px">%d</span>'
                            '<span class="sm dim">번 카드</span>' % (fg, i))
                else:
                    # 카드가 없는 현장을 「오늘 이것만」 에 적으면 프로님이 아래에서 못 찾습니다
                    mark = '<span class="sm dim" style="margin-left:6px">(아래 카드에 없습니다 — 붙임 파일)</span>'
            h.append('<div class="line">%s%s</div>' % (esc(text), mark))
        h.append('</div></div>')

    if shown:
        h.append('<div class="box" style="border:2px solid #DDD"><div class="hd" style="background:#F4F6F8">'
                 '한눈에 보기 <span class="sm dim" style="font-weight:400">아래 카드와 번호가 같습니다</span></div>'
                 '<div class="pad"><table cellpadding="0" cellspacing="0" style="width:100%">')
        for i, (g, rec, res) in enumerate(shown, 1):
            cd = res.get('카드') or {}
            fg, _ = color(g)
            what = (cd.get('급한무엇') or '').replace('(착공 기준 어림)', '')
            day = cd.get('급한날') or ''
            D = cd.get('급한D', 9999)
            h.append('<tr><td class="k" style="padding:6px 8px 6px 0"><span class="idx" style="background:%s">%d</span></td>'
                     '<td class="v" style="padding:6px 0">%s'
                     '<div class="sm dim" style="font-weight:400;margin-top:2px">%s%s</div></td>'
                     '<td class="d">%s%s</td></tr>'
                     % (fg, i, esc(rec.get('현장명')), esc(rec.get('소재지')),
                        (' · ' + esc(what)) if what else ' · 착공일이 없어 납기를 못 셌습니다', chip(D),
                        ('<div class="sm dim" style="margin-top:2px">%s</div>' % esc(day)) if day else ''))
        h.append('</table></div></div>')

    if routes:
        h.append('<div class="box" style="border:1px solid #C6D8FF"><div class="hd" style="background:#F2F7FF">'
                 '한 번 나가실 때 같이 보실 곳</div><div class="pad">')
        for sido, xs in routes:
            names = '  /  '.join('%s %s' % (str(c['등급'])[:1], c['현장명']) for c in xs)
            h.append('<div style="margin:6px 0;font-size:15px;line-height:1.55"><b>%s</b> %d곳<br>'
                     '<span style="color:#444">%s</span></div>' % (esc(sido), len(xs), esc(names)))
        h.append('</div></div>')

    due = [c for c in (cards or []) if c.get('급한것')]
    due.sort(key=lambda c: c.get('급한D', 9999))
    if due:
        h.append('<div style="margin:16px 0"><div style="font-size:16px;font-weight:800;margin-bottom:6px">'
                 '작업의뢰서 — 급한 순서</div>')
        h.append('<table cellpadding="0" cellspacing="0" style="width:100%">')
        for c in due[:8]:
            D = c.get('급한D', 9999)
            late = D < 0
            h.append('<tr><td class="v" style="padding:6px 0;border-left:5px solid %s;'
                     'background:%s;padding-left:9px">%s'
                     '<div class="sm dim" style="font-weight:400;margin-top:2px">%s%s</div></td>'
                     '<td class="d" style="background:%s">%s</td></tr>'
                     % ('#C0392B' if late else '#8E99A4', '#FFF4F2' if late else '#F7F8FA',
                        esc(c['현장명']),
                        esc(c.get('급한무엇') or c.get('급한것')),
                        (' · ' + esc(c.get('급한날'))) if c.get('급한날') else '',
                        '#FFF4F2' if late else '#F7F8FA', chip(D)))
        h.append('</table>')
        h.append('<div class="sm dim" style="margin-top:4px">기사에 적힌 준공 예정에서 거꾸로 계산한 추정입니다. '
                 '현장에 확인하시고 쓰십시오.</div></div>')

    i = 0
    for g in G[:3]:
        xs = groups.get(g) or []
        if not xs:
            continue
        fg, _ = color(g)
        h.append('<div style="margin:22px 0 8px;font-size:18px;font-weight:800;color:%s;'
                 'border-bottom:3px solid %s;padding-bottom:5px">%s <span class="dim">%d곳</span></div>'
                 % (fg, fg, esc(g), len(xs)))
        for j, (rec, res) in enumerate(xs):
            if i >= wide:
                h.append('<div class="sm dim">이 등급의 나머지 %d곳은 붙임 파일에 있습니다.</div>'
                         % (len(xs) - j))
                break
            i += 1
            h.append(card3(i, rec, res))

    for g in G[3:]:
        xs = groups.get(g) or []
        if not xs:
            continue
        h.append('<div style="margin:22px 0 6px;font-size:16px;font-weight:800;color:#8a8a8a">'
                 '%s <span style="font-weight:400">%d곳</span></div>' % (esc(g), len(xs)))
        for rec, res in xs[:25]:
            cd = res.get('카드') or {}
            tail = cd.get('급한것') or (res.get('한줄') or '')[:36]
            h.append('<div class="row"><b>%s</b><div class="sm" style="color:#666;margin-top:2px">%s%s</div></div>'
                     % (esc(rec.get('현장명')), esc(rec.get('소재지')), (' · ' + esc(tail)) if tail else ''))
        if len(xs) > 25:
            h.append('<div class="sm dim">그 밖 %d곳은 붙임 파일에</div>' % (len(xs) - 25))

    if jsonname:
        h.append('<div class="box" style="border:2px solid #A8DCC0"><div class="hd" style="background:#F1FBF5">'
                 '앱에 넣으시려면</div><div class="pad" style="font-size:15px;line-height:1.65">'
                 '이 메일에 붙은 <b>%s</b> 를 저장하시고,<br>앱 &gt; <b>영업 파이프라인</b> &gt; '
                 '<b>📡 산군 불러오기</b> 에서 고르십시오.<br>'
                 '<span style="color:#555">이미 있는 현장은 건너뜁니다. 금액·단계는 직접 정하십시오.</span>'
                 '</div></div>' % esc(jsonname))

    h.append('<div class="foot">산군 파일 : %s<br>'
             'PC 도구 50번이 산군 자료와 구글 뉴스를 합쳐 만들었습니다 (클로드·Gemini 안 씀, 0원).%s<br>'
             '알리미 메일·구글AI 레이더 메일은 따로 옵니다.<br>'
             '예상 금액·소요 시간이 비어 있으면 설정.ini 의 [역산] 실당단가 · [소요시간] 을 채워 주십시오.<br>'
             '서식을 바꾸시려면 설정.ini [산군메일] 서식 = v3 / v2 / v1</div></div>'
             % (esc(basename(src)), (' 검색이 막힌 곳 %d곳은 따로 모았습니다.' % err_n) if err_n else ''))
    return ''.join(h)

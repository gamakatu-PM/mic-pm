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
"""

C = {
    '🔴': ('#C0392B', '#FDECEA'),
    '🟠': ('#C77B2B', '#FEF3E2'),
    '🟡': ('#2A6099', '#EAF1FB'),
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


def build(groups, cards, src, err_n, jsonname, today_s, wide=25, top3=None, routes=None,
          basename=lambda p: p):
    """v2 본문. groups={등급:[(rec,res)]}, cards=영업카드 목록"""
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

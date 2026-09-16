# -*- coding: utf-8 -*-
"""1. 제안서 후보 + 초안 - 회의록에서 '자료를 달라'는 말이 나온 건만 뽑아 제안서 초안을 만든다.
하루 한 장을 억지로 채우지 않는다. 요구가 나온 날만, 대신 그날은 반드시."""
import os, re, io, datetime
from common import *

WANT = ('제안서', '검토서', '설명 자료', '설명자료', '자료 요청', '자료요청', '자료 주', '자료 좀',
        '비교표', '구성도', '계통도', '운영 시나리오', '공사한계', '스코프', '질의', '회신')
TYPE = [('설명자료', ('설명', '모르', '이해', '교육')), ('비교검토서', ('비교', '검토', '타사', '경쟁')),
        ('공사한계/스코프', ('한계', '스코프', '범위', '구분')), ('질의답변', ('질의', '회신', '답변')),
        ('운영시나리오', ('운영', '시나리오', 'PMS', '연동')), ('제안서', ('제안',))]

def kind_of(line):
    for k, keys in TYPE:
        if any(x in line for x in keys):
            return k
    return '제안서'

def scan(days=3):
    root = sites_root()
    cut = datetime.datetime.now().timestamp() - days * 86400
    out = []
    for p in walk_files(root, {'.txt', '.md'}):
        if os.path.getmtime(p) < cut:
            continue
        rel = os.path.relpath(p, root); site = rel.split(os.sep)[0]
        for ln in read_text(p).splitlines():
            s = ln.strip(' -*.\t')
            if len(s) >= 8 and any(w in s for w in WANT):
                out.append([site, kind_of(s), s[:160], p])
    return out

def draft(site, kind, lines):
    od = outdir('제안서초안')
    body = ['%s  %s 초안' % (site, kind),
            '작성일 : %s   작성 : 한국마이크로닉(주) 배성윤' % today().isoformat(), '',
            '1. 배경 (회의록에서 그대로 옮김)']
    body += ['   - %s' % l for l in lines]
    body += ['', '2. 우리가 제공하는 범위',
             '   - 객실관리 시스템(RCU/BSP/CB 제어분전함) 공급 및 약전 결선, 시운전',
             '   - CB 외함 선납품 후 전기/통신 공사에서 설치, 그 안에 제어분전함 설치',
             '', '3. 상대 공종이 해야 하는 것',
             '   - 강전 결선(전기), 외함 취부, 벽지/페인트 완료 후 기구물 설치 여건 제공',
             '', '4. 일정', '   - 납기 역산표(도구 5번) 결과를 붙이십시오.',
             '', '5. 확인이 필요한 것', '   - (프로님이 채우실 칸)', '',
             '※ 이 초안은 회의록 문장을 옮겨 만든 것입니다. 대외 제출 전 반드시 손보십시오.',
             '※ 장수를 맞춘 pptx 가 필요하면 원틀을 _원틀 폴더에 넣어주십시오.']
    f = os.path.join(od, '%s_%s_초안_%s.txt' % (safe_name(site), safe_name(kind), ymd6()))
    io.open(f, 'w', encoding='utf-8').write('\n'.join(body))
    tpl = find_template('제안')
    if tpl and tpl.lower().endswith('.pptx'):
        g = os.path.join(od, '%s_%s_%s.pptx' % (safe_name(site), safe_name(kind), ymd6()))
        try:
            zip_replace(tpl, g, {'{{현장}}': site, '{{날짜}}': today().isoformat(), '{{종류}}': kind})
            return f, g
        except Exception:
            pass
    return f, None

def run():
    title('1. 제안서 후보 + 초안')
    days = int(ask('최근 며칠에서 찾을까요? (기본 3) > ', '3') or 3)
    hits = scan(days)
    if not hits:
        print('최근 %d일 회의록에 자료 요청이 없습니다. 오늘은 만들 것이 없습니다.' % days)
        print('(하루 한 장을 억지로 채우지 않습니다)')
        return
    bag = {}
    for site, kind, line, p in hits:
        bag.setdefault((site, kind), []).append(line)
    keys = list(bag)
    print('')
    print('후보 %s건' % won(len(keys)))
    for i, (s, k) in enumerate(keys, 1):
        print(' %2d. [%s] %s  (근거 %d줄)' % (i, s, k, len(bag[(s, k)])))
    sel = ask('\n번호 (엔터=전부 만들기) > ')
    pick = [keys[int(sel) - 1]] if sel.isdigit() and 1 <= int(sel) <= len(keys) else keys
    print('')
    for s, k in pick:
        f, g = draft(s, k, bag[(s, k)])
        print('만듦 : %s' % f)
        if g:
            print('       %s (원틀 적용)' % g)
    log('제안서초안', '%d건' % len(pick))

if __name__ == '__main__':
    run(); pause()

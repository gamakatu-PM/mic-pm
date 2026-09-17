# -*- coding: utf-8 -*-
"""43. 확정 입력·찾기 - 프로님이 고친 것을 결정 사항으로 남긴다. 토큰 0.
  ★KM_번호입력 -> 43 : 현장 / 항목 / 값 / 근거 네 칸만 넣는다 (엔터로 넘어가면 기본값)
  찾기 : 43 을 누른 뒤 첫 칸에 「?낱말」 을 넣으면 확정 대장에서 그 낱말을 찾아 보여 준다 (예: ?연합, ?공정)
  받은답 csv 한 줄 `확정,현장,항목,값,근거` 도 같은 효과 (30번·36번이 반영). 확정사항.csv 를 직접 고쳐도 된다.
표준 항목 : 공정단계(외함·속판·기구물제작·벽지·빽커버·기구물설치·강전·약전·시운전) · 객실수 · 준공일 · 발주처 · 시공사 · 계약금액 · 증감누적 · 담당자 · 결정 · 메모
"""
import os, sys
import common
from common import *
import facts

TOOL = '확정'
ITEMS = ['공정단계', '객실수', '준공일', '발주처', '시공사', '계약금액', '증감누적', '담당자', '결정', '메모']

def show(rows, title_=''):
    if title_:
        print(title_)
    if not rows:
        print('  (없음)'); return
    print('  %-10s %-14s %-10s %-24s %-24s %s' % ('일자', '현장', '항목', '값', '근거', '상태'))
    for d in rows:
        print('  %-10s %-14s %-10s %-24s %-24s %s' % (d['일자'], d['현장'][:14], d['항목'][:10], d['값'][:24], d['근거'][:24], d['상태']))

def find(q):
    rows = facts.search(q)
    show(rows, '「%s」 확정 대장에서 %d줄' % (q, len(rows)))
    return rows

def sites():
    try:
        import sitebook
        return [d['site'] for d in sitebook.load()]
    except Exception:
        return []

def run(argv=None):
    title('43. 확정 입력·찾기   (프로님이 고친 값 = 결정 사항. 추정보다 항상 우선. 토큰 0)')
    print('파일 : %s' % facts.path())
    cur = facts.load()
    show(cur[:8], '최근 확정 %d건 (전체 %d)' % (min(8, len(cur)), len(cur)))
    print('')
    print('현장 이름을 넣으십시오. 찾기는 「?낱말」 (예: ?연합 / ?공정). 그냥 엔터 = 나가기')
    ss = sites()
    if ss:
        print('현장대장 : ' + ' / '.join(ss[:12]))
    site = ask('현장 > ', '').strip()
    if not site:
        return None
    if site.startswith('?'):
        find(site[1:].strip())
        return None
    print('항목 : ' + ' / '.join('%d %s' % (i + 1, x) for i, x in enumerate(ITEMS)) + '  (번호 또는 글자)')
    item = ask('항목 > ', '1').strip()
    if item.isdigit() and 1 <= int(item) <= len(ITEMS):
        item = ITEMS[int(item) - 1]
    if item == '공정단계':
        print('단계 : ' + ' / '.join('%d %s' % (i + 1, x) for i, x in enumerate(facts.STEPS)) + '  (번호 또는 글자. 「외함 납품 중」 처럼 문장도 됨)')
    value = ask('값 > ', '').strip()
    if item == '공정단계' and value.isdigit() and 1 <= int(value) <= 9:
        value = facts.STEPS[int(value) - 1]
    if not value:
        print('값이 비어 있어 넣지 않았습니다.'); return None
    basis = ask('근거 (엔터=프로님 확인) > ', '프로님 확인').strip()
    old = facts.get(site, item)
    new = facts.add(site, item, value, basis)
    print('')
    print('확정 : %s · %s = %s  (%s)' % (site, item, value, basis))
    if old:
        print('이전 : %s (%s) -> 상태=이전 으로 남김' % (old['값'], old['일자']))
    print('다음 아침 한 장(42)·현황판·클로드용 md 부터 이 값이 이깁니다. 지금 바로 보시려면 42번.')
    try:
        if not common.AUTO and ask('아침 한 장을 지금 다시 만들까요? (y=엔터 / n) > ', 'y').lower().startswith('y'):
            import t42_morning as MO
            MO.run(quiet=True)
    except Exception as e:
        print('[42 실패] %s' % e)
    return new

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--find':
        find(' '.join(sys.argv[2:]))
    else:
        run(); pause()

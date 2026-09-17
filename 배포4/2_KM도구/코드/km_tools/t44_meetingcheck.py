# -*- coding: utf-8 -*-
"""44. 회의록 확인 - 저장만 해 둔 PLAUD 회의록을 「읽었다」고 표시한다. 토큰 0.
프로님 : "플라우드 회의록은 저장만 하고 (넘어가네). 내가 확인을 못 하니 미확인. 그것을 매일 표현해 달라."

  · 표시 안 된 회의는 42 아침 한 장 **맨 위 「미확인 회의록」** 에 매일 뜬다 (오래될수록 빨강).
  · 44번을 누르면 미확인 목록이 번호와 함께 나온다. 읽은 번호를 「1,3,5」 처럼 넣으면 그 줄이 사라진다.
  · 「a」 = 전부 확인 / 「o3」 = 3번 회의록 워드 열기 / 엔터 = 나가기
  · 받은답 csv 한 줄 `회의확인,<회의폴더>,확인,메모` 로도 된다 (30번·36번이 반영).
확인 대장 : _도구결과\\_대장\\회의확인.csv  (확인일·회의폴더·현장·메모·누가)
"""
import os, sys, datetime
import common
from common import *
import facts

TOOL = '회의록확인'

def unchecked(days=None):
    """미확인 회의 [dict] 오래된 것 먼저"""
    import t42_morning as MO
    done = facts.checked()
    out = []
    for m in MO.meetings():
        if facts._norm(os.path.basename(m['folder'])) in done:
            continue
        gap = (today() - m['day']).days if m['day'] else None
        if days is not None and gap is not None and gap > days:
            continue
        m['gap'] = gap
        out.append(m)
    out.sort(key=lambda m: m['day'] or datetime.date(2000, 1, 1))
    return out

def line(i, m):
    return '%2d. %-10s %-12s %-16s %s%s' % (
        i, (m['day'].isoformat()[5:] if m['day'] else '날짜?'), (m['site'] or '?')[:12], (m['who'] or '')[:16],
        (m['agenda'] or (m['decisions'][0] if m['decisions'] else ''))[:40],
        ('  [%d일 지남]' % m['gap']) if m['gap'] and m['gap'] > 2 else '')

def run():
    title('44. 회의록 확인   (저장만 해 둔 회의록을 읽었다고 표시. 미확인은 아침 한 장 맨 위에 매일 뜬다)')
    xs = unchecked()
    if not xs:
        print('미확인 회의록이 없습니다. 전부 확인하셨습니다.')
        return True
    print('미확인 회의록 %d건 (오래된 것부터)' % len(xs))
    print('-' * 88)
    for i, m in enumerate(xs, 1):
        print(line(i, m))
        for t in m['todos'][:2]:
            print('     할 일 : %s' % t[:70])
        for d in m['decisions'][:1]:
            print('     결정   : %s' % d[:70])
    print('-' * 88)
    print('읽은 번호를 넣으십시오.  예) 1,3,5   /   a = 전부 확인   /   o3 = 3번 워드 열기   /   엔터 = 나가기')
    while True:
        s = ask('> ', '').strip()
        if not s:
            return True
        if s.lower().startswith('o'):
            try:
                m = xs[int(s[1:]) - 1]
                open_file(m['docx']) or open_folder(m['folder'])
                print('열었습니다 : %s' % os.path.basename(m['docx']))
            except Exception:
                print('번호를 다시 넣으십시오.')
            continue
        if s.lower() == 'a':
            pick = list(range(1, len(xs) + 1))
        else:
            pick = []
            for t in s.replace(' ', '').split(','):
                if t.isdigit() and 1 <= int(t) <= len(xs):
                    pick.append(int(t))
        if not pick:
            print('번호를 다시 넣으십시오.')
            continue
        n = 0
        for i in pick:
            m = xs[i - 1]
            if facts.check_meeting(os.path.basename(m['folder']), m['site'], (m['agenda'] or '')[:40]):
                n += 1
        print('%d건 확인 처리했습니다. (대장 : %s)' % (n, facts.chk_path()))
        left = unchecked()
        print('남은 미확인 %d건' % len(left))
        try:
            if not common.AUTO:
                import t42_morning as MO
                MO.build(quiet=True)
                print('아침 한 장을 다시 만들었습니다.')
        except Exception:
            pass
        return True

if __name__ == '__main__':
    run(); pause()

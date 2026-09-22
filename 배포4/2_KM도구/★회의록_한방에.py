# -*- coding: utf-8 -*-
"""★회의록 한 방에 — 이 파일만 더블클릭하십시오. (2026-09-22)

PLAUD 메모장을 넣어 두시고 이것 하나만 누르시면, 아래가 저절로 다 됩니다.

    1) 회의록 만들기          40번 : 받는함 txt -> _현장비서 -> 회의록(docx + meta.json)
    2) 구글 드라이브로 올리기  51번 : 회의록 -> 드라이브\회의록\incoming
    3) 메일 원고 만들기        52번 : meta.json -> 「회의록정리_YYMMDD.txt」  (AI 사용량 0)
    4) 메일 원고를 드라이브로   드라이브\KM_아침메일\ 에 올려 둔다
                               -> 내일 07:00 앱스 스크립트가 읽어서 메일로 보냅니다

차장님 손은 두 번뿐입니다 : PLAUD 메모장 저장 -> 이 파일 누르기. 그다음은 전부 저절로.

왜 시작.py 가 아니라 이 파일인가
    시작.py 엔터는 「오늘 한 방에」 가 돌면서 새 zip 을 자동 적용합니다.
    그 zip 이 51번 연결을 지워 버리는 일이 3번 있었습니다(2026-09-22).
    이 파일은 2_KM도구 폴더 바로 아래에 있어 zip 이 건드리지 않습니다.

※ 전에 드린 「★회의록_드라이브로.py」 는 위 2)번만 하던 것입니다.
  이 파일이 그것을 품고 있으니 앞으로는 이것만 누르시면 됩니다. (그 파일은 지우지 않았습니다)
"""
import os, sys, io, shutil, datetime, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = []


def say(s=''):
    print(s)
    NOTE.append(s)


def find_tools():
    """km_tools 폴더를 스스로 찾는다."""
    cands = [os.path.join(HERE, '코드', 'km_tools'),
             os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
             os.path.join(HERE, 'km_tools')]
    for p in cands:
        if os.path.isfile(os.path.join(p, 't51_driveup.py')):
            return p
    for root, _dirs, files in os.walk(HERE):
        if 't51_driveup.py' in files and root.count(os.sep) - HERE.count(os.sep) <= 3:
            return root
    return ''


def step(n, title, fn):
    """한 걸음. 넘어져도 다음 걸음으로 간다."""
    say('')
    say('-' * 60)
    say(' %d) %s' % (n, title))
    say('-' * 60)
    try:
        return fn()
    except Exception:
        say('  ★ 여기서 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        for ln in traceback.format_exc().split('\n'):
            say('    ' + ln)
        return None


def main():
    say('=' * 60)
    say(' 회의록 한 방에        %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
    say('=' * 60)

    tools = find_tools()
    if not tools:
        say('')
        say('★ 도구 폴더(km_tools)를 못 찾았습니다.')
        say('  이 파일이 「2_KM도구」 폴더 바로 아래에 있어야 합니다.')
        say('  지금 자리 : %s' % HERE)
        return
    sys.path.insert(0, tools)
    say(' 도구 자리 : %s' % tools)

    # ── 1) 회의록 만들기 (40번) ───────────────────────────
    def s1():
        try:
            import t40_meeting as MT
        except Exception:
            say('  40번이 없어 건너뜁니다. (회의록을 이미 만들어 두셨다면 그대로 진행됩니다)')
            return None
        r = MT.run() if hasattr(MT, 'run') else None
        say('  회의록 만들기 끝.')
        return r
    step(1, '회의록 만들기  (PLAUD 메모장 -> 회의록)', s1)

    # ── 2) 드라이브로 올리기 (51번) ───────────────────────
    drive = ['']

    def s2():
        import t51_driveup as DU
        drive[0] = DU.drive_root()
        r = DU.run(quiet=True)
        if r.get('이유'):
            say('  못 올렸습니다 : %s' % r['이유'])
        else:
            say('  찾음 %s개 / 새로 올림 %s개' % (r.get('찾음', 0), r.get('올림', 0)))
        return r
    r2 = step(2, '구글 드라이브로 올리기', s2)

    # ── 3) 메일 원고 만들기 (52번) ────────────────────────
    made = ['']

    def s3():
        import t52_mailbuild as MB
        root = drive[0]
        if not root:
            say('  드라이브 폴더를 못 찾아 건너뜁니다.')
            return None
        meta_dir = os.path.join(root, '회의록', 'incoming')
        if not os.path.isdir(meta_dir):
            say('  %s 가 없어 건너뜁니다.' % meta_dir)
            return None
        today = datetime.date.today()
        frm = (today - datetime.timedelta(days=1)).strftime('%y%m%d')   # 어제부터
        to = today.strftime('%y%m%d')
        out = os.path.join(HERE, '_회의록정리')
        text, stat = MB.run(meta_dir, frm, to, out=out, today=today)
        made[0] = os.path.join(out, '회의록정리_%s.txt' % to)
        say('  기간 : %s ~ %s' % (frm, to))
        say('  회의 %s건 / 현장 %s개 / %s줄' % (stat['회의수'], stat['현장수'], stat['줄수']))
        if stat.get('현장별'):
            for k, v in sorted(stat['현장별'].items(), key=lambda x: -x[1]['회의']):
                say('      %-14s 협의 %d건' % (k, v['회의']))
        say('  만든 곳 : %s' % out)
        return stat
    r3 = step(3, '메일 원고 만들기  (AI 사용량 0)', s3)

    # ── 4) 메일 원고를 드라이브로 ─────────────────────────
    def s4():
        if not made[0] or not os.path.isfile(made[0]):
            say('  올릴 원고가 없어 건너뜁니다.')
            return None
        root = drive[0]
        if not root:
            say('  드라이브 폴더를 못 찾아 건너뜁니다.')
            return None
        dest = os.path.join(root, 'KM_아침메일')
        if not os.path.isdir(dest):
            os.makedirs(dest)
        tgt = os.path.join(dest, os.path.basename(made[0]))
        shutil.copy2(made[0], tgt)
        say('  올렸습니다 : %s' % tgt)
        say('  내일 07:00 에 앱스 스크립트가 이것을 읽어 메일로 보냅니다.')
        return tgt
    step(4, '메일 원고를 드라이브로 올리기', s4)

    # ── 마무리 ────────────────────────────────────────────
    say('')
    say('=' * 60)
    if r3 and r3.get('회의수'):
        say(' 끝났습니다. 회의 %d건 / 현장 %d개 가 메일로 나갑니다.' % (r3['회의수'], r3['현장수']))
        say(' 지금 바로 보시려면 「_회의록정리」 폴더의 html 을 여십시오.')
        say(' 급하시면 클로드 대화창에 「지금 보내」 라고만 하십시오.')
    elif r2 and r2.get('이유'):
        say(' 멈춘 까닭 : %s' % r2['이유'])
        say(' 위 화면을 클로드에게 보여 주십시오.')
    elif r2 and not r2.get('찾음'):
        say(' 새 회의록을 못 찾았습니다. 위 목록을 클로드에게 보여 주십시오.')
    else:
        say(' 새로 정리할 회의록이 없습니다 (전부 전에 처리한 것).')
    say('=' * 60)


def save_note():
    """화면이 꺼져도 볼 수 있게 남긴다."""
    p = os.path.join(HERE, '한방에_결과.txt')
    try:
        with io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n') as f:
            f.write('\n'.join(NOTE))
        try:
            os.startfile(p)
        except Exception:
            pass
    except Exception:
        pass


if __name__ == '__main__':
    try:
        main()
    except Exception:
        say('')
        say('★ 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        for ln in traceback.format_exc().split('\n'):
            say('  ' + ln)
    finally:
        save_note()
        try:
            input('\n엔터를 누르면 닫힙니다... ')
        except Exception:
            pass

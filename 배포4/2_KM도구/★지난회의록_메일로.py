# -*- coding: utf-8 -*-
"""★지난 회의록 메일로 — 이미 쌓여 있는 회의록을 메일로 받으실 때. (2026-09-22)

「★회의록_한방에.py」 는 어제~오늘 것만 봅니다.
그 전에 쌓아 두신 회의록을 받고 싶으실 때 이 파일을 누르십시오.

누르면 물어봅니다
    언제부터 ? 260901    (엔터만 치시면 지난 30일)
    언제까지 ? 260920    (엔터만 치시면 오늘)
    현장당 따로 보낼까요? (y/엔터)

그러면
    드라이브\회의록\incoming 의 meta.json 을 그 기간만 골라
    메일 원고를 만들어 드라이브\KM_아침메일\ 에 올려 둡니다.
    5분 안에 KM_즉시발송 이 bsy 메일로 보냅니다.

AI 사용량 0. 파이썬만 돕니다.
"""
import os, sys, io, re, shutil, datetime, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = []


def say(s=''):
    print(s)
    NOTE.append(s)


def find_tools():
    cands = [os.path.join(HERE, '코드', 'km_tools'),
             os.path.join(HERE, '2_도구모음_25종', '코드', 'km_tools'),
             os.path.join(HERE, 'km_tools')]
    for p in cands:
        if os.path.isfile(os.path.join(p, 't52_mailbuild.py')):
            return p
    for root, _dirs, files in os.walk(HERE):
        if 't52_mailbuild.py' in files and root.count(os.sep) - HERE.count(os.sep) <= 3:
            return root
    return ''


def ask(q, default):
    try:
        v = input(q).strip()
    except Exception:
        v = ''
    return v or default


def norm_ymd(v, fallback):
    """260901 / 26-09-01 / 2026-09-01 을 다 받아 260901 로."""
    d = re.sub(r'\D', '', str(v or ''))
    if len(d) == 8:
        d = d[2:]
    if len(d) == 6 and d.isdigit():
        return d
    return fallback


def run(d_from=None, d_to=None, per_site=False, drive=None, out=None):
    """시험에서도 부를 수 있게 물어보는 부분과 떼어 놓았다."""
    tools = find_tools()
    if not tools:
        say('★ 도구 폴더(km_tools)를 못 찾았습니다. 이 파일이 「2_KM도구」 바로 아래에 있어야 합니다.')
        say('  지금 자리 : %s' % HERE)
        return None
    sys.path.insert(0, tools)

    if drive is None:
        import t51_driveup as DU
        drive = DU.drive_root()
    if not drive:
        say('★ 구글 드라이브 폴더를 못 찾았습니다. 드라이브 데스크톱이 켜져 있는지 보십시오.')
        return None

    meta_dir = os.path.join(drive, '회의록', 'incoming')
    if not os.path.isdir(meta_dir):
        say('★ %s 가 없습니다. 먼저 51번으로 회의록을 올리십시오.' % meta_dir)
        return None

    import t52_mailbuild as MB
    today = datetime.date.today()
    out = out or os.path.join(HERE, '_지난회의록')
    text, stat = MB.run(meta_dir, d_from, d_to, out=out, today=today)

    say(' 기간 : %s ~ %s' % (d_from, d_to))
    say(' 회의 %s건 / 현장 %s개 / %s줄' % (stat['회의수'], stat['현장수'], stat['줄수']))
    if not stat['회의수']:
        say('')
        say(' 그 기간에 회의록이 없습니다. 날짜를 넓혀 보십시오.')
        return stat
    for k, v in sorted(stat.get('현장별', {}).items(), key=lambda x: -x[1]['회의']):
        say('     %-14s 협의 %d건' % (k, v['회의']))

    dest = os.path.join(drive, 'KM_아침메일')
    if not os.path.isdir(dest):
        os.makedirs(dest)

    stamp = today.strftime('%y%m%d')
    tag = '%s-%s' % (d_from, d_to)
    put = []
    if per_site:
        per = os.path.join(out, '현장별_%s' % stamp)
        for fn in sorted(os.listdir(per)) if os.path.isdir(per) else []:
            if not fn.endswith('.txt'):
                continue
            site = os.path.splitext(fn)[0]
            tgt = os.path.join(dest, '회의록정리_%s_%s_%s.txt' % (stamp, tag, site))
            shutil.copy2(os.path.join(per, fn), tgt)
            put.append(tgt)
    else:
        src = os.path.join(out, '회의록정리_%s.txt' % stamp)
        tgt = os.path.join(dest, '회의록정리_%s_%s.txt' % (stamp, tag))
        shutil.copy2(src, tgt)
        put.append(tgt)

    say('')
    say(' 드라이브에 %d개 올렸습니다.' % len(put))
    for p in put:
        say('   %s' % os.path.basename(p))
    say('')
    say(' 5분 안에 bsy 메일로 갑니다.')
    stat['올린파일'] = put
    return stat


def main():
    say('=' * 60)
    say(' 지난 회의록 메일로        %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
    say('=' * 60)
    say('')
    say(' 날짜는 260901 처럼 여섯 자리로 치십시오. 그냥 엔터만 쳐도 됩니다.')
    say('')

    today = datetime.date.today()
    d30 = (today - datetime.timedelta(days=30)).strftime('%y%m%d')
    d_from = norm_ymd(ask(' 언제부터 ? (엔터=지난 30일 %s) : ' % d30, d30), d30)
    d_to = norm_ymd(ask(' 언제까지 ? (엔터=오늘 %s) : ' % today.strftime('%y%m%d'),
                        today.strftime('%y%m%d')), today.strftime('%y%m%d'))
    if d_from > d_to:
        d_from, d_to = d_to, d_from
    per = ask(' 현장당 따로 보낼까요 ? (y / 엔터=한 통) : ', '').lower().startswith('y')

    say('')
    say('-' * 60)
    try:
        run(d_from, d_to, per)
    except Exception:
        say('★ 멈췄습니다. 아래 글자를 클로드에게 보여 주십시오.')
        for ln in traceback.format_exc().split('\n'):
            say('  ' + ln)
    say('=' * 60)


def save_note():
    p = os.path.join(HERE, '지난회의록_결과.txt')
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
    finally:
        save_note()
        try:
            input('\n엔터를 누르면 닫힙니다... ')
        except Exception:
            pass

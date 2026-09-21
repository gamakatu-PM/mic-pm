# -*- coding: utf-8 -*-
"""아침대장 CSV 만들기 (2026-09-21)

무엇을 하나
  저장소의 확정 대장(앞으로할것.csv)을 읽어서, 앱스 스크립트가 판단 없이 그대로
  메일 3통으로 찍어낼 수 있는 한 장짜리 CSV 를 만든다.

왜 CSV 인가
  앱스 스크립트는 구글 서버에서 07:00 에 혼자 돈다. 그때 클로드도 PC 도 없어도 된다.
  그래서 「무엇을 보낼지」는 전날까지 CSV 에 다 적혀 있어야 한다.

쓰는 법
  python3 아침대장_만들기.py            -> 아침대장_YYMMDD.csv 를 옆에 만든다
  python3 아침대장_만들기.py --out 경로

열 : 구분,코드,현장,때,등급,상태,할일,누가,왜,만들기,경과일
  구분 = 설정 | 답해주십시오 | 오늘할것 | 어제일어난일
"""
import os, io, csv, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.normpath(os.path.join(
    HERE, '..', '..', '배포4', '3_공통사용', '산출물', '도구결과', '_대장', '앞으로할것.csv'))
HEAD = ['구분', '코드', '현장', '때', '등급', '상태', '할일', '누가', '왜', '만들기', '경과일']
받는사람 = 'bsy@micronic.co.kr'


def _read(p):
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                return list(csv.DictReader(fp))
        except Exception:
            continue
    return []


def _days(s, today):
    """일자 문자열과 오늘 사이의 날 수. 못 읽으면 빈칸"""
    for f in ('%Y-%m-%d', '%y%m%d', '%Y/%m/%d'):
        try:
            return (today - datetime.datetime.strptime(s.strip(), f).date()).days
        except Exception:
            continue
    return ''


def build(today=None):
    today = today or datetime.date.today()
    rows = [r for r in _read(LEDGER) if (r.get('현장') or '').strip()]
    out = []

    # 설정 — 앱스 스크립트가 이 줄들을 먼저 읽는다
    out.append(['설정', '받는사람', 받는사람, '', '', '', '', '', '', '', ''])
    out.append(['설정', '만든날', today.strftime('%Y-%m-%d'), '', '', '', '', '', '', '', ''])
    out.append(['설정', '만든이', '클로드', '', '', '', '', '', '', '', ''])

    for r in rows:
        상태 = (r.get('상태') or '').strip()
        if 상태 in ('완료', '취소'):
            continue
        등급 = (r.get('등급') or '').strip()
        경과 = _days(r.get('일자') or '', today)
        줄 = [r.get('코드', ''), r.get('현장', ''), r.get('때', ''), 등급, 상태,
              r.get('할일', ''), r.get('누가', ''), r.get('왜', ''), r.get('만들기', ''),
              str(경과)]
        # ① 답해 주십시오 = 아직 제안 등급인 것 (확정이 안 난 것만)
        if 등급 == '제안':
            out.append(['답해주십시오'] + 줄)
        else:
            out.append(['오늘할것'] + 줄)
    return out


def main():
    args = sys.argv[1:]
    today = datetime.date.today()
    if '--today' in args:
        today = datetime.datetime.strptime(args[args.index('--today') + 1], '%Y-%m-%d').date()
    out = args[args.index('--out') + 1] if '--out' in args else \
        os.path.join(HERE, '아침대장_%s.csv' % today.strftime('%y%m%d'))
    rows = build(today)
    with io.open(out, 'w', encoding='utf-8-sig', newline='') as fp:
        w = csv.writer(fp)
        w.writerow(HEAD)
        w.writerows(rows)
    print('만들었습니다 : %s  (설정 3줄 + 할 일 %d줄)' % (out, len(rows) - 3))
    return out


if __name__ == '__main__':
    main()

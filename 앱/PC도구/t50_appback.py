# -*- coding: utf-8 -*-
"""50. 앱에서 온 것 받기 — 「KM 손바닥」 앱이 보낸 줄을 회사 대장에 넣는다. 토큰 0.

프로님 (2026-09-19) : "앱에서 소통해서 결론 난 데이터를 저장하는 곳이 있나?" → 1번(자동으로 보내기) 선택.

  읽는 곳 (있는 것부터)
    ① 메일   : 설정.ini [메일] 계정의 받은편지함에서 제목이 「[KM] 회신」 인 것
    ② 파일   : 다운로드\\KM_회의록받는함\\앱회신.txt  (메일이 막혔을 때 붙여넣기)
  넣는 곳 (append — 기존 줄을 지우지 않는다)
    확정사항.csv   ← 확정,현장,항목,값,근거
    전화번호부.csv ← 담당자,현장,역할,이름,회사,전화
    경계.csv       ← 경계,현장,항목,누가,확정|추정      (없으면 만든다)
    하자.csv       ← 하자,현장,객실,내용,사진
    앞으로할것.csv ← 답/완료/진행중  (48번이 이미 하는 것은 건드리지 않는다)
    _클로드부탁서  ← 질문,현장,내용 · 못 알아들은 줄
  48번(회신 읽기)과 겹치지 않는다 : 48번은 「KM-003 완료」 같은 번호 줄, 50번은 쉼표로 칸이 나뉜 줄.
"""
import os, re, io, csv, sys, glob, datetime, configparser

TOOL = '앱받기'
MARK = '[KM] 회신'
INBOX_TXT = '앱회신.txt'

HEAD = {
    '확정사항.csv':   ['일자', '현장', '항목', '값', '근거', '누가', '상태'],
    '전화번호부.csv': ['현장', '역할', '이름', '회사', '전화', '적은날'],
    '경계.csv':       ['일자', '현장', '항목', '누가', '확정여부', '근거'],
    '하자.csv':       ['일자', '현장', '객실', '내용', '사진', '상태'],
}

def rd(p):
    try: b = open(p, 'rb').read()
    except Exception: return ''
    for e in ('utf-8-sig', 'cp949', 'utf-8'):
        try: return b.decode(e)
        except Exception: pass
    return b.decode('utf-8', 'replace')

def append(path, head, row):
    """머리글이 없으면 넣고, 같은 줄이 이미 있으면 건너뛴다(두 번 받아도 안 늘어난다)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = rd(path)
    key = ','.join(str(x) for x in row[1:4])
    if key and key in old:
        return False
    new = not old.strip()
    with open(path, 'a', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        if new: w.writerow(head)
        w.writerow(row)
    return True

def split_line(ln):
    """쉼표로 나누되, 값 안의 쉼표는 앱이 이미 · 로 바꿔 보낸다."""
    return [x.strip() for x in ln.split(',')]

def take(lines, led, out_dir, today):
    got = {'확정': 0, '담당자': 0, '경계': 0, '하자': 0, '질문': 0, '기타': 0, '건너뜀': 0}
    asks, unknown = [], []
    for raw in lines:
        ln = (raw or '').strip().strip('-·• \t')
        if not ln or ',' not in ln:
            continue
        c = split_line(ln)
        head = c[0]
        try:
            if head in ('확정', '추정', '진행중') and len(c) >= 4:
                if head != '확정':          # 확정만 대장에 넣는다. 추정은 아직 결론이 아니다
                    got['건너뜀'] += 1; continue
                ok = append(os.path.join(led, '확정사항.csv'), HEAD['확정사항.csv'],
                            [today, c[1], c[2], c[3], (c[4] if len(c) > 4 else '앱'), '앱(프로님)', '확정'])
                got['확정'] += 1 if ok else 0
            elif head == '담당자' and len(c) >= 5:
                ok = append(os.path.join(led, '전화번호부.csv'), HEAD['전화번호부.csv'],
                            [c[1], c[2], c[3], (c[4] if len(c) > 4 else ''), (c[5] if len(c) > 5 else ''), today])
                got['담당자'] += 1 if ok else 0
            elif head == '경계' and len(c) >= 4:
                ok = append(os.path.join(led, '경계.csv'), HEAD['경계.csv'],
                            [today, c[1], c[2], c[3], (c[4] if len(c) > 4 else ''), '앱'])
                got['경계'] += 1 if ok else 0
            elif head == '하자' and len(c) >= 4:
                ok = append(os.path.join(led, '하자.csv'), HEAD['하자.csv'],
                            [today, c[1], c[2], c[3], (c[4] if len(c) > 4 else ''), '대기'])
                got['하자'] += 1 if ok else 0
            elif head == '질문':
                asks.append(ln); got['질문'] += 1
            elif head in ('답', '메모', '회의', '일정', '돈', '요청', '현장명', '앱고침', '비움'):
                got['기타'] += 1
            else:
                unknown.append(ln)
        except Exception as e:
            unknown.append(ln + '   (읽다 막힘: %s)' % e)
    # 클로드에게 넘길 것
    if asks or unknown:
        p = os.path.join(out_dir, '_클로드부탁서_앱.md')
        with open(p, 'a', encoding='utf-8') as f:
            f.write('\n## %s 앱에서 온 것\n' % today)
            for a in asks:    f.write('- 프로님 질문 : %s\n' % a)
            for u in unknown: f.write('- 못 알아들은 줄 : %s\n' % u)
    return got, asks, unknown

def from_mail(cfg):
    """메일에서 [KM] 회신 을 읽어 줄 목록으로. 48번과 같은 계정·같은 방식."""
    try:
        import imaplib, email
        from email.header import decode_header
    except Exception:
        return []
    g = lambda k, d='': (cfg.get('메일', k, fallback=d) or d).strip()
    host = g('imap') or (g('smtp') or 'smtp.gmail.com').replace('smtp.', 'imap.')
    user, pw = g('user'), g('pass')
    if not user or not pw:
        return []
    out = []
    try:
        M = imaplib.IMAP4_SSL(host, int(g('imap_port') or 993))
        M.login(user, pw); M.select('INBOX')
        typ, data = M.search(None, 'UNSEEN')
        for num in (data[0].split() if data and data[0] else []):
            t, d = M.fetch(num, '(RFC822)')
            if not d or not d[0]: continue
            msg = email.message_from_bytes(d[0][1])
            subj = ''
            for s, enc in decode_header(msg.get('Subject') or ''):
                subj += s.decode(enc or 'utf-8', 'replace') if isinstance(s, bytes) else s
            if MARK not in subj: continue
            body = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body += (part.get_payload(decode=True) or b'').decode('utf-8', 'replace')
            else:
                body = (msg.get_payload(decode=True) or b'').decode('utf-8', 'replace')
            out += body.split('\n')
        M.close(); M.logout()
    except Exception as e:
        print('메일을 못 읽었습니다 :', e)
    return out

def run(base=None, quiet=False):
    if base is None:
        try:
            import common; base = common.cfg('common')
        except Exception:
            base = os.getcwd()
    today = datetime.date.today().isoformat()
    led = os.path.join(base, '산출물', '도구결과', '_대장')
    if not os.path.isdir(led):
        alt = os.path.join(base, '_도구결과', '_대장')
        led = alt if os.path.isdir(alt) else led
    out_dir = os.path.join(base, '산출물', '도구결과', '앱받기', datetime.date.today().strftime('%y%m%d'))
    os.makedirs(out_dir, exist_ok=True)

    cfg = configparser.ConfigParser()
    for ini in (os.path.join(base, '설정.ini'), os.path.join(base, '..', '설정.ini')):
        if os.path.exists(ini):
            cfg.read(ini, encoding='utf-8'); break

    lines = from_mail(cfg)
    src = '메일'
    if not lines:
        for p in (os.path.join(os.path.expanduser('~'), 'Downloads', 'KM_회의록받는함', INBOX_TXT),
                  os.path.join(base, INBOX_TXT)):
            if os.path.exists(p):
                lines = rd(p).split('\n'); src = os.path.basename(p); break
    if not lines:
        if not quiet:
            print('앱에서 온 것이 없습니다.')
            print('  · 메일 : 제목에 「%s」 가 있는 안 읽은 메일' % MARK)
            print('  · 파일 : 다운로드\\KM_회의록받는함\\%s 에 붙여넣기' % INBOX_TXT)
        return {'확정': 0, '읽은곳': ''}

    got, asks, unknown = take(lines, led, out_dir, today)
    if not quiet:
        print('앱에서 온 것 (%s)' % src)
        print('  확정 대장  +%d' % got['확정'])
        print('  전화번호부 +%d' % got['담당자'])
        print('  경계       +%d' % got['경계'])
        print('  하자       +%d' % got['하자'])
        print('  프로님 질문 %d건 · 못 알아들은 줄 %d건 → _클로드부탁서_앱.md' % (len(asks), len(unknown)))
        if got['건너뜀']: print('  추정·진행중 %d줄은 넣지 않았습니다 (확정만 대장에 들어갑니다)' % got['건너뜀'])
    got['읽은곳'] = src
    return got

if __name__ == '__main__':
    run()

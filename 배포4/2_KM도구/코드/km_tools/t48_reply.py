# -*- coding: utf-8 -*-
"""48. 회신 읽기 - 프로님이 고치신 것을 받아서 반영한다. 토큰 0.
프로님 (2026-09-18) : "매일 메일로 보내는 것은 너무 일방적이야. 니가 보낸 것이 틀릴 수 있는데
                      그걸 내가 바로잡아서 너와 소통을 해야 하는데 방법을 만들어."

  받는 길 3가지 (셋 다 같은 곳으로 들어온다)
    ① 메일 회신   : 아침 메일에 그대로 회신 → 48번이 메일함(IMAP)에서 읽는다
    ② 파일       : 다운로드\\KM_회의록받는함\\회신.txt 에 한 줄씩 적어도 된다 (메일이 막혔을 때)
    ③ 대화       : 클로드에게 말씀하시면 받은답 `회신,KM-003,아니야 1개 층 선납으로` 로 들어온다

  한 줄 문법 (번호 + 말)   번호는 **고정**입니다 — 끝날 때까지 안 바뀝니다
    KM-003 완료 / 3 완료 / 3 했어              -> 완료 (내일부터 안 뜸)
    3 확인 / 3 맞아 / 3 그대로                  -> 확정 (제안 -> 확정)
    3 아니야 1개 층 선납으로 / 3 틀려 ...       -> 수정 (옛 값은 이력에 남김)
    3 만들어줘                                   -> 「제가 만들까요?」 에 예 (만들 것 목록으로)
    3 취소 / 3 빼                                -> 취소
    3 미뤄 22일 / 3 연기 다음주                  -> 때를 바꿈
    그 밖의 말                                   -> 「제가 못 알아들었습니다」 로 다음 메일에 되물음
"""
import os, sys, re, io, email, imaplib, configparser
from email.header import decode_header
import common
from common import *
import facts

TOOL = '회신'
INBOX_TXT = '회신.txt'

# ---------------- 한 줄 해석 ----------------
DONE = ('완료', '했어', '했음', '끝', '됐어', '됐음', 'ok', 'o.k', '오케이', '처리')
OKAY = ('확인', '맞아', '맞음', '그대로', '진행', '좋아', '예스', 'yes')
NOPE = ('아니야', '아냐', '아님', '틀려', '틀렸', '수정', '바꿔', '바꾸', '고쳐', '변경')
MAKE = ('만들어', '만들까', '작성해', '써줘', '초안')
KILL = ('취소', '빼', '필요없', '안해', '없앰', '삭제')
HOLD = ('미뤄', '연기', '나중', '다음주', '보류', '뒤로')
ASK = ('물어봐', '확인해봐', '알아봐', '체크해')
# v46 프로님 : "진행중 을 넣어줘" - 손 댔지만 아직 안 끝난 것.
# OKAY 의 '진행' 보다 먼저 걸러야 하므로 parse_line 에서 순서가 앞선다.
WIP = ('진행중', '진행 중', '하는중', '하는 중', '하고있', '하고 있', '착수', '시작했', '보냈어', '보냄', '접수', '넣었어')

def parse_line(line):
    """한 줄 -> (코드, 명령, 값, 원문). 코드가 없으면 (None, ...)"""
    s = (line or '').strip().strip('-•·').strip()
    if not s:
        return None
    m = re.match(r'^\s*(?:KM[-\s]?)?(\d{1,4})\s*[.)\]:]?\s*(.*)$', s, re.I)
    if not m:
        return None
    code, rest = m.group(1), (m.group(2) or '').strip()
    r = rest.replace('->', '→')
    low = r.lower()
    def has(ws):
        return any(w in low for w in ws)
    if not r:
        return (code, '확인', '', s)              # 번호만 보내면 「확인」
    if has(KILL):
        return (code, '취소', r, s)
    if has(NOPE):
        val = re.sub(r'^.*?(?:%s)\s*' % '|'.join(NOPE), '', r, flags=re.I).lstrip('→ ').strip()
        return (code, '수정', val, s)
    if has(HOLD):
        # v46 고침 : 「다음주로 미뤄」 가 '로 미뤄' 로 잘리던 것.
        #            미룸 낱말을 전부 빼고 남은 조사(로/으로/까지/에)도 턴다.
        # 「미뤄·연기·보류」 는 시키는 말이라 빼고, 「다음주·나중」 은 때 그 자체라 남긴다
        val = re.sub(r'(?:미뤄|미룸|미루|연기|보류|뒤로)', ' ', r, flags=re.I)
        val = re.sub(r'\s+', ' ', val).strip()
        val = re.sub(r'^(?:로|으로|까지|에|은|는|을|를)\s*', '', val).strip()
        val = re.sub(r'\s*(?:로|으로|에)$', '', val).strip()
        return (code, '미룸', val or '미정', s)
    if has(MAKE):
        return (code, '만들기', r, s)
    if has(ASK):
        return (code, '물어봄', r, s)
    if has(WIP):
        return (code, '진행중', r, s)
    if has(DONE):
        return (code, '완료', r, s)
    if has(OKAY):
        return (code, '확인', r, s)
    return (code, '?', r, s)                      # 못 알아들음

def apply_one(route, code, cmd, val, said):
    """해석한 한 줄을 대장에 반영. (반영글, 상태) 돌려줌"""
    d = facts.plan_by_code(code)
    site = (d or {}).get('현장', '')
    todo = (d or {}).get('할일', '')
    code = 'KM-%03d' % int(re.sub(r'[^0-9]', '', str(code)) or 0)   # 보기 좋게 통일
    if not d:
        facts.talk_add(route, code, '', said, '번호를 못 찾음', '', '못알아들음')
        return ('번호 %s 를 못 찾았습니다' % code, '못알아들음')
    if cmd == '완료':
        facts.plan_done(site, todo)
        out = '완료 표시 (내일부터 안 뜹니다)'
    elif cmd == '확인':
        # v46 : 이미 확정인 줄에 「맞아」 를 하시면 대장은 안 변한다.
        #       그 사실을 그대로 적어야 프로님이 나중에 헷갈리지 않는다.
        was = (d.get('등급') or '').strip()
        facts.plan_set(code, 등급='확정')
        if was == '확정':
            out = '이미 확정이라 대장은 그대로입니다. 확인하셨다는 것만 소통이력에 남겼습니다'
        else:
            out = '확정으로 올림 (제안 → 확정)'
    elif cmd == '수정':
        if not val:
            facts.talk_add(route, code, site, said, '무엇으로 고칠지 안 적혀 있음', '', '못알아들음')
            return ('무엇으로 고칠지 못 알아들었습니다', '못알아들음')
        # 짧게 답하시면 원래 할 일을 지우지 않고 「원래 → 고친 것」 으로 남긴다 (맥락 보존)
        newtodo = val if len(val) >= 18 else ('%s → %s' % (todo, val))
        facts.plan_set(code, 할일=newtodo, 등급='확정')
        facts.add(site, '결정', val, '프로님 회신 (%s)' % route)      # 확정 대장에도 남긴다
        out = '「%s」 로 고치고 확정 대장에 남김' % newtodo[:60]
    elif cmd == '취소':
        facts.plan_set(code, 상태='취소', 완료일=today().isoformat())
        out = '취소 (목록에서 뺐습니다)'
    elif cmd == '미룸':
        facts.plan_set(code, 때=val or '미정')
        out = '때를 「%s」 로 미룸' % (val or '미정')
    elif cmd == '진행중':
        # 이미 완료·취소로 닫힌 줄은 다시 열지 않는다
        if (d.get('상태') or '').strip() in ('완료', '취소'):
            out = '이미 %s 된 줄이라 그대로 두었습니다' % (d.get('상태') or '').strip()
        else:
            facts.plan_set(code, 상태='진행중', 등급='확정')
            out = '진행중으로 표시 (목록에 남되 「진행중」 으로 뜹니다)'
    elif cmd == '만들기':
        # v46 : 바로 만들지 않는다. 「이렇게 만들겠습니다」 를 먼저 아침 한 장에 띄우고
        #       프로님이 「맞아」 하시면 그때 만든다. (프로님 : "어떻게 만들지 나하고 상의 하는 거야?")
        if (d.get('상태') or '').strip() in ('완료', '취소'):
            facts.talk_add(route, code, site, said, '제가 만들 것 : %s' % ((d.get('만들기') or todo)[:40]), '이미 닫힌 줄', '반영')
            return ('이미 %s 된 줄이라 다시 열지 않았습니다' % (d.get('상태') or '').strip(), '반영')
        facts.plan_set(code, 등급='확정', 상태='만들기대기')
        facts.talk_add(route, code, site, said, '제가 만들 것 : %s' % ((d.get('만들기') or todo)[:40]), '만들기대기', '반영')
        return ('만들 것으로 적었습니다. 내일 아침 「이렇게 만들겠습니다」 를 먼저 보여 드리고, 맞다고 하시면 만듭니다', '반영')
    elif cmd == '물어봄':
        facts.plan_set(code, 왜=(d.get('왜', '') + ' / 프로님 : ' + val)[:200])
        out = '물어볼 것으로 적어 둠'
    else:
        facts.talk_add(route, code, site, said, '무슨 뜻인지 모르겠음', '', '못알아들음')
        return ('무슨 뜻인지 못 알아들었습니다', '못알아들음')
    facts.talk_add(route, code, site, said, '%s : %s' % (cmd, val or '-'), out, '반영')
    return (out, '반영')

def apply_text(text, route='메일'):
    """여러 줄을 한꺼번에. [(코드, 명령, 결과, 상태)]"""
    res = []
    for line in (text or '').splitlines():
        if re.search(r'(보낸 사람|From:|Sent:|원본 메일|아침 한 장|KM 도구)', line):
            continue
        p = parse_line(line)
        if not p:
            continue
        code, cmd, val, said = p
        out, st = apply_one(route, code, cmd, val, said)
        res.append((code, cmd, out, st))
    return res

# ---------------- 메일함에서 읽기 ----------------

def conf():
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        c.read(INI, encoding='utf-8')
    if not c.has_section('메일'):
        c.add_section('메일')
    return c

def _dec(s):
    try:
        return ''.join((x.decode(enc or 'utf-8', 'replace') if isinstance(x, bytes) else x) for x, enc in decode_header(s or ''))
    except Exception:
        return s or ''

def _body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', 'replace')
                except Exception:
                    continue
        return ''
    try:
        return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', 'replace')
    except Exception:
        return ''

def fetch_mail(quiet=True):
    """받는 메일함에서 안 읽은 「KM 아침 한 장」 회신을 가져온다. [(제목, 본문)]"""
    c = conf()
    g = lambda k, d='': c.get('메일', k, fallback=d)
    host = g('imap') or (g('smtp') or 'smtp.gmail.com').replace('smtp.', 'imap.')
    user, pw = g('user'), g('password')
    if not user or not pw:
        if not quiet:
            print('메일 설정이 없습니다 (35번 → 1 설정).')
        return []
    out = []
    try:
        M = imaplib.IMAP4_SSL(host, int(g('imap_port') or 993))
        M.login(user, pw)
        M.select('INBOX')
        typ, data = M.search(None, '(UNSEEN)')
        for num in (data[0].split() if data and data[0] else []):
            typ, d = M.fetch(num, '(RFC822)')
            if not d or not d[0]:
                continue
            msg = email.message_from_bytes(d[0][1])
            subj = _dec(msg.get('Subject'))
            if 'KM' not in subj and '아침 한 장' not in subj and '회신' not in subj:
                continue
            out.append((subj, _body(msg)))
            M.store(num, '+FLAGS', '\\Seen')
        M.logout()
    except Exception as e:
        if not quiet:
            print('[메일함 읽기 실패] %s' % e)
        log(TOOL, '메일함 실패 %s' % str(e)[:60])
    return out

def fetch_file():
    """받는함\\회신.txt (메일이 막혔을 때). 읽고 나면 처리済 폴더로 옮긴다"""
    try:
        import t40_meeting as M
        d = M.inbox_dir()
    except Exception:
        d = os.path.join(cfg('base'), '받는함')
    p = os.path.join(d, INBOX_TXT)
    if not os.path.exists(p):
        return ''
    t = read_text(p)
    try:
        done = os.path.join(d, '_처리됨')
        os.makedirs(done, exist_ok=True)
        os.replace(p, os.path.join(done, '회신_%s.txt' % ymd6()))
    except Exception:
        pass
    return t

def run(quiet=False, auto=False):
    if not quiet:
        title('48. 회신 읽기   (프로님이 고치신 것을 받아 반영. 메일 회신 · 받는함 회신.txt · 대화)')
    res = []
    for subj, body in fetch_mail(quiet=quiet):
        res += apply_text(body, '메일')
    ft = fetch_file()
    if ft:
        res += apply_text(ft, '파일')
    bad = [r for r in res if r[3] != '반영']
    if not quiet:
        if not res:
            print('새 회신이 없습니다.')
            print('  메일에 그대로 회신하시거나, 받는함에 「%s」 로 한 줄씩 적어 두시면 됩니다.' % INBOX_TXT)
            if not common.AUTO and ask('여기서 바로 넣을까요? (y=엔터 / n) > ', 'y').lower().startswith('y'):
                print('한 줄씩 넣으십시오. 빈 줄이면 끝납니다.  예) 3 아니야 1개 층 선납으로')
                lines = []
                while True:
                    s = ask('> ', '').strip()
                    if not s:
                        break
                    lines.append(s)
                res = apply_text('\n'.join(lines), '대화')
                bad = [r for r in res if r[3] != '반영']
        for code, cmd, out, st in res:
            print('  %-8s %-6s %s%s' % ('KM-' + str(code).zfill(3), cmd, out, '' if st == '반영' else '   ← 되묻겠습니다'))
        if res:
            print('')
            print('반영 %d건 / 못 알아들음 %d건' % (len(res) - len(bad), len(bad)))
    if res:
        log(TOOL, '반영 %d · 못알아들음 %d' % (len(res) - len(bad), len(bad)))
        try:
            import t42_morning as MO
            MO.build(quiet=True)
        except Exception:
            pass
    return res

if __name__ == '__main__':
    run(); pause()

# -*- coding: utf-8 -*-
"""49. 산군 관심현장 정리 - 산군(sankun.com)에서 내려받은 관심현장 파일을 넣으면
    ① 이미 아는 현장을 빼고(중복 제거) ② ★최우선/△검토/✕제외 판정을 붙이고
    ③ 「어느 설계사를 찾아가야 하는가」 까지 만들어 냅니다. 토큰 0(로컬 파이썬).

프로님 (2026-09-19) :
  "구글AI 레이더가 매일 0건으로 오는데 나한테 아무 의미가 없다. 지금은 내가 산군을 쓰니까,
   산군에서 조회된 현장을 조사해서 알려 주는 쪽으로 하면 사용량도 안 들지 않겠나."

그래서 이 도구는 클로드도 Gemini 도 부르지 않습니다. 산군이 이미 모아 준 표를 읽어
판정·중복제거·갈 곳만 계산합니다. 조사(발주처·객실수 확인)는 프로님이 산군 화면에서 보시거나,
★ 줄만 골라 클로드에게 「이 현장 조사해 줘」 라고 주시면 됩니다.

쓰는 법
  1) 산군 > 관심현장 > 엑셀 내려받기 (주 1회 최대 300건)
  2) 49번 실행 → 엔터 (다운로드 폴더에서 가장 최근 산군 파일을 스스로 찾습니다)
  3) 결과 : _도구결과\\산군\\산군_새현장_YYMMDD.xlsx / .csv / 한장.html

판정 기준(= km-site-radar 프로님 확정값)은 설정.ini [산군] 에서 고치실 수 있습니다.
  숙박 1500㎡ / 단독 496㎡ / 클럽하우스 1000㎡ / 그 밖 500㎡ , 기준의 2배면 ★
금액·요율은 이 도구가 정하지 않습니다(규칙 19).

대장 : _도구결과\\_대장\\산군_처리.csv  — 한 번 본 현장은 다음 번에 다시 올라오지 않습니다.

끝나면 50번(흔적 찾기 + 산군 전용 메일)으로 이어집니다. 엔터만 치시면 됩니다.
"""
import os
import io
import csv
import re
import glob
import configparser
import datetime

from common import (INI, cfg, title, ask, pause, today, ymd6, outdir,
                    write_csv, write_html, safe_name, won, log, open_file)

TOOL = '산군'

# ---- 판정 기준 (설정.ini [산군] 에서 덮어쓸 수 있습니다) ----
DEFAULT_LIMIT = {
    '숙박': 1500.0,
    '단독': 496.0,
    '클럽하우스': 1000.0,
    '기타': 500.0,
}
STAY_WORDS = ('숙박', '호텔', '리조트', '모텔', '여관', '콘도', '관광', '생활숙박', '펜션')
ROOM_WORDS = ('기숙사', '연수원', '수련원', '생활관', '교육원', '실버', '요양', '산후조리',
              '조리원', '시니어', '레지던스', '게스트하우스', '유스호스텔')
ETC_WORDS = ('클럽하우스', '골프', '운동시설', '컨벤션', '수련')
HOUSE_WORDS = ('단독주택', '전원주택')
SKIP_WORDS = ('공동주택', '아파트', '오피스텔', '근린생활', '공장', '창고', '주차장',
              '판매시설', '업무시설', '교육연구', '종교', '의료시설')

HEAD = ['판정', '왜', '현장명', '소재지', '단계', '허가일', '착공일', '용도', '구분',
        '연면적㎡', '평', '객실추정', '건축설계(갈 곳)', '시공사', '건축주·발주처', '다음 행동']
SEEN_HEAD = ['처음본날', '키', '현장명', '소재지', '판정', '메모']

# 산군 파일의 열 이름이 조금씩 달라도 잡아내기 위한 후보 낱말
COLMAP = [
    ('현장명', ('현장명', '건물명', '사업명', '공사명', '현장')),
    ('소재지', ('소재지', '주소', '대지위치', '위치')),
    ('공종', ('공종',)),
    ('단계', ('단계', '건축단계', '진행단계', '상태')),
    ('허가일', ('허가일', '건축허가', '허가', '승인일', '날짜1')),
    ('착공일', ('착공일', '착공', '실착공', '날짜2')),
    ('건축설계', ('건축설계', '설계사', '설계', '건축사')),
    ('시공사', ('시공사', '시공', '건설사')),
    ('건축주', ('건축주', '발주처', '발주', '사업주', '감리')),
    ('용도', ('주용도', '용도')),
    ('구분', ('허가구분', '구분', '종류')),
    ('연면적', ('연면적', '면적')),
    ('구조', ('구조',)),
]


# ====================== 설정 ======================

def limits():
    c = configparser.ConfigParser()
    out = dict(DEFAULT_LIMIT)
    if os.path.exists(INI):
        try:
            c.read(INI, encoding='utf-8')
            if c.has_section('산군'):
                for k in out:
                    if c.has_option('산군', k):
                        try:
                            out[k] = float(str(c.get('산군', k)).replace(',', '').strip())
                        except Exception:
                            pass
        except Exception:
            pass
    return out


def write_default_ini():
    """[산군] 섹션이 없으면 기준값을 넣어 둔다(프로님이 숫자만 고치시면 됩니다)."""
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        try:
            c.read(INI, encoding='utf-8')
        except Exception:
            pass
    if c.has_section('산군'):
        return False
    c.add_section('산군')
    for k, v in DEFAULT_LIMIT.items():
        c.set('산군', k, str(int(v)))
    c.set('산군', '착공최근개월', '6')
    try:
        with io.open(INI, 'w', encoding='utf-8') as fp:
            c.write(fp)
        return True
    except Exception:
        return False


# ====================== 파일 읽기 ======================

def guess_file():
    """다운로드 폴더 등에서 가장 최근 산군 파일을 찾는다."""
    pats = []
    for d in (os.path.join(os.path.expanduser('~'), 'Downloads'),
              os.path.join(os.path.expanduser('~'), '다운로드'),
              os.path.join(cfg('base'), '산군'),
              os.path.join(cfg('out'), TOOL)):
        if not d or not os.path.isdir(d):
            continue
        for ext in ('xlsx', 'xls', 'csv'):
            pats += glob.glob(os.path.join(d, '*.%s' % ext))
    cand = [p for p in pats if any(k in os.path.basename(p) for k in ('산군', 'sankun', '관심현장', '현장DB'))]
    pool = cand or pats
    pool = [p for p in pool if not os.path.basename(p).startswith('~$')]
    if not pool:
        return ''
    pool.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return pool[0]


def read_table(path):
    """xlsx/csv 를 [[셀,...], ...] 로 읽는다."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xlsm', '.xls'):
        try:
            import openpyxl
        except Exception:
            print('[openpyxl 없음] 엑셀을 읽으려면 openpyxl 이 필요합니다.')
            print('  해결 : 산군 파일을 엑셀에서 열어 「다른 이름으로 저장 > CSV」 로 바꿔 주십시오.')
            return []
        wb = openpyxl.load_workbook(path, data_only=True)
        rows = []
        for ws in wb.worksheets:
            for r in ws.iter_rows(values_only=True):
                rows.append(['' if c is None else str(c).strip() for c in r])
            if rows:
                break
        return rows
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(path, 'r', encoding=enc, newline='') as fp:
                return [[(c or '').strip() for c in r] for r in csv.reader(fp)]
        except Exception:
            continue
    return []


def find_header(rows):
    """현장명·소재지처럼 보이는 낱말이 가장 많은 줄을 머리줄로 본다."""
    best, best_i = 0, -1
    for i, r in enumerate(rows[:30]):
        hit = 0
        for _, words in COLMAP:
            for c in r:
                if c and any(w in c for w in words):
                    hit += 1
                    break
        if hit > best:
            best, best_i = hit, i
    return best_i if best >= 3 else -1


def build_map(header):
    """머리줄 → {필드: 열번호}"""
    m = {}
    for key, words in COLMAP:
        for j, c in enumerate(header):
            if not c or j in m.values():
                continue
            if any(w in c for w in words):
                m[key] = j
                break
    return m


# ====================== 판정 ======================

def to_f(s):
    try:
        return float(re.sub(r'[^0-9.]', '', str(s or '')) or 0)
    except Exception:
        return 0.0


def to_date(s):
    s = re.sub(r'[^0-9]', '', str(s or ''))
    if len(s) == 8:
        try:
            return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        except Exception:
            return None
    return None


def kind_of(text):
    """용도·현장명을 보고 어느 기준을 쓸지 고른다."""
    if any(w in text for w in STAY_WORDS):
        return '숙박'
    if any(w in text for w in ROOM_WORDS):
        return '숙박'          # 객실이 있는 건물이라 숙박 기준을 쓴다
    if any(w in text for w in ETC_WORDS):
        return '클럽하우스'
    if any(w in text for w in HOUSE_WORDS):
        return '단독'
    return ''


def grade(rec, lim, months):
    """★최우선 / △검토 / ✕제외 + 왜 그렇게 봤는지.

    프로님이 손으로 만드신 「산군_관심현장 v1 (2026-09-14, 11건)」 의 판정과 맞춰 놓았습니다.
      ★ = 기준의 2배 이상(대형) 이면서 지금 들어갈 때(착공 n개월 이내 또는 착공 전)
      △ = 기준은 넘지만 대형이 아니거나, 착공한 지 오래돼 표류 여부를 봐야 하는 것
      ✕ = 객실 용도가 아니거나 규모 미달, 허가 3년 넘도록 착공 기록 없음
    """
    text = '%s %s' % (rec.get('현장명', ''), rec.get('용도', ''))
    kind = kind_of(text)
    if not kind:
        if any(w in text for w in SKIP_WORDS):
            return '✕제외', '객실이 없는 용도(%s)' % (rec.get('용도') or '용도 미표시')
        return '✕제외', '객실 용도로 안 보임(%s)' % (rec.get('용도') or '용도 미표시')

    area = to_f(rec.get('연면적'))
    need = lim.get(kind, lim['기타'])
    if area and area < need:
        return '✕제외', '%s 기준 %s㎡ 미만 (%s㎡)' % (kind, won(need), won(area))

    big = bool(area) and area >= need * 2
    why = ['%s㎡%s' % (won(area), ' 대형' if big else '')] if area else ['연면적 미표시 - 확인 필요']

    t0 = today()
    d_start = to_date(rec.get('착공일'))
    d_perm = to_date(rec.get('허가일'))
    timely = False
    if d_start:
        gap = (t0 - d_start).days
        if gap <= months * 31:
            timely = True
            why.append('착공 %s (골조 단계 - 지금이 외함 협의 때)' % d_start.isoformat())
        else:
            why.append('착공 %s (%d개월 지남 - 이미 끝났는지 확인)' % (d_start.isoformat(), gap // 30))
    elif d_perm:
        gap = (t0 - d_perm).days
        if gap > 365 * 3:
            return '✕제외', '허가 %s · 3년 넘도록 착공 기록 없음' % d_perm.isoformat()
        if gap <= months * 31:
            timely = True
            why.append('허가 %s · 착공 전 (설계 단계 - 가장 좋은 때)' % d_perm.isoformat())
        else:
            why.append('허가 %s · 착공 기록 없음 (표류 여부 확인)' % d_perm.isoformat())
    else:
        why.append('허가일·착공일 미표시 - 산군 상세에서 확인')

    gubun = str(rec.get('구분') or '')
    if gubun and '신축' not in gubun:
        why.append('%s - 리모델링이면 교체 기회' % gubun)

    if big and timely:
        return '★최우선', ' / '.join(why)
    return '△검토', ' / '.join(why)


def rooms(rec):
    """연면적으로 객실 수를 어림잡는다(1실 40~60㎡, 공용 포함)."""
    a = to_f(rec.get('연면적'))
    if a < 200:
        return ''
    return '약 %s~%s실' % (won(a / 60.0), won(a / 40.0))


def next_step(rec, g):
    if g == '✕제외':
        return ''
    designer = (rec.get('건축설계') or '').strip()
    if designer:
        return '%s 에 객실관리 설계 협의 요청 (시방서·심볼 전달)' % designer
    sido = (rec.get('소재지') or '').split(' ')
    where = ' '.join(sido[:2]) if len(sido) >= 2 else (rec.get('소재지') or '')
    return '설계사 미표시 - 산군 상세 또는 %s 건축과에 설계자 확인' % where


# ====================== 이미 본 현장 ======================

def seen_path():
    p = os.path.join(cfg('out'), '_대장')
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, '산군_처리.csv')


def key_of(rec):
    s = '%s|%s' % (rec.get('현장명', ''), rec.get('소재지', ''))
    s = re.sub(r'[\s\-()·,]', '', s)
    return s[:120]


def load_seen():
    p = seen_path()
    if not os.path.exists(p):
        return {}
    for enc in ('cp949', 'utf-8-sig', 'utf-8'):
        try:
            with io.open(p, 'r', encoding=enc, newline='') as fp:
                rows = list(csv.reader(fp))
            break
        except Exception:
            rows = []
    out = {}
    for r in rows[1:]:
        if len(r) >= 2 and r[1]:
            out[r[1]] = r
    return out


def save_seen(seen, new_rows):
    body = [seen[k] for k in seen] + new_rows
    write_csv(seen_path(), body, SEEN_HEAD)


# ====================== 산출물 ======================

def build_xlsx(path, body):
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
    except Exception:
        return ''
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '1.새 현장'
    ws.append(HEAD)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='2A6099')
    for r in body:
        ws.append(r)
    widths = [9, 40, 26, 30, 9, 11, 11, 12, 9, 10, 8, 12, 20, 16, 16, 38]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(vertical='top', wrap_text=(c.column in (2, 16)))
        if str(row[0].value or '').startswith('★'):
            for c in row:
                c.fill = PatternFill('solid', fgColor='FDE8E6')
    ws.freeze_panes = 'A2'
    wb.save(path)
    return path


def esc(s):
    return (str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def line_of(r):
    return ('<b>%s</b> (%s)<br>%s · %s㎡ · %s<br>설계 : <b>%s</b> · 시공 : %s<br>'
            '<span style="color:#555">%s</span><br>→ %s'
            % (esc(r[2]), esc(r[3]), esc(r[4] or '단계 미표시'), esc(r[9] or '?'),
               esc(r[11] or '객실수 미상'), esc(r[12] or '설계사 미표시'), esc(r[13] or '미표시'),
               esc(r[1]), esc(r[15])))


def build_html(path, body, src, skipped, dup, files=()):
    stars = [r for r in body if r[0].startswith('★')]
    revs = [r for r in body if r[0].startswith('△')]
    blocks = [
        ('이번 산군 파일', [
            ('blue', '파일 : %s' % esc(os.path.basename(src))),
            ('green' if body else 'gray',
             '새 현장 <b>%d</b>건 (★최우선 %d · △검토 %d)' % (len(body), len(stars), len(revs))),
            ('gray', '이미 본 현장 %d건 · 객실 아닌 용도 %d건 은 뺐습니다.' % (dup, skipped)),
        ]),
        ('★ 최우선 — 이번 주에 연락할 곳 (%d건)' % len(stars), [('red', line_of(r)) for r in stars]),
        ('△ 검토 (%d건)' % len(revs), [('yellow', line_of(r)) for r in revs]),
        ('이 한 장에 없는 것', [
            ('gray', '발주처·객실수 조사는 이 도구가 하지 않습니다. ★ 줄만 클로드에게 주시면 조사합니다.'),
            ('gray', '판정 기준(숙박 1500㎡ 등)은 설정.ini [산군] 에서 고치실 수 있습니다.'),
        ]),
    ]
    return write_html(path, '산군 새 현장 %s' % today().isoformat(), blocks, files=files)


# ====================== 본체 ======================

def parse(path):
    rows = read_table(path)
    if not rows:
        return [], '파일을 읽지 못했습니다'
    hi = find_header(rows)
    if hi < 0:
        return [], '머리줄(현장명·소재지…)을 못 찾았습니다'
    cmap = build_map(rows[hi])
    if '현장명' not in cmap:
        return [], '「현장명」 열을 못 찾았습니다'
    out = []
    for r in rows[hi + 1:]:
        if not any((c or '').strip() for c in r):
            continue
        rec = {}
        for k, j in cmap.items():
            rec[k] = r[j].strip() if j < len(r) else ''
        if not rec.get('현장명'):
            continue
        out.append(rec)
    return out, ''


def run():
    title('49. 산군 관심현장 정리 (토큰 0)')
    if write_default_ini():
        print('설정.ini 에 [산군] 기준값을 넣어 두었습니다 — 숫자는 프로님이 고치시면 됩니다.')

    auto = guess_file()
    p = ask('산군 파일 경로 [%s] > ' % (os.path.basename(auto) if auto else '없음'), auto)
    if not p or not os.path.exists(p):
        print('[없음] 산군에서 관심현장을 내려받아 다운로드 폴더에 두신 뒤 다시 실행해 주십시오.')
        print('       산군 > 관심현장 > 엑셀 내려받기 (주 1회 최대 300건)')
        return

    recs, err = parse(p)
    if err:
        print('[읽기 실패] %s' % err)
        print('  파일 : %s' % p)
        print('  엑셀에서 열어 첫 줄이 머리줄인지 보시고, 안 되면 CSV 로 저장해 주십시오.')
        return
    print('받은 줄 : %s' % won(len(recs)))

    lim = limits()
    months = 6
    c = configparser.ConfigParser()
    if os.path.exists(INI):
        try:
            c.read(INI, encoding='utf-8')
            if c.has_option('산군', '착공최근개월'):
                months = int(to_f(c.get('산군', '착공최근개월')) or 6)
        except Exception:
            pass

    seen = load_seen()
    body, new_seen = [], []
    dup = skipped = 0
    for rec in recs:
        k = key_of(rec)
        if k in seen:
            dup += 1
            continue
        g, why = grade(rec, lim, months)
        row = [g, why, rec.get('현장명', ''), rec.get('소재지', ''), rec.get('단계', ''),
               rec.get('허가일', ''), rec.get('착공일', ''), rec.get('용도', ''), rec.get('구분', ''),
               won(to_f(rec.get('연면적'))) if to_f(rec.get('연면적')) else '',
               won(to_f(rec.get('연면적')) / 3.3058) if to_f(rec.get('연면적')) else '',
               rooms(rec), rec.get('건축설계', ''), rec.get('시공사', ''), rec.get('건축주', ''),
               next_step(rec, g)]
        # 대장은 엑셀(cp949)에서도 열리게 ✕ 대신 X 로 적는다
        new_seen.append([today().isoformat(), k, rec.get('현장명', ''), rec.get('소재지', ''),
                         g.replace('✕', 'X'), ''])
        if g == '✕제외':
            skipped += 1
            continue
        body.append(row)

    order = {'★최우선': 0, '△검토': 1}
    body.sort(key=lambda r: (order.get(r[0], 2), r[12] or 'ㅎ'))

    od = outdir(TOOL)
    cp = write_csv(os.path.join(od, '산군_새현장_%s.csv' % ymd6()), body, HEAD)
    xp = build_xlsx(os.path.join(od, '산군_새현장_%s.xlsx' % ymd6()), body)
    hp = build_html(os.path.join(od, '산군_새현장_%s.html' % ymd6()), body, p, skipped, dup,
                    files=[f for f in (xp, cp) if f])
    save_seen(seen, new_seen)

    stars = sum(1 for r in body if r[0].startswith('★'))
    print('')
    print('새 현장 %s건 (★최우선 %s · △검토 %s)' % (won(len(body)), won(stars), won(len(body) - stars)))
    print('이미 본 것 %s건 · 객실 아님 %s건 은 뺐습니다.' % (won(dup), won(skipped)))
    print('')
    for r in body[:15]:
        print('  [%s] %-22s %-14s %s' % (r[0], r[2][:22], (r[12] or '설계사 미표시')[:14], r[1][:40]))
    if len(body) > 15:
        print('  ... 그 밖 %s건은 파일에 있습니다.' % won(len(body) - 15))
    print('')
    print('엑셀 : %s' % (xp or cp))
    print('한 장 : %s' % hp)
    print('* 발주처·객실수 조사는 이 도구가 하지 않습니다. ★ 줄만 클로드에게 주시면 조사합니다.')
    log(TOOL, '%s건 중 새 %s건(★%s)' % (len(recs), len(body), stars))
    try:
        open_file(hp)
    except Exception:
        pass

    # 이어서 50번(흔적 찾기 + 산군 전용 메일) — 엔터만 치시면 됩니다
    if body:
        go = (ask('\n이어서 인터넷에서 흔적을 찾아 메일로 보낼까요? (엔터=예) > ', '예') or '예').strip()
        if go not in ('아니오', '아니요', 'n', 'N'):
            try:
                import t50_sangun_trace as TR
                TR.run(src=cp)
            except Exception as e:
                print('[50번 실행 실패] %s' % e)
                print('  50번을 따로 실행하셔도 됩니다.')


if __name__ == '__main__':
    run()
    pause()

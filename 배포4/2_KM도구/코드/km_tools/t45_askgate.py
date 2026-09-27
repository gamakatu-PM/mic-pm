# -*- coding: utf-8 -*-
"""45. 요청 분기 · 보낼 메일 - 「견적 주세요」 「제안서 주세요」 가 왔을 때
도구가 도면 유무로 할 일을 정하고, 못 하는 경우에는 **보낼 메일 본문까지** 써 준다. 토큰 0.

  · 도면 있음 -> 「견적 만들 수 있음」 : 32번(현장 한 방에) 한 줄로 수량->실행->견적까지
  · 도면 없음 -> 「도면 필요」 : 도면 요청 메일 제목+본문을 만들어 둔다 (프로님은 복사·붙여넣기만)
  · 제안서 요청이 회의록에 있으면 : 필요한 자료·장수·구성을 먼저 물어보는 메일을 같이 만든다

금액·수량·요율은 도구가 정하지 않는다 -> 본문에 `[  ]` 빈칸으로 남긴다 (프로님이 채우신다).
산출 : _도구결과\\요청분기\\{YYMMDD}\\_요청분기.html + 보낼메일_*.txt + 보낼메일_모음.txt
"""
import os, io, glob
import common
from common import *
import facts

TOOL = '요청분기'
DWG_EXT = {'.dxf', '.dwg', '.pdf'}
SIGN = ('한국마이크로닉(주)  배성윤 차장\n'
        '객실관리시스템(RCU/BSP/CB 제어분전함) 설계·시공\n'
        '전화 [        ]   메일 [        ]')

def _sites():
    """[(현장, 폴더)] - 도면 폴더 기준(연도 폴더 포함), 없으면 현장대장"""
    out = []
    try:
        import t31_intake as IN
        for name, d in IN.sites():        # [(현장명, 폴더)] - 연도 폴더 안까지, 같은 현장은 최신 연도만
            out.append((name, d))
    except Exception:
        pass
    have = {n for n, _ in out}
    try:
        import sitebook
        for d in sitebook.load():
            if d['site'] not in have:
                out.append((d['site'], None))
    except Exception:
        pass
    return out

def _book(site):
    try:
        import sitebook
        for d in sitebook.load():
            if d['site'] == site:
                return d
    except Exception:
        pass
    return {}

def _val(site, item, book_key=None, book=None):
    """확정 대장이 먼저, 없으면 현장대장, 둘 다 없으면 '' (도구가 짐작하지 않는다)"""
    d = facts.get(site, item)
    if d and d['값']:
        return d['값']
    if book and book_key:
        return book.get(book_key, '')
    return ''

def _drawings(site, site_dir):
    if not site_dir or not os.path.isdir(site_dir):
        return []
    try:
        import t31_intake as IN
        return list(IN.drawing_files(site_dir))
    except Exception:
        return [p for p in glob.glob(os.path.join(site_dir, '*'))
                if os.path.splitext(p)[1].lower() in DWG_EXT]

def _qty_sheet(site):
    """프로님이 주신 수량표가 어딘가 있는지 (있으면 견적을 바로 만들 수 있다)"""
    pat = os.path.join(cfg('out'), '**', '*수량표*')
    for p in glob.glob(pat, recursive=True):
        if safe_name(site)[:6] in safe_name(os.path.basename(p)):
            return p
    return None

def _prop_asks(days=14):
    """회의록에서 제안서·자료 요청이 나온 현장 {현장: [줄]}"""
    out = {}
    try:
        import t15_proposal as PR
        for site, kind, line, _p in PR.scan(days=days):
            out.setdefault(site, []).append('%s : %s' % (kind, line))
    except Exception:
        pass
    return out

def gate(site, site_dir):
    book = _book(site)
    dwg = _drawings(site, site_dir)
    rooms = _val(site, '객실수', 'rooms', book)
    return {
        'site': site, 'dir': site_dir, 'dwg': dwg, 'rooms': rooms,
        'pic': _val(site, '담당자', 'pic', book),
        'owner': _val(site, '발주처', 'owner', book),
        'builder': _val(site, '시공사', 'builder', book),
        'due': _val(site, '준공일', 'due', book),
        'star': book.get('star', ''),
        'floors': book.get('floors', ''),
        'qty': _qty_sheet(site),
        'state': '견적가능' if dwg else '도면필요',
    }

# ---------------- 보낼 메일 본문 ----------------

def mail_drawing(g):
    """도면 요청 메일 - km-34 19번 규칙의 필수 항목을 모두 넣는다"""
    site = g['site']
    rooms = g['rooms'] or '[객실수 확인 필요]'
    pic = g['pic'] or '[담당자]'
    sub = '[%s] 객실관리 견적을 위한 도면 요청 (한국마이크로닉)' % site
    b = []
    b.append('%s님 안녕하십니까. 한국마이크로닉(주) 배성윤입니다.' % pic)
    b.append('')
    b.append('%s 객실관리 시스템 견적을 요청해 주셔서 감사합니다.' % site)
    b.append('견적 금액은 객실 타입별 기구물 수량에서 나오는데, 현재 저희가 받은 도면이 없어')
    b.append('수량을 확정할 수 없습니다. 아래 자료를 주시면 바로 뽑아 드리겠습니다.')
    b.append('')
    b.append('■ 주셔야 하는 도면 (캐드 + PDF 둘 다)')
    b.append('  1) 객실 평면도 - 룸타입별 1장씩 (타입이 많으면 대표 타입 전부)')
    b.append('  2) 객실 천장도 - 조명 배치가 보이는 것')
    b.append('  3) 전기 계통도 - 전등 스위치 구수(1~6구)가 확정된 것')
    b.append('  4) 객실관리(약전) 계통도 - 있으시면. 없으면 저희가 그려 회신드립니다.')
    b.append('')
    b.append('■ 같이 알려 주시면 좋은 것')
    b.append('  · 객실 수 : %s 실   · 층수 : %s' % (rooms, g.get('floors') or '[    ]'))
    b.append('  · 성급 : %s 성급 (온도조절기·USB·유니버셜 콘센트 적용 범위가 달라집니다)' % (g['star'] or '[  ]'))
    b.append('  · 준공 예정일 : %s' % (g['due'] or '[          ]'))
    b.append('  · 베란다 유무 / 거실 유무 / 책상 유무 (스위치 구성이 달라집니다)')
    b.append('')
    b.append('■ 도면이 아직 안 나왔다면')
    b.append('  룸타입별 평면 1장이라도 먼저 주시면 타입 기준으로 개략 견적을 드리고,')
    b.append('  최종 도면이 나온 뒤 정식 견적으로 갱신해 드리겠습니다.')
    b.append('')
    b.append('■ 받으면 언제까지 드리는지')
    b.append('  도면 받은 날부터 객실 수량표 [   ]일, 견적서 [   ]일 안에 드리겠습니다.')
    b.append('')
    b.append('필요한 날짜가 정해져 있으시면 알려 주십시오. 그 날짜에 맞춰 순서를 조정하겠습니다.')
    b.append('')
    b.append(SIGN)
    return sub, '\n'.join(b)

def mail_proposal(g, asks):
    site = g['site']
    pic = g['pic'] or '[담당자]'
    sub = '[%s] 객실관리 제안서 준비 - 필요한 자료와 구성 확인 (한국마이크로닉)' % site
    b = []
    b.append('%s님 안녕하십니까. 한국마이크로닉(주) 배성윤입니다.' % pic)
    b.append('')
    b.append('%s 제안서를 준비하겠습니다. 헛일이 되지 않도록 구성을 먼저 확인드립니다.' % site)
    b.append('')
    b.append('■ 제안서 구성 (7장 안. 더 필요하시면 늘리겠습니다)')
    b.append('  1장 표지 / 2장 현장 개요와 적용 범위 / 3장 객실 타입별 기구물 구성(평면에 표기)')
    b.append('  4장 시스템 계통도(RCU·BSP·CB 제어분전함) / 5장 타사 대비 차이 / 6장 공사 한계와 일정')
    b.append('  7장 납품 실적 (유사 규모 호텔)')
    b.append('')
    b.append('■ 주셔야 제안서가 나옵니다')
    b.append('  · 객실 평면도(룸타입별) · 전기 계통도 · 객실 수 · 성급 · 준공 예정일')
    b.append('  · 제안서 제출 기한과 받는 분(발주처 / 설계사 / 시공사 중 어디로 가는지)')
    b.append('  · 비교 대상이 있으면 그 회사명 (같은 기준으로 비교표를 만들겠습니다)')
    if asks:
        b.append('')
        b.append('■ 회의에서 나온 요청 (이대로 반영하겠습니다)')
        for a in asks[:8]:
            b.append('  - %s' % a)
    b.append('')
    b.append('자료 받은 날부터 [   ]일 안에 초안을 드리고, 한 번 보신 뒤 수정본을 드리겠습니다.')
    b.append('')
    b.append(SIGN)
    return sub, '\n'.join(b)

def plan(g):
    """도면이 있을 때 프로님이 누를 것 한 줄"""
    if g['qty']:
        return '수량표도 있습니다 -> 28번(단가 붙이기) -> 18번(견적서 채우기). 32번 한 방에도 됩니다.'
    return '32번 「현장 한 방에」 하나로 27 수량 -> 28 단가 -> 29 단가장 -> 30 부탁서까지 돕니다. 수량은 확정 전 「검토용」 입니다.'

def gate_all():
    """현장 전부의 분기 상태 (파일은 만들지 않는다 - 42 아침 한 장이 읽는다)"""
    return [gate(s, d) for s, d in _sites()]

def mail_path(site, kind='도면요청'):
    """이미 만들어 둔 보낼 메일 파일 (최신 날짜 폴더). 없으면 None"""
    pat = os.path.join(cfg('out'), safe_name(TOOL), '*', '보낼메일_%s_%s.txt' % (kind, safe_name(site, 30)))
    got = sorted(glob.glob(pat))
    return got[-1] if got else None

# ---------------- 실행 ----------------

def run(quiet=False, argv=None):
    if not quiet:
        title('45. 요청 분기 · 보낼 메일   (견적/제안 요청이 왔을 때 무엇을 할지 + 메일 본문. 토큰 0)')
    od = outdir(TOOL)
    asks = _prop_asks()
    gs = [gate(s, d) for s, d in _sites()]
    made, can, need_dwg, prop = [], [], [], []
    allmail = []
    for g in gs:
        site = g['site']
        a = asks.get(site) or []
        if g['state'] == '견적가능':
            can.append('<b>%s</b> · 도면 %d개 · %s' % (site, len(g['dwg']), plan(g)))
        else:
            sub, body = mail_drawing(g)
            p = os.path.join(od, '보낼메일_도면요청_%s.txt' % safe_name(site, 30))
            io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n').write(
                '제목 : %s\n\n%s\n' % (sub, body))
            made.append(p)
            allmail.append((sub, body))
            need_dwg.append('<b>%s</b> · 도면 0개 → 도면 요청 메일을 만들어 두었습니다 '
                            '(객실수 %s · 담당 %s)' % (site, g['rooms'] or '미확인', g['pic'] or '미확인'))
        if a:
            sub, body = mail_proposal(g, a)
            p = os.path.join(od, '보낼메일_제안서자료_%s.txt' % safe_name(site, 30))
            io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n').write(
                '제목 : %s\n\n%s\n' % (sub, body))
            made.append(p)
            allmail.append((sub, body))
            prop.append('<b>%s</b> · 회의에서 자료·제안 요청 %d건 → 구성 확인 메일을 만들어 두었습니다'
                        % (site, len(a)))
    if allmail:
        p = os.path.join(od, '보낼메일_모음.txt')
        buf = []
        for i, (sub, body) in enumerate(allmail, 1):
            buf.append('=' * 60)
            buf.append('%d. %s' % (i, sub))
            buf.append('=' * 60)
            buf.append(body)
            buf.append('')
        io.open(p, 'w', encoding='cp949', errors='replace', newline='\r\n').write('\n'.join(buf))
        made.insert(0, p)
    blocks = [
        ('지금 할 것', [('red', x) for x in need_dwg] + [('yellow', x) for x in prop]
         or [('green', '도면이 없어 막힌 현장이 없습니다.')]),
        ('견적 만들 수 있음 (도면 있음)', [('green', x) for x in can]),
        ('도면이 없어 견적을 못 만드는 현장', [('red', x) for x in need_dwg]),
        ('제안서·자료 요청이 나온 현장', [('yellow', x) for x in prop]),
        ('규칙', [('gray', '금액·수량·요율은 도구가 정하지 않습니다. 메일 본문의 <b>[   ]</b> 칸만 채워서 보내십시오.'),
                ('gray', '대외로 나가는 메일에는 내부 사정(원가·타사 단가·내부 비판)을 넣지 않았습니다.'),
                ('gray', '담당자·객실수가 「미확인」 이면 43번으로 확정해 두시면 다음부터 메일에 저절로 들어갑니다.')]),
    ]
    hp = os.path.join(od, '_요청분기.html')
    write_html(hp, '45. 요청 분기 · 보낼 메일', blocks, files=made)
    log(TOOL, '견적가능 %d · 도면필요 %d · 제안 %d' % (len(can), len(need_dwg), len(prop)))
    if not quiet:
        print('')
        print('견적 만들 수 있음 %d곳 / 도면 필요 %d곳 / 제안·자료 요청 %d곳' % (len(can), len(need_dwg), len(prop)))
        for x in need_dwg:
            print('  · ' + x.replace('<b>', '').replace('</b>', ''))
        print('')
        print('메일 본문 : %s' % od)
        if not common.AUTO:
            open_file(hp)
    return {'html': hp, 'files': made, 'can': can, 'need': need_dwg, 'prop': prop, 'gates': gs}

if __name__ == '__main__':
    run(); pause()

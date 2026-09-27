# -*- coding: utf-8 -*-
# 54판 v8 2026-09-27  (★제안서_PPT.py 가 이 줄의 v숫자로 새 판인지 가린다)
"""site_index - 흩어진 결과를 「현장 하나당 한 곳」 으로 모아 보는 화면을 만든다. 토큰 0.

왜 만들었나
  프로님 2026-09-17 : "폴더가 여기 저기 흩어져 있는 것은 결과값 찾기가 힘드니
  생성된 폴더는 몰아서 하나의 폴더에서 볼 수 있게 해. 산출, 견적, 실행, 회의록, 제안서, 단가장."

무엇을 하지 않는가
  ★ 파일을 옮기지 않는다. 폴더도 만들지 않는다. 이름도 바꾸지 않는다.
  폴더는 프로님이 정하고 도구가 따라간다(km-00 10번). 그래서 「보는 화면」 만 더한다.
  원본은 _도구결과\\{도구}\\{날짜}\\ 그대로 있고, 이 화면이 현장별로 묶어 링크만 건다.

만드는 것
  {base}\\_현장별_한곳에.html   더블클릭 -> 현장 카드. 파일을 누르면 그대로 열린다

쓰는 법
  단독 : python site_index.py
  33번에 합치기 : t33_dashboard.py 안에서
        import site_index
        site_index.build()          # 현황판을 만들 때 같이 부른다
"""
import os, io, re, glob, html, datetime, collections

try:
    from common import cfg, outdir, today, ymd6, log
except Exception:                      # 단독 실행 대비
    def cfg(k):
        d = {'base': r'C:\Users\gamak\OneDrive\26년도 현장\!!클로드가 저장하는 폴더'}
        d['out'] = os.path.join(d['base'], '_도구결과')
        return d.get(k, '')
    def today():
        return datetime.date.today()
    def log(*a):
        pass

# 도구 폴더 이름 -> 프로님이 부르시는 이름 (없으면 폴더 이름 그대로)
KIND = collections.OrderedDict([
    ('도면수량', '산출'), ('객실수량표', '산출'), ('CB외함세트', '산출'),
    ('견적서채우기', '견적'), ('증감비교', '견적'), ('단가붙이기', '실행'),
    ('단가장채우기', '단가장'), ('단가장검진', '단가장'),
    ('회의록', '회의록'), ('부서메일', '회의록'),
    ('제안서초안', '제안서'), ('제안서PPT', '제안서'), ('자재사양서', '제안서'),
    ('시방서치환', '제안서'), ('사진대지', '사진'), ('이미지PPT', '사진'),
    ('납기역산', '일정'), ('수금레이더', '돈'), ('월말집계', '돈'),
    ('의뢰서대장', '의뢰서'), ('완성품', '부탁서'), ('도면접수', '도면'),
])
ORDER = ['산출', '견적', '실행', '단가장', '제안서', '회의록', '의뢰서',
         '일정', '돈', '도면', '사진', '부탁서', '그 밖']

BAD = ('_클로드에게', '_모르는기호', '_읽은파일', '_쪼개서맞춘것', 'log', '.tmp', '~$')


def kind_of(tool):
    for k, v in KIND.items():
        if k in tool:
            return v
    return '그 밖'


# 도구가 파일 이름 앞에 붙이는 말 - 현장명이 아니다 (2026-09-27 미리보기에서 현장으로 잡혀 나옴)
NOT_SITE = ('메일', '보낼메일', '자가시험', '미확인회의록', '회의변경수량', '현황판', '아침한장',
            '총괄점검', '회의록정리', '오늘할것', '답해주십시오', '어제있었던일', '할일추가',
            '현장별', '발송로그', '아침대장', '소통이력', '확정', '앞으로할것', '찾아갈곳')
GENERIC = '표준 (현장명 없는 범용본)'


def site_of(fname, tool):
    """파일 이름 앞머리에서 현장명을 뽑는다. 못 뽑으면 빈 값."""
    base = os.path.splitext(fname)[0]
    base = re.sub(r'_?\d{6}(_r\d+)?$', '', base)          # 뒤 날짜·판 제거
    site = ''
    for tag in ('_도면수량', '_수량표', '_실행산출', '_견적서', '_제안서', '_증감',
                '_사진대지', '_자재사양서', '_역산', '_초안'):
        if tag in base:
            site = base.split(tag)[0].strip(' _-')
            break
    if not site:
        parts = base.split('_')
        if len(parts) >= 2 and len(parts[0]) >= 2:
            site = parts[0].strip(' _-')
    site = re.sub(r'[_ ]*\d{6}$', '', site).strip(' _-')     # 「앵커호텔_260927」 -> 「앵커호텔」
    if site in NOT_SITE:
        return ''
    if site == '표준':
        return GENERIC
    return site


def _known_sites():
    """도면 폴더의 현장 이름 (있으면). 이름 뒤쪽에 현장명이 붙은 파일을 찾는 데 쓴다."""
    out = set()
    try:
        root = cfg('drawing')
    except Exception:
        return out
    for base in [root] + [os.path.join(root, d) for d in (os.listdir(root) if os.path.isdir(root) else [])
                          if re.match(r'^\d{2,4}년?$', d)]:
        if not os.path.isdir(base):
            continue
        for d in os.listdir(base):
            if os.path.isdir(os.path.join(base, d)) and not d.startswith(('_', '~')) \
                    and not re.match(r'^\d{2,4}년?$', d):
                out.add(d)
    return out


def scan():
    """_도구결과 아래를 훑어 {현장: {종류: [(파일명, 경로, 날짜)]}} 로 모은다."""
    root = cfg('out')
    found = collections.defaultdict(lambda: collections.defaultdict(list))
    loose = collections.defaultdict(list)
    pending = []
    if not root or not os.path.isdir(root):
        return found, loose, root
    for tool in sorted(os.listdir(root)):
        tdir = os.path.join(root, tool)
        if not os.path.isdir(tdir) or tool.startswith('_'):
            continue
        kind = kind_of(tool)
        for p in glob.glob(os.path.join(tdir, '*', '*')):
            fn = os.path.basename(p)
            if os.path.isdir(p) or any(b in fn for b in BAD):
                continue
            try:
                mt = datetime.date.fromtimestamp(os.path.getmtime(p))
            except Exception:
                mt = None
            site = site_of(fn, tool)
            rec = (fn, p, mt, tool)
            if site:
                found[site][kind].append(rec)
            else:
                pending.append((kind, rec))
    # 현장명이 앞에 없는 파일 (보낼메일_도면요청_연합기숙사.txt 등) - 아는 현장 이름이 들어 있으면 그 현장으로
    known = set(k for k in found if k != GENERIC) | _known_sites()
    for kind, rec in pending:
        hit = [k for k in known if k and k in rec[0]]
        if len(hit) == 1:
            found[hit[0]][kind].append(rec)
        else:
            loose[kind].append(rec)
    for site in found:
        for kind in found[site]:
            found[site][kind].sort(key=lambda r: (r[2] or datetime.date(1900, 1, 1)), reverse=True)
    return found, loose, root


def _esc(s):
    return html.escape(str(s))


def _url(p):
    return 'file:///' + p.replace('\\', '/').replace(' ', '%20')


CSS = """
:root{--bg:#F2F4F7;--card:#fff;--ink:#18212E;--ink2:#43505F;--muted:#77838F;
 --line:#DCE1E8;--navy:#1F3864;--blue:#2E74B5;--sky:#E7EEF7;--warn:#C77B2B}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-size:14px;line-height:1.55;
 font-family:"맑은 고딕","Malgun Gothic",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px}
h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.tools input{flex:1 1 260px;padding:9px 12px;border:1px solid var(--line);border-radius:4px;font-size:14px}
.site{background:var(--card);border:1px solid var(--line);border-radius:5px;margin-bottom:12px;overflow:hidden}
.site>summary{cursor:pointer;padding:12px 16px;font-weight:700;font-size:15px;
 display:flex;gap:10px;align-items:center;list-style:none;background:var(--card)}
.site>summary::-webkit-details-marker{display:none}
.site[open]>summary{border-bottom:1px solid var(--line);background:var(--sky)}
.cnt{margin-left:auto;font-weight:400;font-size:12px;color:var(--muted)}
.body{padding:6px 16px 14px}
.kind{margin-top:10px}
.kind h3{font-size:12px;letter-spacing:.06em;color:var(--navy);margin:0 0 5px;
 border-left:3px solid var(--blue);padding-left:7px}
.f{display:flex;gap:10px;padding:5px 0 5px 10px;border-bottom:1px dotted var(--line);font-size:13px}
.f:last-child{border-bottom:0}
.f a{color:var(--ink2);text-decoration:none;flex:1;word-break:break-all}
.f a:hover{color:var(--blue);text-decoration:underline}
.f .d{color:var(--muted);font-size:12px;white-space:nowrap;font-variant-numeric:tabular-nums}
.f .t{color:var(--muted);font-size:11px;white-space:nowrap}
.note{background:#FAF0E2;border:1px solid var(--warn);border-radius:5px;padding:12px 15px;
 font-size:13px;color:var(--ink2);margin-top:20px}
.note b{color:var(--warn)}
.empty{color:var(--muted);padding:24px;text-align:center;background:var(--card);
 border:1px dashed var(--line);border-radius:5px}
"""

JS = """
function kmFilter(v){
  v=(v||'').trim().toLowerCase();
  document.querySelectorAll('.site').forEach(function(d){
    var hit = !v || d.dataset.k.indexOf(v)>=0;
    d.style.display = hit?'':'none';
    if(v && hit) d.open = true;
  });
}
"""


def render(found, loose, root):
    out = ['<!doctype html><meta charset="utf-8">',
           '<title>현장별 한 곳에</title><style>%s</style>' % CSS,
           '<div class="wrap">',
           '<h1>현장별 한 곳에</h1>',
           '<div class="sub">%s 기준 · 결과 원본은 %s 안에 그대로 있습니다. '
           '이 화면은 현장별로 묶어 보여줄 뿐 파일을 옮기지 않습니다.</div>'
           % (_esc(today().strftime('%Y-%m-%d')), _esc(root or '(폴더를 못 찾음)')),
           '<div class="tools"><input id="q" placeholder="현장 이름을 치면 걸러집니다" '
           'oninput="kmFilter(this.value)"></div>']
    if not found and not loose:
        out.append('<div class="empty">아직 결과가 없습니다. 도구를 한 번 돌리시면 여기에 쌓입니다.</div>')
    for site in sorted(found):
        kinds = found[site]
        total = sum(len(v) for v in kinds.values())
        keys = [k for k in ORDER if k in kinds] + [k for k in kinds if k not in ORDER]
        out.append('<details class="site" data-k="%s"><summary>%s'
                   '<span class="cnt">%s · 파일 %d개</span></summary><div class="body">'
                   % (_esc(site.lower()), _esc(site),
                      _esc(' · '.join(keys)), total))
        for k in keys:
            out.append('<div class="kind"><h3>%s</h3>' % _esc(k))
            for fn, p, mt, tool in kinds[k][:12]:
                out.append('<div class="f"><a href="%s">%s</a>'
                           '<span class="t">%s</span><span class="d">%s</span></div>'
                           % (_url(p), _esc(fn), _esc(tool),
                              _esc(mt.strftime('%m-%d') if mt else '')))
            if len(kinds[k]) > 12:
                out.append('<div class="f"><a>… 그 밖 %d개</a></div>' % (len(kinds[k]) - 12))
            out.append('</div>')
        out.append('</div></details>')
    if loose:
        n = sum(len(v) for v in loose.values())
        out.append('<details class="site" data-k="현장미상"><summary>현장을 못 읽은 파일'
                   '<span class="cnt">파일 %d개</span></summary><div class="body">' % n)
        for k in sorted(loose):
            out.append('<div class="kind"><h3>%s</h3>' % _esc(k))
            for fn, p, mt, tool in loose[k][:10]:
                out.append('<div class="f"><a href="%s">%s</a><span class="t">%s</span></div>'
                           % (_url(p), _esc(fn), _esc(tool)))
            out.append('</div>')
        out.append('</div></details>')
    out.append('<div class="note"><b>파일은 움직이지 않았습니다.</b> '
               '원본은 도구별 폴더에 그대로 있고, 이 화면이 현장 이름으로 묶어 링크만 겁니다. '
               '현장 이름은 파일 이름 앞머리에서 읽습니다 — 「현장을 못 읽은 파일」에 들어간 것은 '
               '파일 이름이 현장명으로 시작하지 않는 것입니다.</div>')
    out.append('</div><script>%s</script>' % JS)
    return '\n'.join(out)


def build(quiet=False):
    found, loose, root = scan()
    doc = render(found, loose, root)
    base = cfg('base')
    path = os.path.join(base, '_현장별_한곳에.html') if base else '_현장별_한곳에.html'
    try:
        io.open(path, 'w', encoding='utf-8').write(doc)
    except Exception as e:
        path = '_현장별_한곳에.html'
        io.open(path, 'w', encoding='utf-8').write(doc)
        if not quiet:
            print('기본 위치에 못 써서 현재 폴더에 만들었습니다 : %s' % e)
    if not quiet:
        print('현장 %d곳 · 파일 %d개'
              % (len(found), sum(len(v) for s in found.values() for v in s.values())))
        print('만듦 : %s' % path)
    try:
        log('현장별한곳에', '현장 %d곳' % len(found))
    except Exception:
        pass
    return path


if __name__ == '__main__':
    build()

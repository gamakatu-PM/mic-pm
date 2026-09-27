# -*- coding: utf-8 -*-
"""모든 pptx 를 HTML 로 다시 그려 넘침·겹침·표 밀림을 잰다."""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # preview.py 가 같은 폴더에
from preview import slide_html
from pptx import Presentation
from playwright.sync_api import sync_playwright

CSS = ('<style>body{margin:0;font-family:"Noto Sans CJK KR","Malgun Gothic",sans-serif}'
       '.s{position:relative;background:#fff;margin:0 0 14px 0;overflow:visible}'
       '.b{position:absolute;box-sizing:border-box;padding:1px}'
       'table{position:absolute;border-collapse:collapse;table-layout:fixed}'
       'td{border:1px solid #d9d9d9;padding:2px 4px;vertical-align:middle;word-break:break-all}</style>')
JS = r"""
() => {
 const out = [];
 document.querySelectorAll('.s').forEach((s, si) => {
  const sr = s.getBoundingClientRect();
  const texts = [];
  s.querySelectorAll(':scope > .b').forEach((b, bi) => {
   const inner = b.firstElementChild;
   if (!inner) return;
   const br = b.getBoundingClientRect();
   let top = 1e9, bot = -1e9, left = 1e9, right = -1e9;
   inner.querySelectorAll('div').forEach(d => {
     const rg = document.createRange(); rg.selectNodeContents(d);
     for (const r of rg.getClientRects()) { if (r.width < 1) continue;
       top = Math.min(top, r.top); bot = Math.max(bot, r.bottom);
       left = Math.min(left, r.left); right = Math.max(right, r.right); }
   });
   if (bot < 0) return;
   const txt = b.innerText.trim().slice(0, 30);
   const over = bot - br.bottom;
   if (over > 3) out.push({slide: si + 1, kind: '글자넘침(아래)', px: Math.round(over), text: txt});
   if (bot > sr.bottom - 2) out.push({slide: si + 1, kind: '장 밖으로', px: Math.round(bot - sr.bottom), text: txt});
   texts.push({top, bot, left, right, txt, el: b});
  });
  for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
   const a = texts[i], c = texts[j];
   const ox = Math.min(a.right, c.right) - Math.max(a.left, c.left);
   const oy = Math.min(a.bot, c.bot) - Math.max(a.top, c.top);
   if (ox > 3 && oy > 3) out.push({slide: si + 1, kind: '글자겹침', px: Math.round(Math.min(ox, oy)), text: a.txt + ' / ' + c.txt});
   else if (oy > 3 && ox > -4) out.push({slide: si + 1, kind: '글자붙음', px: Math.round(ox), text: a.txt + ' / ' + c.txt});
  }
  const fills = [];
  s.querySelectorAll(':scope > .b').forEach(b => {
    const bg = getComputedStyle(b).backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)') { const r = b.getBoundingClientRect(); if (r.width > 2 && r.height > 2) fills.push({r, el: b, bg}); }
  });
  texts.forEach(t => fills.forEach(f => {
    if (f.el === t.el) return;
    const r = f.r;
    const inside = t.left >= r.left - 0.5 && t.right <= r.right + 0.5 && t.top >= r.top - 0.5 && t.bot <= r.bottom + 0.5;
    if (inside) return;
    const ox = Math.min(t.right, r.right) - Math.max(t.left, r.left);
    const oy = Math.min(t.bot, r.bottom) - Math.max(t.top, r.top);
    // 글자가 그 도형 안에 걸쳐 있거나 3px 안으로 붙어 있으면
    if (oy > 2 && ox > -3) {
      // 도형이 글자를 반쯤 덮거나 바로 옆에 붙은 경우만 (글자 상자 자체가 그 도형을 품는 배경이면 제외)
      const tb = t.el.getBoundingClientRect();
      if (tb.left <= r.left && tb.right >= r.right && tb.top <= r.top && tb.bottom >= r.bottom) {
        if (ox > -3 && !(t.right < r.left - 3 || t.left > r.right + 3)) out.push({slide: si + 1, kind: '글자-도형 붙음', px: Math.round(ox), text: t.txt + ' / (' + f.el.innerText.trim().slice(0, 12) + ')'});
        return;
      }
      out.push({slide: si + 1, kind: '글자-도형 붙음', px: Math.round(ox), text: t.txt + ' / (' + f.el.innerText.trim().slice(0, 12) + ')'});
    }
  }));
  s.querySelectorAll(':scope > table').forEach(t => {
   const tr = t.getBoundingClientRect();
   if (tr.bottom > sr.bottom - 30) out.push({slide: si + 1, kind: '표가 바닥글 침범', px: Math.round(tr.bottom - (sr.bottom - 30)), text: t.innerText.trim().slice(0, 20)});
  });
 });
 return out;
}
"""
def main(folder, out_json):
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1000, 'height': 700})
        for f in sorted(glob.glob(os.path.join(folder, '*.pptx'))):
            prs = Presentation(f)
            html = '<!doctype html><meta charset="utf-8">' + CSS + ''.join(slide_html(s, prs.slide_width, prs.slide_height) for s in prs.slides)
            hp = os.path.join(os.path.dirname(out_json), '_qa.html')
            open(hp, 'w', encoding='utf-8').write(html)
            pg.goto('file://' + hp)
            r = pg.evaluate(JS)
            if r:
                res[os.path.basename(f)] = r
        b.close()
    json.dump(res, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = sum(len(v) for v in res.values())
    print('decks with issues', len(res), 'issues', n)
    for k, v in res.items():
        for it in v:
            print('%-28s %2d장 %-10s %4dpx  %s' % (k[:28], it['slide'], it['kind'], it['px'], it['text']))
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const st=fs.readFileSync('state.json','utf8');
const tabs=[['map','여정'],['today','오늘'],['sites','현장'],['ask','창고']];
const out={};
for(const [tag,path] of [['1호','split/index.html'],['2호','v2/index.html'],['3호','v3/index.html']]){
  const ctx=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2});
  const p=await ctx.newPage();p.setDefaultTimeout(3000);
  await p.addInitScript(s=>{try{localStorage.setItem('km6_state',s)}catch(e){}},st);
  await p.goto('file://'+process.cwd()+'/'+path,{waitUntil:'load'});await p.waitForTimeout(700);
  const r={};
  for(const [v,nm] of tabs){
    await p.click(`nav.tabbar button[data-v="${v}"]`);await p.waitForTimeout(450);
    await p.screenshot({path:`cap_${tag}_${v}.png`});
    r[nm]=await p.evaluate(()=>{
      const vis=e=>{const b=e.getBoundingClientRect();return b.height>0&&b.width>0};
      const main=document.querySelector('main');
      const H=window.innerHeight, tab=document.querySelector('nav.tabbar').getBoundingClientRect().height,
            hd=document.querySelector('header.top').getBoundingClientRect().height;
      const view=H-tab-hd;                       // 실제로 보이는 높이
      const cards=[...document.querySelectorAll('.card,.jcard,.row')].filter(vis);
      const inView=cards.filter(e=>{const b=e.getBoundingClientRect();return b.top<H-tab&&b.bottom>hd}).length;
      const btns=[...document.querySelectorAll('button')].filter(vis).map(e=>e.getBoundingClientRect().height);
      const small=btns.filter(h=>h<44).length;   // 손가락 기준 44px 미만
      return {스크롤길이:Math.round(main.scrollHeight),
              보이는높이:Math.round(view),
              한화면카드:inView, 전체카드:cards.length,
              작은단추:small, 전체단추:btns.length,
              가장작은단추:btns.length?Math.round(Math.min(...btns)):0,
              위띠:Math.round(hd), 아래띠:Math.round(tab)};
    });
  }
  r['글씨']=await p.evaluate(()=>getComputedStyle(document.body).fontSize);
  r['줄간격']=await p.evaluate(()=>getComputedStyle(document.body).lineHeight);
  out[tag]=r; await ctx.close();
}
fs.writeFileSync('비교.json',JSON.stringify(out,null,1));
console.log(JSON.stringify(out,null,1));
await b.close();

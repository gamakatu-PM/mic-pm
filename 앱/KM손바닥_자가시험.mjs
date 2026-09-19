/* KM 손바닥 자가 시험 — 고칠 때마다 이것부터 돌린다.
   쓰는 법 : node 시험.mjs            (split 폴더를 시험)
            node 시험.mjs wrap.html  (한 파일판을 시험)                */
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const TARGET=process.argv[2]||'split/index.html';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await (await b.newContext({viewport:{width:390,height:844}})).newPage();p.setDefaultTimeout(2500);
await p.addInitScript(s=>{try{localStorage.setItem('km6_state',s)}catch(e){}},fs.readFileSync('state.json','utf8'));
const errs=[];p.on('pageerror',e=>errs.push('오류 '+e.message));
p.on('console',m=>{if(m.type()==='error'&&!/ERR_CERT|Failed to load resource/.test(m.text()))errs.push('콘솔 '+m.text())});
p.on('dialog',d=>d.accept());
await p.goto('file://'+process.cwd()+'/'+TARGET,{waitUntil:'load'});await p.waitForTimeout(600);
let ok=0,bad=0;const T=async(n,f)=>{const e0=errs.length;try{await f();if(errs.length>e0)throw new Error(errs[e0]);ok++;console.log('✓',n)}catch(e){bad++;console.log('✗',n,'—',e.message.split('\n')[0].slice(0,90))}};
const X=async()=>{if(await p.isVisible('.sheetbar .b'))await p.click('.sheetbar .b');await p.waitForTimeout(150)};
const go=async v=>{await X();await p.click(`nav.tabbar button[data-v="${v}"]`);await p.waitForTimeout(300)};

await T('여정 — 현장이 뜬다',async()=>{const n=await p.$$eval('.jcard',e=>e.length);if(n<5)throw new Error('현장 '+n)});
await T('여정 — 조용한 현장 표시',async()=>{const t=await p.textContent('#mapBody');if(!/일째 조용|오늘 통화/.test(t))throw new Error('없음')});
await T('여정 — 단계를 열면 열쇠가 나온다',async()=>{await p.click('.jcard >> nth=0');await p.waitForTimeout(250);
  await p.click('.qn >> nth=0');await p.waitForSelector('#sheetBox .row.rq');await X()});
await T('여정 — 열쇠에 확정·추정·문안 단추',async()=>{await p.click('.qn >> nth=0');await p.waitForTimeout(200);
  await p.click('#sheetBox .row.rq >> nth=0');await p.waitForSelector('#rqOk');
  const t=await p.textContent('#sheetBox');if(!/제가 .*만들까요|전화 첫마디/.test(t))throw new Error('단추 없음');await X()});
await T('계약·계산서 게이트',async()=>{let hit=false;
  for(let i=0;i<9;i++){await p.click(`.qn >> nth=${i}`);await p.waitForTimeout(200);
    const t=await p.textContent('#sheetBox');
    if(/계약 · 계산서 확인/.test(t)){hit=true;await X();break} await X()}
  if(!hit)throw new Error('게이트 열쇠가 없음')});
await T('오늘 — 카드와 단추',async()=>{await go('today');await p.waitForSelector('#todayBody .card');
  const t=await p.textContent('#todayBody');if(!/맞아|문안/.test(t))throw new Error('단추 없음')});
await T('오늘 — 연락 끊긴 곳',async()=>{const t=await p.textContent('#todayBody');if(!/연락이 끊긴 곳/.test(t))throw new Error('절 없음')});
await T('창고 — 질문과 정해진 것',async()=>{await go('ask');await p.waitForSelector('#askBody .card');
  const t=await p.textContent('#askBody');if(!/제가 여쭙는 것/.test(t))throw new Error('질문 절 없음')});
await T('창고 — 찾기',async()=>{await p.fill('#askFind','연합');await p.waitForTimeout(350);
  const n=await p.$$eval('#askBody .deci',e=>e.length);await p.fill('#askFind','');await p.waitForTimeout(250);if(n<1)throw new Error('0건')});
await T('현장 — 목록과 상세',async()=>{await go('sites');
  if(await p.isVisible('text=‹ 현장 목록')){await p.click('text=‹ 현장 목록');await p.waitForTimeout(250)}
  await p.waitForSelector('#siteCards .card');
  await p.click('#siteCards .card >> nth=0');await p.waitForSelector('.tabs2')});
await T('현장 — 공정·사람·돈 탭',async()=>{for(const i of [0,1,3]){await p.click(`.tabs2 button >> nth=${i}`);await p.waitForTimeout(200)}});
await T('회의 — 시작 화면',async()=>{await go('meet');await p.waitForSelector('#mtStart')});
await T('설정 — PC 붙여넣기·고치기',async()=>{await go('set');await p.waitForSelector('#feedText');
  const t=await p.textContent('#v-set');if(!/앱 내용 고치기/.test(t))throw new Error('고치기 없음')});
await T('고치기 — 단계 9개',async()=>{await p.click('text=고치기 열기');await p.waitForSelector('#sheetBox .row');
  const n=await p.$$eval('#sheetBox .row',e=>e.length);if(n<9)throw new Error('단계 '+n);await X()});
await T('결론 대장 — 확정하면 한 줄 쌓인다',async()=>{await X();await p.click('nav.tabbar button[data-v="map"]');await p.waitForTimeout(250);
  if(await p.isVisible('text=‹ 현장 지도')){await p.click('text=‹ 현장 지도');await p.waitForTimeout(250)}
  const before=await p.evaluate(()=>Object.keys(JSON.parse(localStorage.getItem('km6_state')).decisions||{}).length);
  await p.click('.jcard >> nth=0');await p.waitForTimeout(250);
  await p.click('.qn >> nth=0');await p.waitForTimeout(250);
  await p.click('#sheetBox .row.rq >> nth=0');await p.waitForSelector('#rqVal');
  await p.fill('#rqVal','시험값 '+Date.now());await p.fill('#rqBasis','자가시험');await p.click('#rqOk');await p.waitForTimeout(500);await X();
  const after=await p.evaluate(()=>Object.keys(JSON.parse(localStorage.getItem('km6_state')).decisions||{}).length);
  if(after!==before+1)throw new Error(before+'→'+after)});
await T('창고 — 결론 대장이 보인다',async()=>{await go('ask');await p.waitForTimeout(300);
  const t=await p.textContent('#askBody');if(!/\[프로님\]|\[제가\]/.test(t))throw new Error('결론 대장 표시 없음')});
await T('확정 대장 CSV 내보내기',async()=>{await go('set');await p.waitForTimeout(250);
  await p.click('#btnCsv');await p.waitForSelector('#sheetBox .draft');
  const t=await p.textContent('#sheetBox .draft');
  if(!/^일자,현장,항목,값,근거,누가,상태/.test(t.trim()))throw new Error('머리글 다름: '+t.slice(0,40));
  console.log('     ',t.trim().split('\n')[1].slice(0,80));await X()});
await T('마감 — 오늘 화면에 늦으면 안 되는 것',async()=>{await X();await go('today');await p.waitForTimeout(400);
  const t=await p.textContent('#todayBody');
  if(!/늦으면 안 되는 것/.test(t))throw new Error('절 없음');
  const seg=t.replace(/\s+/g,' ').match(/늦으면 안 되는 것[\s\S]{0,200}/)[0];console.log('     ',seg.slice(0,190))});
await T('마감 — 열쇠에 D-day',async()=>{await go('map');
  if(await p.isVisible('text=‹ 현장 지도')){await p.click('text=‹ 현장 지도');await p.waitForTimeout(250)}
  await p.click('.jcard:has-text("조선호텔")');await p.waitForTimeout(300);
  const t=await p.textContent('#mapBody');
  if(!/D-\d|일 지남|오늘까지/.test(t))throw new Error('D-day 없음');
  console.log('     ',t.replace(/\s+/g,' ').match(/늦으면 안 되는 것[\s\S]{0,150}/)?.[0]?.slice(0,150)||'(현장 카드에만)')});
console.log(`\n통과 ${ok} / 실패 ${bad}`);
if(errs.length)console.log('페이지 오류:',errs);
process.exitCode=bad?1:0;
await b.close();

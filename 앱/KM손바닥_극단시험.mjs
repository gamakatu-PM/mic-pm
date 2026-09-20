import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import fs from 'fs';
const TARGET=process.argv[2]||'split/index.html';
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const errsAll=[];
async function run(name,state,fn){
  const p=await (await b.newContext({viewport:{width:390,height:844}})).newPage();p.setDefaultTimeout(2500);
  if(state!==null)await p.addInitScript(s=>{try{localStorage.setItem('km6_state',s)}catch(e){}},state);
  const errs=[];p.on('pageerror',e=>errs.push(e.message.split('\n')[0]));
  p.on('console',m=>{if(m.type()==='error'&&!/ERR_CERT|Failed to load resource/.test(m.text()))errs.push('콘솔 '+m.text().slice(0,100))});
  p.on('dialog',d=>d.accept());
  await p.goto('file://'+process.cwd()+'/'+TARGET,{waitUntil:'load'});await p.waitForTimeout(500);
  try{await fn(p)}catch(e){errs.push('시험 '+e.message.split('\n')[0].slice(0,100))}
  console.log((errs.length?'✗ ':'✓ ')+name,errs.length?'\n     '+errs.join('\n     '):'');
  errsAll.push(...errs.map(e=>name+': '+e));await p.context().close();
}
const tabs=['map','today','sites','ask','meet','set'];
const walk=async p=>{for(const v of tabs){await p.click(`nav.tabbar button[data-v="${v}"]`);await p.waitForTimeout(200)}};
const toList=async p=>{const t=await p.$('#mapBody .b.ghost');if(t&&/현장 지도/.test(await t.textContent()))await t.click();await p.waitForTimeout(250)};
const S0=JSON.parse(fs.readFileSync('state.json','utf8'));

await run('1 완전 빈 상태(첫 설치)',null,async p=>{await walk(p);await p.click('nav.tabbar button[data-v="sites"]');await p.click('#btnAddSite');await p.fill('#nsName','시험현장');await p.click('#nsOk');await p.waitForTimeout(300);
  await p.click('nav.tabbar button[data-v="map"]');await p.waitForTimeout(250);await toList(p);await p.click('.jcard');await p.waitForTimeout(250);await p.click('.qn >> nth=0');await p.waitForTimeout(200)});
await run('2 현장 있고 할 일 0',JSON.stringify({...S0,items:{},asks:{}}),async p=>{await walk(p)});
await run('3 회의 시작 → 아무것도 안 찍고 끝',JSON.stringify(S0),async p=>{await p.click('nav.tabbar button[data-v="meet"]');await p.click('#mtStart');await p.waitForTimeout(200);await p.click('text=회의 끝');await p.waitForTimeout(400)});
await run('4 열쇠를 지운 설정(판)이 들어온 뒤',(()=>{const s=JSON.parse(JSON.stringify(S0));
  // 프로님이 앱 내용 고치기에서 외함 단계의 열쇠를 전부 지웠다고 가정
  s.cfg={ver:9,ts:'2026-09-19T00:00:00Z',quests:null,lists:{}};return JSON.stringify(s)})(),async p=>{
  await p.evaluate(()=>{QUESTS[2].req=[];render()});await walk(p);await p.click('nav.tabbar button[data-v="map"]');await p.click('.jcard >> nth=0');await p.waitForTimeout(200);await p.click('.qn >> nth=2');await p.waitForTimeout(200)});
await run('5 현장 200곳 · 할 일 800건 (성능)',(()=>{const s=JSON.parse(JSON.stringify(S0));
  for(let i=0;i<200;i++){const n='현장'+i;const id='s_x'+i;s.sites[id]={id,name:n,people:[],facts:[],req:{},due:'2027-0'+(1+i%9)+'-15',updated:'2026-09-19T00:00:00Z',lastCall:'09-0'+(1+i%9)};
    for(let j=0;j<4;j++)s.items['X'+i+'_'+j]={id:'X'+i+'_'+j,kind:j%2?'todo':'ask',site:n,text:'할 일 '+j,status:'open',created:'2026-09-19T00:00:00Z',quest:'계약'}}
  return JSON.stringify(s)})(),async p=>{const t0=Date.now();await walk(p);const ms=Date.now()-t0;console.log('     6탭 순회',ms,'ms');
  await p.click('nav.tabbar button[data-v="today"]');const t1=Date.now();await p.waitForSelector('#todayBody .card');console.log('     오늘 화면',Date.now()-t1,'ms');
  const bytes=await p.evaluate(()=>localStorage.getItem('km6_state').length);console.log('     저장 크기',Math.round(bytes/1024),'KB');if(ms>6000)throw new Error('느림')});
await run('6 같은 할 일이 A- 와 T- 로 두 번 (PC 피드 중복)',JSON.stringify(S0),async p=>{
  const before=await p.evaluate(()=>Object.keys(JSON.parse(localStorage.getItem('km6_state')).items).length);
  const feed={sites:{},items:[{id:'T-zf8uzd',kind:'todo',site:'연합기숙사',text:'연합기숙사 타공도 정식 재송부',when:'오늘',status:'open',quest:'외함설치'}],src:{}};
  await p.click('nav.tabbar button[data-v="set"]');await p.fill('#feedText',JSON.stringify(feed));await p.click('#btnFeed');await p.waitForTimeout(400);
  const after=await p.evaluate(()=>Object.keys(JSON.parse(localStorage.getItem('km6_state')).items).length);
  if(after!==before)throw new Error(`같은 할 일이 중복으로 늘어남 ${before}→${after} (A-zf8uzd 가 이미 있음)`)});
await run('7 보내기 30줄일 때 메일 길이',JSON.stringify({...S0,outbox:Array.from({length:30},(_,i)=>({ts:'',line:'확정,현장'+i+',항목,값이 꽤 길어서 메일 주소 길이 제한에 걸릴 수 있는 값 '+i+',근거',site:'',type:'확정'}))}),async p=>{
  await p.click('#fab');await p.waitForSelector('#sbMail');
  const t=await p.textContent('#sheetBox');const len=(await p.textContent('.draft')).length;console.log('     본문',len,'자');
  if(len>1800&&!/길어|복사/.test(t))throw new Error('본문이 '+len+'자인데 길이 경고가 없음 — 일부 메일 앱은 2,000자 넘으면 열지 못함')});
await run('8 확정값 넣기 → 결론 대장에 남나',JSON.stringify(S0),async p=>{await p.click('nav.tabbar button[data-v="sites"]');await p.click('#siteCards .card >> nth=0');await p.click('.tabs2 button:has-text("기록")');
  await p.click('text=+ 확정값 넣기');await p.fill('#fcItem','시험 항목');await p.fill('#fcVal','시험 값');await p.click('#fcOk');await p.waitForTimeout(300);
  const n=await p.evaluate(()=>Object.values(JSON.parse(localStorage.getItem('km6_state')).decisions||{}).filter(d=>d.item==='시험 항목').length);
  if(!n)throw new Error('확정값을 넣었는데 결론 대장에 없음')});
await run('9 경계를 확정으로 → 결론 대장에 남나',JSON.stringify(S0),async p=>{await p.click('nav.tabbar button[data-v="sites"]');await p.click('#siteCards .card >> nth=0');await p.click('.tabs2 button:has-text("경계")');
  await p.selectOption('.row select >> nth=0','전기');await p.waitForTimeout(200);await p.click('.row .pill >> nth=0');await p.waitForTimeout(300);
  const n=await p.evaluate(()=>Object.values(JSON.parse(localStorage.getItem('km6_state')).decisions||{}).filter(d=>d.source==='경계').length);
  if(!n)throw new Error('경계를 확정했는데 결론 대장에 없음')});
await run('10 현장 이름에 따옴표·꺾쇠',JSON.stringify(S0),async p=>{await p.click('nav.tabbar button[data-v="sites"]');await p.click('#btnAddSite');await p.fill('#nsName',`이상한"현장'<b>`);await p.click('#nsOk');await p.waitForTimeout(300);
  await p.click('nav.tabbar button[data-v="map"]');await p.waitForTimeout(250);await toList(p);await p.click('.jcard:has-text("이상한")');await p.waitForTimeout(200);await p.click('.qn >> nth=0');await p.waitForTimeout(200);await p.click('#sheetBox .row.rq >> nth=0');await p.waitForTimeout(200)});
console.log('\n오류 합계',errsAll.length);
await b.close();

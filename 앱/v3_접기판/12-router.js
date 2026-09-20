/* ============ 화면 전환 ============ */
document.querySelectorAll('nav.tabbar button').forEach(b=>b.onclick=()=>{view=b.dataset.v;render()});
function render(){
  document.querySelectorAll('nav.tabbar button').forEach(b=>b.classList.toggle('on',b.dataset.v===view));
  ['map','today','sites','ask','meet','set'].forEach(v=>document.getElementById('v-'+v).hidden=(v!==view));
  const titles={map:'여정',today:'오늘',sites:'현장',ask:'창고',meet:'회의',set:'설정'};
  document.getElementById('hTitle').textContent=titles[view];
  const d=new Date();document.getElementById('hSub').textContent=ymd(d)+' ('+'일월화수목금토'[d.getDay()]+') · 현장 '+Object.keys(S.sites).length+'곳';
  if(view==='ask')renderAsk();if(view==='map')renderMap();if(view==='today')renderToday();if(view==='sites')renderSites();if(view==='meet')renderMeet();if(view==='set')renderSet();
  renderFab();
  if(typeof applyFold==='function')applyFold();   /* 3호 : 접기 */
}
function renderFab(){const f=document.getElementById('fab');const n=S.outbox.length;f.hidden=!n||view==='set';f.textContent='보내기 '+n+'건 ↑'}
document.getElementById('fab').onclick=()=>sendOutbox();


/* ---- 결정 · 질문 창고 ---- */
function askDays(a){const t=a.ts||a.date;if(!t)return 0;return Math.max(0,Math.floor((Date.now()-new Date(t).getTime())/86400000))}
function allDecisions(){
  const led=decisionList();
  if(led.length)return led.map(d=>({date:d.date,site:d.site,item:d.item,value:d.value,basis:(d.by==='클로드'?'[제가] ':'[프로님] ')+(d.basis||''),kind:d.source||'결론',prev:d.prev}));
  const out=[];
  Object.values(S.asks||{}).filter(a=>a.status==='답함').forEach(a=>out.push({date:(a.answeredAt||a.ts||'').slice(0,10),site:a.site||'',item:a.q,value:a.answer,basis:(a.who==='클로드'?'제 질문에 답하심':'제 답')+(a.why?' · '+a.why:''),kind:'문답'}));
  Object.values(S.sites).forEach(s=>{
    (s.facts||[]).forEach(f=>out.push({date:f.date||'',site:s.name,item:f.item,value:f.value,basis:f.basis||'',kind:'확정값'}));
    Object.keys(s.req||{}).forEach(k=>{const v=s.req[k];if(v.state!=='확정')return;const r=reqDef(k);
      out.push({date:(v.date||'').slice(0,10),site:s.name,item:r?r.n:k,value:v.value,basis:v.basis||'',kind:'열쇠'})});
  });
  return out.sort((a,b)=>(b.date||'').localeCompare(a.date||''));
}
function renderAsk(){
  const A=Object.values(S.asks||{});
  const mine=A.filter(a=>a.who==='클로드'&&a.status!=='답함'&&a.status!=='닫힘').sort((a,b)=>askDays(b)-askDays(a));
  const yours=A.filter(a=>a.who==='프로님'&&a.status!=='답함'&&a.status!=='닫힘').sort((a,b)=>askDays(b)-askDays(a));
  const dec=allDecisions();
  const q=(S.askFind||'').trim();
  const shown=q?dec.filter(d=>(d.site+d.item+d.value+d.basis).includes(q)):dec;
  let o=`<div class="notice">여기가 <b>결정과 질문 창고</b>입니다. 제가 여쭙는 것, 프로님이 물으시는 것, 정해진 것이 한곳에 쌓이고 찾을 수 있습니다. 찾기는 이 폰 안에서 도니 비용이 없습니다.</div>
  <div class="chips"><span class="chip ask">제가 여쭙는 것 ${mine.length}</span><span class="chip warn">프로님이 물으신 것 ${yours.length}</span><span class="chip ok">정해진 것 ${dec.length}</span></div>`;
  o+=`<h2 class="sec">제가 여쭙는 것 <small>답을 주셔야 제가 진행합니다</small></h2>`;
  o+=mine.length?mine.map(a=>{const d=askDays(a);
    return `<div class="card askq ${d>=3?'old':''}"><div class="id">${esc(a.site||'전체')} · ${d?d+'일째':'오늘'} ${a.urgency==='급함'?'<span class="pill p-ask">급함</span>':''}</div>
    <div class="t">${esc(a.q)}</div>${a.why?`<div class="m">${esc(a.why)}</div>`:''}
    ${(a.options||[]).length?`<div class="opt">${a.options.map((o2,ix)=>`<button onclick="answerAsk('${a.id}',${ix})">${esc(o2)}</button>`).join('')}</div>`:''}
    <div class="btns"><button class="b mic" onclick="answerAsk('${a.id}',-1)">말로 답하기 🎙</button><button class="b ghost" onclick="answerAsk('${a.id}',-2)">모르겠음 · 나중에</button></div></div>`}).join(''):'<div class="empty">없음</div>';
  o+=`<h2 class="sec">프로님이 물으신 것 <small>제가 답할 것</small></h2>`;
  o+=yours.length?yours.map(a=>`<div class="card askmine"><div class="id">${esc(a.site||'전체')} · ${askDays(a)?askDays(a)+'일째':'오늘'} <span class="pill p-warn">답 기다리는 중</span></div><div class="t">${esc(a.q)}</div><div class="small">다음에 제가 창을 열면 답하고, 답은 여기에 남습니다</div></div>`).join(''):'<div class="empty">없음</div>';
  o+=`<button class="bigask" onclick="newAsk()">＋ 클로드에게 물어보기 🎙</button>`;
  o+=`<h2 class="sec">정해진 것 ${dec.length} <small>언제 · 무엇을 · 왜</small></h2>
   <input class="search" id="askFind" placeholder="현장·품목·낱말로 찾기" value="${esc(q)}">`;
  o+=shown.slice(0,120).map(d=>`<div class="deci"><div class="h"><span class="d">${esc(d.date||'—')}</span><span class="pill p-${d.kind==='열쇠'?'acc':d.kind==='문답'?'warn':'ok'}">${d.kind}</span><b>${esc(d.site)}</b></div>
    <div><span class="v">${esc(d.item)}</span> = ${esc(String(d.value||'').slice(0,120))}</div>${d.basis?`<div class="small">${esc(d.basis.slice(0,110))}</div>`:''}</div>`).join('')||'<div class="empty">아직 없음</div>';
  if(shown.length>120)o+=`<div class="small" style="padding:6px">그 밖 ${shown.length-120}건 — 낱말로 좁혀 주십시오</div>`;
  document.getElementById('askBody').innerHTML=o;
  const f=document.getElementById('askFind');
  if(f){f.oninput=()=>{S.askFind=f.value;const s=f.selectionStart;renderAsk();const g=document.getElementById('askFind');if(g){g.focus();g.setSelectionRange(s,s)}}}
}
window.answerAsk=function(id,ix){
  const a=S.asks[id];if(!a)return;
  const put=(ans)=>{a.answer=ans;a.status='답함';a.answeredAt=now();saveAsk(a);
    saveDecision({site:a.site,item:a.q,value:ans,basis:(a.who==='클로드'?'제 질문에 프로님이 답하심':'제 답')+(a.why?' · '+a.why:''),source:'문답',by:a.who==='클로드'?'프로님':'클로드',ref:{askId:a.id}});
    queue(`답,${safe(a.site||'전체')},${safe(a.q)},${safe(ans)},앱 창고`,a.site,'답');
    if(a.site&&a.reqKey&&S.sites[a.sid]){setReq(S.sites[a.sid],a.reqKey,'확정',ans,'프로님 답 (창고)');saveSite(S.sites[a.sid])}
    render();toast('답을 담았습니다')};
  if(ix===-2){a.status='나중에';a.ts=now();saveAsk(a);render();toast('다음에 다시 여쭙겠습니다');return}
  if(ix===-1){micSheet(a.q,a.why||'말씀하시면 그대로 남습니다','',v=>{if(v)put(v)});return}
  put((a.options||[])[ix]||'');
};
window.newAsk=function(){
  micSheet('클로드에게 물어보기','무엇이든 물어보십시오. 제가 다음에 창을 열 때 답하고, 답은 창고에 남습니다.','',v=>{
    if(!v)return;const id='Q'+Date.now();
    const a={id,who:'프로님',q:v,site:curSite&&S.sites[curSite]?S.sites[curSite].name:'',status:'열림',ts:now()};
    saveAsk(a);queue(`질문,${safe(a.site||'전체')},${safe(v)}`,a.site,'질문');view='ask';render();toast('담았습니다. 제가 답하면 여기에 뜹니다')});
};
function saveAsk(a){a.updated=now();S.asks[a.id]=a;persist();dbWrite('asks/'+a.id,a)}


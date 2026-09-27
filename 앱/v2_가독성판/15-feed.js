/* ---- 연동 : 쌓이는 데이터가 앱으로, 앱이 다시 나에게 ---- */
function idleOf(s){
  // 「쉰 날」 = 마지막 통화·회의·기록에서 오늘까지. 녹취 분석의 값이 있으면 그것을 기준으로 이어 센다
  if(s.lastCall){
    const y=new Date().getFullYear();const m=s.lastCall.match(/(\d{1,2})-(\d{1,2})/);
    if(m){const d=new Date(y,+m[1]-1,+m[2]);const n=Math.floor((Date.now()-d.getTime())/86400000);if(n>=0&&n<400)return n}
  }
  const n=parseInt(s.idleDays||'',10);return isNaN(n)?null:n;
}
function idlePill(s){const n=idleOf(s);if(n==null)return '';
  const cls=n>=14?'p-ask':n>=7?'p-warn':'p-off';return `<span class="pill ${cls}">${n===0?'오늘 통화':n+'일째 조용'}</span>`}
function quietSites(){return Object.values(S.sites).map(s=>({s,n:idleOf(s)})).filter(x=>x.n!=null&&x.n>=7).sort((a,b)=>b.n-a.n)}
function claudeFilled(s){const out=[];const r=s.req||{};
  Object.keys(r).forEach(k=>{const v=r[k];if(v&&v.from&&v.state!=='확정')out.push({site:s.name,sid:s.id,key:k,...v})});return out}
function allFilled(){let a=[];Object.values(S.sites).forEach(s=>{a=a.concat(claudeFilled(s))});return a}
function renderFeedBar(){
  const f=allFilled();const inb=(S.inbox||[]).filter(x=>!x.seen);
  let o='';
  if(inb.length)o+=`<div class="inboxbar"><div class="it">제가 반영했습니다 · ${inb.length}건</div>${inb.slice(0,4).map(x=>`<div class="small">· ${esc(x.text)}</div>`).join('')}<div class="btns"><button class="b sm" onclick="seenInbox()">봤습니다</button>${inb.length>4?`<button class="b sm ghost" onclick="view='set';render()">전부 보기</button>`:''}</div></div>`;
  if(f.length)o+=`<div class="feedbar" onclick="filledSheet()"><div><div class="ft">제가 채운 것 ${f.length}건</div><div class="fs">대장·통화 기록에서 읽었습니다. 맞는지 봐 주십시오</div></div><span class="b sm pri">보기</span></div>`;
  return o;
}
window.seenInbox=function(){(S.inbox||[]).forEach(x=>x.seen=1);persist();dbWrite('meta/inbox',{lines:S.inbox});render()};
window.filledSheet=function(){
  const f=allFilled();
  openSheet(`<div class="story">대장(확정사항·견적발송)과 통화 기록에서 읽어 채운 것입니다. 전부 <b>추정·진행중</b> 이라 프로님이 「맞아」 를 누르셔야 확정이 됩니다. 틀리면 「아니야」 로 고쳐 주십시오.</div>
  ${f.map(x=>{const r=reqDef(x.key);return `<div class="card"><div class="id">${esc(x.site)} · <span class="pill p-${x.state==='추정'?'warn':'acc'}">${esc(x.state)}</span> <span class="small">${esc(x.from||'')}</span></div>
    <div class="t">${esc(r?r.n:x.key)}</div><div class="m">${esc(x.value||'')}</div><div class="small">근거 : ${esc(x.basis||'')}</div>
    <div class="btns"><button class="b pri" onclick="fillOk('${x.sid}','${x.key}')">맞아 (확정)</button><button class="b mic" onclick="fillNo('${x.sid}','${x.key}')">아니야 🎙</button><button class="b ghost" onclick="fillOpen('${x.sid}','${x.key}')">열쇠 열기</button></div></div>`}).join('')||'<div class="empty">없음</div>'}
  <div class="btns"><button class="b ghost" onclick="closeSheet()">닫기</button></div>`,'제가 채운 것 '+f.length+'건');
};
window.fillOk=function(sidv,key){const s=S.sites[sidv];const cur=(s.req||{})[key]||{};
  setReq(s,key,'확정',cur.value,(cur.basis||'')+' · 프로님 확인');saveSite(s);closeSheet();render();toast('확정했습니다')};
window.fillNo=function(sidv,key){const s=S.sites[sidv];const r=reqDef(key);
  micSheet((r?r.n:key)+' · 아니야','제가 읽은 값이 틀렸습니다. 맞는 값을 말씀해 주십시오. 제 값은 이력에 남습니다.','',v=>{
    if(!v)return;setReq(s,key,'확정',v,'프로님이 고치심');saveSite(s);closeSheet();render();toast('고치신 값으로 확정했습니다')})};
window.fillOpen=function(sidv,key){const pr=key.split('/');const qi=QUESTS.findIndex(q=>q.k===pr[0]);closeSheet();curSite=sidv;view='map';render();if(qi>=0)reqSheet(sidv,qi,pr[1])};


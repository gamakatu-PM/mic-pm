/* ---- 화면 : 여정 지도 (홈) ---- */
function renderMap(){
  const el=document.getElementById('mapBody');
  if(curSite&&S.sites[curSite]){el.innerHTML=journeyHtml(S.sites[curSite]);return}
  const sortBy=S.mapSort||'급한순';
  const arr=Object.values(S.sites).sort((a,b)=>{
    if(sortBy==='급한순'){const ia=idleOf(a),ib=idleOf(b);const oa=openOf(a),ob=openOf(b);
      return (ob+(ib>=7?3:0))-(oa+(ia>=7?3:0))||(ib||0)-(ia||0)||(a.name>b.name?1:-1)}
    if(sortBy==='조용한순'){return (idleOf(b)||0)-(idleOf(a)||0)}
    if(sortBy==='진행순'){return siteProg(b).pct-siteProg(a).pct}
    return (a.name>b.name?1:-1)});
  function openOf(s){return Object.values(S.items).filter(i=>i.site===s.name&&!['done','confirmed','cancel','requested'].includes(i.status)).length}
  if(!arr.length){el.innerHTML=renderFeedBar()+`<div class="notice">현장이 없습니다. 「현장」 탭에서 추가하거나 아침 한 장을 가져오십시오.</div>`;return}
  const totalOpen=Object.values(S.items).filter(i=>!['done','confirmed','cancel','requested'].includes(i.status)).length;
  el.innerHTML=renderFeedBar()+`<div class="notice">현장마다 9단계 여정입니다. 단계를 누르면 <b>무엇이 필요하고 · 지금 어디까지 왔고 · 제가 무엇을 만들어 드릴 수 있는지</b>가 나옵니다. 열쇠(필요한 것)를 채우면 단계가 닫힙니다.</div>
  <div class="chips">${['급한순','조용한순','진행순','이름순'].map(k=>`<button class="chip ${sortBy===k?'sel':''}" onclick="S.mapSort='${k}';persist();render()">${k}</button>`).join('')}</div>
  <div class="chips"><span class="chip acc">현장 ${arr.length}</span><span class="chip ask">미결 ${totalOpen}</span><span class="chip">열쇠 ${arr.reduce((a,s)=>a+siteProg(s).done,0)} / ${arr.reduce((a,s)=>a+siteProg(s).total,0)}</span></div>
  ${arr.map(s=>{const p=siteProg(s);const qi=currentQuest(s);const m=nextMove(s);
    return `<div class="card jcard" onclick="curSite='${s.id}';render()">
      <div class="jhead"><div><div class="t" style="font-size:1.05rem;margin:0">${esc(s.name)} ${idlePill(s)}</div><div class="small">${s.rooms?esc(s.rooms)+'실 · ':''}${s.due?'준공 '+esc(s.due):'준공일 [ ]'}${s.lastMeeting?' · 회의 '+esc(s.lastMeeting):''}${s.calls?' · 통화 '+esc(String(s.calls))+'건':''}${s.mainWho?' · '+esc(s.mainWho.slice(0,26)):''}</div></div><div class="pct">${p.pct}%</div></div>
      <div class="trail-mini">${QUESTS.map((q,i)=>{const st=questStatus(s,i);return `<span class="tm ${st.cls}" title="${esc(q.n)}">${i===qi?'●':questProg(s,q).done===q.req.length?'✓':''}</span>`}).join('<i></i>')}</div>
      <div class="small" style="margin-top:6px"><b>${esc(QUESTS[qi].n)}</b> · 다음 한 수 : ${m?esc(m.r.n):'없음'}${(()=>{const n=Object.values(S.items).filter(i=>i.site===s.name&&!['done','confirmed','cancel','requested'].includes(i.status)).length;return n?` · <span class="pill p-ask">할 일 ${n}</span>`:''})()}</div>
    </div>`}).join('')}`;
}
function journeyHtml(s){
  const p=siteProg(s);const qi=currentQuest(s);const m=nextMove(s);
  let h=`<div class="btns" style="margin-top:0"><button class="b ghost" onclick="curSite=null;render()">‹ 현장 지도</button><button class="b ghost" onclick="view='sites';siteTab='기록';render()">기록 · 사람 · 돈</button></div>
  <div class="card"><div class="jhead"><div><div class="t" style="font-size:1.15rem;margin:0">${esc(s.name)}</div><div class="small">${s.rooms?esc(s.rooms)+'실 · ':''}${s.due?'준공 '+esc(s.due):'준공일 [ ] · 「정보 고치기」 에서'}</div></div><div class="pct">${p.pct}%</div></div>
    <div class="bar"><i style="width:${p.pct}%"></i></div>
    <div class="small" style="margin-top:4px">열쇠 ${p.done} / ${p.total} · 지금 <b>${esc(QUESTS[qi].n)}</b> (${qi+1}/9)</div></div>`;
  const lateHere=lateList().filter(x=>x.s.id===s.id);
  if(lateHere.length){h+=`<div class="card" style="border-color:var(--ask)"><div class="id" style="color:var(--ask)">늦으면 안 되는 것 ${lateHere.length}</div>
    ${lateHere.slice(0,4).map(x=>`<div class="row" onclick="openReqByKey('${s.id}','${x.key}')"><span class="grow"><b>${esc(x.r?x.r.n:x.key)}</b><div class="small">${esc(x.date)} 까지 · ${esc(x.why)}</div></span>${duePill(x)}</div>`).join('')}</div>`}
  if(m){h+=`<div class="card next"><div class="id">다음 한 수</div><div class="t">${esc(m.r.n)}</div><div class="m">${esc(moveText(m))}</div>
    <div class="btns"><button class="b pri" onclick="reqSheet('${s.id}',${qi},'${m.r.k}')">열기</button><button class="b" onclick="reqDraft('${s.id}',${qi},'${m.r.k}')">${esc(moveAsk(m.r))}</button></div></div>`}
  h+=`<div class="trail">`+QUESTS.map((q,i)=>{const pr=questProg(s,q);const st=questStatus(s,i);const deg=Math.round(pr.done/pr.total*360);
    return `<div class="qn ${st.cls}" onclick="questSheet('${s.id}',${i})">
      <div class="ring" style="--deg:${deg}deg"><span>${pr.done===pr.total?'✓':q.icon}</span></div>
      <div class="qtxt"><div class="qname">${i+1}. ${esc(q.n)}</div><div class="small">${esc(st.label)} · 열쇠 ${pr.done}/${pr.total}${pr.part?' · 추정·진행 '+pr.part:''}</div></div>
      <div class="qgo">›</div></div>`}).join('')+`</div>`;
  return h;
}
window.openReqByKey=function(sid,key){const pr=key.split('/');const qi=QUESTS.findIndex(q=>q.k===pr[0]);if(qi>=0)reqSheet(sid,qi,pr[1])};
window.questSheet=function(sid,qi){
  const s=S.sites[sid],q=QUESTS[qi];const pr=questProg(s,q);const st=questStatus(s,qi);
  const miss=q.req.filter(r=>reqOf(s,q.k,r.k).state!=='확정');
  const rel=relatedItems(s,q);
  let story='';
  if(!miss.length)story=`이 단계는 닫혔습니다. 산출 : ${q.out}.`;
  else{const first=miss.find(x=>reqOf(s,q.k,x.k).state==='')||miss[0];const fs=reqOf(s,q.k,first.k);
    story=`${q.n}${qi===currentQuest(s)?'에 지금 서 있습니다':qi<currentQuest(s)?'는 지나왔지만 빈칸이 남았습니다':'는 아직 앞입니다'}. 열쇠 ${pr.total}개 중 ${pr.done}개 확정${pr.part?', '+pr.part+'개는 추정·진행 중':''}. 먼저 채울 것은 「${first.n}」 — ${fs.state==='추정'?'지금 값은 추정('+(fs.value||'')+')입니다. ':fs.state==='진행중'?'진행 중입니다. ':''}${first.how}`;
  }
  openSheet(`<div style="margin-bottom:6px"><span class="pill ${st.cls==='ok'?'p-ok':st.cls==='here'?'p-acc':st.cls==='warn'?'p-warn':'p-off'}">${esc(st.label)}</span></div>
  <div class="story">${esc(story)}</div>
  <div class="kv" style="margin:8px 0"><b>이 단계가 내는 것</b><span>${esc(q.out)}</span></div>
  <h2 class="sec">열쇠 (필요한 것) · 누르면 채웁니다</h2>
  ${q.req.map(r=>{const rs=reqOf(s,q.k,r.k);const cls=rs.state==='확정'?'ok':rs.state==='추정'?'warn':rs.state==='진행중'?'acc':'off';
    const dd=dueOf(s,q.k+'/'+r.k);
    return `<div class="row rq${r.gate?' gaterow':''}" onclick="reqSheet('${sid}',${qi},'${r.k}')"><span class="dot d-${cls==='acc'?'ask':cls}"></span><span class="grow"><b>${esc(r.n)}</b> ${duePill(dd)}<div class="small">${esc(r.who)}${rs.value?' · '+esc(rs.value):''}${dd?' · '+esc(dd.date)+' 까지 ('+esc(dd.why)+')':''}</div></span><span class="pill p-${cls}">${esc(RSTATE[rs.state||''])}</span></div>`}).join('')}
  ${rel.length?`<h2 class="sec">이 단계의 할 일 ${rel.length} <small>회의록에서 나온 것</small></h2>`+rel.map(i=>`<div class="card"><div class="id">${esc(i.id)} ${whenPill(i.when)} ${i.quest?'<span class="pill p-acc">이 단계</span>':'<span class="pill p-off">글자 매칭</span>'}</div><div class="t">${esc(i.makeq||i.text)}</div>${i.memo?`<div class="m">${esc(i.memo)}</div>`:''}
    <div class="btns">${i.kind==='todo'?`<button class="b pri" onclick="showDraft('${esc(i.id)}')">문안</button>`:''}${i.kind==='make'?`<button class="b pri" onclick="actMake('${esc(i.id)}')">만들어줘</button>`:''}<button class="b" onclick="act('${esc(i.id)}','done')">완료</button><button class="b mic" onclick="actNo('${esc(i.id)}')">아니야 🎙</button></div></div>`).join(''):'<div class="empty">이 단계에 걸린 할 일 없음</div>'}
  <div class="btns">${miss.length&&qi<currentQuest(s)?`<button class="b" onclick="questPass('${sid}',${qi})">이 단계는 이미 지났음 (남은 열쇠 전부 확정)</button>`:''}<button class="b ghost" onclick="closeSheet()">닫기</button></div>`,(qi+1)+'. '+q.n);
};
window.questPass=function(sid,qi){
  const s=S.sites[sid],q=QUESTS[qi];
  if(!confirm(`${q.n} 의 남은 열쇠를 전부 「확정 · 지남」 으로 채울까요? (프로님 확인으로 기록됩니다)`))return;
  s.req=s.req||{};
  q.req.forEach(r=>{if(reqOf(s,q.k,r.k).state!=='확정'){s.req[q.k+'/'+r.k]={state:'확정',value:'지남',basis:'프로님 확인(앱)',date:ymd(),ts:now()}}});
  saveSite(s);queue(`확정,${safe(s.name)},${safe(q.n)},단계 지남,프로님 확인`,s.name,'확정');saveDecision({site:s.name,item:q.n,value:'단계 지남',basis:'프로님 확인(앱)',source:'열쇠',by:'프로님'});closeSheet();render();toast(q.n+' 닫힘');
};
function gateBlocked(s,q,r){
  // 의뢰서(제작 착수)인데 같은 단계의 「계약·계산서」 게이트가 아직 확정이 아니면 막는다
  if(!r.order)return null;
  const g=q.req.find(x=>x.gate);if(!g)return null;
  const gs=reqOf(s,q.k,g.k);
  return gs.state==='확정'?null:{g,gs};
}
window.reqSheet=function(sid,qi,rk){
  const s=S.sites[sid],q=QUESTS[qi],r=q.req.find(x=>x.k===rk);const rs=reqOf(s,q.k,rk);
  const stateTxt=rs.state==='확정'?`확정 · ${rs.value||''} ${rs.date||''}${rs.basis?' · 근거 '+rs.basis:''}`:rs.state==='추정'?`추정 · ${rs.value||''}${rs.basis?' · '+rs.basis:''} → 상대가 말해 주면 확정으로`:rs.state==='진행중'?`진행 중 · ${rs.value||''}${rs.basis?' · '+rs.basis:''}`:'비어 있음';
  openSheet(`<div class="kv"><b>지금</b><span>${esc(stateTxt)}</span><b>누가</b><span>${esc(r.who)}</span><b>어떻게</b><span>${esc(r.how)}</span><b>왜</b><span>${esc(r.why)}</span></div>
  <h2 class="sec">채우기</h2>
  <label class="f">값 (날짜·수량·내용)</label><input id="rqVal" value="${esc(rs.value||'')}" placeholder="${r.type==='fact'?'예: 정식 계약서 / 299실 / 스터드':'날짜 또는 한 줄'}">
  <label class="f">근거 (누구 · 언제)</label><input id="rqBasis" value="${esc(rs.basis||'')}" placeholder="홍부장 9/15 통화 / 회의 / 메일">
  <div class="btns"><button class="b pri" id="rqOk">확정</button><button class="b" id="rqEst">추정으로</button><button class="b" id="rqWip">진행중</button>${rs.state?'<button class="b ghost" id="rqClr">비우기</button>':''}</div>
  ${(()=>{const b=gateBlocked(s,q,r);return b?`<div class="gate">🔒 <b>계약·계산서가 먼저입니다.</b> ${esc(b.gs.state?'지금 '+b.gs.state+' — '+(b.gs.value||''):'아직 확인 전')}.<br>프로님 규칙대로 제작에 들어가기 전에 계약서와 계산서 요청이 끝나야 합니다.<div class="btns"><button class="b pri" onclick="reqSheet('${sid}',${qi},'${b.g.k}')">계약·계산서 열쇠 열기</button><button class="b" onclick="moneyDraft('${sid}',${qi})">계약·계산서 요청 문안</button></div></div>`:''})()}
  <h2 class="sec">제가 할 수 있는 것</h2>
  <div class="btns" style="margin-top:0"><button class="b" onclick="reqDraft('${sid}',${qi},'${rk}')">${esc(moveAsk(r))}</button><button class="b" onclick="reqCall('${sid}',${qi},'${rk}')">전화 첫마디</button><button class="b mic" onclick="reqNote('${sid}',${qi},'${rk}')">🎙 들은 대로 한 줄</button></div>
  <div class="btns"><button class="b ghost" onclick="questSheet('${sid}',${qi})">‹ 단계로</button><button class="b ghost" onclick="closeSheet();editOneReq(${qi},${QUESTS[qi].req.findIndex(x=>x.k===rk)})">이 설명 고치기</button></div>`,r.n);
  const setState=(state)=>{const val=document.getElementById('rqVal').value.trim(),basis=document.getElementById('rqBasis').value.trim();
    if(state==='확정'&&!val){toast('확정에는 값이 필요합니다');return}
    if(state===''){delete (s.req||{})[q.k+'/'+rk];saveSite(s);queue(`비움,${safe(s.name)},${safe(r.n)},-,앱`,s.name,'비움');closeSheet();render();toast('비웠습니다');return}
    setReq(s,q.k+'/'+rk,state,val,basis||'앱 입력',{force:true});
    saveSite(s);closeSheet();render();
    const pr=questProg(s,q);const rel=relatedItems(s,q);
    if(state==='확정'&&rel.length){askClose(s,q,rel,pr,qi);return}
    if(state==='확정'&&pr.done===pr.total)cheer(s,q,qi);else toast(RSTATE[state]+' 으로 담았습니다');
  };
  document.getElementById('rqOk').onclick=()=>setState('확정');
  document.getElementById('rqEst').onclick=()=>setState('추정');
  document.getElementById('rqWip').onclick=()=>setState('진행중');
  const c=document.getElementById('rqClr');if(c)c.onclick=()=>{if(confirm('이 열쇠를 비울까요? (이력은 남습니다)'))setState('')};
};
function cheer(s,q,qi){
  const nx=QUESTS[qi+1];const p=siteProg(s);
  openSheet(`<div style="text-align:center;padding:6px 0 2px"><div style="font-size:2.4rem">🎉</div>
    <div class="t" style="font-size:1.1rem">${esc(q.n)} 닫혔습니다</div>
    <div class="small">${esc(s.name)} · 열쇠 ${p.done}/${p.total} · ${p.pct}%</div></div>
    <div class="story" style="margin-top:8px">${nx?`다음은 <b>${esc(nx.n)}</b> 입니다. 먼저 채울 것 : ${esc(nx.req[0].n)} — ${esc(nx.req[0].how)}`:'마지막 단계까지 끝났습니다. 수금만 남았습니다.'}</div>
    <div class="btns">${nx?`<button class="b pri" onclick="questSheet('${s.id}',${qi+1})">다음 단계 열기</button>`:''}<button class="b ghost" onclick="closeSheet()">닫기</button></div>`,'단계 완료');
}
function askClose(s,q,rel,pr,qi){
  openSheet(`<div class="story">「${esc(q.n)}」 의 열쇠를 채우셨습니다. 이 단계에 얽힌 할 일 ${rel.length}건이 아직 열려 있습니다. 같이 끝난 것이면 눌러 주십시오.</div>
    ${rel.map(i=>`<div class="row"><span class="grow">${esc(i.id)} · ${esc(i.makeq||i.text)}</span><button class="b sm pri" onclick="act('${esc(i.id)}','done');this.closest('.row').remove()">완료</button></div>`).join('')}
    <div class="btns"><button class="b" onclick="closeSheet();${pr.done===pr.total?`cheer(S.sites['${s.id}'],QUESTS[${qi}],${qi})`:''}">${pr.done===pr.total?'다 끝났습니다':'닫기'}</button></div>`,'같이 끝난 것이 있습니까?');
}
window.cheer=cheer;
window.reqDraft=function(sid,qi,rk){
  const s=S.sites[sid],q=QUESTS[qi],r=q.req.find(x=>x.k===rk);const rs=reqOf(s,q.k,rk);
  if(r.gate){moneyDraft(sid,qi);return}
  if(r.type==='doc'&&r.order){
    const facts=q.req.filter(x=>reqOf(s,q.k,x.k).state==='확정').map(x=>`- ${x.n} : ${reqOf(s,q.k,x.k).value}`).join('\n')||'- (확정된 값 없음 — 아래 [ ] 를 채워 주십시오)';
    const text=`[작업의뢰서 초안 · ${r.order}]\n현장 : ${s.name}${s.rooms?' ('+s.rooms+'실)':''}\n건명 : ${q.n}\n의뢰 내용 :\n${facts}\n- 수량 : [        ]\n- 규격·형번 : [        ]\n- 납기 : [        ]  (근거 : ${r.how})\n- 현장 주소·인수자 : [        ]\n첨부 : 도면 Rev [  ] · 수량표 [  ]\n의뢰 : 배성윤  결재 : [  ]\n\n※ 이 초안은 앱이 만든 것입니다. 「맞아」 를 주시면 원틀 양식으로 완성해 드립니다.`;
    draftSheet(r.n+' · 초안',text,s.name);
    queue(`만들기,${s.name},${r.n},초안 요청,${rs.value||''}`,s.name,'만들기');
    return;
  }
  const to=r.who.includes('→')?r.who.split('→')[1].trim():r.who;
  const text=`제목 : [${s.name}] ${r.n} 확인 요청\n\n${to} 담당자님, 한국마이크로닉 배성윤입니다.\n\n${s.name} 현장 객실관리 공정을 진행하려면 「${r.n}」 이 확정되어야 합니다.\n${rs.state==='추정'?`- 현재 저희가 파악한 값 : ${rs.value} (${rs.basis||'구두'}) — 맞는지 확인 부탁드립니다.\n`:'- 확인 요청 : [        ]\n'}- 필요한 이유 : ${r.why}\n- 회신 부탁 기한 : [        ]\n- 확정되면 저희가 바로 : ${q.out}\n\n확인 회신 주시면 그대로 진행하겠습니다. 감사합니다.\n\n한국마이크로닉(주) 배성윤 차장\n객실관리시스템(RCU/BSP/CB 제어분전함) 설계·시공\n전화 [        ]  메일 [        ]`;
  draftSheet(r.n+' · 확인 요청 문안',text,s.name);
};
window.moneyDraft=function(sid,qi){
  const s=S.sites[sid],q=QUESTS[qi];
  const made={'외함':'CB외함','속판':'제어분전함(속판)','기구물제작':'객실 기구물'}[q.k]||q.n;
  const con=reqOf(s,'계약','계약완료'), form=reqOf(s,'계약','계약형태');
  const text=`제목 : [${s.name}] ${made} 제작 착수 전 계약 · 계산서 요청\n\n담당자님, 한국마이크로닉 배성윤입니다.\n\n${s.name} 현장 ${made} 제작에 들어가려 합니다. 착수 전에 아래 두 가지를 부탁드립니다.\n\n1. 계약\n   - 현재 상태 : ${con.state==='확정'?'계약 완료 ('+(con.value||'')+')':'미완료'}${form.value?'\n   - 계약 형태 : '+form.value:''}\n   - 계약서(또는 발주서)를 보내 주시면 즉시 제작 의뢰를 넣겠습니다.\n\n2. 계산서\n   - 구분 : ${made} 분 [선금 / 기성 / 납품]\n   - 금액 : [        ]\n   - 발행 요청일 : [        ]\n   - 사업자 정보·발행 이메일 : [        ]\n\n제작 기간이 ${q.k==='속판'?'약 2개월':q.k==='외함'?'약 2주':'약 1.5~2개월'} 걸리므로, 계약이 늦어지면 현장 일정에 그대로 영향이 갑니다.\n회신 주시는 대로 진행하겠습니다. 감사합니다.\n\n한국마이크로닉(주) 배성윤 차장\n객실관리시스템(RCU/BSP/CB 제어분전함) 설계·시공\n전화 [        ]  메일 [        ]`;
  draftSheet('계약 · 계산서 요청 · '+s.name,text,s.name);
  queue(`요청,${safe(s.name)},${safe(made)} 계약·계산서 요청 문안,만듦,앱`,s.name,'요청');
};
window.reqCall=function(sid,qi,rk){
  const s=S.sites[sid],q=QUESTS[qi],r=q.req.find(x=>x.k===rk);const rs=reqOf(s,q.k,rk);
  const text=`전화 첫마디\n\n"${r.who} 담당자님, 마이크로닉 배성윤입니다. ${s.name} 건으로 한 가지만 확인드리려고요.\n${r.n} 이 ${rs.state==='추정'?'저희는 '+rs.value+' 로 알고 있는데 맞는지':'아직 저희가 못 받았는데 언제쯤 정해지는지'} 여쭙고 싶습니다.\n그게 정해져야 저희가 ${q.out.split(' · ')[0]} 을(를) 바로 진행할 수 있어서요."\n\n끊고 나서 → 이 열쇠에 「들은 대로 한 줄 🎙」`;
  draftSheet(r.n+' · 전화',text,s.name);
};
window.reqNote=function(sid,qi,rk){
  const s=S.sites[sid],q=QUESTS[qi],r=q.req.find(x=>x.k===rk);
  micSheet(r.n+' · 들은 대로','상대가 말한 것을 그대로. 값이 나왔으면 다음에 「확정」 으로 올립니다.','',v=>{if(!v)return;s.req=s.req||{};const cur=s.req[q.k+'/'+rk]||{};s.req[q.k+'/'+rk]={...cur,state:cur.state||'진행중',value:cur.value||v,basis:(cur.basis?cur.basis+' / ':'')+v.slice(0,60),ts:now(),date:ymd()};saveSite(s);queue(`메모,${s.name},${r.n} : ${v}`,s.name,'메모');render();toast('기록했습니다')});
};


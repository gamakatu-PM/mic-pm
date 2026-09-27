/* ============ 오늘 ============ */
function itemsBy(kind){return Object.values(S.items).filter(i=>i.kind===kind)}
function openItems(kind){return itemsBy(kind).filter(i=>!['done','confirmed','cancel','requested'].includes(i.status))}
function whenRank(w){if(!w)return 5;if(w==='오늘')return 0;if(/^\d{4}-\d{2}-\d{2}$/.test(w))return w<=ymd()?0:2;if(w==='이번주')return 3;return 4}
function sortItems(a){return a.sort((x,y)=>whenRank(x.when)-whenRank(y.when)||(x.id>y.id?1:-1))}
function daysSince(iso){if(!iso)return '';const d=Math.floor((Date.now()-new Date(iso).getTime())/86400000);return d>=1?d+'일째':''}
function renderToday(){
  const ask=sortItems(openItems('ask')), todo=sortItems(openItems('todo')), make=sortItems(openItems('make'));
  const doneToday=Object.values(S.items).filter(i=>['done','confirmed','requested'].includes(i.status)&&(i.updated||'').slice(0,10)===ymd());
  const openAsk=Object.values(S.asks||{}).filter(a=>a.who==='클로드'&&a.status!=='답함'&&a.status!=='닫힘').length;
  const lateN=lateList().filter(x=>x.d<=7).length;
  document.getElementById('todayChips').innerHTML=(lateN?`<button class="chip ask" onclick="scrollTo(0,0)">늦으면 안 됨 ${lateN}</button>`:'')+(openAsk?`<button class="chip ask" onclick="view='ask';render()">창고에 답할 것 ${openAsk}</button>`:'')+
    `<span class="chip ask">답해 주십시오 ${ask.length}</span><span class="chip ok">오늘 할 것 ${todo.filter(t=>whenRank(t.when)===0).length}</span><span class="chip acc">제가 만들까요 ${make.length}</span><span class="chip">끝낸 것 ${doneToday.length}</span>`;
  let h='';
  if(!ask.length&&!todo.length&&!make.length){
    h+=`<div class="notice">아직 줄이 없습니다. <b>설정 › 아침 한 장 가져오기</b>에 PC가 보낸 [KM] 메일 글을 붙이시면 여기에 카드가 됩니다. 클로드와 연결되면 클로드가 직접 채워 넣기도 합니다.</div>`;
  }
  const late=lateList();
  if(late.length){
    h+=`<h2 class="sec">늦으면 안 되는 것 <small>준공일·납품일에서 거꾸로 센 것</small></h2>`;
    h+=late.slice(0,8).map(x=>`<div class="card" style="border-color:${x.d<0?'var(--ask)':x.d<=7?'var(--warn)':'var(--line)'}" onclick="curSite='${x.s.id}';view='map';render();openReqByKey('${x.s.id}','${x.key}')">
      <div class="id">${esc(x.s.name)} · ${esc(x.date)} 까지 · ${esc(x.why)}</div>
      <div class="t">${esc(x.r?x.r.n:x.key)} ${duePill(x)}</div>
      <div class="m">${esc(x.r&&x.r.how?x.r.how.slice(0,70):'')}</div></div>`).join('');
    if(late.length>8)h+=`<div class="small" style="padding:4px">그 밖 ${late.length-8}건</div>`;
  }
  h+=`<h2 class="sec">답해 주십시오 <small>확인 전에는 전부 제안</small></h2>`;
  h+=ask.length?ask.map(cardAsk).join(''):`<div class="empty">없음</div>`;
  h+=`<h2 class="sec">오늘 할 것 <small>확정 · 문안이 붙어 있음</small></h2>`;
  h+=todo.length?todo.map(cardTodo).join(''):`<div class="empty">없음</div>`;
  h+=`<h2 class="sec">제가 만들까요? <small>「예」 → 이렇게 만들겠습니다 → 「맞아」</small></h2>`;
  h+=make.length?make.map(cardMake).join(''):`<div class="empty">없음</div>`;
  const q=quietSites();const dr=(S.drops||[]);
  if(q.length||dr.length){
    h+=`<h2 class="sec">연락이 끊긴 곳 <small>회의록·통화 기록 기준</small></h2>`;
    h+=q.slice(0,6).map(x=>`<div class="row" onclick="curSite='${x.s.id}';view='map';render()"><span class="dot d-${x.n>=14?'ask':'warn'}"></span><span class="grow"><b>${esc(x.s.name)}</b><div class="small">${esc(x.s.mainWho||'')}</div></span><span class="pill ${x.n>=14?'p-ask':'p-warn'}">${x.n}일째</span></div>`).join('');
    h+=dr.slice(0,6).map(d=>`<div class="row"><span class="dot d-off"></span><span class="grow"><b>${esc(d.name)}</b><div class="small">${esc(d.about||'')} · ${esc(d.history||'')}</div></span><span class="pill p-off">${esc(d.idle)}</span></div>`).join('');
    if(q.length>6||dr.length>6)h+=`<div class="small" style="padding:4px">그 밖 ${Math.max(0,q.length-6)+Math.max(0,dr.length-6)}곳</div>`;
  }
  if(doneToday.length){h+=`<h2 class="sec">오늘 끝낸 것 ${doneToday.length}</h2>`+doneToday.map(i=>`<div class="card done"><div class="id">${esc(i.id)} · ${esc(i.site)} · <span class="pill p-off">${esc(statusKo(i.status))}</span></div><div class="t">${esc(i.text)}</div></div>`).join('')}
  document.getElementById('todayBody').innerHTML=h;
}
function statusKo(s){return {open:'대기',progress:'진행중',done:'완료',confirmed:'확정',cancel:'취소',requested:'만들기 요청',fixed:'고침'}[s]||s}
function whenPill(w){if(!w)return '';const r=whenRank(w);return `<span class="pill ${r===0?'p-ask':r<=3?'p-warn':'p-off'}">${esc(w)}</span>`}
function cardAsk(i){
  return `<div class="card" data-id="${esc(i.id)}"><div class="id">${esc(i.id)} · ${esc(i.site)} ${whenPill(i.when)} ${i.status==='progress'?'<span class="pill p-acc">진행중</span>':''} <span>${esc(daysSince(i.created))}</span></div>
  <div class="t">${esc(i.text)}</div>${i.memo?`<div class="m">${esc(i.memo)}</div>`:''}${i.to?`<div class="m">→ ${esc(i.to)}</div>`:''}
  ${i.fix?`<div class="fix">원래 → 고치신 것 : ${esc(i.fix)}</div>`:''}
  <div class="btns"><button class="b" onclick="act('${esc(i.id)}','progress')">진행중</button><button class="b" onclick="act('${esc(i.id)}','done')">완료</button><button class="b pri" onclick="act('${esc(i.id)}','confirmed')">맞아</button><button class="b mic" onclick="actNo('${esc(i.id)}')">아니야 🎙</button><button class="b" onclick="actMake('${esc(i.id)}')">만들어줘</button></div></div>`;
}
function cardTodo(i){
  return `<div class="card" data-id="${esc(i.id)}"><div class="id">${esc(i.id)} · ${esc(i.site)} ${whenPill(i.when)} <span class="pill p-ok">확정</span></div>
  <div class="t">${esc(i.text)}</div>${i.to?`<div class="m">→ ${esc(i.to)}</div>`:''}${i.memo?`<div class="m">${esc(i.memo)}</div>`:''}
  <div class="btns"><button class="b pri" onclick="showDraft('${esc(i.id)}')">문안</button><button class="b" onclick="act('${esc(i.id)}','done')">완료</button><button class="b" onclick="act('${esc(i.id)}','progress')">진행중</button><button class="b mic" onclick="actNo('${esc(i.id)}')">아니야 🎙</button></div></div>`;
}
function cardMake(i){
  return `<div class="card" data-id="${esc(i.id)}"><div class="id">${esc(i.id)} · ${esc(i.site)} ${whenPill(i.when)}</div>
  <div class="t">${esc(i.makeq||('제가 '+i.text+' 만들까요?'))}</div>${i.text&&i.makeq?`<div class="m">할 일 : ${esc(i.text)}</div>`:''}
  <div class="btns"><button class="b pri" onclick="actYes('${esc(i.id)}')">예</button><button class="b" onclick="act('${esc(i.id)}','cancel')">아니</button><button class="b" onclick="act('${esc(i.id)}','progress')">나중에</button></div></div>`;
}
function replyLine(i,word,val){
  const num=/^KM-\d+$/.test(i.id)?i.id:null;
  if(num)return `${num} ${word}${val?' '+val:''}`;
  return `${i.site} · ${i.text} → ${word}${val?' '+val:''}`;
}
window.act=function(id,status){
  const i=S.items[id];if(!i)return;
  const word={progress:'진행중',done:'완료',confirmed:'맞아',cancel:'취소'}[status];
  i.history=(i.history||[]).concat([{ts:now(),from:i.status,to:status}]);
  i.status=status;saveItem(i);queue(replyLine(i,word),i.site,'회신');render();toast(word+' — 보내기에 담았습니다');
};
window.actNo=function(id){
  const i=S.items[id];if(!i)return;
  micSheet('아니야 — 어떻게 고칠까요?','원래 글은 지우지 않고 「원래 → 고치신 것」 으로 남습니다. 이 값이 제 추정을 이깁니다.','',v=>{
    if(!v)return;i.history=(i.history||[]).concat([{ts:now(),from:i.status,to:'fixed',fix:v}]);i.fix=v;i.status='progress';saveItem(i);
    queue(replyLine(i,'아니야',v),i.site,'수정');render();toast('고치신 것을 담았습니다');
  });
};
window.actMake=function(id){
  const i=S.items[id];if(!i)return;
  openSheet(`<div class="hint">바로 만들지 않습니다. 「맞아」 를 누르시면 만들기 요청이 PC·클로드로 갑니다.</div>
  <pre class="draft">${esc(makePlan(i))}</pre>
  <div class="btns"><button class="b pri" id="mkOk">맞아, 만들어</button><button class="b mic" id="mkFix">다르게 🎙</button><button class="b ghost" id="mkX">취소</button></div>`,'이렇게 만들겠습니다');
  document.getElementById('mkOk').onclick=()=>{i.status='requested';saveItem(i);queue(replyLine(i,'만들어줘'),i.site,'만들기');closeSheet();render();toast('만들기 요청을 담았습니다')};
  document.getElementById('mkFix').onclick=()=>{closeSheet();micSheet('어떻게 다르게?','',(v)=>{if(!v)return;i.status='requested';i.fix=v;saveItem(i);queue(replyLine(i,'만들어줘',v),i.site,'만들기');render()})};
  document.getElementById('mkX').onclick=closeSheet;
};
window.actYes=function(id){actMake(id)};
function makePlan(i){
  const what=(i.makeq||'').replace(/^제가\s*/,'').replace(/\s*만들까요\?*$/,'')||i.text;
  return `현장 : ${i.site}\n만들 것 : ${what}\n근거 : ${i.text}${i.memo?'\n메모 : '+i.memo:''}\n\n형식 : 회사 원틀(정답본) 그대로, 값만 채움\n채울 칸 : 금액·수량·기한은 [ ] 로 비워 두고 프로님이 채움\n나오는 것 : 편집용 파일 + 보낼 메일 제목·본문\n언제 : 다음 아침 한 장에 「제가 이렇게 만들겠습니다」 로 먼저 띄우고, 맞아 → 만듦`;
}
window.showDraft=function(id){
  const i=S.items[id];if(!i)return;
  const to=i.to||'[받는 곳]';
  const text=`제목 : [${i.site}] ${i.text}\n\n${to} 담당자님, 한국마이크로닉 배성윤입니다.\n\n${i.site} 현장 「${i.text}」 건으로 연락드립니다.\n${i.memo?'- '+i.memo.replace(/\n/g,'\n- ')+'\n':''}- 요청 사항 : [        ]\n- 필요 시점 : [        ] (사유 : [        ])\n- 첨부 : [        ]\n\n확인되시면 회신 부탁드립니다. 감사합니다.\n\n한국마이크로닉(주) 배성윤 차장\n객실관리시스템(RCU/BSP/CB 제어분전함) 설계·시공\n전화 [        ]  메일 [        ]`;
  draftSheet('문안 · '+i.id,text,i.site,()=>act(id,'done'));
};


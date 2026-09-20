/* ============ 회의 ============ */
function renderMeet(){
  const body=document.getElementById('meetBody');
  const m=curMeet&&S.meetings[curMeet];
  if(!m){
    const past=Object.values(S.meetings).sort((a,b)=>(b.created>a.created?1:-1));
    body.innerHTML=`<div class="notice">회의 중 또는 회의 뒤 차 안에서, 바뀐 것만 단추로 찍습니다. 「회의 끝」 을 누르면 초안 5종이 나옵니다. PLAUD 회의록은 밤에 PC가 대조합니다.</div>
    <div class="card"><div class="t">새 회의</div><label class="f">현장</label><select id="mtSite">${Object.values(S.sites).map(s=>`<option>${esc(s.name)}</option>`).join('')}<option value="__new">+ 새 현장…</option></select>
    <label class="f">참석</label><div class="chips" id="mtParties">${LISTS.PARTIES.map(p=>`<button class="chip" data-p="${p}" onclick="this.classList.toggle('sel')">${p}</button>`).join('')}</div>
    <div class="btns"><button class="b pri" id="mtStart">회의 시작</button></div></div>
    ${past.length?`<h2 class="sec">지난 회의</h2>`+past.slice(0,20).map(x=>`<div class="card" onclick="curMeet='${x.id}';render()"><div class="id">${esc(x.created.slice(0,16).replace('T',' '))} ${x.ended?'<span class="pill p-off">끝</span>':'<span class="pill p-acc">진행중</span>'}</div><div class="t">${esc(x.site)} · ${(x.attendees||[]).join('·')}</div><div class="m">변경 ${x.changes.length} · 일정 ${x.sched.length} · 메모 ${x.notes.length}</div></div>`).join(''):''}`;
    document.getElementById('mtStart').onclick=()=>{
      let site=document.getElementById('mtSite').value;
      if(site==='__new'){site=prompt('현장명');if(!site)return;ensureSite(site);saveSite(S.sites[siteId(site)])}
      if(!site){toast('현장을 먼저 추가해 주십시오');return}
      const att=[...document.querySelectorAll('#mtParties .chip.sel')].map(b=>b.dataset.p);
      const id='m_'+Date.now();const mm={id,site,attendees:att,changes:[],sched:[],bound:[],notes:[],ended:'',created:now(),updated:now()};saveMeet(mm);curMeet=id;render();
    };
    return;
  }
  let h=`<div class="btns" style="margin-top:0"><button class="b ghost" onclick="curMeet=null;render()">‹ 회의 목록</button></div>
  <div class="card"><div class="id">${esc(m.created.slice(0,16).replace('T',' '))} ${m.ended?'<span class="pill p-off">끝 '+esc(m.ended.slice(11,16))+'</span>':'<span class="pill p-acc">진행 중</span>'}</div><div class="t" style="font-size:1.05rem">${esc(m.site)}</div><div class="m">참석 : ${(m.attendees||[]).join(' · ')||'[ ]'}</div></div>`;
  h+=`<h2 class="sec">수량 · 규격 <small>누르면 전→후</small></h2><div class="chips">${LISTS.ITEMS_MEET.map(k=>`<button class="chip" onclick="mtChange('${m.id}','${k}')">${k}</button>`).join('')}<button class="chip" onclick="mtChange('${m.id}','')">+ 기타</button></div>`;
  h+=m.changes.length?m.changes.map((c,ix)=>`<div class="row"><span class="grow"><b>${esc(c.item)}</b> <span class="mono">${esc(c.from||'?')} → ${esc(c.to)}</span>${c.spec?'<div class="small">'+esc(c.spec)+'</div>':''}</span><span class="pill ${c.sure==='확정'?'p-ok':'p-warn'}" onclick="mtToggle('${m.id}','changes',${ix})">${esc(c.sure)}</span>${m.ended?'':`<button class="b sm ghost" onclick="mtDel('${m.id}','changes',${ix})">✕</button>`}</div>`).join(''):`<div class="empty">아직 없음</div>`;
  h+=`<h2 class="sec">일정</h2><div class="btns" style="margin:0 0 6px"><button class="b" onclick="mtSched('${m.id}')">+ 단계 · 날짜</button></div>`;
  h+=m.sched.length?m.sched.map((c,ix)=>`<div class="row"><span class="grow"><b>${esc(c.label)}</b> <span class="mono">${esc(c.date)}</span>${c.note?'<div class="small">'+esc(c.note)+'</div>':''}</span><span class="pill ${c.sure==='확정'?'p-ok':'p-warn'}" onclick="mtToggle('${m.id}','sched',${ix})">${esc(c.sure)}</span></div>`).join(''):`<div class="empty">아직 없음</div>`;
  h+=`<h2 class="sec">경계 (누가 무엇을)</h2><div class="btns" style="margin:0 0 6px"><button class="b" onclick="mtBound('${m.id}')">+ 경계</button></div>`;
  h+=m.bound.length?m.bound.map((c,ix)=>`<div class="row"><span class="grow"><b>${esc(c.item)}</b> = ${esc(c.who)}</span><span class="pill ${c.sure==='확정'?'p-ok':'p-warn'}" onclick="mtToggle('${m.id}','bound',${ix})">${esc(c.sure)}</span></div>`).join(''):`<div class="empty">아직 없음</div>`;
  h+=`<h2 class="sec">메모 (말한 대로)</h2><div class="btns" style="margin:0 0 6px"><button class="b mic" onclick="mtNote('${m.id}')">🎙 한 줄</button></div>`;
  h+=m.notes.length?m.notes.map(n=>`<div class="row"><span class="grow"><span class="small mono">${esc(n.ts.slice(11,16))}</span> ${esc(n.text)}</span></div>`).join(''):`<div class="empty">아직 없음</div>`;
  h+=`<div class="btns" style="margin-top:16px">${m.ended?`<button class="b pri" onclick="mtDrafts('${m.id}')">초안 5종 다시 보기</button>`:`<button class="b pri" onclick="mtEnd('${m.id}')">회의 끝 → 초안 5종</button>`}</div>`;
  body.innerHTML=h;
}
window.mtChange=function(mid,item){const m=S.meetings[mid];
  openSheet(`<label class="f">품목</label><input id="chItem" value="${esc(item)}" placeholder="품목"><div class="grid"><div><label class="f">전 (도면·견적)</label><input id="chFrom" inputmode="numeric" placeholder="[ ]"></div><div><label class="f">후 (회의)</label><input id="chTo" inputmode="numeric" placeholder="[ ]"></div></div><label class="f">규격·메모 (선택)</label><input id="chSpec"><label class="f">누가 말했나</label><select id="chSure"><option>확정</option><option>추정</option></select><div class="hint" style="margin-top:6px">상대가 말한 것=확정, 제가 짐작한 것=추정</div><div class="btns"><button class="b pri" id="chOk">넣기</button><button class="b ghost" id="chX">취소</button></div>`,'수량 · 규격 변경');
  document.getElementById('chOk').onclick=()=>{const c={item:document.getElementById('chItem').value.trim(),from:document.getElementById('chFrom').value.trim(),to:document.getElementById('chTo').value.trim(),spec:document.getElementById('chSpec').value.trim(),sure:document.getElementById('chSure').value};if(!c.item||!c.to)return;m.changes.push(c);saveMeet(m);closeSheet();render()};
  document.getElementById('chX').onclick=closeSheet};
window.mtSched=function(mid){const m=S.meetings[mid];
  openSheet(`<label class="f">단계</label><select id="scKey">${STAGES.map(([k,l])=>`<option value="${k}">${l}</option>`).join('')}<option value="기타">기타</option></select><label class="f">날짜</label><input type="date" id="scDate" value="${ymd()}"><label class="f">메모</label><input id="scNote"><label class="f">누가 말했나</label><select id="scSure"><option>확정</option><option>추정</option></select><div class="btns"><button class="b pri" id="scOk">넣기</button><button class="b ghost" id="scX">취소</button></div>`,'일정');
  document.getElementById('scOk').onclick=()=>{const k=document.getElementById('scKey').value;const st=STAGES.find(x=>x[0]===k);m.sched.push({key:k,label:st?st[1]:'기타',date:document.getElementById('scDate').value,note:document.getElementById('scNote').value.trim(),sure:document.getElementById('scSure').value});saveMeet(m);closeSheet();render()};
  document.getElementById('scX').onclick=closeSheet};
window.mtBound=function(mid){const m=S.meetings[mid];
  openSheet(`<label class="f">항목</label><select id="bdItem">${LISTS.BOUND.map(b=>`<option>${b}</option>`).join('')}</select><label class="f">누가</label><select id="bdWho">${['한국마이크로닉','전기','통신','건축','설비','발주처','미정'].map(o=>`<option>${o}</option>`).join('')}</select><label class="f">누가 말했나</label><select id="bdSure"><option>확정</option><option>추정</option></select><div class="btns"><button class="b pri" id="bdOk">넣기</button><button class="b ghost" id="bdX">취소</button></div>`,'경계');
  document.getElementById('bdOk').onclick=()=>{m.bound.push({item:document.getElementById('bdItem').value,who:document.getElementById('bdWho').value,sure:document.getElementById('bdSure').value});saveMeet(m);closeSheet();render()};
  document.getElementById('bdX').onclick=closeSheet};
window.mtNote=function(mid){const m=S.meetings[mid];micSheet('메모 · 말한 대로','들은 그대로. 고치지 않습니다.','',v=>{if(!v)return;m.notes.push({ts:now(),text:v});saveMeet(m);render()})};
window.mtToggle=function(mid,arr,ix){const m=S.meetings[mid];if(m.ended)return;const c=m[arr][ix];c.sure=c.sure==='확정'?'추정':'확정';saveMeet(m);render()};
window.mtDel=function(mid,arr,ix){const m=S.meetings[mid];m[arr].splice(ix,1);saveMeet(m);render()};
window.mtEnd=function(mid){const m=S.meetings[mid];m.ended=now();saveMeet(m);
  const s=ensureSite(m.site);
  // 현장 반영 + 보내기 줄
  const att=(m.attendees||[]).join('·')||'회의';
  let touched=0;
  m.changes.forEach(c=>{
    queue(`회의,${safe(m.site)},${safe(c.item)},${safe((c.from||'?')+'→'+c.to)},${c.sure},${safe(att)}`,m.site,'회의');
    if(setReq(s,itemReqKey(c.item),c.sure==='확정'?'확정':'진행중',`${c.item} ${c.from||'?'}→${c.to}${c.spec?' ('+c.spec+')':''}`,`${m.created.slice(0,10)} ${att} 회의`))touched++;
  });
  m.sched.forEach(c=>{
    const key=STAGE2REQ[c.key];
    if(key&&setReq(s,key,c.sure,c.date,`${m.created.slice(0,10)} ${att} 회의${c.note?' · '+c.note:''}`))touched++;
    else queue(`${c.sure},${safe(m.site)},${safe(c.label)},${safe(c.date)},회의 ${safe(c.note||'')}`,m.site,'일정');
  });
  m.bound.forEach(c=>{s.bound=s.bound||{};s.bound[c.item]={who:c.who,sure:c.sure,ts:now()};queue(`경계,${safe(m.site)},${safe(c.item)},${safe(c.who)},${c.sure}`,m.site,'경계');
    if(c.sure==='확정')saveDecision({site:m.site,item:'경계 · '+c.item,value:c.who,basis:`${m.created.slice(0,10)} ${att} 회의`,source:'경계',by:'프로님'})});
  m.notes.forEach(n=>queue(`메모,${m.site},${n.text}`,m.site,'메모'));
  saveSite(s);render();mtDrafts(mid,touched)};
window.mtDrafts=function(mid,touched){const m=S.meetings[mid];const d=meetDrafts(m);
  openSheet(`<div class="hint">복사해 그룹웨어 의뢰서·메일에 붙이십니다. 단가·금액은 PC 7번이 붙입니다. 이 회의의 줄들은 보내기에 담겼고${touched?`, <b>여정 열쇠 ${touched}개</b>가 갱신되었습니다`:''}.</div>
  ${d.map((x,ix)=>`<h2 class="sec">${ix+1}. ${esc(x.title)}</h2><pre class="draft">${esc(x.text)}</pre><div class="btns" style="margin-top:0"><button class="b sm" onclick="copy(${JSON.stringify(x.text).replace(/"/g,'&quot;')})">복사</button></div>`).join('')}
  <div class="btns"><button class="b pri" id="mdAll">전부 복사</button>${touched?`<button class="b" onclick="closeSheet();curMeet=null;view='map';render()">여정에서 보기</button>`:''}<button class="b ghost" id="mdX">닫기</button></div>`,'회의 끝 · '+m.site);
  document.getElementById('mdAll').onclick=()=>copy(d.map(x=>'■ '+x.title+'\n'+x.text).join('\n\n'));
  document.getElementById('mdX').onclick=closeSheet};
function meetDrafts(m){
  const dt=m.created.slice(0,10), att=(m.attendees||[]).join('·')||'[ ]';
  const chg=m.changes.map(c=>`- ${c.item} : ${c.from||'?'} → ${c.to}${c.spec?' ('+c.spec+')':''} [${c.sure}]`).join('\n')||'- 없음';
  const sch=m.sched.map(c=>`- ${c.label} : ${c.date}${c.note?' · '+c.note:''} [${c.sure}]`).join('\n')||'- 없음';
  const bnd=m.bound.map(c=>`- ${c.item} : ${c.who} [${c.sure}]`).join('\n')||'- 없음';
  const notes=m.notes.map(n=>'- '+n.text).join('\n')||'- 없음';
  const out=[];
  out.push({title:'회의 요약',text:`${m.site} 협의 · ${dt} · 참석 ${att}\n\n[수량·규격]\n${chg}\n\n[일정]\n${sch}\n\n[업무 경계]\n${bnd}\n\n[말한 대로]\n${notes}\n\n※ [확정]=상대가 말한 것 / [추정]=내 판단. 추정은 서면 확인 전까지 확정이 아님`});
  const depts=[];if(m.changes.length){depts.push(['설계팀','수량·규격 변경을 객실관리 도면(배치·계통·CB 배선)에 반영, Rev 올림',chg]);depts.push(['제작팀','아래 수량으로 제작 수량 변경 (이미 발행된 의뢰서와 대조 요망)',chg])}
  if(m.sched.length)depts.push(['시공팀','아래 일정으로 현장 투입 계획 조정',sch]);
  if(m.bound.length)depts.push(['시공팀·구매팀','업무 경계 변경 확인',bnd]);
  out.push({title:'작업의뢰서 본문 (부서별)',text:depts.length?depts.map(([d,why,body])=>`[작업의뢰서 · ${d}]\n현장 : ${m.site}\n의뢰 사유 : ${dt} ${att} 협의 결과\n의뢰 내용 : ${why}\n${body}\n납기 : [        ]\n첨부 : [        ]\n의뢰 : 배성윤`).join('\n\n'):'변경이 없어 의뢰서 없음'});
  out.push({title:'상대 확인 메일',text:`제목 : [${m.site}] ${dt} 협의 내용 확인 요청\n\n${att} 담당자님, 한국마이크로닉 배성윤입니다.\n오늘 협의한 내용을 아래와 같이 정리하였습니다. 다른 부분이 있으면 회신 부탁드립니다. 회신이 없으면 아래대로 진행하겠습니다.\n\n[수량·규격]\n${chg}\n\n[일정]\n${sch}\n\n[업무 경계]\n${bnd}\n\n회신 기한 : [        ]\n감사합니다.\n한국마이크로닉(주) 배성윤 차장  전화 [        ]`});
  out.push({title:'증감 예비표 (단가·금액은 PC 7번)',text:`품목 | 전 | 후 | 증감 | 단가 | 금액\n`+(m.changes.map(c=>{const a=parseFloat(c.from),b=parseFloat(c.to);const d=(isFinite(a)&&isFinite(b))?(b-a):'?';return `${c.item} | ${c.from||'?'} | ${c.to} | ${d} | [PC] | [PC]`}).join('\n')||'없음')+`\n\n※ 요율·단가는 앱이 정하지 않음. 수량은 검토용, 수량표로 확정`});
  const todos=[];if(m.changes.length)todos.push('- 증감 내역 확정 → 발주처·시공사 서면 확인 [기한  ]');if(m.sched.some(c=>c.sure==='추정'))todos.push('- 추정 일정 확인 전화 → '+att);if(m.bound.length)todos.push('- 경계 확인 메일 발송');todos.push('- PLAUD 회의록과 대조 (PC 40번, 밤)');
  out.push({title:'할 일',text:todos.join('\n')});
  return out;
}


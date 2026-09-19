/* ============ 현장 ============ */
function renderSites(){
  const det=document.getElementById('siteDetail'), list=document.getElementById('sitesList');
  if(curSite&&S.sites[curSite]){list.hidden=true;det.hidden=false;renderSiteDetail(S.sites[curSite]);return}
  list.hidden=false;det.hidden=true;
  const cts=(S.contacts||[]).filter(c=>!c.site);
  const q=(document.getElementById('siteSearch').value||'').trim();
  const arr=Object.values(S.sites).filter(s=>!q||s.name.includes(q)).sort((a,b)=>(b.updated||'')>(a.updated||'')?1:-1);
  const head=cts.length?`<div class="feedbar" onclick="contactSheet()"><div><div class="ft">현장을 못 정한 연락처 ${cts.length}명</div><div class="fs">통화 기록에서 나온 분들입니다. 현장을 정해 주시면 그 현장으로 옮깁니다</div></div><span class="b sm pri">보기</span></div>`:'';
  document.getElementById('siteCards').innerHTML=head+(arr.length?arr.map(s=>{
    const st=stageState(s);const cur=st.find(x=>x.status!=='확정')||st[st.length-1];
    const open=Object.values(S.items).filter(i=>i.site===s.name&&!['done','confirmed','cancel','requested'].includes(i.status)).length;
    return `<div class="card" onclick="openSite('${s.id}')"><div class="id">${s.rooms?esc(s.rooms)+'실 · ':''}${s.due?'준공 '+esc(s.due):'준공일 미입력'}</div><div class="t">${esc(s.name)}</div>
    <div class="m"><span class="dot d-${cur.status==='확정'?'ok':cur.status==='추정'?'warn':'off'}" style="display:inline-block;vertical-align:middle;margin-right:4px"></span>${esc(cur.label)} · ${esc(cur.status)}${cur.date?' '+esc(cur.date):''} · 미결 ${open}</div></div>`;
  }).join(''):`<div class="empty">현장이 없습니다. 아침 한 장을 가져오거나 「+ 현장 추가」.</div>`);
}
window.contactSheet=function(){
  const cts=(S.contacts||[]).map((c,i)=>({...c,_i:i})).filter(c=>!c.site).sort((a,b)=>(b.calls||0)-(a.calls||0));
  const opts=Object.values(S.sites).map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('');
  openSheet(`<div class="story">통화는 했는데 이름에 현장이 없어 제가 배정하지 못한 분들입니다. 짐작으로 옮기지 않았습니다. 고르시면 그 현장 「사람」 탭으로 들어갑니다.</div>
  ${cts.slice(0,60).map(c=>`<div class="row"><span class="grow"><b>${esc(c.name||c.org)}</b><div class="small">${esc(c.org||'')} · 통화 ${c.calls||0}건${c.last?' · 최종 '+esc(c.last):''}</div></span>
    <select onchange="assignContact(${c._i},this.value)" style="width:120px"><option value="">현장 고르기</option>${opts}<option value="__new">+ 새 현장</option><option value="__skip">안 씀</option></select>
    ${c.phone?`<a class="b sm" href="tel:${esc(c.phone)}">📞</a>`:''}</div>`).join('')}
  ${cts.length>60?`<div class="small">그 밖 ${cts.length-60}명은 배정 뒤에 보여 드립니다</div>`:''}
  <div class="btns"><button class="b ghost" onclick="closeSheet()">닫기</button></div>`,'현장 못 정한 연락처 '+cts.length+'명');
};
window.assignContact=function(ix,val){
  const c=(S.contacts||[])[ix];if(!c)return;
  if(val==='__skip'){c.site='(안 씀)';saveContacts();closeSheet();render();return}
  let s;
  if(val==='__new'){const n=prompt('현장명');if(!n)return;s=ensureSite(n);saveSite(s)}
  else s=S.sites[val];
  if(!s)return;
  s.people=(s.people||[]).concat([{role:c.role||'미정',name:c.name||c.org,org:c.org||'',phone:c.phone||'',calls:c.calls,last:c.last,from:'프로님이 배정'}]);
  c.site=s.name;saveSite(s);saveContacts();
  queue(`담당자,${safe(s.name)},${safe(c.role||'미정')},${safe(c.name||c.org)},${safe(c.org||'')},${safe(c.phone||'')}`,s.name,'담당자');
  closeSheet();render();toast(s.name+' 으로 옮겼습니다');
};
function saveContacts(){persist();dbWrite('meta/contacts',{lines:S.contacts})}
document.getElementById('siteSearch').oninput=renderSites;
document.getElementById('btnAddSite').onclick=()=>{
  openSheet(`<label class="f">현장명</label><input id="nsName"><div class="grid"><div><label class="f">객실 수</label><input id="nsRooms" inputmode="numeric"></div><div><label class="f">준공일</label><input id="nsDue" type="date"></div></div>
  <div class="btns"><button class="b pri" id="nsOk">추가</button><button class="b ghost" id="nsX">취소</button></div>`,'현장 추가');
  document.getElementById('nsOk').onclick=()=>{const n=document.getElementById('nsName').value.trim();if(!n)return;const s=ensureSite(n);s.rooms=document.getElementById('nsRooms').value.trim();s.due=document.getElementById('nsDue').value;saveSite(s);closeSheet();curSite=s.id;render()};
  document.getElementById('nsX').onclick=closeSheet;
};
function ensureSite(name){const id=siteId(name);if(!S.sites[id]){S.sites[id]={id,name,rooms:'',due:'',stages:{},people:[],facts:[],created:now(),updated:now()}}return S.sites[id]}
window.openSite=function(id){curSite=id;siteTab='공정';render()};
function addDays(iso,n){const d=new Date(iso+'T00:00:00');d.setDate(d.getDate()+n);return ymd(d)}
function isDate(v){return /^\d{4}-\d{2}-\d{2}$/.test(String(v||'').slice(0,10))}
function stageState(s){
  // 진실은 열쇠(req) 하나. 아래 구역만 준공일에서 거꾸로 (시운전 7 → 설치 7 → 빽커버 10 → 벽지 → 제작 60)
  const est={};
  if(s.due){let d=s.due;est['시운전']=addDays(d,-7);est['강전약전']=est['시운전'];est['기구물설치']=addDays(est['시운전'],-7);est['빽커버']=addDays(est['기구물설치'],-10);est['벽지완료']=est['빽커버'];est['기구물제작']=addDays(est['벽지완료'],-60)}
  const doneKeyOf={};Object.keys(REQ2STAGE).forEach(kk=>doneKeyOf[REQ2STAGE[kk]]=kk);
  return STAGES.map(([k,label])=>{
    const dk=doneKeyOf[k], dr=dk?((s.req||{})[dk]||{}):{};
    if(dr.state==='확정')return {key:k,label,status:'확정',date:isDate(dr.value)?dr.value.slice(0,10):(dr.date||''),note:dr.basis||'',reqKey:dk};
    const c=(s.stages||{})[k];
    if(c&&c.date)return {key:k,label,status:'확정',date:c.date,note:c.note||'',reqKey:dk};
    const pk=STAGE2REQ[k], pr=pk?((s.req||{})[pk]||{}):{};
    if(pr.state&&isDate(pr.value))return {key:k,label,status:pr.state==='확정'?'예정':'추정',date:pr.value.slice(0,10),note:pr.basis||'',reqKey:pk};
    if(pr.state)return {key:k,label,status:'진행',date:'',note:pr.value||pr.basis||'',reqKey:pk};
    if(est[k])return {key:k,label,status:'추정',date:est[k],note:'준공일 역산',reqKey:dk||pk};
    return {key:k,label,status:'미확정',date:'',note:'',reqKey:dk||pk};
  });
}
function stageCls(st){return st==='확정'?'ok':st==='예정'?'ok':st==='추정'||st==='진행'?'warn':'off'}
function renderSiteDetail(s){
  const tabs=['공정','사람','기록','돈','검수','경계'];
  let h=`<div class="btns" style="margin-top:0"><button class="b ghost" onclick="curSite=null;render()">‹ 현장 목록</button><button class="b ghost" onclick="editSite('${s.id}')">정보 고치기</button></div>
  <div class="card"><div class="t" style="font-size:1.05rem">${esc(s.name)}</div><div class="kv"><b>객실</b><span>${esc(s.rooms||'[ ]')}</span><b>준공일</b><span>${s.due?esc(s.due)+' <span class="pill p-ok">확정</span>':'[ ] <span class="small">넣으면 아래 추정이 채워집니다</span>'}</span></div></div>
  <div class="tabs2">${tabs.map(t=>`<button class="${t===siteTab?'on':''}" onclick="siteTab='${t}';render()">${t}</button>`).join('')}</div>`;
  if(siteTab==='공정'){
    const st=stageState(s);
    h+=`<div class="btns" style="margin:0 0 6px"><button class="b pri" onclick="view='map';render()">⛳ 여정 지도로 (필요한 것 · 지금 상태)</button></div><div class="notice">단계를 누르면 그 단계의 <b>열쇠</b>가 열립니다. <span class="pill p-ok">확정</span>=끝난 것·상대가 말한 날 <span class="pill p-warn">추정</span>=역산·제 판독 <span class="pill p-off">미확정</span></div><div class="tl">`;
    h+=st.map(x=>`<div class="st" onclick="stageTap('${s.id}','${x.key}')"><span class="dot d-${stageCls(x.status)}"></span><span>${esc(x.label)}${x.note?' <span class="small">'+esc(x.note.slice(0,36))+'</span>':''}</span><span class="dt">${esc(x.status)}${x.date?' '+esc(x.date):''}</span></div>`).join('');
    h+=`</div>`;
    const items=Object.values(S.items).filter(i=>i.site===s.name&&!['done','confirmed','cancel','requested'].includes(i.status));
    if(items.length){h+=`<h2 class="sec">이 현장의 미결 ${items.length}</h2>`+items.map(i=>`<div class="row"><span class="dot d-${i.kind==='todo'?'ok':'ask'}"></span><span class="grow"><span class="pill ${i.kind==='todo'?'p-ok':i.kind==='make'?'p-acc':'p-ask'}">${i.kind==='todo'?'할 것':i.kind==='make'?'만들까요':'제안'}</span> ${esc(i.makeq||i.text)}</span>${whenPill(i.when)}</div>`).join('')}
  }
  if(siteTab==='사람'){
    h+=`<div class="notice">담당자를 누르면 전화가 걸립니다. 통화가 끝나면 「한 줄 남기기」.</div>`;
    h+=(s.people||[]).length?(s.people||[]).map((p,ix)=>`<div class="row"><span class="grow"><b>${esc(p.name)}</b> ${p.role&&p.role!=='미정'?`<span class="pill p-off">${esc(p.role)}</span>`:''}<div class="small">${esc(p.org||'')}${p.calls?' · 통화 '+p.calls+'건'+(p.last?' · 최종 '+esc(p.last):''):''}</div></span>${p.phone?`<a class="b" href="tel:${esc(p.phone.replace(/[^\d+]/g,''))}">📞</a>`:''}<button class="b sm" onclick="noteLine('${s.id}','${esc(p.role)} ${esc(p.name)}')">한 줄</button></div>`).join(''):`<div class="empty">담당자가 없습니다</div>`;
    h+=`<div class="btns"><button class="b" onclick="addPerson('${s.id}')">+ 담당자</button><button class="b mic" onclick="noteLine('${s.id}','')">🎙 한 줄 남기기</button></div>`;
  }
  if(siteTab==='기록'){
    const facts=(s.facts||[]);const logs=S.log.filter(l=>l.site===s.name).slice().reverse();
    h+=`<h2 class="sec">확정 (프로님이 정한 값 · 어떤 추정보다 우선)</h2>`;
    h+=facts.length?facts.slice().reverse().map(f=>`<div class="row"><span class="grow"><span class="small mono">${esc(f.date||'')}</span> <b>${esc(f.item)}</b> = ${esc(f.value)}<div class="small">${esc(f.basis||'')}</div></span></div>`).join(''):`<div class="empty">없음</div>`;
    h+=`<h2 class="sec">한 줄 기록 ${logs.length}</h2>`;
    h+=logs.length?logs.slice(0,60).map(l=>`<div class="row"><span class="grow"><span class="small mono">${esc(l.ts.slice(5,16).replace('T',' '))}</span> <span class="pill p-off">${esc(l.type)}</span> ${esc(l.text)}</span></div>`).join(''):`<div class="empty">없음</div>`;
    h+=`<div class="btns"><button class="b" onclick="addFact('${s.id}')">+ 확정값 넣기</button><button class="b mic" onclick="noteLine('${s.id}','')">🎙 한 줄</button></div>`;
  }
  if(siteTab==='돈'){
    const m=s.money||{};
    h+=`<div class="notice">금액은 프로님만 넣습니다. 납품 완료를 누르면 계산서 시점을 알려 드립니다. (v6.2에서 6번 수금레이더와 연결)</div>`;
    h+=['견적','계약','계산서1 외함','계산서2 속판','계산서3 기구물','수금'].map(k=>{const v=m[k]||{};return `<div class="row"><span class="grow"><b>${k}</b> <span class="small">${v.date?esc(v.date):''}</span></span><input style="width:120px" inputmode="numeric" placeholder="금액 [ ]" value="${esc(v.amt||'')}" onchange="moneySet('${s.id}','${k}','amt',this.value)"><button class="b sm ${v.date?'':'pri'}" onclick="moneySet('${s.id}','${k}','date','${ymd()}')">${v.date?'완료':'완료 표시'}</button></div>`}).join('');
  }
  if(siteTab==='검수'){
    h+=inspHtml(s);
  }
  if(siteTab==='경계'){
    const b=s.bound||{};
    h+=`<div class="notice">「누가 무엇을」. 셀을 바꾸면 경계 줄이 보내기에 담기고, 확인 메일 문안을 만들 수 있습니다. 회의에서 들은 것은 확정, 제 짐작은 추정.</div>`;
    h+=LISTS.BOUND.map(k=>{const v=b[k]||{};return `<div class="row"><span class="grow"><b>${k}</b></span><select style="width:130px" onchange="boundSet('${s.id}','${k}',this.value)"><option value="">[ ]</option>${['한국마이크로닉','전기','통신','건축','설비','발주처','미정'].map(o=>`<option ${v.who===o?'selected':''}>${o}</option>`).join('')}</select>${v.who?`<span class="pill ${v.sure==='확정'?'p-ok':'p-warn'}" onclick="boundSure('${s.id}','${k}')">${esc(v.sure||'추정')}</span>`:''}</div>`}).join('');
    h+=`<div class="btns"><button class="b" onclick="boundDraft('${s.id}')">경계 확인 메일 문안</button></div>`;
  }
  document.getElementById('siteDetail').innerHTML=h;
}
/* ── 검수 · 시운전 : 객실 번호 격자, 탭하면 O → X → 미확인. X 는 하자 한 줄 → 하자 대장 */
const INSP_STAGES=[['외함','외함 설치 검수','외함 위치·높이·타공이 도면과 맞나'],['기구물','기구물 설치 검수','챠임벨·K·DM·온도·L·BSP 가 제자리에 붙었나'],['시운전','시운전','전기 들어온 뒤 품목마다 동작하나']];
function parseRooms(txt){
  const out=[];String(txt||'').split(/[,\s]+/).forEach(t=>{if(!t)return;const m=t.match(/^(\d+)-(\d+)$/);
    if(m){const a=+m[1],b=+m[2];if(b>=a&&b-a<400)for(let i=a;i<=b;i++)out.push(String(i))}else out.push(t)});
  return [...new Set(out)];
}
function inspHtml(s){
  const st=s.inspStage||'시운전';const rooms=s.roomList||[];const data=((s.insp||{})[st])||{};
  const ok=rooms.filter(r=>data[r]&&data[r].ok===true).length, bad=rooms.filter(r=>data[r]&&data[r].ok===false).length;
  let h=`<div class="tabs2">${INSP_STAGES.map(([k,l])=>`<button class="${st===k?'on':''}" onclick="S.sites['${s.id}'].inspStage='${k}';saveSite(S.sites['${s.id}']);render()">${l}</button>`).join('')}</div>
  <div class="notice">${esc(INSP_STAGES.find(x=>x[0]===st)[2])}. 객실을 누르면 <b>O → X → 미확인</b> 으로 돌아갑니다. X 는 한 줄이 하자 대장으로 갑니다.</div>`;
  if(!rooms.length){
    h+=`<div class="card"><div class="t">객실 번호를 넣어 주십시오</div><div class="m">「301-320, 401-420」 처럼 범위로 적으시면 격자가 됩니다. 한 번만 넣으면 세 검수가 같이 씁니다.</div>
      <textarea id="roomTxt" placeholder="301-320, 401-420, 501">${esc(s.roomTxt||'')}</textarea>
      <div class="btns"><button class="b pri" onclick="setRooms('${s.id}')">격자 만들기</button></div></div>`;
    return h;
  }
  h+=`<div class="card"><div class="jhead"><div><div class="t" style="margin:0">${esc(INSP_STAGES.find(x=>x[0]===st)[1])}</div><div class="small">O ${ok} · X ${bad} · 미확인 ${rooms.length-ok-bad} / ${rooms.length}실</div></div><div class="pct">${Math.round(ok/rooms.length*100)}%</div></div>
    <div class="bar"><i style="width:${Math.round(ok/rooms.length*100)}%"></i></div>
    <div class="grid9" style="margin-top:10px">${rooms.map(r=>{const c=data[r]||{};const cls=c.ok===true?'c-ok':c.ok===false?'c-x':'';return `<span class="cell ${cls}" onclick="inspTap('${s.id}','${esc(r)}')">${esc(r)}</span>`}).join('')}</div>
    <div class="btns"><button class="b" onclick="inspAll('${s.id}',true)">전부 O</button><button class="b ghost" onclick="S.sites['${s.id}'].roomList=null;saveSite(S.sites['${s.id}']);render()">객실 번호 다시</button></div></div>`;
  const defects=rooms.filter(r=>data[r]&&data[r].ok===false);
  if(defects.length){h+=`<h2 class="sec">하자 ${defects.length} <small>X 인 객실</small></h2>`+defects.map(r=>`<div class="row"><span class="grow"><b>${esc(r)}호</b> ${esc((data[r].note||'').slice(0,60))}</span><button class="b sm" onclick="inspNote('${s.id}','${esc(r)}')">🎙</button></div>`).join('')
    +`<div class="btns"><button class="b pri" onclick="asDraft('${s.id}')">시공팀 AS 의뢰서 초안</button></div>`}
  if(ok===rooms.length&&st==='시운전'){h+=`<div class="card next"><div class="id">시운전 100%</div><div class="t">계산서 시점입니다</div><div class="btns"><button class="b pri" onclick="finishTest('${s.id}')">시운전 완료로 확정</button><button class="b" onclick="moneyDraftSimple('${s.id}')">제가 계산서 요청 문안 만들까요?</button></div></div>`}
  return h;
}
window.setRooms=function(sid){const s=S.sites[sid];const t=document.getElementById('roomTxt').value;const r=parseRooms(t);
  if(!r.length){toast('객실 번호를 못 읽었습니다');return}s.roomTxt=t;s.roomList=r;if(!s.rooms)s.rooms=String(r.length);saveSite(s);render();toast(r.length+'실 격자를 만들었습니다')};
window.inspTap=function(sid,r){const s=S.sites[sid];const st=s.inspStage||'시운전';s.insp=s.insp||{};s.insp[st]=s.insp[st]||{};
  const c=s.insp[st][r]||{};const nx=c.ok===true?false:c.ok===false?null:true;
  s.insp[st][r]={...c,ok:nx,ts:now()};saveSite(s);render();
  if(nx===false)inspNote(sid,r);};
window.inspNote=function(sid,r){const s=S.sites[sid];const st=s.inspStage||'시운전';
  micSheet(`${r}호 · 무엇이 안 됩니까?`,'품목과 증상을 말씀하시면 하자 대장으로 갑니다. 사진은 나중에 붙여도 됩니다.',(s.insp[st][r]||{}).note||'',v=>{
    if(!v)return;s.insp[st][r].note=v;saveSite(s);queue(`하자,${safe(s.name)},${safe(r)},${safe(v)},${st}`,s.name,'하자');render()})};
window.inspAll=function(sid,val){const s=S.sites[sid];const st=s.inspStage||'시운전';if(!confirm('전부 O 로 표시할까요?'))return;
  s.insp=s.insp||{};s.insp[st]=s.insp[st]||{};(s.roomList||[]).forEach(r=>{s.insp[st][r]={...(s.insp[st][r]||{}),ok:val,ts:now()}});saveSite(s);render()};
window.finishTest=function(sid){const s=S.sites[sid];setReq(s,'시운전/시운전완료','확정',ymd(),'검수 화면 100% · 프로님 확정');saveSite(s);render();cheer(s,QUESTS.find(q=>q.k==='시운전'),QUESTS.findIndex(q=>q.k==='시운전'))};
window.moneyDraftSimple=function(sid){const s=S.sites[sid];
  const text=`제목 : [${s.name}] 시운전 완료 · 계산서 발행 요청\n\n담당자님, 한국마이크로닉 배성윤입니다.\n\n${s.name} 현장 객실관리 시운전이 완료되었습니다(${ymd()}, ${(s.roomList||[]).length}실).\n아래와 같이 계산서 발행을 요청드립니다.\n\n- 구분 : 기구물 납품·시운전 완료분\n- 금액 : [        ]\n- 발행 요청일 : [        ]\n- 사업자 정보·발행 이메일 : [        ]\n- 첨부 : 시운전 확인서 · 사진대지\n\n감사합니다.\n한국마이크로닉(주) 배성윤 차장  전화 [        ]`;
  draftSheet('계산서 요청 · '+s.name,text,s.name)};
window.asDraft=function(sid){const s=S.sites[sid];const st=s.inspStage||'시운전';const d=s.insp[st]||{};
  const rows=(s.roomList||[]).filter(r=>d[r]&&d[r].ok===false).map(r=>`- ${r}호 : ${d[r].note||'[증상  ]'}`).join('\n');
  const text=`[작업의뢰서 초안 · 시공팀 AS]\n현장 : ${s.name}\n건명 : ${INSP_STAGES.find(x=>x[0]===st)[1]} 하자 처리\n의뢰 내용 :\n${rows}\n- 방문 희망일 : [        ]\n- 현장 연락 : [        ]\n첨부 : 사진 [  ]장\n의뢰 : 배성윤`;
  draftSheet('AS 의뢰서 초안 · '+s.name,text,s.name);queue(`만들기,${safe(s.name)},AS 의뢰서 초안,하자 ${rows.split('\n').length}건,앱`,s.name,'만들기')};

window.editSite=function(id){const s=S.sites[id];openSheet(`<label class="f">현장명 <span class="small">제가 통화 기록에서 뽑은 이름이라 틀릴 수 있습니다. 고치시면 그 이름을 씁니다</span></label><input id="esName" value="${esc(s.name)}"><div class="grid"><div><label class="f">객실 수</label><input id="esRooms" value="${esc(s.rooms||'')}" inputmode="numeric"></div><div><label class="f">준공일</label><input id="esDue" type="date" value="${esc(s.due||'')}"></div></div>
  <h2 class="sec">이 현장 소요일 <small>비우면 기본값(전 현장 공통)</small></h2>
  <div class="grid">${[['외함제작','외함 제작(일)'],['속판제작','속판 제작(일)'],['기구물제작','기구물 제작(일)'],['빽커버','빽커버(일)'],['기구물설치','기구물 설치(일)'],['시운전','시운전(일)'],['강전','강전 접속(일)'],['마감여유','준공 전 여유(일)']].map(([k,l])=>`<div><label class="f">${l} <span class="small">기본 ${LEAD[k]}</span></label><input id="ld_${k}" inputmode="numeric" value="${esc(String(((s.lead||{})[k])||''))}" placeholder="${LEAD[k]}"></div>`).join('')}</div>
  <div class="btns"><button class="b pri" id="esOk">저장</button><button class="b ghost" id="esX">취소</button></div>`,'현장 정보');
  document.getElementById('esOk').onclick=()=>{const due=document.getElementById('esDue').value;
    const nn=document.getElementById('esName').value.trim();
    if(nn&&nn!==s.name){const old=s.name;Object.values(S.items).forEach(i=>{if(i.site===old){i.site=nn;saveItem(i)}});
      Object.values(S.meetings).forEach(m=>{if(m.site===old){m.site=nn;saveMeet(m)}});
      queue(`현장명,${safe(old)},→,${safe(nn)},프로님이 고치심`,nn,'현장명');s.name=nn;s.renamedFrom=old}
    if(due&&due!==s.due){queue(`확정,${safe(s.name)},준공일,${safe(due)},앱 입력`,s.name,'확정');saveDecision({site:s.name,item:'준공일',value:due,basis:'앱 입력',source:'현장정보',by:'프로님',prev:s.due?{value:s.due}:null})}
    const lead={};Object.keys(LEAD).forEach(k=>{const el=document.getElementById('ld_'+k);const v=el?parseInt(el.value,10):NaN;if(!isNaN(v)&&v>0&&v!==LEAD[k])lead[k]=v});
    if(JSON.stringify(lead)!==JSON.stringify(s.lead||{})){s.lead=lead;const leadTxt=Object.keys(lead).map(k=>k+' '+lead[k]+'일').join(' · ')||'기본값';queue('소요일,'+safe(s.name)+','+safe(leadTxt)+',현장별,앱',s.name,'소요일')}
    s.rooms=document.getElementById('esRooms').value.trim();s.due=due;saveSite(s);closeSheet();render();toast('저장했습니다')};
  document.getElementById('esX').onclick=closeSheet};
window.stageTap=function(sid,key){
  const s=S.sites[sid];
  const _st=stageState(s).find(x=>x.key===key);
  if(_st&&_st.reqKey){const pr=_st.reqKey.split('/');const qi=QUESTS.findIndex(q=>q.k===pr[0]);if(qi>=0){view='map';curSite=sid;render();reqSheet(sid,qi,pr[1]);return}}
  const label=STAGES.find(x=>x[0]===key)[1];const cur=(s.stages||{})[key]||{};
  openSheet(`<h3>${esc(label)}</h3><div class="hint">완료된 날짜를 넣으면 「확정」 이 되어 확정 대장에 들어갑니다. 역산 추정을 이깁니다.</div>
  <label class="f">완료일</label><input type="date" id="stDate" value="${esc(cur.date||ymd())}"><label class="f">근거 (선택)</label><input id="stNote" value="${esc(cur.note||'')}" placeholder="현장 확인 / 홍부장 통화 …">
  <div class="btns"><button class="b pri" id="stOk">확정</button>${cur.date?'<button class="b" id="stClr">확정 지우기(미확정으로)</button>':''}<button class="b ghost" id="stX">취소</button></div>`);
  document.getElementById('stOk').onclick=()=>{const d=document.getElementById('stDate').value;if(!d)return;const n=document.getElementById('stNote').value.trim();s.stages=s.stages||{};s.stages[key]={date:d,note:n,ts:now()};saveSite(s);queue(`확정,${s.name},${label},${d},${n||'앱 입력'}`,s.name,'확정');closeSheet();render();toast('확정 대장에 담았습니다')};
  const c=document.getElementById('stClr');if(c)c.onclick=()=>{if(!confirm('확정을 지우고 미확정으로 되돌릴까요? (이력은 남습니다)'))return;addLog('되돌림',s.name,`${label} 확정 ${cur.date} 지움`);delete s.stages[key];saveSite(s);queue(`확정,${s.name},${label},취소,앱에서 되돌림`,s.name,'확정');closeSheet();render()};
  document.getElementById('stX').onclick=closeSheet;
};
window.addPerson=function(sid){const s=S.sites[sid];openSheet(`<label class="f">역할</label><select id="ppRole">${LISTS.PARTIES.concat(['협력업체','내부']).map(p=>`<option>${p}</option>`).join('')}</select><label class="f">이름·직함</label><input id="ppName"><label class="f">회사</label><input id="ppOrg"><label class="f">전화</label><input id="ppPhone" inputmode="tel"><div class="btns"><button class="b pri" id="ppOk">추가</button><button class="b ghost" id="ppX">취소</button></div>`,'담당자');
  document.getElementById('ppOk').onclick=()=>{const p={role:document.getElementById('ppRole').value,name:document.getElementById('ppName').value.trim(),org:document.getElementById('ppOrg').value.trim(),phone:document.getElementById('ppPhone').value.trim()};if(!p.name)return;s.people=(s.people||[]).concat([p]);saveSite(s);queue(`담당자,${s.name},${p.role},${p.name},${p.org},${p.phone}`,s.name,'담당자');closeSheet();render()};
  document.getElementById('ppX').onclick=closeSheet};
window.noteLine=function(sid,prefix){const s=S.sites[sid];micSheet('한 줄 남기기 · '+s.name,'통화·현장에서 들은 것을 그대로. 고치지 않고 기록에 남습니다.',prefix||'',v=>{if(!v)return;queue(`메모,${s.name},${v}`,s.name,'메모');saveSite(s);render();toast('기록했습니다')})};
window.addFact=function(sid){const s=S.sites[sid];openSheet(`<div class="hint">프로님이 정한 값. 어떤 추정보다 우선합니다.</div><label class="f">항목</label><input id="fcItem" placeholder="CB외함 납품일 / 객실 수 / 계약 형태 …"><label class="f">값</label><input id="fcVal"><label class="f">근거</label><input id="fcBasis" placeholder="누구 통화 · 언제"><div class="btns"><button class="b pri" id="fcOk">확정</button><button class="b ghost" id="fcX">취소</button></div>`,'확정값 넣기');
  document.getElementById('fcOk').onclick=()=>{const f={date:ymd(),item:document.getElementById('fcItem').value.trim(),value:document.getElementById('fcVal').value.trim(),basis:document.getElementById('fcBasis').value.trim()};if(!f.item||!f.value)return;s.facts=(s.facts||[]).concat([f]);saveSite(s);queue(`확정,${s.name},${f.item},${f.value},${f.basis||'앱 입력'}`,s.name,'확정');closeSheet();render()};
  document.getElementById('fcX').onclick=closeSheet};
window.moneySet=function(sid,k,f,v){const s=S.sites[sid];s.money=s.money||{};s.money[k]=s.money[k]||{};if(f==='date'&&s.money[k].date){return}s.money[k][f]=v;
  if(f==='date'){queue(`돈,${safe(s.name)},${safe(k)},완료,${safe(v)}`,s.name,'돈');
    const key=MONEY2REQ[k];if(key)setReq(s,key,'확정',v,'돈 탭에서 완료 표시');
    const nx={'계산서1 외함':'외함 납품분','계산서2 속판':'속판 납품분','계산서3 기구물':'기구물 납품분'}[k];
    if(nx)toast(nx+' 계산서 시점입니다. 여정 열쇠도 갱신했습니다');else toast('담았습니다');}
  saveSite(s);render()};
window.boundSet=function(sid,k,who){const s=S.sites[sid];s.bound=s.bound||{};s.bound[k]={who,sure:(s.bound[k]||{}).sure||'추정',ts:now()};saveSite(s);if(who)queue(`경계,${s.name},${k},${who},${s.bound[k].sure}`,s.name,'경계');render()};
window.boundSure=function(sid,k){const s=S.sites[sid];const b=s.bound[k];b.sure=b.sure==='확정'?'추정':'확정';saveSite(s);queue(`경계,${s.name},${k},${b.who},${b.sure}`,s.name,'경계');render()};
window.boundDraft=function(sid){const s=S.sites[sid];const b=s.bound||{};const rows=LISTS.BOUND.filter(k=>b[k]&&b[k].who).map(k=>`- ${k} : ${b[k].who}${b[k].sure==='추정'?' (확인 요청)':''}`);
  const text=`제목 : [${s.name}] 객실관리 공사 업무 경계 확인 요청\n\n담당자님, 한국마이크로닉 배성윤입니다.\n\n${s.name} 현장의 객실관리 관련 업무 경계를 아래와 같이 정리하였습니다. 다른 부분이 있으면 회신 부탁드립니다.\n\n${rows.length?rows.join('\n'):'- [ ]'}\n\n※ 강전 결선은 전기공사, 약전 결선·제어분전함 내부 설치·시운전은 당사 범위입니다.\n확인 회신 기한 : [        ]\n\n감사합니다.\n한국마이크로닉(주) 배성윤 차장  전화 [        ]`;
  draftSheet('경계 확인 메일 · '+s.name,text,s.name)};


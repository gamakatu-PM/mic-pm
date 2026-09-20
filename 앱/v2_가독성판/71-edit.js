/* ---- 앱 내용 고치기 : 프로님이 직접 (재발행 없이 즉시) ---- */
window.editQuests=function(){
  openSheet(`<div class="story">공정 단계와 열쇠(필요한 것)를 <b>프로님이 직접</b> 고치실 수 있습니다. 고치면 이 폰과 제 쪽에 바로 반영되고, 이전 판은 남습니다. 지금 판 : <b>${S.cfgVer||0}</b>${S.cfgAt?' · '+esc(S.cfgAt.slice(0,16).replace('T',' ')):''}</div>
  ${QUESTS.map((q,i)=>`<div class="row" onclick="editOneQuest(${i})"><span class="grow"><b>${i+1}. ${esc(q.n)}</b><div class="small">열쇠 ${q.req.length}개 · ${esc(q.out||'')}</div></span><span class="qgo">›</span></div>`).join('')}
  <div class="btns"><button class="b" onclick="editLists()">품목·업체·경계 목록 고치기</button><button class="b ghost" onclick="cfgHistory()">이전 판으로 되돌리기</button></div>
  <div class="btns"><button class="b ghost" onclick="resetCfg()">처음 상태로 (전부 되돌림)</button></div>`,'앱 내용 고치기');
};
window.editOneQuest=function(i){
  const q=QUESTS[i];
  openSheet(`<label class="f">단계 이름</label><input id="qn" value="${esc(q.n)}">
  <label class="f">이 단계가 내는 것</label><input id="qo" value="${esc(q.out||'')}">
  <h2 class="sec">열쇠 ${q.req.length}개 <small>누르면 고칩니다</small></h2>
  ${q.req.map((r,j)=>`<div class="row"><span class="grow" onclick="editOneReq(${i},${j})"><b>${esc(r.n)}</b>${r.gate?' <span class="pill p-ask">게이트</span>':''}<div class="small">${esc(r.who)} · ${esc(r.type)}</div></span>
    <button class="b sm ghost" onclick="moveReq(${i},${j},-1)">▲</button><button class="b sm ghost" onclick="moveReq(${i},${j},1)">▼</button></div>`).join('')}
  <div class="btns"><button class="b" onclick="addReq(${i})">＋ 열쇠 추가</button><button class="b pri" onclick="saveQuestHead(${i})">단계 이름 저장</button><button class="b ghost" onclick="editQuests()">‹ 뒤로</button></div>`,(i+1)+'. '+q.n);
};
window.saveQuestHead=function(i){const n=document.getElementById('qn').value.trim(),o=document.getElementById('qo').value.trim();
  if(n)QUESTS[i].n=n; QUESTS[i].out=o; saveConfig('단계 이름 : '+n); render(); editOneQuest(i); toast('저장했습니다')};
window.editOneReq=function(i,j){
  const r=QUESTS[i].req[j];
  openSheet(`<label class="f">열쇠 이름</label><input id="rn" value="${esc(r.n)}">
  <label class="f">누가 (담당·상대)</label><input id="rw" value="${esc(r.who||'')}">
  <label class="f">어떻게 확정하나</label><textarea id="rh" style="min-height:70px">${esc(r.how||'')}</textarea>
  <label class="f">왜 필요한가</label><textarea id="ry" style="min-height:60px">${esc(r.why||'')}</textarea>
  <label class="f">종류</label><select id="rt">${['fact','doc','ext','work'].map(t=>`<option value="${t}" ${r.type===t?'selected':''}>${({fact:'확정값(숫자·내용)',doc:'서류·문안',ext:'상대가 해야 할 것',work:'우리가 하는 일'})[t]}</option>`).join('')}</select>
  <label class="f">의뢰 부서 (서류일 때만)</label><input id="ro" value="${esc(r.order||'')}" placeholder="제작팀(외함) 등">
  <label class="f"><input type="checkbox" id="rg" style="width:auto" ${r.gate?'checked':''}> 이 열쇠는 게이트 (이게 안 되면 의뢰서를 막는다)</label>
  <div class="btns"><button class="b pri" onclick="saveReq(${i},${j})">저장</button><button class="b" onclick="delReq(${i},${j})">삭제</button><button class="b ghost" onclick="editOneQuest(${i})">‹ 뒤로</button></div>`,r.n);
};
window.saveReq=function(i,j){const r=QUESTS[i].req[j];
  const n=document.getElementById('rn').value.trim();if(!n){toast('이름이 필요합니다');return}
  r.n=n;r.who=document.getElementById('rw').value.trim();r.how=document.getElementById('rh').value.trim();
  r.why=document.getElementById('ry').value.trim();r.type=document.getElementById('rt').value;
  const o=document.getElementById('ro').value.trim();if(o)r.order=o;else delete r.order;
  if(document.getElementById('rg').checked)r.gate=true;else delete r.gate;
  saveConfig('열쇠 : '+n);render();editOneQuest(i);toast('저장했습니다')};
window.addReq=function(i){const k='x'+Date.now().toString(36);
  QUESTS[i].req.push({k,n:'새 열쇠',type:'fact',who:'',how:'',why:''});saveConfig('열쇠 추가');render();editOneReq(i,QUESTS[i].req.length-1)};
window.delReq=function(i,j){const r=QUESTS[i].req[j];
  if(!confirm(`「${r.n}」 열쇠를 지울까요? 현장에 이미 넣은 값은 남지만 화면에서는 사라집니다.`))return;
  QUESTS[i].req.splice(j,1);saveConfig('열쇠 삭제 : '+r.n);render();editOneQuest(i)};
window.moveReq=function(i,j,d){const a=QUESTS[i].req;const t=j+d;if(t<0||t>=a.length)return;
  const x=a[j];a[j]=a[t];a[t]=x;saveConfig('열쇠 순서');render();editOneQuest(i)};
window.editLists=function(){
  const L=[['ITEMS_MEET','회의에서 찍는 품목'],['PARTIES','회의 참석 업체'],['BOUND','업무 경계 항목']];
  openSheet(`<div class="story">회의 화면의 품목·업체와 경계 항목을 고칩니다. 쉼표로 나눠 적으십시오.</div>
  ${L.map(([k,label])=>`<label class="f">${label}</label><textarea id="L_${k}" style="min-height:64px">${esc((LISTS[k]||[]).join(', '))}</textarea>`).join('')}
  <div class="btns"><button class="b pri" onclick="saveLists()">저장</button><button class="b ghost" onclick="editQuests()">‹ 뒤로</button></div>`,'목록 고치기');
};
window.saveLists=function(){['ITEMS_MEET','PARTIES','BOUND'].forEach(k=>{
  const v=document.getElementById('L_'+k).value.split(',').map(x=>x.trim()).filter(Boolean);if(v.length)LISTS[k]=v});
  saveConfig('목록 수정');render();toast('저장했습니다')};
window.cfgHistory=function(){
  const H=(S.cfgHist||[]).slice().reverse();
  openSheet(`<div class="story">고치실 때마다 판이 올라가고 이전 판은 지워지지 않습니다. 지금 판 <b>${S.cfgVer||0}</b>. 아래 판을 누르면 그 내용으로 돌아가고, 그것도 새 판으로 기록됩니다(덮어쓰지 않음).</div>
  ${H.length?H.map(c=>`<div class="row"><span class="grow"><b>판 ${c.ver}</b> <span class="small mono">${esc((c.ts||'').slice(5,16).replace('T',' '))}</span><div class="small">${esc(c.why||'')}</div></span>${c.ver!==S.cfgVer?`<button class="b sm" onclick="restoreCfg(${c.ver})">이 판으로</button>`:'<span class="pill p-ok">지금</span>'}</div>`).join(''):'<div class="empty">이 폰에는 이전 판이 없습니다. 제게 「N번 되돌려」 라고 말씀해 주시면 저장소에서 꺼냅니다.</div>'}
  <div class="btns"><button class="b ghost" onclick="editQuests()">‹ 뒤로</button></div>`,'판 이력');
};
window.restoreCfg=function(ver){const c=(S.cfgHist||[]).find(x=>x.ver===ver);if(!c)return;
  if(!confirm(`판 ${ver} 내용으로 되돌릴까요? 지금 판은 이력에 남습니다.`))return;
  QUESTS=JSON.parse(JSON.stringify(c.quests));LISTS={...DEFAULT_LISTS,...(c.lists||{})};
  saveConfig(`판 ${ver} 으로 되돌림`);render();closeSheet();toast(`판 ${ver} 내용으로 돌아왔습니다 (새 판 ${S.cfgVer})`)};
window.resetCfg=function(){if(!confirm('앱 내용을 처음 상태로 되돌릴까요? 고치신 것이 사라집니다(이전 판은 남습니다).'))return;
  QUESTS=JSON.parse(JSON.stringify(DEFAULT_QUESTS));LISTS=JSON.parse(JSON.stringify(DEFAULT_LISTS));
  saveConfig('처음 상태로 되돌림');render();closeSheet();toast('되돌렸습니다')};


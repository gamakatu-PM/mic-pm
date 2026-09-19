/* ============ 설정 · 가져오기 ============ */
function renderSet(){
  document.getElementById('setMailTo').value=S.settings.mailTo||'';document.getElementById('setCc').value=S.settings.cc||'';document.getElementById('setBig').checked=!!S.settings.big;
  const SRC=[['확정 대장','확정사항.csv · 43번'],['통화 기록','녹취 분석 · PLAUD'],['앞으로 할 것','46번'],['견적 발송','47번'],['회의록','PLAUD v10'],['의뢰서 대장','10번']];
  document.getElementById('srcList').innerHTML=SRC.map(([k,w])=>{const v=(S.feedsrc||{})[k]||{};
    return `<span><b>${k}</b><div class="small">${w}</div></span><span class="small">${v.date?esc(v.date):'—'}</span><span class="pill ${v.date?'p-ok':'p-off'}">${v.count!=null?esc(String(v.count))+'건':'아직'}</span>`}).join('');
  const inb=S.inbox||[];
  document.getElementById('inbCount').textContent=inb.length+'건';
  document.getElementById('inbList').innerHTML=inb.slice().reverse().slice(0,20).map(x=>`<div class="row"><span class="grow"><span class="mono">${esc((x.ts||'').slice(5,10))}</span> ${esc(x.text)}</span>${x.seen?'':'<span class="pill p-ok">새것</span>'}</div>`).join('')||'<div class="empty">아직 없음</div>';
  const cv=document.getElementById('cfgVerNow');if(cv)cv.textContent=String(S.cfgVer||0);
  const dc=document.getElementById('decCount');if(dc)dc.textContent=decisionList().length+'줄';
  document.getElementById('logCount').textContent=S.log.length+'줄';
  document.getElementById('logList').innerHTML=S.log.slice(-30).reverse().map(l=>`<div class="row"><span class="grow"><span class="mono">${esc(l.ts.slice(5,16).replace('T',' '))}</span> <span class="pill p-off">${esc(l.type)}</span> ${esc(l.text)}</span></div>`).join('')||'<div class="empty">없음</div>';
}
document.getElementById('btnSaveSet').onclick=()=>{S.settings.mailTo=document.getElementById('setMailTo').value.trim()||DEFAULT_SET.mailTo;S.settings.cc=document.getElementById('setCc').value.trim();S.settings.big=document.getElementById('setBig').checked;document.body.classList.toggle('big',S.settings.big);saveMeta();toast('저장했습니다')};
document.getElementById('btnCsv').onclick=()=>{
  const L=decisionList();
  const head='일자,현장,항목,값,근거,누가,상태';
  const esc2=v=>{v=String(v==null?'':v);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v};
  const body=L.map(d=>[d.date,d.site,d.item,d.value,d.basis,d.by,'확정'].map(esc2).join(',')).join('\n');
  const t=head+'\n'+body;
  openSheet(`<div class="hint">PC 43번 확정 대장(<span class="mono">확정사항.csv</span>)과 같은 칸입니다. 복사해 그 파일 아래에 붙이시면 됩니다. ${L.length}줄.</div>
    <pre class="draft" style="max-height:260px;overflow:auto">${esc(t.slice(0,4000))}${t.length>4000?'\n…':''}</pre>
    <div class="btns"><button class="b pri" onclick="copy(${JSON.stringify(t).replace(/"/g,'&quot;')})">복사</button><button class="b ghost" onclick="closeSheet()">닫기</button></div>`,'확정 대장으로 내보내기');
};
document.getElementById('btnExport').onclick=()=>{const t=JSON.stringify(S,null,1);openSheet(`<h3>내보내기</h3><div class="hint">전체 상태 JSON. 복사해 파일로 두시면 새 폰에서 붙여넣어 복원할 수 있습니다.</div><textarea style="min-height:200px">${esc(t)}</textarea><div class="btns"><button class="b pri" onclick="copy(${JSON.stringify(t).replace(/"/g,'&quot;')})">복사</button><button class="b ghost" onclick="closeSheet()">닫기</button></div>`)};
document.getElementById('btnReset').onclick=()=>{if(!confirm('이 폰의 앱 데이터를 전부 지웁니다 (공유 저장소는 그대로). 계속할까요?'))return;S={sites:{},items:{},meetings:{},log:[],outbox:[],settings:{...DEFAULT_SET}};persist();render();toast('지웠습니다')};
document.getElementById('btnFeed').onclick=()=>{
  const t=document.getElementById('feedText').value.trim();if(!t)return;
  let d;try{d=JSON.parse(t)}catch(e){toast('PC 49번이 만든 글이 아닙니다');return}
  const r=takeFeed(d);document.getElementById('feedText').value='';
  toast(`받았습니다 : 현장 ${r.sites} · 할 일 ${r.items} · 열쇠 ${r.keys}`);view='map';render();
};
function takeFeed(d){
  let ns=0,ni=0,nk=0;
  Object.values(d.sites||{}).forEach(x=>{
    const id=(Object.values(S.sites).find(s=>s.name===x.name)||{}).id||x.id;
    const s=S.sites[id]||{id,name:x.name,people:[],facts:[],req:{},stages:{},created:now()};
    if(!S.sites[id])ns++;
    if(x.due&&!s.due)s.due=x.due; if(x.rooms&&!s.rooms)s.rooms=x.rooms;
    if(x.lastMeeting)s.lastMeeting=x.lastMeeting;
    if(Array.isArray(x.meetings)&&x.meetings.length){const have=new Set((s.mlist||[]).map(m=>m.title));s.mlist=(s.mlist||[]).concat(x.meetings.filter(m=>!have.has(m.title)))}
    (x.facts||[]).forEach(f=>{if(!(s.facts||[]).some(y=>y.item===f.item&&y.value===f.value))(s.facts=s.facts||[]).push(f)});
    Object.keys(x.req||{}).forEach(k=>{const cur=(s.req||{})[k];
      if(cur&&cur.state==='확정')return;                       // 프로님 확정은 덮지 않는다
      if(cur&&cur.value===x.req[k].value)return;
      (s.req=s.req||{})[k]={...x.req[k]};nk++});
    S.sites[id]=s;saveSite(s);
  });
  (d.items||[]).forEach(x=>{
    const ex=S.items[x.id];
    if(ex){if(['done','confirmed','cancel','requested'].includes(ex.status))return;
      let ch=false;['when','to','memo','quest','text'].forEach(k=>{if(x[k]&&!ex[k]){ex[k]=x[k];ch=true}});
      if(ch)saveItem(ex);return}
    S.items[x.id]={...x,created:now()};saveItem(S.items[x.id]);ni++;
  });
  if(d.src){S.feedsrc={...(S.feedsrc||{}),...d.src};dbWrite('meta/feedsrc',S.feedsrc)}
  S.inbox=(S.inbox||[]).concat([{ts:now(),text:`PC 49번에서 받음 — 현장 ${ns} · 할 일 ${ni} · 열쇠 ${nk}`}]);
  persist();dbWrite('meta/inbox',{lines:S.inbox});
  addLog('PC피드','',`현장 ${ns} · 할 일 ${ni} · 열쇠 ${nk}`);saveMeta();
  return {sites:ns,items:ni,keys:nk};
}
document.getElementById('btnImport').onclick=()=>{const t=document.getElementById('importText').value;if(!t.trim())return;const r=importText(t);document.getElementById('importText').value='';render();toast(`가져옴 : 줄 ${r.items}건 · 확정 ${r.facts}건 · 현장 ${r.sites}곳`);if(r.items||r.facts){view='today';render()}};
function importText(t){
  let items=0,facts=0,sites=0;const seenSites=new Set();
  const lines=t.replace(/\r/g,'').split('\n');
  let section='',site='';
  const put=(id,obj)=>{const ex=S.items[id];if(ex){if(['done','confirmed','cancel','requested'].includes(ex.status))return;const merged={...ex,status:ex.status,fix:ex.fix,history:ex.history,created:ex.created};for(const k in obj){if(obj[k]&&!ex[k])merged[k]=obj[k]}if(JSON.stringify(merged)!==JSON.stringify(ex)){saveItem(merged)}return}obj.id=id;obj.status='open';obj.created=now();saveItem(obj);items++};
  const mark=(name)=>{if(!name)return;if(!seenSites.has(name)){seenSites.add(name);if(!S.sites[siteId(name)]){ensureSite(name);sites++}}};
  for(let raw of lines){
    const l=raw.trim();
    if(/^##\s/.test(l)){section=l.replace(/^#+\s*/,'');site='';continue}
    if(/^###\s/.test(l)){site=l.replace(/^#+\s*/,'').trim();mark(site);continue}
    let m;
    // 확정 표 : | 일자 | 현장 | 항목 | 값 | 근거 |
    if((m=l.match(/^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$/))){
      const sName=m[2].trim();mark(sName);const s=ensureSite(sName);const f={date:m[1],item:m[3].trim(),value:m[4].replace(/\*\*/g,'').trim(),basis:m[5].trim()};
      s.facts=s.facts||[];if(!s.facts.find(x=>x.item===f.item&&x.value===f.value)){s.facts.push(f);facts++;saveSite(s)}continue}
    // KM-010 현장 · 내용 [n일째]
    if((m=l.match(/^-?\s*(KM-\d{3,4})\s+([^·]+?)\s*·\s*(.+?)\s*(?:\[(\d+)일째\])?\s*$/))){
      const sName=m[2].trim();mark(sName);put(m[1],{kind:'ask',site:sName,text:m[3].trim(),when:''});continue}
    // - **현장** · 이번주 · 「제가 … 만들까요?」 (할 일 : …)
    if((m=l.match(/^-\s*\*\*([^*]+)\*\*\s*·\s*([^·]+?)\s*·\s*「([^」]+)」\s*(?:\(할 일\s*:\s*(.+?)\))?\s*$/))){
      const sName=m[1].trim();mark(sName);const q=m[3].trim();const todo=(m[4]||'').trim();put('M-'+hash(sName+q+todo),{kind:'make',site:sName,when:m[2].trim(),makeq:q,text:todo});continue}
    // - 오늘 [확정] 내용 → 받는곳 — 메모 【제가 … 만들까요?】
    if(site&&(m=l.match(/^-\s*(\S+)\s*\[(확정|제안)\]\s*(.+?)\s*(?:→\s*([^—]+?))?\s*(?:—\s*(.+?))?\s*(?:【([^】]+)】)?\s*$/))){
      const when=m[1].replace(/\(.*\)/,'').trim();const kind=m[2]==='확정'?'todo':'ask';const text=m[3].trim();
      const whenV=/^\d{1,2}\/\d{1,2}/.test(when)?(String(new Date().getFullYear())+'-'+when.split('/').map(x=>x.padStart(2,'0')).join('-')):when;
      const same=Object.values(S.items).find(x=>x.site===site&&x.text===text&&x.kind!=='make');
      const id=same?same.id:((kind==='todo'?'A-':'P-')+hash(site+text));
      put(id,{kind:same?same.kind:kind,site,text,when:whenV,to:(m[4]||'').trim(),memo:(m[5]||'').trim()});
      if(m[6]){put('M-'+hash(site+m[6].trim()+text),{kind:'make',site,when:whenV,makeq:m[6].trim(),text})}
      continue}
  }
  addLog('가져옴','',`아침 한 장 붙여넣기 : 줄 ${items} · 확정 ${facts} · 현장 ${sites}`);saveMeta();
  return {items,facts,sites};
}


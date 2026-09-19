/* ============ 상태 ============ */
const LS='km6_state';
const STAGES=[['외함제작','외함 제작'],['외함납품','외함 납품'],['속판제작','속판 제작'],['기구물제작','기구물 제작'],['벽지완료','벽지 완료'],['빽커버','빽커버 설치'],['기구물설치','기구물 설치'],['강전약전','강전·약전 결선'],['시운전','시운전']];
const ITEMS_MEET=['K','DM','L','온도조절기','BSP','챠임벨','FIP','PC','멀티아울렛','CB','외함','전력계량기','도어락'];
const PARTIES=['시공사','전기','통신','감리','발주처','설계사','인테리어','건축','설비','에어컨','바닥난방'];
const BOUND=['외함 설치','강전 결선','약전 결선','외함 커버','전력계량기','바닥난방 밸브','타공','도어락 설치'];
const DEFAULT_SET={mailTo:'gamakatu0924@gmail.com',cc:'',big:false};
let S=loadLocal()||{sites:{},items:{},meetings:{},log:[],outbox:[],inbox:[],settings:{...DEFAULT_SET}};
S.inbox=S.inbox||[];S.feedsrc=S.feedsrc||{};S.contacts=S.contacts||[];S.drops=S.drops||[];S.asks=S.asks||{};
S.settings={...DEFAULT_SET,...(S.settings||{})};
let view='map', curSite=null, siteTab='공정', curMeet=null;
let db=null; const dbq={};
function loadLocal(){try{return JSON.parse(localStorage.getItem(LS)||'null')}catch(e){return null}}
function persist(){try{localStorage.setItem(LS,JSON.stringify(S))}catch(e){}}
function now(){return new Date().toISOString()}
function ymd(d){d=d||new Date();const p=n=>String(n).padStart(2,'0');return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())}
function yymmdd(){return ymd().slice(2).replace(/-/g,'')}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function hash(s){let h=5381;for(const c of s)h=((h<<5)+h+c.charCodeAt(0))>>>0;return h.toString(36)}
function siteId(name){return 's_'+hash(name.replace(/\s/g,''))}
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),1800)}


/* ============ 저장 (폰 + 공유 저장소) ============ */
function dbWrite(path,data){
  if(!db)return;
  dbq[path]=(dbq[path]||Promise.resolve()).then(()=>db.doc(path).set(JSON.parse(JSON.stringify(data)))).then(()=>{
    const b=document.getElementById('dbBadge');if(b&&b.dataset.fail){delete b.dataset.fail;b.textContent='클로드와 연결됨';b.className='badge on'}
  }).catch(e=>{console.warn('db',path,e&&e.code);
    const b=document.getElementById('dbBadge');if(b){b.dataset.fail='1';b.textContent='저장 실패 — 폰에만 있음';b.className='badge fail'}});
}
function saveItem(it){it.updated=now();S.items[it.id]=it;persist();dbWrite('items/'+it.id,it)}
function saveSite(s){s.updated=now();S.sites[s.id]=s;persist();dbWrite('sites/'+s.id,s)}
function saveMeet(m){m.updated=now();S.meetings[m.id]=m;persist();dbWrite('meetings/'+m.id,m)}
function saveMeta(){persist();dbWrite('meta/outbox',{lines:S.outbox});dbWrite('meta/log',{lines:S.log.slice(-600)});dbWrite('meta/settings',S.settings)}
function addLog(type,site,text){S.log.push({ts:now(),type,site:site||'',text});if(S.log.length>600)S.log=S.log.slice(-600)}
function safe(v){return String(v==null?'':v).replace(/[,\r\n]+/g,' · ').replace(/\s+/g,' ').trim()}
function queue(line,site,type){S.outbox.push({ts:now(),line,site:site||'',type:type||'회신'});addLog(type||'회신',site,line);saveMeta();renderFab()}

async function initDb(){
  const badge=document.getElementById('dbBadge');
  try{
    db=await (window.claude&&window.claude.use?window.claude.use('db'):Promise.resolve(null));
  }catch(e){db=null}
  if(!db){badge.textContent='이 폰에만 저장';badge.className='badge';return}
  try{
    const [it,si,me,ob,lg,st,ib,fs]=await Promise.all([db.collection('items').get(),db.collection('sites').get(),db.collection('meetings').get(),db.doc('meta/outbox').get(),db.doc('meta/log').get(),db.doc('meta/settings').get(),db.doc('meta/inbox').get(),db.doc('meta/feedsrc').get()]);
    if(ib.exists&&Array.isArray(ib.data().lines))S.inbox=ib.data().lines;
    if(fs.exists)S.feedsrc=fs.data()||{};
    try{const cg=await db.doc('config/quests').get();if(cg.exists){applyConfig(cg.data());persist()}}catch(e){}
    try{db.doc('config/quests').onSnapshot(d=>{if(d.metadata.hasPendingWrites||!d.exists)return;applyConfig(d.data());persist();render();toast('앱 내용이 갱신되었습니다 (판 '+(d.data().ver||'')+')')})}catch(e){}
    try{const dp=await db.doc('meta/drops').get();if(dp.exists&&Array.isArray(dp.data().lines))S.drops=dp.data().lines}catch(e){}
    try{const ct=await db.doc('meta/contacts').get();if(ct.exists&&Array.isArray(ct.data().lines)){const mine=S.contacts||[];S.contacts=ct.data().lines.map((x,i)=>({...x,...(mine[i]&&mine[i].site?{site:mine[i].site}:{})}))}}catch(e){}
    const remoteHas=it.size||si.size||me.size;
    if(remoteHas){
      it.docs.forEach(d=>mergeIn(S.items,d.id,d.data()));
      try{(await db.collection('asks').get()).docs.forEach(d=>mergeIn(S.asks,d.id,d.data()))}catch(e){}
      si.docs.forEach(d=>mergeIn(S.sites,d.id,d.data()));
      me.docs.forEach(d=>mergeIn(S.meetings,d.id,d.data()));
      if(ob.exists&&Array.isArray(ob.data().lines))S.outbox=ob.data().lines;
      if(lg.exists&&Array.isArray(lg.data().lines))S.log=lg.data().lines;
      if(st.exists)S.settings={...S.settings,...st.data()};
      // 폰에만 있던 것은 올린다
      Object.values(S.items).forEach(x=>{if(!it.docs.find(d=>d.id===x.id))dbWrite('items/'+x.id,x)});
      Object.values(S.sites).forEach(x=>{if(!si.docs.find(d=>d.id===x.id))dbWrite('sites/'+x.id,x)});
      persist();
    }else if(Object.keys(S.items).length||Object.keys(S.sites).length){
      Object.values(S.items).forEach(x=>dbWrite('items/'+x.id,x));
      Object.values(S.sites).forEach(x=>dbWrite('sites/'+x.id,x));
      Object.values(S.meetings).forEach(x=>dbWrite('meetings/'+x.id,x));
      saveMeta();
    }
    badge.textContent='클로드와 연결됨';badge.className='badge on';
    const sub=(col,tgt)=>db.collection(col).onSnapshot(snap=>{
      if(snap.metadata.hasPendingWrites)return;
      let ch=false;snap.docChanges().forEach(c=>{if(c.type==='removed'){delete tgt[c.doc.id];ch=true}else{const d=c.doc.data();if(!tgt[c.doc.id]||(d.updated||'')>(tgt[c.doc.id].updated||'')){tgt[c.doc.id]=d;ch=true}}});
      if(ch){persist();render()}
    },e=>console.warn(col,e&&e.code));
    sub('items',S.items);sub('sites',S.sites);sub('meetings',S.meetings);sub('asks',S.asks);
    db.doc('meta/outbox').onSnapshot(s=>{if(s.metadata.hasPendingWrites||!s.exists)return;S.outbox=s.data().lines||[];persist();renderFab()});
    db.doc('meta/inbox').onSnapshot(s=>{if(s.metadata.hasPendingWrites||!s.exists)return;const L=s.data().lines||[];const n=L.filter(x=>!x.seen).length;const had=(S.inbox||[]).filter(x=>!x.seen).length;S.inbox=L;persist();render();if(n>had)toast('클로드가 '+(n-had)+'건 반영했습니다')});
    db.doc('meta/feedsrc').onSnapshot(s=>{if(s.metadata.hasPendingWrites||!s.exists)return;S.feedsrc=s.data()||{};persist();if(view==='set')render()});
    render();
  }catch(e){console.warn(e);badge.textContent='이 폰에만 저장';badge.className='badge'}
}
function mergeIn(tgt,id,d){if(!tgt[id]||(d.updated||'')>(tgt[id].updated||''))tgt[id]=d}


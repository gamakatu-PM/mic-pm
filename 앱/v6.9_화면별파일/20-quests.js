/* ============ 공정 여정 (게임판) ============ */
/* 프로님이 알려 주신 흐름 : 설계의뢰→도면납품 → 견적·계약 → CB외함 제작·납품 → 외함 설치(전기·통신)
   → 속판(제어분전함) 제작·설치 → 강전(전기)·약전(우리) 결선·커버 → 기구물 제작(의뢰서 없으면 안 움직임)
   → 벽지 완료 후 설치 → 전기 공급·시운전 → 계산서·수금.  각 단계 = 퀘스트, 필요한 것 = 열쇠. */
const DEFAULT_QUESTS=[
 {k:'설계',n:'설계 · 도면 납품',icon:'✎',hint:['설계','도면','평면','전등','성급','룸타입','Rev'],out:'객실관리 도면 + 수량표(검토용)',
  req:[
   {k:'의뢰접수',n:'설계사 설계의뢰 접수',type:'ext',who:'설계사',how:'의뢰 메일·건축 도면이 들어온 날을 넣습니다.',why:'이 날부터 우리 시계가 돕니다.'},
   {k:'평면도',n:'건축 단위세대 평면도 수령',type:'ext',who:'설계사·건축',how:'룸타입별 평면(작업 전 도면)이 있어야 배치를 예상합니다. 없으면 요청 메일.',why:'평면이 없으면 수량도 견적도 없습니다.'},
   {k:'등급객실',n:'성급 · 객실 수 · 룸타입 확정',type:'fact',who:'발주처·설계사',how:'1~3성=K만·온도+L / 4~5성=K+DM·BSP(온도+L+USB+유니버셜)·욕실 L. 리조트는 DM 제외.',why:'성급 하나가 기구물 종류를 전부 정합니다.'},
   {k:'전등설계',n:'전기설계 전등 회로(L 구수)',type:'ext',who:'전기설계 업체',how:'전등 설계가 나오기 전에는 「L」 로만 표기합니다. 나오면 1~6구를 넣습니다.',why:'조명 스위치 구수는 우리가 정하지 않습니다.'},
   {k:'도면납품',n:'객실관리 도면 납품',type:'work',who:'설계팀',how:'작업의뢰서(설계)가 있어야 설계팀이 움직입니다. 납품한 Rev 와 날짜를 넣습니다.',why:'이 도면이 견적·외함·속판·기구물의 뿌리입니다.',order:'설계팀'},
  ]},
 {k:'계약',n:'견적 · 계약',icon:'₩',hint:['견적','계약','실행','수량표','증감','감액','명절'],out:'견적서 · 실행산출 · 계약서',
  req:[
   {k:'수량표',n:'수량표 확정',type:'fact',who:'프로님',how:'도면 NOTE 수량과 블록 수량을 나란히 보고 프로님이 채택합니다. 계통도에 수량이 없으면 상대에게 수량표를 요청합니다.',why:'검토용 수량으로 견적을 내면 증감 분쟁이 됩니다.'},
   {k:'실행',n:'실행(원가) 산출',type:'work',who:'PC 28번',how:'단가장 + 정답본(연합기숙사 v5) 틀로 PC가 만듭니다. 빈칸은 프로님 숫자.',why:'이윤을 알아야 계약가를 정합니다.'},
   {k:'견적발송',n:'견적서 발송',type:'doc',who:'프로님',how:'광희동 Rev1 틀. 보낸 날을 넣으면 47번 「찾아갈 곳」 에 올라갑니다.',why:'보내 놓고 가만히 있으면 식습니다. 3일 뒤 방문.'},
   {k:'계약형태',n:'계약 형태 확정',type:'fact',who:'시공사·발주처',how:'정식 계약서(내역서+사업자등록증+기본내역) / 약식 / 구두. 상대가 말한 것만 확정.',why:'외함 출고 조건이 계약 완료인 현장이 많습니다.'},
   {k:'계약완료',n:'계약 체결',type:'ext',who:'시공사·발주처',how:'계약서 서명일. 안 되면 독촉 문안.',why:'계약 전 출고는 우리 위험입니다.'},
  ]},
 {k:'외함',n:'CB외함 제작 · 납품',icon:'▣',hint:['외함','CB외함','타공','석고','골조','매립','스터드'],out:'외함 작업의뢰서 · 외함 납품 · 계산서 1회',
  req:[
   {k:'외함공법',n:'외함 설치 공법 확정',type:'fact',who:'시공사(건축)',how:'옹벽 매립이면 골조 올릴 때, 스터드 고정이면 석고 치기 전. 현장이 정하는 값이라 역산하지 않습니다.',why:'납품 시점이 여기서 정해집니다.'},
   {k:'외함규격',n:'외함 규격 · CB 대수 확정',type:'fact',who:'프로님·설계팀',how:'도면의 CB 대수와 외함 치수. 층별 CB 위치까지.',why:'외함 세트(4번 도구)가 이 값을 씁니다.'},
   {k:'외함납기',n:'외함 납품일 확정',type:'fact',who:'시공사',how:'현장이 요구한 날. 제작 2주가 필요하니 그 2주 전이 의뢰서 발행 마감입니다.',why:'외함이 늦으면 전기·통신 공정이 섭니다.'},
{k:'계약선금',n:'★ 계약 · 계산서 확인 (제작 전)',type:'doc',who:'시공사·발주처',how:'계약서가 있고 선금·기성 계산서를 요청했는지 확인합니다. 아직이면 계약 요청 + 계산서 요청 문안을 냅니다.',why:'프로님 규칙 — 물건을 만들기 전에 계약과 계산서를 먼저 요청한다. 계약 없이 제작에 들어가면 손실이 우리 것이 됩니다.',gate:true},
   {k:'외함의뢰서',n:'작업의뢰서(외함) 발행',type:'doc',who:'프로님→제작',how:'규격·수량·납기·현장 주소. 결재 후 제작 착수.',why:'의뢰서가 없으면 제작팀은 시작하지 않습니다.',order:'제작팀(외함)'},
   {k:'외함납품',n:'외함 납품 완료',type:'work',who:'제작·물류',how:'납품일과 인수자. 이때 계산서 1회.',why:'수금의 첫 근거입니다.'},
  ]},
 {k:'외함설치',n:'외함 설치 (전기 · 통신)',icon:'⚒',hint:['설치 업체','설치 위치','타공도'],out:'설치 완료 사진',
  req:[
   {k:'설치주체',n:'외함 설치 업체 확정',type:'fact',who:'시공사',how:'전기업체인지 통신업체인지. 통합 공정회의에서 확정.',why:'타공도를 누구에게 보내야 하는지 정해집니다.'},
   {k:'타공도',n:'타공도 · 설치 안내 송부',type:'doc',who:'프로님→설치 업체',how:'보낸 날 + 상대가 「받았다」 한 날. 읽음 표시만으로는 확정이 아닙니다.',why:'못 받았다는 말이 나오면 우리가 늦은 것이 됩니다.'},
   {k:'설치완료',n:'외함 설치 완료 확인',type:'ext',who:'설치 업체',how:'사진 한 장 + 날짜. 위치·높이가 도면과 다르면 하자 한 줄.',why:'속판은 외함이 붙어 있어야 들어갑니다.'},
  ]},
 {k:'속판',n:'속판(제어분전함) 제작 · 설치',icon:'⊞',hint:['속판','배선도','모듈','CB 구성','RCBO','릴레이'],out:'속판 작업의뢰서 · 속판 납품 · 계산서 2회',
  req:[
   {k:'배선도',n:'CB 배선도 · 모듈 구성 확정',type:'fact',who:'설계팀·프로님',how:'배선도에서 모듈 종류·수량을 뽑아 단가장(29번)에 맞춥니다. 없는 모듈은 주황 줄.',why:'속판 내부가 이 그림대로 만들어집니다.'},
{k:'계약선금',n:'★ 계약 · 계산서 확인 (제작 전)',type:'doc',who:'시공사·발주처',how:'계약서가 있고 선금·기성 계산서를 요청했는지 확인합니다. 아직이면 계약 요청 + 계산서 요청 문안을 냅니다.',why:'프로님 규칙 — 물건을 만들기 전에 계약과 계산서를 먼저 요청한다. 계약 없이 제작에 들어가면 손실이 우리 것이 됩니다.',gate:true},
   {k:'속판의뢰서',n:'작업의뢰서(속판) 발행',type:'doc',who:'프로님→제작',how:'제작 2달. 납품 예정 2달 전이 발행 마감.',why:'2달은 줄일 수 없습니다.',order:'제작팀(속판)'},
   {k:'속판납품',n:'속판 납품 · 외함 내 설치',type:'work',who:'우리(시공팀)',how:'외함 설치 완료 뒤. 설치일과 대수. 이때 계산서 2회.',why:'강전 결선이 이 뒤에 옵니다.',order:'시공팀(속판 설치)'},
  ]},
 {k:'결선',n:'강전 · 약전 결선 · 커버',icon:'⚡',hint:['강전','약전','결선','커버','전기업체'],out:'결선 완료 · 커버 설치',
  req:[
   {k:'강전일정',n:'전기업체 강전 결선 일정',type:'ext',who:'전기업체',how:'속판 납품 후 1달 안. 전기업체가 말한 날.',why:'강전이 끝나야 우리 약전이 들어갑니다.'},
   {k:'약전의뢰서',n:'시공팀 약전 결선 의뢰서',type:'doc',who:'프로님→시공팀',how:'객실 수·CB 대수·현장 일정.',why:'의뢰서 없이는 시공팀 배정이 안 됩니다.',order:'시공팀(약전 결선)'},
   {k:'커버',n:'외함 커버 설치',type:'work',who:'우리(시공팀)',how:'강전·약전 끝난 뒤. 날짜.',why:'커버가 붙으면 CB 공정이 닫힙니다.'},
  ]},
 {k:'기구물제작',n:'기구물 제작',icon:'◈',hint:['기구물','챠임벨','키센서','온도조절기','조명','BSP','스위치','도어락','형번','2000M','색상'],out:'기구물 작업의뢰서 · 기구물 납품 · 계산서 3회',
  req:[
   {k:'기구물수량',n:'기구물 수량 · 형번 확정',type:'fact',who:'프로님',how:'수량표 확정본 + 계열(규격 없으면 2000M). 회의에서 바뀐 것은 증감으로.',why:'제작에 들어간 뒤 바뀌면 손실입니다.'},
   {k:'마감',n:'색상 · 마감 확정',type:'fact',who:'인테리어',how:'벽지·도장 색에 맞춘 플레이트 색. 인테리어가 말한 것.',why:'색이 늦으면 제작이 섭니다.'},
   {k:'벽지예정',n:'벽지 · 페인트 완료 예정일',type:'ext',who:'건축',how:'건축이 말한 예정일. 제작 1.5~2달이 여기서 거꾸로 갑니다.',why:'설치는 벽지 뒤에만 됩니다.'},
{k:'계약선금',n:'★ 계약 · 계산서 확인 (제작 전)',type:'doc',who:'시공사·발주처',how:'계약서가 있고 선금·기성 계산서를 요청했는지 확인합니다. 아직이면 계약 요청 + 계산서 요청 문안을 냅니다.',why:'프로님 규칙 — 물건을 만들기 전에 계약과 계산서를 먼저 요청한다. 계약 없이 제작에 들어가면 손실이 우리 것이 됩니다.',gate:true},
   {k:'기구물의뢰서',n:'작업의뢰서(기구물) 발행',type:'doc',who:'프로님→제작·개발',how:'품목별 수량·형번·색상·납기. 벽지 예정일 −(빽커버 10일+설치 7일+시운전 7일) 이 납기.',why:'의뢰서가 관문입니다.',order:'제작팀·개발팀(기구물)'},
   {k:'기구물납품',n:'기구물 납품',type:'work',who:'제작·물류',how:'납품일. 이때 계산서 3회.',why:'세 번째 수금 근거.'},
  ]},
 {k:'설치',n:'빽커버 · 기구물 설치',icon:'⌂',hint:['벽지','페인트','빽커버','설치'],out:'설치 완료 · 사진대지',
  req:[
   {k:'벽지완료',n:'벽지 · 페인트 완료',type:'ext',who:'건축',how:'실제 완료된 날. 층별로 다르면 먼저 끝난 층부터.',why:'이 날 전에는 아무것도 붙일 수 없습니다.'},
   {k:'빽커버',n:'빽커버 설치',type:'work',who:'우리(시공팀)',how:'벽지 완료 후 1~2주.',why:'기구물 설치의 바탕.'},
   {k:'설치의뢰서',n:'시공팀 설치 의뢰서',type:'doc',who:'프로님→시공팀',how:'객실 수·품목·현장 일정·인원.',why:'배정 근거.',order:'시공팀(기구물 설치)'},
   {k:'설치완료',n:'기구물 설치 완료',type:'work',who:'우리(시공팀)',how:'빽커버 후 1주. 완료일 + 사진.',why:'시운전 시작 조건.'},
  ]},
 {k:'시운전',n:'시운전 · 수금',icon:'★',hint:['시운전','전기 공급','하자','계산서','수금','중도금','잔금'],out:'시운전 완료 · 계산서 3회 · 수금',
  req:[
   {k:'전기공급',n:'전기 공급',type:'ext',who:'전기업체·시공사',how:'수전된 날.',why:'전기가 와야 제품이 동작합니다.'},
   {k:'시운전완료',n:'시운전 완료',type:'work',who:'우리',how:'1주. 객실 O/X 로 확인(v6.3).',why:'납품의 마지막 증명.'},
   {k:'하자',n:'하자 처리 완료',type:'work',who:'우리(시공팀·AS)',how:'X 였던 객실이 전부 O 가 된 날.',why:'하자가 남으면 수금이 밀립니다.'},
   {k:'계산서',n:'계산서 3회 발행 확인',type:'doc',who:'프로님→경리',how:'외함·속판·기구물 각 납품 때 1회씩.',why:'발행하지 않은 계산서는 수금이 없습니다.'},
   {k:'수금',n:'수금 완료',type:'fact',who:'발주처·시공사',how:'입금일과 금액 [ ]. 금액은 프로님만.',why:'여기가 결승선입니다.'},
  ]},
];
let QUESTS=JSON.parse(JSON.stringify(DEFAULT_QUESTS));
const DEFAULT_LISTS={ITEMS_MEET,PARTIES,BOUND,STAGES};
let LISTS=JSON.parse(JSON.stringify(DEFAULT_LISTS));
function applyConfig(c){
  if(c&&Array.isArray(c.quests)&&c.quests.length){QUESTS=c.quests}
  if(c&&c.lists){LISTS={...DEFAULT_LISTS,...c.lists}}
  S.cfgVer=(c&&c.ver)||0;S.cfgAt=(c&&c.ts)||'';
}
function cfgNow(){return {quests:QUESTS,lists:LISTS,ver:(S.cfgVer||0)+1,ts:now(),by:'프로님(앱)'}}
function saveConfig(why){
  const c=cfgNow();S.cfgVer=c.ver;S.cfgAt=c.ts;S.cfg=c;persist();
  dbWrite('config/quests',c);dbWrite('config/bak_'+String(c.ver).padStart(3,'0'),{...c,why:why||''});
  queue(`앱고침,전체,${safe(why||'내용 수정')},판 ${c.ver},앱`,'','앱고침');
  addLog('앱고침','',`판 ${c.ver} · ${why||''}`);saveMeta();
}
const RSTATE={'':'미확정','추정':'추정','진행중':'진행중','확정':'확정'};
function reqOf(s,qk,rk){return ((s.req||{})[qk+'/'+rk])||{}}
/* 어느 화면에서든 열쇠를 갱신하는 단 하나의 길. 확정은 덮지 않는다(프로님 값이 이긴다). */
function setReq(s,key,state,value,basis,opt){
  const cur=(s.req||{})[key]||{};
  if(cur.state==='확정'&&state!=='확정'&&!(opt&&opt.force))return false;   // 확정을 추정으로 되돌리지 않는다
  s.req=s.req||{};
  s.req[key]={state,value:value||cur.value||'',basis:basis||cur.basis||'',date:ymd(),ts:now(),prev:cur.state?{state:cur.state,value:cur.value}:undefined};
  const st=REQ2STAGE[key];
  if(st&&state==='확정'){s.stages=s.stages||{};const d=/^\d{4}-\d{2}-\d{2}$/.test(value||'')?value:ymd();s.stages[st]={date:d,note:basis||'',ts:now()}}
  const r=reqDef(key);
  queue(`${state},${safe(s.name)},${safe(r?r.n:key)},${safe(value)},${safe(basis||'앱')}`,s.name,state);
  return true;
}
function reqDef(key){const [qk,rk]=key.split('/');const q=QUESTS.find(x=>x.k===qk);return q&&q.req.find(x=>x.k===rk)}
const REQ2STAGE={'외함/외함의뢰서':'외함제작','외함/외함납품':'외함납품','속판/속판납품':'속판제작','기구물제작/기구물납품':'기구물제작','설치/벽지완료':'벽지완료','설치/빽커버':'빽커버','설치/설치완료':'기구물설치','결선/커버':'강전약전','시운전/시운전완료':'시운전'};
/* 회의에서 찍은 공정 단계 → 열쇠 */
const STAGE2REQ={'외함제작':'외함/외함의뢰서','외함납품':'외함/외함납기','속판제작':'속판/속판납품','기구물제작':'기구물제작/기구물납품','벽지완료':'기구물제작/벽지예정','빽커버':'설치/빽커버','기구물설치':'설치/설치완료','강전약전':'결선/강전일정','시운전':'시운전/시운전완료'};
/* 돈 탭 → 열쇠 */
const MONEY2REQ={'견적':'계약/견적발송','계약':'계약/계약완료','계산서1 외함':'외함/외함납품','계산서2 속판':'속판/속판납품','계산서3 기구물':'기구물제작/기구물납품','수금':'시운전/수금'};
/* 회의 품목 → 수량 열쇠 */
const ITEM2REQ={'CB':'외함/외함규격','외함':'외함/외함규격','전력계량기':'기구물제작/기구물수량'};
function itemReqKey(item){if(ITEM2REQ[item])return ITEM2REQ[item];return '기구물제작/기구물수량'}
function questProg(s,q){const done=q.req.filter(r=>reqOf(s,q.k,r.k).state==='확정').length;const part=q.req.filter(r=>['추정','진행중'].includes(reqOf(s,q.k,r.k).state)).length;return {done,part,total:q.req.length,pct:Math.round(done/q.req.length*100)}}
function questStatus(s,qi){
  const q=QUESTS[qi];const p=questProg(s,q);
  if(p.done===p.total)return {label:'완료',cls:'ok'};
  const prev=qi>0?questProg(s,QUESTS[qi-1]):null;
  const cur=currentQuest(s);
  if(qi===cur)return {label:p.done||p.part?'여기 · 진행 중':'여기 · 시작 전',cls:'here'};
  if(qi<cur)return {label:'지나왔을 수 있음 · 빈칸 '+(p.total-p.done),cls:'warn'};
  if(p.done||p.part)return {label:'준비 중',cls:'next'};
  if(prev&&prev.done<prev.total*0.5)return {label:'아직 멀음',cls:'lock'};
  return {label:'다음',cls:'next'};
}
function currentQuest(s){
  // 위치 = 활동(확정·추정·진행)이 있는 첫 미완 단계. 활동이 전혀 없으면 첫 미완 단계.
  const inc=i=>questProg(s,QUESTS[i]).done<QUESTS[i].req.length;
  const act=i=>{const p=questProg(s,QUESTS[i]);return p.done+p.part>0};
  for(let i=0;i<QUESTS.length;i++)if(inc(i)&&act(i))return i;
  for(let i=0;i<QUESTS.length;i++)if(inc(i))return i;
  return QUESTS.length-1}
function siteProg(s){let d=0,t=0;QUESTS.forEach(q=>{const p=questProg(s,q);d+=p.done;t+=p.total});return {done:d,total:t,pct:Math.round(d/t*100)}}
function relatedItems(s,q){return Object.values(S.items).filter(i=>i.site===s.name&&!['done','confirmed','cancel','requested'].includes(i.status)&&(i.quest===q.k||(!i.quest&&q.hint.some(h=>(i.text+' '+(i.makeq||'')).includes(h)))))}
function nextMove(s){
  const qi=currentQuest(s);const q=QUESTS[qi];
  const miss=q.req.filter(r=>reqOf(s,q.k,r.k).state!=='확정');
  const r=miss.find(x=>reqOf(s,q.k,x.k).state==='')||miss[0];
  return r?{q,r,st:reqOf(s,q.k,r.k)}:null;
}
function moveText(m){
  if(!m)return '전부 확정입니다. 결승선.';
  const {q,r,st}=m;
  const lead=st.state==='진행중'?'진행 중이라 마무리만 남았습니다':st.state==='추정'?`지금은 추정(${st.value||''})이라 확정이 필요합니다`:'아직 비어 있습니다';
  return `${q.n} › ${r.n} — ${lead}. ${r.how}`;
}
function moveAsk(r){if(r.gate)return '제가 계약·계산서 요청 문안 만들까요?';return r.type==='doc'?(r.order?`제가 ${r.n.replace(/발행|송부/,'').trim()} 초안 만들까요?`:'제가 문안 만들까요?'):r.type==='fact'?'제가 협의 문안 만들까요?':r.type==='ext'?'제가 확인 요청 문안 만들까요?':'제가 시공팀 의뢰서 초안 만들까요?'}


/* ============ 공용 UI ============ */
const sheet=document.getElementById('sheet'), sheetBox=document.getElementById('sheetBox');
function openSheet(html,title){
  sheetBox.innerHTML='<div class="sheetbar"><span class="ttl">'+esc(title||'')+'</span><button class="b" onclick="closeSheet()">✕ 닫기</button></div>'+html;
  sheet.hidden=false;sheetBox.scrollTop=0}
function closeSheet(){sheet.hidden=true;sheetBox.innerHTML=''}
sheet.addEventListener('click',e=>{if(e.target===sheet)closeSheet()});
function micSheet(title,hint,initial,cb){
  openSheet(`<div class="hint">${esc(hint||'')}</div>
    <textarea id="micText">${esc(initial||'')}</textarea>
    <div class="btns"><button class="b mic" id="micBtn">🎙 말하기</button><button class="b pri" id="micOk">확인</button><button class="b ghost" id="micCancel">취소</button></div>`,title);
  const ta=document.getElementById('micText');
  const R=window.SpeechRecognition||window.webkitSpeechRecognition;
  const mb=document.getElementById('micBtn');
  if(!R){mb.textContent='이 브라우저는 말하기 미지원';mb.disabled=true}
  else{let rec=null;mb.onclick=()=>{
    if(rec){rec.stop();return}
    rec=new R();rec.lang='ko-KR';rec.interimResults=true;rec.continuous=false;
    const base=ta.value?ta.value.trim()+' ':'';
    rec.onresult=e=>{let s='';for(const r of e.results)s+=r[0].transcript;ta.value=base+s};
    rec.onend=()=>{rec=null;mb.classList.remove('rec');mb.textContent='🎙 말하기'};
    rec.onerror=()=>{rec=null;mb.classList.remove('rec');mb.textContent='🎙 말하기';toast('마이크를 못 썼습니다. 글로 적어 주십시오')};
    rec.start();mb.classList.add('rec');mb.textContent='● 듣는 중 (누르면 멈춤)';
  }}
  document.getElementById('micOk').onclick=()=>{const v=ta.value.trim();closeSheet();cb(v)};
  document.getElementById('micCancel').onclick=closeSheet;
  setTimeout(()=>ta.focus(),50);
}
function draftSheet(title,text,site,doneLine){
  openSheet(`<div class="hint">금액·수량·기한의 [ ] 는 프로님이 채우십니다. 복사해 그룹웨어·카톡에 붙이시면 됩니다.</div>
    <pre class="draft" id="draftText">${esc(text)}</pre>
    <div class="btns"><button class="b pri" id="dCopy">복사</button><button class="b" id="dMail">메일로</button>${doneLine?'<button class="b" id="dDone">보냈음 (완료)</button>':''}<button class="b ghost" id="dClose">닫기</button></div>`,title);
  document.getElementById('dCopy').onclick=()=>copy(text);
  document.getElementById('dMail').onclick=()=>{const [subj,...rest]=text.split('\n');location.href='mailto:?subject='+encodeURIComponent(subj.replace(/^제목\s*:\s*/,''))+'&body='+encodeURIComponent(rest.join('\n').trim())};
  const dd=document.getElementById('dDone');if(dd)dd.onclick=()=>{doneLine();closeSheet()};
  document.getElementById('dClose').onclick=closeSheet;
}
async function copy(t){try{await navigator.clipboard.writeText(t);toast('복사했습니다')}catch(e){const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');toast('복사했습니다')}catch(_){toast('길게 눌러 복사해 주십시오')}ta.remove()}}


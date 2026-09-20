/* ============ 보내기 ============ */
function sendOutbox(){
  if(!S.outbox.length)return;
  const subj=`[KM] 회신 ${yymmdd()} · ${S.outbox.length}건`;
  const body=S.outbox.map(o=>o.line).join('\n')+'\n\n(KM 손바닥 v6.8 에서 보냄 · 줄 앞 번호가 있는 줄은 48번이 읽고, 없는 줄은 「못 알아들은 답」 으로 클로드가 읽습니다)';
  const tooLong=body.length>1800;
  openSheet(`${tooLong?'<div class="gate">⚠ 본문이 '+body.length+'자입니다. 메일 앱에 따라 2,000자가 넘으면 열리지 않습니다. 안 열리면 「복사만」 을 눌러 메일에 붙여 주십시오.</div>':''}<div class="hint">메일 한 통으로 갑니다. 받는 곳 ${esc(S.settings.mailTo)}${S.settings.cc?' · 사본 '+esc(S.settings.cc):''}</div>
  <pre class="draft">${esc(body)}</pre>
  <div class="btns"><button class="b pri" id="sbMail">메일 앱으로</button><button class="b" id="sbCopy">복사만</button><button class="b" id="sbSent">보냈음 (비우기)</button><button class="b ghost" id="sbX">닫기</button></div>`,'PC로 보내기 '+S.outbox.length+'건');
  document.getElementById('sbMail').onclick=()=>{location.href='mailto:'+encodeURIComponent(S.settings.mailTo)+(S.settings.cc?'?cc='+encodeURIComponent(S.settings.cc)+'&':'?')+'subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(body)};
  document.getElementById('sbCopy').onclick=()=>copy(body);
  document.getElementById('sbSent').onclick=()=>{addLog('보냄','',subj+' ('+S.outbox.length+'줄)');S.outbox=[];saveMeta();closeSheet();render();toast('비웠습니다. 이력에 남아 있습니다')};
  document.getElementById('sbX').onclick=closeSheet;
}


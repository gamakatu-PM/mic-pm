/* ============ 시작 (2호) ============ */
/* 글씨 크기 3단 : 0 보통 17px / 1 크게 20px / 2 아주 크게 23px
   고칠 곳은 여기 한 곳. km.css 의 body.big / body.big2 와 짝입니다. */
const FS_NAME=['보통','크게','아주 크게'];
function fsGet(){
  let n=S.settings.fs;
  if(n===undefined||n===null) n=S.settings.big?1:0;
  n=Number(n); if(!(n>=0&&n<=2)) n=0;
  return n;
}
function fsApply(){
  const n=fsGet();
  document.body.classList.toggle('big',n===1);
  document.body.classList.toggle('big2',n===2);
  const lv=document.getElementById('fsLv'); if(lv) lv.textContent=FS_NAME[n];
  const dn=document.getElementById('fsDn'); if(dn) dn.disabled=(n===0);
  const up=document.getElementById('fsUp'); if(up) up.disabled=(n===2);
}
function fsSet(n){
  n=Math.max(0,Math.min(2,n));
  S.settings.fs=n; S.settings.big=(n>=1);
  fsApply(); saveMeta();
  const cb=document.getElementById('setBig'); if(cb) cb.checked=!!S.settings.big;
}
document.getElementById('fsUp').onclick=()=>fsSet(fsGet()+1);
document.getElementById('fsDn').onclick=()=>fsSet(fsGet()-1);

fsApply();
render();
initDb();

/* ============ 접기 (3호에만 있는 것) ============
   프로님 : 2호는 글씨·단추는 좋은데 너무 많이 민다(창고 13.5번).
   그래서 카드를 「제목 + 두 줄 + 단추 하나」 까지만 보이게 접고,
   누르면 펴지게 한다. 기능은 하나도 줄이지 않는다 — 가려질 뿐이다.

   고칠 곳은 이 파일 하나. km.css 의 .folded / .foldbtn 과 짝이다.
   - 접는 높이  : km.css 의 --foldh
   - 접지 않을 것 : NOFOLD 에 선택자를 더한다
   - 펴 둔 것 기억 : FOLD_OPEN (제목 글이 열쇠. 다시 그려도 펴진 채로 남는다) */

const FOLD_SEL='.card, .notice, .inboxbar, .feedbar';   // 접기를 적용할 것
const NOFOLD='#v-set';                    // 설정 화면은 입력칸이 있어 접지 않는다
const FOLD_OPEN=new Set();                // 프로님이 펴 두신 카드
let foldBusy=false;

function foldKey(c){
  const t=c.querySelector('.t,.q,b');
  return ((t?t.textContent:c.textContent)||'').replace(/\s+/g,' ').trim().slice(0,70);
}
function foldSkip(c){
  return c.closest(NOFOLD) || c.classList.contains('jcard') || c.classList.contains('nofold')
      || c.querySelector('input,textarea,select');
}
function foldSet(c,open){
  const k=foldKey(c);
  if(open)FOLD_OPEN.add(k); else FOLD_OPEN.delete(k);
  c.classList.toggle('folded',!open);
  const b=c.querySelector(':scope > .foldbtn');
  if(b)b.textContent=open?'− 접기':(c.classList.contains('notice')?'＋ 설명 보기':'＋ 더 보기');
}
function applyFold(){
  if(foldBusy)return; foldBusy=true;
  try{
    const v=document.querySelector('.view:not([hidden])'); if(!v)return;
    const cards=[...v.querySelectorAll(FOLD_SEL)].filter(c=>!foldSkip(c));
    if(!cards.length)return;

    /* 현장 200곳·할 일 800건에서도 멈추지 않게 읽기와 쓰기를 갈라 놓는다.
       카드마다 재면 카드 수만큼 화면을 다시 그린다(800번). 아래처럼 세 번에 나누면 두 번이면 끝난다. */
    // ① 쓰기 : 제목은 밖에 두고 그 아래 본문만 감싼다 (제목은 접혀도 항상 보여야 한다)
    cards.forEach(c=>{
      if(!c.querySelector(':scope > .foldbody')){
        const w=document.createElement('div'); w.className='foldbody';
        // 제목 줄(.id/.t/.q)까지는 밖에 남긴다
        let head=null;
        for(const ch of [...c.children]){
          if(ch.classList&&(ch.classList.contains('id')||ch.classList.contains('t')||ch.classList.contains('q'))){head=ch;continue}
          break;
        }
        const from=head?head.nextSibling:c.firstChild;
        let n=from;
        while(n){const nx=n.nextSibling;w.appendChild(n);n=nx}
        c.appendChild(w);
      }
      c.classList.add('foldable');
    });
    // ② 읽기 : 한 번에 다 잰다 (--foldh 는 전체가 같은 값이라 한 번만 읽는다)
    const lim=parseInt(getComputedStyle(document.body).getPropertyValue('--foldh'),10)||104;
    const lim2=Math.round(lim*0.5);   // 안내 글·알림 띠는 더 짧게 (본문이 아니라 설명이라서)
    const limOf=c=>c.classList.contains('card')?lim:lim2;
    const tall=cards.map(c=>c.querySelector(':scope > .foldbody').scrollHeight>limOf(c)+24);
    // ③ 쓰기 : 단추를 붙이고 접는다
    cards.forEach((c,i)=>{
      let b=c.querySelector(':scope > .foldbtn');
      if(!tall[i]){ c.classList.remove('folded'); if(b)b.remove(); return }
      if(!b){
        b=document.createElement('button'); b.type='button'; b.className='foldbtn';
        b.addEventListener('click',e=>{e.stopPropagation();foldSet(c,c.classList.contains('folded'))});
        c.appendChild(b);
      }
      const body=c.querySelector(':scope > .foldbody');
      // 카드 자체에 할 일이 없으면 본문을 눌러도 펴진다 (단추는 제외)
      if(!c.hasAttribute('onclick') && !body.dataset.tap){
        body.dataset.tap='1';
        body.addEventListener('click',e=>{
          if(e.target.closest('button,a,input,textarea,select,label'))return;
          if(c.classList.contains('folded')){e.stopPropagation();foldSet(c,true)}
        });
      }
      if(!c.classList.contains('card'))c.style.setProperty('--foldh',lim2+'px');
      foldSet(c,FOLD_OPEN.has(foldKey(c)));
    });
    foldBar(cards.length);
  }finally{foldBusy=false}
}
/* 전부 펴기 / 전부 접기 — 접힌 카드가 3장 넘으면 화면 맨 위에 띠가 생긴다 */
function foldAll(open){
  const v=document.querySelector('.view:not([hidden])'); if(!v)return;
  v.querySelectorAll('.foldable').forEach(c=>{if(c.querySelector(':scope > .foldbtn'))foldSet(c,open)});
  foldBar();
}
function foldBar(){
  const v=document.querySelector('.view:not([hidden])'); if(!v)return;
  /* 다른 화면에 남아 있는 띠는 치운다 (안 보이는 곳에 쌓이지 않게) */
  document.querySelectorAll('.view[hidden] > .foldbar').forEach(x=>x.remove());
  const n=v.querySelectorAll('.foldable > .foldbtn').length;
  let bar=v.querySelector(':scope > .foldbar');
  if(n<3){if(bar)bar.remove();return}
  const shut=v.querySelectorAll('.foldable.folded').length;
  if(!bar){
    bar=document.createElement('div'); bar.className='foldbar';
    const a=document.createElement('button'); a.type='button';
    a.addEventListener('click',()=>foldAll(true));
    const b=document.createElement('button'); b.type='button';
    b.addEventListener('click',()=>foldAll(false));
    bar.appendChild(a); bar.appendChild(b);
    v.insertBefore(bar,v.firstChild);
  }
  bar.children[0].textContent='전부 펴기 ('+shut+')';
  bar.children[1].textContent='전부 접기';
}

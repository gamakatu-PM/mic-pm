// KM 아침메일 모의 실행 — 구글 서비스를 가짜로 만들어 글이 제대로 나오는지 본다
const fs=require('fs'),path=require('path'),vm=require('vm');
const dir=path.join(__dirname,'..');
const src=fs.readFileSync(path.join(dir,'KM_아침메일.gs'),'utf8');
const csvName=process.argv[2]||'아침대장_260921.csv';
const csvText=fs.readFileSync(path.join(dir,csvName),'utf8');
const 오늘=process.argv[3]||'2026-09-21';

function parseCsv(t){const out=[];let row=[],cur='',q=false;
 for(let i=0;i<t.length;i++){const c=t[i];
  if(q){ if(c==='"'){ if(t[i+1]==='"'){cur+='"';i++;} else q=false; } else cur+=c; }
  else if(c==='"')q=true;
  else if(c===','){row.push(cur);cur='';}
  else if(c==='\n'){row.push(cur);cur='';out.push(row);row=[];}
  else if(c!=='\r')cur+=c; }
 if(cur!==''||row.length){row.push(cur);out.push(row);} return out.filter(r=>r.length>1||r[0]!=='');}

const sent=[]; let logged=null;
const file={getName:()=>csvName,getBlob:()=>({getDataAsString:()=>csvText})};
const folder={getFiles:()=>{let done=false;return{hasNext:()=>!done,next:()=>{done=true;return file;}};},
 getFilesByName:()=>({hasNext:()=>false}),createFile:(n,c)=>{logged=c;return{};},getUrl:()=>'(모의)',
 getFoldersByName:()=>({hasNext:()=>true,next:()=>folder}),createFolder:()=>folder};
const ctx={
 DriveApp:{getFolderById:()=>folder},
 GmailApp:{sendEmail:(to,s,b,o)=>sent.push({to,s,html:o&&o.htmlBody||b})},
 MimeType:{CSV:'text/csv'},
 Logger:{log:m=>console.log('[log]',m)},
 ScriptApp:{getProjectTriggers:()=>[],newTrigger:()=>({timeBased:()=>({everyDays:()=>({atHour:()=>({nearMinute:()=>({inTimezone:()=>({create:()=>{}})})})})})})},
 Utilities:{parseCsv,formatDate:(d,tz,f)=>{
   if(f==='u'){const n=new Date(오늘+'T00:00:00Z').getUTCDay();return String(n===0?7:n);}
   if(f==='yyyy-MM-dd')return 오늘;
   if(f==='HH:mm')return '07:00'; return 오늘;}},
 console};
vm.createContext(ctx);
vm.runInContext(src+'\n;__r=testSendNow();',ctx);
console.log('결과 :',ctx.__r);
let bad=0;
if(sent.length!==3){console.log('✗ 3통이 아님:',sent.length);bad++;}
sent.forEach(m=>{
 console.log('\n──────',m.s,'→',m.to);
 console.log(m.html.replace(/<style>[\s\S]*?<\/style>/,'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').slice(0,700));
 if(!/KM-\d/.test(m.html)&&!/없습니다/.test(m.html)){console.log('✗ 코드 없음');bad++;}
 if(/undefined|NaN/.test(m.html)){console.log('✗ undefined/NaN 섞임');bad++;}
});
if(!/KM-004/.test(sent[1].html)){console.log('✗ ②에 확정 항목 없음');bad++;}
if(!/KM-010/.test(sent[0].html)){console.log('✗ ①에 제안 항목 없음');bad++;}
if(!/진행중/.test(sent[0].html)){console.log('✗ 회신 단추 없음');bad++;}
console.log('\n발송로그 :',logged?logged.trim().split('\n').pop():'(없음)');
console.log(bad?('✗ 실패 '+bad+'건'):'✓ 모의 실행 통과');
process.exit(bad?1:0);

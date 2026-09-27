/*************************************************************
 * KM 카톡 비서 - 카카오 i 오픈빌더 스킬서버  (Google Apps Script)
 * 한국마이크로닉(주) 배성윤 차장 전용 · v1 (2026-09-19)
 *
 * 하는 일
 *   카톡에 「3 완료」 라고 치시면
 *     → 카카오 채널 → 오픈빌더 → 이 스크립트
 *     → ① 구글시트 「받은말」 에 한 줄 쌓고
 *       ② 클로드가 읽는 메일로 한 통 보내고
 *       ③ 5초 안에 「접수했습니다」 라고 즉답
 *
 *   카톡에 「할일」 이라고 치시면
 *     → 클로드가 미리 채워 둔 「보낼말」 시트를 그대로 즉답 (메일 안 여셔도 됨)
 *
 * 처음 한 번만 하실 것 (설치안내 파일 참조)
 *   1) 아래 TOKEN 을 아무도 모르는 글자로 바꾸십시오
 *   2) MAIL_TO 가 클로드가 읽는 메일 주소가 맞는지 보십시오
 *   3) 배포 > 새 배포 > 웹 앱 / 실행 사용자=나 / 액세스=모든 사용자
 *   4) 나온 주소 뒤에 ?k=TOKEN 을 붙여 오픈빌더 스킬 URL 에 넣으십시오
 *************************************************************/

var TOKEN   = 'km2026change';                 // ★ 반드시 바꾸십시오
var MAIL_TO = 'gamakatu0924@gmail.com';       // 클로드가 읽는 메일함
var SHEET   = 'KM_카톡';                       // 없으면 저절로 만들어집니다
var TAB_IN  = '받은말';
var TAB_OUT = '보낼말';

/* ---------- 카카오가 부르는 자리 ---------- */
function doPost(e) {
  try {
    if (!e || !e.parameter || e.parameter.k !== TOKEN) return reply('열쇠가 맞지 않습니다.');

    var body = JSON.parse(e.postData.contents);
    var utter = ((body.userRequest || {}).utterance || '').trim();
    var who   = (((body.userRequest || {}).user || {}).id || '').slice(0, 12);
    if (!utter) return reply('빈 메시지입니다.');

    // ① 클로드가 미리 채워 둔 답이 있으면 그것부터 (즉답 · 5초 제한 안에 들어옵니다)
    var canned = lookOut(utter);
    if (canned) return reply(canned);

    // ② 회신으로 보고 기록한다
    var p = parseLine(utter);
    logIn(utter, who, p);
    notify(utter, p);

    if (p.code) {
      return reply('접수했습니다.\n\n' + p.code + ' → ' + p.cmd +
                   (p.val ? ('\n내용 : ' + p.val) : '') +
                   '\n\n대장에 반영하고 결과는 아침 한 장에 올려 드리겠습니다.');
    }
    return reply('적어 두었습니다.\n\n「' + cut(utter, 40) + '」\n\n' +
                 '번호를 같이 주시면 바로 그 줄에 반영됩니다. 예) 3 완료 · 6 아니야 32실이 맞아');
  } catch (err) {
    try { notify('[오류] ' + err, {}); } catch (e2) {}
    return reply('잠깐 문제가 있었습니다. 다시 한 번 보내 주십시오.');
  }
}

function doGet(e) {
  if (!e || !e.parameter || e.parameter.k !== TOKEN) {
    return ContentService.createTextOutput('no').setMimeType(ContentService.MimeType.TEXT);
  }
  return ContentService.createTextOutput('KM 카톡 비서 살아 있습니다 · ' + now())
                       .setMimeType(ContentService.MimeType.TEXT);
}

/* ---------- 말 알아듣기 (48번 회신읽기와 같은 낱말) ---------- */
var WIP  = ['진행중','진행 중','하는중','하고있','착수','시작했','보냈어','보냄','접수','넣었어'];
var DONE = ['완료','했어','했음','끝','됐어','됐음','오케이','처리','ok'];
var OKAY = ['확인','맞아','맞음','그대로','좋아','예스','yes'];
var NOPE = ['아니야','아냐','아님','틀려','틀렸','수정','바꿔','바꾸','고쳐','변경'];
var MAKE = ['만들어','만들까','작성해','써줘','초안'];
var KILL = ['취소','빼','필요없','안해','없앰','삭제'];
var HOLD = ['미뤄','연기','나중','다음주','보류','뒤로'];
var ASKW = ['물어봐','확인해봐','알아봐','체크해'];

function has(s, arr) {
  for (var i = 0; i < arr.length; i++) if (s.indexOf(arr[i]) >= 0) return true;
  return false;
}

function parseLine(line) {
  var s = String(line || '').trim().replace(/^[-•·\s]+/, '');
  var m = s.match(/^\s*(?:KM[-\s]?)?(\d{1,4})\s*[.)\]:]?\s*(.*)$/i);
  var out = { code: '', cmd: '', val: '', raw: s };
  if (!m) return out;
  out.code = 'KM-' + ('00' + m[1]).slice(-3);
  var r = (m[2] || '').trim();
  if (!r)              { out.cmd = '확인';   return out; }
  out.val = r;
  if (has(r, KILL))    { out.cmd = '취소';   return out; }
  if (has(r, NOPE))    { out.cmd = '수정';   return out; }
  if (has(r, HOLD))    { out.cmd = '미룸';   return out; }
  if (has(r, MAKE))    { out.cmd = '만들기'; return out; }
  if (has(r, ASKW))    { out.cmd = '물어봄'; return out; }
  if (has(r, WIP))     { out.cmd = '진행중'; return out; }
  if (has(r, DONE))    { out.cmd = '완료';   return out; }
  if (has(r, OKAY))    { out.cmd = '확인';   return out; }
  out.cmd = '?';
  return out;
}

/* ---------- 시트 ---------- */
function book() {
  var it = DriveApp.getFilesByName(SHEET);
  if (it.hasNext()) return SpreadsheetApp.open(it.next());
  var ss = SpreadsheetApp.create(SHEET);
  var a = ss.getActiveSheet(); a.setName(TAB_IN);
  a.appendRow(['시각', '보낸이', '원문', '코드', '명령', '값', '처리']);
  var b = ss.insertSheet(TAB_OUT);
  b.appendRow(['열쇠말', '내용']);
  b.appendRow(['할일', '아직 없습니다. 클로드가 아침에 채웁니다.']);
  b.appendRow(['도움말', '이렇게 보내시면 됩니다.\n3 완료 · 3 진행중 · 6 아니야 32실이 맞아\n7 만들어줘 · 4 미뤄 다음주\n\n「할일」 이라고 치시면 오늘 할 것이 나옵니다.']);
  return ss;
}

function logIn(utter, who, p) {
  var sh = book().getSheetByName(TAB_IN);
  sh.appendRow([now(), who, utter, p.code, p.cmd, p.val, '']);
}

/* 클로드가 미리 채워 둔 답 (열쇠말이 앞에 들어 있으면 그대로 돌려준다) */
function lookOut(utter) {
  var sh = book().getSheetByName(TAB_OUT);
  if (!sh) return '';
  var v = sh.getDataRange().getValues();
  var u = String(utter).replace(/\s/g, '');
  for (var i = 1; i < v.length; i++) {
    var key = String(v[i][0] || '').replace(/\s/g, '');
    if (key && u.indexOf(key) === 0) return String(v[i][1] || '');
  }
  return '';
}

/* ---------- 클로드가 읽는 메일로 알림 ---------- */
function notify(utter, p) {
  MailApp.sendEmail({
    to: MAIL_TO,
    subject: '[KM카톡] ' + (p.code ? (p.code + ' ' + p.cmd) : '메모') + ' · ' + now(),
    body: '카톡으로 들어온 회신입니다.\n\n' +
          '원문 : ' + utter + '\n' +
          '번호 : ' + (p.code || '(없음)') + '\n' +
          '명령 : ' + (p.cmd || '(없음)') + '\n' +
          '내용 : ' + (p.val || '') + '\n\n' +
          '시트 : ' + book().getUrl() + '\n'
  });
}

/* ---------- 도우미 ---------- */
function reply(text) {
  var out = { version: '2.0', template: { outputs: [{ simpleText: { text: String(text) } }] } };
  return ContentService.createTextOutput(JSON.stringify(out))
                       .setMimeType(ContentService.MimeType.JSON);
}
function now() {
  return Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm');
}
function cut(s, n) {
  s = String(s); return s.length > n ? s.slice(0, n) + '…' : s;
}

/* ---------- 설치 후 한 번 눌러 확인하는 자리 ---------- */
function 설치확인() {
  var ss = book();
  Logger.log('시트 : ' + ss.getUrl());
  Logger.log('해석 시험 : ' + JSON.stringify(parseLine('3 완료')));
  Logger.log('해석 시험 : ' + JSON.stringify(parseLine('6 아니야 32실이 맞아')));
  Logger.log('해석 시험 : ' + JSON.stringify(parseLine('1 진행중')));
  MailApp.sendEmail(MAIL_TO, '[KM카톡] 설치 확인 · ' + now(),
                    '카톡 비서가 설치되었습니다.\n시트 : ' + ss.getUrl());
  return ss.getUrl();
}

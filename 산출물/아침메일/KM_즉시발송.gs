/**
 * KM 즉시발송 v1 (2026-09-22)
 * 한국마이크로닉(주) 배성윤 차장 전용.
 *
 * 하는 일 : 구글 드라이브 「KM_아침메일」 폴더에 회의록 정리 파일이 들어오면
 *           5분 안에 bsy@micronic.co.kr 로 보낸다. 07:00 을 기다리지 않는다.
 *
 * 흐름
 *   PC 에서 ★회의록_한방에.py 를 누름
 *     -> 파이썬이 「회의록정리_YYMMDD.txt」 를 드라이브 KM_아침메일 폴더에 올림
 *     -> (5분 안에) 이 스크립트가 그것을 보고 메일로 보냄
 *
 * 두 번 보내지 않는다
 *   보낸 파일은 Drive 속성(보냄=시각)에 표시하고 「즉시발송_로그.csv」 에도 남긴다.
 *   같은 파일을 다시 고쳐 올리면 크기가 달라지므로 다시 보낸다(고친 판을 받으시게).
 *
 * 설치 (처음 한 번)
 *   1) script.google.com 에서 이 파일 내용을 붙여 넣는다
 *   2) setupNow() 를 한 번 실행하고 권한을 허락한다
 *   3) 끝. 이후 5분마다 혼자 돈다
 *
 * ※ KM_아침메일.gs(07:00 세 통)와 서로 건드리지 않는다. 트리거 이름이 다르다.
 */

var IM = {
  VERSION: 'v1 2026-09-22',
  TZ: 'Asia/Seoul',
  // ★ 2026-09-23 고침 : KM_아침메일 폴더가 두 개여서 엇갈려 있었다.
  //    파이썬(★회의록_한방에.py)은 「내 드라이브\KM_아침메일」 에 쓴다.
  //    그래서 그 폴더를 id 로 직접 잡는다. 이름으로 찾으면 또 엇갈린다.
  FOLDER_ID: '1uIon56BcKjSxIo5rCUyVzLDQLn3tZEZB',   // 내 드라이브 바로 밑 KM_아침메일
  PREFIX: '회의록정리_',          // 이 이름으로 시작하는 .txt 만 본다
  TO: 'bsy@micronic.co.kr',
  EVERY_MIN: 5,                   // 1 · 5 · 10 · 15 · 30 만 됩니다 (구글 제한)
  LOG_NAME: '즉시발송_로그.csv',
  MAX_BODY: 90000,                // 한 통에 담을 글자 수. 넘으면 나눠 보낸다
  PROP_KEY: 'km_sent'             // 파일에 붙이는 「보냄」 표시
};

/* ═════════════════════════ 설치 ═════════════════════════ */

/** 처음 한 번만 누르십시오. */
function setupNow() {
  installTrigger_();
  var f = folder_();
  var msg = '폴더 : ' + f.getUrl() + '\n트리거 : ' + IM.EVERY_MIN + '분마다 watchDrive\n받는 곳 : ' + IM.TO;
  Logger.log(msg);
  return msg;
}

function installTrigger_() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'watchDrive') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('watchDrive').timeBased().everyMinutes(IM.EVERY_MIN).create();
}

/** 트리거를 떼고 싶을 때. */
function stopWatching() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'watchDrive') ScriptApp.deleteTrigger(t);
  });
  return '멈췄습니다.';
}

/* ═════════════════════════ 본체 ═════════════════════════ */

/** 5분마다 구글이 부른다. 새 파일이 있으면 보낸다. */
function watchDrive() {
  var list = newFiles_();
  if (!list.length) return 0;
  var sent = 0;
  for (var i = 0; i < list.length; i++) {
    try {
      sendOne_(list[i]);
      mark_(list[i]);
      sent++;
    } catch (e) {
      log_(list[i].getName(), '실패 : ' + e);
    }
  }
  return sent;
}

/** 아직 안 보낸 파일 목록. 이름순(오래된 것 먼저). */
function newFiles_() {
  var f = folder_();
  var it = f.getFiles();
  var out = [];
  while (it.hasNext()) {
    var file = it.next();
    var name = file.getName();
    if (name.indexOf(IM.PREFIX) !== 0) continue;
    if (name.slice(-4).toLowerCase() !== '.txt') continue;
    if (stamp_(file) === sentStamp_(file)) continue;   // 이미 보냄 (크기·수정시각 같음)
    out.push(file);
  }
  out.sort(function (a, b) { return a.getName() < b.getName() ? -1 : 1; });
  return out;
}

/** 파일의 지금 상태. 크기+수정시각이 바뀌면 다른 것으로 본다. */
function stamp_(file) {
  return file.getSize() + '|' + file.getLastUpdated().getTime();
}

function sentStamp_(file) {
  try { return file.getDescription() ? String(file.getDescription()) : ''; }
  catch (e) { return ''; }
}

function mark_(file) {
  try { file.setDescription(stamp_(file)); } catch (e) {}
  log_(file.getName(), '보냄');
}

/** 한 파일을 메일로. 길면 나눠 보낸다. */
function sendOne_(file) {
  var text = file.getBlob().getDataAsString('UTF-8');
  var head = headline_(file.getName(), text);
  var parts = split_(text, IM.MAX_BODY);

  for (var i = 0; i < parts.length; i++) {
    var subj = head + (parts.length > 1 ? '  (' + (i + 1) + '/' + parts.length + ')' : '');
    var body = (parts.length > 1 ? '※ 길어서 ' + parts.length + '통으로 나눠 보냅니다. 이것은 ' + (i + 1) + '번째입니다.\n\n' : '')
             + parts[i];
    MailApp.sendEmail({ to: IM.TO, subject: subj, body: body });
  }
}

/** 제목 만들기. 본문 둘째 줄의 「협의 N건 · M개 현장」 을 그대로 쓴다. */
function headline_(fname, text) {
  var ymd = (fname.match(/(\d{6})/) || [])[1] || '';
  var d = ymd ? ('20' + ymd.slice(0, 2) + '-' + ymd.slice(2, 4) + '-' + ymd.slice(4, 6)) : '';
  var cnt = '';
  var lines = text.split('\n');
  for (var i = 0; i < Math.min(lines.length, 6); i++) {
    if (/협의\s*\d+건/.test(lines[i])) { cnt = lines[i].trim(); break; }
  }
  return '[KM] 회의록 정리 ' + (d || ymd) + (cnt ? ' · ' + cnt : '');
}

/** 글자 수로 자르되 줄 가운데를 자르지 않는다. */
function split_(text, max) {
  if (text.length <= max) return [text];
  var out = [], buf = '';
  var lines = text.split('\n');
  for (var i = 0; i < lines.length; i++) {
    if (buf.length + lines[i].length + 1 > max && buf) { out.push(buf); buf = ''; }
    buf += (buf ? '\n' : '') + lines[i];
  }
  if (buf) out.push(buf);
  return out;
}

/* ═════════════════════════ 폴더·로그 ═════════════════════════ */

function folder_() {
  return DriveApp.getFolderById(IM.FOLDER_ID);
}

/** 덮어쓰지 않고 뒤에 붙인다. */
function log_(name, what) {
  try {
    var f = folder_();
    var when = Utilities.formatDate(new Date(), IM.TZ, 'yyyy-MM-dd HH:mm');
    var line = when + ',' + name + ',' + what + '\n';
    var it = f.getFilesByName(IM.LOG_NAME);
    if (it.hasNext()) {
      var file = it.next();
      file.setContent(file.getBlob().getDataAsString('UTF-8') + line);
    } else {
      f.createFile(IM.LOG_NAME, '시각,파일,결과\n' + line, MimeType.PLAIN_TEXT);
    }
  } catch (e) {}
}

/* ═════════════════════════ 시험 ═════════════════════════ */

/** 보내지 않고 무엇을 보낼지만 본다. */
function dryRun() {
  var list = newFiles_();
  if (!list.length) return '보낼 것이 없습니다.';
  var out = [];
  for (var i = 0; i < list.length; i++) {
    var t = list[i].getBlob().getDataAsString('UTF-8');
    out.push(headline_(list[i].getName(), t) + '   (' + t.length + '자, ' + split_(t, IM.MAX_BODY).length + '통)');
  }
  Logger.log(out.join('\n'));
  return out.join('\n');
}

/** 지금 당장 한 번 돌린다. */
function sendNow() {
  var n = watchDrive();
  return n + '통 보냈습니다.';
}

/** 「보냄」 표시를 지워 전부 다시 보내게 한다. 조심해서 쓰십시오. */
function resendAll() {
  var it = folder_().getFiles(), n = 0;
  while (it.hasNext()) {
    var f = it.next();
    if (f.getName().indexOf(IM.PREFIX) === 0) { try { f.setDescription(''); n++; } catch (e) {} }
  }
  return n + '개를 다시 보낼 수 있게 했습니다. sendNow() 를 누르십시오.';
}

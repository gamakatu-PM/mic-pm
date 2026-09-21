/**
 * KM 아침메일 — 보내는 것은 구글이 한다  (v1, 2026-09-21)
 * 한국마이크로닉(주) 배성윤 프로 전용
 *
 * 왜 있나
 *   아침 3통이 9/19부터 끊겼다. 원인은 스케줄러가 아니라 "보내던 것이 사람(클로드)" 이었기 때문.
 *   PC 는 자료만 올려 두고(km_morning_push.py), 보내는 것은 이 스크립트가 매일 07:00 에 한다.
 *   그래서 PC 가 꺼져 있어도, 새 창이 없어도 메일이 온다.
 *
 * 쓰는 순서 (자세한 것은 설치하는법.md)
 *   1) 아래 설정의 암호를 바꾼다
 *   2) 배포 → 새 배포 → 웹 앱 (실행: 나 / 접근: 모든 사용자) → 주소를 복사
 *   3) 함수 목록에서 `설치` 를 한 번 실행한다 (07:00 트리거가 걸린다)
 *   4) PC 에서 km_morning_push.py 를 한 번 돌린다
 *   5) `시험발송` 을 눌러 지금 한 번 받아 본다
 */

var 설정 = {
  받는사람: 'bsy@micronic.co.kr',
  암호: 'km-2609-여기를-바꾸십시오',           // ← push 쪽 설정.ini 의 secret 과 같아야 한다
  폴더ID: '16TXRgGJ7XxFhCq71EVY9l1DYIA9Ewj_U', // KM_블록작업
  파일명: 'km_morning.json',
  보내는시각: 7,                                 // 07:00 (스크립트 시간대 = 서울로 맞출 것)
  자료없을때알림: true                           // PC 자료가 없으면 한 줄짜리 알림을 보낸다
};

// ───────────────────────────────────────── PC 가 올릴 때

function doPost(e) {
  try {
    var 짐 = JSON.parse(e.postData.contents);
    if (짐.secret !== 설정.암호) return _답({ok: false, why: '암호가 다릅니다'});
    if (!짐.parts || !짐.parts.length) return _답({ok: false, why: '편이 비었습니다'});

    _파일쓰기(JSON.stringify(짐));

    var 덧 = '';
    if (짐.sendNow) 덧 = _보내기(짐, ['meet'], '(새 회의록)');   // 7시 이후 회의록이 들어온 경우만
    return _답({ok: true, 받은편: 짐.parts.length, 자료기준: 짐.builtAt, 지금보냄: 덧});
  } catch (err) {
    return _답({ok: false, why: String(err)});
  }
}

function doGet() { return _답({ok: true, 살아있음: true, 마지막: _자료().builtAt || '없음'}); }

// ───────────────────────────────────────── 매일 07:00

function 아침발송() {
  var 짐 = _자료();
  if (!짐.parts) {
    if (설정.자료없을때알림) {
      GmailApp.sendEmail(설정.받는사람,
        '[KM] 아침 메일 — PC 자료가 없습니다 ' + _오늘(),
        '',
        {htmlBody: '<div style="font-family:맑은 고딕,sans-serif;font-size:14px">' +
          '<b>아직 한 번도 자료가 올라오지 않았습니다.</b><br>' +
          'PC 에서 36번(★KM_도면넣고_여기클릭) 또는 <code>아침메일_보내기.bat</code> 을 한 번 눌러 주십시오.' +
          '</div>'});
    }
    return;
  }
  _보내기(짐, null, '');
}

/** 편을 골라 보낸다. 같은 날 같은 편은 두 번 가지 않는다. */
function _보내기(짐, 고를것, 꼬리) {
  var 기록 = PropertiesService.getScriptProperties();
  var 오늘 = _오늘();
  var 보낸것 = [];

  짐.parts.forEach(function (편) {
    if (고를것 && 고를것.indexOf(편.key) < 0) return;
    var 열쇠 = 'sent_' + 오늘 + '_' + 편.key;
    if (기록.getProperty(열쇠)) return;                      // 이미 오늘 갔다

    var 제목 = 편.subject + _묵은표시(짐.builtAt) + (꼬리 ? ' ' + 꼬리 : '');
    GmailApp.sendEmail(설정.받는사람, 제목, '', {htmlBody: 편.html});
    기록.setProperty(열쇠, new Date().toISOString());
    보낸것.push(편.key);
  });

  if (보낸것.length) _적어두기(오늘 + ',' + 보낸것.join('|') + ',' + (짐.builtAt || '') + ',' + _지금());
  return 보낸것.join('|');
}

/** 자료가 어제 것보다 낡았으면 제목에 그 사실을 적는다 — 낡은 줄 모르고 믿으시면 안 되니까. */
function _묵은표시(기준) {
  if (!기준) return '';
  var 지난날 = Math.floor((new Date() - new Date(기준.replace(' ', 'T'))) / 86400000);
  if (지난날 <= 0) return '';
  if (지난날 === 1) return ' · 자료는 어제(' + 기준.substring(5, 10) + ') 것입니다';
  return ' · ⚠ 자료가 ' + 지난날 + '일 지났습니다(' + 기준.substring(5, 10) + ')';
}

// ───────────────────────────────────────── 차장님이 누르는 것

/** 07:00 트리거를 건다. 두 번 눌러도 겹치지 않는다. */
function 설치() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === '아침발송') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('아침발송').timeBased().atHour(설정.보내는시각).everyDays(1).create();
  Logger.log('매일 %s시 발송으로 걸었습니다. 시간대 : %s',
             설정.보내는시각, Session.getScriptTimeZone());
}

/** 지금 한 번 받아 본다 (오늘 이미 간 편은 건너뛴다). */
function 시험발송() { 아침발송(); }

/** 오늘 것을 다시 받아 보고 싶을 때 — 보냈다는 표시를 지운다. */
function 오늘다시() {
  var 기록 = PropertiesService.getScriptProperties(), 오늘 = _오늘();
  기록.getKeys().forEach(function (k) { if (k.indexOf('sent_' + 오늘) === 0) 기록.deleteProperty(k); });
  Logger.log('오늘 표시를 지웠습니다. 시험발송 을 누르시면 다시 옵니다.');
}

function 상태보기() {
  var 짐 = _자료();
  Logger.log('자료기준 : %s / 편 : %s / 시간대 : %s / 트리거 : %s',
    짐.builtAt || '없음',
    짐.parts ? 짐.parts.map(function (p) { return p.key; }).join(' ') : '없음',
    Session.getScriptTimeZone(),
    ScriptApp.getProjectTriggers().map(function (t) { return t.getHandlerFunction(); }).join(' ') || '없음');
}

// ───────────────────────────────────────── 속

function _폴더() { return DriveApp.getFolderById(설정.폴더ID); }

function _파일쓰기(글) {
  var 있는것 = _폴더().getFilesByName(설정.파일명);
  if (있는것.hasNext()) 있는것.next().setContent(글);
  else _폴더().createFile(설정.파일명, 글, MimeType.PLAIN_TEXT);
}

function _자료() {
  var 있는것 = _폴더().getFilesByName(설정.파일명);
  if (!있는것.hasNext()) return {};
  try { return JSON.parse(있는것.next().getBlob().getDataAsString('UTF-8')); }
  catch (e) { return {}; }
}

function _적어두기(줄) {
  var 이름 = 'km_morning_log.csv';
  var 있는것 = _폴더().getFilesByName(이름);
  if (있는것.hasNext()) {
    var f = 있는것.next();
    f.setContent(f.getBlob().getDataAsString('UTF-8') + 줄 + '\n');
  } else {
    _폴더().createFile(이름, '날짜,보낸편,자료기준,보낸시각\n' + 줄 + '\n', MimeType.PLAIN_TEXT);
  }
}

function _오늘() { return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd'); }
function _지금() { return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'HH:mm'); }
function _답(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

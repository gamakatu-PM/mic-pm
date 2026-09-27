/**
 * KM 아침메일 v1 (2026-09-21)
 * 한국마이크로닉(주) 배성윤 차장 전용.
 *
 * 하는 일 : 평일 07:00 에 구글 서버가 혼자 돌면서 메일 3통을 보낸다.
 *   ① 답해 주십시오   - 아직 제안 등급이라 결정이 필요한 것
 *   ② 오늘 할 것       - 확정된 것. 날짜 지난 것이 맨 위
 *   ③ 어제 있었던 일   - 자료 상태·건수·답 못 받은 것
 *
 * 자료는 어디서 오나
 *   드라이브 폴더 「KM_블록작업 … / KM_아침메일」 안의 가장 최근 `아침대장_YYMMDD.csv`.
 *   그 파일은 클로드가 전날 또는 당일 06:40 에 올려 둔다.
 *   클로드가 못 올려도 이 스크립트는 **지난 자료로 그대로 보낸다** — 대신 머리에
 *   「자료가 n일 전 것입니다」 를 붙인다. 아무 말 없이 멈추지 않는 것이 핵심이다.
 *
 * 설치 : README.md 참조. 처음 한 번 setup() 만 실행하면 끝.
 */

var KM = {
  VERSION: 'v1 2026-09-21',
  TZ: 'Asia/Seoul',
  // ★ 2026-09-23 고침 : KM_아침메일 폴더가 두 개여서 엇갈려 있었다. id 로 직접 잡는다.
  FOLDER_ID: '1uIon56BcKjSxIo5rCUyVzLDQLn3tZEZB',   // 내 드라이브 바로 밑 KM_아침메일 (즉시발송과 같은 곳)
  FILE_PREFIX: '아침대장_',
  TO_FALLBACK: 'bsy@micronic.co.kr',
  HOUR: 7,
  WEEKDAY_ONLY: true
};

/* ═════════════════════════ 1. 설치 ═════════════════════════ */

/** 처음 한 번만. 폴더를 만들고 평일 07:00 트리거를 건다. */
function setup() {
  var f = folder_();
  installTrigger();
  var msg = '폴더 : ' + f.getUrl() + '\n트리거 : 평일 ' + KM.HOUR + ':00 morningMail';
  Logger.log(msg);
  return msg;
}

/** 같은 이름 트리거를 전부 지우고 하나만 다시 만든다 (중복 발송 사고 방지). */
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'morningMail') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('morningMail').timeBased()
    .everyDays(1).atHour(KM.HOUR).nearMinute(0).inTimezone(KM.TZ).create();
}

function folder_() {
  return DriveApp.getFolderById(KM.FOLDER_ID);
}

/* ═════════════════════════ 2. 자료 읽기 ═════════════════════════ */

/** 폴더에서 가장 최근 아침대장 CSV 를 읽어 {rows, 설정, 파일명, 만든날} 로 준다. */
function loadLedger_() {
  var best = null, files = folder_().getFiles();
  while (files.hasNext()) {
    var f = files.next();
    if (f.getName().indexOf(KM.FILE_PREFIX) !== 0) continue;
    if (!best || f.getName() > best.getName()) best = f;
  }
  if (!best) return null;
  var text = best.getBlob().getDataAsString('UTF-8').replace(/^﻿/, '');
  var grid = Utilities.parseCsv(text);
  if (!grid.length) return null;
  var head = grid[0], rows = [], conf = {};
  for (var i = 1; i < grid.length; i++) {
    var d = {};
    for (var c = 0; c < head.length; c++) d[head[c]] = (grid[i][c] || '').trim();
    if (d['구분'] === '설정') { conf[d['코드']] = d['현장']; continue; }
    if (!d['할일']) continue;
    rows.push(d);
  }
  return { rows: rows, conf: conf, name: best.getName(), made: conf['만든날'] || '' };
}

/** 자료가 며칠 묵었나 */
function ageDays_(made) {
  if (!made) return 99;
  var m = new Date(made + 'T00:00:00+09:00');
  var t = new Date(Utilities.formatDate(new Date(), KM.TZ, 'yyyy-MM-dd') + 'T00:00:00+09:00');
  return Math.round((t - m) / 86400000);
}

/* ═════════════════════════ 3. 발송 ═════════════════════════ */

/** 평일 07:00 트리거가 부르는 본체. */
function morningMail() {
  var now = new Date();
  var dow = Number(Utilities.formatDate(now, KM.TZ, 'u')); // 1=월 … 7=일
  if (KM.WEEKDAY_ONLY && dow >= 6) return '주말이라 건너뜀';

  var L = loadLedger_();
  var to = (L && L.conf['받는사람']) || KM.TO_FALLBACK;
  var today = Utilities.formatDate(now, KM.TZ, 'yyyy-MM-dd');
  var dowKo = '월화수목금토일'.charAt(dow - 1);
  var stamp = today + ' (' + dowKo + ')';

  if (!L) {
    GmailApp.sendEmail(to, '[KM] ⚠ 아침 대장이 없습니다 ' + stamp,
      '드라이브 「' + KM.FOLDER_NAME + '」 폴더에 아침대장 CSV 가 하나도 없습니다.\n' +
      '클로드에게 「아침대장 올려줘」 라고 한 번만 말씀해 주십시오.');
    return '대장 없음';
  }

  var age = ageDays_(L.made);
  // 경과일은 대장을 만든 날 기준으로 적혀 있다. 대장이 묵었으면 그만큼 더해 오늘 기준으로 맞춘다
  L.rows.forEach(function (r) { r['경과일'] = String((Number(r['경과일']) || 0) + age); });
  var 제안 = L.rows.filter(function (r) { return r['구분'] === '답해주십시오'; });
  var 확정 = L.rows.filter(function (r) { return r['구분'] === '오늘할것'; });
  확정.sort(function (a, b) { return (Number(b['경과일']) || 0) - (Number(a['경과일']) || 0); });

  var n = 0;
  n += send_(to, '[KM] ① 답해 주십시오 ' + stamp + ' · 제안 ' + 제안.length + '건',
             mail1_(제안, stamp, age, L)) ? 1 : 0;
  n += send_(to, '[KM] ② 오늘 할 것 ' + stamp + ' · ' + 확정.length + '건',
             mail2_(확정, stamp, age, L)) ? 1 : 0;
  n += send_(to, '[KM] ③ 어제 있었던 일 ' + stamp,
             mail3_(제안, 확정, stamp, age, L)) ? 1 : 0;

  log_(today, n, L.name, age);
  return n + '통 보냄 (' + L.name + ', ' + age + '일 전 자료)';
}

function send_(to, subject, html) {
  try {
    GmailApp.sendEmail(to, subject, html.replace(/<[^>]+>/g, ' '), { htmlBody: html, name: 'KM 아침' });
    return true;
  } catch (err) {
    Logger.log('발송 실패 : ' + subject + ' / ' + err);
    return false;
  }
}

/** 발송 기록을 폴더 안 발송로그.csv 에 덧붙인다 (덮어쓰지 않는다). */
function log_(today, n, name, age) {
  var f = folder_(), it = f.getFilesByName('발송로그.csv'), line =
    [today, Utilities.formatDate(new Date(), KM.TZ, 'HH:mm'), n + '통', name, age + '일전'].join(',') + '\n';
  if (it.hasNext()) {
    var file = it.next();
    file.setContent(file.getBlob().getDataAsString('UTF-8') + line);
  } else {
    f.createFile('발송로그.csv', '날짜,시각,보낸수,쓴대장,자료나이\n' + line, MimeType.CSV);
  }
}

/* ═════════════════════════ 4. 글 만들기 ═════════════════════════ */

var CSS = '<style>' +
  'body{font-family:-apple-system,"Malgun Gothic",sans-serif;font-size:15px;line-height:1.6;color:#222;margin:0;padding:14px}' +
  '.h{font-size:17px;font-weight:700;margin:0 0 4px}' +
  '.sub{color:#777;font-size:13px;margin:0 0 14px}' +
  '.warn{background:#fff4e5;border-left:4px solid #e8912d;padding:9px 11px;margin:0 0 14px;font-size:14px}' +
  '.it{border:1px solid #e3e3e3;border-radius:8px;padding:11px 12px;margin:0 0 10px}' +
  '.id{font-weight:700;color:#1a5fb4;font-size:14px}' +
  '.late{color:#c01c28;font-weight:700}' +
  '.t{font-weight:600;margin:3px 0}' +
  '.m{color:#666;font-size:13px;margin:2px 0}' +
  '.btns{margin:8px 0 0}' +
  '.btns a{display:inline-block;border:1px solid #c8c8c8;border-radius:14px;padding:4px 11px;margin:3px 5px 0 0;' +
  'font-size:13px;text-decoration:none;color:#333;background:#fafafa}' +
  '.none{color:#777;padding:16px 0}' +
  '</style>';

/** 회신 단추 5개. 누르면 회신 메일이 문장까지 채워져서 열린다. */
function btns_(code) {
  var list = [['진행중', '진행중'], ['완료', '완료'], ['맞아', '맞아'], ['아니야', '아니야'], ['만들어줘', '만들어줘']];
  var h = '<div class="btns">';
  for (var i = 0; i < list.length; i++) {
    var body = encodeURIComponent(code + ' ' + list[i][1]);
    h += '<a href="mailto:?subject=' + encodeURIComponent('[KM] 회신') + '&body=' + body + '">' + list[i][0] + '</a>';
  }
  return h + '</div>';
}

function head_(title, stamp, age, L) {
  var h = CSS + '<p class="h">' + title + '</p><p class="sub">' + stamp + '</p>';
  if (age >= 1) {
    h += '<div class="warn">자료가 <b>' + age + '일 전(' + L.made + ')</b> 것입니다. ' +
         '그 뒤로 바뀐 것은 이 메일에 없습니다.</div>';
  }
  return h;
}

function item_(r, showLate) {
  var 경과 = Number(r['경과일']) || 0;
  var h = '<div class="it"><span class="id">' + (r['코드'] || '') + '</span>';
  if (showLate && 경과 >= 1) h += ' <span class="late">' + 경과 + '일 지남</span>';
  h += ' <span class="m">' + (r['현장'] || '') + (r['때'] ? ' · ' + r['때'] : '') +
       (r['상태'] ? ' · ' + r['상태'] : '') + '</span>';
  h += '<div class="t">' + (r['할일'] || '') + '</div>';
  if (r['누가']) h += '<div class="m">상대 : ' + r['누가'] + '</div>';
  if (r['왜']) h += '<div class="m">왜 : ' + r['왜'] + '</div>';
  if (r['만들기']) h += '<div class="m">말씀만 하시면 만듭니다 : ' + r['만들기'] + '</div>';
  return h + btns_(r['코드'] || '') + '</div>';
}

function mail1_(제안, stamp, age, L) {
  var h = head_('① 답해 주십시오', stamp, age, L);
  if (!제안.length) return h + '<p class="none">결정을 기다리는 제안이 없습니다.</p>';
  h += '<p class="m">아래는 제가 판단한 것일 뿐 아직 확정이 아닙니다. ' +
       '「맞아」를 받기 전에는 서류를 만들지 않습니다.</p>';
  제안.forEach(function (r) { h += item_(r, true); });
  return h + reply_();
}

function mail2_(확정, stamp, age, L) {
  var late = 확정.filter(function (r) { return (Number(r['경과일']) || 0) >= 1; }).length;
  var h = head_('② 오늘 할 것', stamp, age, L);
  if (!확정.length) return h + '<p class="none">확정된 할 일이 없습니다.</p>';
  if (late) h += '<p class="m">날짜가 지난 것 <b>' + late + '건</b>이 맨 위에 있습니다.</p>';
  확정.forEach(function (r) { h += item_(r, true); });
  return h + reply_();
}

function mail3_(제안, 확정, stamp, age, L) {
  var h = head_('③ 어제 있었던 일', stamp, age, L);
  var 현장 = {}, all = 제안.concat(확정);
  all.forEach(function (r) { 현장[r['현장']] = (현장[r['현장']] || 0) + 1; });
  h += '<div class="it"><div class="t">지금 대장에 남아 있는 것</div>' +
       '<div class="m">확정 ' + 확정.length + '건 · 제안 ' + 제안.length + '건</div>';
  Object.keys(현장).forEach(function (k) { h += '<div class="m">· ' + k + ' ' + 현장[k] + '건</div>'; });
  h += '</div>';

  var 오래 = all.filter(function (r) { return (Number(r['경과일']) || 0) >= 3; });
  if (오래.length) {
    h += '<div class="it"><div class="t">사흘 넘게 그대로인 것 ' + 오래.length + '건</div>';
    오래.forEach(function (r) {
      h += '<div class="m">· <b>' + r['코드'] + '</b> ' + r['할일'] + ' (' + r['경과일'] + '일)</div>';
    });
    h += '</div>';
  }
  h += '<div class="it"><div class="t">이 메일은 누가 보냈나</div>' +
       '<div class="m">구글 서버의 앱스 스크립트가 평일 07:00 에 혼자 보냅니다. ' +
       '차장님 PC 도, 클로드도 켜져 있지 않아도 됩니다.</div>' +
       '<div class="m">쓴 자료 : ' + L.name + ' (' + age + '일 전)</div></div>';
  return h + reply_();
}

function reply_() {
  return '<div class="it"><div class="t">회신하는 법</div>' +
    '<div class="m">이 메일에 <b>그냥 답장</b>하시고 한 줄만 쓰시면 됩니다. ' +
    '예 : <code>KM-004 완료</code> · <code>KM-006 만들어줘</code> · <code>KM-008 아니야 299개 아니고 280개</code></div>' +
    '<div class="m">쓸 수 있는 말 : 진행중 · 완료 · 맞아 · 아니야 · 만들어줘 · 취소 · 미뤄 · 물어봄</div>' +
    '<div class="m">여러 줄을 한 번에 쓰셔도 됩니다. 다음 아침에 대장에 반영된 결과가 옵니다.</div></div>';
}

/* ═════════════════════════ 5. 손으로 확인 ═════════════════════════ */

/** 지금 당장 한 번 보내 본다 (요일·시각 무시). */
function testSendNow() {
  var keep = KM.WEEKDAY_ONLY; KM.WEEKDAY_ONLY = false;
  var r = morningMail(); KM.WEEKDAY_ONLY = keep;
  Logger.log(r); return r;
}

/** 보내지 않고 자료만 확인한다. */
function dryRun() {
  var L = loadLedger_();
  if (!L) return '대장 파일이 없습니다';
  var s = L.name + ' / 만든날 ' + L.made + ' (' + ageDays_(L.made) + '일 전) / 줄 ' + L.rows.length;
  Logger.log(s); return s;
}

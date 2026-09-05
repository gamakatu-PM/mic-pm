/**
 * KM 카카오 알림 v1 (2026-09-05)
 * 한국마이크로닉(주) 배성윤 차장 전용 — 구글시트·캘린더·드라이브의 알림거리를
 * 카카오톡 「나에게 보내기」로 전송하는 독립 Apps Script.
 *
 * 설치 순서는 README.md 참조. 이 파일은 script.google.com 새 프로젝트에 그대로 붙여넣는다.
 *
 * 돌아가는 것
 *   morningBrief  평일 07:30  ① 오늘 할 일(무조건할일) ② D-day 경고 ③ 오늘 일정
 *   eveningBrief  평일 18:00  ① 내일 D-day ② 미완료 무조건할일 ③ 내일 일정
 *   hourlyCheck   매시간      ④ 신규 현장 ★ ⑤ 시스템 이상 (같은 건은 하루 1번만)
 *
 * 카카오 텍스트 메시지는 한 건 200자 제한 → 자동으로 나눠 보낸다 (1/3, 2/3 …).
 */

// ───────────────────────── 고정 상수 (시트 규격 정본: km-11 / km-18 / km-site-radar) ─────────────────────────
var KM = {
  VERSION: 'v1 2026-09-05',
  TZ: 'Asia/Seoul',
  MEETING_SHEET_ID: '1RzDj_mm3fY6l42hF9AJ-r5KY50OCVIV7IwSIQeh3rms',   // 26년 회의록
  TAB_TODO: '할 일 모음',            // A기한 B종류 C현장 D할일 E상대 F상태 G(D-) H현장시트 I통화원본 J캘린더ID
  GID_TODO: 408777773,
  TAB_MUSTDO: '0.무조건할일',        // A완료 B★ C날짜 D현장 E담당 F내용 G구분 H링크 I출처 J알림횟수 K마지막알림일 L완료일
  GID_MUSTDO: 1213919957,
  TAB_SELFCHECK: '0.브리지 자가진단',
  GID_SELFCHECK: 1148120135,
  RADAR_SHEET_ID: '1LWK3fmXgf2_aG12B3cunutLUHnSqNMDf_sr3lXOyr-c',     // 신규 현장 레이더
  TAB_SURVEY: '조사노트',            // 판정,출처,분류,허가일,허가구분,시군구,대지위치,건물명,주용도,연면적㎡,연면적평,객실추정,조사 내용,다음 행동
  TAB_RADAR_LOG: '로그',
  DRIVE_FOLDER_ID: '16TXRgGJ7XxFhCq71EVY9l1DYIA9Ewj_U',               // KM_블록작업 (브리지 큐·오류_ 파일)
  KAKAO_TEXT_MAX: 200,               // 카카오 텍스트 템플릿 한도 (공식 문서)
  CHUNK_MAX: 190,                    // 여유분
  CONFIG_TITLE: 'KM 카카오 알림 설정'
};

// 설정 탭 기본값 — 차장님이 시트에서 바꾸면 그 값이 우선한다
var DEFAULT_SETTINGS = [
  ['아침 브리핑 시각', '07:30', '평일 아침. 바꾸면 installTriggers 다시 실행'],
  ['저녁 브리핑 시각', '18:00', '평일 저녁. 바꾸면 installTriggers 다시 실행'],
  ['주말 발송', 'N', 'Y면 토·일에도 브리핑. 시스템 경고는 항상 발송'],
  ['D-day 경고 일수', '3', '기한이 이 일수 안이면 경고 (D-3 이내)'],
  ['할 일 최대 줄수', '10', '한 종류 메시지에 담는 최대 줄. 넘치면 "외 N건"'],
  ['캘린더 ID', '', '비우면 기본 캘린더'],
  ['신규 현장 알림', 'Y', '조사노트 탭의 ★최우선 신규 행'],
  ['시스템 경고', 'Y', '오류_ 파일 · 자가진단 ★ · 레이더 미수집'],
  ['무조건할일 J·K 기록', 'Y', '알림 보낼 때 J알림횟수·K마지막알림일 갱신 (Claude 전용 열)'],
  ['실패 시 이메일 대체', 'Y', '카카오 전송 실패 시 같은 내용을 내 Gmail로'],
  ['레이더 미수집 기준(시간)', '36', '로그 탭 마지막 기록이 이 시간보다 오래되면 경고']
];

var SOURCE_HEADERS = ['출처 이름', '시트 ID', '탭 이름', '헤더 행', '날짜 열', '제목 열', '현장 열', '상태 열', '완료로 볼 값(쉼표)', '사용(Y/N)'];
var SOURCE_EXAMPLES = [
  ['현장 역산표', '', '', '1', 'B', 'A', '', 'F', '완료', 'N'],
  ['정본 대시보드 이슈', '', '', '1', 'C', 'B', 'A', 'D', '완료,종결', 'N']
];

// ═══════════════════════════════ 1. 설치 ═══════════════════════════════

/** 최초 1회. 설정 시트 만들고 트리거 설치. */
function setup() {
  var ss = getConfigSheet_();
  installTriggers();
  log_('setup', true, 0, '설정 시트: ' + ss.getUrl());
  Logger.log('설정 시트: ' + ss.getUrl());
  Logger.log('다음: ① 설정 탭에 KAKAO_REST_KEY 입력 ② 웹앱 배포 후 /exec 열어 카카오 인증');
  return ss.getUrl();
}

/** 트리거를 같은 이름끼리 전부 지우고 1개씩만 다시 만든다 (중복 트리거 사고 방지). */
function installTriggers() {
  var mine = { morningBrief: 1, eveningBrief: 1, hourlyCheck: 1 };
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (mine[t.getHandlerFunction()]) ScriptApp.deleteTrigger(t);
  });
  var m = parseHHMM_(getSetting_('아침 브리핑 시각', '07:30'));
  var e = parseHHMM_(getSetting_('저녁 브리핑 시각', '18:00'));
  ScriptApp.newTrigger('morningBrief').timeBased().everyDays(1).atHour(m.h).nearMinute(m.m).inTimezone(KM.TZ).create();
  ScriptApp.newTrigger('eveningBrief').timeBased().everyDays(1).atHour(e.h).nearMinute(e.m).inTimezone(KM.TZ).create();
  ScriptApp.newTrigger('hourlyCheck').timeBased().everyHours(1).create();
  log_('installTriggers', true, 0, '아침 ' + pad2_(m.h) + ':' + pad2_(m.m) + ' / 저녁 ' + pad2_(e.h) + ':' + pad2_(e.m) + ' / 매시간');
}

/** 설정 스프레드시트(없으면 생성). ID는 Script Properties에 보관. */
function getConfigSheet_() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('CONFIG_SHEET_ID');
  var ss = null;
  if (id) { try { ss = SpreadsheetApp.openById(id); } catch (err) { ss = null; } }
  if (!ss) {
    ss = SpreadsheetApp.create(KM.CONFIG_TITLE);
    props.setProperty('CONFIG_SHEET_ID', ss.getId());
    try { DriveApp.getFileById(ss.getId()).moveTo(DriveApp.getFolderById(KM.DRIVE_FOLDER_ID)); } catch (err) { /* 폴더 없어도 진행 */ }
  }
  var st = ss.getSheetByName('설정');
  if (!st) {
    st = ss.getSheets()[0]; st.setName('설정');
    st.getRange(1, 1, 1, 3).setValues([['항목', '값', '설명']]).setFontWeight('bold');
    st.getRange(2, 1, DEFAULT_SETTINGS.length, 3).setValues(DEFAULT_SETTINGS);
    var r = DEFAULT_SETTINGS.length + 3;
    st.getRange(r, 1, 3, 3).setValues([
      ['KAKAO_REST_KEY', '', '카카오 개발자 콘솔 → 앱 → 앱 키 → REST API 키'],
      ['KAKAO_CLIENT_SECRET', '', '보안 → Client Secret 을 「사용함」으로 켠 경우만'],
      ['WEBAPP_URL', '', '배포 → 웹 앱 URL(/exec). 카카오 Redirect URI에 똑같이 등록']
    ]);
    st.getRange(2, 2, r + 2, 1).setBackground('#FFF2CC');
    st.setColumnWidth(1, 200); st.setColumnWidth(2, 380); st.setColumnWidth(3, 420);
    st.setFrozenRows(1);
  }
  if (!ss.getSheetByName('추가출처')) {
    var so = ss.insertSheet('추가출처');
    so.getRange(1, 1, 1, SOURCE_HEADERS.length).setValues([SOURCE_HEADERS]).setFontWeight('bold');
    so.getRange(2, 1, SOURCE_EXAMPLES.length, SOURCE_HEADERS.length).setValues(SOURCE_EXAMPLES);
    so.getRange(2, 2, SOURCE_EXAMPLES.length, 2).setBackground('#FFF2CC');
    so.setFrozenRows(1);
  }
  if (!ss.getSheetByName('발송로그')) {
    var lg = ss.insertSheet('발송로그');
    lg.getRange(1, 1, 1, 5).setValues([['시각', '종류', '성공', '글자수', '내용/오류']]).setFontWeight('bold');
    lg.setFrozenRows(1);
  }
  return ss;
}

function getSetting_(key, dflt) {
  try {
    var st = getConfigSheet_().getSheetByName('설정');
    var vals = st.getRange(1, 1, st.getLastRow(), 2).getValues();
    for (var i = 0; i < vals.length; i++) {
      if (String(vals[i][0]).trim() === key) {
        var v = vals[i][1];
        if (v === '' || v === null || v === undefined) return dflt;
        return String(v).trim();
      }
    }
  } catch (err) { /* 설정 시트 못 열면 기본값 */ }
  return dflt;
}
function isYes_(v) { return /^(y|yes|예|on|true|1)$/i.test(String(v || '').trim()); }

// ═══════════════════════════════ 2. 카카오 인증 (웹앱) ═══════════════════════════════

/** 웹앱 /exec — 카카오 인증 시작·완료 페이지 */
function doGet(e) {
  var p = (e && e.parameter) || {};
  var restKey = getSetting_('KAKAO_REST_KEY', '');
  var redirect = getSetting_('WEBAPP_URL', '') || (ScriptApp.getService && ScriptApp.getService().getUrl && ScriptApp.getService().getUrl()) || '';
  if (!restKey) return html_('<h3>설정 탭에 KAKAO_REST_KEY 를 먼저 넣어 주세요.</h3>');
  if (!redirect) return html_('<h3>설정 탭 WEBAPP_URL 에 이 페이지 주소(/exec)를 넣어 주세요.</h3>');

  if (p.error) return html_('<h3>카카오 인증 실패</h3><p>' + esc_(p.error) + ' — ' + esc_(p.error_description || '') + '</p>');

  if (p.code) {
    try {
      var tok = exchangeCode_(restKey, redirect, p.code);
      saveTokens_(tok);
      var n = sendKakao_('✅ KM 카카오 알림 연결 완료 (' + KM.VERSION + ')\n아침 ' + getSetting_('아침 브리핑 시각', '07:30') + ' · 저녁 ' + getSetting_('저녁 브리핑 시각', '18:00') + ' · 이상 시 즉시', null, null, 'auth');
      return html_('<h3>연결 완료 ✅</h3><p>카카오톡 「나와의 채팅」에 확인 메시지 ' + n + '건이 갔습니다. 이 창은 닫으셔도 됩니다.</p>');
    } catch (err) {
      log_('auth', false, 0, String(err));
      return html_('<h3>토큰 발급 실패</h3><pre>' + esc_(String(err)) + '</pre><p>Redirect URI가 카카오 콘솔에 똑같이 등록됐는지 확인해 주세요.</p>');
    }
  }
  var url = 'https://kauth.kakao.com/oauth/authorize?response_type=code'
    + '&client_id=' + encodeURIComponent(restKey)
    + '&redirect_uri=' + encodeURIComponent(redirect)
    + '&scope=talk_message';
  return html_('<h2>KM 카카오 알림</h2><p>아래를 누르면 카카오 로그인 → 「카카오톡 메시지 전송」 동의 → 자동으로 돌아옵니다.</p>'
    + '<p><a href="' + url + '" target="_top" style="display:inline-block;padding:14px 22px;background:#FEE500;color:#191919;border-radius:8px;font-size:18px;text-decoration:none;font-weight:bold">카카오 인증 시작</a></p>'
    + '<p style="color:#888;font-size:12px">Redirect URI: ' + esc_(redirect) + '</p>');
}

function html_(body) {
  return HtmlService.createHtmlOutput('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><body style="font-family:sans-serif;padding:24px;max-width:520px">' + body + '</body>')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
function esc_(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

function exchangeCode_(restKey, redirect, code) {
  var payload = { grant_type: 'authorization_code', client_id: restKey, redirect_uri: redirect, code: code };
  var sec = getSetting_('KAKAO_CLIENT_SECRET', '');
  if (sec) payload.client_secret = sec;
  return tokenRequest_(payload);
}

function tokenRequest_(payload) {
  var res = UrlFetchApp.fetch('https://kauth.kakao.com/oauth/token', {
    method: 'post', payload: payload, muteHttpExceptions: true,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' }
  });
  var code = res.getResponseCode(), body = res.getContentText();
  var j = {};
  try { j = JSON.parse(body); } catch (err) { /* 비JSON */ }
  if (code !== 200 || !j.access_token) throw new Error('kauth ' + code + ': ' + body);
  return j;
}

function saveTokens_(tok) {
  var props = PropertiesService.getScriptProperties();
  var now = Date.now();
  var o = { KAKAO_ACCESS_TOKEN: tok.access_token, KAKAO_ACCESS_EXP: String(now + (tok.expires_in || 21600) * 1000) };
  if (tok.refresh_token) {                       // 갱신 응답에는 없을 수 있음(남은 기간 1개월 이상) → 기존 것 유지
    o.KAKAO_REFRESH_TOKEN = tok.refresh_token;
    o.KAKAO_REFRESH_EXP = String(now + (tok.refresh_token_expires_in || 5184000) * 1000);
  }
  props.setProperties(o);
}

/** 유효한 액세스 토큰. 만료 10분 전이면 리프레시. 없으면 예외. */
function getAccessToken_() {
  var props = PropertiesService.getScriptProperties();
  var at = props.getProperty('KAKAO_ACCESS_TOKEN'), exp = Number(props.getProperty('KAKAO_ACCESS_EXP') || 0);
  if (at && Date.now() < exp - 10 * 60 * 1000) return at;
  var rt = props.getProperty('KAKAO_REFRESH_TOKEN');
  if (!rt) throw new Error('카카오 인증 안 됨 — 웹앱 URL(/exec)을 열어 인증하세요');
  var payload = { grant_type: 'refresh_token', client_id: getSetting_('KAKAO_REST_KEY', ''), refresh_token: rt };
  var sec = getSetting_('KAKAO_CLIENT_SECRET', '');
  if (sec) payload.client_secret = sec;
  var tok = tokenRequest_(payload);
  saveTokens_(tok);
  return tok.access_token;
}

// ═══════════════════════════════ 3. 카카오 전송 ═══════════════════════════════

/**
 * 텍스트를 200자 단위로 나눠 「나에게 보내기」. 성공 건수 반환.
 * kind 는 로그·중복방지용 이름.
 */
function sendKakao_(text, linkUrl, buttonTitle, kind) {
  var chunks = chunkText_(text, KM.CHUNK_MAX);
  var sent = 0, lastErr = null;
  for (var i = 0; i < chunks.length; i++) {
    var body = chunks.length > 1 ? '(' + (i + 1) + '/' + chunks.length + ') ' + chunks[i] : chunks[i];
    try {
      sendKakaoOne_(body, linkUrl, buttonTitle);
      sent++;
      log_(kind || 'send', true, body.length, body.slice(0, 120));
    } catch (err) {
      lastErr = err;
      log_(kind || 'send', false, body.length, String(err));
    }
  }
  if (sent === 0 && lastErr) {
    if (isYes_(getSetting_('실패 시 이메일 대체', 'Y'))) mailFallback_(kind, text, lastErr);
    throw lastErr;
  }
  return sent;
}

function sendKakaoOne_(text, linkUrl, buttonTitle) {
  if (text.length > KM.KAKAO_TEXT_MAX) throw new Error('200자 초과 ' + text.length);
  var url = linkUrl || 'https://docs.google.com/spreadsheets/d/' + KM.MEETING_SHEET_ID + '/edit#gid=' + KM.GID_MUSTDO;
  var tpl = { object_type: 'text', text: text, link: { web_url: url, mobile_web_url: url }, button_title: buttonTitle || '시트 열기' };
  var res = UrlFetchApp.fetch('https://kapi.kakao.com/v2/api/talk/memo/default/send', {
    method: 'post', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + getAccessToken_(), 'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8' },
    payload: { template_object: JSON.stringify(tpl) }
  });
  var code = res.getResponseCode();
  if (code !== 200) throw new Error('kapi ' + code + ': ' + res.getContentText());
  return true;
}

/** 줄 단위로 자르되, 한 줄이 한도를 넘으면 글자 단위로 자른다. */
function chunkText_(text, max) {
  var lines = String(text || '').split('\n'), out = [], cur = '';
  var push = function () { if (cur.trim()) out.push(cur.trim()); cur = ''; };
  for (var i = 0; i < lines.length; i++) {
    var ln = lines[i];
    while (ln.length > max) { push(); out.push(ln.slice(0, max)); ln = ln.slice(max); }
    var cand = cur ? cur + '\n' + ln : ln;
    if (cand.length > max) { push(); cur = ln; } else cur = cand;
  }
  push();
  return out.length ? out : [''];
}

function mailFallback_(kind, text, err) {
  try {
    var to = Session.getEffectiveUser().getEmail();
    MailApp.sendEmail(to, '[KM 알림 대체] ' + (kind || '') + ' — 카카오 전송 실패', text + '\n\n오류: ' + String(err));
    log_('mail-fallback', true, text.length, to);
  } catch (e2) { log_('mail-fallback', false, 0, String(e2)); }
}

// ═══════════════════════════════ 4. 데이터 읽기 ═══════════════════════════════

/** 「할 일 모음」 미완료 행 → {due, kind, site, task, who, status, row} */
function readTodo_() {
  var sh = SpreadsheetApp.openById(KM.MEETING_SHEET_ID).getSheetByName(KM.TAB_TODO);
  if (!sh) return [];
  var vals = sh.getDataRange().getValues();
  var hdr = findHeaderRow_(vals, ['기한', '할일', '할 일']);
  var items = [];
  for (var r = hdr + 1; r < vals.length; r++) {
    var row = vals[r];
    var task = String(row[3] || '').trim();
    if (!task) continue;
    var status = String(row[5] || '').trim();
    if (isDone_(status)) continue;
    items.push({ due: parseDate_(row[0]), kind: String(row[1] || '').trim(), site: String(row[2] || '').trim(), task: task, who: String(row[4] || '').trim(), status: status, row: r + 1, src: '할 일 모음' });
  }
  return items;
}

/** 「0.무조건할일」 미완료 행 → {star, date, site, who, content, kind, row} */
function readMustDo_() {
  var sh = SpreadsheetApp.openById(KM.MEETING_SHEET_ID).getSheetByName(KM.TAB_MUSTDO);
  if (!sh) return [];
  var vals = sh.getDataRange().getValues();
  var items = [];
  for (var r = 1; r < vals.length; r++) {              // 1행 머리글, 2행부터 데이터(km-18)
    var row = vals[r];
    var content = String(row[5] || '').trim();
    if (!content) continue;
    if (row[0] === true || /^(true|완료|✔|✓)$/i.test(String(row[0]).trim())) continue;
    items.push({ star: row[1] === true, date: parseDate_(row[2]), site: String(row[3] || '').trim(), who: String(row[4] || '').trim(), content: content, kind: String(row[6] || '').trim(), row: r + 1, src: '무조건할일' });
  }
  items.sort(function (a, b) { return (b.star ? 1 : 0) - (a.star ? 1 : 0); });
  return items;
}

/** 무조건할일 J알림횟수·K마지막알림일 갱신 (Claude 전용 열, km-18 §4-1) */
function markMustDoNotified_(items) {
  if (!isYes_(getSetting_('무조건할일 J·K 기록', 'Y')) || !items.length) return;
  try {
    var sh = SpreadsheetApp.openById(KM.MEETING_SHEET_ID).getSheetByName(KM.TAB_MUSTDO);
    var today = ymd6_(nowKST_());
    items.forEach(function (it) {
      var rg = sh.getRange(it.row, 10, 1, 2);
      var cur = rg.getValues()[0];
      var n = Number(cur[0] || 0) + 1;
      rg.setValues([[n, today]]);
    });
  } catch (err) { log_('mustdo-mark', false, 0, String(err)); }
}

/** 「추가출처」 탭에 등록된 시트들 (역산표·대시보드 등) → 할 일 모음과 같은 모양 */
function readExtraSources_() {
  var out = [];
  var so;
  try { so = getConfigSheet_().getSheetByName('추가출처'); } catch (err) { return out; }
  if (!so) return out;
  var rows = so.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    var c = rows[i];
    var name = String(c[0] || '').trim(), id = String(c[1] || '').trim(), tab = String(c[2] || '').trim();
    if (!name || !id || !tab || !isYes_(c[9])) continue;
    try {
      var sh = SpreadsheetApp.openById(id).getSheetByName(tab);
      if (!sh) { log_('extra:' + name, false, 0, '탭 없음 ' + tab); continue; }
      var vals = sh.getDataRange().getValues();
      var hdr = Math.max(1, Number(c[3] || 1));
      var dc = colIdx_(c[4]), tc = colIdx_(c[5]), sc = colIdx_(c[6]), stc = colIdx_(c[7]);
      var doneVals = String(c[8] || '완료').split(',').map(function (s) { return s.trim(); }).filter(String);
      for (var r = hdr; r < vals.length; r++) {
        var row = vals[r];
        if (dc < 0 || tc < 0) break;
        var title = String(row[tc] || '').trim();
        if (!title) continue;
        var status = stc >= 0 ? String(row[stc] || '').trim() : '';
        if (status && doneVals.indexOf(status) >= 0) continue;
        if (row[stc] === true) continue;
        out.push({ due: parseDate_(row[dc]), kind: name, site: sc >= 0 ? String(row[sc] || '').trim() : '', task: title, who: '', status: status, row: r + 1, src: name, sheetId: id, tabName: tab });
      }
    } catch (err) { log_('extra:' + name, false, 0, String(err)); }
  }
  return out;
}

/** 캘린더 하루치 → ['09:00 조선호텔 현장회의', …] */
function readCalendar_(day) {
  try {
    var id = getSetting_('캘린더 ID', '');
    var cal = id ? CalendarApp.getCalendarById(id) : CalendarApp.getDefaultCalendar();
    if (!cal) return [];
    return cal.getEventsForDay(day).map(function (ev) {
      var t = ev.getTitle();
      if (/^\[완료\]/.test(t)) return null;
      var when = ev.isAllDayEvent() ? '종일' : Utilities.formatDate(ev.getStartTime(), KM.TZ, 'HH:mm');
      return when + ' ' + t;
    }).filter(Boolean);
  } catch (err) { log_('calendar', false, 0, String(err)); return []; }
}

/** 조사노트 ★최우선 행 중 아직 알리지 않은 것 */
function readNewRadarStars_() {
  var sh = SpreadsheetApp.openById(KM.RADAR_SHEET_ID).getSheetByName(KM.TAB_SURVEY);
  if (!sh) return [];
  var vals = sh.getDataRange().getValues();
  if (vals.length < 2) return [];
  var h = vals[0].map(function (x) { return String(x).trim(); });
  var ix = function (n) { return h.indexOf(n); };
  var cJ = ix('판정'), cSi = ix('시군구'), cAd = ix('대지위치'), cNm = ix('건물명'), cAr = ix('연면적㎡'), cRm = ix('객실추정'), cNx = ix('다음 행동'), cUs = ix('주용도');
  if (cJ < 0) { log_('radar', false, 0, '조사노트에 판정 열 없음'); return []; }
  var seen = getSeen_('radar');
  var out = [];
  for (var r = 1; r < vals.length; r++) {
    var row = vals[r];
    if (String(row[cJ]).indexOf('★') !== 0) continue;
    var key = String(row[cAd] || '') + '|' + String(row[cNm] || '');
    if (!key.replace('|', '').trim() || seen[key]) continue;
    out.push({ key: key, region: String(row[cSi] || ''), addr: String(row[cAd] || ''), name: String(row[cNm] || ''), use: String(row[cUs] || ''), area: row[cAr], rooms: String(row[cRm] || ''), next: String(row[cNx] || '') });
  }
  return out;
}

/** 시스템 이상 목록 → [{key, msg}] */
function systemChecks_() {
  var out = [], today = ymd6_(nowKST_());
  // ① 브리지 오류_ 파일 (24시간 내)
  try {
    var f = DriveApp.getFolderById(KM.DRIVE_FOLDER_ID).getFiles(), n = 0, names = [];
    var cut = Date.now() - 24 * 3600 * 1000;
    while (f.hasNext()) {
      var fl = f.next();
      if (fl.getName().indexOf('오류_') === 0 && fl.getLastUpdated().getTime() > cut) { n++; if (names.length < 3) names.push(fl.getName()); }
    }
    if (n) out.push({ key: 'err-file|' + today, msg: '브리지 오류_ 파일 ' + n + '개 (24h)\n' + names.join('\n') });
  } catch (err) { log_('sys-drive', false, 0, String(err)); }
  // ② 브리지 자가진단 ★ (최근 30행, 2일 이내 날짜)
  try {
    var sc = SpreadsheetApp.openById(KM.MEETING_SHEET_ID).getSheetByName(KM.TAB_SELFCHECK);
    if (sc) {
      var last = sc.getLastRow(), from = Math.max(1, last - 29);
      var rows = last >= 1 ? sc.getRange(from, 1, last - from + 1, Math.max(1, sc.getLastColumn())).getValues() : [];
      var hits = [];
      rows.forEach(function (row) {
        var line = row.map(String).join(' ');
        if (line.indexOf('★') < 0) return;
        var d = parseDate_(row[0]);
        if (d && daysBetween_(nowKST_(), d) < -2) return;   // 2일 넘게 지난 경고는 제외
        hits.push(line.slice(0, 80));
      });
      if (hits.length) out.push({ key: 'selfcheck|' + today + '|' + hits[0].slice(0, 30), msg: '자가진단 ★경고 ' + hits.length + '건\n' + hits.slice(0, 3).join('\n') });
    }
  } catch (err) { log_('sys-selfcheck', false, 0, String(err)); }
  // ③ 레이더 미수집
  try {
    var lg = SpreadsheetApp.openById(KM.RADAR_SHEET_ID).getSheetByName(KM.TAB_RADAR_LOG);
    if (lg && lg.getLastRow() >= 2) {
      var lastRow = lg.getRange(lg.getLastRow(), 1, 1, Math.max(1, lg.getLastColumn())).getValues()[0];
      var lastAt = lastRow[0] instanceof Date ? lastRow[0] : parseDate_(lastRow[0]);
      var hrs = Number(getSetting_('레이더 미수집 기준(시간)', '36'));
      if (lastAt && (Date.now() - lastAt.getTime()) > hrs * 3600 * 1000) {
        out.push({ key: 'radar-stale|' + today, msg: '레이더 마지막 수집 ' + Utilities.formatDate(lastAt, KM.TZ, 'M/d HH:mm') + ' — ' + hrs + '시간 넘게 기록 없음' });
      }
      var txt = lastRow.map(String).join(' ');
      if (/실패|오류|error/i.test(txt) && !/실패\s*0/.test(txt)) out.push({ key: 'radar-fail|' + today, msg: '레이더 로그 마지막 줄에 실패 표시\n' + txt.slice(0, 120) });
    }
  } catch (err) { log_('sys-radar', false, 0, String(err)); }
  return out;
}

// ═══════════════════════════════ 5. 브리핑 조립 ═══════════════════════════════

/** 아침 07:30 */
function morningBrief() {
  return runBrief_('morning');
}
/** 저녁 18:00 */
function eveningBrief() {
  return runBrief_('evening');
}

function runBrief_(mode) {
  var now = nowKST_();
  if (!isYes_(getSetting_('주말 발송', 'N')) && isWeekend_(now)) { log_(mode, true, 0, '주말 — 건너뜀'); return 0; }
  var msgs = buildBriefMessages_(mode, now);
  var total = 0;
  msgs.forEach(function (m) {
    try { total += sendKakao_(m.text, m.link, m.button, mode + ':' + m.kind); } catch (err) { /* 로그는 sendKakao_ 안에서 */ }
  });
  if (mode === 'morning' || mode === 'evening') {
    try { markMustDoNotified_(readMustDo_()); } catch (err) { log_('mustdo-mark', false, 0, String(err)); }
  }
  return total;
}

/**
 * 순수 조립 함수 (전송 없음). 모의 실행·미리보기용.
 * 반환: [{kind, text, link, button}]
 */
function buildBriefMessages_(mode, now) {
  var maxLines = Number(getSetting_('할 일 최대 줄수', '10')) || 10;
  var warnDays = Number(getSetting_('D-day 경고 일수', '3')) || 3;
  var dayLabel = fmtMD_(now);
  var msgs = [];
  var mustdo = safe_(readMustDo_, []);
  var todos = safe_(readTodo_, []).concat(safe_(readExtraSources_, []));

  if (mode === 'morning') {
    // ① 오늘 할 일 (무조건할일)
    if (mustdo.length) {
      var lines = mustdo.slice(0, maxLines).map(function (it) {
        return (it.star ? '★ ' : '· ') + (it.site ? '[' + it.site + '] ' : '') + it.content.replace(/\s+/g, ' ').slice(0, 40) + (it.date ? ' (' + dday_(now, it.date) + ')' : '');
      });
      if (mustdo.length > maxLines) lines.push('외 ' + (mustdo.length - maxLines) + '건');
      msgs.push({ kind: 'mustdo', text: '📌 ' + dayLabel + ' 무조건할일 ' + mustdo.length + '건\n' + lines.join('\n'), link: sheetLink_(KM.MEETING_SHEET_ID, KM.GID_MUSTDO), button: '무조건할일 열기' });
    }
    // ② D-day 경고
    var dd = ddayGroups_(todos, now, warnDays);
    if (dd.lines.length) {
      msgs.push({ kind: 'dday', text: '⏰ D-day 경고 (지남 ' + dd.over + ' · 오늘 ' + dd.today + ' · ' + warnDays + '일 내 ' + dd.soon + ')\n' + dd.lines.slice(0, maxLines).join('\n') + (dd.lines.length > maxLines ? '\n외 ' + (dd.lines.length - maxLines) + '건' : ''), link: sheetLink_(KM.MEETING_SHEET_ID, KM.GID_TODO), button: '할 일 모음 열기' });
    }
    // ③ 오늘 일정
    var ev = readCalendar_(now);
    if (ev.length) msgs.push({ kind: 'calendar', text: '📅 ' + dayLabel + ' 일정 ' + ev.length + '건\n' + ev.slice(0, maxLines).join('\n'), link: 'https://calendar.google.com/calendar/r/day', button: '캘린더 열기' });
    if (!msgs.length) msgs.push({ kind: 'empty', text: '🟢 ' + dayLabel + ' 무조건할일·D-day·일정 없음', link: sheetLink_(KM.MEETING_SHEET_ID, KM.GID_MUSTDO), button: '시트 열기' });
  } else {
    var tomorrow = addDays_(now, 1);
    // ① 내일 D-day (+ 지남·오늘 미완료)
    var dd2 = ddayGroups_(todos, now, 1);
    if (dd2.lines.length) {
      msgs.push({ kind: 'dday', text: '🌙 내일 마감·미완료 (지남 ' + dd2.over + ' · 오늘 ' + dd2.today + ' · 내일 ' + dd2.soon + ')\n' + dd2.lines.slice(0, maxLines).join('\n') + (dd2.lines.length > maxLines ? '\n외 ' + (dd2.lines.length - maxLines) + '건' : ''), link: sheetLink_(KM.MEETING_SHEET_ID, KM.GID_TODO), button: '할 일 모음 열기' });
    }
    // ② 미완료 무조건할일
    if (mustdo.length) {
      var stars = mustdo.filter(function (i) { return i.star; });
      var l2 = stars.slice(0, maxLines).map(function (it) { return '★ ' + (it.site ? '[' + it.site + '] ' : '') + it.content.replace(/\s+/g, ' ').slice(0, 40); });
      msgs.push({ kind: 'mustdo', text: '📌 미완료 무조건할일 ' + mustdo.length + '건 (★ ' + stars.length + ')' + (l2.length ? '\n' + l2.join('\n') : ''), link: sheetLink_(KM.MEETING_SHEET_ID, KM.GID_MUSTDO), button: '무조건할일 열기' });
    }
    // ③ 내일 일정
    var ev2 = readCalendar_(tomorrow);
    if (ev2.length) msgs.push({ kind: 'calendar', text: '📅 내일 ' + fmtMD_(tomorrow) + ' 일정 ' + ev2.length + '건\n' + ev2.slice(0, maxLines).join('\n'), link: 'https://calendar.google.com/calendar/r/day', button: '캘린더 열기' });
    if (!msgs.length) msgs.push({ kind: 'empty', text: '🟢 내일 ' + fmtMD_(tomorrow) + ' 마감·미완료·일정 없음', link: sheetLink_(KM.MEETING_SHEET_ID, KM.GID_MUSTDO), button: '시트 열기' });
  }
  return msgs;
}

/** D-day 분류. 지남 → 오늘 → 임박 순. 기한 없는 항목은 제외. */
function ddayGroups_(items, now, warnDays) {
  var over = [], today = [], soon = [];
  items.forEach(function (it) {
    if (!it.due) return;
    var d = daysBetween_(now, it.due);
    var line = dday_(now, it.due) + ' ' + (it.site ? '[' + it.site + '] ' : '') + it.task.replace(/\s+/g, ' ').slice(0, 40) + (it.src !== '할 일 모음' ? ' 〈' + it.src + '〉' : '');
    if (d < 0) over.push({ d: d, line: line });
    else if (d === 0) today.push({ d: d, line: line });
    else if (d <= warnDays) soon.push({ d: d, line: line });
  });
  var by = function (a, b) { return a.d - b.d; };
  over.sort(by); today.sort(by); soon.sort(by);
  return { over: over.length, today: today.length, soon: soon.length, lines: over.concat(today, soon).map(function (x) { return x.line; }) };
}

/** 매시간: 신규 현장 ★ + 시스템 이상. 같은 키는 다시 보내지 않는다. */
function hourlyCheck() {
  var sent = 0;
  if (isYes_(getSetting_('신규 현장 알림', 'Y'))) {
    var stars = safe_(readNewRadarStars_, []);
    if (stars.length) {
      var lines = stars.slice(0, 5).map(function (s) {
        return '★ ' + (s.region ? s.region + ' ' : '') + (s.name || s.addr) + (s.use ? ' / ' + s.use : '') + (s.area ? ' / ' + fmtNum_(s.area) + '㎡' : '') + (s.rooms ? ' / ' + s.rooms : '') + (s.next ? '\n  → ' + s.next.slice(0, 50) : '');
      });
      var text = '🏗 신규 현장 ★최우선 ' + stars.length + '건\n' + lines.join('\n') + (stars.length > 5 ? '\n외 ' + (stars.length - 5) + '건' : '');
      try {
        sent += sendKakao_(text, sheetLink_(KM.RADAR_SHEET_ID, null), '레이더 열기', 'radar');
        markSeen_('radar', stars.map(function (s) { return s.key; }));
      } catch (err) { /* 로그됨 */ }
    }
  }
  if (isYes_(getSetting_('시스템 경고', 'Y'))) {
    var seen = getSeen_('sys');
    var warns = safe_(systemChecks_, []).filter(function (w) { return !seen[w.key]; });
    if (warns.length) {
      var t2 = '🚨 시스템 이상 ' + warns.length + '건\n' + warns.map(function (w) { return '· ' + w.msg; }).join('\n');
      try {
        sent += sendKakao_(t2, sheetLink_(KM.MEETING_SHEET_ID, KM.GID_SELFCHECK), '자가진단 열기', 'system');
        markSeen_('sys', warns.map(function (w) { return w.key; }));
      } catch (err) { /* 로그됨 */ }
    }
  }
  return sent;
}

// ═══════════════════════════════ 6. 중복 방지 (Script Properties) ═══════════════════════════════

function getSeen_(bucket) {
  try { return JSON.parse(PropertiesService.getScriptProperties().getProperty('SEEN_' + bucket) || '{}'); } catch (err) { return {}; }
}
function markSeen_(bucket, keys) {
  var seen = getSeen_(bucket), today = ymd6_(nowKST_());
  keys.forEach(function (k) { seen[k] = today; });
  // 90일 넘은 키 정리 (속성 크기 9KB 한도)
  var ks = Object.keys(seen);
  if (ks.length > 400) ks.sort(function (a, b) { return String(seen[a]).localeCompare(String(seen[b])); }).slice(0, ks.length - 400).forEach(function (k) { delete seen[k]; });
  PropertiesService.getScriptProperties().setProperty('SEEN_' + bucket, JSON.stringify(seen));
}

// ═══════════════════════════════ 7. 유틸 ═══════════════════════════════

function nowKST_() {
  // Apps Script Date는 UTC 기반이지만 formatDate로 KST 날짜 성분을 얻어 로컬 자정 기준 Date를 만든다
  var s = Utilities.formatDate(new Date(), KM.TZ, 'yyyy-MM-dd HH:mm');
  var m = s.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/);
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5]));
}
function isWeekend_(d) { var w = d.getDay(); return w === 0 || w === 6; }
function addDays_(d, n) { var x = new Date(d.getFullYear(), d.getMonth(), d.getDate()); x.setDate(x.getDate() + n); return x; }
function startOfDay_(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
function daysBetween_(now, due) { return Math.round((startOfDay_(due) - startOfDay_(now)) / 86400000); }
function dday_(now, due) { var d = daysBetween_(now, due); return d === 0 ? 'D-day' : d > 0 ? 'D-' + d : 'D+' + (-d); }
function pad2_(n) { return (n < 10 ? '0' : '') + n; }
function ymd6_(d) { return String(d.getFullYear()).slice(2) + pad2_(d.getMonth() + 1) + pad2_(d.getDate()); }
function fmtMD_(d) { return (d.getMonth() + 1) + '/' + d.getDate() + '(' + '일월화수목금토'[d.getDay()] + ')'; }
function fmtNum_(v) { var n = Number(v); return isNaN(n) ? String(v) : n.toLocaleString('en-US'); }
function parseHHMM_(s) { var m = String(s || '').match(/(\d{1,2})\s*[:시]\s*(\d{0,2})/); return m ? { h: Math.min(23, Number(m[1])), m: Math.min(59, Number(m[2] || 0)) } : { h: 7, m: 30 }; }
function colIdx_(letter) { var s = String(letter || '').trim().toUpperCase(); if (!s) return -1; if (/^\d+$/.test(s)) return Number(s) - 1; var n = 0; for (var i = 0; i < s.length; i++) { var c = s.charCodeAt(i) - 64; if (c < 1 || c > 26) return -1; n = n * 26 + c; } return n - 1; }
function sheetLink_(id, gid) { return 'https://docs.google.com/spreadsheets/d/' + id + '/edit' + (gid ? '#gid=' + gid : ''); }
function isDone_(status) { return /완료|종결|취소|done|closed/i.test(String(status || '')); }
function safe_(fn, dflt) { try { return fn(); } catch (err) { log_(fn.name || 'fn', false, 0, String(err)); return dflt; } }
function findHeaderRow_(vals, words) {
  for (var r = 0; r < Math.min(5, vals.length); r++) {
    var line = vals[r].map(String).join('|');
    for (var i = 0; i < words.length; i++) if (line.indexOf(words[i]) >= 0) return r;
  }
  return 0;
}

/**
 * 날짜 파서. Date / '260904' / '260904(예정) 문구' / '2026-09-04' / '2026.9.4' / '9/4' / '9월 4일' → Date(로컬 자정). 못 읽으면 null.
 * ★ D·E열 규격(km-11): 앞 6자리 = 완료(예정)일.
 */
function parseDate_(v) {
  if (v === null || v === undefined || v === '') return null;
  if (v instanceof Date) return isNaN(v.getTime()) ? null : startOfDay_(v);
  if (typeof v === 'number') {
    var s6 = String(Math.floor(v));
    if (s6.length === 6) return parse6_(s6);
    if (v > 20000 && v < 80000) { var dd = new Date(Math.round((v - 25569) * 86400000)); return new Date(dd.getUTCFullYear(), dd.getUTCMonth(), dd.getUTCDate()); } // 엑셀 일련번호
    return null;
  }
  var s = String(v).trim(), m, y = nowKST_().getFullYear();
  if ((m = s.match(/^(\d{2})(\d{2})(\d{2})(?!\d)/))) return parse6_(m[1] + m[2] + m[3]);
  if ((m = s.match(/(\d{4})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})/))) return mk_(m[1], m[2], m[3]);
  if ((m = s.match(/^(\d{1,2})[./월]\s*(\d{1,2})일?(?!\d)/))) return mk_(y, m[1], m[2]);
  if ((m = s.match(/^(\d{4})(\d{2})(\d{2})(?!\d)/))) return mk_(m[1], m[2], m[3]);
  return null;
}
function parse6_(s) { return mk_('20' + s.slice(0, 2), s.slice(2, 4), s.slice(4, 6)); }
function mk_(y, mo, d) { var dt = new Date(Number(y), Number(mo) - 1, Number(d)); return (dt.getMonth() === Number(mo) - 1 && dt.getDate() === Number(d)) ? dt : null; }

function log_(kind, ok, chars, msg) {
  try {
    var lg = getConfigSheet_().getSheetByName('발송로그');
    lg.appendRow([Utilities.formatDate(new Date(), KM.TZ, 'yyyy-MM-dd HH:mm:ss'), kind, ok ? 'O' : 'X', chars, String(msg).slice(0, 500)]);
    if (lg.getLastRow() > 3000) lg.deleteRows(2, 500);
  } catch (err) { Logger.log('[log_ 실패] ' + kind + ' ' + msg); }
}

// ═══════════════════════════════ 8. 손으로 눌러보는 것 ═══════════════════════════════

/** 카카오 연결 확인 — 메시지 1건 */
function testSend() { return sendKakao_('🔔 KM 카카오 알림 테스트 ' + Utilities.formatDate(new Date(), KM.TZ, 'M/d HH:mm'), null, null, 'test'); }
/** 전송 없이 아침 브리핑 내용만 로그로 확인 */
function previewMorning() { var m = buildBriefMessages_('morning', nowKST_()); m.forEach(function (x) { Logger.log('[' + x.kind + '] ' + x.text.length + '자\n' + x.text); }); return m; }
/** 전송 없이 저녁 브리핑 내용만 로그로 확인 */
function previewEvening() { var m = buildBriefMessages_('evening', nowKST_()); m.forEach(function (x) { Logger.log('[' + x.kind + '] ' + x.text.length + '자\n' + x.text); }); return m; }
/** 전송 없이 시스템 검사·신규 현장만 로그로 확인 */
function previewHourly() { Logger.log(JSON.stringify({ radar: safe_(readNewRadarStars_, []), system: safe_(systemChecks_, []) }, null, 1)); }
/** 중복 방지 기록 초기화 (다시 전부 알리고 싶을 때) */
function resetSeen() { var p = PropertiesService.getScriptProperties(); p.deleteProperty('SEEN_radar'); p.deleteProperty('SEEN_sys'); log_('resetSeen', true, 0, '초기화'); }
/** 카카오 토큰 삭제 (재인증할 때) */
function resetKakaoAuth() { var p = PropertiesService.getScriptProperties(); ['KAKAO_ACCESS_TOKEN', 'KAKAO_ACCESS_EXP', 'KAKAO_REFRESH_TOKEN', 'KAKAO_REFRESH_EXP'].forEach(function (k) { p.deleteProperty(k); }); log_('resetKakaoAuth', true, 0, '토큰 삭제'); }

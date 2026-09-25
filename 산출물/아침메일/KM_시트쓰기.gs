/**
 * KM_시트쓰기 v1 (2026-09-25)  — 클로드가 부르는 웹 앱. Zapier 없이 0원·무제한.
 *   ping   : 연결 확인
 *   read   : 「26년 회의록2」·「신규 현장 레이더」 읽기 (값 그대로)
 *   batch  : 「26년 회의록2」 에 줄 덧붙이기·병합·체크박스·▼ (t53 --write 가 만든 본문 그대로)
 *   old26  : 옛 「26년 회의록」 현장 탭에 회의 기록 덧붙이기 + 「0.전체 반영모음」 맨 위에 한 줄
 *
 * ★ 지우는 기능은 없다. 허용한 요청 종류만 받는다. 암호(KM_TOKEN)가 맞을 때만 움직인다.
 * ★ 설치 : 확장 프로그램 → Apps Script → 새 파일에 이 전문 붙여넣기 → KM_TOKEN 칸에 클로드가 드린 암호
 *          → 배포 → 새 배포 → 유형 「웹 앱」 → 실행 : 나 / 액세스 : 모든 사용자 → 배포 → 권한 허용 → 주소 복사해 클로드에게
 */

var KM_TOKEN = '';   // ← 클로드가 드린 암호를 따옴표 안에 (저장소에는 비워 둔다 — 공개 저장소)

var KM_IDS = {
  new2:  '1S02QcwHnRNiJJbq3qfSPs9sRtR1UDtTMSUPhLy4_Ckk',   // 26년 회의록2 (읽기·쓰기)
  radar: '1LWK3fmXgf2_aG12B3cunutLUHnSqNMDf_sr3lXOyr-c',   // 신규 현장 레이더 (읽기만)
  old:   '1RzDj_mm3fY6l42hF9AJ-r5KY50OCVIV7IwSIQeh3rms'    // 옛 26년 회의록 (old26 로만 쓴다)
};

// batch 에서 받는 요청 종류 — delete* · clear* · 탭 지우기는 없다
var KM_BATCH_OK = ['updateCells', 'mergeCells', 'repeatCell', 'setDataValidation',
                   'appendDimension', 'updateDimensionProperties'];

// 옛 시트 : 새 현장 탭은 이 탭 바로 앞(현장 구역 끝)에 만든다 — 관리 탭은 늘 맨 뒤 (km-11 §4-8)
var KM_OLD_FIRST_ADMIN = '현장 갑지';
var KM_OLD_HEADER_FROM = '연합기숙사';          // 새 탭의 1·2행 머리 모양을 가져올 탭
var KM_OLD_MASTER = '0.전체 반영모음';


function doPost(e) {
  var body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return km_out_({ok: false, error: '본문이 JSON 이 아님'}); }
  if (!KM_TOKEN || body.token !== KM_TOKEN) return km_out_({ok: false, error: '암호 틀림'});
  try {
    if (body.action === 'ping')  return km_out_({ok: true, version: 'v1 2026-09-25', now: new Date().toISOString()});
    if (body.action === 'read')  return km_out_(km_read_(body));
    if (body.action === 'batch') return km_out_(km_batch_(body));
    if (body.action === 'old26') return km_out_(km_old26_(body));
    return km_out_({ok: false, error: '모르는 action : ' + body.action});
  } catch (err) {
    return km_out_({ok: false, error: String(err && err.stack || err)});
  }
}

function km_out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function km_api_(method, url, payload) {
  var opt = {method: method, muteHttpExceptions: true,
             headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()}};
  if (payload) { opt.contentType = 'application/json'; opt.payload = JSON.stringify(payload); }
  var res = UrlFetchApp.fetch(url, opt);
  return {code: res.getResponseCode(), text: res.getContentText()};
}

/** read : {which:'new2'|'radar', ranges:["'답요청'!A1:G2000", ...]} → valueRanges (Zapier batchGet 과 같은 모양) */
function km_read_(body) {
  var id = KM_IDS[body.which];
  if (!id || body.which === 'old') return {ok: false, error: '읽을 수 없는 시트'};
  var q = (body.ranges || []).map(function (r) { return 'ranges=' + encodeURIComponent(r); }).join('&');
  var r = km_api_('get', 'https://sheets.googleapis.com/v4/spreadsheets/' + id + '/values:batchGet?' + q);
  if (r.code !== 200) return {ok: false, code: r.code, error: r.text.slice(0, 800)};
  var d = JSON.parse(r.text);
  return {ok: true, valueRanges: d.valueRanges || []};
}

/** batch : {requests:[…]} → 26년 회의록2 batchUpdate (허용 종류만) */
function km_batch_(body) {
  var reqs = body.requests || [];
  for (var i = 0; i < reqs.length; i++) {
    var k = Object.keys(reqs[i])[0];
    if (KM_BATCH_OK.indexOf(k) < 0) return {ok: false, error: '허용 안 된 요청 : ' + k};
  }
  if (!reqs.length) return {ok: true, skipped: '요청 없음'};
  var r = km_api_('post', 'https://sheets.googleapis.com/v4/spreadsheets/' + KM_IDS.new2 + ':batchUpdate', {requests: reqs});
  return {ok: r.code === 200, code: r.code, error: r.code === 200 ? '' : r.text.slice(0, 800), n: reqs.length};
}

/** old26 : {records:[{tab, rows:[[A..G],…], person, preview}]}
 *   탭이 없으면 현장 구역 끝(「현장 갑지」 앞)에 새로 만든다. 같은 날짜+담당자+내용 앞부분이 이미 있으면 건너뛴다.
 *   흰 바탕, 줄바꿈. A열은 글자(6자리 날짜가 숫자로 바뀌지 않게). 반영모음은 2행에 끼워 넣는다(최신이 위). */
function km_old26_(body) {
  var ss = SpreadsheetApp.openById(KM_IDS.old);
  var out = [];
  (body.records || []).forEach(function (rec) {
    var one = {tab: rec.tab, ok: false};
    try {
      var sh = ss.getSheetByName(rec.tab);
      if (!sh) { sh = km_newTab_(ss, rec.tab); one.created = true; }
      var last = km_lastRow_(sh, 7);
      var rows = rec.rows || [];
      if (!rows.length) { one.ok = true; one.skipped = '줄 없음'; out.push(one); return; }
      if (km_dup_(sh, last, rows[0])) { one.ok = true; one.skipped = '이미 있음'; out.push(one); return; }
      var r0 = Math.max(last + 1, 3);
      var rg = sh.getRange(r0, 1, rows.length, 7);
      sh.getRange(r0, 1, rows.length, 1).setNumberFormat('@');
      rg.setValues(rows.map(function (r) { var x = r.slice(0, 7); while (x.length < 7) x.push(''); return x; }));
      rg.setWrap(true).setBackground('#ffffff').setVerticalAlignment('top');
      one.ok = true; one.firstRow = r0; one.lastRow = r0 + rows.length - 1;
      one.link = 'https://docs.google.com/spreadsheets/d/' + KM_IDS.old + '/edit#gid=' + sh.getSheetId() + '&range=A' + r0;
      km_master_(ss, rec, one.link);
    } catch (err) { one.error = String(err); }
    out.push(one);
  });
  return {ok: out.every(function (o) { return o.ok; }), results: out};
}

function km_lastRow_(sh, ncol) {
  var n = sh.getLastRow();
  if (n < 1) return 0;
  var v = sh.getRange(1, 1, n, ncol).getDisplayValues();
  for (var i = v.length - 1; i >= 0; i--) {
    for (var j = 0; j < ncol; j++) if (String(v[i][j]).trim() !== '' && String(v[i][j]) !== 'FALSE') return i + 1;
  }
  return 0;
}

function km_dup_(sh, last, row) {
  if (last < 3) return false;
  var key = function (a, b, c) { return String(a).trim() + '|' + String(b).trim() + '|' + String(c).replace(/\s+/g, '').slice(0, 40); };
  var want = key(row[0], row[1], row[2]);
  var v = sh.getRange(3, 1, last - 2, 3).getDisplayValues();
  for (var i = 0; i < v.length; i++) if (key(v[i][0], v[i][1], v[i][2]) === want) return true;
  return false;
}

function km_newTab_(ss, name) {
  var admin = ss.getSheetByName(KM_OLD_FIRST_ADMIN);
  var idx = admin ? admin.getIndex() - 1 : ss.getSheets().length;   // getIndex 는 1부터, insertSheet 는 0부터
  var sh = ss.insertSheet(name, idx);
  var src = ss.getSheetByName(KM_OLD_HEADER_FROM);
  if (src) {
    src.getRange('A1:G2').copyTo(sh.getRange('A1:G2'));
    for (var c = 1; c <= 7; c++) sh.setColumnWidth(c, src.getColumnWidth(c));
  } else {
    sh.getRange('A2:G2').setValues([['날짜', '담당자', '내용', '캔린더1', '캔린더2', '담당에게 확인해야 할 사항', '회의록']]);
  }
  return sh;
}

function km_master_(ss, rec, link) {
  var m = ss.getSheetByName(KM_OLD_MASTER);
  if (!m) return;
  m.insertRowBefore(2);
  var content = '[신규] ' + String(rec.preview || '').slice(0, 320);
  m.getRange(2, 1, 1, 8).setValues([['', '', new Date(), rec.tab, rec.person || '', content, link, '']]);
  m.getRange(2, 1, 1, 8).setBackground('#ffffff').setWrap(true);
}

/** 설치 뒤 한 번 눌러 보는 시험 (편집기 위 ▶ 실행). 시트를 바꾸지 않는다 */
function km_selfTest() {
  var ss = SpreadsheetApp.openById(KM_IDS.old);
  Logger.log('옛 시트 탭 수 : ' + ss.getSheets().length + ' / 현장 갑지 위치 : ' + (ss.getSheetByName(KM_OLD_FIRST_ADMIN) || {getIndex: function () { return '없음'; }}).getIndex());
  Logger.log('회의록2 : ' + SpreadsheetApp.openById(KM_IDS.new2).getName());
  Logger.log('암호 넣음 : ' + (KM_TOKEN ? '예' : '아니오 — 암호 칸이 비어 있음'));
}

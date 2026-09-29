/**
 * KM_시트쓰기 v11 (2026-09-29 아침) — v11 : appendLog 추가 (차장님 「회의록처럼 대화 핵심을 각 창별로 저장, 총괄할 것은 총괄에도」, 2026-09-29)
 *   새 탭 「대화 로그」(KM_IDS.handover 안, 요약 탭과 같은 시트) — 날짜|창|종류|내용|상태 5칸, 회의록처럼 덧붙이기만(안 지움).
 *   각 세션(창)마다 자기 세션ID 로 「창」 칸을 채워 남기므로, 서로 다른 창이 반대되는 지시를 해도 섞이지 않고 따로 구분됨.
 *   supersede 를 같이 주면 예전 줄의 「상태」 칸만 「대체됨→N행」 으로 고친다(그 줄 자체는 지우지 않음 — 무엇이 무엇으로 바뀌었는지 이력이 남는다).
 *   appendLog : {row:[날짜,창,종류,내용,상태], supersede:{row,note}}
 * KM_시트쓰기 v10 (2026-09-28 밤) — v10 : setHandover 추가 (차장님 「새 창 만들 때마다 인수인계 준비하는 시트」, 2026-09-28 밤)
 *   새 구글시트 「KM 인수인계」(KM_IDS.handover) 요약 1장에 지금 상태를 통째로 덮어쓴다 — 누적 안 함(항상 「지금」만 보여준다).
 *   md 파일(2_창이어가기_vN)은 그대로 상세 기록으로 계속 쓴다 — 이 시트는 그 위에 얹는 "요약 1장"일 뿐, md 를 대신하지 않는다.
 *   setHandover : {rows:[[항목,내용],...]} — 첫 탭을 통째로 지우고 그 rows 로 다시 쓴다(줄바꿈 있는 칸은 자동 줄바꿈).
 * KM_시트쓰기 v9 (2026-09-28 밤) — v9 : appendDoc 추가 (차장님 「메일·보고서도 구글시트에 탭 만들어서 날짜별로 누적」·「캘린더 1개 더」, 2026-09-28 밤)
 *   appendDoc : {tab:'메일'|'보고서', rows:[[날짜,현장,할일,본문],…], markTab, marks} — 그 탭에 4칸 줄을 덧붙이기만(덮어쓰지 않음, 탭 없으면 새로 만듦).
 *     markTab·marks 를 같이 주면 append 가 된 다음에만 그 탭 J열도 같이 표시한다 — 한 번의 요청으로 묶어서, 시트에 안 들어갔는데 「만듦」 표시만 되는 일이 없게 한다.
 *   KM_DOC_PICKS 에 「캘린더」 추가 — sweep 이 나머지 4종과 같이 「만들 차례」 탭으로 옮긴다. 구글캘린더 등록은 이 웹 앱이 아니라 1시간 Routine(대화창 도구)이 직접 한다.
 * KM_시트쓰기 v8 (2026-09-28 낮) — v8 : markQueue 추가 — 「만들 차례」 탭 J열에 표시해 t56_makequeue 가 만든 것을 또 안 만들게 한다
 *   markQueue : {tab, marks:[{row, text}]} — 그 칸만 쓴다. km_sweepTab_ 도 「만들 차례」 탭만 J「생성결과」 한 칸 더 만든다
 * KM_시트쓰기 v7 (2026-09-28 낮) — v7 : sweep 이 두 갈래 더 처리(차장님 「아니야는 삭제로」·「만들어줘 4개로 나눠」, 2026-09-28)
 *   고르기(E열)='아니야'  → 「삭제된 것」 탭으로 옮기고 원본에서 지운다 (필요 없는 내용)
 *   고르기(E열)=제안서·보고서·메일·작업의뢰서 중 하나 → 「만들 차례」 탭으로 옮기고 원본에서 지운다
 *     (실제로 만드는 것은 이 웹 앱이 아니라 1시간마다 도는 별도 Routine — 문서 내용 판단은 여기서 안 한다)
 *   완료 > 아니야 > 답 결정 > 문서 4종 순으로 센다(한 줄이 여러 조건에 걸치면 앞선 것으로만 감). onOpen·doPost 양쪽 다 새 갈래를 그대로 씀
 * KM_시트쓰기 v6.1 (2026-09-28 낮) — v6.1 : 방금 붙이신 v6 이 그 자리에서 오류(「지정된 권한으로는 SpreadsheetApp.openById 을 호출할 수 없습니다」) —
 *   onOpen(단순 트리거)은 openById 를 쓸 권한이 없다. km_sweep_ 에 ss 를 직접 넘길 수 있게 고치고, onOpen 은 getActiveSpreadsheet() 를 넘긴다. sweep 로직 자체는 안 바꿈
 * KM_시트쓰기 v6 (2026-09-28) — v6 : onOpen 추가 (차장님 「내가 원할 때 새로고침을 하면 옮겨지는 것으로 해」, 2026-09-28)
 *   onOpen : 「26년 회의록2」 를 열거나(브라우저 새로고침 포함) sweep({}) 을 자동으로 한 번 돌린다. 결과는 화면 아래 토스트로.
 *            07:00 자동 실행과는 별개 — 차장님이 체크하신 뒤 브라우저를 새로고침하는 순간마다 반영된다(정해진 시각을 기다리지 않는다)
 *            암호(KM_TOKEN) 없이도 돈다 — 웹 앱 밖에서, doPost 를 거치지 않고 시트 안에서 직접 부른다
 * KM_시트쓰기 v5 (2026-09-28) — v5 : sweep 추가 (차장님 「완료 채크 한것은 삭제 하도록 양방향 소통」 · 「고르기 답 결정」, 2026-09-28)
 *   sweep : 「26년 회의록2」 답요청·오늘 할일·앞으로 할일 3탭에서
 *           완료(D열 체크) 된 줄 → 「완료 기록」 탭으로 옮기고 원본에서 지운다
 *           고르기(E열)="답 결정" 인 줄     → 「답 결정」 탭으로 옮기고 원본에서 지운다 (완료 체크가 더 세다 — 둘 다면 완료 기록으로)
 *           두 탭은 없으면 새로 만든다(원본과 같은 7칸 + H「원본탭」 + I「처리일」). A·B열 세로 병합은 지운 뒤 다시 계산해 붙인다.
 *           {dry:true} 면 세기만 하고 시트를 바꾸지 않는다. {tabs:[...]} 로 대상 탭을 고를 수 있다(기본 3탭 전부)
 *   ★ v4 까지의 「지우는 기능은 없다」 는 이 sweep 하나로 깨졌다 — 답요청·오늘 할일·앞으로 할일 3탭에서만, 완료 기록·답 결정 탭으로
 *     옮긴 뒤에만 원본 줄을 지운다(그냥 버리지 않는다). 다른 action 은 여전히 지우지 않는다.
 * KM_시트쓰기 v4 (2026-09-27) — v4 : oldStrip (옛 시트 통찰 칸 끝 「/ =====」 구분선 지우기) · 옛 시트 읽기 허용 (확인용)
 * KM_시트쓰기 v3 (2026-09-25)  — 클로드가 부르는 웹 앱. Zapier 없이 0원·무제한.
 *   v3 : read·batch 를 「Google Sheets API」 서비스(편집기 왼쪽 서비스 + 에서 추가)로 — UrlFetch 는 프로젝트에서 API 를 켜야 해서 403 이 났다
 *   v2 : oldMerge 추가 — 차장님 지시 「예전에 잘못 만들어진 이름은 합쳐야 돼」 (옛 탭 이름 바꾸기, 이미 있으면 줄 옮기기. 지우지 않는다)
 *   ping   : 연결 확인
 *   read   : 「26년 회의록2」·「신규 현장 레이더」 읽기 (값 그대로)
 *   batch  : 「26년 회의록2」 에 줄 덧붙이기·병합·체크박스·▼ (t53 --write 가 만든 본문 그대로)
 *   old26  : 옛 「26년 회의록」 현장 탭에 회의 기록 덧붙이기 + 「0.전체 반영모음」 맨 위에 한 줄
 *   oldMerge : 옛 탭 합치기 {merges:[{from,to}]} — to 가 없으면 from 을 to 로 이름 바꿈 / to 가 있으면 from 의 줄(3행~)을 to 끝에 옮기고 from 은 「(합침) from」 으로 이름만 바꿈
 *
 * ★ 설치 : 확장 프로그램 → Apps Script → 왼쪽 「서비스 +」 → Google Sheets API 추가(식별자 Sheets) → 이 전문 붙여넣기 → KM_TOKEN 칸에 클로드가 드린 암호
 *          → 배포 → 배포 관리 → 연필 → 버전 「새 버전」 → 배포 → 완료  (주소는 그대로 — 「새 배포」 는 하지 않는다)
 */

var KM_TOKEN = '';   // ← 클로드가 드린 암호를 따옴표 안에 (저장소에는 비워 둔다 — 공개 저장소)

var KM_IDS = {
  new2:  '1S02QcwHnRNiJJbq3qfSPs9sRtR1UDtTMSUPhLy4_Ckk',   // 26년 회의록2 (읽기·쓰기)
  radar: '1LWK3fmXgf2_aG12B3cunutLUHnSqNMDf_sr3lXOyr-c',   // 신규 현장 레이더 (읽기만)
  old:   '1RzDj_mm3fY6l42hF9AJ-r5KY50OCVIV7IwSIQeh3rms',   // 옛 26년 회의록 (old26 로만 쓴다)
  handover: '1kqRpOf_oqAA66Jg98nkjFDR2JYYoFaImmci8XohOOnA'  // v10 (2026-09-28 밤) KM 인수인계 — 요약 1장, setHandover 로만 쓴다
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
    if (body.action === 'ping')  return km_out_({ok: true, version: 'v11 2026-09-29', sheetsService: (typeof Sheets !== 'undefined'), now: new Date().toISOString()});
    if (body.action === 'read')  return km_out_(km_read_(body));
    if (body.action === 'batch') return km_out_(km_batch_(body));
    if (body.action === 'old26') return km_out_(km_old26_(body));
    if (body.action === 'oldMerge') return km_out_(km_oldMerge_(body));
    if (body.action === 'oldStrip') return km_out_(km_oldStrip_(body));
    if (body.action === 'sweep') return km_out_(km_sweep_(body));
    if (body.action === 'markQueue') return km_out_(km_markQueue_(body));
    if (body.action === 'appendDoc') return km_out_(km_appendDoc_(body));
    if (body.action === 'setHandover') return km_out_(km_setHandover_(body));
    if (body.action === 'appendLog') return km_out_(km_appendLog_(body));
    return km_out_({ok: false, error: '모르는 action : ' + body.action});
  } catch (err) {
    return km_out_({ok: false, error: String(err && err.stack || err)});
  }
}

function km_out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

/** read : {which:'new2'|'radar', ranges:["'답요청'!A1:G2000", ...]} → valueRanges (Zapier batchGet 과 같은 모양)
 *   Google Sheets API 서비스(Sheets) 를 쓴다. 서비스가 안 붙어 있으면 그 말을 돌려준다 */
function km_read_(body) {
  var id = KM_IDS[body.which];
  if (!id) return {ok: false, error: '읽을 수 없는 시트'};   // v4 : old 도 읽기 허용 (확인용)
  if (typeof Sheets === 'undefined') return {ok: false, error: '편집기 왼쪽 「서비스 +」 에서 Google Sheets API 를 추가해 주십시오'};
  var d = Sheets.Spreadsheets.Values.batchGet(id, {ranges: body.ranges || []});
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
  if (typeof Sheets === 'undefined') return {ok: false, error: '편집기 왼쪽 「서비스 +」 에서 Google Sheets API 를 추가해 주십시오'};
  Sheets.Spreadsheets.batchUpdate({requests: reqs}, KM_IDS.new2);
  return {ok: true, n: reqs.length};
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

/** oldMerge : {merges:[{from:'조선호텔 리뉴얼 ', to:'조선호텔'}, …]}  순서대로. 차장님 표(옛시트_탭이름.json _합치기) 그대로 */
function km_oldMerge_(body) {
  var ss = SpreadsheetApp.openById(KM_IDS.old);
  var out = [];
  (body.merges || []).forEach(function (m) {
    var one = {from: m.from, to: m.to, ok: false};
    try {
      var src = ss.getSheetByName(m.from);
      if (!src) { one.error = '탭 없음 : ' + m.from; out.push(one); return; }
      if (!m.to || m.to === m.from) { one.error = '바꿀 이름 없음'; out.push(one); return; }
      var dst = ss.getSheetByName(m.to);
      if (!dst) {
        src.setName(m.to); one.ok = true; one.did = '이름 바꿈';
      } else {
        var last = km_lastRow_(src, 7);
        var n = last - 2;
        if (n > 0) {
          var vals = src.getRange(3, 1, n, 7).getValues();
          var dl = km_lastRow_(dst, 7);
          var r0 = Math.max(dl + 1, 3);
          dst.getRange(r0, 1, 1, 1).setNumberFormat('@');
          dst.getRange(r0, 1, n, 1).setNumberFormat('@');
          dst.getRange(r0, 1, n, 7).setValues(vals).setWrap(true).setBackground('#ffffff').setVerticalAlignment('top');
          one.moved = n; one.firstRow = r0;
        }
        var keep = '(합침) ' + m.from;
        if (!ss.getSheetByName(keep)) src.setName(keep);
        one.ok = true; one.did = '줄 옮기고 (합침) 표시';
      }
    } catch (err) { one.error = String(err); }
    out.push(one);
  });
  return {ok: out.every(function (o) { return o.ok; }), results: out};
}

/** oldStrip (v4, 2026-09-27 차장님 「맞다고 생각한 것은 다 해」) :
 *   옛 「26년 회의록」 현장 탭 F칸(통찰) 끝에 t53_old26 v1 이 잘못 붙인 「/ ===================」 를 지운다.
 *   고치는 것 : 날짜(A)가 2609 로 시작하는 줄의 F칸만, 끝이 「=」 3개 이상으로 끝나는 것만. 셀 끝 빈 줄 3개는 그대로 둔다. 지우는 줄·다른 칸 없음.
 *   {dry:true} 면 세기만 한다 */
function km_oldStrip_(body) {
  var ss = SpreadsheetApp.openById(KM_IDS.old);
  var fixed = 0, tabs = [];
  ss.getSheets().forEach(function (sh) {
    var name = sh.getName();
    if (name.indexOf('0.') === 0 || name === KM_OLD_FIRST_ADMIN || name === '할 일 모음' || name === '업무일지') return;
    var last = sh.getLastRow();
    if (last < 3) return;
    var a = sh.getRange(3, 1, last - 2, 1).getDisplayValues();
    var f = sh.getRange(3, 6, last - 2, 1).getValues();
    var n = 0;
    for (var i = 0; i < f.length; i++) {
      if (String(a[i][0]).trim().indexOf('2609') !== 0) continue;
      var v = String(f[i][0]);
      var m = v.match(/^([\s\S]*?)(\s*\/\s*={3,}|\n?그 밖의 할 일 : ={3,})(\s*)$/);
      if (!m) continue;
      var tail = /\n\s*$/.test(v) ? '\n\n\n' : '';
      f[i][0] = m[1].replace(/\s+$/, '') + tail;
      n++;
    }
    if (n) {
      if (!body.dry) sh.getRange(3, 6, last - 2, 1).setValues(f);
      fixed += n; tabs.push(name + ' ' + n);
    }
  });
  return {ok: true, dry: !!body.dry, fixed: fixed, tabs: tabs};
}


// v7 (2026-09-28 낮) : 고르기(E열) 문서 종류 — 고르면 「만들 차례」 탭으로(1시간마다 도는 Routine 이 만든다). 「아니야」 는 「삭제된 것」 탭으로(필요 없는 내용, 차장님 확정)
// v9 (2026-09-28 밤) : 「캘린더」 추가 — 나머지 4종과 같은 「만들 차례」 탭으로 옮기고, 구글캘린더 등록은 Routine 이 직접 한다(이 웹 앱은 시트만 다룬다)
var KM_DOC_PICKS = ['제안서', '보고서', '메일', '작업의뢰서', '캘린더'];

/** sweep (v7, 2026-09-28) : {tabs:['답요청','오늘 할일','앞으로 할일'], dry:true|false}
 *   답요청·오늘 할일·앞으로 할일 각 탭에서, 세는 순서(세면 그 줄은 다른 걸로 안 셈) :
 *     완료(D열 체크)               → 「완료 기록」 탭
 *     고르기(E열)='아니야'         → 「삭제된 것」 탭 (v7, 필요 없는 내용)
 *     고르기(E열)='답 결정'        → 「답 결정」 탭
 *     고르기(E열)=문서 4종 중 하나 → 「만들 차례」 탭 (v7, 제안서·보고서·메일·작업의뢰서 — 1시간마다 도는 Routine 이 만든다)
 *   지운 뒤 A(날짜)·B(현장) 세로 병합을 다시 계산해 붙인다. {dry:true} 면 세기만 하고 시트를 바꾸지 않는다. */
function km_sweep_(body, ss) {
  // ss 를 안 주면(doPost 경로) openById. onOpen(단순 트리거)은 openById 를 쓸 권한이 없어 getActiveSpreadsheet() 를 넘겨준다(9/28 오류로 발견)
  ss = ss || SpreadsheetApp.openById(KM_IDS.new2);
  var names = body.tabs || ['답요청', '오늘 할일', '앞으로 할일'];
  var dry = !!body.dry;
  var doneTab = dry ? null : km_sweepTab_(ss, '완료 기록');
  var delTab = dry ? null : km_sweepTab_(ss, '삭제된 것');
  var pickTab = dry ? null : km_sweepTab_(ss, '답 결정');
  var makeTab = dry ? null : km_sweepTab_(ss, '만들 차례');
  var out = [];
  names.forEach(function (name) {
    var sh = ss.getSheetByName(name);
    if (!sh) { out.push({tab: name, error: '탭 없음'}); return; }
    var last = sh.getLastRow();
    var n = last - 1;
    if (n <= 0) { out.push({tab: name, 전체: 0, 완료: 0, 삭제: 0, 답결정: 0, 만들차례: 0, 남김: 0}); return; }
    var vals = sh.getRange(2, 1, n, 7).getValues();
    var lastA = '', lastB = '';                              // 세로 병합이라 이어지는 줄은 A·B가 빈칸 — 지우기 전에 채워 넣는다
    for (var f = 0; f < vals.length; f++) {
      if (vals[f][0] !== '') lastA = vals[f][0]; else vals[f][0] = lastA;
      if (vals[f][1] !== '') lastB = vals[f][1]; else vals[f][1] = lastB;
    }
    var keep = [], doneRows = [], delRows = [], pickRows = [], makeRows = [];
    for (var i = 0; i < vals.length; i++) {
      var r = vals[i], e = String(r[4]).trim();
      if (r[3] === true || r[3] === '완료') doneRows.push(r);
      else if (e === '아니야') delRows.push(r);
      else if (e === '답 결정') pickRows.push(r);
      else if (KM_DOC_PICKS.indexOf(e) >= 0) makeRows.push(r);
      else keep.push(r);
    }
    var rec = {tab: name, 전체: vals.length, 완료: doneRows.length, 삭제: delRows.length,
               답결정: pickRows.length, 만들차례: makeRows.length, 남김: keep.length};
    if (!dry && (doneRows.length || delRows.length || pickRows.length || makeRows.length)) {
      sh.getRange(2, 1, n, 2).breakApart();               // 옛 세로 병합 먼저 해제
      sh.getRange(2, 1, n, 7).clearContent();
      if (keep.length) sh.getRange(2, 1, keep.length, 7).setValues(keep);
      if (n > keep.length) sh.deleteRows(2 + keep.length, n - keep.length);
      km_reMerge_(sh, keep.length);
      if (doneRows.length) km_sweepAppend_(doneTab, name, doneRows);
      if (delRows.length) km_sweepAppend_(delTab, name, delRows);
      if (pickRows.length) km_sweepAppend_(pickTab, name, pickRows);
      if (makeRows.length) km_sweepAppend_(makeTab, name, makeRows);
    }
    out.push(rec);
  });
  return {ok: true, dry: dry, tabs: out};
}

/** 완료 기록 · 삭제된 것 · 답 결정 · 만들 차례 탭 — 없으면 만든다(원본 7칸 + H 원본탭 + I 처리일).
 *   「만들 차례」 탭만 J 「생성결과」 한 칸 더(v8) — t56_makequeue 가 만든 뒤 markQueue 로 여기 적으면 다음엔 또 안 만든다 */
function km_sweepTab_(ss, name) {
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    var head = ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)', '원본탭', '처리일'];
    if (name === '만들 차례') head.push('생성결과');
    sh.getRange(1, 1, 1, head.length).setValues([head]);
    sh.getRange(1, 1, 1, head.length).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  return sh;
}

/** markQueue (v8) : {tab:'만들 차례', marks:[{row:2, text:'만듦 · 파일명'}, ...]}
 *   지정한 탭의 J열(10번째)에 값을 쓴다. row 는 read 로 받은 값 배열 인덱스 + 2(머리줄 다음이 2행).
 *   t56_makequeue 가 문서를 실제로 만든 뒤 「또 만들지 않도록」 표시하는 용도. 그 칸만 쓴다 — 다른 칸은 안 건드리고 지우지 않는다 */
function km_markQueue_(body) {
  var ss = SpreadsheetApp.openById(KM_IDS.new2);
  var sh = ss.getSheetByName(body.tab || '');
  if (!sh) return {ok: false, error: '탭 없음 : ' + body.tab};
  var marks = body.marks || [];
  marks.forEach(function (m) { sh.getRange(m.row, 10).setValue(m.text || ''); });
  return {ok: true, n: marks.length};
}

// v9 (2026-09-28 밤) : 메일·보고서 전용 탭 — 이 두 개만 허용(다른 탭 이름은 거절, 아무 데나 못 쓰게)
var KM_DOC_TABS = ['메일', '보고서'];

/** appendDoc (v9) : {tab:'메일'|'보고서', rows:[[날짜,현장,할일,본문],…], markTab, marks:[{row,text}]}
 *   그 탭에 4칸 줄을 덧붙이기만 한다 — 날짜별로 누적, 덮어쓰지 않는다. 탭이 없으면 머리줄(날짜|현장|할일|본문)과 함께 새로 만든다.
 *   markTab·marks 를 같이 주면(t56_makequeue 가 「만들 차례」 J열도 같이 표시하고 싶을 때) append 가 실제로 된 다음에만 그 탭 J열을 쓴다 —
 *   한 번의 요청으로 묶어서 "시트엔 안 들어갔는데 표시만 됨(다시 안 만듦)" 이 생기지 않게 한다 */
function km_appendDoc_(body) {
  var tab = body.tab;
  if (KM_DOC_TABS.indexOf(tab) < 0) return {ok: false, error: '허용 안 된 탭 : ' + tab};
  var rows = (body.rows || []).map(function (r) {
    var x = (r || []).slice(0, 4);
    while (x.length < 4) x.push('');
    return x;
  });
  var ss = SpreadsheetApp.openById(KM_IDS.new2);
  var sh = ss.getSheetByName(tab);
  if (!sh) {
    sh = ss.insertSheet(tab);
    sh.getRange(1, 1, 1, 4).setValues([['날짜', '현장', '할일', '본문']]);
    sh.getRange(1, 1, 1, 4).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  var n = 0, firstRow = 0;
  if (rows.length) {
    var r0 = sh.getLastRow() + 1;
    sh.getRange(r0, 1, rows.length, 1).setNumberFormat('@');
    sh.getRange(r0, 1, rows.length, 4).setValues(rows).setWrap(true).setVerticalAlignment('top');
    n = rows.length; firstRow = r0;
  }
  var marked = 0;
  if (body.markTab && body.marks && body.marks.length) {
    var msh = ss.getSheetByName(body.markTab);
    if (msh) {
      body.marks.forEach(function (m) { msh.getRange(m.row, 10).setValue(m.text || ''); });
      marked = body.marks.length;
    }
  }
  return {ok: true, tab: tab, n: n, firstRow: firstRow, marked: marked};
}

/** setHandover (v10) : {rows:[[항목,내용],...]} — 「KM 인수인계」 시트 첫 탭을 통째로 지우고 다시 쓴다.
 *   누적하지 않는다(md 파일이 이미 상세 기록을 맡는다) — 이 시트는 "지금 이 순간"만 보여주는 요약 1장이라 매번 덮어쓰는 게 맞다. */
function km_setHandover_(body) {
  var rows = (body.rows || []).map(function (r) { return [String((r || [])[0] || ''), String((r || [])[1] || '')]; });
  var ss = SpreadsheetApp.openById(KM_IDS.handover);
  var sh = ss.getSheets()[0];
  sh.clearContents();
  sh.setName('요약');
  if (rows.length) {
    sh.getRange(1, 1, rows.length, 2).setValues(rows).setWrap(true).setVerticalAlignment('top');
    sh.setColumnWidth(1, 160);
    sh.setColumnWidth(2, 640);
    sh.getRange(1, 1, rows.length, 1).setFontWeight('bold');
  }
  return {ok: true, n: rows.length, url: 'https://docs.google.com/spreadsheets/d/' + KM_IDS.handover + '/edit'};
}

/** appendLog (v11) : {row:[날짜,창,종류,내용,상태], supersede:{row,note}}
 *   「KM 인수인계」 시트 안 「대화 로그」 탭(요약 탭과 같은 시트, 다른 탭)에 한 줄 덧붙인다 — 회의록처럼 누적, 안 지움.
 *   탭이 없으면 머리줄(날짜|창|종류|내용|상태)과 함께 새로 만든다.
 *   supersede.row 를 주면(예전에 적어 둔 줄 번호) 그 줄의 「상태」 칸만 「대체됨→새 줄 번호」 로 고친다 — 그 줄 자체는 지우지 않는다(무엇이 무엇으로
 *   바뀌었는지 이력이 남아야, 서로 다른 창이 반대로 지시했을 때 어느 것이 최신인지 다음 창이 헷갈리지 않는다). */
function km_appendLog_(body) {
  var ss = SpreadsheetApp.openById(KM_IDS.handover);
  var sh = ss.getSheetByName('대화 로그');
  if (!sh) {
    sh = ss.insertSheet('대화 로그');
    sh.getRange(1, 1, 1, 5).setValues([['날짜', '창', '종류', '내용', '상태']]);
    sh.getRange(1, 1, 1, 5).setFontWeight('bold');
    sh.setFrozenRows(1);
    sh.setColumnWidth(4, 600);
  }
  var row = body.row || [];
  var r0 = sh.getLastRow() + 1;
  var vals = [String(row[0] || ''), String(row[1] || ''), String(row[2] || ''), String(row[3] || ''), String(row[4] || '유효')];
  sh.getRange(r0, 1, 1, 5).setValues([vals]).setWrap(true).setVerticalAlignment('top');
  if (body.supersede && body.supersede.row) {
    var note = body.supersede.note ? ' (' + body.supersede.note + ')' : '';
    sh.getRange(body.supersede.row, 5).setValue('대체됨→' + r0 + '행' + note);
  }
  return {ok: true, row: r0, url: 'https://docs.google.com/spreadsheets/d/' + KM_IDS.handover + '/edit'};
}

function km_sweepAppend_(sh, fromName, rows) {
  var last = sh.getLastRow();
  var r0 = last + 1;
  var today = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');
  var out = rows.map(function (r) {
    var x = r.slice(0, 7);
    while (x.length < 7) x.push('');
    x.push(fromName, today);
    return x;
  });
  sh.getRange(r0, 1, out.length, 9).setValues(out).setWrap(true).setVerticalAlignment('top');
}

/** 지운 뒤 A(날짜)·B(현장) 세로 병합을 남은 n줄(2행부터) 기준으로 다시 계산해 붙인다.
 *   A 열은 값이 이어지는 만큼, B 열은 같은 A 그룹 안에서 값이 이어지는 만큼(v11 규칙 그대로) */
function km_reMerge_(sh, n) {
  if (n <= 0) return;
  var v = sh.getRange(2, 1, n, 2).getValues();
  var i = 0;
  while (i < n) {
    var j = i;
    while (j + 1 < n && v[j + 1][0] === v[i][0] && v[i][0] !== '') j++;
    if (j > i) sh.getRange(2 + i, 1, j - i + 1, 1).merge();
    var k = i;
    while (k <= j) {
      var m = k;
      while (m + 1 <= j && v[m + 1][1] === v[k][1] && v[k][1] !== '') m++;
      if (m > k) sh.getRange(2 + k, 2, m - k + 1, 1).merge();
      k = m + 1;
    }
    i = j + 1;
  }
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

/** onOpen (v6, 2026-09-28 차장님 「내가 원할 때 새로고침을 하면 옮겨지는 것으로 해」) :
 *   「26년 회의록2」 를 열 때마다(브라우저 새로고침도 「다시 열기」 라 포함) sweep({}) 을 자동으로 한 번 돌린다.
 *   07:00 자동 실행과 별개 — 중복으로 돌아도 옮길 게 없으면 그냥 아무 일도 안 한다. 옮긴 게 있을 때만 화면 아래 토스트로 알린다.
 *   실패해도 시트 자체는 문제없이 열리도록 통째로 감싼다(에러가 나도 열기를 막지 않는다)
 *   ★ v6-1 (2026-09-28 낮 오류 수정) : onOpen 은 「단순 트리거」 라 SpreadsheetApp.openById 를 쓸 권한이 없다(「지정된 권한으로는 호출할 수 없습니다」).
 *     그래서 openById(KM_IDS.new2) 대신 이 시트 자체인 getActiveSpreadsheet() 를 km_sweep_ 에 직접 넘긴다 */
function onOpen(e) {
  try {
    var r = km_sweep_({}, SpreadsheetApp.getActiveSpreadsheet());
    var done = 0, del = 0, pick = 0, make = 0;
    (r.tabs || []).forEach(function (t) {
      done += t.완료 || 0; del += t.삭제 || 0; pick += t.답결정 || 0; make += t.만들차례 || 0;
    });
    if (done + del + pick + make > 0) {
      var msg = '완료 기록 ' + done + '건 · 삭제 ' + del + '건 · 답 결정 ' + pick + '건';
      if (make) msg += ' · 만들 차례 ' + make + '건(1시간 안에 만들어 드립니다)';
      SpreadsheetApp.getActiveSpreadsheet().toast(msg, 'KM 자동 정리', 5);
    }
  } catch (err) {
    try { SpreadsheetApp.getActiveSpreadsheet().toast('자동 정리 중 오류 : ' + err, 'KM', 5); } catch (e2) { /* 토스트도 실패하면 조용히 넘어간다 */ }
  }
}

/** 설치 뒤 한 번 눌러 보는 시험 (편집기 위 ▶ 실행). 시트를 바꾸지 않는다 */
function km_selfTest() {
  var ss = SpreadsheetApp.openById(KM_IDS.old);
  Logger.log('옛 시트 탭 수 : ' + ss.getSheets().length + ' / 현장 갑지 위치 : ' + (ss.getSheetByName(KM_OLD_FIRST_ADMIN) || {getIndex: function () { return '없음'; }}).getIndex());
  Logger.log('회의록2 : ' + SpreadsheetApp.openById(KM_IDS.new2).getName());
  Logger.log('암호 넣음 : ' + (KM_TOKEN ? '예' : '아니오 — 암호 칸이 비어 있음'));
  Logger.log('Sheets API 서비스 : ' + (typeof Sheets !== 'undefined' ? '붙어 있음' : '없음 — 왼쪽 서비스 + 에서 Google Sheets API 추가'));
}

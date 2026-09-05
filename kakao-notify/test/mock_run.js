/**
 * Code.gs 모의 실행기 — Apps Script 전역 객체(SpreadsheetApp 등)를 흉내 내어 Node에서 돌린다.
 *   node kakao-notify/test/mock_run.js
 * 정상 경로 + 고장 경로를 함께 검사한다. 실패하면 종료코드 1.
 */
const fs = require('fs'); const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', 'Code.gs'), 'utf8');

// ─── 스텁 ───
const NOW = new Date(2026, 8, 7, 7, 30); // 2026-09-07(월) 07:30 KST 가정
let fetchLog = [], mailLog = [], logRows = [], props = {}, sheets = {}, calEvents = {};
const kapi = { status: 200, body: '{"result_code":0}' };
const kauth = { status: 200, body: JSON.stringify({ access_token: 'AT2', expires_in: 21600, refresh_token: 'RT2', refresh_token_expires_in: 5184000 }) };
const userMe = { status: 200, body: '{"id":111}' };
let triggers = [];

function mkSheet(name, rows) {
  const data = rows.map(r => r.slice());
  return {
    _name: name, _data: data,
    getName: () => name, setName(n) { this._name = n; return this; },
    getDataRange() { const d = data; return { getValues: () => d.map(r => (r || []).slice()) }; },
    getLastRow: () => data.length, getLastColumn: () => Math.max(...data.map(r => r.length), 1),
    getRange(r, c, nr = 1, nc = 1) {
      return {
        getValues: () => Array.from({ length: nr }, (_, i) => Array.from({ length: nc }, (_, j) => (data[r - 1 + i] || [])[c - 1 + j] ?? '')),
        setValues(v) { if (v.length !== nr || v.some(row => row.length !== nc)) throw new Error('setValues 크기 불일치 ' + v.length + 'x' + (v[0] || []).length + ' vs ' + nr + 'x' + nc); for (let i = 0; i < nr; i++) { data[r - 1 + i] = data[r - 1 + i] || []; for (let j = 0; j < nc; j++) data[r - 1 + i][c - 1 + j] = v[i][j]; } return this; },
        setFontWeight() { return this; }, setBackground() { return this; }
      };
    },
    appendRow(row) { data.push(row.slice()); if (name === '발송로그') logRows.push(row); return this; },
    deleteRows() {}, setFrozenRows() {}, setColumnWidth() {}, getUrl: () => 'https://sheet/' + name
  };
}
function mkSS(id, tabs) {
  const ss = { _id: id, _tabs: tabs, getId: () => id, getUrl: () => 'https://docs.google.com/' + id,
    getSheetByName: n => tabs[n] || Object.values(tabs).find(t => t._name === n) || null, getSheets: () => Object.values(tabs),
    insertSheet(n) { tabs[n] = mkSheet(n, []); return tabs[n]; } };
  return ss;
}
global.SpreadsheetApp = { openById: id => { if (!sheets[id]) throw new Error('no sheet ' + id); return sheets[id]; }, create: t => { const ss = mkSS('CFG', { Sheet1: mkSheet('Sheet1', []) }); sheets.CFG = ss; return ss; } };
global.PropertiesService = { getScriptProperties: () => ({ getProperty: k => props[k] ?? null, setProperty: (k, v) => { props[k] = v; }, setProperties: o => Object.assign(props, o), deleteProperty: k => { delete props[k]; } }) };
global.UrlFetchApp = { fetch: (url, opt) => { fetchLog.push({ url, opt }); const r = url.indexOf('kauth') >= 0 ? kauth : url.indexOf('user/me') >= 0 ? userMe : kapi; return { getResponseCode: () => r.status, getContentText: () => r.body }; } };
let uuidN = 0;
global.Utilities = { getUuid: () => 'uuid-' + (++uuidN) + '-xxxx', formatDate: (d, tz, fmt) => { const p = n => String(n).padStart(2, '0'); const m = { yyyy: d.getFullYear(), MM: p(d.getMonth() + 1), dd: p(d.getDate()), HH: p(d.getHours()), mm: p(d.getMinutes()), ss: p(d.getSeconds()), M: d.getMonth() + 1, d: d.getDate() }; return fmt.replace(/yyyy|MM|dd|HH|mm|ss|M|d/g, k => m[k]); } };
global.Logger = { log: () => {} };
global.Session = { getEffectiveUser: () => ({ getEmail: () => 'me@example.com' }) };
global.MailApp = { sendEmail: (to, sub, body) => mailLog.push({ to, sub, body }) };
global.CalendarApp = { getDefaultCalendar: () => ({ getEventsForDay: d => (calEvents[d.getDate()] || []).map(e => ({ getTitle: () => e.t, isAllDayEvent: () => !!e.all, getStartTime: () => new Date(2026, 8, d.getDate(), e.h || 9, 0) })) }), getCalendarById: () => null };
let driveFiles = [];
global.DriveApp = { getFolderById: () => ({ getFiles: () => { let i = 0; return { hasNext: () => i < driveFiles.length, next: () => driveFiles[i++] }; } }), getFileById: () => ({ moveTo() {} }) };
global.ScriptApp = { getProjectTriggers: () => triggers.slice(), deleteTrigger(t) { triggers = triggers.filter(x => x !== t); }, newTrigger: (fn) => ({ _fn: fn, timeBased() { return this; }, everyDays() { return this; }, everyHours() { return this; }, atHour(h) { this._h = h; return this; }, nearMinute(m) { this._m = m; return this; }, inTimezone() { return this; }, create() { const t = { getHandlerFunction: () => fn, _h: this._h, _m: this._m }; triggers.push(t); return t; } }), getService: () => ({ getUrl: () => 'https://script.google.com/macros/s/X/exec' }) };
global.HtmlService = { createHtmlOutput: h => ({ _h: h, setXFrameOptionsMode() { return this; } }), XFrameOptionsMode: { ALLOWALL: 1 } };

// Code.gs 로드 (전역 함수로)
const vm = require('vm'); vm.runInThisContext(src, { filename: 'Code.gs' });
// 시각 고정
global.nowKST_ = () => new Date(NOW);
// Date.now 고정 (토큰 만료 판정용)
const FIXED_NOW = NOW.getTime(); Date.now = () => FIXED_NOW;

// ─── 시트 데이터 (실제 규격대로) ───
function seed() {
  fetchLog = []; mailLog = []; logRows = []; props = {}; driveFiles = []; calEvents = {}; triggers = [];
  if (typeof clearSettingsCache_ === 'function') clearSettingsCache_();
  sheets = {};
  sheets[KM.MEETING_SHEET_ID] = mkSS(KM.MEETING_SHEET_ID, {
    '할 일 모음': mkSheet('할 일 모음', [
      ['=AI(...)', '', '', '', '', '', '', '', '', ''],
      ['기한', '종류', '현장', '할 일', '상대', '상태', '(D-)', '현장시트', '통화원본', '캘린더ID'],
      ['260905', '확인', '조선호텔 리뉴얼', '외함 규격 회신', '김과장', '진행', '', '', '', ''],      // D+2 지남
      ['260907', '전달', '유한대 기숙사', '작업의뢰서 MB-004 발행', '설계팀', '', '', '', '', ''],    // D-day
      ['260909(예정)', '방문', '제천 워케이션', '벽지 완료 확인 후 빽커버 설치 일정', '현장소장', '', '', '', '', ''], // D-2
      ['260920', '확인', '청담PJ', '키센서 폐지 반영 도면', '', '', '', '', '', ''],                  // D-13 → 경고 밖
      ['260906', '확인', '전북연수원', '이미 끝난 일', '', '완료', '', '', '', ''],                   // 완료 → 제외
      ['', '', '', '', '', '', '', '', '', '']
    ]),
    '0.무조건할일': mkSheet('0.무조건할일', [
      ['완료', '★', '날짜', '현장', '담당', '내용', '구분', '링크', '출처', '알림 횟수', '마지막 알림일', '완료일'],
      [false, false, '260903', '조선호텔 리뉴얼', '김과장', '외함 400*700*90 규격 확정 회신 받기', '확인/진행', '', '할 일 모음 12행', '', '', ''],
      [true, false, '260901', '전북연수원', '', '끝난 일', '', '', '할 일 모음 3행', 2, '260904', '260905'],
      [false, true, '260910', 'SK하이닉스', '배팀장', '2차공사 ZONE4·5·6 속판 제작 작업의뢰서 결재', '작업의뢰서', '', '반영모음 40행', 1, '260904', '']
    ]),
    '0.브리지 자가진단': mkSheet('0.브리지 자가진단', [['일시', '항목', '결과'], ['260906', '스냅샷', '정상'], ['260907', 'CH 번호 중복', '★ CH-12 두 번']])
  });
  sheets[KM.RADAR_SHEET_ID] = mkSS(KM.RADAR_SHEET_ID, {
    '조사노트': mkSheet('조사노트', [
      ['판정', '출처', '분류', '허가일', '허가구분', '시군구', '대지위치', '건물명', '주용도', '연면적㎡', '연면적평', '객실추정', '조사 내용', '다음 행동'],
      ['★최우선', '허가데이터', '숙박', '2026-08-30', '신축', '강원 양양군', '양양읍 조산리 1-2', '(가칭)양양 오션리조트', '숙박시설', 12500, 3781, '약 200실', '…', '양양군청 건축과에 건축주·설계사 확인'],
      ['△검토', '허가데이터', '기타', '2026-08-28', '증축', '서울 종로구', '…', '…', '운동시설', 1200, 363, '', '', ''],
      ['★최우선', '뉴스·공고', '숙박', '', '신축', '부산 해운대구', '우동 1500', '해운대 호텔 신축', '숙박시설', 8000, 2420, '약 130실', '', '시공사 확인']
    ]),
    '로그': mkSheet('로그', [['시각', '호출', '신규', '실패'], [new Date(2026, 8, 7, 4, 0), 180, 3, 0]])
  });
  props.CONFIG_SHEET_ID = 'CFG';
  sheets.CFG = mkSS('CFG', {
    '설정': mkSheet('설정', [['항목', '값', '설명']].concat(DEFAULT_SETTINGS.map(r => r.slice())).concat([['KAKAO_REST_KEY', 'RESTKEY', ''], ['KAKAO_CLIENT_SECRET', '', ''], ['WEBAPP_URL', 'https://script.google.com/macros/s/X/exec', '']])),
    '추가출처': mkSheet('추가출처', [SOURCE_HEADERS.slice()].concat(SOURCE_EXAMPLES.map(r => r.slice()))),
    '발송로그': mkSheet('발송로그', [['시각', '종류', '성공', '글자수', '내용/오류']])
  });
  props.KAKAO_ACCESS_TOKEN = 'AT1'; props.KAKAO_ACCESS_EXP = String(FIXED_NOW + 3600e3); props.KAKAO_REFRESH_TOKEN = 'RT1';
}

// ─── 검사 도우미 ───
let pass = 0, fail = 0;
const setCfg = (k, v) => { sheets.CFG._tabs['설정']._data.find(r => r[0] === k)[1] = v; clearSettingsCache_(); };
function check(name, cond, extra) { if (cond) { pass++; console.log('  ✔ ' + name); } else { fail++; console.log('  ✘ ' + name + (extra ? ' — ' + extra : '')); } }
const kapiCalls = () => fetchLog.filter(f => f.url.indexOf('kapi') >= 0);
const sentTexts = () => kapiCalls().map(f => JSON.parse(f.opt.payload.template_object).text);

// ═══ 1. 날짜 파서 ═══
console.log('\n[1] parseDate_');
seed();
const P = v => { const d = parseDate_(v); return d ? Utilities.formatDate(d, '', 'yyyy-MM-dd') : null; };
check("'260904' → 2026-09-04", P('260904') === '2026-09-04');
check("'260904(예정) 문구' → 2026-09-04", P('260904(예정) 외함 회신') === '2026-09-04');
check("'2026-09-04' → 2026-09-04", P('2026-09-04') === '2026-09-04');
check("'2026.9.4' → 2026-09-04", P('2026.9.4') === '2026-09-04');
check("'9/4' → 올해 9-04", P('9/4') === '2026-09-04');
check("'9월 4일' → 2026-09-04", P('9월 4일') === '2026-09-04');
check('Date 객체 → 자정', P(new Date(2026, 8, 4, 15, 0)) === '2026-09-04');
check('숫자 260904 → 2026-09-04', P(260904) === '2026-09-04');
check("'261340'(없는 달) → null", P('261340') === null);
check("'외함 회신'(글자) → null", P('외함 회신') === null);
check("'' → null / null → null", P('') === null && P(null) === null);
check("'260907 (이어짐)' → 2026-09-07", P('260907 (이어짐)') === '2026-09-07');

// ═══ 2. 200자 분할 ═══
console.log('\n[2] chunkText_');
const long = Array.from({ length: 12 }, (_, i) => '· [현장' + i + '] 이것은 마흔 글자 정도 되는 할 일 내용입니다 확인 회신 필요 (D-' + i + ')').join('\n');
const ch = chunkText_(long, KM.CHUNK_MAX);
check('모든 조각 ≤ 190자', ch.every(c => c.length <= 190), ch.map(c => c.length).join(','));
check('조각 수 > 1 (' + ch.length + ')', ch.length > 1);
check('내용 유실 없음', ch.join('\n').replace(/\s/g, '') === long.replace(/\s/g, ''));
const oneLine = 'x'.repeat(450);
check('한 줄 450자 → 190/190/70', JSON.stringify(chunkText_(oneLine, 190).map(c => c.length)) === '[190,190,70]');
check("빈 문자열 → ['']", JSON.stringify(chunkText_('', 190)) === '[""]');

// ═══ 3. 아침 브리핑 ═══
console.log('\n[3] morningBrief (월요일 07:30)');
seed(); calEvents[7] = [{ t: '조선호텔 현장회의', h: 10 }, { t: '[완료] 끝난 회의', h: 14 }, { t: '유한대 방문', all: true }];
const m = buildBriefMessages_('morning', new Date(NOW));
const kinds = m.map(x => x.kind);
check('메시지 3종 (mustdo, dday, calendar)', JSON.stringify(kinds) === '["mustdo","dday","calendar"]', kinds.join(','));
const md = m.find(x => x.kind === 'mustdo');
check('무조건할일: 완료행 제외 → 2건', /무조건할일 2건/.test(md.text), md.text);
check('무조건할일: ★행이 첫 줄', md.text.split('\n')[1].startsWith('★ [SK하이닉스]'), md.text.split('\n')[1]);
check('무조건할일: 링크 = gid 1213919957', md.link.indexOf('gid=1213919957') > 0);
const dd = m.find(x => x.kind === 'dday');
check('D-day: 지남1 · 오늘1 · 3일내1', /지남 1 · 오늘 1 · 3일 내 1/.test(dd.text), dd.text);
check('D-day: 완료행·D-13 제외', dd.text.indexOf('전북연수원') < 0 && dd.text.indexOf('청담PJ') < 0);
check('D-day: 순서 D+2 → D-day → D-2', /D\+2[\s\S]*D-day[\s\S]*D-2/.test(dd.text), dd.text);
const cal = m.find(x => x.kind === 'calendar');
check('캘린더: [완료] 제외 → 2건, 종일 표시', /일정 2건/.test(cal.text) && /종일 유한대 방문/.test(cal.text) && /10:00 조선호텔/.test(cal.text), cal.text);
check('모든 메시지 ≤ 200자 (분할 전 확인용)', m.every(x => x.text.length <= 600));
const n = runBrief_('morning');
check('실제 전송 3건 (kapi 호출 3)', n === 3 && kapiCalls().length === 3, n + '/' + kapiCalls().length);
check('전송 본문 전부 ≤ 200자', sentTexts().every(t => t.length <= 200), sentTexts().map(t => t.length).join(','));
check('template_object.object_type=text + link 포함', kapiCalls().every(f => { const t = JSON.parse(f.opt.payload.template_object); return t.object_type === 'text' && t.link.web_url; }));
check('Authorization Bearer AT1 (만료 전 → 리프레시 안 함)', kapiCalls()[0].opt.headers.Authorization === 'Bearer AT1' && fetchLog.every(f => f.url.indexOf('kauth') < 0));
const jk = sheets[KM.MEETING_SHEET_ID].getSheetByName('0.무조건할일')._data;
check('무조건할일 J·K 갱신 (미완료 2행만: J=1,4 / K=260907)', jk[1][9] === 1 && jk[1][10] === '260907' && jk[3][9] === 2 && jk[3][10] === '260907' && jk[2][9] === 2, JSON.stringify([jk[1][9], jk[1][10], jk[2][9], jk[3][9], jk[3][10]]));
check('발송로그 3행 O', logRows.filter(r => r[2] === 'O' && String(r[1]).indexOf('morning:') === 0).length === 3);

// ═══ 4. 저녁 브리핑 ═══
console.log('\n[4] eveningBrief');
seed(); calEvents[8] = [{ t: '제천 워케이션 공정회의', h: 14 }];
const e = buildBriefMessages_('evening', new Date(NOW));
check('메시지 3종 (dday, mustdo, calendar)', JSON.stringify(e.map(x => x.kind)) === '["dday","mustdo","calendar"]', e.map(x => x.kind).join(','));
check('내일 마감: 지남1 · 오늘1 · 내일0', /지남 1 · 오늘 1 · 내일 0/.test(e[0].text), e[0].text);
check('미완료 무조건할일 2건 (★ 1)', /무조건할일 2건 \(★ 1\)/.test(e[1].text), e[1].text);
check('내일 일정 9/8(화) 1건', /내일 9\/8\(화\) 일정 1건/.test(e[2].text), e[2].text);

// ═══ 5. 빈 날 / 주말 ═══
console.log('\n[5] 빈 날·주말');
seed(); sheets[KM.MEETING_SHEET_ID]._tabs['할 일 모음']._data.length = 2; sheets[KM.MEETING_SHEET_ID]._tabs['0.무조건할일']._data.length = 1;
const em = buildBriefMessages_('morning', new Date(NOW));
check('아무것도 없으면 🟢 1건', em.length === 1 && em[0].kind === 'empty' && em[0].text.indexOf('🟢') === 0);
seed(); global.nowKST_ = () => new Date(2026, 8, 6, 7, 30); // 일요일
check('일요일 → 발송 0, 로그 "주말"', runBrief_('morning') === 0 && kapiCalls().length === 0 && logRows.some(r => /주말/.test(r[4])));
global.nowKST_ = () => new Date(NOW);

// ═══ 6. hourlyCheck: 레이더 ★ + 시스템 ═══
console.log('\n[6] hourlyCheck');
seed();
driveFiles = [{ getName: () => '오류_km_queue_2609070200.json', getLastUpdated: () => new Date(FIXED_NOW - 3600e3) }, { getName: () => '완료_km_queue.json', getLastUpdated: () => new Date(FIXED_NOW - 3600e3) }, { getName: () => '오류_옛날.json', getLastUpdated: () => new Date(FIXED_NOW - 50 * 3600e3) }];
let s1 = hourlyCheck();
let texts = sentTexts();
check('1회차: 레이더 1건 + 시스템 1건 전송', s1 === 2 && texts.length === 2, s1 + ' ' + texts.length);
check('레이더: ★ 2건, △ 제외, 다음 행동 포함', /★최우선 2건/.test(texts[0]) && texts[0].indexOf('종로구') < 0 && /→ 양양군청/.test(texts[0]), texts[0]);
check('시스템: 오류_ 1개(24h) + 자가진단 ★ 1건, 옛 파일 제외', /오류_ 파일 1개/.test(texts[1]) && /자가진단 ★경고 1건/.test(texts[1]) && texts[1].indexOf('옛날') < 0 && texts[1].indexOf('레이더') < 0, texts[1]);
check('레이더 링크 = 레이더 시트', kapiCalls()[0].opt.payload.template_object.indexOf(KM.RADAR_SHEET_ID) > 0);
fetchLog = [];
let s2 = hourlyCheck();
check('2회차 (같은 시간대): 재전송 0', s2 === 0 && kapiCalls().length === 0, s2);
// 레이더 미수집: 로그 48시간 전
sheets[KM.RADAR_SHEET_ID]._tabs['로그']._data[1][0] = new Date(FIXED_NOW - 48 * 3600e3); fetchLog = [];
let s3 = hourlyCheck();
check('레이더 48h 미수집 → 새 경고 1건', s3 === 1 && /레이더 마지막 수집/.test(sentTexts()[0]) && /36시간/.test(sentTexts()[0]), sentTexts()[0]);
// 조사노트에 판정 열이 없으면 조용히 로그
sheets[KM.RADAR_SHEET_ID]._tabs['조사노트']._data[0][0] = '등급'; fetchLog = []; props.SEEN_radar = '{}';
check('판정 열 없음 → 전송 0 + 로그 X', hourlyCheck() === 0 && logRows.some(r => /판정 열 없음/.test(r[4])));

// ═══ 7. 고장 경로: 토큰·전송 실패 ═══
console.log('\n[7] 고장 경로');
seed(); props.KAKAO_ACCESS_EXP = String(FIXED_NOW - 1); // 만료
testSend();
check('만료 토큰 → kauth refresh 1회 후 새 토큰으로 전송', fetchLog[0].url.indexOf('kauth') >= 0 && fetchLog[0].opt.payload.grant_type === 'refresh_token' && fetchLog[0].opt.payload.refresh_token === 'RT1' && kapiCalls()[0].opt.headers.Authorization === 'Bearer AT2' && props.KAKAO_REFRESH_TOKEN === 'RT2');
seed(); delete props.KAKAO_ACCESS_TOKEN; delete props.KAKAO_REFRESH_TOKEN;
let threw = null; try { testSend(); } catch (err) { threw = String(err); }
check('토큰 전무 → 예외 "카카오 인증 안 됨" + 이메일 대체 1통', /인증 안 됨/.test(threw) && mailLog.length === 1 && /카카오 전송 실패/.test(mailLog[0].sub), threw);
seed(); kapi.status = 401; kapi.body = '{"code":-401,"msg":"this access token does not exist"}';
threw = null; try { runBrief_('morning'); } catch (err) { threw = err; }
check('kapi 401 → runBrief_는 예외 없이 끝남, 로그 X 2행(캘린더 없음), 메일 대체 2통', threw === null && logRows.filter(r => r[2] === 'X' && /kapi 401/.test(r[4])).length === 2 && mailLog.length === 2, threw + ' ' + mailLog.length);
kapi.status = 200; kapi.body = '{"result_code":0}';
seed(); kauth.status = 400; kauth.body = '{"error":"invalid_grant"}'; props.KAKAO_ACCESS_EXP = '0';
threw = null; try { testSend(); } catch (err) { threw = String(err); }
check('리프레시 실패(invalid_grant) → 예외 + 메일 대체', /kauth 400/.test(threw) && mailLog.length === 1, threw);
kauth.status = 200; kauth.body = JSON.stringify({ access_token: 'AT2', expires_in: 21600, refresh_token: 'RT2', refresh_token_expires_in: 5184000 });
seed(); threw = null; try { sendKakaoOne_('x'.repeat(201)); } catch (err) { threw = String(err); }
check('201자 직접 전송 → 차단', /200자 초과/.test(threw));
seed(); delete sheets[KM.MEETING_SHEET_ID];
const broken = buildBriefMessages_('morning', new Date(NOW));
check('회의록 시트 못 열어도 브리핑은 🟢/빈 상태로 조립되고 로그에 X', broken.length >= 1 && logRows.some(r => r[2] === 'X' && /no sheet/.test(r[4])));
seed(); props.KAKAO_ACCESS_EXP = String(FIXED_NOW + 3600e3);
kauth.body = JSON.stringify({ access_token: 'AT3', expires_in: 21600 }); props.KAKAO_ACCESS_EXP = '0';
testSend();
check('갱신 응답에 refresh_token 없으면 기존 RT1 유지', props.KAKAO_REFRESH_TOKEN === 'RT1' && props.KAKAO_ACCESS_TOKEN === 'AT3');

// ═══ 8. 추가출처 (역산표) ═══
console.log('\n[8] 추가출처');
seed();
sheets.EXTRA = mkSS('EXTRA', { '역산': mkSheet('역산', [['공정', '마감', '현장', '', '', '상태'], ['속판 작업의뢰서 발행', '260908', '목포 선샤인', '', '', ''], ['외함 납품', '260901', '목포 선샤인', '', '', '완료'], ['기구물 제작', '2026-10-30', '목포 선샤인', '', '', '']]) });
sheets.CFG._tabs['추가출처']._data[1] = ['현장 역산표', 'EXTRA', '역산', '1', 'B', 'A', 'C', 'F', '완료', 'Y'];
const ex = readExtraSources_();
check('역산표: 완료 제외 → 2건, 현장·제목 매핑', ex.length === 2 && ex[0].task === '속판 작업의뢰서 발행' && ex[0].site === '목포 선샤인', JSON.stringify(ex));
const m8 = buildBriefMessages_('morning', new Date(NOW));
check('D-day에 〈현장 역산표〉 D-1 포함, 10/30은 제외', /D-1 \[목포 선샤인\] 속판 작업의뢰서 발행 〈현장 역산표〉/.test(m8[1].text) && m8[1].text.indexOf('기구물') < 0, m8[1].text);
sheets.CFG._tabs['추가출처']._data[1][1] = 'NOPE';
check('없는 시트 ID → 건너뛰고 로그 X', readExtraSources_().length === 0 && logRows.some(r => /extra:현장 역산표/.test(r[1]) && r[2] === 'X'));

// ═══ 9. doGet 인증 흐름 ═══
console.log('\n[9] doGet');
kauth.body = JSON.stringify({ access_token: 'AT2', expires_in: 21600, refresh_token: 'RT2', refresh_token_expires_in: 5184000 });
seed(); delete props.KAKAO_ACCESS_TOKEN; delete props.KAKAO_REFRESH_TOKEN;
let pg = doGet({ parameter: {} });
check('코드 없음 → 인증 시작 버튼 + scope=talk_message + redirect_uri', /kauth\.kakao\.com\/oauth\/authorize/.test(pg._h) && /scope=talk_message/.test(pg._h) && /redirect_uri=https%3A%2F%2Fscript/.test(pg._h));
const st1 = (pg._h.match(/state=([a-z0-9-]+)/) || [])[1];
check('state 발급·저장', !!st1 && props.KAKAO_OAUTH_STATE.indexOf(st1 + '|') === 0);
pg = doGet({ parameter: { code: 'ABC' } });
check('state 없는 콜백 → 거부, 토큰 교환 없음', /만료됐거나 올바르지/.test(pg._h) && fetchLog.length === 0);
pg = doGet({ parameter: { code: 'ABC', state: 'WRONG' } });
check('state 틀린 콜백 → 거부', /만료됐거나 올바르지/.test(pg._h) && fetchLog.length === 0);
pg = doGet({ parameter: {} }); const st2 = (pg._h.match(/state=([a-z0-9-]+)/) || [])[1];
pg = doGet({ parameter: { code: 'ABC', state: st2 } });
check('올바른 state → 토큰 교환 + user/me로 소유자 111 저장 + 확인 메시지 1건 + state 소거', fetchLog[0].opt.payload.grant_type === 'authorization_code' && fetchLog[0].opt.payload.code === 'ABC' && props.KAKAO_REFRESH_TOKEN === 'RT2' && props.KAKAO_OWNER_ID === '111' && /연결 완료/.test(pg._h) && kapiCalls().filter(f => /memo/.test(f.url)).length === 1 && !props.KAKAO_OAUTH_STATE, pg._h);
pg = doGet({ parameter: {} }); const st3 = (pg._h.match(/state=([a-z0-9-]+)/) || [])[1];
userMe.body = '{"id":999}'; props.KAKAO_REFRESH_TOKEN = 'RT2'; fetchLog = [];
pg = doGet({ parameter: { code: 'EVIL', state: st3 } });
check('다른 카카오 계정(999) → 거부, 기존 토큰 RT2 유지', /등록된 카카오 계정이 아닙니다/.test(pg._h) && props.KAKAO_REFRESH_TOKEN === 'RT2' && props.KAKAO_OWNER_ID === '111');
userMe.body = '{"id":111}';
pg = doGet({ parameter: {} }); const st4 = (pg._h.match(/state=([a-z0-9-]+)/) || [])[1];
props.KAKAO_OAUTH_STATE = st4 + '|' + (FIXED_NOW - 11 * 60 * 1000); fetchLog = [];
check('10분 지난 state → 거부', /만료됐거나 올바르지/.test(doGet({ parameter: { code: 'ABC', state: st4 } })._h) && fetchLog.length === 0);
// PIN
sheets.CFG._tabs['설정']._data.push(['AUTH_PIN', '246810', '']); clearSettingsCache_();
pg = doGet({ parameter: {} });
check('PIN 설정 시 pin 없이 열면 링크 없음', /AUTH_PIN/.test(pg._h) && pg._h.indexOf('kauth.kakao.com') < 0);
pg = doGet({ parameter: { pin: '000000' } });
check('틀린 pin → 링크 없음', pg._h.indexOf('kauth.kakao.com') < 0);
pg = doGet({ parameter: { pin: '246810' } });
check('맞는 pin → 인증 링크', pg._h.indexOf('kauth.kakao.com') > 0);
pg = doGet({ parameter: { error: 'access_denied', error_description: 'user cancel' } });
check('사용자 취소 → 실패 페이지, 전송 없음', /인증 실패/.test(pg._h));
setCfg('KAKAO_REST_KEY', '');
pg = doGet({ parameter: {} });
check('REST 키 비어 있으면 안내만', /KAKAO_REST_KEY/.test(pg._h));

// ═══ 10. 유틸 ═══
console.log('\n[10] 유틸');
check("parseHHMM_('07:30')", JSON.stringify(parseHHMM_('07:30')) === '{"h":7,"m":30}');
check("parseHHMM_('18시')", JSON.stringify(parseHHMM_('18시')) === '{"h":18,"m":0}');
check("colIdx_ A=0, F=5, AB=27, '3'=2, ''=-1", colIdx_('A') === 0 && colIdx_('F') === 5 && colIdx_('AB') === 27 && colIdx_('3') === 2 && colIdx_('') === -1);
check("dday_ 오늘/D-2/D+3", dday_(NOW, NOW) === 'D-day' && dday_(NOW, addDays_(NOW, 2)) === 'D-2' && dday_(NOW, addDays_(NOW, -3)) === 'D+3');
check('markSeen_ 450개 → 저장 문자열 6000자 이하로 오래된 키 정리, 최근 키는 유지', (() => { seed(); markSeen_('t', Array.from({ length: 450 }, (_, i) => 'k' + i)); return props.SEEN_t.length <= 6000 && Object.keys(getSeen_('t')).length >= 200; })());

// ═══ 11. 주말 검토판 ═══
console.log('\n[11] weekendReview');
seed();
const SAT = new Date(2026, 8, 5, 9, 0); // 토요일 → 다음 주 월 9/7~일 9/13
global.nowKST_ = () => new Date(SAT);
calEvents[7] = [{ t: '조선호텔 현장회의', h: 10 }]; calEvents[10] = [{ t: '유한대 기구물 설치 확인', all: true }];
props.SEEN_radar = JSON.stringify({ '양양읍 조산리 1-2|(가칭)양양 오션리조트': '260903' });
props.SEEN_sys = JSON.stringify({ 'err-file|260902': '260902', 'old|260801': '260801' });
props.KAKAO_REFRESH_EXP = String(new Date(2026, 10, 1).getTime());
sheets.CFG._tabs['발송로그']._data.push(['2026-09-01 07:30:00', 'morning:mustdo', 'O', 120, ''], ['2026-09-03 18:00:00', 'evening:dday', 'X', 100, 'kapi 401'], ['2026-08-20 07:30:00', 'morning:dday', 'X', 100, '옛날']);
const wk = buildWeekendMessages_(new Date(SAT));
const wkinds = wk.map(x => x.kind);
check('메시지 5종 (todo-all, mustdo-all, calendar-week, radar-week, health)', JSON.stringify(wkinds) === '["todo-all","mustdo-all","calendar-week","radar-week","health"]', wkinds.join(','));
const ta = wk[0].text;
check('미완료 전체 4건 (완료 제외), 기한 분류: 지남0·이번주1·다음주2·그뒤1·기한없음0', /전체 4건/.test(ta) && /지남 0 · 이번 주 1 · 다음 주 2 · 그 뒤 1 · 기한없음 0/.test(ta), ta);
check('현장별 ■ 묶음, 청담PJ(D-15)도 포함', /■ 조선호텔 리뉴얼 1건/.test(ta) && /■ 청담PJ 1건/.test(ta) && /D-15/.test(ta), ta);
check('현장 순서 = 가장 이른 기한 순 (조선호텔 → 유한대 → 제천 → 청담)', ta.indexOf('■ 조선호텔') < ta.indexOf('■ 유한대') && ta.indexOf('■ 유한대') < ta.indexOf('■ 제천') && ta.indexOf('■ 제천') < ta.indexOf('■ 청담'));
check('담당자 —김과장 표시', /—김과장/.test(ta));
const ma = wk[1].text;
check('무조건할일 상세: 담당·구분·알림횟수 포함, ★ 먼저', /★ \[SK하이닉스\][^\n]*—배팀장 \/작업의뢰서 알림1회/.test(ma) && ma.indexOf('★') < ma.indexOf('· [조선호텔'), ma);
const ca = wk[2].text;
check('다음 주 일정 2건, 9/7(월)·9/10(목) 날짜별', /다음 주 일정 2건 \(9\/7\(월\)~9\/13\(일\)\)/.test(ca) && /▸ 9\/7\(월\)\n 10:00 조선호텔/.test(ca) && /▸ 9\/10\(목\)\n 종일 유한대/.test(ca), ca);
const ra = wk[3].text;
check('신규 현장: ★ 2 · △ 1, 이번 주 발견 🆕 표시(양양만)', /★ 2건 · △검토 1건/.test(ra) && /양양 오션리조트[^\n]*🆕/.test(ra) && !/해운대 호텔 신축[^\n]*🆕/.test(ra), ra);
const ha = wk[4].text;
check('시스템 상태: 성공1/실패1(7일 내만), 경고 1건(7일 내만), 레이더 수집시각, 인증 만료 11/1', /성공 1 \/ 실패 1 \(evening:dday 1\)/.test(ha) && /시스템 경고 1건/.test(ha) && /레이더 마지막 수집 9\/7 04:00/.test(ha) && /인증 만료 11\/1/.test(ha), ha);
check('현재 경고: 자가진단 ★(260907)만 → ⚠ 1줄', (ha.match(/⚠/g) || []).length === 1 && /자가진단 ★경고/.test(ha), ha);
const wn = weekendReview();
check('토요일 실제 전송 ≥ 5건, 전부 ≤ 200자', wn >= 5 && sentTexts().every(t => t.length <= 200), wn + ' ' + sentTexts().map(t => t.length).join(','));
check('긴 메시지는 (1/n) 분할 접두어', sentTexts().some(t => /^\(1\/\d+\) /.test(t)));
fetchLog = []; global.nowKST_ = () => new Date(2026, 8, 7, 9, 0); // 월요일
check('월요일 → 검토판 0건, 로그 "대상 아님"', weekendReview() === 0 && kapiCalls().length === 0 && logRows.some(r => /대상 아님/.test(r[4])));
setCfg('주말 검토판 요일', '토'); fetchLog = []; global.nowKST_ = () => new Date(2026, 8, 6, 9, 0); // 일요일
check("요일 설정 '토' → 일요일 0건", weekendReview() === 0 && kapiCalls().length === 0);
setCfg('주말 검토판 발송', 'N'); global.nowKST_ = () => new Date(SAT); fetchLog = [];
check('발송 N → 토요일도 0건', weekendReview() === 0 && kapiCalls().length === 0);
global.nowKST_ = () => new Date(NOW);
seed(); global.nowKST_ = () => new Date(SAT); sheets[KM.MEETING_SHEET_ID]._tabs['할 일 모음']._data.length = 2; sheets[KM.MEETING_SHEET_ID]._tabs['0.무조건할일']._data.length = 1; delete sheets[KM.RADAR_SHEET_ID];
const wk2 = buildWeekendMessages_(new Date(SAT));
check('할 일·레이더 없어도 health 1건은 나감', wk2.length === 1 && wk2[0].kind === 'health', wk2.map(x => x.kind).join(','));
global.nowKST_ = () => new Date(NOW);

// ═══ 12. 매시간 상황판 ═══
console.log('\n[12] hourlyPulse_');
seed(); const MON14 = new Date(2026, 8, 7, 14, 5); global.nowKST_ = () => new Date(MON14);
calEvents[7] = [{ t: '조선호텔 현장회의', h: 10 }, { t: '유한대 방문', h: 15 }, { t: '설계팀 회의', h: 17 }, { t: '[완료] 끝', h: 16 }];
props.SEEN_radar = JSON.stringify({ '양양읍 조산리 1-2|(가칭)양양 오션리조트': '260903', '우동 1500|해운대 호텔 신축': '260903' });
const pm = buildPulseMessage_(new Date(MON14));
check('상황판 ≤ 190자 한 장', pm.text.length <= 190, pm.text.length);
check('머리 🕐 14:05 상황 9/7(월)', /^🕐 14:05 상황 9\/7\(월\)/.test(pm.text), pm.text);
check('다음 일정 = 15:00 유한대 방문 (이후 1건), [완료] 제외', /▸ 다음 일정: 15:00 유한대 방문 \(이후 1건\)/.test(pm.text), pm.text);
check('마감: 지남 1 · 오늘 1 · 임박 1 + 최대 3줄', /▸ 마감: 지남 1 · 오늘 1 · 임박 1/.test(pm.text) && /D\+2 \[조선호텔/.test(pm.text), pm.text);
check('무조건할일 미완료 2 (★1: 내용 앞부분) — 190자 맞추려 마감 줄 1개 뺌', /▸ 무조건할일 미완료 2 \(★1: 2차공사 ZONE4·5·6/.test(pm.text) && (pm.text.match(/\n D/g) || []).length === 2, pm.text);
const pulses = () => sentTexts().filter(t => /^🕐/.test(t)).length;
let hp = hourlyCheck();
check('14시 hourlyCheck → 상황판 1건 + 시스템(자가진단★) 1건, 레이더 0', hp === 2 && pulses() === 1 && sentTexts().some(t => /🚨/.test(t)), hp + ' ' + sentTexts().length);
fetchLog = [];
check("'보냄'(기본) → 같은 내용도 다음 시간 다시 보냄 (시스템은 중복 안 보냄)", hourlyCheck() === 1 && pulses() === 1);
setCfg('매시간 상황판 변화 없을 때', '생략'); fetchLog = [];
check("'생략' → 직전과 같으면 0건 + 로그", hourlyCheck() === 0 && logRows.some(r => /변화 없음/.test(r[4])));
calEvents[7].push({ t: '추가 통화', h: 20 }); fetchLog = [];
check("'생략'이라도 내용이 바뀌면 다시 보냄", hourlyCheck() === 1);
global.nowKST_ = () => new Date(2026, 8, 7, 22, 10); fetchLog = [];
check('22시 → 시간대(07-21) 밖 → 0', hourlyCheck() === 0);
global.nowKST_ = () => new Date(2026, 8, 7, 18, 20); fetchLog = [];
check('18시(저녁 브리핑 시각) → 상황판 건너뜀', hourlyCheck() === 0);
global.nowKST_ = () => new Date(2026, 8, 5, 14, 0); fetchLog = []; setCfg('매시간 상황판 변화 없을 때', '보냄');
hourlyCheck(); check('토요일 14시 (주말 Y) → 상황판 1건', pulses() === 1);
setCfg('매시간 상황판 주말', 'N'); fetchLog = [];
hourlyCheck(); check('토요일 (주말 N) → 상황판 0건', pulses() === 0);
setCfg('매시간 상황판', 'N'); global.nowKST_ = () => new Date(MON14); fetchLog = [];
hourlyCheck(); check('상황판 N → 평일 14시도 0건', pulses() === 0);
setCfg('매시간 상황판', 'Y'); calEvents[7] = []; fetchLog = [];
check('일정 없는 날 → "오늘 일정 없음"', /▸ 오늘 일정 없음/.test(buildPulseMessage_(new Date(MON14)).text));
global.nowKST_ = () => new Date(2026, 8, 7, 19, 0); calEvents[7] = [{ t: '조선호텔 현장회의', h: 10 }];
check('일정 다 지났으면 "오늘 일정 끝 (1건 완료)"', /▸ 오늘 일정 끝 \(1건 완료\)/.test(buildPulseMessage_(nowKST_()).text));
global.nowKST_ = () => new Date(NOW);

// ═══ 13. 감사 지적 반영 검사 ═══
console.log('\n[13] 감사 지적 반영');
seed(); setCfg('D-day 경고 일수', '0');
const m13 = buildBriefMessages_('morning', new Date(NOW));
check("'D-day 경고 일수'=0 → 임박 0건 (0이 기본값 3으로 바뀌지 않음)", /3일 내 0|0일 내 0/.test(m13[1].text) && m13[1].text.indexOf('제천') < 0, m13[1].text);
seed(); kapi.status = 401; kapi.body = '{"code":-401}';
runBrief_('morning');
const jk13 = sheets[KM.MEETING_SHEET_ID].getSheetByName('0.무조건할일')._data;
check('카카오 전부 실패 → 무조건할일 J·K 기록 안 함', jk13[1][9] === '' && jk13[1][10] === '' && jk13[3][9] === 1, JSON.stringify([jk13[1][9], jk13[3][9]]));
kapi.status = 200; kapi.body = '{"result_code":0}';
seed();
markSeen_('big', Array.from({ length: 2000 }, (_, i) => '서울특별시 강남구 청담동 ' + i + '번지 어느 호텔 신축 공사 현장 건물명이 아주 긴 경우 ' + i));
const big = props.SEEN_big;
check('중복방지 저장 문자열 ≤ 6000자 (9KB 한도 안), 키는 8자리 해시', big.length <= 6000 && /^\{"[0-9a-f]{8}":"\d{6}"/.test(big), big.length);
check('해시 키로도 원문 조회 됨 (has)', !!getSeen_('big').has('서울특별시 강남구 청담동 1999번지 어느 호텔 신축 공사 현장 건물명이 아주 긴 경우 1999') && !getSeen_('big').has('없는 키'));
// 첫 설치 경로: 설정 시트 없음 → 생성
seed(); delete props.CONFIG_SHEET_ID; delete sheets.CFG; clearSettingsCache_();
const url13 = setup();
const cfg = sheets.CFG;
check('setup: 설정 시트 생성 + 탭 3개 (설정·추가출처·발송로그)', !!cfg && ['설정', '추가출처', '발송로그'].every(n => cfg.getSheetByName(n)) && props.CONFIG_SHEET_ID === 'CFG', url13);
const setRows = cfg.getSheetByName('설정')._data.map(r => (r || [])[0]);
check('설정 탭에 기본 항목 전부 + KAKAO_REST_KEY·WEBAPP_URL·AUTH_PIN(6자리)', DEFAULT_SETTINGS.every(d => setRows.indexOf(d[0]) >= 0) && ['KAKAO_REST_KEY', 'KAKAO_CLIENT_SECRET', 'WEBAPP_URL', 'AUTH_PIN'].every(k => setRows.indexOf(k) >= 0) && /^\d{6}$/.test(cfg.getSheetByName('설정')._data.find(r => r && r[0] === 'AUTH_PIN')[1]));
check('setup: 트리거 4개 (morning 7:30 / evening 18:00 / hourly / weekend 9:00)', triggers.length === 4 && triggers.map(t => t.getHandlerFunction()).sort().join(',') === 'eveningBrief,hourlyCheck,morningBrief,weekendReview' && triggers.find(t => t.getHandlerFunction() === 'morningBrief')._h === 7 && triggers.find(t => t.getHandlerFunction() === 'weekendReview')._h === 9, triggers.map(t => t.getHandlerFunction() + ':' + t._h).join(','));
installTriggers();
check('installTriggers 재실행해도 트리거는 4개 (중복 없음)', triggers.length === 4);
check('추가출처 탭 예시 2행 (사용 N)', cfg.getSheetByName('추가출처')._data.length === 3 && cfg.getSheetByName('추가출처')._data[1][9] === 'N');
seed(); kauth.status = 400; kauth.body = '{"error":"invalid_grant","error_description":"bad","access_token_leak":"SECRET"}'; props.KAKAO_ACCESS_EXP = '0';
let e13 = null; try { testSend(); } catch (err) { e13 = String(err); }
check('토큰 오류 메시지에 응답 원문(비밀값) 미포함', /kauth 400: invalid_grant bad/.test(e13) && e13.indexOf('SECRET') < 0, e13);
kauth.status = 200; kauth.body = JSON.stringify({ access_token: 'AT2', expires_in: 21600, refresh_token: 'RT2', refresh_token_expires_in: 5184000 });

console.log('\n결과: 통과 ' + pass + ' / 실패 ' + fail);
process.exit(fail ? 1 : 0);

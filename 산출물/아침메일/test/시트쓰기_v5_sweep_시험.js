// KM_시트쓰기 v5 sweep 자가시험 — 구글 시트를 흉내 낸 가짜로 실제 km_sweep_ 을 돌린다.
// node 산출물/아침메일/test/시트쓰기_v5_sweep_시험.js
const fs = require('fs');
const path = require('path');
let OK = 0; const NG = [];
const chk = (n, c, why = '') => c ? (OK++, console.log('  OK   ' + n))
                                   : (NG.push(n), console.log('  NG   ' + n + '  ' + why));

// ── 가짜 시트(값 배열 + 병합 기록) ─────────────────────────
function makeSheet(name, rows) {
  let grid = rows.map(r => r.slice());
  let merges = [];   // {row,col,numRows,numCols} — km_reMerge_ 가 부른 merge() 기록
  function range(row, col, numRows, numCols) {
    numRows = numRows || 1; numCols = numCols || 1;
    const self = {
      getValues: () => {
        const out = [];
        for (let i = 0; i < numRows; i++) {
          const g = grid[row - 1 + i] || [];
          const line = [];
          for (let j = 0; j < numCols; j++) line.push(g[col - 1 + j] !== undefined ? g[col - 1 + j] : '');
          out.push(line);
        }
        return out;
      },
      setValues: (vals) => {
        for (let i = 0; i < vals.length; i++) {
          const gi = row - 1 + i;
          while (grid.length <= gi) grid.push([]);
          for (let j = 0; j < vals[i].length; j++) grid[gi][col - 1 + j] = vals[i][j];
        }
        return self;
      },
      setValue: (v) => {
        while (grid.length <= row - 1) grid.push([]);
        grid[row - 1][col - 1] = v;
        return self;
      },
      clearContent: () => {
        for (let i = 0; i < numRows; i++) {
          const g = grid[row - 1 + i];
          if (g) for (let j = 0; j < numCols; j++) g[col - 1 + j] = '';
        }
        return self;
      },
      breakApart: () => { merges = merges.filter(m => !(m.row >= row && m.row < row + numRows)); return self; },
      merge: () => {
        merges.push({ row, col, numRows, numCols });
        // 실제 구글시트처럼 왼쪽 위 칸만 남기고 나머지는 비운다
        for (let i = 1; i < numRows; i++) { const g = grid[row - 1 + i]; if (g) g[col - 1] = ''; }
        for (let j = 1; j < numCols; j++) { const g = grid[row - 1]; if (g) g[col - 1 + j] = ''; }
        return self;
      },
      setWrap: () => self, setVerticalAlignment: () => self, setFontWeight: () => self,
      setNumberFormat: () => self, setBackground: () => self,
    };
    return self;
  }
  const self2 = {
    getName: () => name,
    setName: (n) => { name = n; return self2; },
    getLastRow: () => grid.length,
    setFrozenRows: () => {},
    setColumnWidth: () => self2,
    clearContents: () => { grid = []; return self2; },
    getRange: (r, c, nr, nc) => range(r, c, nr, nc),
    deleteRows: (startRow, numRows) => { grid.splice(startRow - 1, numRows); },
    _grid: () => grid,
    _merges: () => merges,
  };
  return self2;
}

let SHEETS = {};
let TOASTS = [];
// 실제 구글시트 : openById 는 전체 권한(doPost 경로) · getActiveSpreadsheet 는 단순 트리거(onOpen)도 쓸 수 있는 제한 권한.
// 둘 다 같은 시트(SHEETS)를 가리키되, ssObj 자체는 매번 새로 만들어 "openById 를 쓰면 안 되는 onOpen 이 실수로 openById 를 쓰면" 잡아낼 수 있게 한다.
function ssObj(withToast) {
  var o = {
    getSheetByName: (n) => SHEETS[n] || null,
    insertSheet: (n) => { SHEETS[n] = makeSheet(n, []); return SHEETS[n]; },
    getSheets: () => { if (!SHEETS['__first__']) SHEETS['__first__'] = makeSheet('Sheet1', []); return [SHEETS['__first__']]; },
  };
  if (withToast) o.toast = (msg, title, sec) => TOASTS.push({ msg, title, sec });
  return o;
}
global.SpreadsheetApp = {
  openById: () => ssObj(false),
  getActiveSpreadsheet: () => ssObj(true),
};
global.Utilities = { formatDate: () => '2026-09-28' };
global.ContentService = { createTextOutput: (s) => ({ setMimeType: () => ({ text: s }) }), MimeType: { JSON: 'json' } };
global.KM_TOKEN = 'x';

eval(fs.readFileSync(path.join(__dirname, '..', 'KM_시트쓰기.gs'), 'utf8'));

// ── 시험 1 : 기본 분류(4갈래) + 세로 병합 이어채움 + 재병합 ──────
function setup1() {
  SHEETS = {};
  SHEETS['답요청'] = makeSheet('답요청', [
    ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
    ['2026-09-27', 'A현장', '할일1', '완료', '', '', 'A현장'],   // 완료 → 「완료 기록」
    ['', '', '할일2', '', '', '', 'A현장'],                      // 남음 (A·B 이어채움 필요)
    ['', 'B현장', '할일3', '', '답 결정', '', 'B현장'],           // 답 결정 → 「답 결정」
    ['', '', '할일3b', '', '아니야', '', 'B현장'],                // 아니야(v7) → 「삭제된 것」
    ['2026-09-28', 'C현장', '할일4', '', '', '', 'C현장'],        // 남음
    ['', 'C현장', '할일5', '완료', '', '', 'C현장'],               // 완료 → 「완료 기록」
    ['', 'C현장', '할일6', '', '제안서', '', 'C현장'],             // 제안서(v7) → 「만들 차례」
    ['', 'C현장', '할일7', '', '캘린더', '', 'C현장'],             // 캘린더(v9) → 「만들 차례」
  ]);
}

setup1();
let out = km_sweep_({ tabs: ['답요청'], dry: false });
let rec = out.tabs[0];
chk('분류 : 완료 2건', rec.완료 === 2, JSON.stringify(rec));
chk('분류 : 삭제(아니야) 1건 (v7)', rec.삭제 === 1, JSON.stringify(rec));
chk('분류 : 답 결정 1건', rec.답결정 === 1, JSON.stringify(rec));
chk('분류 : 만들차례(제안서+캘린더) 2건 (v9)', rec.만들차례 === 2, JSON.stringify(rec));
chk('분류 : 남김 2건', rec.남김 === 2, JSON.stringify(rec));
chk('분류 : 전체 8건', rec.전체 === 8, JSON.stringify(rec));

let g = SHEETS['답요청']._grid();
chk('원본 탭 남은 줄 수 = 헤더+2', g.length === 3, '실제 ' + g.length);
chk('할일2 가 남고 날짜가 이어채워짐(2026-09-27)', g[1][0] === '2026-09-27' && g[1][2] === '할일2', JSON.stringify(g[1]));
chk('할일4 가 남음(2026-09-28·C현장)', g[2][0] === '2026-09-28' && g[2][2] === '할일4', JSON.stringify(g[2]));

let done = SHEETS['완료 기록'];
let del = SHEETS['삭제된 것'];
let pick = SHEETS['답 결정'];
let make = SHEETS['만들 차례'];
chk('완료 기록 탭이 만들어짐', !!done, '');
chk('삭제된 것 탭이 만들어짐 (v7)', !!del, '');
chk('답 결정 탭이 만들어짐', !!pick, '');
chk('만들 차례 탭이 만들어짐 (v7)', !!make, '');
if (done) {
  let dg = done._grid();
  chk('완료 기록 : 머리줄+2건', dg.length === 3, '실제 ' + dg.length);
  chk('완료 기록 : 할일1 이 날짜·현장 채워져서 옮겨감', dg[1][0] === '2026-09-27' && dg[1][1] === 'A현장' && dg[1][2] === '할일1', JSON.stringify(dg[1]));
  chk('완료 기록 : 원본탭·처리일 칸(H·I)', dg[1][7] === '답요청' && dg[1][8] === '2026-09-28', JSON.stringify(dg[1]));
}
if (del) {
  let lg = del._grid();
  chk('삭제된 것 : 머리줄+1건 (v7)', lg.length === 2, '실제 ' + lg.length);
  chk('삭제된 것 : 할일3b 가 현장 채워져서 옮겨감 (v7)', lg[1][1] === 'B현장' && lg[1][2] === '할일3b', JSON.stringify(lg[1]));
}
if (pick) {
  let pg = pick._grid();
  chk('답 결정 : 머리줄+1건', pg.length === 2, '실제 ' + pg.length);
  chk('답 결정 : 할일3 이 현장 채워져서 옮겨감', pg[1][1] === 'B현장' && pg[1][2] === '할일3', JSON.stringify(pg[1]));
}
if (make) {
  let mkg = make._grid();
  chk('만들 차례 : 머리줄+2건 (v9)', mkg.length === 3, '실제 ' + mkg.length);
  chk('만들 차례 : 할일6 이 고르기=제안서 그대로 옮겨감 (v7)', mkg[1][1] === 'C현장' && mkg[1][2] === '할일6' && mkg[1][4] === '제안서', JSON.stringify(mkg[1]));
  chk('만들 차례 : 할일7 이 고르기=캘린더 그대로 옮겨감 (v9)', mkg[2][1] === 'C현장' && mkg[2][2] === '할일7' && mkg[2][4] === '캘린더', JSON.stringify(mkg[2]));
}
let mg = SHEETS['답요청']._merges();
chk('재병합 호출 있었음(남은 2줄은 날짜·현장이 서로 달라 병합 없음이 정상)', mg.length === 0, JSON.stringify(mg));

// ── 시험 1-1 (v7) : 완료 체크가 가장 세다 — E열이 뭐든 완료면 완료 기록으로만 간다 ──
SHEETS = {};
SHEETS['오늘 할일'] = makeSheet('오늘 할일', [
  ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
  ['2026-09-28', 'F현장', '완료+아니야', '완료', '아니야', '', 'F현장'],
  ['', 'F현장', '완료+답결정', '완료', '답 결정', '', 'F현장'],
  ['', 'F현장', '완료+제안서', '완료', '제안서', '', 'F현장'],
]);
let out11 = km_sweep_({ tabs: ['오늘 할일'], dry: true });
let rec11 = out11.tabs[0];
chk('완료 우선순위 (v7) : 3건 다 완료로만 잡힘', rec11.완료 === 3 && rec11.삭제 === 0 && rec11.답결정 === 0 && rec11.만들차례 === 0, JSON.stringify(rec11));

// ── 시험 2 : 남은 줄끼리 같은 날짜·같은 현장이면 다시 병합됨 ──
function setup2() {
  SHEETS = {};
  SHEETS['오늘 할일'] = makeSheet('오늘 할일', [
    ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
    ['2026-09-28', 'D현장', '할일A', '완료', '', '', 'D현장'],   // 지워짐
    ['', 'D현장', '할일B', '', '', '', 'D현장'],                 // 남음
    ['', 'D현장', '할일C', '', '', '', 'D현장'],                 // 남음 — B 와 같은 날짜·현장이라 다시 합쳐져야 함
  ]);
}
setup2();
let out2 = km_sweep_({ tabs: ['오늘 할일'], dry: false });
let mg2 = SHEETS['오늘 할일']._merges();
chk('남은 두 줄(같은 날짜·같은 현장)이 A·B 열 다시 병합됨(2건 : A열 1 + B열 1)', mg2.length === 2, JSON.stringify(mg2));
chk('A열 병합 범위 2행~3행', mg2.some(m => m.col === 1 && m.row === 2 && m.numRows === 2), JSON.stringify(mg2));
chk('B열 병합 범위 2행~3행', mg2.some(m => m.col === 2 && m.row === 2 && m.numRows === 2), JSON.stringify(mg2));

// ── 시험 3 : dry:true 는 아무것도 안 바꾼다 ──────────────────
setup1();
let before = JSON.stringify(SHEETS['답요청']._grid());
let out3 = km_sweep_({ tabs: ['답요청'], dry: true });
let after = JSON.stringify(SHEETS['답요청']._grid());
chk('dry:true 는 시트를 안 바꿈', before === after, '');
chk('dry:true 도 개수는 셈(완료 2·삭제 1·답결정 1·만들차례 2)',
    out3.tabs[0].완료 === 2 && out3.tabs[0].삭제 === 1 && out3.tabs[0].답결정 === 1 && out3.tabs[0].만들차례 === 2, JSON.stringify(out3.tabs[0]));
chk('dry:true 는 새 탭 4개(완료 기록·삭제된 것·답 결정·만들 차례) 다 안 만듦',
    !SHEETS['완료 기록'] && !SHEETS['삭제된 것'] && !SHEETS['답 결정'] && !SHEETS['만들 차례'], '');

// ── 시험 4 : 완료·답결정 없으면 그대로 둠 ────────────────────
SHEETS = {};
SHEETS['앞으로 할일'] = makeSheet('앞으로 할일', [
  ['기한', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
  ['2026-10-01', 'E현장', '할일X', '', '', '', 'E현장'],
]);
let out4 = km_sweep_({ tabs: ['앞으로 할일'], dry: false });
chk('완료·답결정 0건이면 남김 그대로', out4.tabs[0].남김 === 1 && out4.tabs[0].완료 === 0, JSON.stringify(out4.tabs[0]));

// ── 시험 5 : 실제 답요청 실 데이터(1097행, 완료 18건) 규모로도 오류 없이 도는지 ──
const real = JSON.parse(fs.readFileSync('/tmp/claude-0/-home-user-mic-pm/fe0bf48a-f114-506e-9732-df9f852b5e4a/scratchpad/sheet_now.json', 'utf8'));
const realRows = real.valueRanges[0].values;   // 답요청, 헤더 포함 1097행
SHEETS = {};
SHEETS['답요청'] = makeSheet('답요청', realRows);
let out5 = km_sweep_({ tabs: ['답요청'], dry: true });
chk('실제 데이터 dry 시험 : 완료 18건 그대로 나옴', out5.tabs[0].완료 === 18, JSON.stringify(out5.tabs[0]));
chk('실제 데이터 dry 시험 : 전체 1096행', out5.tabs[0].전체 === 1096, JSON.stringify(out5.tabs[0]));

// ── 시험 6 : onOpen (v6, 새로고침하면 자동 정리) ──────────────
setup1();
TOASTS = [];
onOpen({});
chk('onOpen : 새 탭 4개 다 만들어짐(기본값)', SHEETS['완료 기록'] && SHEETS['삭제된 것'] && SHEETS['답 결정'] && SHEETS['만들 차례'], '');
chk('onOpen : 완료 2·삭제 1·답결정 1·만들차례 2 실제로 옮겨짐',
    SHEETS['완료 기록']._grid().length === 3 && SHEETS['삭제된 것']._grid().length === 2 &&
    SHEETS['답 결정']._grid().length === 2 && SHEETS['만들 차례']._grid().length === 3, '');
chk('onOpen : 토스트로 알림(완료·삭제·답결정·만들차례 다 보임)',
    TOASTS.length === 1 && /완료 기록 2건/.test(TOASTS[0].msg) && /삭제 1건/.test(TOASTS[0].msg) &&
    /답 결정 1건/.test(TOASTS[0].msg) && /만들 차례 2건/.test(TOASTS[0].msg), JSON.stringify(TOASTS));

// 옮길 게 없으면 토스트 없음(조용히 넘어감)
SHEETS = {};
SHEETS['답요청'] = makeSheet('답요청', [
  ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
  ['2026-09-28', 'D현장', '할일X', '', '', '', 'D현장'],
]);
TOASTS = [];
onOpen({});
chk('onOpen : 옮길 게 없으면 토스트 안 띄움', TOASTS.length === 0, JSON.stringify(TOASTS));

// ── 시험 6-1 (재발 방지, 9/28 낮 실제로 겪은 오류) : onOpen 은 openById 를 절대 부르면 안 된다 ──
// 실제 구글시트에서 단순 트리거(onOpen)가 openById 를 부르면 "지정된 권한으로는 호출할 수 없습니다" 로 죽는다.
// 여기서 openById 를 부르는 순간 예외가 나게 만들어 두고, onOpen 이 그래도 정상 작동하면(=openById 를 안 썼으면) 통과.
setup1();
TOASTS = [];
const savedOpenById = SpreadsheetApp.openById;
SpreadsheetApp.openById = () => { throw new Error('지정된 권한으로는 SpreadsheetApp.openById을(를) 호출할 수 없습니다.'); };
let threwPerm = false;
try { onOpen({}); } catch (e) { threwPerm = true; }
chk('onOpen : openById 를 아예 안 써서 실제 권한 오류를 안 맞음', !threwPerm, '');
chk('onOpen : openById 가 막혀 있어도 sweep 은 정상 완료(토스트로 확인)', TOASTS.length === 1 && /완료 기록 2건/.test(TOASTS[0].msg), JSON.stringify(TOASTS));
SpreadsheetApp.openById = savedOpenById;

// doPost 경로(웹 앱 sweep 명령)는 여전히 openById 를 그대로 쓴다 — ss 를 안 넘기면 openById 로 연다
setup1();
let outDopost = km_sweep_({ tabs: ['답요청'], dry: false });   // ss 인자 없음 = doPost 가 부르는 모양 그대로
chk('doPost 경로(ss 인자 없음) : 여전히 openById 로 열어 정상 동작', outDopost.tabs[0].완료 === 2, JSON.stringify(outDopost.tabs[0]));

// 시트 자체에서 뭔가 진짜로 깨져도(오류) onOpen 은 밖으로 안 던지고 오류 토스트만 띄운다
setup1();
const savedGetSheetByName = SHEETS['답요청'].getSheetByName;
TOASTS = [];
let threw = false;
const brokenActive = { getSheetByName: () => { throw new Error('강제 오류'); }, insertSheet: () => { throw new Error('강제 오류'); }, toast: (msg, title, sec) => TOASTS.push({ msg, title, sec }) };
const savedGetActive = SpreadsheetApp.getActiveSpreadsheet;
SpreadsheetApp.getActiveSpreadsheet = () => brokenActive;
try { onOpen({}); } catch (e) { threw = true; }
chk('onOpen : 내부에서 오류가 나도 밖으로 안 던짐(시트 열기를 막지 않음)', !threw, '');
chk('onOpen : 오류면 오류 토스트라도 띄움', TOASTS.length === 1 && /오류/.test(TOASTS[0].msg), JSON.stringify(TOASTS));
SpreadsheetApp.getActiveSpreadsheet = savedGetActive;

// ── 시험 7 (v8) : 「만들 차례」 탭은 J열 「생성결과」 한 칸 더, 다른 새 탭은 9칸 그대로 ──
setup1();
km_sweep_({ tabs: ['답요청'], dry: false });
let makeHead = SHEETS['만들 차례']._grid()[0];
let doneHead = SHEETS['완료 기록']._grid()[0];
chk('만들 차례 : 머리줄 10칸(J=생성결과) (v8)', makeHead.length === 10 && makeHead[9] === '생성결과', makeHead);
chk('완료 기록 : 머리줄 9칸 그대로(J 없음)', doneHead.length === 9, doneHead);

// ── 시험 8 (v8) : markQueue — 지정한 줄 J열에만 쓰고 다른 칸은 안 건드림 ──
let mkOut = km_markQueue_({ tab: '만들 차례', marks: [{ row: 2, text: '만듦 · 작업의뢰서_대기_C현장_1.xlsx' }] });
chk('markQueue : n=1 반환', mkOut.ok && mkOut.n === 1, JSON.stringify(mkOut));
let mkGrid = SHEETS['만들 차례']._grid();
chk('markQueue : 2행 J열(10번째)에 적힘', mkGrid[1][9] === '만듦 · 작업의뢰서_대기_C현장_1.xlsx', mkGrid[1]);
chk('markQueue : 같은 줄의 다른 칸(할일)은 안 건드림', mkGrid[1][2] === '할일6', mkGrid[1]);
let mkNotFound = km_markQueue_({ tab: '없는탭', marks: [] });
chk('markQueue : 없는 탭이면 오류', mkNotFound.ok === false && /탭 없음/.test(mkNotFound.error), mkNotFound);

// ── 시험 9 (v9) : appendDoc — 메일·보고서 탭 새로 만들고 누적, 다른 탭 이름은 거절 ──
SHEETS = {};
let adOut1 = km_appendDoc_({ tab: '메일', rows: [['2026-09-28', '양양 쏠비치', '- 견적 재확인 메일 보내기', '안녕하십니까,\n\n견적 재확인 메일 보내기']] });
chk('appendDoc : 탭 없으면 새로 만들고 머리줄(날짜|현장|할일|본문)', SHEETS['메일'] && SHEETS['메일']._grid()[0].join('|') === '날짜|현장|할일|본문', SHEETS['메일'] && SHEETS['메일']._grid()[0]);
chk('appendDoc : ok:true · n=1 · firstRow=2', adOut1.ok && adOut1.n === 1 && adOut1.firstRow === 2, JSON.stringify(adOut1));
chk('appendDoc : 줄 내용 그대로 들어감(현장·할일·본문)', SHEETS['메일']._grid()[1][1] === '양양 쏠비치' && SHEETS['메일']._grid()[1][2] === '- 견적 재확인 메일 보내기', SHEETS['메일']._grid()[1]);

let adOut2 = km_appendDoc_({ tab: '메일', rows: [['2026-09-29', '단양디캠프', '- 다른 메일', '본문2']] });
chk('appendDoc : 두 번째 호출은 덮어쓰지 않고 이어붙임(날짜별 누적)', SHEETS['메일']._grid().length === 3 && SHEETS['메일']._grid()[2][1] === '단양디캠프', SHEETS['메일']._grid());

let adBad = km_appendDoc_({ tab: '아무탭', rows: [['x', 'x', 'x', 'x']] });
chk('appendDoc : 허용 안 된 탭 이름은 거절(메일·보고서만)', adBad.ok === false && /허용 안 된 탭/.test(adBad.error), adBad);
chk('appendDoc : 거절되면 탭을 만들지 않음', !SHEETS['아무탭'], '');

// appendDoc + markTab/marks 를 한 요청으로 — append 된 다음에만 「만들 차례」 J열도 같이 표시(원자적으로)
SHEETS['만들 차례'] = makeSheet('만들 차례', [
  ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)', '원본탭', '처리일', '생성결과'],
  ['2026-09-28', '단양디캠프', '- 보고서 쓰기', '', '보고서', '', '단양디캠프', '오늘 할일', '2026-09-28', ''],
]);
let adOut3 = km_appendDoc_({ tab: '보고서', rows: [['2026-09-28', '단양디캠프', '- 보고서 쓰기', '단양디캠프 보고\n\n일자 : 2026-09-28\n내용 : 보고서 쓰기']],
                             markTab: '만들 차례', marks: [{ row: 2, text: '만듦(시트) · 보고서 탭' }] });
chk('appendDoc + markTab/marks : ok:true · marked=1', adOut3.ok && adOut3.marked === 1, JSON.stringify(adOut3));
chk('appendDoc + markTab/marks : 「만들 차례」 J열에도 같이 표시됨', SHEETS['만들 차례']._grid()[1][9] === '만듦(시트) · 보고서 탭', SHEETS['만들 차례']._grid()[1]);
chk('appendDoc + markTab/marks : 보고서 탭에도 실제로 들어감', SHEETS['보고서'] && SHEETS['보고서']._grid()[1][3].indexOf('단양디캠프 보고') === 0, SHEETS['보고서'] && SHEETS['보고서']._grid()[1]);

let adNoMark = km_appendDoc_({ tab: '메일', rows: [['2026-09-28', 'x', 'x', 'x']], markTab: '없는탭', marks: [{ row: 2, text: 'x' }] });
chk('appendDoc : markTab 이 없는 탭이면 marked=0(오류로 죽지 않음, append 는 됨)', adNoMark.ok && adNoMark.marked === 0, JSON.stringify(adNoMark));

// ── 시험 10 (v10) : setHandover — 「KM 인수인계」 요약 1장, 누적 아니고 매번 덮어씀 ──
SHEETS = {};
let shOut1 = km_setHandover_({ rows: [['브랜치', 'claude/cowork-suggestions-bohllt'], ['최신 커밋', 'abc123 어떤 커밋'], ['안 한 것', '웹앱 v10 아직 안 붙임\n현장관리 캘린더 아직 없음']] });
chk('setHandover : ok:true · n=3', shOut1.ok && shOut1.n === 3, JSON.stringify(shOut1));
let hg1 = SHEETS['__first__']._grid();
chk('setHandover : 항목·내용 2칸으로 들어감', hg1[0][0] === '브랜치' && hg1[0][1] === 'claude/cowork-suggestions-bohllt', hg1[0]);
chk('setHandover : 줄바꿈 있는 칸도 그대로(지어내거나 자르지 않음)', hg1[2][1] === '웹앱 v10 아직 안 붙임\n현장관리 캘린더 아직 없음', hg1[2]);

let shOut2 = km_setHandover_({ rows: [['브랜치', '다시 씀']] });
let hg2 = SHEETS['__first__']._grid();
chk('setHandover : 두 번째 호출은 누적이 아니라 덮어씀(1줄만 남음)', hg2.length === 1 && hg2[0][1] === '다시 씀', hg2);

// ── 시험 11 (v11) : appendLog — 「대화 로그」 탭, 회의록처럼 덧붙이기(안 지움) + supersede 로 예전 줄만 상태 표시 ──
SHEETS = {};
let logOut1 = km_appendLog_({ row: ['2026-09-29', 'session-aaa1', '지시', 'A 는 이렇게 하기로 함', '유효'] });
chk('appendLog : ok:true · 2행(머리줄 다음)에 들어감', logOut1.ok && logOut1.row === 2, JSON.stringify(logOut1));
let lg1 = SHEETS['대화 로그']._grid();
chk('appendLog : 머리줄 5칸(날짜|창|종류|내용|상태)', lg1[0].join('|') === '날짜|창|종류|내용|상태', lg1[0]);
chk('appendLog : 1번째 로그 줄 값 그대로', lg1[1].join('|') === '2026-09-29|session-aaa1|지시|A 는 이렇게 하기로 함|유효', lg1[1]);

let logOut2 = km_appendLog_({ row: ['2026-09-30', 'session-bbb2', '변경', 'A 대신 B 로 바꾸기로 함(차장님 확인)', '유효'], supersede: { row: 2, note: 'A→B 로 바뀜' } });
let lg2 = SHEETS['대화 로그']._grid();
chk('appendLog : 두 번째 호출은 누적(1행이 아니라 2행 남음, 안 지움)', lg2.length === 3, lg2);
chk('appendLog : supersede 는 예전 줄(2행) 상태만 고침, 내용은 그대로 남음', lg2[1][3] === 'A 는 이렇게 하기로 함' && lg2[1][4] === '대체됨→3행 (A→B 로 바뀜)', lg2[1]);
chk('appendLog : 새 줄(3행)은 유효 그대로', lg2[2][4] === '유효', lg2[2]);

let logOut3 = km_appendLog_({ row: ['2026-10-01', 'session-ccc3', '메모', '세 번째 줄', '유효'] });
let lg3 = SHEETS['대화 로그']._grid();
chk('appendLog : 세 번째 호출도 계속 누적(4행)', lg3.length === 4 && logOut3.row === 4, lg3);

console.log('\n합계 ' + (OK + NG.length) + '개 중 통과 ' + OK + ' · 실패 ' + NG.length);
if (NG.length) { console.log('실패 : ' + NG.join(', ')); process.exit(1); }

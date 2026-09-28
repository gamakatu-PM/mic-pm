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
  return {
    getName: () => name,
    getLastRow: () => grid.length,
    setFrozenRows: () => {},
    getRange: (r, c, nr, nc) => range(r, c, nr, nc),
    deleteRows: (startRow, numRows) => { grid.splice(startRow - 1, numRows); },
    _grid: () => grid,
    _merges: () => merges,
  };
}

let SHEETS = {};
let TOASTS = [];
global.SpreadsheetApp = {
  openById: () => ({
    getSheetByName: (n) => SHEETS[n] || null,
    insertSheet: (n) => { SHEETS[n] = makeSheet(n, []); return SHEETS[n]; },
  }),
  getActiveSpreadsheet: () => ({ toast: (msg, title, sec) => TOASTS.push({ msg, title, sec }) }),
};
global.Utilities = { formatDate: () => '2026-09-28' };
global.ContentService = { createTextOutput: (s) => ({ setMimeType: () => ({ text: s }) }), MimeType: { JSON: 'json' } };
global.KM_TOKEN = 'x';

eval(fs.readFileSync(path.join(__dirname, '..', 'KM_시트쓰기.gs'), 'utf8'));

// ── 시험 1 : 기본 분류 + 세로 병합 이어채움 + 재병합 ──────────
function setup1() {
  SHEETS = {};
  SHEETS['답요청'] = makeSheet('답요청', [
    ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
    ['2026-09-27', 'A현장', '할일1', '완료', '', '', 'A현장'],   // 완료 → 지워짐
    ['', '', '할일2', '', '', '', 'A현장'],                      // 남음 (A·B 이어채움 필요)
    ['', 'B현장', '할일3', '', '답 결정', '', 'B현장'],           // 답 결정 → 지워짐
    ['2026-09-28', 'C현장', '할일4', '', '', '', 'C현장'],        // 남음
    ['', 'C현장', '할일5', '완료', '', '', 'C현장'],               // 완료 → 지워짐
  ]);
}

setup1();
let out = km_sweep_({ tabs: ['답요청'], dry: false });
let rec = out.tabs[0];
chk('분류 : 완료 2건', rec.완료 === 2, JSON.stringify(rec));
chk('분류 : 답 결정 1건', rec.답결정 === 1, JSON.stringify(rec));
chk('분류 : 남김 2건', rec.남김 === 2, JSON.stringify(rec));

let g = SHEETS['답요청']._grid();
chk('원본 탭 남은 줄 수 = 헤더+2', g.length === 3, '실제 ' + g.length);
chk('할일2 가 남고 날짜가 이어채워짐(2026-09-27)', g[1][0] === '2026-09-27' && g[1][2] === '할일2', JSON.stringify(g[1]));
chk('할일4 가 남음(2026-09-28·C현장)', g[2][0] === '2026-09-28' && g[2][2] === '할일4', JSON.stringify(g[2]));

let done = SHEETS['완료 기록'];
let pick = SHEETS['답 결정'];
chk('완료 기록 탭이 만들어짐', !!done, '');
chk('답 결정 탭이 만들어짐', !!pick, '');
if (done) {
  let dg = done._grid();
  chk('완료 기록 : 머리줄+2건', dg.length === 3, '실제 ' + dg.length);
  chk('완료 기록 : 할일1 이 날짜·현장 채워져서 옮겨감', dg[1][0] === '2026-09-27' && dg[1][1] === 'A현장' && dg[1][2] === '할일1', JSON.stringify(dg[1]));
  chk('완료 기록 : 원본탭·처리일 칸(H·I)', dg[1][7] === '답요청' && dg[1][8] === '2026-09-28', JSON.stringify(dg[1]));
}
if (pick) {
  let pg = pick._grid();
  chk('답 결정 : 머리줄+1건', pg.length === 2, '실제 ' + pg.length);
  chk('답 결정 : 할일3 이 현장 채워져서 옮겨감', pg[1][1] === 'B현장' && pg[1][2] === '할일3', JSON.stringify(pg[1]));
}
let mg = SHEETS['답요청']._merges();
chk('재병합 호출 있었음(남은 2줄은 날짜·현장이 서로 달라 병합 없음이 정상)', mg.length === 0, JSON.stringify(mg));

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
chk('dry:true 도 개수는 셈(완료 2·답결정 1)', out3.tabs[0].완료 === 2 && out3.tabs[0].답결정 === 1, JSON.stringify(out3.tabs[0]));
chk('dry:true 는 완료 기록·답 결정 탭도 안 만듦', !SHEETS['완료 기록'] && !SHEETS['답 결정'], '');

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
chk('onOpen : 답요청·오늘 할일·앞으로 할일 3탭 다 처리(기본값)', SHEETS['완료 기록'] && SHEETS['답 결정'], '');
chk('onOpen : 완료 2건·답결정 1건 실제로 옮겨짐', SHEETS['완료 기록']._grid().length === 3 && SHEETS['답 결정']._grid().length === 2, '');
chk('onOpen : 토스트로 알림(완료 2건·답 결정 1건)', TOASTS.length === 1 && /완료 기록 2건/.test(TOASTS[0].msg) && /답 결정 1건/.test(TOASTS[0].msg), JSON.stringify(TOASTS));

// 옮길 게 없으면 토스트 없음(조용히 넘어감)
SHEETS = {};
SHEETS['답요청'] = makeSheet('답요청', [
  ['날짜', '현장', '할일', '완료', '고르기', '메모', '현장(걸러보기)'],
  ['2026-09-28', 'D현장', '할일X', '', '', '', 'D현장'],
]);
TOASTS = [];
onOpen({});
chk('onOpen : 옮길 게 없으면 토스트 안 띄움', TOASTS.length === 0, JSON.stringify(TOASTS));

// 시트를 못 열어도(오류) onOpen 자체는 죽지 않는다
const savedOpenById = SpreadsheetApp.openById;
SpreadsheetApp.openById = () => { throw new Error('강제 오류'); };
TOASTS = [];
let threw = false;
try { onOpen({}); } catch (e) { threw = true; }
chk('onOpen : 내부에서 오류가 나도 밖으로 안 던짐(시트 열기를 막지 않음)', !threw, '');
chk('onOpen : 오류면 오류 토스트라도 띄움', TOASTS.length === 1 && /오류/.test(TOASTS[0].msg), JSON.stringify(TOASTS));
SpreadsheetApp.openById = savedOpenById;

console.log('\n합계 ' + (OK + NG.length) + '개 중 통과 ' + OK + ' · 실패 ' + NG.length);
if (NG.length) { console.log('실패 : ' + NG.join(', ')); process.exit(1); }

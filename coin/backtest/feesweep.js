// 파라미터를 고정하고 수수료만 바꾼다 — 수수료가 성적에 미치는 「순수한」 영향.
// 실행: node coin/backtest/feesweep.js
'use strict';
const path = require('path');
const { backtest, loadCsv } = require('./engine');
const { CATALOG } = require('./strategies');
const C = loadCsv(path.join(__dirname, 'data', 'ethusdt-1h.csv'));
const WARM = 320, SLIP = 2, LEV = 1;
const FIX = {                                   // 대표 파라미터 하나로 고정 (최적화 안 함)
  maCross:    { fast: 20, slow: 100 },
  donchian:   { n: 48 },
  trendBreak: { n: 48, trend: 200 },
  rsiRevert:  { n: 14, lo: 30, hi: 70 }
};
const FEES = [0, 2, 6, 10, 20, 40, 60];
const sl = { c: C, warm: WARM };

console.log('전 구간 2017-10~2020-05 · 파라미터 고정 · 슬리피지 ' + SLIP + 'bp · 레버리지 ' + LEV + '배');
console.log('(최적화를 하지 않았으므로 수수료 말고는 바뀌는 것이 없다)\n');
console.log('전략        거래수   ' + FEES.map(f => ((f / 100).toFixed(2) + '%').padStart(9)).join(''));
const rows = {};
for (const name of Object.keys(FIX)) {
  const line = []; let tr = 0;
  for (const f of FEES) {
    const r = backtest(sl.c, CATALOG[name].make(FIX[name])(sl.c), { feeBp: f, slipBp: SLIP, lev: LEV, equity0: 1000, warmup: WARM });
    tr = r.trades;
    line.push(r);
  }
  rows[name] = { trades: tr, line };
  console.log(name.padEnd(11) + String(tr).padStart(6) + '   ' +
    line.map(r => (((r.retPct >= 0 ? '+' : '') + r.retPct.toFixed(0)) + '%').padStart(9)).join(''));
}
console.log('\n── 수수료 0% 대비 얼마를 잃었나 (거래를 많이 할수록 크다) ──');
for (const name of Object.keys(FIX)) {
  const b = rows[name].line[0].retPct, t = rows[name].trades;
  const at40 = rows[name].line[FEES.indexOf(40)].retPct;
  console.log(name.padEnd(11) + '거래 ' + String(t).padStart(4) + '회 · 수수료 0% 일 때 ' +
    ((b >= 0 ? '+' : '') + b.toFixed(0) + '%').padStart(7) + ' → 편도 0.40% 일 때 ' +
    ((at40 >= 0 ? '+' : '') + at40.toFixed(0) + '%').padStart(7) +
    '  (' + (b - at40).toFixed(0) + '%p 증발)');
}

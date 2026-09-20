// 무작위 대조군 — 「같은 횟수로 아무렇게나 사고팔았을 때」의 성적 분포를 만든다.
// 전략 성적이 이 분포 안에 들어가면 그것은 실력이 아니라 그 시기의 시장 덕이다.
// 실행: node coin/backtest/montecarlo.js
'use strict';
const path = require('path');
const { backtest, loadCsv } = require('./engine');
const { CATALOG, expand } = require('./strategies');

const CANDLES = loadCsv(path.join(__dirname, 'data', 'ethusdt-1h.csv'));
const WARM = 320, IS = 24 * 30 * 8, OOS = 24 * 30 * 4, SLIP = 2, LEV = 1, MIN_TRADES = 10;
const FEES = [6, 40];
const SEEDS = 300;

function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function slice(from, to) { const s = Math.max(0, from - WARM); return { c: CANDLES.slice(s, to), warm: from - s }; }

const folds = [];
for (let start = WARM; start + IS + OOS <= CANDLES.length; start += OOS)
  folds.push({ isFrom: start, isTo: start + IS, oosFrom: start + IS, oosTo: start + IS + OOS });

// 무작위 신호: 매 봉 p 확률로 방향을 새로 뽑는다 (거래 횟수를 목표치에 맞추려고 p 를 조절)
function randomSignal(seed, p, allowShort) {
  const r = rng(seed);
  let state = 'FLAT';
  return () => {
    if (r() < p) { const x = r(); state = x < (allowShort ? 0.5 : 1) ? 'LONG' : 'SHORT'; }
    return state;
  };
}

console.log('무작위 대조군 ' + SEEDS + '회 · 워크포워드 ' + folds.length + '구간 · 레버리지 ' + LEV + '배\n');

for (const feeBp of FEES) {
  // 1) 실제 전략 성적 (run.js 와 같은 방식)
  const real = {};
  for (const name of Object.keys(CATALOG)) {
    if (name === 'buyHold') continue;
    const combos = expand(CATALOG[name].grid);
    let eq = 1000, tr = 0;
    for (const f of folds) {
      let best = null;
      for (const p of combos) {
        const sl = slice(f.isFrom, f.isTo);
        const r = backtest(sl.c, CATALOG[name].make(p)(sl.c), { feeBp, slipBp: SLIP, lev: LEV, equity0: 1000, warmup: sl.warm });
        if (r.trades < MIN_TRADES) continue;
        if (!best || r.retPct > best.r.retPct) best = { p, r };
      }
      if (!best) continue;
      const sl2 = slice(f.oosFrom, f.oosTo);
      const o = backtest(sl2.c, CATALOG[name].make(best.p)(sl2.c), { feeBp, slipBp: SLIP, lev: LEV, equity0: 1000, warmup: sl2.warm });
      eq *= (1 + o.retPct / 100); tr += o.trades;
    }
    real[name] = { ret: (eq / 1000 - 1) * 100, trades: tr };
  }

  // 2) 무작위 대조군 — 거래 횟수를 전략 평균에 맞춘다
  const targetTrades = Math.round(Object.values(real).reduce((a, r) => a + r.trades, 0) / Object.keys(real).length);
  const barsOos = folds.length * OOS;
  const p = Math.min(0.5, targetTrades / barsOos);

  const rets = [];
  for (let s = 1; s <= SEEDS; s++) {
    let eq = 1000, tr = 0;
    for (let fi = 0; fi < folds.length; fi++) {
      const f = folds[fi], sl = slice(f.oosFrom, f.oosTo);
      const o = backtest(sl.c, randomSignal(s * 1000 + fi, p, true), { feeBp, slipBp: SLIP, lev: LEV, equity0: 1000, warmup: sl.warm });
      eq *= (1 + o.retPct / 100); tr += o.trades;
    }
    rets.push({ ret: (eq / 1000 - 1) * 100, trades: tr });
  }
  rets.sort((a, b) => a.ret - b.ret);
  const q = (x) => rets[Math.min(rets.length - 1, Math.floor(rets.length * x))].ret;
  const avgTr = Math.round(rets.reduce((a, r) => a + r.trades, 0) / rets.length);

  console.log('══════ 편도 수수료 ' + (feeBp / 100).toFixed(2) + '% ══════');
  console.log('무작위 매매 ' + SEEDS + '회 (평균 ' + avgTr + '거래): ' +
              '최악 ' + q(0).toFixed(0) + '% / 하위25% ' + q(0.25).toFixed(0) + '% / 중앙 ' + q(0.5).toFixed(0) +
              '% / 상위25% ' + q(0.75).toFixed(0) + '% / 상위5% ' + q(0.95).toFixed(0) + '% / 최고 ' + q(0.999).toFixed(0) + '%');
  console.log('무작위가 흑자일 확률: ' + (rets.filter(r => r.ret > 0).length / rets.length * 100).toFixed(0) + '%\n');
  console.log('전략        검증수익   무작위 중 몇 등(백분위)   판정');
  for (const name of Object.keys(real)) {
    const v = real[name].ret;
    const beat = rets.filter(r => r.ret < v).length / rets.length * 100;
    const verdict = beat >= 95 ? '★ 무작위보다 확실히 낫다' : beat >= 80 ? '△ 나은 편이나 운일 수 있다' : '✕ 무작위와 구별 안 됨';
    console.log(name.padEnd(11) + ((v >= 0 ? '+' : '') + v.toFixed(1) + '%').padStart(9) + '   ' +
                (beat.toFixed(0) + '%').padStart(10) + '                ' + verdict);
  }
  console.log('');
}

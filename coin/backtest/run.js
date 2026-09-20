// 워크포워드 백테스트 — 앞 기간에서 파라미터를 고르고, 그 다음 기간(처음 보는 구간)에서 검증한다.
// 과거에 맞춘 숫자가 미래에도 통하는지 보려는 것. 실행: node coin/backtest/run.js
'use strict';
const fs = require('fs'), path = require('path');
const { backtest, loadCsv } = require('./engine');
const { CATALOG, expand } = require('./strategies');

const CANDLES = loadCsv(path.join(__dirname, 'data', 'ethusdt-1h.csv'));
const WARM = 320;                  // 지표가 자리잡는 데 필요한 앞 봉 (가장 긴 지표 300 + 여유)
const IS = 24 * 30 * 8;            // 최적화 구간 8개월
const OOS = 24 * 30 * 4;           // 검증 구간 4개월
const FEES = [2, 6, 10, 40];       // 편도 수수료(bp) = 0.02% / 0.06% / 0.10% / 0.40%
const SLIP = 2;                    // 슬리피지 2bp (시장가 체결 밀림)
const LEV = 1;
const MIN_TRADES = 10;             // 표본이 이보다 적은 파라미터는 IS 에서 고르지 않는다

const iso = (s) => new Date(s * 1000).toISOString().slice(0, 10);
const pct = (x) => (x >= 0 ? '+' : '') + x.toFixed(1) + '%';

// 구간 자르기 — 앞에 warmup 을 붙여 지표를 살린 뒤, 그 지점부터 매매 시작
function slice(from, to) {
  const s = Math.max(0, from - WARM);
  return { c: CANDLES.slice(s, to), warm: from - s };
}

// 폴드 만들기
const folds = [];
for (let start = WARM; start + IS + OOS <= CANDLES.length; start += OOS) {
  folds.push({ isFrom: start, isTo: start + IS, oosFrom: start + IS, oosTo: start + IS + OOS });
}

console.log('데이터: ETH/USDT 1시간봉 ' + CANDLES.length.toLocaleString() + '개  ' +
            iso(CANDLES[0].t) + ' ~ ' + iso(CANDLES[CANDLES.length - 1].t) + ' (출처: Huobi 공개 1분봉 집계)');
console.log('워크포워드 ' + folds.length + '구간 · 최적화 8개월 → 검증 4개월 · 슬리피지 ' + SLIP + 'bp · 레버리지 ' + LEV + '배\n');

function run(sl, sig, feeBp) {
  return backtest(sl.c, sig, { feeBp: feeBp, slipBp: SLIP, lev: LEV, equity0: 1000, warmup: sl.warm });
}

const report = { meta: { candles: CANDLES.length, from: iso(CANDLES[0].t), to: iso(CANDLES[CANDLES.length - 1].t),
                         folds: folds.length, isMonths: 8, oosMonths: 4, slipBp: SLIP, lev: LEV }, rows: [] };

for (const feeBp of FEES) {
  console.log('══════ 편도 수수료 ' + (feeBp / 100).toFixed(2) + '%  (왕복 ' + (feeBp / 50).toFixed(2) + '%) ══════');
  const lines = [];
  for (const name of Object.keys(CATALOG)) {
    const combos = expand(CATALOG[name].grid);
    let eq = 1000, totTrades = 0, totFee = 0, totGross = 0, wins = 0, mddMax = 0, chosen = [];
    let oosPositive = 0;

    for (const fold of folds) {
      // ① 최적화 구간에서 가장 좋은 파라미터를 고른다
      let best = null;
      for (const p of combos) {
        const sl = slice(fold.isFrom, fold.isTo);
        const r = run(sl, CATALOG[name].make(p)(sl.c), feeBp);
        if (name !== 'buyHold' && r.trades < MIN_TRADES) continue;
        if (!best || r.retPct > best.r.retPct) best = { p: p, r: r };
      }
      if (!best) { chosen.push('-'); continue; }

      // ② 그 파라미터로 「처음 보는」 검증 구간을 돌린다
      const sl2 = slice(fold.oosFrom, fold.oosTo);
      const o = run(sl2, CATALOG[name].make(best.p)(sl2.c), feeBp);
      eq *= (1 + o.retPct / 100);                       // 구간을 복리로 이어붙임
      totTrades += o.trades; totFee += o.feePaid; totGross += o.grossPnl;
      wins += o.list.filter(t => t.net > 0).length;
      if (o.mddPct > mddMax) mddMax = o.mddPct;
      if (o.retPct > 0) oosPositive++;
      chosen.push(JSON.stringify(best.p).replace(/["{}]/g, ''));
    }

    const ret = (eq / 1000 - 1) * 100;
    const feeShare = totGross > 0 ? (totFee / totGross * 100) : (totFee > 0 ? Infinity : 0);
    lines.push({ name, ret, totTrades, winRate: totTrades ? wins / totTrades * 100 : 0,
                 totFee, totGross, feeShare, mddMax, oosPositive, folds: folds.length, chosen });
  }
  lines.sort((a, b) => b.ret - a.ret);
  console.log('전략        검증수익   거래   승률   최대낙폭  수수료합  총이익   수수료/총이익  흑자구간');
  for (const l of lines) {
    console.log(
      l.name.padEnd(11) +
      pct(l.ret).padStart(8) + '  ' +
      String(l.totTrades).padStart(5) + '  ' +
      (l.winRate.toFixed(0) + '%').padStart(5) + '  ' +
      (l.mddMax.toFixed(0) + '%').padStart(7) + '  ' +
      l.totFee.toFixed(0).padStart(8) + '  ' +
      l.totGross.toFixed(0).padStart(7) + '  ' +
      (l.totGross > 0 ? (l.feeShare.toFixed(0) + '%') : '총이익없음').padStart(12) + '  ' +
      (l.oosPositive + '/' + l.folds).padStart(7));
  }
  console.log('');
  report.rows.push({ feeBp, lines });
}

fs.writeFileSync(path.join(__dirname, 'result.json'), JSON.stringify(report, null, 1));
console.log('결과 저장: coin/backtest/result.json');

// 손익분기 — 거래 한 번에 최소 몇 % 를 벌어야 수수료를 넘기는가
console.log('\n── 손익분기: 왕복 비용(수수료+슬리피지)을 넘으려면 거래당 최소 이 정도는 움직여야 한다 ──');
for (const feeBp of FEES) {
  const roundTrip = (feeBp * 2 + SLIP * 2) / 100;
  console.log('편도 ' + (feeBp / 100).toFixed(2) + '% → 왕복 비용 ' + roundTrip.toFixed(2) + '% ' +
              '| 승률 50% 라면 이기는 거래가 평균 ' + (roundTrip * 2).toFixed(2) + '% 이상이어야 본전');
}

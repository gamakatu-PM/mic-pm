// 백테스트 엔진 — 수수료·슬리피지·레버리지·손절을 넣고 돌린다.
// 규칙(실제 브리지와 같게 맞춤): 한 번에 포지션 1개, 추가 진입 없음(ALLOW_PYRAMID=NO).
// 미래를 보지 않는다: 신호는 봉 i 의 종가까지만 보고 계산하고, 체결은 봉 i+1 의 시가에서 한다.
'use strict';

/**
 * @param candles [{t,o,h,l,c,v}] 시간순
 * @param signal  (i, c) => 'LONG' | 'SHORT' | 'FLAT'   ← 봉 i 종가까지만 보고 목표 포지션을 반환
 * @param opt {feeBp 편도 수수료(bp), slipBp 슬리피지(bp), lev 레버리지, slPct 손절%, tpPct 익절%,
 *             equity0 초기자본, warmup 앞쪽 건너뛸 봉 수, allowShort}
 */
function backtest(candles, signal, opt) {
  const o = Object.assign({ feeBp: 6, slipBp: 2, lev: 1, slPct: 0, tpPct: 0,
                            equity0: 1000, warmup: 200, allowShort: true }, opt || {});
  const fee = o.feeBp / 10000, slip = o.slipBp / 10000;

  let equity = o.equity0, peak = equity, mdd = 0, feePaid = 0, bust = false;
  let pos = null;                       // {side:1|-1, entry, notional, sl, tp, ti}
  const trades = [];
  const curve = [];

  const close_ = (px, i, why) => {
    // 청산: 불리한 방향으로 슬리피지
    const fill = px * (1 - pos.side * slip);
    const pnlPct = pos.side * (fill - pos.entry) / pos.entry;
    const gross = pos.notional * pnlPct;
    const f = pos.notional * fee + (pos.notional * (1 + pnlPct)) * fee;   // 진입분 + 청산분
    equity += gross - f;
    feePaid += f;
    trades.push({
      side: pos.side, entry: pos.entry, exit: fill, ti: pos.ti, to: i, why: why,
      bars: i - pos.ti, gross: gross, fee: f, net: gross - f, equity: equity
    });
    pos = null;
    if (equity <= 0) bust = true;
  };

  const open_ = (side, px, i) => {
    const fill = px * (1 + side * slip);                  // 진입: 불리한 방향으로 슬리피지
    const notional = equity * o.lev;
    pos = { side: side, entry: fill, notional: notional, ti: i,
            sl: o.slPct > 0 ? fill * (1 - side * o.slPct / 100) : 0,
            tp: o.tpPct > 0 ? fill * (1 + side * o.tpPct / 100) : 0 };
  };

  for (let i = o.warmup; i < candles.length - 1; i++) {
    const cur = candles[i], nxt = candles[i + 1];

    // ① 보유 중이면 다음 봉 안에서 손절·익절이 먼저 닿는지 본다 (봉 내부는 순서를 모르므로 손절을 먼저 본다 = 보수적)
    if (pos) {
      if (pos.sl > 0) {
        const hit = pos.side === 1 ? (nxt.l <= pos.sl) : (nxt.h >= pos.sl);
        if (hit) {
          // 시가가 이미 손절선을 지나쳤으면 시가에 체결(갭). 아니면 손절가에 체결.
          const px = pos.side === 1 ? Math.min(pos.sl, nxt.o) : Math.max(pos.sl, nxt.o);
          close_(px, i + 1, 'SL');
          if (bust) break;
        }
      }
      if (pos && pos.tp > 0) {
        const hit = pos.side === 1 ? (nxt.h >= pos.tp) : (nxt.l <= pos.tp);
        if (hit) {
          const px = pos.side === 1 ? Math.max(pos.tp, nxt.o) : Math.min(pos.tp, nxt.o);
          close_(px, i + 1, 'TP');
          if (bust) break;
        }
      }
    }

    // ② 봉 i 종가 기준 신호 → 봉 i+1 시가에 반영
    let want = signal(i, candles);
    if (want === 'SHORT' && !o.allowShort) want = 'FLAT';
    const have = pos ? (pos.side === 1 ? 'LONG' : 'SHORT') : 'FLAT';
    if (want !== have) {
      if (pos) { close_(nxt.o, i + 1, 'SIG'); if (bust) break; }
      if (want === 'LONG') open_(1, nxt.o, i + 1);
      else if (want === 'SHORT') open_(-1, nxt.o, i + 1);
    }

    // ③ 자산곡선·최대낙폭 (미실현 포함)
    const unreal = pos ? pos.notional * pos.side * (cur.c - pos.entry) / pos.entry : 0;
    const eq = equity + unreal;
    if (eq > peak) peak = eq;
    const dd = peak > 0 ? (peak - eq) / peak : 0;
    if (dd > mdd) mdd = dd;
    curve.push(eq);
  }
  if (pos) close_(candles[candles.length - 1].c, candles.length - 1, 'END');

  // 집계
  const wins = trades.filter(t => t.net > 0), losses = trades.filter(t => t.net <= 0);
  const grossWin = wins.reduce((a, t) => a + t.gross, 0);
  const grossLoss = losses.reduce((a, t) => a + t.gross, 0);
  const sum = (a) => a.reduce((x, y) => x + y, 0);
  return {
    equity0: o.equity0, equity: equity, bust: bust,
    retPct: (equity / o.equity0 - 1) * 100,
    trades: trades.length,
    winRate: trades.length ? wins.length / trades.length * 100 : 0,
    avgWin: wins.length ? sum(wins.map(t => t.net)) / wins.length : 0,
    avgLoss: losses.length ? sum(losses.map(t => t.net)) / losses.length : 0,
    profitFactor: grossLoss < 0 ? grossWin / -grossLoss : (grossWin > 0 ? Infinity : 0),
    mddPct: mdd * 100,
    feePaid: feePaid,
    grossPnl: sum(trades.map(t => t.gross)),
    netPnl: sum(trades.map(t => t.net)),
    avgBars: trades.length ? sum(trades.map(t => t.bars)) / trades.length : 0,
    list: trades
  };
}

// 캔들 CSV 읽기 (t,o,h,l,c,v,n)
function loadCsv(file) {
  const fs = require('fs');
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const out = [];
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i]) continue;
    const p = lines[i].split(',');
    out.push({ t: +p[0], o: +p[1], h: +p[2], l: +p[3], c: +p[4], v: +p[5] });
  }
  return out;
}

module.exports = { backtest, loadCsv };

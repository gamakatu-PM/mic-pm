// 엔진 자가시험 — 손으로 계산한 답과 맞는지 본다. 실행: node coin/backtest/selftest.js
'use strict';
const { backtest } = require('./engine');

const results = [];
const ok = (name, cond, info) => results.push({ name, ok: !!cond, info: info === undefined ? '' : String(info) });
const near = (a, b, eps) => Math.abs(a - b) < (eps === undefined ? 1e-6 : eps);
const bar = (p, h, l) => ({ t: 0, o: p, h: h === undefined ? p : h, l: l === undefined ? p : l, c: p, v: 1 });

// 1. 항상 롱 — 손으로 계산: 100에 진입, 110에 종료, 편도 10bp
{
  const c = [bar(100), bar(100), bar(110)];
  const r = backtest(c, () => 'LONG', { feeBp: 10, slipBp: 0, lev: 1, equity0: 1000, warmup: 0 });
  // 진입가 = 봉1의 시가 100, 청산 = 마지막 종가 110 → 총이익 100, 수수료 1 + 1.1 = 2.1
  ok('1 진입가는 신호 다음 봉의 시가(미래 안 봄)', near(r.list[0].entry, 100), r.list[0] && r.list[0].entry);
  ok('1a 총이익 100', near(r.list[0].gross, 100), r.list[0] && r.list[0].gross);
  ok('1b 수수료 2.1 (진입 1 + 청산 1.1)', near(r.feePaid, 2.1), r.feePaid);
  ok('1c 최종자산 1097.9', near(r.equity, 1097.9), r.equity);
  ok('1d 거래 1건·승률 100', r.trades === 1 && near(r.winRate, 100), r.trades + '/' + r.winRate);
}

// 2. 슬리피지 — 롱 진입은 비싸게, 청산은 싸게
{
  const c = [bar(100), bar(100), bar(100)];
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 10, lev: 1, equity0: 1000, warmup: 0 });
  ok('2 진입 100.1 / 청산 99.9 (슬리피지 10bp 양쪽)', near(r.list[0].entry, 100.1) && near(r.list[0].exit, 99.9),
     r.list[0] && (r.list[0].entry + '/' + r.list[0].exit));
  ok('2a 가격이 안 움직여도 슬리피지만큼 손실', r.list[0].gross < 0, r.list[0] && r.list[0].gross);
}

// 3. 손절 — 롱 진입 100, 손절 5% = 95. 다음 봉 저가 90 이면 95 에 체결
{
  const c = [bar(100), bar(100), { t: 0, o: 99, h: 99, l: 90, c: 92, v: 1 }, bar(92)];
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 1, slPct: 5, equity0: 1000, warmup: 0 });
  ok('3 손절가 95 에 체결, 사유 SL', r.list[0].why === 'SL' && near(r.list[0].exit, 95),
     r.list[0] && (r.list[0].why + '/' + r.list[0].exit));
  ok('3a 손실 -5%', near(r.list[0].gross, -50), r.list[0] && r.list[0].gross);
}

// 3b. 갭 하락 — 시가가 이미 손절선 아래면 시가에 체결(손절가보다 불리)
{
  const c = [bar(100), bar(100), { t: 0, o: 90, h: 91, l: 88, c: 89, v: 1 }, bar(89)];
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 1, slPct: 5, equity0: 1000, warmup: 0 });
  ok('3b 갭이면 손절가 95 가 아니라 시가 90 에 체결', near(r.list[0].exit, 90), r.list[0] && r.list[0].exit);
}

// 4. 익절
{
  const c = [bar(100), bar(100), { t: 0, o: 101, h: 120, l: 100, c: 118, v: 1 }, bar(118)];
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 1, tpPct: 10, equity0: 1000, warmup: 0 });
  ok('4 익절가 110 에 체결, 사유 TP', r.list[0].why === 'TP' && near(r.list[0].exit, 110),
     r.list[0] && (r.list[0].why + '/' + r.list[0].exit));
}

// 5. 숏 — 가격이 내리면 이익
{
  const c = [bar(100), bar(100), bar(90)];
  const r = backtest(c, () => 'SHORT', { feeBp: 0, slipBp: 0, lev: 1, equity0: 1000, warmup: 0 });
  ok('5 숏 100→90 이면 +10%', near(r.list[0].gross, 100) && r.list[0].side === -1, r.list[0] && r.list[0].gross);
}

// 5b. allowShort=false 면 숏 신호를 무시
{
  const c = [bar(100), bar(100), bar(90)];
  const r = backtest(c, () => 'SHORT', { feeBp: 0, slipBp: 0, allowShort: false, equity0: 1000, warmup: 0 });
  ok('5b 숏 금지면 거래 0건', r.trades === 0, r.trades);
}

// 6. 레버리지 — 3배면 손익도 3배
{
  const c = [bar(100), bar(100), bar(110)];
  const a = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 1, equity0: 1000, warmup: 0 });
  const b = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 3, equity0: 1000, warmup: 0 });
  ok('6 레버리지 3배면 손익 3배', near(b.list[0].gross, a.list[0].gross * 3), a.list[0].gross + ' vs ' + b.list[0].gross);
}

// 7. 수수료만으로 자산이 줄어드는가 (왕복 계속)
{
  const c = []; for (let i = 0; i < 60; i++) c.push(bar(100));
  let k = 0;
  const r = backtest(c, () => (++k % 2 ? 'LONG' : 'SHORT'), { feeBp: 40, slipBp: 0, lev: 1, equity0: 1000, warmup: 0 });
  ok('7 가격이 전혀 안 움직여도 왕복 수수료로 자산 감소', r.equity < 1000 && r.trades > 10,
     '거래 ' + r.trades + '건, 자산 ' + r.equity.toFixed(1) + ', 수수료 ' + r.feePaid.toFixed(1));
  ok('7a 총손익 0인데 순손익은 수수료만큼 마이너스', near(r.grossPnl, 0, 1e-6) && near(r.netPnl, -r.feePaid, 1e-6),
     r.grossPnl.toFixed(6) + ' / ' + r.netPnl.toFixed(3));
}

// 8. 최대낙폭
{
  const c = [bar(100), bar(100), bar(200), bar(100), bar(150)];
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 1, equity0: 1000, warmup: 0 });
  ok('8 최대낙폭이 0보다 큼', r.mddPct > 0, r.mddPct.toFixed(1) + '%');
}

// 9. 파산 — 레버리지 20배에 -10% 면 자산 0 이하
{
  const c = [bar(100), bar(100), bar(90), bar(90)];
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, lev: 20, equity0: 1000, warmup: 0 });
  ok('9 20배 레버리지에 -10% 면 파산 표시', r.bust === true && r.equity <= 0, r.equity.toFixed(1) + ' bust=' + r.bust);
}

// 10. warmup 존중
{
  const c = []; for (let i = 0; i < 20; i++) c.push(bar(100 + i));
  const r = backtest(c, () => 'LONG', { feeBp: 0, slipBp: 0, equity0: 1000, warmup: 10 });
  ok('10 warmup 10 이면 11번째 봉 시가에 진입', near(r.list[0].entry, c[11].o), r.list[0] && r.list[0].entry);
}

const fails = results.filter(r => !r.ok);
for (const r of results) console.log((r.ok ? 'PASS' : 'FAIL') + '  ' + r.name + (r.ok ? '' : '   ← ' + r.info));
console.log('\n엔진 자가시험: ' + results.length + '건 중 PASS ' + (results.length - fails.length) + ' / FAIL ' + fails.length);
process.exit(fails.length ? 1 : 0);

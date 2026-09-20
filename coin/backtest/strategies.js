// 전략 모음 — 전부 「봉 i 종가까지만」 보고 목표 포지션을 반환한다(미래 안 봄).
'use strict';

function smaSeries(c, n) {
  const out = new Array(c.length).fill(NaN);
  let s = 0;
  for (let i = 0; i < c.length; i++) {
    s += c[i].c;
    if (i >= n) s -= c[i - n].c;
    if (i >= n - 1) out[i] = s / n;
  }
  return out;
}

function rsiSeries(c, n) {
  const out = new Array(c.length).fill(NaN);
  let ag = 0, al = 0;
  for (let i = 1; i < c.length; i++) {
    const d = c[i].c - c[i - 1].c;
    const g = d > 0 ? d : 0, l = d < 0 ? -d : 0;
    if (i <= n) { ag += g / n; al += l / n; if (i === n) out[i] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); }
    else { ag = (ag * (n - 1) + g) / n; al = (al * (n - 1) + l) / n; out[i] = al === 0 ? 100 : 100 - 100 / (1 + ag / al); }
  }
  return out;
}

function atrSeries(c, n) {
  const out = new Array(c.length).fill(NaN);
  let s = 0;
  for (let i = 1; i < c.length; i++) {
    const tr = Math.max(c[i].h - c[i].l, Math.abs(c[i].h - c[i - 1].c), Math.abs(c[i].l - c[i - 1].c));
    s += tr;
    if (i > n) s -= Math.max(c[i - n].h - c[i - n].l, Math.abs(c[i - n].h - c[i - n - 1].c), Math.abs(c[i - n].l - c[i - n - 1].c));
    if (i >= n) out[i] = s / n;
  }
  return out;
}

// ── 전략들 ──────────────────────────────────────────────────────────────
// 1. 이동평균 교차 — 가장 흔한 추세추종
function maCross(p) {
  return (c) => {
    const f = smaSeries(c, p.fast), s = smaSeries(c, p.slow);
    return (i) => {
      if (isNaN(f[i]) || isNaN(s[i])) return 'FLAT';
      return f[i] > s[i] ? 'LONG' : 'SHORT';
    };
  };
}

// 2. 돈치안 돌파 — n봉 최고가 돌파 시 롱, 최저가 이탈 시 숏
function donchian(p) {
  return (c) => {
    const n = p.n;
    const hi = new Array(c.length).fill(NaN), lo = new Array(c.length).fill(NaN);
    for (let i = n; i < c.length; i++) {
      let H = -Infinity, L = Infinity;
      for (let k = i - n; k < i; k++) { if (c[k].h > H) H = c[k].h; if (c[k].l < L) L = c[k].l; }
      hi[i] = H; lo[i] = L;
    }
    let state = 'FLAT';
    return (i) => {
      if (isNaN(hi[i])) return 'FLAT';
      if (c[i].c > hi[i]) state = 'LONG';
      else if (c[i].c < lo[i]) state = 'SHORT';
      return state;
    };
  };
}

// 3. RSI 역추세 — 과매도에 사고 과매수에 판다
function rsiRevert(p) {
  return (c) => {
    const r = rsiSeries(c, p.n);
    let state = 'FLAT';
    return (i) => {
      if (isNaN(r[i])) return 'FLAT';
      if (r[i] < p.lo) state = 'LONG';
      else if (r[i] > p.hi) state = 'SHORT';
      else if ((state === 'LONG' && r[i] > 50) || (state === 'SHORT' && r[i] < 50)) state = 'FLAT';
      return state;
    };
  };
}

// 4. 추세 필터 + 돌파 — 장기 추세 방향으로만 돌파를 먹는다
function trendBreak(p) {
  return (c) => {
    const s = smaSeries(c, p.trend);
    const n = p.n;
    const hi = new Array(c.length).fill(NaN), lo = new Array(c.length).fill(NaN);
    for (let i = n; i < c.length; i++) {
      let H = -Infinity, L = Infinity;
      for (let k = i - n; k < i; k++) { if (c[k].h > H) H = c[k].h; if (c[k].l < L) L = c[k].l; }
      hi[i] = H; lo[i] = L;
    }
    let state = 'FLAT';
    return (i) => {
      if (isNaN(hi[i]) || isNaN(s[i])) return 'FLAT';
      const up = c[i].c > s[i];
      if (up && c[i].c > hi[i]) state = 'LONG';
      else if (!up && c[i].c < lo[i]) state = 'SHORT';
      else if ((state === 'LONG' && !up) || (state === 'SHORT' && up)) state = 'FLAT';
      return state;
    };
  };
}

// 5. 기준선 — 그냥 들고 있기 (전략이 이것보다 못하면 의미 없음)
function buyHold() {
  return () => () => 'LONG';
}

const CATALOG = {
  maCross:    { make: maCross,    grid: { fast: [5, 10, 20, 30, 50], slow: [50, 100, 150, 200] } },
  donchian:   { make: donchian,   grid: { n: [12, 24, 48, 72, 120, 168] } },
  rsiRevert:  { make: rsiRevert,  grid: { n: [7, 14, 21], lo: [20, 25, 30], hi: [70, 75, 80] } },
  trendBreak: { make: trendBreak, grid: { n: [12, 24, 48, 72], trend: [100, 200, 300] } },
  buyHold:    { make: buyHold,    grid: {} }
};

// 격자를 조합 목록으로 펼친다
function expand(grid) {
  const keys = Object.keys(grid);
  if (!keys.length) return [{}];
  let out = [{}];
  for (const k of keys) {
    const next = [];
    for (const base of out) for (const v of grid[k]) next.push(Object.assign({}, base, { [k]: v }));
    out = next;
  }
  // maCross 는 fast < slow 인 것만
  return out.filter(p => !(p.fast !== undefined && p.slow !== undefined && p.fast >= p.slow));
}

module.exports = { CATALOG, expand, smaSeries, rsiSeries, atrSeries };

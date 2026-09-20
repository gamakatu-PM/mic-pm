// 1분봉 CSV(Huobi ethusdt) → 1시간봉으로 집계.  실행: node coin/backtest/prep.js <원본폴더>
'use strict';
const fs = require('fs'), path = require('path');
const SRC = process.argv[2] || '/home/user/data/raw';
const OUT = path.join(__dirname, 'data', 'ethusdt-1h.csv');

const files = fs.readdirSync(SRC).filter(f => /ethusdt_1min.*\.csv$/i.test(f)).sort();
if (!files.length) { console.error('원본 CSV 없음: ' + SRC); process.exit(1); }

const bars = new Map();                       // 시간(초, UTC 정각) → {o,h,l,c,v,n}
let minRows = 0, bad = 0;
for (const f of files) {
  const lines = fs.readFileSync(path.join(SRC, f), 'utf8').split('\n');
  for (let i = 1; i < lines.length; i++) {
    const s = lines[i]; if (!s) continue;
    const p = s.split(',');
    const t = parseInt(p[0], 10), o = +p[1], h = +p[2], l = +p[3], c = +p[4], v = +p[5];
    if (!(t > 0) || !(o > 0) || !(h > 0) || !(l > 0) || !(c > 0)) { bad++; continue; }
    minRows++;
    const hk = t - (t % 3600);
    const b = bars.get(hk);
    if (!b) bars.set(hk, { o: o, h: h, l: l, c: c, v: v || 0, n: 1, first: t, last: t });
    else {
      if (h > b.h) b.h = h;
      if (l < b.l) b.l = l;
      if (t < b.first) { b.first = t; b.o = o; }
      if (t > b.last) { b.last = t; b.c = c; }
      b.v += (v || 0); b.n++;
    }
  }
}
const keys = [...bars.keys()].sort((a, b) => a - b);
const out = ['t,o,h,l,c,v,n'];
for (const k of keys) { const b = bars.get(k); out.push([k, b.o, b.h, b.l, b.c, Math.round(b.v), b.n].join(',')); }
fs.writeFileSync(OUT, out.join('\n') + '\n');

const iso = (s) => new Date(s * 1000).toISOString().slice(0, 16).replace('T', ' ');
const thin = keys.filter(k => bars.get(k).n < 30).length;
console.log('원본 분봉 ' + minRows.toLocaleString() + '행 (불량 ' + bad + ')');
console.log('1시간봉 ' + keys.length.toLocaleString() + '개 : ' + iso(keys[0]) + ' ~ ' + iso(keys[keys.length - 1]) + ' UTC');
console.log('분봉 30개 미만으로 만들어진(구멍 있는) 시간봉: ' + thin + '개');
console.log('저장: ' + OUT);

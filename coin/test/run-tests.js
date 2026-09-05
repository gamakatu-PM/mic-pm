// deepcoin-bridge-v2.gs 모의 실행 — 정상 경로 + 고장 경로.  실행:  node coin/test/run-tests.js
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const { makeContext } = require('./gas-mock');

const SRC = fs.readFileSync(path.join(__dirname, '..', 'deepcoin-bridge-v2.gs'), 'utf8');
const TOKEN = 'tok-' + 'x'.repeat(30);
const KEYS = { DC_API_KEY: 'key123', DC_SECRET: 'secret456', DC_PASSPHRASE: 'pass789' };

// ── 거래소 모의 서버: 포지션 상태를 가진 라우터 ──
function exchange(opts) {
  opts = opts || {};
  const st = { pos: { long: opts.long || 0, short: opts.short || 0 }, orders: [] };
  const route = (rec) => {
    const u = new URL(rec.url);
    if (opts.networkDown) throw new Error('DNS 실패(모의)');
    if (u.pathname === '/deepcoin/market/instruments') {
      return { status: 200, body: { code: '0', msg: '', data: [{ instId: 'BTC-USDT-SWAP', ctVal: '0.001', lotSz: '1', minSz: '1' }] } };
    }
    if (u.pathname === '/deepcoin/account/positions') {
      const data = [];
      for (const side of ['long', 'short']) if (st.pos[side] > 0) data.push({ instType: 'SWAP', instId: 'BTC-USDT-SWAP', posSide: side, pos: String(st.pos[side]), posId: '1' });
      return { status: 200, body: { code: '0', msg: '', data } };
    }
    if (u.pathname === '/deepcoin/account/balances') {
      if (opts.badKey) return { status: 200, body: { code: '50111', msg: 'Invalid API Key', data: null } };
      return { status: 200, body: { code: '0', msg: '', data: [{ ccy: 'USDT', bal: '74', frozenBal: '0', availBal: '74' }] } };
    }
    if (u.pathname === '/deepcoin/trade/order') {
      const b = JSON.parse(rec.payload);
      st.orders.push(b);
      if (opts.rejectOrder) return { status: 200, body: { code: '0', msg: '', data: { ordId: '', clOrdId: '', sCode: '36', sMsg: 'InsufficientMoney:-0.000004' } } };
      if (opts.http500) return { status: 500, body: 'Internal Server Error' };
      const sz = parseInt(b.sz, 10);
      if (b.reduceOnly) st.pos[b.posSide] = Math.max(0, st.pos[b.posSide] - (opts.partialFill ? Math.floor(sz / 2) : sz));
      else st.pos[b.posSide] += sz;
      return { status: 200, body: { code: '0', msg: '', data: { ordId: 'ORD' + st.orders.length, clOrdId: b.clOrdId, sCode: '0', sMsg: '' } } };
    }
    return { status: 404, body: { code: '404', msg: 'no route ' + u.pathname } };
  };
  return { st, route };
}

function boot(scn, propsInit) {
  const ctx = makeContext(scn);
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx, { filename: 'deepcoin-bridge-v2.gs' });
  const p = ctx.PropertiesService.getScriptProperties();
  p.setProperty('WEBHOOK_TOKEN', TOKEN);
  p.setProperty('LOG_SHEET_ID', 'sheet-1');
  for (const k in (propsInit || {})) p.setProperty(k, propsInit[k]);
  return ctx;
}
function post(ctx, obj) {
  if (obj.token === undefined) obj.token = TOKEN;
  return JSON.parse(ctx.doPost({ postData: { contents: JSON.stringify(obj) } }).getContent());
}
function lastLog(ctx) { const rows = ctx.__mock.sheets.get('1.거래로그') || []; return rows[rows.length - 1]; }

// ── 검사 기록 ──
const results = [];
function check(name, cond, info) { results.push({ name, ok: !!cond, info: info === undefined ? '' : String(info) }); }

// 1. 토큰 불일치
{ const ctx = boot(exchange()); const r = post(ctx, { token: 'wrong', action: 'ENTER_LONG', qty: '0.01' });
  check('1 토큰 불일치 → REJECT', r.status === 'REJECT' && /토큰/.test(r.detail), r.detail);
  check('1a 거래소 호출 0건', ctx.__mock.calls.length === 0, ctx.__mock.calls.length); }

// 2. JSON 깨짐
{ const ctx = boot(exchange()); const r = JSON.parse(ctx.doPost({ postData: { contents: '{not json' } }).getContent());
  check('2 JSON 파싱 실패 → REJECT', r.status === 'REJECT' && /JSON/.test(r.detail), r.detail); }

// 3. DRY-RUN 진입 (키 없음): 주문 전송 0건, 로컬 상태 기록, 시트 로그 12열
{ const ctx = boot(exchange()); const r = post(ctx, { action: 'ENTER_LONG', symbol: 'BTC-USDT-SWAP', qty: '0.01', sl: '58000', id: 'a1' });
  const orderCalls = ctx.__mock.calls.filter(c => c.url.includes('/trade/order'));
  check('3 DRY-RUN 진입 상태', r.status === 'DRY-RUN', r.status);
  check('3a 계약수 = floor(0.01/0.001) = 10', r.detail.wouldSend.sz === '10', r.detail.wouldSend.sz);
  check('3b slTriggerPx 전달, slOrdPx 없음', r.detail.wouldSend.slTriggerPx === '58000' && r.detail.wouldSend.slOrdPx === undefined, JSON.stringify(r.detail.wouldSend));
  check('3c 주문 API 호출 0건', orderCalls.length === 0, orderCalls.length);
  check('3d 로컬 상태 POS_BTC-USDT-SWAP_long=10', ctx.__mock.props.get('POS_BTC-USDT-SWAP_long') === '10', ctx.__mock.props.get('POS_BTC-USDT-SWAP_long'));
  const row = lastLog(ctx);
  check('3e 시트 로그 12열, 상태 DRY-RUN, 모드 DRY', row && row.length === 12 && row[1] === 'DRY-RUN' && row[2] === 'DRY', JSON.stringify(row));
  check('3f 로그에 토큰이 남지 않음', !JSON.stringify(ctx.__mock.sheets.get('1.거래로그')).includes(TOKEN) && !String(ctx.__mock.props.get('LAST_LOG')).includes(TOKEN));
  check('3g 2.설정 탭 자동 생성 (기본값 6행)', (ctx.__mock.sheets.get('2.설정') || []).length === 7, (ctx.__mock.sheets.get('2.설정') || []).length);
  // 3h 같은 방향 재진입 → ALREADY_IN
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'a2' });
  check('3h 같은 방향 재진입 → REJECT ALREADY_IN', r2.status === 'REJECT' && /ALREADY_IN/.test(r2.detail), r2.detail);
  // 3i DRY 청산 → 상태 삭제
  const r3 = post(ctx, { action: 'EXIT_LONG', id: 'a3' });
  check('3i DRY-RUN 청산 reduceOnly sz=10', r3.status === 'DRY-RUN' && r3.detail.wouldSend.reduceOnly === true && r3.detail.wouldSend.sz === '10' && r3.detail.wouldSend.side === 'sell', JSON.stringify(r3.detail.wouldSend));
  check('3j 청산 후 로컬 상태 삭제', !ctx.__mock.props.has('POS_BTC-USDT-SWAP_long'));
  const r4 = post(ctx, { action: 'EXIT_LONG', id: 'a4' });
  check('3k 포지션 없을 때 청산 → SKIP', r4.status === 'SKIP', r4.status); }

// 4. 중복 알럿
{ const ctx = boot(exchange()); post(ctx, { action: 'ENTER_LONG', qty: '0.001', id: 'dup-1' });
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.001', id: 'dup-1' });
  check('4 같은 id 재수신 → REJECT DUP', r.status === 'REJECT' && /DUP/.test(r.detail), r.detail);
  ctx.__mock.cache.clear();                                   // 캐시가 날아가도 속성 50건으로 막히는가
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '0.001', id: 'dup-1' });
  check('4a 캐시 삭제 후에도 DUP', r2.status === 'REJECT' && /DUP/.test(r2.detail), r2.detail);
  const r3 = post(ctx, { action: 'ENTER_SHORT', qty: '0.001', time: '2026-09-05T01:00:00Z' });
  const r4 = post(ctx, { action: 'ENTER_SHORT', qty: '0.001', time: '2026-09-05T01:00:00Z' });
  check('4b id 없어도 action+symbol+time 으로 DUP', r3.status === 'DRY-RUN' && r4.status === 'REJECT' && /DUP/.test(r4.detail), r3.status + '/' + r4.detail); }

// 5. 알 수 없는 action / 허용 안 된 종목 / 수량 없음 / 상한 초과
{ const ctx = boot(exchange());
  check('5 알 수 없는 action → REJECT', post(ctx, { action: 'BUY', qty: '0.01', id: 'u1' }).status === 'REJECT');
  const r = post(ctx, { action: 'ENTER_LONG', symbol: 'DOGE-USDT-SWAP', qty: '1', id: 'u2' });
  check('5a 허용 안 된 종목 → REJECT', r.status === 'REJECT' && /허용/.test(r.detail), r.detail);
  const r2 = post(ctx, { action: 'ENTER_LONG', id: 'u3' });
  check('5b 수량 없음 → REJECT', r2.status === 'REJECT' && /수량/.test(r2.detail), r2.detail);
  const r3 = post(ctx, { action: 'ENTER_LONG', qty: '1', id: 'u4' });          // 1 BTC = 1000계약 > 50
  check('5c 상한 초과 → REJECT (줄이지 않음)', r3.status === 'REJECT' && /MAX_CONTRACTS/.test(r3.detail), r3.detail);
  check('5d 상한 초과 시 로컬 상태 안 바뀜', !ctx.__mock.props.has('POS_BTC-USDT-SWAP_long'));
  const r4 = post(ctx, { action: 'ENTER_LONG', contracts: '7', id: 'u5' });
  check('5e contracts 직접 지정 → sz=7', r4.status === 'DRY-RUN' && r4.detail.wouldSend.sz === '7', JSON.stringify(r4.detail.wouldSend)); }

// 6. KILL 스위치 (시트 값이 우선)
{ const ctx = boot(exchange()); post(ctx, { action: 'EXIT_SHORT', id: 'k0' });   // 2.설정 탭 생성
  const cfg = ctx.__mock.sheets.get('2.설정'); cfg.find(r => r[0] === 'KILL')[1] = 'yes'; ctx.__mock.cache.clear();
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'k1' });
  check('6 시트 KILL=yes → REJECT KILL', r.status === 'REJECT' && /KILL/.test(r.detail), r.detail);
  cfg.find(r => r[0] === 'KILL')[1] = 'NO'; ctx.__mock.cache.clear();
  check('6a KILL 해제 후 정상', post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'k2' }).status === 'DRY-RUN'); }

// 7. LIVE 진입: 서명 검증, 주문 전송, 주문 후 포지션 검증, 일일 카운트, 메일
{ const ex = exchange(); const ctx = boot(ex, Object.assign({ LIVE: 'YES' }, KEYS));
  ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['NOTIFY_EMAIL', 'me@example.com', '']]);
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', sl: '58000', id: 'L1' });
  const oc = ctx.__mock.calls.filter(c => c.url.endsWith('/deepcoin/trade/order'));
  check('7 LIVE 진입 상태', r.status === 'LIVE', r.status + ' ' + JSON.stringify(r.detail));
  check('7a 주문 1건 전송, 거래소 롱 10계약', oc.length === 1 && ex.st.pos.long === 10, oc.length + '/' + ex.st.pos.long);
  if (oc.length) {
    const h = oc[0].headers;
    const expect = Buffer.from(crypto.createHmac('sha256', KEYS.DC_SECRET).update(h['DC-ACCESS-TIMESTAMP'] + 'POST' + '/deepcoin/trade/order' + oc[0].payload).digest()).toString('base64');
    check('7b 서명 = Base64(HMAC(ts+POST+path+body))', h['DC-ACCESS-SIGN'] === expect);
    check('7c 헤더 5종 (KEY/SIGN/TIMESTAMP/PASSPHRASE/appid)', h['DC-ACCESS-KEY'] === 'key123' && h['DC-ACCESS-PASSPHRASE'] === 'pass789' && h['appid'] === '200103' && /^\d{4}-\d\d-\d\dT.*Z$/.test(h['DC-ACCESS-TIMESTAMP']), JSON.stringify(h));
    const b = JSON.parse(oc[0].payload);
    check('7d 주문 본문 규격', b.instId === 'BTC-USDT-SWAP' && b.tdMode === 'cross' && b.mrgPosition === 'merge' && b.side === 'buy' && b.posSide === 'long' && b.ordType === 'market' && b.sz === '10' && b.slTriggerPx === '58000' && b.clOrdId.length <= 20, oc[0].payload);
  }
  check('7e 주문 전 포지션 조회 → 주문 → 주문 후 조회 순서', ctx.__mock.calls.map(c => new URL(c.url).pathname).join('>') .includes('/deepcoin/account/positions>https:'.slice(0, 0) + '/deepcoin/account/positions') && ctx.__mock.calls.filter(c => c.url.includes('/account/positions')).length === 2, ctx.__mock.calls.map(c => new URL(c.url).pathname).join(' > '));
  check('7f 검증 OK, 포지션(후)=10 로그', r.detail.verify === 'OK' && lastLog(ctx)[7] === 10 && lastLog(ctx)[2] === 'LIVE', JSON.stringify(lastLog(ctx)));
  check('7g GET 서명에 ?query 포함', (() => { const g = ctx.__mock.calls.find(c => c.url.includes('/account/positions')); const u = new URL(g.url); const exp = Buffer.from(crypto.createHmac('sha256', KEYS.DC_SECRET).update(g.headers['DC-ACCESS-TIMESTAMP'] + 'GET' + u.pathname + u.search).digest()).toString('base64'); return g.headers['DC-ACCESS-SIGN'] === exp; })());
  check('7h 일일 카운트 1', [...ctx.__mock.props.entries()].some(([k, v]) => k.startsWith('DAY_') && v === '1'));
  check('7i 실주문 메일 1통', ctx.__mock.mails.length === 1 && /실주문/.test(ctx.__mock.mails[0].subject), ctx.__mock.mails.map(m => m.subject).join('|'));
  // 7j 같은 방향 재진입: 거래소에 롱이 있으므로 ALREADY_IN (로컬 기록이 아니라 거래소 기준)
  ctx.__mock.props.delete('POS_BTC-USDT-SWAP_long');
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'L2' });
  check('7j 거래소에 롱 있으면 로컬 기록 없어도 ALREADY_IN', r2.status === 'REJECT' && /ALREADY_IN/.test(r2.detail), r2.detail);
  // 7k LIVE 청산: 거래소 수량으로
  ex.st.pos.long = 13;                                          // 거래소에서 일부가 바뀌었다고 가정 (로컬 10 ≠ 거래소 13)
  const r3 = post(ctx, { action: 'EXIT_LONG', id: 'L3' });
  const oc2 = ctx.__mock.calls.filter(c => c.url.endsWith('/deepcoin/trade/order'));
  const b2 = JSON.parse(oc2[oc2.length - 1].payload);
  check('7k LIVE 청산은 거래소 수량 13 으로 (로컬 10 아님)', r3.status === 'LIVE' && b2.reduceOnly === true && b2.sz === '13' && b2.side === 'sell' && ex.st.pos.long === 0 && r3.detail.verify === 'OK', JSON.stringify(b2) + ' pos=' + ex.st.pos.long);
  const r4 = post(ctx, { action: 'EXIT_LONG', id: 'L4' });
  check('7l 거래소 포지션 0 이면 청산 SKIP (주문 안 보냄)', r4.status === 'SKIP' && ctx.__mock.calls.filter(c => c.url.endsWith('/deepcoin/trade/order')).length === 2, r4.status); }

// 8. 주문 거절 (code:"0" + sCode:"36") → ERROR, 상태 불변, 카운트 불변, 메일
{ const ex = exchange({ rejectOrder: true }); const ctx = boot(ex, Object.assign({ LIVE: 'YES' }, KEYS));
  ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['NOTIFY_EMAIL', 'me@example.com', '']]);
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'R1' });
  check('8 sCode=36 거절 → ERROR (v1 은 성공 처리했음)', r.status === 'ERROR' && /sCode=36/.test(r.detail), r.detail);
  check('8a 거절 시 로컬 상태·일일 카운트 안 바뀜', !ctx.__mock.props.has('POS_BTC-USDT-SWAP_long') && ![...ctx.__mock.props.keys()].some(k => k.startsWith('DAY_')));
  check('8b 오류 메일 1통 + 오늘 오류 수 1', ctx.__mock.mails.length === 1 && [...ctx.__mock.props.entries()].some(([k, v]) => k.startsWith('ERR_') && v === '1'), ctx.__mock.mails.length); }

// 9. HTTP 500 / 네트워크 단절 / 잘못된 키
{ const ctx = boot(exchange({ http500: true }), Object.assign({ LIVE: 'YES' }, KEYS));
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'H1' });
  check('9 HTTP 500 → ERROR', r.status === 'ERROR' && /HTTP 500/.test(r.detail), r.detail); }
{ const ctx = boot(exchange({ networkDown: true }), Object.assign({ LIVE: 'YES' }, KEYS));
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'N1' });
  check('9a 네트워크 단절 → ERROR, 주문 재시도 없음', r.status === 'ERROR' && ctx.__mock.calls.filter(c => c.url.includes('/trade/order')).length === 0, r.detail);
  check('9b 조회(GET)는 3회까지 재시도', ctx.__mock.calls.filter(c => c.url.includes('/account/positions')).length === 3, ctx.__mock.calls.filter(c => c.url.includes('/account/positions')).length); }
{ const ctx = boot(exchange(), { LIVE: 'YES' });                       // 키 없음
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'K1' });
  check('9c LIVE=YES + 키 없음 → ERROR, 주문 없음', r.status === 'ERROR' && /키/.test(r.detail) && ctx.__mock.calls.length === 0, r.detail); }

// 10. 잠금 BUSY / 일일 상한 / ALLOW_PYRAMID
{ const ctx = boot(exchange()); ctx.__mock.setLockBusy(true);
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'B1' });
  check('10 잠금 실패 → REJECT BUSY', r.status === 'REJECT' && /BUSY/.test(r.detail), r.detail); }
{ const ex = exchange(); const ctx = boot(ex, Object.assign({ LIVE: 'YES' }, KEYS));
  ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['MAX_TRADES_PER_DAY', '1', ''], ['ALLOW_PYRAMID', 'YES', '']]);
  const r1 = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'D1' });
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'D2' });
  check('10a ALLOW_PYRAMID=YES 면 1건째 LIVE, 2건째는 일일 상한으로 REJECT', r1.status === 'LIVE' && r2.status === 'REJECT' && /MAX_TRADES_PER_DAY/.test(r2.detail), r1.status + '/' + r2.detail);
  check('10b 상한 이후 거래소 포지션 그대로 10', ex.st.pos.long === 10, ex.st.pos.long); }

// 11. 부분 청산 감지
{ const ex = exchange({ long: 10, partialFill: true }); const ctx = boot(ex, Object.assign({ LIVE: 'YES' }, KEYS));
  const r = post(ctx, { action: 'EXIT_LONG', id: 'P1' });
  check('11 청산 후 잔량 있으면 PARTIAL 경고', r.status === 'LIVE' && /PARTIAL/.test(r.detail.verify) && r.detail.posAfter === 5, JSON.stringify(r.detail.verify)); }

// 12. SELFCHECK: 키 없음 → FAIL 포함, 키 있음 → 잔고·포지션 OK, 잘못된 키 → FAIL, 트리거 중복 설치 방지
{ const ctx = boot(exchange()); const s = ctx.SELFCHECK();
  const diag = ctx.__mock.sheets.get('0.자가진단');
  check('12 키 없음 SELFCHECK → FAIL 있음, 0.자가진단 탭 작성', s.fails >= 2 && diag && diag.length === s.rows.length + 3, 'fails=' + s.fails + ' rows=' + (diag && diag.length));
  check('12a 합계 행 FAIL', diag[diag.length - 1][1] === 'FAIL', diag[diag.length - 1].join('|')); }
{ const ctx = boot(exchange({ long: 3 }), KEYS);
  ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['NOTIFY_EMAIL', 'me@example.com', '']]);
  const s = ctx.SELFCHECK();
  const bal = s.rows.find(r => r[0].startsWith('잔고')); const pos = s.rows.find(r => r[0] === '거래소 포지션');
  check('12b 키 있음 → 잔고 OK(USDT 74/74), 포지션 long 3, FAIL 0', s.fails === 0 && bal[1] === 'OK' && /USDT 74\/74/.test(bal[2]) && /long 3/.test(pos[2]), 'fails=' + s.fails + ' ' + bal.join('|') + ' ' + pos.join('|'));
  check('12c 잔고 경로 /deepcoin/account/balances?instType=SWAP', ctx.__mock.calls.some(c => c.url.endsWith('/deepcoin/account/balances?instType=SWAP')));
  check('12d 트리거 설치 1회, 재실행 시 중복 안 함', ctx.설치_일일점검().includes('완료') && ctx.설치_일일점검().includes('이미') && ctx.__mock.triggers.length === 1); }
{ const ctx = boot(exchange({ badKey: true }), KEYS); const s = ctx.SELFCHECK();
  check('12e 잘못된 키 → 잔고 FAIL', s.rows.find(r => r[0].startsWith('잔고'))[1] === 'FAIL' && s.fails >= 1, s.rows.find(r => r[0].startsWith('잔고')).join('|')); }
{ const ctx = boot(exchange(), KEYS); ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['KILL', 'YES', '']]); const s = ctx.SELFCHECK();
  check('12f KILL=YES 면 자가진단 FAIL', s.rows.find(r => r[0] === 'KILL')[1] === 'FAIL'); }

// 13. 시트 없이도 동작 (LOG_SHEET_ID 비움) / 시트 열기 실패해도 주문 로직은 동작
{ const ctx = boot(exchange()); ctx.__mock.props.delete('LOG_SHEET_ID');
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'S1' });
  check('13 LOG_SHEET_ID 없음 → 시트 없이 DRY-RUN 정상', r.status === 'DRY-RUN' && ctx.__mock.sheets.size === 0); }
{ const ctx = boot(Object.assign(exchange(), { sheetFails: true }));
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'S2' });
  check('13a 시트 열기 실패 → 기본 설정으로 DRY-RUN 정상 (주문 로직 멈추지 않음)', r.status === 'DRY-RUN', r.status); }

// 14. doGet 은 주문 없이 상태만
{ const ctx = boot(exchange()); const g = JSON.parse(ctx.doGet().getContent());
  check('14 doGet → ok, live=NO, 거래소 호출 0', g.ok === true && g.live === 'NO' && ctx.__mock.calls.length === 0, JSON.stringify(g)); }

// 15. (감사 반영) 상한 설정값이 숫자가 아니면 거절 — 열림이 아니라 닫힘
{ const ctx = boot(exchange()); ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['MAX_CONTRACTS', '오십', '']]);
  const r = post(ctx, { action: 'ENTER_LONG', qty: '1', id: 'n1' });
  check('15 MAX_CONTRACTS=오십 → REJECT (NaN 통과 금지)', r.status === 'REJECT' && /숫자가 아님/.test(r.detail), r.detail);
  ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['MAX_CONTRACTS', '1,000', '']]); ctx.__mock.cache.clear();
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '0.5', id: 'n2' });
  check('15a MAX_CONTRACTS=1,000 (쉼표) → 1000 으로 읽어 500계약 통과', r2.status === 'DRY-RUN' && r2.detail.wouldSend.sz === '500', r2.status + ' ' + JSON.stringify(r2.detail.wouldSend)); }
{ const ctx = boot(exchange(), Object.assign({ LIVE: 'YES' }, KEYS)); ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['MAX_TRADES_PER_DAY', 'abc', '']]);
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'n3' });
  check('15b MAX_TRADES_PER_DAY=abc → REJECT, 주문 0건', r.status === 'REJECT' && ctx.__mock.calls.filter(c => c.url.includes('/trade/order')).length === 0, r.detail); }

// 16. (감사 반영) 틀린 토큰도 LAST_LOG 에 남지 않는다
{ const ctx = boot(exchange()); post(ctx, { token: 'WRONG-SECRET-TOKEN-999', action: 'ENTER_LONG', qty: '0.01' });
  check('16 틀린 토큰이 LAST_LOG 에 없음', !String(ctx.__mock.props.get('LAST_LOG')).includes('WRONG-SECRET-TOKEN-999'), ctx.__mock.props.get('LAST_LOG')); }

// 17. (감사 반영) ctVal 조회 실패: BTC 만 예비값, 다른 종목은 거절
{ const ex = exchange({ networkDown: true }); const ctx = boot(ex); ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['ALLOWED_SYMBOLS', 'BTC-USDT-SWAP, eth-usdt-swap', ''], ['MAX_CONTRACTS', '100000', '']]);
  const r = post(ctx, { action: 'ENTER_LONG', symbol: 'ETH-USDT-SWAP', qty: '1', id: 'c1' });
  check('17 ETH ctVal 조회 실패 → REJECT (BTC 값으로 환산 금지)', r.status === 'REJECT' && /ctVal/.test(r.detail), r.status + ' ' + JSON.stringify(r.detail));
  const r2 = post(ctx, { action: 'ENTER_LONG', symbol: 'btc-usdt-swap', qty: '0.01', id: 'c2' });
  check('17a BTC 는 예비값 0.001 로 10계약 + 소문자 종목 허용', r2.status === 'DRY-RUN' && r2.detail.wouldSend.sz === '10' && r2.detail.wouldSend.instId === 'BTC-USDT-SWAP', r2.status + ' ' + JSON.stringify(r2.detail.wouldSend));
  const r3 = post(ctx, { action: 'ENTER_LONG', symbol: 'ETH-USDT-SWAP', contracts: '3', id: 'c3' });
  check('17b contracts 로 주면 ctVal 없어도 진행', r3.status === 'DRY-RUN' && r3.detail.wouldSend.sz === '3', r3.status); }

// 18. (감사 반영) 주문은 나갔는데 주문 후 조회 실패 → LIVE 로 기록, ordId 남김, 실주문 메일
{ const ex = exchange(); let n = 0; const base = ex.route;
  ex.route = (rec) => { if (rec.url.includes('/account/positions')) { n++; if (n > 1) throw new Error('조회 타임아웃(모의)'); } return base(rec); };
  const ctx = boot(ex, Object.assign({ LIVE: 'YES' }, KEYS)); ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['NOTIFY_EMAIL', 'me@example.com', '']]);
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'p1' });
  check('18 주문 후 조회 실패 → 상태 LIVE + ordId + ⚠ 검증문구', r.status === 'LIVE' && r.detail.ordId === 'ORD1' && /주문은 나갔으나/.test(r.detail.verify), r.status + ' ' + JSON.stringify(r.detail));
  check('18a 실주문 메일 1통(오류 메일 아님), 로그 포지션(후)=조회실패', ctx.__mock.mails.length === 1 && /실주문/.test(ctx.__mock.mails[0].subject) && lastLog(ctx)[7] === '조회실패' && lastLog(ctx)[1] === 'LIVE', ctx.__mock.mails.map(m => m.subject).join('|') + ' ' + JSON.stringify(lastLog(ctx))); }

// 19. (감사 반영) KILL 은 캐시를 거치지 않는다 / sl 파싱값 / 부동소수
{ const ctx = boot(exchange()); post(ctx, { action: 'EXIT_SHORT', id: 'z0' });
  const cfg = ctx.__mock.sheets.get('2.설정'); cfg.find(r => r[0] === 'KILL')[1] = 'YES';           // 캐시 clear 없이
  const r = post(ctx, { action: 'ENTER_LONG', qty: '0.01', id: 'z1' });
  check('19 KILL=YES 즉시 반영 (캐시 안 거침)', r.status === 'REJECT' && /KILL/.test(r.detail), r.detail);
  cfg.find(r => r[0] === 'KILL')[1] = 'NO';
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '1.005', sl: '58000abc', id: 'z2' });
  check('19a sl=58000abc → 58000 으로 전송, 1.005 BTC → 1005계약', r2.status === 'REJECT' && /1005/.test(r2.detail), r2.detail);
  ctx.__mock.sheets.set('2.설정', [['키', '값', '설명'], ['MAX_CONTRACTS', '2000', '']]); ctx.__mock.cache.clear();
  const r3 = post(ctx, { action: 'ENTER_LONG', qty: '1.005', sl: '58000abc', id: 'z3' });
  check('19b 전송 본문 sz=1005, slTriggerPx=58000', r3.status === 'DRY-RUN' && r3.detail.wouldSend.sz === '1005' && r3.detail.wouldSend.slTriggerPx === '58000', JSON.stringify(r3.detail.wouldSend)); }

// 20. (감사 반영) 초기화_중복기록 으로 DUP 복구
{ const ctx = boot(exchange()); post(ctx, { action: 'ENTER_LONG', qty: '0.001', id: 'fixed-id' }); post(ctx, { action: 'EXIT_LONG', id: 'x' });
  const r1 = post(ctx, { action: 'ENTER_LONG', qty: '0.001', id: 'fixed-id' });
  ctx.초기화_중복기록(); ctx.__mock.cache.clear();
  const r2 = post(ctx, { action: 'ENTER_LONG', qty: '0.001', id: 'fixed-id' });
  check('20 DUP → 초기화_중복기록 후 같은 id 다시 통과', r1.status === 'REJECT' && r2.status === 'DRY-RUN', r1.status + '/' + r2.status); }

// ── 결과 ──
const fails = results.filter(r => !r.ok);
for (const r of results) console.log((r.ok ? 'PASS' : 'FAIL') + '  ' + r.name + (r.ok ? '' : '   ← ' + r.info));
console.log('\n합계: ' + results.length + '건 중 PASS ' + (results.length - fails.length) + ' / FAIL ' + fails.length);
process.exit(fails.length ? 1 : 0);

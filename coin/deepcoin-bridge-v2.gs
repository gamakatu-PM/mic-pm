/***********************************************************************
 * 딥코인(DeepCoin) 자동매매 중계 서버  v2.0  (Google Apps Script)
 * ───────────────────────────────────────────────────────────────────
 * 역할: 트레이딩뷰 알럿(웹훅) → 딥코인 무기한선물 시장가 주문
 *
 * 흐름:
 *   TradingView 알럿 ──POST──▶ 이 스크립트(웹앱 URL)
 *        ① 토큰 확인 → ② 잠금(동시 실행 차단) → ③ 중복 알럿 차단
 *        ④ 비상정지(KILL) → ⑤ 종목·수량·일일횟수 상한 → ⑥ 거래소 포지션 확인
 *        ⑦ 주문 (LIVE=YES 일 때만 실제 전송) → ⑧ 주문 후 포지션 재확인
 *        ⑨ 시트 기록 + 오류 시 메일 알림
 *
 * v1 → v2 에서 바뀐 것 (B등급: 기존 동작 수정, 이전 값은 주석에 보존)
 *   1. 주문 거절 감지: v1은 응답 code만 봤다. 딥코인은 거절도 code:"0"에
 *      data.sCode:"31" 식으로 온다 → v2는 sCode·retCode까지 본다.
 *   2. 포지션 진실은 거래소: v1은 스크립트 속성에 적어둔 수량으로 청산했다.
 *      v2는 청산 직전 /deepcoin/account/positions 를 조회해 실제 수량으로 청산.
 *   3. 잔고 조회 경로: v1 '/deepcoin/account/balance' → v2 '/deepcoin/account/balances?instType=SWAP'
 *      (ccxt deepcoin 구현과 동일. 공식 문서 사이트는 작성 환경에서 접근 불가라 ccxt 기준)
 *   4. slOrdPx:'-1' 제거: 딥코인 규격에 없는 항목(OKX 규격). slTriggerPx 만 보낸다.
 *   5. 새로 추가(A등급): 잠금, 중복 차단, KILL, 상한 3종, 주문 후 검증,
 *      자가진단 시트, 메일 알림, 일일 점검 트리거, appid 헤더.
 *
 * v2.0 → v2.1 (2026-09-05, 독립 감사 지적 반영)
 *   - 상한 설정값이 숫자가 아니면 통과시키던 것(sz > NaN = false) → 거절
 *   - 틀린 토큰이 LAST_LOG 속성에 남던 것 → 기록 전에 제거
 *   - ctVal 조회 실패 시 BTC 값으로 다른 종목까지 환산하던 것 → BTC 외 종목은 거절
 *   - 주문 후 포지션 조회가 실패하면 ERROR 로 뭉개던 것 → "주문은 나갔음" 을 LIVE 로 기록+메일
 *   - KILL 은 60초 캐시 없이 매번 시트에서 / 종목 비교 대문자 / sl·tp 파싱값 전송 / 부동소수 보정
 *   - 초기화_중복기록() 추가 (id 고정 사고 복구용)
 *
 * v2.1 → v2.2 (2026-09-05, 차장님: "이더리움인데 … 수입이 작아")
 *   - 기본 종목 ETH-USDT-SWAP (알럿에 symbol 이 없으면 허용 목록의 첫 종목)
 *   - 자가진단에 허용 종목별 「1계약 = ○ ETH」 표시 (ETH 계약 단위는 예비값 없이 반드시 조회)
 *   - 「3.잔고추이」 탭: 매일 07시 USDT 잔고·전일 대비·누적을 한 줄씩 → 수입이 얼마인지 숫자로
 *
 * v2.2 → v2.3 (2026-09-05, Pine 배선 원틀과 함께)
 *   - 알럿에 price(진입가)가 오면 손절·익절 방향 검사 (롱 sl<price, 숏 sl>price 아니면 거절)
 *   - 알럿 JSON 은 Pine 의 alert_message 에서 조립하는 방식을 표준으로 (coin/pine-alert-wiring.pine)
 *
 * v2.3 → v2.4 (2026-09-05, 커넥터 정리)
 *   - 텔레그램 알림(선택): 2.설정 TELEGRAM_CHAT_ID + 스크립트 속성 TELEGRAM_BOT_TOKEN 이 있으면 메일과 함께 폰 푸시
 *
 * ★ 설치 (5분)
 *   프로젝트 설정 → 스크립트 속성:
 *     DC_API_KEY / DC_SECRET / DC_PASSPHRASE  = 딥코인 API 3종 (출금 권한 없는 키로)
 *     WEBHOOK_TOKEN = 긴 임의 문자열 (트레이딩뷰 알럿 JSON의 token 과 동일)
 *     LIVE          = "NO"  ← 처음엔 반드시 NO. 체크리스트 통과 후 "YES"
 *     LOG_SHEET_ID  = 「딥코인-자동매매-로그」 시트 ID
 *   실행 메뉴에서 SELFCHECK() 를 한 번 돌려 0.자가진단 탭이 전부 OK 인지 본다.
 *   설치_일일점검() 을 한 번 실행하면 매일 07:00 자가진단이 자동으로 돈다.
 *
 * ★ 비상정지: 시트 「2.설정」 탭의 KILL 을 YES 로 바꾸면 다음 알럿부터 모든 주문 거절 (KILL 은 캐시 없이 매번 시트를 읽음).
 *   (폰에서 시트만 열면 된다. 스크립트 편집기 안 열어도 됨)
 ***********************************************************************/

var VERSION = 'v2.4 (2026-09-05)';
var BASE = 'https://api.deepcoin.com';
var INST_FALLBACK_CTVAL = 0.001;           // BTC-USDT-SWAP 1계약 = 0.001 BTC (조회 실패 시 예비값)
var TZ = 'Asia/Seoul';

var SHEET_DIAG = '0.자가진단';
var SHEET_LOG  = '1.거래로그';
var SHEET_CFG  = '2.설정';
var SHEET_BAL  = '3.잔고추이';   // 매일 07시 SELFCHECK 가 USDT 잔고를 한 줄씩 적는다 → 수입이 얼마인지 눈으로

// 「2.설정」 탭 기본값 — 시트에 없으면 이 값. 시트가 있으면 시트 값이 우선.
var CFG_DEFAULTS = {
  KILL:               'NO',              // YES 면 모든 주문 거절 (비상정지)
  ALLOWED_SYMBOLS:    'ETH-USDT-SWAP',   // 쉼표로 여러 개. 첫 번째가 알럿에 symbol 이 없을 때의 기본 종목 (2026-09-05 차장님: 이더리움)
  MAX_CONTRACTS:      '50',              // 1회 주문 최대 계약수. 넘으면 거절(줄이지 않음)
  MAX_TRADES_PER_DAY: '20',              // 하루 실주문 상한 (LIVE 만 셈)
  ALLOW_PYRAMID:      'NO',              // 같은 방향 포지션이 있을 때 추가 진입 허용?
  NOTIFY_EMAIL:       '',                // 오류·실주문 알림 메일. 비우면 안 보냄
  TELEGRAM_CHAT_ID:   ''                 // 텔레그램 알림 받을 chat_id. 봇 토큰은 스크립트 속성 TELEGRAM_BOT_TOKEN. 둘 다 있어야 보냄
};
var CFG_HELP = {
  KILL:               'YES 로 바꾸면 즉시 모든 주문 거절. 비상정지 스위치',
  ALLOWED_SYMBOLS:    '주문 허용 종목. 쉼표 구분. 목록에 없는 종목은 거절',
  MAX_CONTRACTS:      '1회 주문 최대 계약수. 초과하면 거절하고 메일',
  MAX_TRADES_PER_DAY: '하루 실주문 최대 횟수. 초과하면 거절하고 메일',
  ALLOW_PYRAMID:      'NO 면 같은 방향 포지션이 이미 있을 때 진입 거절',
  NOTIFY_EMAIL:       '오류·실주문 알림 받을 메일 주소',
  TELEGRAM_CHAT_ID:   '텔레그램 알림(폰 푸시). @userinfobot 에게 받은 숫자 id. 봇 토큰은 스크립트 속성 TELEGRAM_BOT_TOKEN'
};

var LOG_HEADER = ['시간(KST)', '상태', '모드', 'action', 'symbol', '요청sz',
                  '포지션(전)', '포지션(후)', 'ordId', 'alertId', '상세', '오류'];

// ═════════════════ ① 트레이딩뷰가 호출하는 입구 ═════════════════
function doPost(e) {
  var log = { time: new Date().toISOString(), version: VERSION };
  var lock = null;
  try {
    var p;
    try { p = JSON.parse(e.postData.contents); }
    catch (pe) { return reply_(log, 'REJECT', 'JSON 파싱 실패'); }
    var props = PropertiesService.getScriptProperties();
    log.recv = {}; for (var k in p) if (k !== 'token') log.recv[k] = p[k];   // 토큰은 맞든 틀리든 기록에 남기지 않는다

    // 보안: 토큰 불일치면 무시 (아무나 주문 못 쏘게)
    if (!p.token || p.token !== props.getProperty('WEBHOOK_TOKEN')) {
      return reply_(log, 'REJECT', '토큰 불일치');
    }

    // 잠금: 같은 순간 두 알럿이 오면 한 건씩 처리
    lock = LockService.getScriptLock();
    if (!lock.tryLock(20000)) { lock = null; return reply_(log, 'REJECT', 'BUSY — 다른 알럿 처리 중 (20초 대기 초과)'); }

    var action = String(p.action || '').toUpperCase();   // ENTER_LONG 등
    var allowed = cfg_('ALLOWED_SYMBOLS').toUpperCase().split(',').map(function (s) { return s.trim(); }).filter(function (s) { return s; });
    var instId = String(p.symbol || allowed[0] || 'ETH-USDT-SWAP').trim().toUpperCase();   // symbol 없으면 허용 목록의 첫 종목
    log.action = action; log.symbol = instId;

    // 중복 알럿 차단 (같은 id 또는 같은 action+symbol+time 은 한 번만)
    var alertId = String(p.id || (action + '|' + instId + '|' + (p.time || p.bar_time || '')));
    log.alertId = alertId;
    if (isDuplicate_(alertId)) return reply_(log, 'REJECT', 'DUP — 같은 알럿 재수신: ' + alertId);
    markSeen_(alertId);                              // 처리 도중 오류가 나도 재시도 못 하게 먼저 표시

    // 비상정지
    if (cfg_('KILL', true) === 'YES') return reply_(log, 'REJECT', 'KILL=YES — 비상정지 중 (2.설정 탭)');

    // 종목 허용 목록
    if (allowed.indexOf(instId) < 0) return reply_(log, 'REJECT', '허용 안 된 종목: ' + instId + ' (허용: ' + allowed.join(',') + ')');

    var live = (props.getProperty('LIVE') || 'NO').toUpperCase() === 'YES';
    log.mode = live ? 'LIVE' : 'DRY';
    var keysReady = hasKeys_();
    if (live && !keysReady) return reply_(log, 'ERROR', 'LIVE=YES 인데 API 키 3종이 비어 있음');

    var result;
    if (action === 'ENTER_LONG')       result = enter_(instId, 'long',  p, live, keysReady, log);
    else if (action === 'ENTER_SHORT') result = enter_(instId, 'short', p, live, keysReady, log);
    else if (action === 'EXIT_LONG')   result = exit_(instId, 'long',  live, keysReady, log);
    else if (action === 'EXIT_SHORT')  result = exit_(instId, 'short', live, keysReady, log);
    else return reply_(log, 'REJECT', '알 수 없는 action: ' + action);

    if (result && result.reject) return reply_(log, 'REJECT', result.reject);
    if (result && result.skip)   return reply_(log, 'SKIP', result.skip);
    return reply_(log, live ? 'LIVE' : 'DRY-RUN', result);
  } catch (err) {
    log.error = String(err && err.stack ? err.stack : err);
    return reply_(log, 'ERROR', String(err));
  } finally {
    if (lock) { try { lock.releaseLock(); } catch (le) {} }
  }
}

// GET 으로 열면 살아 있는지만 알려준다 (브라우저 확인용. 주문 없음)
function doGet() {
  return ContentService.createTextOutput(JSON.stringify({ ok: true, version: VERSION, live: (PropertiesService.getScriptProperties().getProperty('LIVE') || 'NO') }))
                       .setMimeType(ContentService.MimeType.JSON);
}

// ═════════════════ ② 진입 (시장가 + 손절 동시 설정) ═════════════════
function enter_(instId, posSide, p, live, keysReady, log) {
  // 수량: contracts(계약수) 가 오면 그대로, qty(BTC) 가 오면 계약수로 변환
  var sz;
  if (p.contracts !== undefined && p.contracts !== '') {
    sz = parseInt(p.contracts, 10);
  } else {
    var ctVal = getCtVal_(instId, keysReady);
    if (!(ctVal > 0)) return { reject: instId + ' 계약 단위(ctVal) 조회 실패 — 수량 환산 불가. contracts(계약수)로 보내거나 잠시 후 재시도' };
    var qtyBtc = parseFloat(p.qty);
    if (!(qtyBtc > 0)) return { reject: '수량 없음: qty=' + p.qty + ' (qty=BTC수량 또는 contracts=계약수 중 하나 필수)' };
    sz = Math.floor(qtyBtc / ctVal + 1e-9);        // 계약수 (내림. 1.005/0.001=1004.999… 같은 부동소수 오차 보정)
    log.ctVal = ctVal;
  }
  if (!(sz >= 1)) return { reject: '계약수 1 미만: ' + sz };
  var maxSz = numCfg_('MAX_CONTRACTS');
  if (isNaN(maxSz)) return { reject: 'MAX_CONTRACTS 설정값이 숫자가 아님: "' + cfg_('MAX_CONTRACTS') + '" — 2.설정 탭 확인 (안전을 위해 거절)' };
  if (sz > maxSz) { notify_('[딥코인] 상한 초과로 거절', 'action=' + log.action + ' sz=' + sz + ' > MAX_CONTRACTS=' + maxSz); return { reject: '계약수 ' + sz + ' > MAX_CONTRACTS ' + maxSz + ' — 거절(줄이지 않음)' }; }
  log.sz = sz;

  // 일일 실주문 상한 (LIVE 만 센다)
  if (live) {
    var n = todayCount_();
    var maxN = numCfg_('MAX_TRADES_PER_DAY');
    if (isNaN(maxN)) return { reject: 'MAX_TRADES_PER_DAY 설정값이 숫자가 아님: "' + cfg_('MAX_TRADES_PER_DAY') + '" — 2.설정 탭 확인 (안전을 위해 거절)' };
    if (n >= maxN) { notify_('[딥코인] 일일 상한 도달', '오늘 ' + n + '건 >= MAX_TRADES_PER_DAY ' + maxN); return { reject: '오늘 실주문 ' + n + '건 — MAX_TRADES_PER_DAY ' + maxN + ' 도달' }; }
  }

  // 진입 전 포지션 확인: 키가 있으면 거래소, 없으면 로컬 기록
  var posBefore = keysReady ? getPos_(instId, posSide) : loadState_(instId, posSide);
  log.posBefore = posBefore;
  if (posBefore > 0 && cfg_('ALLOW_PYRAMID') !== 'YES') {
    return { reject: 'ALREADY_IN — ' + posSide + ' 포지션 ' + posBefore + '계약 보유 중. 추가 진입은 ALLOW_PYRAMID=YES 일 때만' };
  }

  var body = {
    instId: instId,
    tdMode: 'cross',
    mrgPosition: 'merge',
    side: posSide === 'long' ? 'buy' : 'sell',
    posSide: posSide,
    ordType: 'market',
    sz: String(sz),
    clOrdId: ('KD' + Date.now()).slice(0, 20)
  };
  // 손절 동시 설정 (Pine 이 sl 가격을 보내줌). price(진입가)가 같이 오면 방향을 검사한다 — 롱 손절은 진입가 아래, 숏 손절은 위
  var px = parseFloat(p.price), sl = parseFloat(p.sl), tp = parseFloat(p.tp);
  if (px > 0 && sl > 0 && ((posSide === 'long' && sl >= px) || (posSide === 'short' && sl <= px)))
    return { reject: '손절 방향 오류 — ' + posSide + ' 진입가 ' + px + ' 인데 sl=' + sl + ' (롱은 아래, 숏은 위여야 함). Pine 의 손절 계산을 확인' };
  if (px > 0 && tp > 0 && ((posSide === 'long' && tp <= px) || (posSide === 'short' && tp >= px)))
    return { reject: '익절 방향 오류 — ' + posSide + ' 진입가 ' + px + ' 인데 tp=' + tp };
  if (p.sl && parseFloat(p.sl) > 0) body.slTriggerPx = String(parseFloat(p.sl));
  // v1 에 있던 slOrdPx:'-1' 은 딥코인 규격에 없어 제거 (B등급 변경, 2026-09-05)
  if (p.tp && parseFloat(p.tp) > 0) body.tpTriggerPx = String(parseFloat(p.tp));

  if (!live) {
    saveState_(instId, posSide, posBefore + sz);   // 모의에서도 상태는 기록
    return { dryRun: true, wouldSend: body, posBefore: posBefore, exchangeChecked: keysReady };
  }

  var res = dcPost_('/deepcoin/trade/order', body);
  log.ordId = res.data && res.data.ordId;
  bumpTodayCount_();
  return afterOrder_(instId, posSide, body, res, log, function (posAfter) {
    return (posAfter >= posBefore + sz) ? 'OK' : ('⚠ 기대 ' + (posBefore + sz) + ' vs 실제 ' + posAfter);
  }, '실주문', posBefore);
}

// ═════════════════ ③ 청산 (반대 방향 reduceOnly 시장가, 거래소 수량 기준) ═════════════════
function exit_(instId, posSide, live, keysReady, log) {
  var sz = keysReady ? getPos_(instId, posSide) : loadState_(instId, posSide);
  log.posBefore = sz;
  if (!(sz > 0)) return { skip: (keysReady ? '거래소' : '로컬 기록') + '에 ' + posSide + ' 포지션 없음 — 이미 손절됐거나 미진입' };
  log.sz = sz;

  var body = {
    instId: instId,
    tdMode: 'cross',
    mrgPosition: 'merge',
    side: posSide === 'long' ? 'sell' : 'buy',   // 롱 청산=매도, 숏 청산=매수
    posSide: posSide,
    ordType: 'market',
    sz: String(sz),
    reduceOnly: true,
    clOrdId: ('KX' + Date.now()).slice(0, 20)
  };

  if (!live) { clearState_(instId, posSide); return { dryRun: true, wouldSend: body, exchangeChecked: keysReady }; }

  var res = dcPost_('/deepcoin/trade/order', body);
  log.ordId = res.data && res.data.ordId;
  bumpTodayCount_();
  return afterOrder_(instId, posSide, body, res, log, function (posAfter) {
    return (posAfter === 0) ? 'OK' : ('⚠ PARTIAL — 청산 후에도 ' + posAfter + '계약 남음');
  }, '실청산', sz);
}

// 주문이 나간 뒤: 포지션 재조회 → 검증 → 메일. 재조회가 실패해도 "주문은 나갔다"를 LIVE 로 남긴다 (ERROR 로 뭉개지 않음)
function afterOrder_(instId, posSide, body, res, log, verifyFn, label, posBefore) {
  var posAfter = null, verify;
  try {
    posAfter = getPos_(instId, posSide);
    log.posAfter = posAfter;
    saveState_(instId, posSide, posAfter);
    verify = verifyFn(posAfter);
  } catch (e) {
    verify = '⚠ 주문은 나갔으나(ordId ' + (log.ordId || '?') + ') 주문 후 포지션 조회 실패 — 앱에서 직접 확인: ' + String(e);
    log.posAfter = '조회실패';
  }
  notify_('[딥코인] ' + label + ' ' + log.action + ' ' + body.sz + '계약 (' + verify + ')', JSON.stringify({ body: body, res: res, posBefore: posBefore, posAfter: posAfter }, null, 1));
  return { sent: body, ordId: log.ordId, posBefore: posBefore, posAfter: posAfter, verify: verify };
}

// ═════════════════ ④ 딥코인 서명·전송 (ccxt deepcoin 구현과 동일 규격) ═════════════════
// 서명 = Base64( HMAC-SHA256( timestamp + METHOD + requestPath(+?query) + body , secret ) )
function hasKeys_() {
  var pr = PropertiesService.getScriptProperties();
  return !!(pr.getProperty('DC_API_KEY') && pr.getProperty('DC_SECRET') && pr.getProperty('DC_PASSPHRASE'));
}

function dcHeaders_(method, requestPath, body) {
  var pr = PropertiesService.getScriptProperties();
  var key = pr.getProperty('DC_API_KEY'), sec = pr.getProperty('DC_SECRET'), pph = pr.getProperty('DC_PASSPHRASE');
  if (!key || !sec || !pph) throw 'API 키 미설정 — 스크립트 속성에 DC_API_KEY/DC_SECRET/DC_PASSPHRASE 저장 필요';
  var ts = new Date().toISOString();               // 예: 2026-08-08T09:08:57.715Z
  var prehash = ts + method + requestPath + (body || '');
  var sign = Utilities.base64Encode(Utilities.computeHmacSha256Signature(prehash, sec));
  return { 'DC-ACCESS-KEY': key, 'DC-ACCESS-SIGN': sign, 'DC-ACCESS-TIMESTAMP': ts,
           'DC-ACCESS-PASSPHRASE': pph, 'appid': '200103' };
}

function checkResp_(res, what) {
  var code = res.getResponseCode ? res.getResponseCode() : 200;
  var text = res.getContentText();
  var out;
  try { out = JSON.parse(text); } catch (e) { throw what + ' 응답이 JSON 아님 (HTTP ' + code + '): ' + String(text).slice(0, 200); }
  if (code !== 200)          throw what + ' HTTP ' + code + ': ' + text;
  if (String(out.code) !== '0') throw what + ' 거부 code=' + out.code + ' msg=' + out.msg;
  var d = out.data || {};
  // ★ 딥코인은 주문 거절도 code:"0" 으로 오고 data.sCode 에 사유가 있다 (예: 31 NotEnoughPositionToClose, 36 InsufficientMoney)
  if (!Array.isArray(d)) {
    if (d.sCode !== undefined && String(d.sCode) !== '0')   throw what + ' 거부 sCode=' + d.sCode + ' ' + (d.sMsg || '');
    if (d.retCode !== undefined && String(d.retCode) !== '0') throw what + ' 거부 retCode=' + d.retCode + ' ' + (d.retMsg || '');
  }
  return out;
}

function dcPost_(path, bodyObj) {
  var body = JSON.stringify(bodyObj);
  var res = UrlFetchApp.fetch(BASE + path, {
    method: 'post', contentType: 'application/json', payload: body,
    headers: dcHeaders_('POST', path, body), muteHttpExceptions: true
  });
  return checkResp_(res, 'POST ' + path);          // 주문은 재시도하지 않는다 (이중 주문 위험)
}

function dcGet_(path, query, retries) {
  var rp = path + (query ? '?' + query : '');
  var tries = (retries === undefined) ? 2 : retries;
  var lastErr;
  for (var i = 0; i <= tries; i++) {
    try {
      var res = UrlFetchApp.fetch(BASE + rp, { method: 'get', headers: dcHeaders_('GET', rp, ''), muteHttpExceptions: true });
      return checkResp_(res, 'GET ' + path);
    } catch (e) { lastErr = e; if (i < tries) Utilities.sleep(500); }
  }
  throw lastErr;
}

// 거래소 실제 포지션(계약수). 없으면 0
function getPos_(instId, posSide) {
  var out = dcGet_('/deepcoin/account/positions', 'instType=SWAP&instId=' + encodeURIComponent(instId));
  var list = out.data || [];
  for (var i = 0; i < list.length; i++) {
    if (list[i].instId === instId && list[i].posSide === posSide) return parseFloat(list[i].pos) || 0;
  }
  return 0;
}

// 계약 단위 (ctVal). 공개 API 라 키 없이도 조회. 6시간 캐시
function getCtVal_(instId, keysReady) {
  var cache = CacheService.getScriptCache();
  var hit = cache.get('ctVal_' + instId);
  if (hit) return parseFloat(hit);
  try {
    var res = UrlFetchApp.fetch(BASE + '/deepcoin/market/instruments?instType=SWAP', { muteHttpExceptions: true });
    var d = JSON.parse(res.getContentText());
    var list = (d && d.data) || [];
    for (var i = 0; i < list.length; i++) {
      if (list[i].instId === instId) {
        var v = parseFloat(list[i].ctVal);
        if (v > 0) { cache.put('ctVal_' + instId, String(v), 21600); return v; }
      }
    }
  } catch (e) {}
  return instId === 'BTC-USDT-SWAP' ? INST_FALLBACK_CTVAL : 0;   // 예비값은 BTC 전용. 다른 종목은 0 → 호출부가 거절
}

// ═════════════════ ⑤ 상태·중복·설정·카운터 ═════════════════
function stateKey_(instId, side) { return 'POS_' + instId + '_' + side; }
function saveState_(instId, side, sz)  { PropertiesService.getScriptProperties().setProperty(stateKey_(instId, side), String(sz)); }
function loadState_(instId, side)      { return parseInt(PropertiesService.getScriptProperties().getProperty(stateKey_(instId, side)) || '0', 10); }
function clearState_(instId, side)     { PropertiesService.getScriptProperties().deleteProperty(stateKey_(instId, side)); }

function isDuplicate_(alertId) {
  if (CacheService.getScriptCache().get('ALERT_' + alertId)) return true;
  var recent = JSON.parse(PropertiesService.getScriptProperties().getProperty('RECENT_ALERTS') || '[]');
  return recent.indexOf(alertId) >= 0;
}
function markSeen_(alertId) {
  CacheService.getScriptCache().put('ALERT_' + alertId, '1', 21600);          // 6시간
  var pr = PropertiesService.getScriptProperties();
  var recent = JSON.parse(pr.getProperty('RECENT_ALERTS') || '[]');
  recent.push(alertId); if (recent.length > 50) recent = recent.slice(-50);   // 최근 50건은 캐시가 날아가도 기억
  pr.setProperty('RECENT_ALERTS', JSON.stringify(recent));
}

function todayKey_() { return 'DAY_' + Utilities.formatDate(new Date(), TZ, 'yyyyMMdd'); }
function todayCount_() { return parseInt(PropertiesService.getScriptProperties().getProperty(todayKey_()) || '0', 10); }
function bumpTodayCount_() { PropertiesService.getScriptProperties().setProperty(todayKey_(), String(todayCount_() + 1)); }

// 설정: 시트 「2.설정」 → 스크립트 속성 → 기본값. 60초 캐시.
function cfg_(key, nocache) {
  var cache = CacheService.getScriptCache();
  var hit = nocache ? null : cache.get('CFG_' + key);
  if (hit !== null && hit !== undefined) return hit;
  var val = null;
  try {
    var sh = cfgSheet_();
    if (sh) {
      var rows = sh.getDataRange().getValues();
      for (var i = 1; i < rows.length; i++) {
        if (String(rows[i][0]).trim() === key) { var v = String(rows[i][1]).trim(); val = (v === '') ? null : v; break; }
      }
    }
  } catch (e) {}
  if (val === null) val = PropertiesService.getScriptProperties().getProperty(key);
  if (val === null || val === undefined) val = CFG_DEFAULTS[key];
  if (key === 'KILL' || key === 'ALLOW_PYRAMID') val = String(val).toUpperCase();
  if (!nocache) cache.put('CFG_' + key, String(val), 60);
  return String(val);
}
// 숫자 설정. 숫자가 아니면 NaN 을 돌려주고 호출부가 거절한다 (기본값으로 조용히 바꾸지 않는다)
function numCfg_(key) { var v = String(cfg_(key)).replace(/,/g, '').trim(); return /^\d+$/.test(v) ? parseInt(v, 10) : NaN; }

// ═════════════════ ⑥ 시트 (로그 · 설정 · 자가진단) ═════════════════
function logBook_() {
  var id = PropertiesService.getScriptProperties().getProperty('LOG_SHEET_ID');
  if (!id) return null;
  return SpreadsheetApp.openById(id);
}
function sheetOrCreate_(book, name, header) {
  var sh = book.getSheetByName(name);
  if (!sh) { sh = book.insertSheet(name); if (header) sh.appendRow(header); }
  else if (header && sh.getLastRow() === 0) sh.appendRow(header);
  return sh;
}
function cfgSheet_() {
  var book = logBook_(); if (!book) return null;
  var sh = book.getSheetByName(SHEET_CFG);
  if (!sh) {                                                // 없으면 기본값으로 만든다 (A등급 추가)
    sh = book.insertSheet(SHEET_CFG);
    sh.appendRow(['키', '값', '설명']);
    for (var k in CFG_DEFAULTS) sh.appendRow([k, CFG_DEFAULTS[k], CFG_HELP[k]]);
  }
  return sh;
}

function appendLog_(log) {
  try {
    var book = logBook_(); if (!book) return;
    var sh = sheetOrCreate_(book, SHEET_LOG, LOG_HEADER);
    // v1 시트(첫 탭 머리글 5열)가 그대로면 머리글을 v2 로 바꾸지 않고 새 탭에 쓴다 (기존 기록 보존)
    sh.appendRow([
      Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd HH:mm:ss'),
      log.status, log.mode || '', log.action || '', log.symbol || '',
      log.sz === undefined ? '' : log.sz,
      log.posBefore === undefined ? '' : log.posBefore,
      log.posAfter === undefined ? '' : log.posAfter,
      log.ordId || '', log.alertId || '',
      JSON.stringify(log.detail || '').slice(0, 45000), log.error || ''
    ]);
  } catch (e) {}
}

function reply_(log, status, detail) {
  log.status = status; log.detail = detail;
  var props = PropertiesService.getScriptProperties();
  try { props.setProperty('LAST_LOG', JSON.stringify(log).slice(0, 2500)); } catch (e) {}   // 최근 1건. 속성 한도 9KB(바이트) — 한글 3바이트라 2500자로
  props.setProperty('LAST_WEBHOOK_AT', log.time);
  if (status === 'ERROR') { bumpErrCount_(); notify_('[딥코인] 오류 ' + (log.action || ''), JSON.stringify(log, null, 1)); }
  appendLog_(log);
  return ContentService.createTextOutput(JSON.stringify({ status: status, detail: detail, version: VERSION }))
                       .setMimeType(ContentService.MimeType.JSON);
}
function bumpErrCount_() { var pr = PropertiesService.getScriptProperties(); var k = 'ERR_' + Utilities.formatDate(new Date(), TZ, 'yyyyMMdd'); pr.setProperty(k, String(parseInt(pr.getProperty(k) || '0', 10) + 1)); }

function notify_(subject, text) {
  try {
    var to = cfg_('NOTIFY_EMAIL');
    if (to && to.indexOf('@') >= 0) MailApp.sendEmail(to, subject, String(text).slice(0, 20000));
  } catch (e) {}
  try {   // 텔레그램 (선택): 폰 푸시. 메일과 별개로 실패해도 서로 영향 없음
    var chat = cfg_('TELEGRAM_CHAT_ID'), bot = PropertiesService.getScriptProperties().getProperty('TELEGRAM_BOT_TOKEN');
    if (chat && bot) {
      UrlFetchApp.fetch('https://api.telegram.org/bot' + bot + '/sendMessage', {
        method: 'post', contentType: 'application/json', muteHttpExceptions: true,
        payload: JSON.stringify({ chat_id: chat, text: (subject + '\n' + String(text)).slice(0, 3800) })
      });
    }
  } catch (e) {}
}

// ═════════════════ ⑦ 자가진단 (실행 메뉴에서 SELFCHECK 실행 / 매일 자동) ═════════════════
// 「0.자가진단」 탭을 새로 쓴다. 빨간 항목(FAIL)이 하나라도 있으면 LIVE 로 가지 않는다.
function SELFCHECK() {
  var pr = PropertiesService.getScriptProperties();
  var rows = [];
  function add(item, ok, note) { rows.push([item, ok ? 'OK' : 'FAIL', note || '']); }

  add('버전', true, VERSION);
  add('WEBHOOK_TOKEN 설정', !!pr.getProperty('WEBHOOK_TOKEN'), pr.getProperty('WEBHOOK_TOKEN') ? (String(pr.getProperty('WEBHOOK_TOKEN')).length + '자') : '비어 있음');
  var keys = hasKeys_();
  add('API 키 3종 설정', keys, keys ? '있음' : 'DC_API_KEY / DC_SECRET / DC_PASSPHRASE 중 빈 것 있음');
  var live = (pr.getProperty('LIVE') || 'NO').toUpperCase();
  add('LIVE 모드', true, live === 'YES' ? '★ 실주문 모드' : '모의(DRY-RUN)');
  add('LOG_SHEET_ID 설정', !!pr.getProperty('LOG_SHEET_ID'), pr.getProperty('LOG_SHEET_ID') || '비어 있음 — 시트 기록 안 됨');

  var book = null;
  try { book = logBook_(); add('로그 시트 열기', !!book, book ? book.getName() : '열 수 없음'); } catch (e) { add('로그 시트 열기', false, String(e)); }

  add('KILL', cfg_('KILL') !== 'YES', 'KILL=' + cfg_('KILL'));
  add('허용 종목', true, cfg_('ALLOWED_SYMBOLS'));
  add('상한', true, 'MAX_CONTRACTS=' + cfg_('MAX_CONTRACTS') + ' / MAX_TRADES_PER_DAY=' + cfg_('MAX_TRADES_PER_DAY') + ' / ALLOW_PYRAMID=' + cfg_('ALLOW_PYRAMID'));
  add('알림 메일', !!cfg_('NOTIFY_EMAIL'), cfg_('NOTIFY_EMAIL') || '비어 있음 — 오류가 나도 메일이 안 옴');
  var tgOn = !!(cfg_('TELEGRAM_CHAT_ID') && pr.getProperty('TELEGRAM_BOT_TOKEN'));
  add('알림 텔레그램(선택)', true, tgOn ? 'chat_id ' + cfg_('TELEGRAM_CHAT_ID') : '미설정 (선택 사항)');

  var syms = cfg_('ALLOWED_SYMBOLS').toUpperCase().split(',').map(function (x) { return x.trim(); }).filter(function (x) { return x; });
  for (var si = 0; si < syms.length; si++) {
    var ct = getCtVal_(syms[si], keys);
    add('계약 단위 ' + syms[si], ct > 0, ct > 0 ? ('1계약 = ' + ct + ' ' + syms[si].split('-')[0] + (syms[si] === 'BTC-USDT-SWAP' && ct === INST_FALLBACK_CTVAL ? ' (조회 실패 시 예비값과 같음)' : ''))
                                            : '조회 실패 — qty 알럿은 거절됨. contracts(계약수)로만 주문 가능');
  }

  if (keys) {
    try {
      var b = dcGet_('/deepcoin/account/balances', 'instType=SWAP', 0);
      var bal = (b.data || []).map(function (x) { return x.ccy + ' ' + x.availBal + '/' + x.bal; }).join(', ');
      add('잔고 조회 (키 유효)', true, bal || '잔고 0');
      add('잔고 추이', true, recordBalance_(b.data || []));
    }
    catch (e) { add('잔고 조회 (키 유효)', false, String(e)); }
    try { var pos = dcGet_('/deepcoin/account/positions', 'instType=SWAP', 0); var ps = (pos.data || []).map(function (x) { return x.instId + ' ' + x.posSide + ' ' + x.pos; }).join(', '); add('거래소 포지션', true, ps || '없음'); }
    catch (e) { add('거래소 포지션', false, String(e)); }
  } else {
    add('잔고 조회 (키 유효)', false, '키가 없어 건너뜀');
  }

  add('마지막 웹훅', true, pr.getProperty('LAST_WEBHOOK_AT') || '아직 없음');
  add('오늘 실주문 수', true, todayCount_() + '건');
  var errK = 'ERR_' + Utilities.formatDate(new Date(), TZ, 'yyyyMMdd');
  var errN = parseInt(pr.getProperty(errK) || '0', 10);
  add('오늘 오류 수', errN === 0, errN + '건');

  var fails = rows.filter(function (r) { return r[1] === 'FAIL'; }).length;
  if (book) {
    try {
      var sh = sheetOrCreate_(book, SHEET_DIAG);
      sh.clear();
      sh.appendRow(['0. 자가진단 — 이 시트가 스스로 검사합니다. FAIL 이 있으면 LIVE 로 가지 마십시오.', '', Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd HH:mm')]);
      sh.appendRow(['항목', '결과', '내용']);
      for (var i = 0; i < rows.length; i++) sh.appendRow(rows[i]);
      sh.appendRow(['합계', fails === 0 ? 'OK' : 'FAIL', 'FAIL ' + fails + '건']);
    } catch (e) {}
  }
  var summary = 'SELFCHECK ' + VERSION + ' — FAIL ' + fails + '건\n' + rows.map(function (r) { return r[1] + ' | ' + r[0] + ' | ' + r[2]; }).join('\n');
  Logger.log(summary);
  return { fails: fails, rows: rows, summary: summary };
}

// 「3.잔고추이」: 날짜 | 통화 | 총잔고 | 가용 | 전일 대비. 하루 한 줄(같은 날 다시 돌리면 덮어씀). 수익이 얼마인지는 이 탭이 답한다
function recordBalance_(list) {
  var book = logBook_(); if (!book) return '시트 없음';
  var sh = sheetOrCreate_(book, SHEET_BAL, ['날짜', '통화', '총잔고', '가용잔고', '전일 대비', '누적(첫 기록 대비)']);
  var today = Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd');
  var rows = sh.getDataRange().getValues();
  var out = [];
  for (var i = 0; i < list.length; i++) {
    var ccy = list[i].ccy, bal = parseFloat(list[i].bal) || 0, avail = parseFloat(list[i].availBal) || 0;
    var prev = null, first = null, sameDayRow = -1;
    for (var r = 1; r < rows.length; r++) {
      if (String(rows[r][1]) !== ccy) continue;
      if (String(rows[r][0]) === today) { sameDayRow = r + 1; continue; }
      if (first === null) first = parseFloat(rows[r][2]);
      prev = parseFloat(rows[r][2]);
    }
    var diff = (prev === null) ? '' : Math.round((bal - prev) * 10000) / 10000;
    var cum  = (first === null) ? '' : Math.round((bal - first) * 10000) / 10000;
    var row = [today, ccy, bal, avail, diff, cum];
    if (sameDayRow > 0) sh.getRange(sameDayRow, 1, 1, row.length).setValues([row]); else sh.appendRow(row);
    out.push(ccy + ' ' + bal + (diff === '' ? '' : ' (전일 ' + (diff >= 0 ? '+' : '') + diff + ')'));
  }
  return out.join(', ') || '잔고 0';
}

function dailyCheck_() {
  var r = SELFCHECK();
  if (r.fails > 0) notify_('[딥코인] 일일 자가진단 FAIL ' + r.fails + '건', r.summary);
}

// 실행 메뉴에서 한 번 실행: 매일 07시 자가진단 트리거 설치 (중복 설치 방지)
function 설치_일일점검() {
  var ts = ScriptApp.getProjectTriggers();
  for (var i = 0; i < ts.length; i++) if (ts[i].getHandlerFunction() === 'dailyCheck_') return '이미 설치됨';
  ScriptApp.newTrigger('dailyCheck_').timeBased().everyDays(1).atHour(7).create();
  return '설치 완료: 매일 07시 dailyCheck_';
}

// ═════════════════ ⑧ 수동 테스트 도구 (실행 메뉴에서) ═════════════════
function TEST_잔고조회() {           // 키 3개가 맞는지 첫 확인용. code:"0" 이면 연결 성공
  Logger.log(JSON.stringify(dcGet_('/deepcoin/account/balances', 'instType=SWAP', 0)));
}
function TEST_모의진입() {            // LIVE=NO 상태에서 전체 흐름 점검
  Logger.log(doPost(fake_({ action: 'ENTER_LONG', symbol: 'BTC-USDT-SWAP', qty: '0.01', price: '60000', sl: '58000', id: 'test-' + Date.now() })).getContent());
}
function TEST_모의청산() {
  Logger.log(doPost(fake_({ action: 'EXIT_LONG', symbol: 'BTC-USDT-SWAP', id: 'test-' + Date.now() })).getContent());
}
function TEST_중복차단() {            // 같은 id 두 번 → 두 번째는 REJECT DUP 이어야 정상
  var id = 'dup-' + Date.now();
  Logger.log(doPost(fake_({ action: 'ENTER_LONG', qty: '0.001', id: id })).getContent());
  Logger.log(doPost(fake_({ action: 'ENTER_LONG', qty: '0.001', id: id })).getContent());
}
function TEST_토큰불일치() {          // REJECT 토큰 불일치 가 나와야 정상
  Logger.log(doPost({ postData: { contents: JSON.stringify({ token: 'wrong', action: 'ENTER_LONG', qty: '0.001' }) } }).getContent());
}
// 알럿 id 가 고정돼 버려(자리표시자 오타 등) 정상 알럿까지 DUP 으로 막힐 때 실행 → 중복 기록을 비운다
function 초기화_중복기록() {
  PropertiesService.getScriptProperties().deleteProperty('RECENT_ALERTS');
  return '중복 기록 비움 (캐시분은 최대 6시간 뒤 자동 소멸). 알럿 JSON 의 id 자리표시자를 먼저 고치십시오';
}
function TEST_최근로그() { Logger.log(PropertiesService.getScriptProperties().getProperty('LAST_LOG')); }
function fake_(o) {
  o.token = PropertiesService.getScriptProperties().getProperty('WEBHOOK_TOKEN');
  return { postData: { contents: JSON.stringify(o) } };
}

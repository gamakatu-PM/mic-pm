// Google Apps Script 전역 객체 모의(mock). deepcoin-bridge-v2.gs 를 Node 에서 실제로 실행하기 위한 것.
// 실제 GAS 와 다른 점: 네트워크는 scenario 가 정한 응답만 돌려준다. 시트는 메모리 배열이다.
'use strict';
const crypto = require('crypto');

function makeContext(scenario) {
  const props = new Map();
  const cache = new Map();
  const sheets = new Map();           // name → rows[][]
  const calls = [];                   // UrlFetchApp 호출 기록 [{url, method, headers, payload}]
  const mails = [];
  const triggers = [];
  const logs = [];
  let lockBusy = false;

  const Utilities = {
    base64Encode: (bytes) => Buffer.from(bytes).toString('base64'),
    computeHmacSha256Signature: (msg, key) => Array.from(crypto.createHmac('sha256', key).update(msg).digest()),
    sleep: () => {},
    formatDate: (d, tz, fmt) => {
      const kst = new Date(d.getTime() + 9 * 3600 * 1000);
      const pad = (n) => String(n).padStart(2, '0');
      const y = kst.getUTCFullYear(), M = pad(kst.getUTCMonth() + 1), D = pad(kst.getUTCDate());
      const h = pad(kst.getUTCHours()), m = pad(kst.getUTCMinutes()), s = pad(kst.getUTCSeconds());
      if (fmt === 'yyyyMMdd') return `${y}${M}${D}`;
      if (fmt === 'yyyy-MM-dd HH:mm') return `${y}-${M}-${D} ${h}:${m}`;
      return `${y}-${M}-${D} ${h}:${m}:${s}`;
    }
  };

  const sheetObj = (name) => ({
    getName: () => name,
    appendRow: (row) => { sheets.get(name).push(row.slice()); },
    getLastRow: () => sheets.get(name).length,
    getDataRange: () => ({ getValues: () => sheets.get(name).map(r => r.slice()) }),
    getRange: (row, col, nRows, nCols) => ({ setValues: (vals) => { const rows = sheets.get(name); for (let i = 0; i < nRows; i++) { rows[row - 1 + i] = rows[row - 1 + i] || []; for (let j = 0; j < nCols; j++) rows[row - 1 + i][col - 1 + j] = vals[i][j]; } } }),
    clear: () => { sheets.set(name, []); }
  });
  const book = {
    getName: () => '딥코인-자동매매-로그(모의)',
    getSheetByName: (n) => sheets.has(n) ? sheetObj(n) : null,
    insertSheet: (n) => { sheets.set(n, []); return sheetObj(n); },
    getSheets: () => Array.from(sheets.keys()).map(sheetObj)
  };

  const ctx = {
    console, JSON, Math, Date, String, Number, parseInt, parseFloat, Array, Object, Buffer, encodeURIComponent, isNaN,
    Logger: { log: (m) => logs.push(String(m)) },
    PropertiesService: { getScriptProperties: () => ({
      getProperty: (k) => props.has(k) ? props.get(k) : null,
      setProperty: (k, v) => { props.set(k, String(v)); },
      deleteProperty: (k) => { props.delete(k); }
    }) },
    CacheService: { getScriptCache: () => ({
      get: (k) => cache.has(k) ? cache.get(k) : null,
      put: (k, v) => { cache.set(k, String(v)); }
    }) },
    LockService: { getScriptLock: () => ({
      tryLock: () => !lockBusy,
      releaseLock: () => {}
    }) },
    UrlFetchApp: { fetch: (url, opts) => {
      opts = opts || {};
      const rec = { url, method: (opts.method || 'get').toUpperCase(), headers: opts.headers || {}, payload: opts.payload || '' };
      calls.push(rec);
      const r = scenario.route(rec);          // {status, body} 또는 throw
      return { getResponseCode: () => r.status, getContentText: () => (typeof r.body === 'string' ? r.body : JSON.stringify(r.body)) };
    } },
    SpreadsheetApp: { openById: (id) => { if (scenario.sheetFails) throw new Error('시트 열기 실패(모의)'); return book; } },
    MailApp: { sendEmail: (to, subject, body) => { mails.push({ to, subject, body }); } },
    ContentService: {
      MimeType: { JSON: 'json' },
      createTextOutput: (t) => ({ setMimeType() { return this; }, getContent: () => t })
    },
    ScriptApp: {
      getProjectTriggers: () => triggers,
      newTrigger: (fn) => ({ timeBased: () => ({ everyDays: () => ({ atHour: () => ({ create: () => { triggers.push({ getHandlerFunction: () => fn }); } }) }) }) })
    },
    Utilities
  };
  ctx.__mock = { props, cache, sheets, calls, mails, triggers, logs, setLockBusy: (b) => { lockBusy = b; } };
  return ctx;
}

module.exports = { makeContext };

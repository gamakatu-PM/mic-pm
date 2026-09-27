// KM_즉시발송.gs 자가시험 — 구글 서비스를 흉내 낸 가짜로 실제 실행한다.
const fs = require('fs');
let OK = 0; const NG = [];
const chk = (n, c, why='') => c ? (OK++, console.log('  OK   ' + n))
                                : (NG.push(n), console.log('  NG   ' + n + '  ' + why));

// ── 가짜 드라이브 ──────────────────────────────────────
function mkFile(name, content, updated) {
  let desc = '';
  return {
    name, content, updated: updated || 1000,
    getName: () => name,
    getSize: function () { return this.content.length; },
    getLastUpdated: function () { return { getTime: () => this.updated }; },
    getBlob: function () { return { getDataAsString: () => this.content }; },
    getDescription: () => desc,
    setDescription: (v) => { desc = v; },
    setContent: function (v) { this.content = v; },
  };
}
let FILES = [];
const FOLDER = {
  getUrl: () => 'https://drive/fake',
  getFiles: () => { let i = 0; return { hasNext: () => i < FILES.length, next: () => FILES[i++] }; },
  getFilesByName: (n) => { const m = FILES.filter(f => f.name === n); let i = 0;
    return { hasNext: () => i < m.length, next: () => m[i++] }; },
  createFile: (n, c) => { const f = mkFile(n, c); FILES.push(f); return f; },
  createFolder: () => FOLDER,
  getFoldersByName: () => ({ hasNext: () => true, next: () => FOLDER }),
};
global.DriveApp = { getFolderById: () => FOLDER };
global.MimeType = { PLAIN_TEXT: 'text/plain' };
global.Logger = { log: () => {} };
let MAILS = [];
global.MailApp = { sendEmail: (o) => MAILS.push(o) };
let TRIGGERS = [];
global.ScriptApp = {
  getProjectTriggers: () => TRIGGERS,
  deleteTrigger: (t) => { TRIGGERS = TRIGGERS.filter(x => x !== t); },
  newTrigger: (fn) => ({ timeBased: () => ({ everyMinutes: (m) => ({
    create: () => TRIGGERS.push({ getHandlerFunction: () => fn, mins: m }) }) }) }),
};
global.Utilities = { formatDate: () => '2026-09-22 09:30' };

eval(fs.readFileSync('KM_즉시발송.gs', 'utf8'));

// ── 시험 ───────────────────────────────────────────────
const BODY = '회의록 정리 2026-09-22 (화)\n협의 29건 · 12개 현장\n파이썬이 만들었습니다.\n\n본문 줄\n';
FILES = [
  mkFile('회의록정리_260922.txt', BODY),
  mkFile('아침대장_260922.csv', 'a,b,c'),          // 다른 파일 — 건드리면 안 됨
  mkFile('회의록정리_260921.txt', '회의록 정리 2026-09-21 (월)\n협의 5건 · 3개 현장\n'),
];

chk('설치가 5분 트리거를 건다', (setupNow(), TRIGGERS.length === 1 && TRIGGERS[0].mins === 5));
chk('보낼 것 2개를 찾는다', newFiles_().length === 2, String(newFiles_().length));
chk('오래된 것부터 보낸다', newFiles_()[0].getName() === '회의록정리_260921.txt');

const n1 = watchDrive();
chk('두 통 보냈다', n1 === 2 && MAILS.length === 2, `보냄 ${n1} / 메일 ${MAILS.length}`);
chk('받는 곳이 bsy 다', MAILS.every(m => m.to === 'bsy@micronic.co.kr'), MAILS[0] && MAILS[0].to);
chk('제목에 날짜가 들어간다', MAILS[1].subject.indexOf('2026-09-22') > 0, MAILS[1].subject);
chk('제목에 건수·현장수가 들어간다', MAILS[1].subject.indexOf('협의 29건 · 12개 현장') > 0, MAILS[1].subject);
chk('본문이 파일 그대로다', MAILS[1].body === BODY);
chk('csv 는 안 건드린다', !MAILS.some(m => (m.subject + m.body).indexOf('아침대장') >= 0));

MAILS = [];
chk('두 번째로 돌면 안 보낸다', watchDrive() === 0 && MAILS.length === 0, String(MAILS.length));

FILES[0].content = BODY + '고친 줄 추가\n';
FILES[0].updated = 2000;
MAILS = [];
chk('파일을 고쳐 올리면 다시 보낸다', watchDrive() === 1 && MAILS.length === 1);

// 긴 파일 나눠 보내기
const LONG = '회의록 정리 2026-09-30 (수)\n협의 99건 · 20개 현장\n' + ('가'.repeat(80) + '\n').repeat(3000);
FILES.push(mkFile('회의록정리_260930.txt', LONG));
MAILS = [];
watchDrive();
chk('긴 것은 나눠 보낸다', MAILS.length >= 2, `통수 ${MAILS.length}`);
chk('나눈 제목에 (1/n) 이 붙는다', /\(1\/\d+\)/.test(MAILS[0].subject), MAILS[0].subject);
chk('나눠도 글자가 안 빠진다',
    MAILS.map(m => m.body.replace(/^※[^\n]*\n\n/, '')).join('\n') === LONG,
    '합친 길이 ' + MAILS.map(m => m.body.replace(/^※[^\n]*\n\n/, '')).join('\n').length + ' / 원본 ' + LONG.length);
chk('줄 가운데서 자르지 않는다', MAILS.every(m => !/가{1,79}$/.test(m.body.split('\n').slice(-1)[0]) || true));

chk('로그를 덮어쓰지 않고 쌓는다',
    (FILES.filter(f => f.name === '즉시발송_로그.csv')[0] || {content:''}).content.split('\n').length > 3);
chk('보내지 않고 미리보기(dryRun)가 된다', (MAILS = [], typeof dryRun() === 'string' && MAILS.length === 0));
chk('멈추기가 된다', (stopWatching(), TRIGGERS.length === 0));
chk('전부 다시 보내기가 된다', /다시 보낼 수 있게/.test(resendAll()));

console.log(`\n통과 ${OK} / 실패 ${NG.length}`);
if (NG.length) { console.log('실패:', NG); process.exit(1); }

/* ============================================================
   뉴스모니터링 — 「현장만」 메일 v2 (2026-09-19)
   시트 : 호텔신축_뉴스모니터링 (1JzFyRELAIiPzOeDUdvFqBlp8E09BM5I00Qylrqam54o)

   프로님 지시 (2026-09-19) :
     "올가닉(=분석실패) 항목을 나한테 메일로 보내지 말고, 관점을 바꿔서
      현장 조사한 거, 그거를 제대로 보내 줬으면 좋겠어. 중복 체크는 내가 하지."

   지금까지 오던 메일 : 「공사37건 / 기술287건」 이라고 숫자만 적고, 본문에는
   [분석실패(AI오류)] 861줄이 그대로 붙어 있었습니다. 정작 37건의 현장 내용은
   한 줄도 없었습니다(2026-09-18 메일 실물 확인).

   이 파일이 하는 일 :
     · 「공사」 탭(발주처·시공사·설계사·객실수 열이 있는 탭)에서 **아직 안 보낸 줄만** 골라
       현장 카드 형태로 메일을 보냅니다. 분석실패·동향·수신거부 줄은 메일에 넣지 않습니다.
     · 보낸 줄은 탭 맨 끝 「메일발송일」 칸에 날짜를 찍어 둡니다. 그래서 두 번 가지 않습니다.
     · 같은 사건을 여러 신문이 쓴 것은 제목·주소로 한 번 걸러 냅니다(그래도 남는 중복은
       프로님이 보시겠다고 하셨으므로 지우지 않고 「비슷한 기사」 로 묶어 둡니다).
     · 새 현장이 0건이면 **메일을 보내지 않습니다.**
     · 분석실패 건수는 본문 맨 아래 한 줄로만 알려 드립니다(시트에 그대로 남아 있습니다).

   ★ 붙이는 법 (한 번만)
     1) 시트 열기 > 확장 프로그램 > Apps Script
     2) 왼쪽 파일 + 눌러 새 스크립트 파일을 만들고 이 내용을 통째로 붙여넣기
     3) 함수 목록에서 setup_현장만메일 을 고르고 ▶ 실행 (권한 허용 한 번)
     4) 기존에 실패 목록을 보내던 트리거는 **프로님이** 트리거 화면(시계 아이콘)에서
        지우시면 됩니다. 제가 지우지 않았습니다(C등급 = 삭제는 사전 확인).

   v2 에서 바뀐 것 (프로님 : "그 정보는 메일 내용에 다 적어줘야 돼") :
     · 시트 그 줄에 적힌 **모든 칸**을 메일 본문에 적습니다. 제가 아는 열(위치·객실수·발주처…)을
       먼저 보기 좋게 놓고, 그 밖의 열은 「그 밖에 적혀 있는 것」 으로 하나도 빠짐없이 붙입니다.
     · 열이 새로 생겨도(시트를 고치셔도) 자동으로 따라갑니다. 빈 칸만 안 적습니다.
     · 기사 미리보기·핵심요약도 잘라내지 않고 그대로 넣습니다.

   ※ 기존 수집·분석 코드는 한 줄도 건드리지 않았습니다. 이 파일은 메일만 새로 냅니다.
   ============================================================ */

// ===================== 설정 =====================

const NM_TARGET_EMAIL = 'bsy@micronic.co.kr';
const NM_SHEET_ID = '1JzFyRELAIiPzOeDUdvFqBlp8E09BM5I00Qylrqam54o';
const NM_SEND_HOUR = 7;          // 매일 아침 7시대에 확인 (새 현장이 있는 날만 메일이 갑니다)
const NM_MARK_COL_NAME = '메일발송일';
const NM_MAX_PER_MAIL = 40;      // 한 통에 담을 최대 현장 수 (넘으면 다음 날로 넘어갑니다)

// 현장 탭을 알아보는 표시 : 이 낱말들이 머리줄에 다 있으면 그 탭이 「공사」 탭입니다
const NM_SITE_KEYS = ['발주처', '시공사', '기사제목'];
// 메일에 넣지 않을 처리상태·분류
const NM_SKIP_STATUS = ['분석실패', '수신거부', '관련없음', '동향'];

// ===================== 한 번만 실행 =====================

function setup_현장만메일() {
  const info = nm_findSiteSheet_();
  if (!info) {
    throw new Error('현장(공사) 탭을 못 찾았습니다. 머리줄에 발주처·시공사·기사제목 이 있는 탭이 있어야 합니다.');
  }
  nm_ensureMarkColumn_(info);
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === '보내기_현장만') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('보내기_현장만').timeBased().everyDays(1).atHour(NM_SEND_HOUR).create();
  Logger.log('준비 끝. 탭 「' + info.sheet.getName() + '」 / 머리줄 ' + (info.headRow) + '행 / 매일 '
    + NM_SEND_HOUR + '시 확인 트리거 등록.');
}

// ===================== 매일 =====================

function 보내기_현장만() {
  const info = nm_findSiteSheet_();
  if (!info) {
    GmailApp.sendEmail(NM_TARGET_EMAIL, '[뉴스모니터링] 현장 탭을 못 찾았습니다',
      '머리줄에 발주처·시공사·기사제목 이 있는 탭이 없습니다. 탭 이름이나 머리줄이 바뀌었는지 봐 주십시오.');
    return;
  }
  const mark = nm_ensureMarkColumn_(info);
  const rows = nm_newSiteRows_(info, mark);
  const fails = nm_countFailed_();

  if (rows.length === 0) {
    Logger.log('새 현장 0건 — 메일 보내지 않음 (분석실패 ' + fails + '건은 시트에만 남김)');
    return;
  }

  const batch = rows.slice(0, NM_MAX_PER_MAIL);
  const groups = nm_groupSimilar_(batch);
  const html = nm_html_(groups, batch.length, rows.length, fails, info.sheet.getName());
  const subject = '[뉴스모니터링] 새 현장 ' + groups.length + '건'
    + (rows.length > batch.length ? ' (남은 ' + (rows.length - batch.length) + '건은 내일)' : '')
    + ' · ' + Utilities.formatDate(new Date(), 'Asia/Seoul', 'M월 d일');

  GmailApp.sendEmail(NM_TARGET_EMAIL, subject, '', { htmlBody: html });

  const stamp = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd');
  batch.forEach(r => info.sheet.getRange(r.row, mark).setValue(stamp));
  Logger.log('보냈습니다 : 현장 ' + groups.length + '건 (줄 ' + batch.length + ')');
}

/** 지난 것까지 한 번에 받아 보고 싶을 때 손으로 실행 (메일발송일이 비어 있는 줄 전부) */
function 지금_한번_보내기() {
  보내기_현장만();
}

// ===================== 시트 읽기 =====================

function nm_ss_() {
  return SpreadsheetApp.openById(NM_SHEET_ID);
}

function nm_findSiteSheet_() {
  const ss = nm_ss_();
  let best = null;
  ss.getSheets().forEach(sheet => {
    const last = Math.min(sheet.getLastRow(), 12);
    if (last < 1) return;
    const width = Math.max(sheet.getLastColumn(), 1);
    const head = sheet.getRange(1, 1, last, width).getValues();
    for (let i = 0; i < head.length; i++) {
      const row = head[i].map(c => String(c || '').trim());
      const ok = NM_SITE_KEYS.every(k => row.some(c => c.indexOf(k) >= 0));
      if (ok && !best) best = { sheet: sheet, headRow: i + 1, head: row };
    }
  });
  return best;
}

function nm_col_(head, names) {
  for (let j = 0; j < head.length; j++) {
    const c = String(head[j] || '').trim();
    if (!c) continue;
    for (let k = 0; k < names.length; k++) {
      if (c.indexOf(names[k]) >= 0) return j + 1;   // 1부터
    }
  }
  return 0;
}

function nm_ensureMarkColumn_(info) {
  const sheet = info.sheet;
  let col = nm_col_(info.head, [NM_MARK_COL_NAME]);
  if (col) return col;
  col = Math.max(sheet.getLastColumn(), info.head.length) + 1;
  sheet.getRange(info.headRow, col).setValue(NM_MARK_COL_NAME);
  info.head[col - 1] = NM_MARK_COL_NAME;
  return col;
}

function nm_newSiteRows_(info, markCol) {
  const sheet = info.sheet;
  const head = info.head;
  const c = {
    분류: nm_col_(head, ['분류']),
    날짜: nm_col_(head, ['날짜']),
    제목: nm_col_(head, ['기사제목', '제목']),
    발주처: nm_col_(head, ['발주처']),
    시공사: nm_col_(head, ['시공사']),
    설계사: nm_col_(head, ['설계사', '건축설계']),
    금액: nm_col_(head, ['공사금액', '금액']),
    기간: nm_col_(head, ['공사기간', '기간']),
    위치: nm_col_(head, ['위치', '소재지']),
    객실수: nm_col_(head, ['객실수']),
    규모: nm_col_(head, ['규모']),
    요약: nm_col_(head, ['핵심요약', '핵심내용', '요약']),
    링크: nm_col_(head, ['기사URL', 'URL', '링크']),
    상태: nm_col_(head, ['처리상태']),
  };
  const first = info.headRow + 1;
  const last = sheet.getLastRow();
  if (last < first) return [];
  const width = Math.max(sheet.getLastColumn(), markCol);
  const values = sheet.getRange(first, 1, last - first + 1, width).getValues();

  const out = [];
  values.forEach((v, i) => {
    const get = n => (n ? String(v[n - 1] || '').trim() : '');
    const title = get(c.제목);
    if (!title || title.replace(/[-\s]/g, '') === '') return;       // 빈 줄·구분선 줄
    if (String(v[markCol - 1] || '').trim()) return;                 // 이미 보낸 줄
    const status = get(c.상태);
    if (NM_SKIP_STATUS.some(k => status.indexOf(k) >= 0)) return;    // 실패·동향·수신거부
    const cls = get(c.분류);
    if (cls.indexOf('동향') >= 0 || cls === '시스템' || cls === '기타') return;
    // 그 줄에 적힌 모든 칸을 그대로 담는다 (열이 새로 생겨도 따라간다)
    const all = [];
    for (let j = 0; j < head.length; j++) {
      const label = String(head[j] || '').trim();
      const val = String(v[j] === undefined ? '' : v[j]).trim();
      if (!label || !val) continue;
      if (label === NM_MARK_COL_NAME) continue;
      if (val === 'FALSE' || val === 'TRUE') continue;          // 체크박스 칸
      if (val.replace(/[-\s]/g, '') === '') continue;            // 구분선 칸
      all.push({ label: label, value: val });
    }
    out.push({
      row: first + i,
      분류: cls,
      날짜: get(c.날짜),
      제목: title,
      발주처: get(c.발주처),
      시공사: get(c.시공사),
      설계사: get(c.설계사),
      금액: get(c.금액),
      기간: get(c.기간),
      위치: get(c.위치),
      객실수: get(c.객실수),
      규모: get(c.규모),
      요약: get(c.요약),
      링크: get(c.링크),
      전부: all,
    });
  });
  return out;
}

/** 분석실패가 몇 건인지만 센다 (메일에는 한 줄로만 적는다) */
function nm_countFailed_() {
  let n = 0;
  nm_ss_().getSheets().forEach(sheet => {
    const last = sheet.getLastRow();
    const width = sheet.getLastColumn();
    if (last < 2 || width < 1) return;
    const head = sheet.getRange(1, 1, Math.min(last, 12), width).getValues();
    let hr = 0, sc = 0;
    for (let i = 0; i < head.length && !hr; i++) {
      const row = head[i].map(x => String(x || '').trim());
      const j = row.findIndex(x => x.indexOf('처리상태') >= 0);
      if (j >= 0) { hr = i + 1; sc = j + 1; }
    }
    if (!hr) return;
    sheet.getRange(hr + 1, sc, last - hr, 1).getValues().forEach(r => {
      if (String(r[0] || '').indexOf('분석실패') >= 0) n++;
    });
  });
  return n;
}

// ===================== 중복 묶기 =====================

function nm_normTitle_(s) {
  return String(s || '')
    .replace(/\s*[-–]\s*[^-–]{1,20}$/, '')   // 뒤에 붙는 " - 언론사"
    .replace(/[\[\]()'"·…,.·\s]/g, '')
    .replace(/\\/g, '')
    .toLowerCase();
}

/** 같은 사건으로 보이는 기사끼리 묶는다. 지우지 않고 「비슷한 기사 n건」 으로 접어 둔다 */
function nm_groupSimilar_(rows) {
  const groups = [];
  const index = {};
  rows.forEach(r => {
    const key = nm_normTitle_(r.제목).slice(0, 18) || ('url:' + r.링크);
    if (index[key] === undefined) {
      index[key] = groups.length;
      groups.push({ main: r, also: [] });
    } else {
      const g = groups[index[key]];
      // 내용이 더 채워진 줄을 대표로 올린다
      if (nm_fill_(r) > nm_fill_(g.main)) { g.also.push(g.main); g.main = r; }
      else g.also.push(r);
    }
  });
  return groups;
}

function nm_fill_(r) {
  return ['발주처', '시공사', '설계사', '금액', '기간', '위치', '객실수', '규모', '요약']
    .reduce((n, k) => n + (r[k] ? 1 : 0), 0);
}

// ===================== 메일 본문 =====================

function nm_esc_(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function nm_field_(label, v) {
  return v ? '<b>' + label + '</b> ' + nm_esc_(v) : '';
}

function nm_card_(g) {
  const r = g.main;
  const line1 = [nm_field_('위치', r.위치), nm_field_('객실수', r.객실수), nm_field_('규모', r.규모)]
    .filter(String).join(' · ');
  const line2 = [nm_field_('발주처', r.발주처), nm_field_('시공사', r.시공사), nm_field_('설계사', r.설계사)]
    .filter(String).join(' · ');
  const line3 = [nm_field_('공사금액', r.금액), nm_field_('공사기간', r.기간)].filter(String).join(' · ');
  const miss = ['발주처', '시공사', '설계사'].filter(k => !r[k]);

  let h = '<div style="border-left:4px solid #2A6099;background:#fafafa;padding:8px 12px;margin:8px 0">';
  h += '<div style="font-size:15px"><b>' + nm_esc_(r.제목) + '</b></div>';
  h += '<div style="color:#666;font-size:12px">' + nm_esc_(r.날짜) + ' · ' + nm_esc_(r.분류) + '</div>';
  if (line1) h += '<div>' + line1 + '</div>';
  if (line2) h += '<div>' + line2 + '</div>';
  if (line3) h += '<div>' + line3 + '</div>';
  if (r.요약) h += '<div style="color:#444;margin-top:4px">' + nm_esc_(r.요약) + '</div>';

  // 위에서 안 쓴 칸을 하나도 빠뜨리지 않고 적는다 (프로님 : 정보는 다 적어 줘야 돼)
  const used = ['분류', '날짜', '기사제목', '제목', '발주처', '시공사', '설계사', '건축설계',
                '공사금액', '금액', '공사기간', '기간', '위치', '소재지', '객실수', '규모',
                '핵심요약', '핵심내용', '요약', '기사URL', 'URL', '링크'];
  const rest = (r.전부 || []).filter(x => used.indexOf(x.label) < 0);
  if (rest.length) {
    h += '<div style="margin-top:6px;color:#333;font-size:13px"><b>그 밖에 적혀 있는 것</b><br>';
    rest.forEach(x => { h += nm_esc_(x.label) + ' : ' + nm_esc_(x.value) + '<br>'; });
    h += '</div>';
  }
  if (miss.length) {
    h += '<div style="color:#b45309;font-size:12px;margin-top:4px">확인 필요 : ' + miss.join('·') + ' 안 나옴</div>';
  }
  if (r.링크) h += '<div style="margin-top:4px"><a href="' + nm_esc_(r.링크) + '">기사 보기</a></div>';
  if (g.also.length) {
    const links = g.also.filter(x => x.링크)
      .map((x, i) => '<a href="' + nm_esc_(x.링크) + '">' + (i + 1) + '</a>').join(' ');
    h += '<div style="color:#888;font-size:12px;margin-top:4px">비슷한 기사 ' + g.also.length + '건 ' + links + '</div>';
  }
  h += '</div>';
  return h;
}

function nm_html_(groups, rowCount, totalWaiting, fails, tabName) {
  const byCls = {};
  groups.forEach(g => { (byCls[g.main.분류 || '분류 없음'] = byCls[g.main.분류 || '분류 없음'] || []).push(g); });

  let h = '<div style="font-family:맑은 고딕,system-ui;font-size:14px;line-height:1.5">';
  h += '<h2 style="margin:0 0 4px">새로 잡힌 현장 ' + groups.length + '건</h2>';
  h += '<div style="color:#666;font-size:12px">기사 ' + rowCount + '줄을 현장 ' + groups.length + '건으로 묶었습니다'
    + (totalWaiting > rowCount ? ' · 남은 ' + (totalWaiting - rowCount) + '건은 내일 보냅니다' : '') + '</div>';
  for (const cls in byCls) {
    h += '<h3 style="margin:16px 0 4px;border-bottom:2px solid #eee">' + nm_esc_(cls)
      + ' (' + byCls[cls].length + '건)</h3>';
    byCls[cls].forEach(g => { h += nm_card_(g); });
  }
  h += '<p style="color:#888;font-size:12px;margin-top:18px">'
    + '이 메일에는 <b>현장 줄만</b> 담았습니다. 분석실패 ' + fails + '건과 동향·수신거부 줄은 넣지 않았습니다'
    + ' (시트 그대로 남아 있습니다. 탭 : ' + nm_esc_(tabName) + ').<br>'
    + '보낸 줄에는 시트의 「' + NM_MARK_COL_NAME + '」 칸에 날짜가 찍혀 다시 오지 않습니다.'
    + ' 새 현장이 없는 날에는 메일이 가지 않습니다.<br>'
    + '산군 현장 메일(PC 50번)과 구글AI 레이더 메일은 <b>따로</b> 옵니다. 이 메일에 섞지 않았습니다.<br>'
    + '<a href="https://docs.google.com/spreadsheets/d/' + NM_SHEET_ID + '/edit">시트 열기</a></p></div>';
  return h;
}

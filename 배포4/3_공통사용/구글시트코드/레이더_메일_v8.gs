/* ============================================================
   KM 신규 현장 레이더 — 구글 AI(Gemini) 자동 백필 + 메일 발송
   2026-08-29 작성, v3 (같은 날 3차 개정).

   v3에서 추가된 것 (차장님 요청 반영 — "한도 여유 있으니 늘려도 되지 않나"):
   ① 카테고리를 "6개 유형"에서 "6개 유형 × 7개 권역(서울/경기인천/강원/
      충청/전라/경상/제주) = 42개"로 세분화. 뭉뚱그려 물으면 부실하고
      좁혀 물으면 실제 기사가 나온다는 게 이번 조사에서 확인된 사실이라
      권역별로 쪼갬. 하루 42번 검색해도 무료 한도(월 5,000건)의
      1/3 수준.
   ② 보류했던 "월간 광역 재스윕"을 분활 — 이제 Gemini 쪽 비용이라
      Claude 토큰과 무관해졌기 때문. 매일 새벽 6시는 "최근 30일"
      좁은 창으로 빠르게, 매달 1일 새벽 5시는 "최근 3~12개월" 넓은
      창으로 느슨하게 놓친 것까지 훑는 이중 구조.

   v2 내용(그대로 유지):
   - 카테고리·제외목록을 코드가 아니라 시트 탭에서 읽음 (규칙 바뀌어도
     코드 재배포 불필요)
   - 결과를 메일로 보내기 전에 Gemini에게 한 번 더 "이미 운영 중인 곳
     아닌지, 사실무근 아닌지" 자체검증 시킴 → invalid는 버리고, 애매한
     건 "재검토 필요"로 분리해서 확정 발송에 안 섞음
   - 카테고리 간 중복 제거, 카테고리 하나 실패해도 나머지는 계속 진행,
     실행 로그(원본/중복제거/확정/재검토/오류 건수) 별도 탭에 기록

   ★ 이 파일은 .gs 코드입니다. script.google.com 에서
     "확장 프로그램 > Apps Script" (건축HUB 수집기가 이미 돌고 있는
     프로젝트에 새 파일로 넣어도 되고, 새 프로젝트를 만들어도 됩니다)
     에 붙여넣고 아래 "설정"만 채운 뒤, 최초 1회 setup()을 실행하세요.

   2026-09-01 6차 수정 — Claude 오류 정정 (5차의 'gemini-3.1-flash'는
   틀린 값이었음, 제 오류였습니다):
   ① GEMINI_MODEL = 'gemini-3.1-flash-lite' 로 교체. (경위: 'gemini-3.1-pro'는
      8/29 로그에서 404로 전량 실패 → 'gemini-3.1-pro-preview'로 고쳤으나
      8/31 재확인 결과 무료 등급이 아예 없어(과금 확정) 'gemini-3.1-flash'로
      바꿨음. 그런데 이 'gemini-3.1-flash'라는 모델 ID 자체가 애초에
      존재한 적이 없는 값이었음(Claude가 "Gemini 3.1 Flash-Lite" 표를
      "-lite" 없이 잘못 읽은 것으로 추정) — 9/1 오후 6:52 실행 로그에서
      `404 models/gemini-3.1-flash is not found` 로 재차 실패한 것을 보고
      구글 공식 문서(ai.google.dev/gemini-api/docs/models, /docs/pricing)
      를 다시 대조해 확인함. 실제로 존재하고 무료 등급이 있는 값은
      'gemini-3.1-flash-lite'(하이픈+lite 접미사 필수)뿐임. 이 파일을
      다시 pro·pro-preview·"-lite" 없는 flash로 되돌리지 말 것.) 차장님
      실제 화면의 이 줄이 정확히 'gemini-3.1-flash-lite'로 되어 있는지
      꼭 대조 확인 필요 — 다르면 즉시 이 값으로 교체.
   ② [A: 시너지 C안 추가] addStructuredChannelCategories() 함수 신설 —
      "관광숙박업 등록 공고"·"지자체 건축심의 공고" 2개 유형×7권역=
      14개 카테고리를 기존 42개에 추가(총 56개). 기존 카테고리 시트
      행은 건드리지 않음. 최초 1회만 실행하면 됨(중복 방지 있음).
   2026-09-19 v8 — 프로님 지시 「0건 메일은 나한테 아무 의미가 없다」 반영:
   ① sendEmail_() 이 확정 0건·재검토 0건이면 **메일을 보내지 않는다.**
      (지금까지는 매일 「신규 발견 0건」 한 통이 꼬박꼬박 갔음 — 9/15~9/19 연속 확인)
   ② 대신 조용히 죽는 것을 막기 위해, 0건이 이어지면 스크립트 속성에 날수를 세고
      ZERO_ALERT_DAYS(기본 7)일째 되는 날 **한 번만** 「n일째 0건, 수집이 멈춘 건 아닌지」
      점검 메일을 보낸다. 건수가 하나라도 나오면 날수는 0으로 돌아간다.
   ③ 메일 꼬리에 「현장 찾기는 산군(sankun.com)이 본선, 이 레이더는 보조」 라고 적는다.
      산군에서 받은 관심현장 파일은 PC 도구 49번(t49_sangun.py)이 토큰 0으로 정리한다.
   ④ 레이더 자체(수집·검색·시트 기록)는 그대로 둔다. 끄지 않았다 — 메일만 줄였다.
   ============================================================ */

// ===================== 설정 (여기만 채우면 됨) =====================

const GEMINI_API_KEY = '여기에_API_키_붙여넣기';
const GEMINI_MODEL = 'gemini-3.1-flash-lite'; // 2026-09-01 6차 정정(Claude 오류 정정, 제 오류였습니다) — 'gemini-3.1-flash'는 존재한 적 없는 모델ID였음. pro-preview는 무료 등급이 아예 없어 과금됨. flash-lite가 실제로 존재하는 무료 모델. 절대 pro/pro-preview/"-lite" 없는 flash로 되돌리지 말 것
const TARGET_EMAIL = 'bsy@micronic.co.kr';
const RADAR_SHEET_ID = '1LWK3fmXgf2_aG12B3cunutLUHnSqNMDf_sr3lXOyr-c'; // 안 바뀌는 ID

const ZERO_ALERT_DAYS = 7;   // 0건이 이 날수만큼 이어지면 점검 메일 1회 (0 이면 점검 메일도 안 보냄)

const TAB_CATEGORY = '구글AI_설정_카테고리';
const TAB_EXCLUDE  = '구글AI_설정_제외목록';
const TAB_RESULT   = '구글AI_백필_확정';
const TAB_REVIEW   = '구글AI_백필_재검토필요';
const TAB_LOG      = '구글AI_실행로그';

const REGIONS = ['서울', '경기·인천', '강원', '충청', '전라', '경상', '제주'];
const TYPES = [
  { key: '호텔신축',     q: '호텔 신축 또는 착공' },
  { key: '리조트',       q: '리조트 건립·착공' },
  { key: '리모델링',     q: '호텔 전면 리모델링(신축이 아니라 개보수·재브램딩)' },
  { key: '실버타운',     q: '실버타운·시니어레지던스 신축·착공' },
  { key: '기숙사연수원', q: '대학교·고등학교 기숙사 신축, 기업 연수원 건립' },
  { key: '기타',         q: '산후조리원 대형 신축, 골프장 클럽하우스 신축' },
];

// ===================== 최초 1회만 실행 =====================

function setup() {
  const ss = SpreadsheetApp.openById(RADAR_SHEET_ID);

  let catSheet = ss.getSheetByName(TAB_CATEGORY);
  if (!catSheet) {
    catSheet = ss.insertSheet(TAB_CATEGORY);
    catSheet.appendRow(['키', '권역', '유형설명']);
    REGIONS.forEach(region => {
      TYPES.forEach(type => {
        catSheet.appendRow([type.key + '_' + region, region, type.q]);
      });
    });
  }

  let exSheet = ss.getSheetByName(TAB_EXCLUDE);
  if (!exSheet) {
    exSheet = ss.insertSheet(TAB_EXCLUDE);
    exSheet.appendRow(['현장명 (이미 아는 곳 — 여기 추가하면 다음부터 제외됨)']);
    const known = [
      '더 플라자 호텔 전면 리모델링', '수송동 85 숙박시설', '한남동 730 시니어레지던스',
      'SM그룹 강남사옥→호텔 전환', '가산동 140-40 숙박시설', '은평 시니어 레지던스',
      '파라다이스 장충동 최고급 호텔 신축', '서울반도체고등학교 기숙사 증축', '포시즌스 호텔 서울',
      '베니키아 프리미어 여의도', '호텔포코', '당산동2가 소형 호텔', '주한교황청대사관',
      '성북동 고급 단독주택', '우면동 단독주택', '상도1동 단독주택', '소요한남 by 파르나스',
      '서울역 힐튼호텔 재개발', '호텔코리아닷컴', '킨텍스 앵커호텔', '과천 아주대학교병원',
      '스카이가든 레지던스', '센트럴타워', '부천과학고 기숙사', '강릉중앙고 기숙사',
      '한국경비협회 연수원', '내포어린이병원', '광주 챔피언스시티 특급호텔', '신세계 5성급 호텔(광주)',
      '오시리아 나4 숙박시설', '롯데리조트 울산(강동)', '삼성창원병원 미래관', '호텔파라곤 증축',
      '암남동 고급 단독주택', '조달품질원 직원수소', '가승개발 골프장 클럽하우스', '모듈러 기숙사 대수선',
      '의용소방대 연수원', '라마다프라자 제주→쉐라톤 제주호텔', '호반호텔앤리조트 고성 화진포',
      '신라모노그램 남해리조트', '레스케이프 서울 명동 럭셔리 컬렉션',
    ];
    known.forEach(name => exSheet.appendRow([name]));
  }

  if (!ss.getSheetByName(TAB_RESULT)) {
    const s = ss.insertSheet(TAB_RESULT);
    s.appendRow(['수집일시', '실행유형', '지역', '현장소재지', '단계', '현장명', '규모', '발주처', '시공사', '건축설계', '핵심요약', '기사링크', '카테고리']);
  }
  if (!ss.getSheetByName(TAB_REVIEW)) {
    const s = ss.insertSheet(TAB_REVIEW);
    s.appendRow(['수집일시', '실행유형', '현장명', '카테고리', '왜 애매한지(검증 사유)', '원본 데이터(JSON)']);
  }
  if (!ss.getSheetByName(TAB_LOG)) {
    const s = ss.insertSheet(TAB_LOG);
    s.appendRow(['실행일시', '실행유형', '카테고리별 원본건수', '중복제거 후', '확정', '재검토', '오류']);
  }

  setTriggers();
  Logger.log('설정 완료. 탭 생성/확인, 일일·월간 트리거 등록 완료.');
}

function setTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => {
    const fn = t.getHandlerFunction();
    if (fn === 'runDailyBackfillSearch' || fn === 'runMonthlyWideSweep') ScriptApp.deleteTrigger(t);
  });
  // 매일 새벽 6시 — 최근 30일 좁은 창, 빠르게
  ScriptApp.newTrigger('runDailyBackfillSearch').timeBased().everyDays(1).atHour(6).create();
  // 매달 1일 새벽 5시 — 최근 3~12개월 넓은 창, 느슨하게 놓친 것까지
  ScriptApp.newTrigger('runMonthlyWideSweep').timeBased().onMonthDay(1).atHour(5).create();
}

// ===================== 2026-09-01 추가: 시너지 C안(구조화 채널 흡수) =====================
// 뉴스 기사가 아니라 "관광숙박업 등록 공고"·"지자체 건축심의위원회 통과 공고" 자체를
// 검색 대상으로 넣는다. 카테고리 시트에 행만 추가하는 것이라 기존 로직 변경 없음(A등급/추가).
// 이미 실행한 적 있으면 중복 방지 로직이 있어 여러 번 실행해도 안전함.
function addStructuredChannelCategories() {
  const ss = SpreadsheetApp.openById(RADAR_SHEET_ID);
  const sheet = ss.getSheetByName(TAB_CATEGORY);
  const existing = sheet.getDataRange().getValues().map(r => r[0]);

  const NEW_TYPES = [
    { key: '관광숙박업등록', q: '관광숙박업 등록 공고(지자체 관광과·시청 홈페이지 고시)' },
    { key: '건축심의공고',   q: '지자체 건축위원회·건축심의위원회 통과 공고(숙박·기숙사·연수원 용도)' },
  ];

  let added = 0;
  REGIONS.forEach(region => {
    NEW_TYPES.forEach(type => {
      const key = type.key + '_' + region;
      if (existing.indexOf(key) === -1) {
        sheet.appendRow([key, region, type.q]);
        added++;
      }
    });
  });
  Logger.log('구조화 채널 카테고리 추가: ' + added + '건 (이미 있던 건 건너뜀)');
}

// ===================== 진입점 2개 =====================

function runDailyBackfillSearch() {
  coreRun_('최근 30일 이내', '일일');
}

function runMonthlyWideSweep() {
  coreRun_('최근 3~12개월 이내(단, 이미 확정 발송된 것은 제외목록에 있으니 자동으로 걸러짐)', '월간정밀');
}

// ===================== 공통 실행 로직 =====================

function coreRun_(lookbackPhrase, runLabel) {
  const errors = [];
  const categories = readCategories_();
  const excludeList = readExcludeList_();

  let rawResults = [];
  categories.forEach(cat => {
    try {
      const prompt = buildPrompt_(lookbackPhrase, cat.region, cat.q, excludeList);
      const hits = callGeminiWithSearch_(prompt);
      hits.forEach(h => { h.카테고리 = cat.key; });
      rawResults = rawResults.concat(hits);
    } catch (e) {
      errors.push(cat.key + ': ' + e);
    }
    Utilities.sleep(1500); // API 과부하 방지 (42개라 간격을 조금 줄임)
  });

  const rawCount = rawResults.length;
  const deduped = dedupeByName_(rawResults);

  let verified = { confirmed: deduped, review: [] };
  try {
    verified = verifyResults_(deduped);
  } catch (e) {
    errors.push('자체검증 실패, 전체를 재검토로 돌림: ' + e);
    verified = { confirmed: [], review: deduped.map(r => Object.assign({}, r, { 검증사유: '검증 단계 오류로 미확정' })) };
  }

  writeResults_(verified.confirmed, TAB_RESULT, false, runLabel);
  writeResults_(verified.review, TAB_REVIEW, true, runLabel);
  sendEmail_(verified.confirmed, verified.review, runLabel);
  writeLog_(rawCount, deduped.length, verified.confirmed.length, verified.review.length, errors, runLabel);
}

// ===================== 규칙 읽기 =====================

function readCategories_() {
  const ss = SpreadsheetApp.openById(RADAR_SHEET_ID);
  const rows = ss.getSheetByName(TAB_CATEGORY).getDataRange().getValues();
  const out = [];
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][0]) out.push({ key: rows[i][0], region: rows[i][1], q: rows[i][2] });
  }
  return out;
}

function readExcludeList_() {
  const ss = SpreadsheetApp.openById(RADAR_SHEET_ID);
  const rows = ss.getSheetByName(TAB_EXCLUDE).getDataRange().getValues();
  const out = [];
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][0]) out.push(rows[i][0]);
  }
  return out;
}

// ===================== Gemini 호출 =====================

function buildPrompt_(lookbackPhrase, region, typeDesc, excludeList) {
  return lookbackPhrase + ' ' + region + ' 지역에서 ' + typeDesc + ' 소식을 찾아라. ' +
    '시공사·발주처·규모가 확인되는 기사만.\n\n' +
    '[찾을 대상 최소 기준] 숙박시설은 1,500㎡ 이상, 아파트 등 공딜주택은 제외.\n\n' +
    '[이미 아는 현장 — 결과에서 제외] ' + excludeList.join(', ') + '\n\n' +
    '[반드시 지킬 것]\n' +
    '- 이건 실제 조사다. "샘플"이나 "예시" 데이터를 만들지 마라.\n' +
    '- 실제로 검색해서 확인된 것만 담아라. 확실하지 않으면 넣지 말고 빼라.\n' +
    '- 지어내지 마라. 없으면 빈 배열을 반환해라.\n\n' +
    '아래 JSON 배열 형식으로만 답하라. 다른 설명·인사말·마크다운 코드블록 표시 없이 순수 JSON만:\n' +
    '[{"지역":"","현장소재지":"","단계":"","현장명":"","규모":"","발주처":"","시공사":"","건축설계":"","핵심요약":"","기사링크":""}]';
}

function callGeminiWithSearch_(prompt) {
  const text = callGemini_({ contents: [{ parts: [{ text: prompt }] }], tools: [{ google_search: {} }] });
  const cleaned = text.replace(/```json/g, '').replace(/```/g, '').trim();
  try {
    return JSON.parse(cleaned);
  } catch (e) {
    Logger.log('JSON 변환 실패, 원문: ' + text);
    return [];
  }
}

function callGemini_(payload) {
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + GEMINI_MODEL + ':generateContent';
  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: { 'x-goog-api-key': GEMINI_API_KEY },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  };
  const res = UrlFetchApp.fetch(url, options);
  const json = JSON.parse(res.getContentText());
  if (json.error) throw new Error(JSON.stringify(json.error));
  const parts = json.candidates && json.candidates[0] && json.candidates[0].content && json.candidates[0].content.parts;
  return parts ? parts.map(p => p.text || '').join('') : '[]';
}

// ===================== 중복 제거 =====================

function dedupeByName_(results) {
  const seen = {};
  const out = [];
  results.forEach(r => {
    const key = (r.현장명 || '').trim();
    if (key && !seen[key]) { seen[key] = true; out.push(r); }
  });
  return out;
}

// ===================== 2차 자체검증 =====================

function verifyResults_(results) {
  if (results.length === 0) return { confirmed: [], review: [] };

  const prompt =
    '아래는 "신규 건설·개발 현장 후보" 목록이다. 각 항목에 대해 구글 검색으로 다시 확인해서,\n' +
    '(a) 이미 운영 중이거나 완공되어 더 이상 "신규 현장"이 아닌 경우\n' +
    '(b) 실제로 존재하지 않거나 사실관계가 틀린 경우\n' +
    '위 (a)(b)에 해당하면 "invalid", 확실히 신규 진행 중이면 "confirmed", 애매하면 "review"로 판정해라.\n\n' +
    '[목록]\n' + JSON.stringify(results) + '\n\n' +
    '아래 JSON 배열 형식으로만 답하라(다른 텍스트 없이):\n' +
    '[{"현장명":"","판정":"confirmed|invalid|review","사유":""}]';

  const text = callGemini_({ contents: [{ parts: [{ text: prompt }] }], tools: [{ google_search: {} }] });
  const cleaned = text.replace(/```json/g, '').replace(/```/g, '').trim();
  let verdicts;
  try {
    verdicts = JSON.parse(cleaned);
  } catch (e) {
    return { confirmed: [], review: results.map(r => Object.assign({}, r, { 검증사유: '자체검증 응답 파싱 실패' })) };
  }

  const verdictMap = {};
  verdicts.forEach(v => { verdictMap[v.현장명] = v; });

  const confirmed = [];
  const review = [];
  results.forEach(r => {
    const v = verdictMap[r.현장명];
    if (!v || v.판정 === 'review') {
      review.push(Object.assign({}, r, { 검증사유: v ? v.사유 : '검증 결과 없음' }));
    } else if (v.판정 === 'confirmed') {
      confirmed.push(r);
    }
  });
  return { confirmed: confirmed, review: review };
}

// ===================== 시트 기록 =====================

function writeResults_(items, tabName, isReview, runLabel) {
  if (items.length === 0) return;
  const ss = SpreadsheetApp.openById(RADAR_SHEET_ID);
  const sheet = ss.getSheetByName(tabName);
  const now = new Date();
  items.forEach(r => {
    if (isReview) {
      sheet.appendRow([now, runLabel, r.현장명, r.카테고리, r.검증사유 || '', JSON.stringify(r)]);
    } else {
      sheet.appendRow([now, runLabel, r.지역, r.현장소재지, r.단계, r.현장명, r.규모, r.발주처, r.시공사, r.건축설계, r.핵심요약, r.기사링크, r.카테고리]);
    }
  });
}

function writeLog_(raw, deduped, confirmed, review, errors, runLabel) {
  const ss = SpreadsheetApp.openById(RADAR_SHEET_ID);
  ss.getSheetByName(TAB_LOG).appendRow([new Date(), runLabel, raw, deduped, confirmed, review, errors.join(' / ')]);
}

// ===================== 메일 발송 =====================

function sendEmail_(confirmed, review, runLabel) {
  const props = PropertiesService.getScriptProperties();

  // ---------- 0건이면 메일을 보내지 않는다 (2026-09-19 프로님 지시) ----------
  if (confirmed.length === 0 && review.length === 0) {
    const days = (parseInt(props.getProperty('ZERO_DAYS'), 10) || 0) + 1;
    props.setProperty('ZERO_DAYS', String(days));
    Logger.log('신규 0건 — 메일 보내지 않음 (연속 ' + days + '일째)');
    if (ZERO_ALERT_DAYS > 0 && days === ZERO_ALERT_DAYS) {
      GmailApp.sendEmail(TARGET_EMAIL,
        '[신규 현장 레이더] ' + days + '일째 0건 — 살아는 있는지 확인해 주십시오',
        days + '일 연속으로 새로 찾은 현장이 0건입니다.\n\n'
        + '고장이 아니라 정말 없는 것일 수도 있고, API 키·한도·모델명이 막혀 전량 실패 중일 수도 있습니다.\n'
        + '시트의 「' + TAB_LOG + '」 탭 맨 아랫줄을 보시면 오류 칸에 이유가 적혀 있습니다.\n\n'
        + '이 점검 메일은 ' + ZERO_ALERT_DAYS + '일에 한 번만 갑니다. 새 현장이 하나라도 잡히면 날수는 0으로 돌아갑니다.\n'
        + '현장 찾기의 본선은 산군(sankun.com)이고, 이 레이더는 보조입니다.');
    }
    return;
  }
  props.setProperty('ZERO_DAYS', '0');

  let html = '';
  if (confirmed.length > 0) {
    html += '<h2>확정 발견 (' + confirmed.length + '건) — 자체검증 통과</h2>';
    const byCat = {};
    confirmed.forEach(r => { (byCat[r.카테고리] = byCat[r.카테고리] || []).push(r); });
    for (const cat in byCat) {
      html += '<h3>' + cat + '</h3><ul>';
      byCat[cat].forEach(r => {
        html += '<li><b>' + r.현장명 + '</b> (' + r.지역 + ' · ' + r.현장소재지 + ')<br>' +
          '단계: ' + r.단계 + ' · 규모: ' + r.규모 + '<br>' +
          '발주처: ' + r.발주처 + ' · 시공사: ' + r.시공사 + ' · 설계: ' + r.건축설계 + '<br>' +
          r.핵심요약 + '<br>' +
          (r.기사링크 ? '<a href="' + r.기사링크 + '">기사 링크</a>' : '(링크 없음)') +
          '</li><br>';
      });
      html += '</ul>';
    }
  }
  if (review.length > 0) {
    html += '<h2 style="color:#b45309">재검토 필요 (' + review.length + '건) — 애매해서 확정 못 함</h2><ul>';
    review.forEach(r => {
      html += '<li><b>' + r.현장명 + '</b> — ' + (r.검증사유 || '사유 미상') + '</li>';
    });
    html += '</ul>';
  }
  html += '<p style="color:#888;font-size:12px">이 메일은 Claude가 아니라 구글 Gemini API가 직접 조사·자체검증·발송한 결과입니다(' + runLabel + ' 실행). ' +
    '판정(★최우선/△검토)은 아직 안 붙어 있으니, 갈곳목록에 옮길 때 확인이 필요합니다.<br>' +
    '현장 찾기의 본선은 산군(sankun.com)이고 이 레이더는 보조입니다. 산군에서 받은 관심현장 파일은 PC 도구 49번이 판정·중복제거까지 해 드립니다.<br>' +
    '0건인 날에는 이 메일이 가지 않습니다(2026-09-19부터). ' + ZERO_ALERT_DAYS + '일 연속 0건일 때만 점검 메일이 한 번 갑니다.</p>';

  const subject = '[신규 현장 레이더-구글AI][' + runLabel + '] 확정 ' + confirmed.length + '건 · 재검토 ' + review.length + '건';
  GmailApp.sendEmail(TARGET_EMAIL, subject, '', { htmlBody: html });
}

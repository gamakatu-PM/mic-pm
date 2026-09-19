const pptxgen = require('pptxgenjs');
const fs = require('fs');
const sharp = require('sharp');
const React = require('react');
const RDS = require('react-dom/server');
const FA = require('react-icons/fa');

const K = '/root/.claude/skills/synced/0efa8a77-0e57-4680-a0ed-04168ed560bd_7ee69130-3a5a-4642-ac5f-faa77fb56d09';
const P = K + '/km-spec-builder/assets/png/';
const PH = K + '/km-proposal/assets/photos/';
const IMG = {
  iface: P + 'BIN0003.png', cbin: P + 'BIN0004.png', lock: P + 'BIN0008.png', fip: P + 'BIN0009.png',
  temp: P + 'BIN000A.png', kdm: P + 'BIN000B.png', bell: P + 'BIN000C.png', light: P + 'BIN000D.png',
  lamp: P + 'BIN000F.png', bsp: P + 'BIN0010.png',
  cb_open: PH + 'cb_노출형_설치.jpg', cb_wire: PH + 'cb_매입_설치중_배선.jpg',
  cb_cover: PH + 'cb_매입형_커버마감.jpg', cb_furn: PH + 'cb_매입형_가구마감.jpg',
  ehp: __dirname + '/diag_ehp.png', lock2: P + 'BIN0005.png',
  diag1: __dirname + '/diag_scenario.png', diag2: __dirname + '/diag_system.png',
};
const C = { NAVY: '1F3864', DEEP: '152A4F', GOLD: 'C8A24B', INK: '2B2B2B', MUTE: '6B7280',
  TINT: 'F4F5F7', LINE: 'D9DDE3', WHITE: 'FFFFFF', SOFT: 'EAF0F8', RED: 'B03A2E' };
const F = '맑은 고딕';
const TOTAL = 15;
let PAGE = 0;

async function size(p) { const m = await sharp(p).metadata(); return { w: m.width, h: m.height }; }
async function fit(p, x, y, w, h) { const s = await size(p); const r = Math.min(w / s.w, h / s.h);
  const ww = s.w * r, hh = s.h * r; return { x: x + (w - ww) / 2, y: y + (h - hh) / 2, w: ww, h: hh }; }
async function cover(p, x, y, w, h) { // crop to fill box (pptxgenjs sizing:cover)
  return { path: p, x, y, w, h, sizing: { type: 'cover', w, h } }; }
async function icon(name, color) {
  const svg = RDS.renderToStaticMarkup(React.createElement(FA[name], { color: '#' + color, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return 'image/png;base64,' + buf.toString('base64');
}
function T(sl, text, o) { sl.addText(text, Object.assign({ fontFace: F, isTextBox: true, margin: 0, color: C.INK }, o)); }
function chrome(sl, dark) { const n = ++PAGE;
  T(sl, '한국마이크로닉(주)  ·  객실관리 시스템 제안서', { x: 0.5, y: 5.25, w: 6, h: 0.22, fontSize: 8, color: dark ? '8FA3C8' : C.MUTE });
  T(sl, `${String(n).padStart(2, '0')}  /  ${TOTAL}`, { x: 8.3, y: 5.25, w: 1.2, h: 0.22, fontSize: 8, align: 'right', color: dark ? '8FA3C8' : C.MUTE });
}
function title(sl, eyebrow, t) {
  T(sl, eyebrow, { x: 0.5, y: 0.38, w: 6, h: 0.22, fontSize: 9, color: C.GOLD, bold: true, charSpacing: 1 });
  T(sl, t, { x: 0.5, y: 0.6, w: 7.5, h: 0.5, fontSize: 24, bold: true, color: C.NAVY });
}
function circleNum(sl, x, y, d, n, bg) {
  sl.addShape('ellipse', { x, y, w: d, h: d, fill: { color: bg || C.GOLD }, line: { color: bg || C.GOLD, width: 0 } });
  T(sl, String(n), { x, y, w: d, h: d, fontSize: d > 0.4 ? 13 : 10, bold: true, color: C.WHITE, align: 'center', valign: 'middle' });
}
async function iconCircle(sl, x, y, d, name, bg, fg) {
  sl.addShape('ellipse', { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg, width: 0 } });
  sl.addImage({ data: await icon(name, fg), x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5 });
}
async function photoCard(sl, p, x, y, w, h, cap, capColor) {
  sl.addShape('roundRect', { x, y, w, h, fill: { color: C.WHITE }, line: { color: C.LINE, width: 0.75 }, rectRadius: 0.06,
    shadow: { type: 'outer', blur: 4, offset: 1.5, angle: 90, color: '000000', opacity: 0.12 } });
  const f = await fit(p, x + 0.08, y + 0.08, w - 0.16, h - (cap ? 0.42 : 0.16));
  sl.addImage({ path: p, x: f.x, y: f.y, w: f.w, h: f.h });
  if (cap) T(sl, cap, { x: x + 0.08, y: y + h - 0.34, w: w - 0.16, h: 0.28, fontSize: 8.5, color: capColor || C.MUTE, align: 'center', valign: 'middle' });
}

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';
  pres.author = '한국마이크로닉(주)'; pres.company = '한국마이크로닉(주)'; pres.subject = '객실관리 시스템 제안서'; pres.title = '객실관리 시스템 제안서';
  const bul = (arr) => arr.map((s, i) => ({ text: s, options: { bullet: true, breakLine: i !== arr.length - 1, paraSpaceAfter: 4 } }));

  // ── 1. 표지 ──────────────────────────────────────────
  { PAGE++; const sl = pres.addSlide(); sl.background = { color: C.NAVY };
    sl.addImage(await cover(IMG.cb_furn, 5.9, 0, 4.1, 5.625));
    sl.addShape('rect', { x: 5.9, y: 0, w: 4.1, h: 5.625, fill: { color: C.NAVY, transparency: 55 }, line: { color: C.NAVY, width: 0 } });
    T(sl, 'PROPOSAL', { x: 0.7, y: 1.35, w: 4.5, h: 0.25, fontSize: 10, color: C.GOLD, bold: true, charSpacing: 3 });
    T(sl, '[ 현장명 ]', { x: 0.7, y: 1.75, w: 4.8, h: 0.5, fontSize: 20, color: 'C9D6EA' });
    T(sl, '객실관리 시스템\n제안서', { x: 0.7, y: 2.25, w: 5, h: 1.4, fontSize: 34, bold: true, color: C.WHITE, lineSpacingMultiple: 1.05 });
    T(sl, '운영 시나리오 · 시스템 구성 · 객실 표준 구성 · 공사 구분', { x: 0.7, y: 3.75, w: 5, h: 0.3, fontSize: 11, color: 'C9D6EA' });
    T(sl, '한국마이크로닉(주)\n2026. 09. 19', { x: 0.7, y: 4.55, w: 3, h: 0.55, fontSize: 10, color: '8FA3C8' });
    T(sl, '40년 연속 객실관리 시스템 1위', { x: 3.4, y: 4.55, w: 2.4, h: 0.55, fontSize: 10, color: C.GOLD, valign: 'top' });
    T(sl, '매입형 CB · 가구 마감 사례', { x: 6.1, y: 5.15, w: 3.7, h: 0.25, fontSize: 8, color: 'C9D6EA', align: 'right' });
  }

  // ── 2. 제안 요약 ─────────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'SUMMARY', '제안 요약');
    T(sl, '객실 상태에 따라 조명 · 전열 · 냉난방을 자동 제어하여\n투숙객 편의와 에너지 절감을 함께 실현합니다.', { x: 0.5, y: 1.2, w: 5.4, h: 0.7, fontSize: 13, color: C.INK, lineSpacingMultiple: 1.15 });
    const rows = [
      ['FaUserCheck', '투숙객 편의', 'Card 투입 한 번으로 조명 · 전열 · 냉난방이 켜지고, 외출 · 재입실은 자동으로 전환됩니다.'],
      ['FaBolt', '운영 · 에너지', '외출 · 공실 온도를 자동 관리하고, PMS와 체크인/아웃 · 청소완료를 실시간으로 주고받습니다.'],
      ['FaTools', '시공 · 유지보수', '국내 표준 매입 박스 호환, RJ45 원터치 결선. 설계부터 시운전까지 당사가 직접 수행합니다.'],
    ];
    let y = 2.05;
    for (const [ic, h, d] of rows) {
      await iconCircle(sl, 0.5, y, 0.5, ic, C.SOFT, C.NAVY);
      T(sl, h, { x: 1.15, y: y - 0.02, w: 4.7, h: 0.28, fontSize: 12.5, bold: true, color: C.NAVY });
      T(sl, d, { x: 1.15, y: y + 0.26, w: 4.7, h: 0.5, fontSize: 9.5, color: C.MUTE, lineSpacingMultiple: 1.1 });
      y += 0.92;
    }
    await photoCard(sl, IMG.bsp, 6.2, 1.2, 3.3, 1.9, 'BED SIDE PANEL  ·  온도 · 조명 · USB · 콘센트');
    await photoCard(sl, IMG.kdm, 6.2, 3.25, 1.55, 1.55, 'Key Sensor + DM');
    await photoCard(sl, IMG.bell, 7.95, 3.25, 1.55, 1.55, '입구 챠임벨');
    sl.addShape('roundRect', { x: 0.5, y: 4.85, w: 5.4, h: 0.3, fill: { color: 'FBF6E9' }, line: { color: 'FBF6E9', width: 0 }, rectRadius: 0.05 });
    T(sl, '설계 단계에서 반영하시면 전기 · 인테리어 공정과 간섭 없이 진행됩니다.', { x: 0.62, y: 4.85, w: 5.2, h: 0.3, fontSize: 9, bold: true, color: '7A5A12', valign: 'middle' });
    chrome(sl);
  }

  // ── 3. 운영 시나리오 ─────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'OPERATION SCENARIO', '운영 시나리오');
    T(sl, '고객 동선 8단계 · PMS 연동 기준', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const f = await fit(IMG.diag1, 0.5, 1.2, 9.0, 3.55);
    sl.addImage({ path: IMG.diag1, x: f.x, y: f.y, w: f.w, h: f.h });
    T(sl, '객실관리 서버가 체크인 · 재실 · 외출 · 공실을 판단하여 조명 · 전열 · 냉난방을 자동 제어합니다.  PMS로부터 체크인/아웃 DATA를 받고, 청소완료 · 객실판매가능 DATA를 전달합니다.',
      { x: 0.5, y: 4.8, w: 9.0, h: 0.4, fontSize: 9, color: C.MUTE });
    chrome(sl);
  }

  // ── 4. 시스템 구성도 ─────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'SYSTEM DIAGRAM', '시스템 구성도');
    T(sl, '방재실 → 각층 린넨실 → 객실', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const f = await fit(IMG.diag2, 0.5, 1.15, 9.0, 3.6);
    sl.addImage({ path: IMG.diag2, x: f.x, y: f.y, w: f.w, h: f.h });
    T(sl, 'PMS 서버 · 호텔 전용망은 발주처 공사분입니다.  객실관리 서버 → FIP → CONTROL BOX → 객실 기구물은 당사가 제작 · 납품 · 약전 결선 · 시운전하며, CB 강전 결선은 전기공사 시행입니다.',
      { x: 0.5, y: 4.8, w: 9.0, h: 0.4, fontSize: 9, color: C.MUTE });
    chrome(sl);
  }


  // ── 냉난방 연동 ──────────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'HVAC INTERLOCK', '냉난방 연동 — EHP · FCU · 바닥난방');
    T(sl, 'C/B ↔ 실내기 · 결선 3지점', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const f = await fit(IMG.ehp, 0.5, 1.15, 5.95, 2.6);
    sl.addImage({ path: IMG.ehp, x: f.x, y: f.y, w: f.w, h: f.h });
    const st = [['배관 · 배선', '전기공사', 'C/B ↔ 실내기 UTP 5E, 반드시 1 : 1'], ['실내기 측 통신선 결선', 'EHP · FCU 업체', '인터페이스 모듈에 결선'], ['C/B 측 통신선 결선', '객실관리', '어드레스 세팅 · 시운전 포함']];
    st.forEach(([h, w, d], i) => { const y = 1.2 + i * 0.86;
      sl.addShape('roundRect', { x: 6.7, y, w: 2.8, h: 0.76, fill: { color: C.TINT }, line: { color: C.TINT, width: 0 }, rectRadius: 0.05 });
      circleNum(sl, 6.82, y + 0.12, 0.32, i + 1, C.NAVY);
      T(sl, h, { x: 7.25, y: y + 0.08, w: 2.2, h: 0.24, fontSize: 9.5, bold: true, color: C.NAVY });
      T(sl, w, { x: 7.25, y: y + 0.3, w: 2.2, h: 0.2, fontSize: 8.5, bold: true, color: C.GOLD });
      T(sl, d, { x: 7.25, y: y + 0.5, w: 2.2, h: 0.2, fontSize: 8, color: C.MUTE }); });
    sl.addShape('roundRect', { x: 0.5, y: 3.9, w: 9.0, h: 1.2, fill: { color: 'FBF6E9' }, line: { color: 'FBF6E9', width: 0 }, rectRadius: 0.05 });
    T(sl, '반드시 지켜 주실 조건', { x: 0.65, y: 3.95, w: 3, h: 0.22, fontSize: 9, bold: true, color: '7A5A12' });
    T(sl, bul(['실내기 전원은 220V 상시전원으로 공급 — 객실 전원과 함께 차단되면 연동이 끊깁니다.',
      '통신선은 실내기마다 1 : 1 입선 — 한 선에 묶으면 주소가 겹쳐 오동작합니다. 실내기 2대면 선도 2가닥입니다.',
      'EHP · FCU는 객실관리 연동 인터페이스 모듈 포함 사양으로 발주 — 현장 반입 후에는 교체가 어렵습니다.',
      '바닥난방 구동기 밸브는 220V 노말 클로즈 타입, 제어선은 밸브 1개당 HFIX 1.5SQ 3C입니다.']),
      { x: 0.65, y: 4.17, w: 8.7, h: 0.9, fontSize: 8.5, color: C.INK, valign: 'top' });
    chrome(sl);
  }

  // ── 도어락 연동 · 주거약자실 ─────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'DOOR LOCK · ACCESSIBLE ROOM', '도어락 연동 · 주거약자실');
    await photoCard(sl, IMG.lock2, 0.5, 1.2, 2.3, 2.35, '객실 도어락 · PMS 연동');
    T(sl, '도어락 연동', { x: 3.05, y: 1.2, w: 3.6, h: 0.3, fontSize: 13, bold: true, color: C.NAVY });
    T(sl, bul(['객실 및 공용부 출입관리 — PMS와 연동합니다.', '배선은 UTP cat.5, C/B에서 도어락 문틀 밖까지 (전기공사).',
      '방화문 타공은 객실만 해당하며, 문틀 · 방화문 타공은 방화문업체가 생산 시 배관까지 시행합니다.',
      '케이블 브릿지 이후 손잡이까지의 입선 · 결선은 도어락 업체 시행입니다.']),
      { x: 3.05, y: 1.55, w: 3.6, h: 2.0, fontSize: 9.5, color: C.INK, valign: 'top' });
    await photoCard(sl, IMG.lamp, 6.9, 1.2, 2.6, 2.35, '방문자 알림램프');
    sl.addShape('roundRect', { x: 0.5, y: 3.75, w: 9.0, h: 1.3, fill: { color: C.SOFT }, line: { color: C.SOFT, width: 0 }, rectRadius: 0.05 });
    await iconCircle(sl, 0.7, 3.95, 0.5, 'FaWheelchair', C.NAVY, 'FFFFFF');
    T(sl, '주거약자실 — 법적의무 2종', { x: 1.35, y: 3.9, w: 5, h: 0.3, fontSize: 12, bold: true, color: C.NAVY });
    T(sl, bul(['비상호출버튼 : 호출 시 관제 PC에 즉시 표시되어 담당자가 대응합니다.', '방문자 알림램프 : 방문 신호를 램프로 표시합니다.', '두 기구물 모두 객실관리 C/B에 연결되며, 위치는 객실 타입별 평면도로 협의합니다.']),
      { x: 1.35, y: 4.2, w: 8.0, h: 0.8, fontSize: 9, color: C.INK, valign: 'top' });
    chrome(sl);
  }

  // ── 5. 주요 제품 구성 ────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'PRODUCTS', '주요 제품 구성');
    T(sl, '객실 1실 기준', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const items = [
      [IMG.cb_open, 'CONTROL BOX (RCU)', '객실 출입문 뒤 · 400×700×100', '조명 · 전열 · 냉난방 제어 장치'],
      [IMG.bell, '입구 INDICATOR', '입구 복도 · 도어락 손잡이 측', 'DO NOT DISTURB · MAKE UP ROOM 표시, 챠임벨'],
      [IMG.kdm, 'Key Sensor + DM', '객실 입구 내부', 'CARD 투입 시 전등 · 전열 공급 (DM은 4~5성급)'],
      [IMG.temp, '온도조절기 · LIGHT S/W', '침대 옆 · 거실 입구', '온도 조절 및 조명 조절'],
      [IMG.bsp, 'BED SIDE PANEL', '침대 옆 (4~5성급)', '온도 + 조명 + USB 충전 + 유니버셜 콘센트'],
      [IMG.light, 'LIGHT SWITCH (L)', '화장실 · 베란다 등', '구수는 조명 설계 확정 후 결정'],
      [IMG.lamp, '비상호출 · 방문자 알림램프', '주거약자실', '법적의무 설치 (2종)'],
      [IMG.fip, 'FIP · 객실관리 서버', '각층 린넨실 · 방재실', '층 통신 중계 · 객실 상태 관제 · PMS 연동'],
    ];
    const cw = 2.1, ch = 1.85, gx = 0.2, gy = 0.2;
    for (let i = 0; i < items.length; i++) {
      const [p, n, loc, fn] = items[i];
      const x = 0.5 + (i % 4) * (cw + gx), y = 1.2 + Math.floor(i / 4) * (ch + gy);
      sl.addShape('roundRect', { x, y, w: cw, h: ch, fill: { color: C.TINT }, line: { color: C.TINT, width: 0 }, rectRadius: 0.06 });
      const f = await fit(p, x + 0.15, y + 0.12, cw - 0.3, 0.85);
      sl.addImage({ path: p, x: f.x, y: f.y, w: f.w, h: f.h });
      T(sl, n, { x: x + 0.12, y: y + 1.02, w: cw - 0.24, h: 0.24, fontSize: 9.5, bold: true, color: C.NAVY });
      T(sl, loc, { x: x + 0.12, y: y + 1.26, w: cw - 0.24, h: 0.2, fontSize: 8, color: C.GOLD, bold: true });
      T(sl, fn, { x: x + 0.12, y: y + 1.46, w: cw - 0.24, h: 0.36, fontSize: 8, color: C.MUTE, lineSpacingMultiple: 1.05 });
    }
    chrome(sl);
  }

  // ── 6. 객실 표준 구성 (등급별) ────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'ROOM STANDARD', '객실 표준 구성 — 등급별');
    T(sl, '당사 표준이며 현장 협의로 조정합니다', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const hd = (t, i) => ({ text: t, options: { fill: { color: C.NAVY }, color: C.WHITE, bold: true, align: i ? 'center' : 'left', valign: 'middle', fontSize: 9.5 } });
    const rows = [
      ['객실 입구 (복도)', '챠임벨 — 도어락 손잡이 측', '챠임벨 — 도어락 손잡이 측'],
      ['객실 입구 (내부)', 'K (Key Sensor)', 'K + DM'],
      ['침대 옆', '온도조절기 + L', 'BSP (온도 + 조명 + USB + 유니버셜 콘센트)'],
      ['화장실', '전기 텀블러 S/W (전기공사 시행)', 'L (객실관리)'],
      ['베란다', '침대 옆 L에서 제어', '베란다 문 옆 L 별도'],
      ['책상', '멀티아울렛', '멀티아울렛'],
      ['거실 입구', '온도조절기 + L', '온도조절기 + L'],
      ['공용부', '관제 PC 방재실 1EA · FIP 층당 1EA', '관제 PC 방재실 1EA · FIP 층당 1EA'],
    ].map((r, ri) => r.map((c, ci) => ({ text: c, options: { fill: { color: ri % 2 ? C.WHITE : 'F9FAFB' }, color: ci ? C.INK : C.NAVY, bold: ci === 0, fontSize: 8.5, valign: 'middle' } })));
    sl.addTable([[hd('위치', 0), hd('1~3성급 · 리조트', 1), hd('4~5성급', 1)], ...rows],
      { x: 0.5, y: 1.2, w: 6.5, colW: [1.35, 2.45, 2.7], fontFace: F, rowH: 0.36, border: { type: 'solid', color: C.LINE, pt: 0.5 }, autoPage: false });
    T(sl, 'L = LIGHT S/W. 구수(1~6구)는 전기설계의 조명 회로가 확정된 후 결정됩니다.  리조트는 DM을 제외합니다.', { x: 0.5, y: 4.55, w: 6.5, h: 0.4, fontSize: 8, color: C.MUTE });
    await photoCard(sl, IMG.temp, 7.25, 1.2, 2.25, 1.6, '1~3성급  ·  온도조절기 + L');
    await photoCard(sl, IMG.bsp, 7.25, 2.95, 2.25, 1.6, '4~5성급  ·  BSP');
    chrome(sl);
  }


  // ── 관제 소프트웨어 ──────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'CONTROL SOFTWARE', '관제 소프트웨어 — 객실 현황');
    T(sl, '방재실 관제 PC 화면 (예시)', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const ST = { in: ['2E74B5', '재실'], out: ['E0B33A', '외출'], vac: ['4E9A5E', '공실'], off: ['9AA1AB', '무동작'] };
    const pat = 'in in out vac in off in vac out in in vac in out in in vac in off in in out in vac'.split(' ');
    sl.addShape('roundRect', { x: 0.5, y: 1.2, w: 5.0, h: 3.3, fill: { color: '1B2A44' }, line: { color: '1B2A44', width: 0 }, rectRadius: 0.06 });
    T(sl, '8F  객실 현황', { x: 0.7, y: 1.3, w: 3, h: 0.25, fontSize: 9, bold: true, color: 'C9D6EA' });
    T(sl, '2026-09-19  14:30', { x: 3.5, y: 1.3, w: 1.85, h: 0.25, fontSize: 8, color: '8FA3C8', align: 'right' });
    pat.forEach((k, i) => { const [col, lab] = ST[k]; const x = 0.7 + (i % 6) * 0.78, y = 1.65 + Math.floor(i / 6) * 0.62;
      sl.addShape('roundRect', { x, y, w: 0.7, h: 0.54, fill: { color: col }, line: { color: col, width: 0 }, rectRadius: 0.04 });
      T(sl, String(801 + i), { x, y: y + 0.05, w: 0.7, h: 0.2, fontSize: 8.5, bold: true, color: C.WHITE, align: 'center' });
      T(sl, k === 'off' ? lab : `${lab} · ${(21 + (i % 4) * 0.5).toFixed(1)}°`, { x, y: y + 0.27, w: 0.7, h: 0.2, fontSize: 7, color: C.WHITE, align: 'center' }); });
    Object.values(ST).forEach(([col, lab], i) => { const x = 0.7 + i * 1.15;
      sl.addShape('rect', { x, y: 4.2, w: 0.16, h: 0.16, fill: { color: col }, line: { color: col, width: 0 } });
      T(sl, lab, { x: x + 0.22, y: 4.17, w: 0.9, h: 0.22, fontSize: 8, color: 'C9D6EA' }); });
    const feats = [['객실 상태 실시간 표시', '체크인 · 재실 · 외출 · 공실을 색으로 구분하고 온도 · 팬 속도(H/M/L)를 표시합니다.'],
      ['온도 제어', '객실별 · 온도그룹(객실당 최대 40개) 제어. 예냉 · 예열은 체크아웃 상태에서 설정하고 체크인 시 자동 정지합니다.'],
      ['청소 상태 · PMS', '청소중은 키 센서의 청소키가 우선하며, 청소완료 시 PMS에 판매가능으로 전달됩니다. 체크인/아웃은 PMS에서 자동 반영됩니다.'],
      ['이력 · 백업 · 경보', '현황 자료 1년 보관, DB는 매일 새벽 3시 자동 백업. 화재경보 기준 온도 초과 시 PC 팝업.']];
    let y = 1.2;
    feats.forEach(([h, d]) => { T(sl, h, { x: 5.8, y, w: 3.7, h: 0.24, fontSize: 10.5, bold: true, color: C.NAVY });
      T(sl, d, { x: 5.8, y: y + 0.25, w: 3.7, h: 0.55, fontSize: 8.5, color: C.MUTE, lineSpacingMultiple: 1.1 }); y += 0.84; });
    T(sl, '화면은 구성 예시이며, 실제 화면과 사용법은 준공 시 운영 매뉴얼로 제공합니다.', { x: 0.5, y: 4.7, w: 9, h: 0.25, fontSize: 8, color: C.MUTE });
    chrome(sl);
  }

  // ── 7. 현장 공사 프로세스 ────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'PROCESS', '현장 공사 프로세스');
    T(sl, '설계 의뢰 → 시운전 · 6단계', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const steps = [
      ['설계 의뢰 · 도면 납품', '평면도 접수 → 배치도 · 수량표 · 견적'],
      ['CB 외함 납품', '골조 · 벽체 공정에 맞춰 납품, 전기 · 통신 설치'],
      ['속판 설치 · 결선', '강전 : 전기공사 / 약전 · 셋팅 : 당사 → 커버'],
      ['객실 기구물 제작', '챠임벨 · 키센서 · 온도조절기 · L · BSP'],
      ['기구물 설치', '벽지 · 페인트 마감 완료 후'],
      ['시운전 · 인수', '전원 투입 후 공종별 체크 → 하자리스트 → 교육'],
    ];
    const sw = 1.45, x0 = 0.5, yline = 1.45;
    sl.addShape('line', { x: x0 + 0.22, y: yline + 0.22, w: sw * 5, h: 0, line: { color: C.LINE, width: 1.5, dashType: 'dash' } });
    steps.forEach(([h, d], i) => {
      const x = x0 + i * sw;
      circleNum(sl, x, yline, 0.44, i + 1, i === 5 ? C.NAVY : C.GOLD);
      T(sl, h, { x, y: yline + 0.55, w: sw - 0.12, h: 0.42, fontSize: 9.5, bold: true, color: C.NAVY, lineSpacingMultiple: 1.05 });
      T(sl, d, { x, y: yline + 0.97, w: sw - 0.12, h: 0.55, fontSize: 8, color: C.MUTE, lineSpacingMultiple: 1.05 });
    });
    await photoCard(sl, IMG.cb_wire, 0.5, 3.05, 2.85, 1.65, '② 외함 설치 · 배선 인입 (시공 중)');
    await photoCard(sl, IMG.cb_open, 3.55, 3.05, 2.85, 1.65, '③ 속판 설치 · 내부 결선');
    await photoCard(sl, IMG.cb_furn, 6.6, 3.05, 2.9, 1.65, '③ 커버 설치 · 가구 마감');
    T(sl, '확인 · 협의 사항  —  CB 외함의 매입/노출과 설치 높이는 사전 협의를 요청드립니다.  EHP·FCU는 연동 인터페이스 모듈 포함 장비로 발주하여 주시고, 통신선은 UTP 5E 1:1 입선 · 상시전원 공급을 요청드립니다.  바닥난방 밸브는 220V 노말 클로즈, 스위치 BOX는 유럽형(나사홀 3곱 나사)으로 부탁드립니다.',
      { x: 0.5, y: 4.8, w: 9.0, h: 0.4, fontSize: 8, color: C.MUTE, lineSpacingMultiple: 1.05 });
    chrome(sl);
  }


  // ── 표준 도입 일정 ───────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'SCHEDULE', '표준 도입 일정 — 준공일 기준 역산');
    T(sl, '당사 표준 소요 기간 · 주(week) 단위', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const X0 = 2.75, W = 6.7, WK = 24, px = W / WK;
    for (let w = 0; w <= WK; w += 4) { const x = X0 + w * px;
      sl.addShape('line', { x, y: 1.45, w: 0, h: 3.05, line: { color: C.LINE, width: 0.5, dashType: 'dash' } });
      T(sl, `${w}주`, { x: x - 0.3, y: 1.2, w: 0.6, h: 0.22, fontSize: 8, color: C.MUTE, align: 'center' }); }
    const rows = [['CB 외함 제작', 0, 2, C.NAVY, '2주'], ['CB 외함 납품 · 설치', 2, 2.6, C.GOLD, '골조 · 벽체 공정에 따름 (전기공사 설치)'],
      ['속판(제어 분전함) 제작', 2, 10, C.NAVY, '2개월'], ['속판 납품 · 강전 접속', 10, 14, C.GOLD, '속판 납품 후 1개월 (전기공사)'],
      ['객실 기구물 제작', 8, 16, C.NAVY, '1.5 ~ 2개월'], ['벽지 · 페인트 완료', 17, 17.6, '9AA1AB', '건축 · 인테리어 공정'],
      ['빽커버 설치', 17.6, 19.4, C.NAVY, '벽지 완료 후 1 ~ 2주'], ['기구물 설치', 19.4, 20.4, C.NAVY, '1주'], ['시운전 · 인수', 20.4, 21.4, C.NAVY, '1주 (전원 투입 후)'],
      ['준공', 22.5, 23.1, C.RED, '여유일 [   ]']];
    rows.forEach(([lab, a, b, col, memo], i) => { const y = 1.5 + i * 0.3;
      T(sl, lab, { x: 0.5, y, w: 2.2, h: 0.26, fontSize: 9, bold: true, color: C.NAVY, valign: 'middle' });
      sl.addShape('roundRect', { x: X0 + a * px, y: y + 0.04, w: Math.max((b - a) * px, 0.14), h: 0.18, fill: { color: col }, line: { color: col, width: 0 }, rectRadius: 0.03 });
      T(sl, memo, { x: X0 + b * px + 0.08, y, w: 3.2, h: 0.26, fontSize: 7.5, color: C.MUTE, valign: 'middle' }); });
    T(sl, '소요 기간은 당사 표준값이며, 실제 일정은 현장 공정표(골조 · 벽지 완료일 · 준공일)를 받아 역산하여 확정합니다.  기구물 설치는 벽지 · 페인트 완료 후에만 가능하므로 마감 일정 공유를 요청드립니다.',
      { x: 0.5, y: 4.62, w: 9, h: 0.45, fontSize: 8.5, color: C.INK, lineSpacingMultiple: 1.1 });
    chrome(sl);
  }

  // ── 8. 공사 구분 (담당 매트릭스) ─────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'WORK SCOPE', '공사 구분 — 공급 · 설치 범위');
    T(sl, '●  시행     ○  협의 · 확인', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const heads = ['공정', '주요 내용', '객실관리\n(당사)', '전기공사', '설비 ·\n인테리어', '발주처 ·\n기타'];
    const hd = heads.map((t, i) => ({ text: t, options: { fill: { color: C.NAVY }, color: C.WHITE, bold: true, align: i < 2 ? 'left' : 'center', valign: 'middle', fontSize: 8.5 } }));
    const data = [
      ['CB 외함', '당사 제작 · 납품 → 전기공사 하역 · 설치 · 배관배선 · 타공 (매입/노출 인테리어 협의)', '●', '●', '○', ''],
      ['CB 속판 · 내부 결선', '속판 · PCB · UTP 약전 결선 · 셋팅은 당사 / 1차 입력 · 2차 출력 강전 결선은 전기공사', '●', '●', '', ''],
      ['CB 커버', '커버 제작 · 설치는 당사 / 벽 마감은 인테리어', '●', '', '●', ''],
      ['EHP · FCU 연동', 'C/B ↔ 실내기 UTP 5E 배관배선(1:1)은 전기 / 실내기 측 결선은 EHP · FCU 업체 / C/B 측은 당사', '●', '●', '●', ''],
      ['FIP', '외함 제작 · 납품 · 속판 · 결선은 당사 / 외함 설치 · 220V · 통신선 입선은 전기공사', '●', '●', '', ''],
      ['객실 기구물 · BSP', '통신선 결선 · 브라켓 · 부착은 당사 / 스위치 BOX · 입선 · BSP 강전은 전기 / 어려운 타공은 인테리어', '●', '●', '○', ''],
      ['메인통신 · 시스템 PC', '결선 · PC 설치 · 셋팅은 당사 / AWG #24 · UTP 배관배선은 전기 / PMS 서버 · 전용망 · PC 책상은 발주처', '●', '●', '', '●'],
      ['시운전', '릴레이 출력 체크는 당사 / 말단 콘센트 · 전등은 전기 / EHP · 밸브는 설비 (전원 투입 후, 하자리스트 작성)', '●', '●', '●', ''],
    ];
    const rows = data.map((r, ri) => r.map((c, ci) => ({ text: c, options: {
      fill: { color: ri % 2 ? C.WHITE : 'F9FAFB' }, valign: 'middle',
      color: ci === 0 ? C.NAVY : ci === 1 ? C.INK : (c === '○' ? C.GOLD : C.NAVY),
      bold: ci === 0 || ci >= 2, fontSize: ci >= 2 ? 11 : ci === 0 ? 8.5 : 7.5, align: ci >= 2 ? 'center' : 'left' } })));
    sl.addTable([hd, ...rows], { x: 0.5, y: 1.2, w: 9.0, colW: [1.45, 4.35, 0.8, 0.8, 0.8, 0.8], fontFace: F, rowH: 0.38,
      border: { type: 'solid', color: C.LINE, pt: 0.5 }, autoPage: false });
    T(sl, '당사 표준 공사한계(r2) 기준이며 현장 조건에 따라 협의하여 확정합니다.  상세 공사한계 자료는 별도 제출합니다.', { x: 0.5, y: 4.85, w: 9.0, h: 0.3, fontSize: 8, color: C.MUTE });
    chrome(sl);
  }


  // ── 당사 강점 5 ──────────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'STRENGTHS', '당사의 강점');
    const cards = [['FaFlag', '국내 호텔 시공 실적', ['5성급 특급 호텔 · 대형 리조트 다수 준공', '1,000실 이상 대단지 안정 운영', '국내 시공 · 감리 기준 대응']],
      ['FaDesktop', '소프트웨어 · 관제', ['PMS 연동 통합 관제', '통신 장비 실시간 모니터링 — 컴플레인 전 사전 조치', '소프트웨어 · 게이트웨이 수준 통합 확장']],
      ['FaHardHat', '현장 시공성', ['국내 표준 매입 박스 100% 호환', 'RJ45 원터치 결선 — 오결선 최소 · 시공 단축', 'CB · 챠임벨 · 강전 · 약전 복합 공정 경험']],
      ['FaExpandArrowsAlt', '확장성', ['도어락 · EHP · 바닥난방 · 인덕션 · 누수감지 연동', '개방형 구조로 현장별 커스터마이징', '준공 후 기능 추가 대응']],
      ['FaHeadset', '유지보수', ['전국 직영망', '24시간 이내 출동 · 자재 즉시 수급', '설계 ~ 시운전 전 공정 자체 수행']]];
    const cw = 1.68, gap = 0.15;
    for (let i = 0; i < cards.length; i++) { const [ic, h, lines] = cards[i]; const x = 0.5 + i * (cw + gap), y = 1.25;
      sl.addShape('roundRect', { x, y, w: cw, h: 3.1, fill: { color: i % 2 ? C.WHITE : C.TINT }, line: { color: C.LINE, width: 0.5 }, rectRadius: 0.06 });
      await iconCircle(sl, x + cw / 2 - 0.3, y + 0.25, 0.6, ic, C.GOLD, 'FFFFFF');
      T(sl, h, { x: x + 0.1, y: y + 1.0, w: cw - 0.2, h: 0.5, fontSize: 11, bold: true, color: C.NAVY, align: 'center', valign: 'middle' });
      T(sl, bul(lines), { x: x + 0.14, y: y + 1.6, w: cw - 0.26, h: 1.85, fontSize: 8.5, color: C.INK, valign: 'top', lineSpacingMultiple: 1.05 }); }
    chrome(sl);
  }

  // ── 9. 주요 실적 ─────────────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.WHITE };
    title(sl, 'REFERENCE', '주요 실적');
    T(sl, '당사 객실관리 시스템 납품 현장 (일부)', { x: 6.3, y: 0.72, w: 3.2, h: 0.3, fontSize: 9.5, color: C.MUTE, align: 'right' });
    const cats = [
      ['FaHotel', '특급 호텔', '포항 베스트웨스턴 · 타니베이호텔 · [ 추가 ]'],
      ['FaUmbrellaBeach', '리조트', '대명리조트 · 비발디파크 · 쏠비치 남해 · 쏠비치 양양 · 진도리조트 · 청송리조트'],
      ['FaBuilding', '레지던스 · 연수원', '킨텍스 레지던스 · LG화학 리더십센터 · 하나글로벌 인재개발원'],
      ['FaBed', '기숙사 · 대단지', 'SK하이닉스 기숙사 (2차 공사 1,116실) · 경복대 · [ 추가 ]'],
    ];
    let y = 1.25;
    for (const [ic, h, d] of cats) {
      await iconCircle(sl, 0.5, y, 0.46, ic, C.NAVY, 'FFFFFF');
      T(sl, h, { x: 1.1, y: y - 0.02, w: 4.9, h: 0.26, fontSize: 11.5, bold: true, color: C.NAVY });
      T(sl, d, { x: 1.1, y: y + 0.25, w: 4.9, h: 0.42, fontSize: 9, color: C.MUTE, lineSpacingMultiple: 1.1 });
      y += 0.82;
    }
    sl.addShape('roundRect', { x: 0.5, y: 4.5, w: 5.5, h: 0.5, fill: { color: C.SOFT }, line: { color: C.SOFT, width: 0 }, rectRadius: 0.05 });
    T(sl, '1,000실 이상 대단지 안정 운영 다수  ·  전국 직영망 24시간 이내 출동  ·  설계 ~ 시운전 전 공정 자체 수행', { x: 0.65, y: 4.5, w: 5.3, h: 0.5, fontSize: 8.5, bold: true, color: C.NAVY, valign: 'middle' });
    await photoCard(sl, IMG.cb_cover, 6.35, 1.2, 3.15, 2.35, '매입형 CB · 벽면 커버 마감');
    await photoCard(sl, IMG.lock, 6.35, 3.7, 1.5, 1.3, '도어락 연동');
    await photoCard(sl, IMG.fip, 8.0, 3.7, 1.5, 1.3, 'FIP · 각층 린넨실');
    sl.addNotes('내부 메모 : 실적 목록은 회사 확정 실적표로 교체 후 제출. [ 추가 ] 자리 채울 것. 연도·객실 수는 확정본 기준.');
    chrome(sl);
  }

  // ── 10. 요청드리는 사항 ──────────────────────────────
  { const sl = pres.addSlide(); sl.background = { color: C.NAVY };
    T(sl, 'REQUEST', { x: 0.7, y: 0.5, w: 4, h: 0.25, fontSize: 10, color: C.GOLD, bold: true, charSpacing: 3 });
    T(sl, '요청드리는 사항', { x: 0.7, y: 0.75, w: 6, h: 0.55, fontSize: 26, bold: true, color: C.WHITE });
    T(sl, '객실관리 시스템을 설계 단계에서 반영하실 수 있도록 아래 자료를 요청드립니다.', { x: 0.7, y: 1.35, w: 5.6, h: 0.3, fontSize: 11, color: 'C9D6EA' });
    const its = [
      ['객실 타입별 평면도(단위세대) 제공을 요청드립니다.', '접수 즉시 기구물 배치도 · 예상 수량표 · 견적서를 제출하겠습니다.'],
      ['냉난방 방식(EHP / FCU / 바닥난방)과 PMS 업체를 확인하여 주시기 바랍니다.', '연동 인터페이스 사양과 구성도를 현장에 맞게 확정하겠습니다.'],
      ['전기설계 · 인테리어와의 협의 일정을 요청드립니다.', 'CB 외함 매입/노출, 기구물 위치, 조명 회로(L 구수)를 협의하여 도면에 반영하겠습니다.'],
    ];
    let y = 1.95;
    its.forEach(([h, d], i) => {
      circleNum(sl, 0.7, y, 0.4, i + 1, C.GOLD);
      T(sl, h, { x: 1.25, y: y - 0.03, w: 5.1, h: 0.45, fontSize: 11.5, bold: true, color: C.WHITE, lineSpacingMultiple: 1.05 });
      T(sl, d, { x: 1.25, y: y + 0.42, w: 5.1, h: 0.3, fontSize: 9, color: 'B9C8E0' });
      y += 0.95;
    });
    sl.addShape('roundRect', { x: 6.8, y: 1.95, w: 2.7, h: 2.55, fill: { color: C.DEEP }, line: { color: '2E4A7A', width: 0.75 }, rectRadius: 0.08 });
    await iconCircle(sl, 7.05, 2.2, 0.5, 'FaPhoneAlt', C.GOLD, 'FFFFFF');
    T(sl, '문의', { x: 7.7, y: 2.25, w: 1.7, h: 0.25, fontSize: 9, color: '8FA3C8' });
    T(sl, '한국마이크로닉(주)', { x: 7.05, y: 2.9, w: 2.3, h: 0.3, fontSize: 12, bold: true, color: C.WHITE });
    T(sl, '배성윤 차장', { x: 7.05, y: 3.2, w: 2.3, h: 0.3, fontSize: 11, color: C.WHITE });
    T(sl, 'www.micronic.co.kr\n한글도메인 : 소프트.한국\n전화 : [          ]\n메일 : [          ]', { x: 7.05, y: 3.55, w: 2.3, h: 0.9, fontSize: 8.5, color: 'C9D6EA', lineSpacingMultiple: 1.2 });
    T(sl, 'Value for customers, Vision for us', { x: 0.7, y: 4.85, w: 5, h: 0.3, fontSize: 9, italic: true, color: C.GOLD });
    chrome(sl, true);
  }

  const out = process.argv[2] || 'proposal_r2.pptx';
  await pres.writeFile({ fileName: out });
  console.log('OK', out);
})().catch(e => { console.error(e); process.exit(1); });

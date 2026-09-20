/**
 * KM 제안서 빌더 v1 (2026-08-15)
 * 사용법:  node build_proposal.js spec.json out.pptx
 *
 * spec.json 한 개로 회사 표준 서식의 제안서 pptx가 나온다.
 * 슬라이드 타입 7종을 조합해 어떤 장수에도 맞출 수 있다.
 *
 * 왜 스크립트로 두는가: 매번 좌표를 새로 잡으면 현장마다 디자인이 달라진다.
 * 여기에 회사 표준(색·여백·글꼴·푸터)을 고정해 두면 내용만 바꿔 끼우면 된다.
 */
const pptxgen = require('pptxgenjs');
const fs = require('fs');

// 이미지 실제 픽셀 크기를 읽는다.
// pptxgenjs의 sizing:contain 은 이 환경에서 세로 사진을 가로로 늘려 버린다(2026-08-16 확인).
// 비율을 직접 계산해 w/h 를 넣는 편이 확실하다.
function imageSize(p) {
  try {
    const b = fs.readFileSync(p);
    if (b.slice(1, 4).toString() === 'PNG') return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
    if (b[0] === 0xFF && b[1] === 0xD8) {                      // JPEG
      let i = 2;
      while (i < b.length) {
        if (b[i] !== 0xFF) { i++; continue; }
        const m = b[i + 1];
        if (m >= 0xC0 && m <= 0xCF && m !== 0xC4 && m !== 0xC8 && m !== 0xCC)
          return { h: b.readUInt16BE(i + 5), w: b.readUInt16BE(i + 7) };
        i += 2 + b.readUInt16BE(i + 2);
      }
    }
  } catch (e) { /* 못 읽으면 박스에 꽉 채운다 */ }
  return null;
}
// 주어진 박스(bx,by,bw,bh) 안에 비율을 지켜 가운데 배치할 좌표를 돌려준다
function fitBox(p, bx, by, bw, bh) {
  const s = imageSize(p);
  if (!s) return { x: bx, y: by, w: bw, h: bh };
  const r = Math.min(bw / s.w, bh / s.h);
  const w = s.w * r, h = s.h * r;
  return { x: bx + (bw - w) / 2, y: by + (bh - h) / 2, w, h };
}

// ── 회사 표준 디자인 토큰 (바꾸지 말 것) ──────────────────────────
const T = {
  NAVY: '1F3864',      // 표지·맺음 배경, 표 머리글
  NAVY_D: '17284A',    // 표지 그라데 대용 딥
  BLUE: '2E74B5',      // 포인트(번호 원, 강조 텍스트)
  RED: 'C00000',       // 경고·기한
  GREEN_BG: 'E2EFD9',  // 결론 카드 배경
  GREEN_TX: '375623',  // 결론 카드 강조 글자
  GRAY_BG: 'F2F2F2',   // 확인·협의 박스
  GRAY_TX: '595959',   // 캡션·푸터
  LINE: 'D9D9D9',
  WHITE: 'FFFFFF',
  BODY: '333333',
  FONT: '맑은 고딕',
};
const M = { L: 0.5, R: 9.5, TOP: 0.45, W: 9.0, BOT: 5.15 };   // 10 x 5.625in 기준 여백


// ── v2 추가 : 한글 폭을 고려해 줄 수를 추정한다 (고정 높이 때문에 글이 겹치던 문제) ──
function estLines(text, widthIn, fontPt) {
  if (!text) return 0;
  const cw = c => (c.charCodeAt(0) > 0x1100 ? 1.0 : 0.52) * fontPt / 72;
  let lines = 1, cur = 0;
  for (const ch of String(text)) {
    if (ch === '\n') { lines++; cur = 0; continue; }
    const w = cw(ch);
    if (cur + w > widthIn) { lines++; cur = w; } else { cur += w; }
  }
  return lines;
}
function textH(text, widthIn, fontPt, pad) {
  return estLines(text, widthIn, fontPt) * fontPt * 1.34 / 72 + (pad === undefined ? 0.06 : pad);
}
// 페이지 번호 · PART 라벨
let PAGE = { n: 0, total: 0 };

function footer(slide, company, note, part) {
  slide.addShape('rect', { x: M.L, y: 5.19, w: M.W, h: 0.008, fill: { color: T.LINE } });
  slide.addText(note || '한국마이크로닉(주)', {
    x: M.L, y: 5.24, w: 5.5, h: 0.24, fontFace: T.FONT, fontSize: 8,
    color: T.GRAY_TX, align: 'left', margin: 0,
  });
  if (PAGE.total) {
    slide.addText([
      { text: (part || '') + (part ? '   ·   ' : ''), options: { color: T.GRAY_TX } },
      { text: String(PAGE.n), options: { color: T.NAVY, bold: true } },
      { text: ' / ' + PAGE.total, options: { color: T.GRAY_TX } },
    ], { x: 6.05, y: 5.24, w: 3.45, h: 0.24, fontFace: T.FONT, fontSize: 8,
         align: 'right', margin: 0 });
  }
}
function pageTitle(slide, title, eyebrow, pill) {
  let y = M.TOP;
  if (eyebrow) {
    slide.addText(eyebrow, { x: M.L, y: y, w: 6.0, h: 0.22, fontFace: T.FONT,
      fontSize: 9, color: T.GRAY_TX, margin: 0 });
    y += 0.26;
  }
  slide.addText(title, { x: M.L, y: y, w: 6.6, h: 0.45, fontFace: T.FONT,
    fontSize: 20, bold: true, color: T.NAVY, margin: 0 });
  slide.addShape('rect', { x: M.L, y: y + 0.5, w: 0.62, h: 0.045, fill: { color: T.BLUE } });
  if (pill) {
    slide.addShape('roundRect', { x: 7.05, y: y + 0.04, w: 2.45, h: 0.34,
      fill: { color: T.GRAY_BG }, line: { color: T.LINE, width: 0.5 }, rectRadius: 0.16 });
    slide.addText(pill, { x: 7.05, y: y + 0.04, w: 2.45, h: 0.34, fontFace: T.FONT,
      fontSize: 9, color: T.GRAY_TX, align: 'center', valign: 'middle', margin: 0 });
  }
  return y + 0.71;
}

// ── 슬라이드 타입 ────────────────────────────────────────────────
const BUILD = {
  // 1) 표지
  cover(pres, s) {
    const sl = pres.addSlide();
    sl.background = { color: T.NAVY };
    sl.addShape('rect', { x: 0.8, y: 1.28, w: 1.15, h: 0.055, fill: { color: '5B8FD6' } });
    sl.addShape('rect', { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: '5B8FD6' } });
    if (s.eyebrow) sl.addText(s.eyebrow, { x: 0.8, y: 1.45, w: 8.4, h: 0.3,
      fontFace: T.FONT, fontSize: 11, color: '9DB2D9', charSpacing: 2, margin: 0 });
    sl.addText(s.title, { x: 0.8, y: 1.85, w: 8.4, h: 0.9, fontFace: T.FONT,
      fontSize: 30, bold: true, color: T.WHITE, margin: 0 });
    if (s.subtitle) sl.addText(s.subtitle, { x: 0.8, y: 2.85, w: 8.4, h: 0.4,
      fontFace: T.FONT, fontSize: 14, color: 'C9D6EA', margin: 0 });
    // 문서 관리 정보 — 갑에 제출하는 문서는 수신/발신/문서번호/일자가 있어야 공식 문서가 된다
    const d = s.doc;
    if (d) {
      const rows = [
        ['수 신', d.to], ['발 신', d.from || '한국마이크로닉(주)'],
        ['문서번호', d.no], ['작성일자', d.date], ['회신요청', d.due],
      ].filter(r => r[1]);
      const top = 3.35, lh = 0.28;
      rows.forEach((r, i) => {
        sl.addText(r[0], { x: 0.8, y: top + i * lh, w: 1.0, h: lh, fontFace: T.FONT,
          fontSize: 9, color: '8FA3C8', margin: 0 });
        sl.addText(r[1], { x: 1.85, y: top + i * lh, w: 6.5, h: lh, fontFace: T.FONT,
          fontSize: 9.5, color: i === 4 ? 'FFC7C2' : 'DCE6F5',
          bold: i === 4, margin: 0 });
      });
    } else {
      sl.addText(s.meta || '한국마이크로닉(주)', { x: 0.8, y: 4.55, w: 8.4, h: 0.3,
        fontFace: T.FONT, fontSize: 10, color: '8FA3C8', margin: 0 });
    }
    return sl;
  },

  // 2) 결론 + 핵심 카드 (2~4장) + 기한 배너
  conclusion(pres, s) {
    const sl = pres.addSlide();
    let y = pageTitle(sl, s.title || '검토 결론', s.eyebrow);
    if (s.headline) {
      const hh = textH(s.headline, M.W, 12, 0.10);
      sl.addText(s.headline, { x: M.L, y: y, w: M.W, h: hh, fontFace: T.FONT,
        fontSize: 12, color: T.BODY, margin: 0 });
      y += hh + 0.12;
    }
    // 카드는 남는 세로 공간을 채운다 — 장수가 적을수록 한 장이 허전해 보이면 안 된다
    const cards = s.cards || [];
    const bannerH = s.banner ? textH('※ ' + s.banner, M.W - 0.3, 10, 0.26) : 0;
    if (cards.length) {
      const gap = 0.25, w = (M.W - gap * (cards.length - 1)) / cards.length;
      const bodyLines = Math.max(...cards.map(c => estLines(c.body || '', (M.W / cards.length) - 0.3, 10.5)));
      const need = 0.54 + bodyLines * 10.5 * 1.3 / 72 + 0.74;
      const h = Math.max(1.55, Math.min(need + 0.12, M.BOT - y - bannerH - 0.15));
      cards.forEach((c, i) => {
        const x = M.L + i * (w + gap);
        sl.addShape('roundRect', { x, y, w, h, fill: { color: c.bg || T.GREEN_BG },
          line: { color: T.LINE, width: 0.5 }, rectRadius: 0.08 });
        sl.addText(c.label, { x: x + 0.15, y: y + 0.18, w: w - 0.3, h: 0.3,
          fontFace: T.FONT, fontSize: 11, bold: true, color: T.GREEN_TX, align: 'center', margin: 0 });
        sl.addText(c.body, { x: x + 0.15, y: y + 0.54, w: w - 0.3, h: h - 1.18,
          fontFace: T.FONT, fontSize: 10.5, color: T.BODY, align: 'center', valign: 'top', margin: 0, lineSpacingMultiple: 1.22 });
        if (c.big) sl.addText(c.big, { x: x + 0.15, y: y + h - 0.62, w: w - 0.3, h: 0.45,
          fontFace: T.FONT, fontSize: 15, bold: true, color: T.GREEN_TX, align: 'center', margin: 0 });
      });
      y += h + 0.15;
    }
    if (s.banner) {
      const bh = bannerH - 0.06, by = M.BOT - bh;
      sl.addShape('rect', { x: M.L, y: by, w: M.W, h: bh, fill: { color: 'FDECEA' },
        line: { color: 'F5C6C0', width: 0.5 } });
      sl.addText('※ ' + s.banner, { x: M.L + 0.15, y: by, w: M.W - 0.3, h: bh,
        fontFace: T.FONT, fontSize: 10, bold: true, color: T.RED, valign: 'middle', margin: 0 });
    }
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 3) 표 (비교표·상세표) — 머리글 네이비
  table(pres, s) {
    const sl = pres.addSlide();
    const y = pageTitle(sl, s.title, s.eyebrow, s.pill);
    const heads = s.headers.map(h => ({
      text: h, options: { fill: T.NAVY, color: T.WHITE, bold: true, align: 'center', valign: 'middle' },
    }));
    const rows = s.rows.map((r, ri) => r.map((cell, ci) => ({
      text: String(cell),
      options: {
        fill: ri % 2 ? 'F7F9FC' : T.WHITE,
        bold: ci === 0,
        color: ci === 0 ? T.NAVY : T.BODY,
        align: ci === 0 ? 'left' : 'left',
        valign: 'middle',
      },
    })));
    const noteH = s.note ? textH('※ ' + s.note, M.W, 8, 0.10) : 0;
    const avail = M.BOT - y - noteH;
    sl.addTable([heads, ...rows], {
      x: M.L, y, w: M.W, colW: s.colW || undefined,
      border: { type: 'solid', color: T.LINE, pt: 0.5 },
      fontFace: T.FONT, fontSize: s.fontSize || 9, autoPage: false,
      rowH: Math.max(0.26, Math.min(0.62, (avail - 0.12) / (rows.length + 1))),
    });
    if (s.note) sl.addText('※ ' + s.note, { x: M.L, y: M.BOT - noteH + 0.02, w: M.W, h: noteH,
      fontFace: T.FONT, fontSize: 8, color: T.GRAY_TX, margin: 0, valign: 'top' });
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 4) 번호 항목 (작업 단계·요청사항·구성요소)
  items(pres, s) {
    const sl = pres.addSlide();
    let y = pageTitle(sl, s.title, s.eyebrow, s.pill);
    if (s.lead) { sl.addText(s.lead, { x: M.L, y, w: M.W, h: 0.32, fontFace: T.FONT,
      fontSize: 11, color: T.BODY, margin: 0 }); y += 0.45; }
    const its = s.items || [];
    const avail = M.BOT - y - (s.box ? 1.0 : 0.1);
    const h = Math.max(0.34, Math.min(0.68, avail / Math.max(its.length, 1)));
    its.forEach((it, i) => {
      const yy = y + i * h;
      sl.addShape('ellipse', { x: M.L, y: yy + (h - 0.3) / 2, w: 0.3, h: 0.3, fill: { color: T.BLUE } });
      sl.addText(String(i + 1), { x: M.L, y: yy + (h - 0.3) / 2, w: 0.3, h: 0.3, fontFace: T.FONT,
        fontSize: 10, bold: true, color: T.WHITE, align: 'center', valign: 'middle', margin: 0 });
      const t = typeof it === 'string' ? { text: it } : it;
      sl.addText(t.text, { x: M.L + 0.42, y: yy, w: M.W - 0.42, h: t.desc ? h * 0.55 : h,
        fontFace: T.FONT, fontSize: 11, bold: !!t.desc, color: T.BODY, valign: 'middle', margin: 0 });
      if (t.desc) sl.addText(t.desc, { x: M.L + 0.42, y: yy + h * 0.5, w: M.W - 0.42, h: h * 0.45,
        fontFace: T.FONT, fontSize: 9, color: T.GRAY_TX, valign: 'top', margin: 0 });
    });
    if (s.box) {
      const by = M.BOT - 0.95;
      sl.addShape('rect', { x: M.L, y: by, w: M.W, h: 0.9, fill: { color: T.GRAY_BG }, line: { color: T.LINE, width: 0.5 } });
      sl.addText(s.box.title || '확인 · 협의 사항', { x: M.L + 0.15, y: by + 0.06, w: M.W - 0.3, h: 0.24,
        fontFace: T.FONT, fontSize: 9, bold: true, color: T.NAVY, margin: 0 });
      sl.addText((s.box.lines || []).map((l, i, a) => ({ text: l, options: { bullet: true, breakLine: i !== a.length - 1 } })),
        { x: M.L + 0.15, y: by + 0.3, w: M.W - 0.3, h: 0.55, fontFace: T.FONT, fontSize: 8.5, color: T.BODY, margin: 0 });
    }
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 5) 이미지 1장 + 캡션 (계통도·다이어그램·현장 사진)
  figure(pres, s) {
    const sl = pres.addSlide();
    const y = pageTitle(sl, s.title, s.eyebrow, s.pill);
    const capH = s.caption ? textH(s.caption, M.W - 0.4, 10, 0.12) : 0;
    if (s.image && fs.existsSync(s.image)) {
      sl.addImage({ path: s.image, x: M.L, y, w: M.W, h: M.BOT - y - capH, sizing: { type: 'contain', w: M.W, h: M.BOT - y - capH } });
    } else {
      sl.addShape('rect', { x: M.L, y, w: M.W, h: M.BOT - y - capH, fill: { color: 'FFF7E0' }, line: { color: 'E8C97A', width: 1 } });
      sl.addText(s.placeholder || '[ 이미지 삽입 필요 ]', { x: M.L, y, w: M.W, h: M.BOT - y - capH,
        fontFace: T.FONT, fontSize: 12, color: '8A6D1F', align: 'center', valign: 'middle', margin: 0 });
    }
    if (s.caption) sl.addText(s.caption, { x: M.L + 0.2, y: M.BOT - capH, w: M.W - 0.4, h: capH,
      fontFace: T.FONT, fontSize: 10, color: T.GRAY_TX, align: 'center', valign: 'top', margin: 0 });
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 6) 구성도 + 번호 설명 — 설명 자료의 주력 타입
  //    (그림만 있으면 담당자가 해석을 못 하고, 글만 있으면 안 읽는다. 둘을 한 장에 붙인다)
  diagram(pres, s) {
    const sl = pres.addSlide();
    let y = pageTitle(sl, s.title, s.eyebrow, s.pill);
    if (s.lead) {
      sl.addText(s.lead, { x: M.L, y, w: M.W, h: 0.3, fontFace: T.FONT,
        fontSize: 11, color: T.BODY, margin: 0 });
      y += 0.42;
    }
    const steps = s.steps || [];
    const stepH = steps.length ? 1.02 : 0;
    const imgH = Math.max(1.6, M.BOT - y - stepH - 0.1);
    if (s.image && fs.existsSync(s.image)) {
      sl.addImage({ path: s.image, x: M.L, y, w: M.W, h: imgH,
        sizing: { type: 'contain', w: M.W, h: imgH } });
    } else {
      sl.addShape('rect', { x: M.L, y, w: M.W, h: imgH, fill: { color: 'FFF7E0' },
        line: { color: 'E8C97A', width: 1 } });
      sl.addText(s.placeholder || '[ 구성도 이미지 필요 ]', { x: M.L, y, w: M.W, h: imgH,
        fontFace: T.FONT, fontSize: 12, color: '8A6D1F', align: 'center', valign: 'middle', margin: 0 });
    }
    if (steps.length) {
      const sy = y + imgH + 0.08, gap = 0.2;
      const w = (M.W - gap * (steps.length - 1)) / steps.length;
      steps.forEach((st, i) => {
        const x = M.L + i * (w + gap);
        sl.addShape('rect', { x, y: sy, w, h: 0.94, fill: { color: 'F7F9FC' },
          line: { color: T.LINE, width: 0.5 } });
        sl.addShape('ellipse', { x: x + 0.12, y: sy + 0.13, w: 0.28, h: 0.28, fill: { color: T.BLUE } });
        sl.addText(String(st.num || i + 1), { x: x + 0.12, y: sy + 0.13, w: 0.28, h: 0.28,
          fontFace: T.FONT, fontSize: 9, bold: true, color: T.WHITE, align: 'center', valign: 'middle', margin: 0 });
        sl.addText(st.text, { x: x + 0.46, y: sy + 0.1, w: w - 0.58, h: 0.34,
          fontFace: T.FONT, fontSize: 10, bold: true, color: T.NAVY, valign: 'middle', margin: 0 });
        if (st.who) sl.addText(st.who, { x: x + 0.46, y: sy + 0.42, w: w - 0.58, h: 0.22,
          fontFace: T.FONT, fontSize: 8.5, color: T.RED, margin: 0 });
        if (st.desc) sl.addText(st.desc, { x: x + 0.14, y: sy + 0.64, w: w - 0.28, h: 0.26,
          fontFace: T.FONT, fontSize: 8.5, color: T.GRAY_TX, margin: 0 });
      });
    }
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 6-2) 회신란 — 협의서의 마지막 장. 상대가 답을 적을 칸을 비워 둔다.
  //      킨텍스 질의답변서의 「운영사 답변」 빈칸 패턴. 이 칸이 없으면 협의서는 읽히고 끝난다.
  reply(pres, s) {
    const sl = pres.addSlide();
    let y = pageTitle(sl, s.title || '회신 요청', s.eyebrow, s.pill);
    if (s.lead) {
      sl.addText(s.lead, { x: M.L, y, w: M.W, h: 0.3, fontFace: T.FONT,
        fontSize: 10.5, color: T.BODY, margin: 0 });
      y += 0.42;
    }
    const heads = ['협의 항목', '당사 의견', '귀사 회신'].map((h, i) => ({
      text: h, options: { fill: i === 2 ? '7F7F7F' : T.NAVY, color: T.WHITE,
        bold: true, align: 'center', valign: 'middle' },
    }));
    const rows = (s.rows || []).map((r, ri) => ([
      { text: r.item, options: { fill: ri % 2 ? 'F7F9FC' : T.WHITE, bold: true,
        color: T.NAVY, valign: 'middle' } },
      { text: r.ours || '', options: { fill: ri % 2 ? 'F7F9FC' : T.WHITE,
        color: T.BODY, valign: 'middle' } },
      { text: '', options: { fill: 'FFFDF0', valign: 'middle' } },   // 회신칸은 비워 둔다
    ]));
    const foot = s.deadline ? textH(s.deadline, M.W - 0.3, 10, 0.26) : 0.1;
    const avail = M.BOT - y - foot;
    sl.addTable([heads, ...rows], {
      x: M.L, y, w: M.W, colW: s.colW || [2.3, 4.0, 2.7],
      border: { type: 'solid', color: T.LINE, pt: 0.5 },
      fontFace: T.FONT, fontSize: s.fontSize || 9.5, autoPage: false,
      rowH: Math.max(0.32, Math.min(0.75, (avail - 0.3) / (rows.length + 1))),
    });
    if (s.deadline) {
      const dh = foot - 0.06, dy = M.BOT - dh;
      sl.addShape('rect', { x: M.L, y: dy, w: M.W, h: dh, fill: { color: 'FDECEA' },
        line: { color: 'F5C6C0', width: 0.5 } });
      sl.addText(s.deadline, { x: M.L + 0.15, y: dy, w: M.W - 0.3, h: dh, fontFace: T.FONT,
        fontSize: 10, bold: true, color: T.RED, valign: 'middle', margin: 0 });
    }
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 7) 1안 / 2안 사진 비교 — 갑에게 형식을 고르게 할 때 쓰는 타입
  //    사진이 주인공이고 글은 거드는 구조. 읽는 사람이 "공부"하지 않고 보고 고르게 한다.
  compare(pres, s) {
    const sl = pres.addSlide();
    let y = pageTitle(sl, s.title, s.eyebrow, s.pill);
    if (s.lead) {
      sl.addText(s.lead, { x: M.L, y, w: M.W, h: 0.3, fontFace: T.FONT,
        fontSize: 11, color: T.BODY, margin: 0 });
      y += 0.44;
    }
    const askH = s.ask ? 0.46 : 0;
    const cols = [s.left, s.right];
    const gap = 0.35, w = (M.W - gap) / 2;
    const bodyBottom = M.BOT - askH - 0.08;
    cols.forEach((c, i) => {
      const x = M.L + i * (w + gap);
      // 라벨 바
      sl.addShape('rect', { x, y, w, h: 0.42, fill: { color: i ? '4A6FA5' : T.NAVY } });
      sl.addText(c.label, { x, y, w, h: 0.42, fontFace: T.FONT, fontSize: 12, bold: true,
        color: T.WHITE, align: 'center', valign: 'middle', margin: 0 });
      // 설명 줄 (사진 아래) — 줄 수만큼만 자리를 준다
      const lines = c.lines || [];
      const txtH = lines.length ? Math.min(1.4, lines.length * 0.30 + 0.06) : 0;
      const capH = c.caption ? 0.24 : 0;
      const imgY = y + 0.42 + 0.10;
      const imgH = bodyBottom - imgY - txtH - capH;
      if (c.image && fs.existsSync(c.image)) {
        const f = fitBox(c.image, x, imgY, w, imgH);
        sl.addImage({ path: c.image, x: f.x, y: f.y, w: f.w, h: f.h });
        if (c.caption) sl.addText(c.caption, { x, y: imgY + imgH, w, h: capH,
          fontFace: T.FONT, fontSize: 8.5, color: T.GRAY_TX, align: 'center', valign: 'top', margin: 0 });
      } else {
        sl.addShape('rect', { x, y: imgY, w, h: imgH, fill: { color: 'FFF7E0' },
          line: { color: 'E8C97A', width: 1 } });
        sl.addText(c.placeholder || '[ 사진 삽입 ]', { x, y: imgY, w, h: imgH,
          fontFace: T.FONT, fontSize: 11, color: '8A6D1F', align: 'center', valign: 'middle', margin: 0 });
        if (c.caption) sl.addText(c.caption, { x, y: imgY + imgH, w, h: capH,
          fontFace: T.FONT, fontSize: 8.5, color: T.GRAY_TX, align: 'center', valign: 'top', margin: 0 });
      }
      if (lines.length) {
        sl.addText(lines.map((l, j, a) => ({ text: l,
          options: { bullet: true, breakLine: j !== a.length - 1, paraSpaceAfter: 5 } })),
          { x: x + 0.1, y: bodyBottom - txtH, w: w - 0.2, h: txtH, fontFace: T.FONT,
            fontSize: 10, color: T.BODY, valign: 'top', margin: 0 });
      }
    });
    if (s.ask) {
      const ay = M.BOT - 0.42;
      sl.addShape('rect', { x: M.L, y: ay, w: M.W, h: 0.42, fill: { color: 'FDECEA' },
        line: { color: 'F5C6C0', width: 0.5 } });
      sl.addText(s.ask, { x: M.L + 0.15, y: ay, w: M.W - 0.3, h: 0.42, fontFace: T.FONT,
        fontSize: 10, bold: true, color: T.RED, valign: 'middle', margin: 0 });
    }
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 8) 좌우 2단 (기존 vs 제안, 안A vs 안B)
  split(pres, s) {
    const sl = pres.addSlide();
    const y = pageTitle(sl, s.title, s.eyebrow, s.pill);
    const w = (M.W - 0.3) / 2;
    // 박스는 가용 높이를 채우고, 줄이 적으면 줄 간격을 벌려 균등하게 보이게 한다.
    // (박스만 줄이면 아래가 통째로 비어 허전하고, 간격을 고정하면 위로 몰린다)
    const maxLines = Math.max((s.left.lines || []).length, (s.right.lines || []).length, 1);
    const bodyH = M.BOT - y - 0.45;
    const gapPt = Math.max(6, Math.min(26, ((bodyH - 0.35) / maxLines - 0.24) * 72));
    [s.left, s.right].forEach((col, i) => {
      const x = M.L + i * (w + 0.3);
      sl.addShape('rect', { x, y, w, h: 0.4, fill: { color: i ? T.BLUE : '7F7F7F' } });
      sl.addText(col.label, { x, y, w, h: 0.4, fontFace: T.FONT, fontSize: 11, bold: true,
        color: T.WHITE, align: 'center', valign: 'middle', margin: 0 });
      sl.addShape('rect', { x, y: y + 0.4, w, h: bodyH, fill: { color: i ? 'F2F7FC' : 'FAFAFA' },
        line: { color: T.LINE, width: 0.5 } });
      sl.addText((col.lines || []).map((l, j, a) => ({ text: l, options: { bullet: true, breakLine: j !== a.length - 1, paraSpaceAfter: gapPt } })),
        { x: x + 0.18, y: y + 0.5, w: w - 0.36, h: bodyH - 0.2, fontFace: T.FONT,
          fontSize: 10.5, color: T.BODY, valign: 'middle', margin: 0 });
    });
    footer(sl, null, s.footer, s.part);
    return sl;
  },

  // 8) 요청사항 / 맺음 (네이비)
  request(pres, s) {
    const sl = pres.addSlide();
    sl.background = { color: T.NAVY };
    sl.addShape('rect', { x: 0, y: 5.5, w: 10, h: 0.125, fill: { color: '5B8FD6' } });
    sl.addShape('rect', { x: 0.8, y: 0.38, w: 1.15, h: 0.055, fill: { color: '5B8FD6' } });
    sl.addText(s.title || '요청드리는 사항', { x: 0.8, y: 0.55, w: 8.4, h: 0.5,
      fontFace: T.FONT, fontSize: 22, bold: true, color: T.WHITE, margin: 0 });
    if (s.lead) sl.addText(s.lead, { x: 0.8, y: 1.1, w: 8.4, h: 0.3, fontFace: T.FONT,
      fontSize: 12, color: 'C9D6EA', margin: 0 });
    const its = s.items || [];
    const top = 1.65, h = Math.min(0.95, (4.5 - top) / Math.max(its.length, 1));
    its.forEach((it, i) => {
      const yy = top + i * h;
      sl.addShape('ellipse', { x: 0.8, y: yy, w: 0.34, h: 0.34, fill: { color: '5B8FD6' } });
      sl.addText(String(i + 1), { x: 0.8, y: yy, w: 0.34, h: 0.34, fontFace: T.FONT, fontSize: 10,
        bold: true, color: T.WHITE, align: 'center', valign: 'middle', margin: 0 });
      sl.addText(it.text, { x: 1.28, y: yy - 0.03, w: 7.9, h: 0.3, fontFace: T.FONT,
        fontSize: 12, bold: true, color: T.WHITE, margin: 0 });
      if (it.desc) sl.addText(it.desc, { x: 1.28, y: yy + 0.27, w: 7.9, h: 0.3, fontFace: T.FONT,
        fontSize: 9.5, color: 'B9C8E0', margin: 0 });
    });
    sl.addText(s.contact || '문의 | 한국마이크로닉(주) 배성윤 차장', { x: 0.8, y: 4.85, w: 8.4, h: 0.3,
      fontFace: T.FONT, fontSize: 10, color: '8FA3C8', margin: 0 });
    return sl;
  },
};

// ── 실행 ────────────────────────────────────────────────────────
function build(spec, outPath) {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';           // 10 x 5.625 in — 좌표는 전부 이 기준
  pres.author = '한국마이크로닉(주)';
  pres.title = spec.title || '제안서';
  const slides = spec.slides || [];
  PAGE.total = slides.length;
  slides.forEach((s, i) => {
    const fn = BUILD[s.type];
    if (!fn) throw new Error(`알 수 없는 슬라이드 타입: ${s.type} (${i + 1}번째)`);
    if (spec.footer && !s.footer) s.footer = spec.footer;
    PAGE.n = i + 1;
    if (!s.part && s.eyebrow) {
      const m = String(s.eyebrow).match(/^([ⅠⅡⅢⅣⅤⅥ]\.[^·]*)/);
      if (m) s.part = m[1].trim();
    }
    fn(pres, s);
  });
  return pres.writeFile({ fileName: outPath }).then(() => {
    console.log(`OK  ${outPath}  (${(spec.slides || []).length}장)`);
  });
}

if (require.main === module) {
  const [, , specPath, outPath] = process.argv;
  if (!specPath || !outPath) { console.error('usage: node build_proposal.js spec.json out.pptx'); process.exit(1); }
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  build(spec, outPath).catch(e => { console.error(e); process.exit(1); });
}
module.exports = { build, T };

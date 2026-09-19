# 객실관리 시스템 제안서 (범용) — 변경 이력 · 자가진단

정본 위치 : 이 폴더. 새 판은 덮어쓰지 않고 `r2`, `r3` 로 낸다. "○번 되돌려" 하시면 그 r 로 복구.
현장명은 `[현장명]` 빈칸이며, 현장이 정해지면 spec 의 `[현장명]` 을 바꿔 r2 로 다시 빌드한다.

## 만든 방법 (새 창이 그대로 재현할 수 있게)
**r3 (현행)** : `node build_r3.js out.pptx` (15장). **r2** : `node build_r2.js out.pptx` (10장) — 스크립트 안 `IMG` 경로(스킬 assets 사진, diag png)만 맞추면 된다. 사진은 km-spec-builder/assets/png(제품)·km-proposal/assets/photos(현장).

**r1 (이전)** :
1. `diag_*_r1.json` → km-proposal 스킬 `assets/draw_diagram.py` 로 png 2장
2. `spec_r1.json` → `assets/build_proposal.js` (pptxgenjs) 로 pptx 10장
3. LibreOffice Impress → PDF (조회본)
- 필요 패키지 : node pptxgenjs, python matplotlib·pymupdf, fonts-noto-cjk, libreoffice-impress
- spec 안의 `image` 경로는 스크래치 절대경로라, 재빌드 때 이 폴더의 `diag_*_r1.png` 경로로 바꿔야 한다.

## 구성 (10장) — 내가 정한 구성이며 프로님 확인 전
| 장 | 유형 | 내용 | 근거 |
|---|---|---|---|
| 1 | cover | 표지 · 현장명 빈칸 | §8 표기 표준 |
| 2 | conclusion | 제안 요약 · 카드 3 · 기한 배너 | 결론 먼저 |
| 3 | figure | 운영 시나리오 8단계 (PMS 연동) | operation-scenario §1 원문 |
| 4 | figure | 시스템 구성도 (발주처 공사분 표기) | operation-scenario §2, tech-constants |
| 5 | table | 주요 제품 구성 8종 | operation-scenario 주요 제품 문구 |
| 6 | table | 객실 표준 구성 등급별 (1~3성급·리조트 / 4~5성급) | 프로님 확정 배치 규칙 (km-room-layout) |
| 7 | items | 공사 프로세스 6단계 + 협의 사항 | tech-constants 6단계 |
| 8 | table | 공사 구분 (당사/전기/발주처·기타) 8공정 | workscope r2 요약 |
| 9 | table | 주요 실적 — 납품 문서 기준, 확정본으로 교체 | km-photo-sheet 납품본 목록 등 |
| 10 | request | 요청 3 (평면도 · 냉난방/PMS · 협의 일정) | §0 결정은 상대가 |

## 변경 이력
| 판 | 날짜 | 바꾼 것 | 등급 |
|---|---|---|---|
| r1 | 2026-09-19 | 최초 작성. 프로님 지시 "니 마음대로 구성해서 만들어봐" | A |
| r3 | 2026-09-19 | 프로님 지시 "5장 더 추가해" → 15장. 추가 5장 : 냉난방 연동(회사 EHP 구성도 example_diagram_ehp) · 도어락 연동·주거약자실 · 관제 소프트웨어 화면(운영 매뉴얼 상수, 화면은 모의 그리드) · 표준 도입 일정(km-site-schedule 소요일 9단계) · 당사 강점 5축(B-2 논거 당사 측만). `build_r3.js` | A |
| r2 | 2026-09-19 | 프로님 지시 "pptx 스킬로, PDF 없이, 사람이 만든 듯이". pptxgenjs 직접 작성(`build_r2.js`) — 제품 사진 10종·현장 사진 4장·아이콘, 표지 반면 사진, 제품 카드 4×2, 공정 타임라인, 담당 매트릭스(●/○). 독립 감사 지적 반영: 구성도 겹침 4건, 9장 내부 메모 문구→발표자 노트로, 조사 띄어쓰기, 파일 속성 subject. r1 PDF 는 저장소에서 제거(프로님 "PDF 필요 없어") | B |

## 자가진단 (r3)
- [x] validate 통과 / 15장 렌더 육안 확인(신규 5장 전부) / 조사 grep 0건
- [ ] 확인 요청 : 6장 「비상호출 시 관제 PC에 표시」 문장(기준 문서에 없음, 상식으로 넣음) / 9장 관제 화면은 모의 화면 / 11장 소요일은 km-site-schedule 표준값

## 자가진단 (r2)
- [x] validate.py 통과 / 렌더 10장 육안 확인 / 조사 띄어쓰기 grep 0건 / core.xml subject 교체
- [x] r1 독립 감사 지적 5건 반영 (구성도 겹침·내부 메모·조사·BSP 문구 결정·subject)
- [ ] BSP 구성 문구 : tech-constants 원문(콘센트+USB+L)이 아니라 프로님 규칙(온도+조명+USB+콘센트)으로 둠 — 확인 요청

## 자가진단 (r1)
- [x] 장수 10 = 렌더 10 (pymupdf 로 셈)
- [x] 10장 전부 렌더 육안 확인 — 3회 재빌드 (구성도 축소, 표·주석 겹침, 라벨 겹침 수정)
- [x] 금액·요율·단가 없음
- [x] 「장애인실」 없음 → 주거약자실
- [x] 독립 감사 서브에이전트 실행 (결과는 채팅 보고에)
- [ ] 프로님 확인 : 구성 10장이 맞는지, 실적 목록 교체, 현장명

## 확신 없이 넣은 것 (④ 자가신고)
- 9장 실적 목록 : 회사 확정 실적표를 못 봤다. 스킬에 남은 납품 문서 현장명을 옮겼고 「확정본으로 교체」 라고 슬라이드에 적었다. 연도·객실 수는 빈칸.
- 2장 카드 문구 「전국 직영 A/S」「RJ45 원터치 결선」 : tech-constants 의 B-2 논거에서 가져옴. 발주처 제출 전 프로님 확인 필요.
- 7장 협의 박스의 시공 조건은 공사한계 r2 문장을 옮긴 것이며 현장별로 다를 수 있음.

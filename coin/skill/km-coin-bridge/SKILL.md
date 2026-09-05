---
name: km-coin-bridge
description: "배성윤 차장의 코인(ETH) 자동매매 중계 브리지 정본 (v1, 2026-09-05, 9칸 골격). 트레이딩뷰 알럿 → Google Apps Script(deepcoin-bridge v2.x) → 딥코인 무기한선물 시장가 주문. 코드·Pine 배선 원틀·체크리스트·모의 실행기의 정본 위치는 GitHub gamakatu-PM/mic-pm 의 coin/ 폴더이며, Claude 는 배포 권한이 없다(차장님이 Apps Script 에 붙여넣음). '코인', '딥코인', '자동매매', '브리지', '트레이딩뷰', 'Pine', '알럿', '손절', '잔고추이', 'KILL', 'LIVE 켜도 돼?', '코인 로그 봐줘', '김남기 통화', '수수료 0.4' 관련이면 반드시 이 스킬을 먼저 읽고, 구조·탭 이름·문 9개를 새로 상상하지 말 것. v1 코드(드라이브 deepcoin-bridge.gs)는 결함 3건이 있어 실전 금지."
---

# km-coin-bridge v1 — 코인 자동매매 브리지 정본 (2026-09-05)

> 회사 업무(호텔 객실관리)가 아닌 **차장님 개인 투자 자동화**다. 회사 스킬(km-00-router 계열)과 섞지 않는다. 저장 위치는 GitHub `gamakatu-PM/mic-pm` → `coin/` 하나뿐. 노션·회의록 시트에 쓰지 않는다.

## 0. 이미 있는 것 — 다시 만들지 않는다
- **정본 코드**: `coin/deepcoin-bridge-v2.gs` (v2.3, 2026-09-05). Google Apps Script 웹앱. 차장님이 편집기에 붙여넣고 배포한다 — Claude 는 배포·실행 권한이 없다.
- **Pine 배선 원틀**: `coin/pine-alert-wiring.pine`. 전략 신호 두 줄(★ longSig/shortSig)만 차장님 전략으로 바꾸면 알럿 JSON(ETH 수량·손절·익절·진입가·id)이 `alert_message` 로 조립된다.
- **알럿 설정**: `coin/tradingview-alert.json` — A(권장) 메시지 칸 `{{strategy.order.alert_message}}` 한 줄 / B(수동, 손절 없음).
- **체크리스트**: `coin/CHECKLIST.md` — 설치 → 모의(DRY-RUN) → 실전 전환(소액) → 매일 볼 것 → 사고 시 → 되돌리기.
- **설계 한 장**: `coin/README.md` — 문 9개, v1 결함 3건, 대안 3개와 잃는 것, 못 하는 것, 검증 결과.
- **모의 실행기**: `coin/test/run-tests.js` + `gas-mock.js`. `node coin/test/run-tests.js` → 89건 PASS 가 기준선. 코드를 고치면 반드시 다시 돌린다.
- **로그 시트**: 드라이브 「딥코인-자동매매-로그」 `1NVDDAue2Arm5xvi8shkwZs2Yg5pu2HtldNgo6RduxKI`. 탭: `0.자가진단` / `1.거래로그`(12열) / `2.설정`(KILL·ALLOWED_SYMBOLS·MAX_CONTRACTS·MAX_TRADES_PER_DAY·ALLOW_PYRAMID·NOTIFY_EMAIL) / `3.잔고추이`. v1 이 남긴 첫 탭(5열 머리글)은 건드리지 않는다.
- **v1 원본**: 드라이브 문서 `deepcoin-bridge.gs` `1E3vJ7GFzJH_4n0vSZPjgnk30ni1W-_tKH7tZ3sCqANs` (2026-08-08). 결함 3건: ①주문 거절(code:"0"+sCode)을 성공 처리 ②청산 수량을 로컬 기록에서 읽음 ③잔고 경로 오류·규격 밖 slOrdPx. **실전에 쓰지 않는다.**
- **딥코인 API 규격 근거**: 공식 문서 사이트는 Claude 작업 환경에서 차단됨. ccxt `deepcoin.ts`(github ccxt/ccxt) 로 대조: 서명 `Base64(HMAC-SHA256(ts+METHOD+path(+?query)+body))`, 헤더 `DC-ACCESS-KEY/SIGN/TIMESTAMP/PASSPHRASE` + `appid:200103`, 주문 `POST /deepcoin/trade/order`(instId·tdMode·mrgPosition·side·posSide·ordType·sz·reduceOnly·slTriggerPx·tpTriggerPx), 포지션 `GET /deepcoin/account/positions?instType=SWAP&instId=`, 잔고 `GET /deepcoin/account/balances?instType=SWAP`, 계약단위 `GET /deepcoin/market/instruments?instType=SWAP`(ctVal). 거절은 `data.sCode≠"0"`(24/31/36/44/49/194/195).
- **인물**: 김남기(010-2589-2300) — 거래 지원 담당자. PLAUD 「다음김남기주식코인」 통화 4건(8/5·8/6·8/11·8/19). 수수료 0.4(딥코인/파이넥스) · 0.6(원래) · 0.81(바이낸스) — 단위 미확정.

## 1. 라우터 기준
회사 라우터(km-00-router) 밖의 **개인 영역**. 저장 위치: `GitHub gamakatu-PM/mic-pm coin/` (코드·문서) + 드라이브 로그 시트(실행 기록). 노션 금지. 코드 전달은 SendUserFile 로 파일째.

## 2. 언제 쓰나
"코인/딥코인/자동매매/브리지 손봐" / "트레이딩뷰 알럿이 안 와" / "Pine 코드 붙인다" / "LIVE 켜도 돼?" / "코인 로그 봐줘" / "잔고추이 봐" / "김남기 통화 정리" / "수수료 얼마야" / 새 종목·새 거래소 추가 요청.

## 3. 입력 체크리스트
| 필요한 것 | 없을 때 묻는 문장 |
|---|---|
| 「0.자가진단」 캡처 또는 시트 열람 | "자가진단 탭 캡처를 보내주세요. 「잔고 조회」가 OK 인지가 키·서명 실증입니다" |
| 「1.거래로그」 마지막 행들 | 드라이브에서 직접 읽는다(묻지 않음). 못 읽으면 캡처 요청 |
| 차장님 Pine 전략 코드(또는 진입·청산 조건 한 줄) | "전략 코드를 붙여주시거나, 어떤 조건에서 사고 파는지 한 줄로 말씀해 주세요" |
| 상한값(계약수·일일횟수)·ETH 수량·손절% | **Claude 가 정하지 않는다.** 노란칸(2.설정 탭·Pine 입력칸)에 차장님이 넣는다. 출발값만 제시 |
| 현재 코드가 정본과 같은가 | GitHub coin/ 의 VERSION 과 자가진단 「버전」 행을 대조. 다르면 정본을 다시 보낸다 |

## 4. 산출물 규격
- **코드 수정**: 정본 `.gs` 전체 파일로 전달(부분 교체 지시는 타이핑 사고를 부른다). 머리말 이력에 `v○ → v○ (날짜) 무엇을 왜` 한 줄 추가. VERSION 상수 갱신. 모의 실행기 검사를 추가하고 전부 PASS 시킨 뒤에만 낸다.
- **문 9개는 순서·의미를 바꾸지 않는다**: ①토큰 ②잠금 ③중복(DUP, 먼저 표시) ④KILL(캐시 없음) ⑤상한 3종(초과·오입력 모두 거절) ⑥거래소 포지션 조회(ALREADY_IN/청산 수량) ⑦주문(LIVE=YES 만) ⑧주문 후 재조회(OK/⚠/PARTIAL, 조회 실패도 LIVE 로 기록) ⑨시트+메일. 새 안전장치는 추가(A)만, 기존 문 제거는 C 등급.
- **Pine 수정**: 원틀의 `f_msg()` JSON 키(token·action·symbol·qty·price·sl·tp·id)를 바꾸지 않는다. 전략 신호만 ★ 두 줄에 잇는다.
- **상한·수량·요율은 노란칸**: 코드 기본값(50계약/20회)은 출발값이며 문서에 "차장님이 정한다"를 명시.
- **전달 세트**: `.gs` + 바뀐 문서 + (필요 시) `.pine` 을 SendUserFile. 드라이브 업로드는 "드라이브에도 올려줘" 라고 하실 때만.

## 5. 절차
1. GitHub `coin/` 최신 파일과 자가진단 「버전」 대조 → 다르면 먼저 정본 재전송.
2. 증상 → 「1.거래로그」 상태/오류 열에서 어느 문에서 막혔는지 특정(REJECT 사유 문구가 문 이름을 포함한다).
3. 코드 수정은 최소 범위 → 모의 실행기에 재현 검사 추가 → 전부 PASS → 고장 주입으로 검사가 실제로 잡는지 1회 확인.
4. 독립 감사(§7.1-2, 읽기 전용 서브에이전트) → HIGH 는 전부 반영.
5. 커밋·푸시 → SendUserFile → 전달 보고 4줄. 배운 것은 이 스킬 8번 칸과 기억 파일에 이중 저장.

## 6. 완료 조건
모의 실행기 PASS = 전체 건수(현재 89) / 자가진단 FAIL 0 / 「1.거래로그」에 ERROR 0·⚠ 0 인 DRY-RUN 기간(일수는 차장님이 정함) / 소액 1계약 LIVE 1회 OK + 앱에서 손절 확인 → 그 뒤에만 MAX_CONTRACTS 상향.

## 7. 실제 사례
- **v1 결함 발견(2026-09-05)**: 로그 시트 기록 0건 = v1 은 돌아간 적 없음. ccxt 오류표에서 `code:"0"+sCode:"36"` 거절 형식을 확인 → v1 은 이를 성공으로 기록했을 것. 모의 실행기 고장 주입으로 3건 FAIL 재현.
- **독립 감사 HIGH 4건(2026-09-05)**: 상한칸에 글자 입력 시 `sz > NaN` 이 false 라 통과 / 틀린 토큰이 LAST_LOG 에 잔존 / ctVal 조회 실패 시 BTC 값으로 ETH 환산 / 주문 후 조회 실패를 ERROR 로 뭉갬 → 전부 v2.1 에 반영. **자기검증 60/60 이었는데도 나왔다** — 감사는 생략하지 않는다.
- **차장님 정정(2026-09-05)**: "이더리움인데" → 기본 종목 ETH-USDT-SWAP. "수입이 작아" → 3.잔고추이 탭(전일 대비·누적). 수익 자체는 전략·수수료 문제라 코드가 못 키운다고 명시.
- **손절이 알럿에 실리는가**: 트레이딩뷰 자리표시자에 손절가는 없다 → Pine 안에서 JSON 조립(A 방식)이 표준. 브리지는 price 가 오면 손절 방향(롱 sl<price, 숏 sl>price)을 검사해 거꾸로면 거절.

## 8. 버전 이력
- v1 (2026-09-05): 신설. 브리지 v2.0→v2.3(60→89건 검사), Pine 원틀, 체크리스트, 설계 한 장, 독립 감사 반영, ETH 기본·잔고추이·손절 방향 검사.

## 9. 금지
- v1 코드(드라이브 원본)를 실전에 쓰거나 v2 에 다시 섞지 않는다.
- 주문 재시도 코드를 넣지 않는다(이중 주문). 청산 수량을 로컬 기록에서 읽지 않는다.
- 상한·수량·손절%·요율을 Claude 가 정하지 않는다. 기본값을 "권장값"이라 부르지 않는다.
- 문 9개 중 하나라도 빼는 수정은 C 등급 — 사전 확인 없이는 안 한다.
- "검증했다"는 모의 실행기를 실제로 돌리고 수치를 적은 뒤에만 쓴다. 딥코인 실서버로는 Claude 가 시험할 수 없다 — 그 사실을 숨기지 않는다.
- 이 스킬에 API 키·토큰·시트 편집 권한을 적지 않는다.

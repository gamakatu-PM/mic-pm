# 공통 기록 — OneDrive

Python 표준 라이브러리만 사용합니다. 별도 AI API·서버·유료 서비스는 호출하지 않습니다.

기본 폴더:
`OneDrive/26년도 현장/!!클로드가 저장하는 폴더/3_공통사용/인수인계함/GPT_공유기록`

실제 PC에서:
`python shared_memory.py install --seed-file INITIAL_HANDOFF.txt`

사용 중인 OneDrive가 하나일 때만 자동 선택합니다. 여러 계정이면 실제 경로를 확인해 `--root`로 지정합니다.
`install`은 위 경로의 업무 루트 AGENTS.md에 시작 시 기록을 읽는 지침을 추가합니다. 기존 내용은 유지하고 사본을 백업합니다.
사용자 지정 root가 기본 업무 경로와 다르면 AGENTS.md를 자동 수정하지 않습니다.

작업 전:
`python shared_memory.py read`

작업 중/종료:
`python shared_memory.py append --title "작업명" --body-file "기록.txt" --status-file "최신상태.txt"`

첫 2개 텍스트와 날짜별 작업일지는 읽기 쉬운 UTF-8 메모장 파일입니다.
원본 기록은 `_events/YYYY-MM-DD/고유파일.json`에 별개로 남겨 두 PC가 같은 로그를 덮는 위험을 줄입니다.
다른 PC로 전환하면 OneDrive 동기화 완료 후 `read`로 합쳐 읽습니다. 실시간 대화 공유나 네트워크 동기화를 직접 구현하는 도구는 아닙니다.
기록 내용 자체는 AI가 작성해야 합니다. 프로그램이 대화 원문을 자동 수집하거나 누락 없이 기록하는 것은 아닙니다.
클라우드에서 OneDrive가 연결되지 않았다면 이 도구도 OneDrive에 접근하지 못합니다.

비밀번호·키·회사 기록은 GitHub에 올리지 않습니다. 이 저장소에는 도구와 비공개 정보를 제외한 기술 시작 요약만 넣습니다.

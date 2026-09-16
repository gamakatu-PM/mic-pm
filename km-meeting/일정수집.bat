@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem ── 여기 두 줄만 프로님 컴퓨터에 맞게 ──
set "ROOT=%USERPROFILE%\OneDrive\26년도 현장\!!클로드가 저장하는 폴더\plaud\26년\1.현장"
set "OUT=%ROOT%\_보고"
rem OUT 을 구글 드라이브 데스크탑 폴더로 바꾸면 클로드가 아침 5시에 읽어 메일을 보냅니다.
rem 예) set "OUT=G:\내 드라이브\KM_블록작업\_보고"

python km_schedule_collect.py --root "%ROOT%" --out "%OUT%"
if errorlevel 1 (
  echo  실패했습니다. 위 메시지를 클로드에게 보여주세요.
  pause
)

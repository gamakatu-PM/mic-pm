@echo off
chcp 65001 >nul
cd /d "%~dp0"

if "%~1"=="" (
  echo.
  echo  [ 사용법 ]
  echo  회의록 .docx 파일을 이 배치파일 위로 끌어다 놓으세요.
  echo.
  pause
  exit /b
)

python km_docx_fix_v2_260916.py "%~1"
if errorlevel 1 (
  echo.
  echo  실패했습니다. 위 메시지를 클로드에게 보여주세요.
) else (
  echo.
  echo  끝났습니다. 같은 폴더에 _v2.docx 가 생겼습니다.
)
echo.
pause

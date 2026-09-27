@echo off
chcp 65001 > nul
title KM 현장비서 도구모음
cd /d "%~dp0"
where py > nul 2>&1
if %errorlevel%==0 (
  py -3 "%~dp0코드\km_tools\menu.py"
) else (
  python "%~dp0코드\km_tools\menu.py"
)
if errorlevel 1 (
  echo.
  echo [오류] 파이썬이 없거나 실행에 실패했습니다.
  echo 처음이시면 _처음_한번만_설치.bat 을 먼저 눌러주십시오.
  pause
)

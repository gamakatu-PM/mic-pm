@echo off
chcp 65001 >nul
title KM 산군 도구 설치
cd /d "%~dp0"
python "%~dp0설치.py" 2>nul
if errorlevel 9009 py "%~dp0설치.py"
if errorlevel 1 (
  echo.
  echo 파이썬을 못 찾았습니다. 시작.bat 이 되는 PC 라면 파이썬은 있습니다.
  echo 이 창을 캡처해서 클로드에게 보여 주십시오.
  pause
)

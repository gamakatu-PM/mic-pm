@echo off
chcp 65001 >nul
title KM 아침메일 - 자료 올리기
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [멈춤] python 을 못 찾았습니다. KM 도구와 같은 파이썬을 쓰십시오.
  pause & exit /b 1
)

python km_morning_push.py %*
echo.
echo 끝났습니다. 보내는 것은 구글이 매일 07:00 에 합니다.
pause

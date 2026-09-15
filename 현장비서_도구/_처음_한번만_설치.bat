@echo off
chcp 65001 > nul
title KM 현장비서 도구모음 - 처음 한 번만 설치
echo 필요한 부품을 받습니다. 인터넷이 연결되어 있어야 합니다.
echo.
where py > nul 2>&1
if %errorlevel%==0 (
  py -3 -m pip install --upgrade pip
  py -3 -m pip install openpyxl pillow
) else (
  python -m pip install --upgrade pip
  python -m pip install openpyxl pillow
)
echo.
echo 끝났습니다. 이제 도구모음.bat 을 누르시면 됩니다.
pause

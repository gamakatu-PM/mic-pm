@echo off
chcp 65001 > nul
title 처음 한 번만 설치
echo 필요한 부품을 받습니다. 인터넷이 연결되어 있어야 합니다.
echo.
setlocal
set "PYEXE=python"
where py > nul 2>&1
if %errorlevel%==0 set "PYEXE=py -3"
%PYEXE% -m pip install --upgrade pip
%PYEXE% -m pip install openpyxl pillow python-pptx
echo.
echo 끝났습니다. 이제 도구모음.bat 을 누르시면 됩니다.
pause

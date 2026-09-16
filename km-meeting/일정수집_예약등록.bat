@echo off
chcp 65001 >nul
cd /d "%~dp0"
schtasks /create /f /tn "KM 일정수집" /tr "\"%~dp0일정수집.bat\"" /sc daily /st 04:40
echo.
echo  매일 04:40 에 일정수집.bat 이 자동으로 돌도록 등록했습니다.
echo  지우려면:  schtasks /delete /tn "KM 일정수집" /f
echo.
pause

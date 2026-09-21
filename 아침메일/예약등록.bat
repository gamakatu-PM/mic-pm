@echo off
chcp 65001 >nul
title KM 아침메일 - 예약 등록 (한 번만 누르면 됩니다)
cd /d "%~dp0"

schtasks /create /tn "KM아침메일_올리기" /tr "\"%~dp0_조용히올리기.bat\"" /sc onlogon /rl highest /f
schtasks /create /tn "KM아침메일_올리기_반복" /tr "\"%~dp0_조용히올리기.bat\"" /sc hourly /mo 3 /f

echo.
echo 등록했습니다.
echo  - 로그인할 때 한 번
echo  - 그 뒤 3시간마다 한 번
echo PC 가 켜져 있을 때 자료가 구글로 올라가고, 메일은 구글이 매일 07:00 에 보냅니다.
echo 올린 기록은 _올린기록.txt 에 쌓입니다.
pause

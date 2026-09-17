@echo off
chcp 949 > nul
title KM 39 - Proposal PPT
cd /d "%~dp0\ÄÚµå\km_tools"
where py > /dev/null 2>&1
if %errorlevel%==0 (
  py -3 t39_deck.py
) else (
  python t39_deck.py
)
pause

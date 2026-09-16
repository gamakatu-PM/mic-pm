@echo off
chcp 949 > nul
title KM 26 - Proposal PPT
cd /d "%~dp0\ÄÚµå\km_tools"
where py > nul 2>&1
if %errorlevel%==0 (
  py -3 t26_deck.py
) else (
  python t26_deck.py
)
pause

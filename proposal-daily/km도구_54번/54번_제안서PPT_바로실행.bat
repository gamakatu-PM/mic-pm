@echo off
chcp 949 > nul
title KM 54 - Proposal PPT
cd /d "%~dp0\ÄÚµå\km_tools"
where py > /dev/null 2>&1
if %errorlevel%==0 (
  py -3 t54_deck.py
) else (
  python t54_deck.py
)
pause

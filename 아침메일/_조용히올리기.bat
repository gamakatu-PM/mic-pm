@echo off
chcp 65001 >nul
cd /d "%~dp0"
python km_morning_push.py >> _올린기록.txt 2>&1

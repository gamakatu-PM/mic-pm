@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "KM_PY=py -3"
%KM_PY% --version >nul 2>&1
if errorlevel 1 set "KM_PY=python"
%KM_PY% --version >nul 2>&1
if errorlevel 1 (
 echo Python 3가 필요합니다. 기존 현장도구에서 사용하던 Python을 확인해 주세요.
 pause
 exit /b 1
)
%KM_PY% -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
 echo 엑셀 읽기 부품을 설치합니다.
 %KM_PY% -m pip install "openpyxl>=3.1.5,<3.2"
 if errorlevel 1 (
  pause
  exit /b 1
 )
)
echo 사용할 업무일지 엑셀을 선택해 주세요.
echo 선택한 파일은 수정 시 자동 백업 후 저장됩니다.
%KM_PY% "%~dp0server.py" --choose
if errorlevel 1 pause

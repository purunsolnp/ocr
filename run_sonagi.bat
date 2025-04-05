@echo off
chcp 65001 > nul
echo ===== 소나기OCR 실행 준비 중 =====
setlocal EnableDelayedExpansion

:: 현재 디렉토리 설정
cd /d %~dp0

:: Python 설치 확인
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [오류] Python이 설치되어 있지 않거나 경로에 추가되지 않았습니다.
    echo Python을 설치한 후 다시 시도하세요 (https://www.python.org/downloads/)
    echo Python 설치 시 "Add Python to PATH" 옵션을 반드시 체크하세요.
    pause
    exit /b 1
)

:: 필요한 패키지 설치
echo 필요한 패키지 설치 중...
pip install -r requirements.txt >nul 2>&1

:: 프로그램 실행
echo 소나기OCR을 시작합니다...
python main.py

:: 오류 발생 시
if %ERRORLEVEL% NEQ 0 (
    echo 프로그램 실행 중 오류가 발생했습니다.
    echo 로그를 확인하거나 Python이 정상적으로 설치되었는지 확인하세요.
    pause
) else (
    echo 프로그램이 정상적으로 시작되었습니다.
)
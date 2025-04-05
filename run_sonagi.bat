@echo off
echo ===== 소나기OCR 실행 준비 중 =====
setlocal EnableDelayedExpansion

:: 현재 디렉토리 설정
cd /d %~dp0

:: 필요한 패키지 설치
echo 필요한 패키지 설치 중...
pip install -r requirements.txt >nul 2>&1

:: 프로그램 실행
echo 소나기OCR을 시작합니다...

:: 직접 Python으로 실행 (start 명령 대신)
python main.py

:: 오류 발생 시
if %ERRORLEVEL% NEQ 0 (
    echo 프로그램 실행 중 오류가 발생했습니다.
    echo 로그를 확인하거나 Python이 정상적으로 설치되었는지 확인하세요.
    pause
) else (
    echo 프로그램이 정상적으로 시작되었습니다.
)
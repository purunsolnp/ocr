@echo off
echo ===== 소나기OCR 직접 실행 중 =====

:: 현재 디렉토리 설정
cd /d %~dp0

:: 프로그램 실행
python main.py

:: 오류 발생 시
if %ERRORLEVEL% NEQ 0 (
    echo 프로그램 실행 중 오류가 발생했습니다.
    pause
)
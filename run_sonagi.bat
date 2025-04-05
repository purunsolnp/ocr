@echo off
echo ===== 소나기OCR 실행 준비 중 =====
setlocal

:: 현재 디렉토리 설정
cd /d %~dp0

:: 필요한 패키지 설치
echo 필요한 패키지 설치 중...
pip install -r requirements.txt

:: 프로그램 실행
echo 소나기OCR을 시작합니다...
start pythonw main.py

echo 프로그램이 백그라운드에서 실행됩니다.
echo 번역 화면이 나타나지 않으면 작업 표시줄을 확인하세요.
timeout /t 3
exit
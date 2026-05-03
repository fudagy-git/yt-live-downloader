@echo off
chcp 65001 > nul
title YTLiveDownloader - Windows EXE 자동 빌드
color 0A

echo.
echo ============================================================
echo   YouTube Live From-Start Downloader
echo   Windows EXE 자동 빌드 스크립트 v1.0
echo ============================================================
echo.

REM ── Python 확인 ──────────────────────────────────────────────
echo [1/5] Python 확인 중...
python --version > nul 2>&1
if errorlevel 1 (
    echo.
    echo  [오류] Python 이 설치되어 있지 않습니다!
    echo.
    echo  아래 주소에서 Python 3.10 이상을 설치하세요:
    echo  https://www.python.org/downloads/
    echo.
    echo  ※ 설치 시 반드시 "Add Python to PATH" 체크!
    echo.
    pause
    exit /b 1
)
echo  [OK] Python 발견:
python --version
echo.

REM ── pip 업그레이드 ────────────────────────────────────────────
echo [2/5] pip 업그레이드 중...
python -m pip install --upgrade pip --quiet --no-warn-script-location
echo  [OK] pip 최신 버전
echo.

REM ── yt-dlp 설치 ──────────────────────────────────────────────
echo [3/5] yt-dlp 설치 / 업데이트 중...
python -m pip install --upgrade yt-dlp --quiet --no-warn-script-location
if errorlevel 1 (
    echo  [오류] yt-dlp 설치 실패
    pause
    exit /b 1
)
echo  [OK] yt-dlp 설치 완료
echo.

REM ── PyInstaller 설치 ─────────────────────────────────────────
echo [4/5] PyInstaller 설치 / 업데이트 중...
python -m pip install --upgrade pyinstaller --quiet --no-warn-script-location
if errorlevel 1 (
    echo  [오류] PyInstaller 설치 실패
    pause
    exit /b 1
)
echo  [OK] PyInstaller 설치 완료
echo.

REM ── EXE 빌드 ─────────────────────────────────────────────────
echo [5/5] EXE 빌드 중... (1~3분 소요, 잠시 기다려 주세요)
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "YTLiveDownloader" ^
    --hidden-import yt_dlp ^
    --hidden-import yt_dlp.utils ^
    --hidden-import yt_dlp.extractor ^
    --collect-all yt_dlp ^
    --clean ^
    --noconfirm ^
    yt_live_downloader.py

if errorlevel 1 (
    echo.
    echo  [오류] 빌드 중 오류가 발생했습니다.
    echo  build 폴더 안의 warn-YTLiveDownloader.txt 를 확인하세요.
    echo.
    pause
    exit /b 1
)

REM ── 빌드 성공 ─────────────────────────────────────────────────
echo.
echo ============================================================
echo.
echo   빌드 성공!
echo.
echo   실행 파일 위치: dist\YTLiveDownloader.exe
echo.
echo ============================================================
echo.

REM 폴더 자동 열기
if exist "dist\YTLiveDownloader.exe" (
    echo  dist 폴더를 여는 중...
    explorer dist
)

pause

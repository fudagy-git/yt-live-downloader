#!/bin/bash
# YouTube Live From-Start Downloader - macOS .app 자동 빌드 스크립트 v1.0

set -e

echo ""
echo "============================================================"
echo "  YouTube Live From-Start Downloader"
echo "  macOS APP 자동 빌드 스크립트 v1.0"
echo "============================================================"
echo ""

# ── Python 확인 ─────────────────────────────────────────────────
echo "[1/5] Python 확인 중..."
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "  [오류] python3 가 설치되어 있지 않습니다!"
    echo ""
    echo "  아래 방법 중 하나로 설치하세요:"
    echo "  1) https://www.python.org/downloads/macos/"
    echo "  2) brew install python3  (Homebrew 설치 후)"
    echo ""
    exit 1
fi
echo "  [OK] $(python3 --version)"
echo ""

# ── pip 업그레이드 ───────────────────────────────────────────────
echo "[2/5] pip 업그레이드 중..."
python3 -m pip install --upgrade pip --quiet 2>/dev/null || true
echo "  [OK] pip 최신 버전"
echo ""

# ── yt-dlp 설치 ─────────────────────────────────────────────────
echo "[3/5] yt-dlp 설치 / 업데이트 중..."
python3 -m pip install --upgrade yt-dlp --quiet
echo "  [OK] yt-dlp 설치 완료"
echo ""

# ── PyInstaller 설치 ────────────────────────────────────────────
echo "[4/5] PyInstaller 설치 / 업데이트 중..."
python3 -m pip install --upgrade pyinstaller --quiet
echo "  [OK] PyInstaller 설치 완료"
echo ""

# ── APP 빌드 ────────────────────────────────────────────────────
echo "[5/5] APP 빌드 중... (1~3분 소요, 잠시 기다려 주세요)"
echo ""

pyinstaller \
    --onefile \
    --windowed \
    --name "YTLiveDownloader" \
    --hidden-import yt_dlp \
    --hidden-import yt_dlp.utils \
    --hidden-import yt_dlp.extractor \
    --collect-all yt_dlp \
    --clean \
    --noconfirm \
    yt_live_downloader.py

# ── 빌드 후 처리 ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo ""
echo "  빌드 성공!"
echo ""
echo "  실행 파일 위치: dist/YTLiveDownloader"
echo ""
echo "============================================================"
echo ""

# 실행 권한 부여
chmod +x dist/YTLiveDownloader 2>/dev/null || true

# macOS Gatekeeper 우회 (quarantine 속성 제거)
xattr -cr dist/YTLiveDownloader 2>/dev/null || true

echo "  ※ '확인되지 않은 개발자' 경고가 나오면:"
echo "     Finder에서 앱 우클릭 → '열기' → '열기' 클릭"
echo "  또는:"
echo "     xattr -cr dist/YTLiveDownloader 명령 실행 후 재시도"
echo ""

# dist 폴더 Finder에서 열기
open dist/ 2>/dev/null || true

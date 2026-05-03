============================================
 YouTube Live From-Start Downloader
 macOS 배포 패키지
============================================

【사용 방법 A - .app 번들 빌드 (권장)】
1. Terminal 열기 (Launchpad → 기타 → 터미널)

2. 이 폴더로 이동:
   cd ~/Downloads/YTLiveDownloader_macOS

3. 빌드 스크립트 실행:
   bash build.sh

4. 완료 후 dist/YTLiveDownloader 실행


【사용 방법 B - Python으로 직접 실행 (빌드 없이)】
1. Terminal에서:
   pip3 install yt-dlp
   python3 yt_live_downloader.py


【처음 실행 시 Gatekeeper 경고 우회】
macOS Ventura 이상에서 "개발자를 확인할 수 없음" 경고 시:

방법 1 (권장):
  - Finder에서 앱 우클릭 → "열기" → "열기" 클릭

방법 2:
  - 시스템 설정 → 개인 정보 보호 및 보안
  → "확인 없이 열기" 버튼 클릭

방법 3 (Terminal):
  xattr -cr ~/Downloads/YTLiveDownloader_macOS/dist/YTLiveDownloader


【앱 기능】
- YouTube 라이브 방송을 처음부터 다운로드
- ffmpeg 자동 다운로드 (첫 실행 시 ~50MB)
- 화질 선택: best / 1080p / 720p / 480p / audio only
- 다운로드 중단 기능
- yt-dlp 업데이트 버튼
- 설정 자동 저장 (~/.yt_live_downloader/settings.json)


【파일 구성】
- yt_live_downloader.py : 메인 소스 파일
- build.sh              : .app 자동 빌드 스크립트
- README.txt            : 이 파일


【요구사항】
- macOS 10.15 (Catalina) 이상
- Python 3.10 이상 (빌드 시 필요)
  설치: https://www.python.org/downloads/macos/
  또는: brew install python3


============================================

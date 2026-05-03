============================================
 YouTube Live From-Start Downloader
 Windows 배포 패키지
============================================

【사용 방법 - EXE 직접 빌드】
1. Python 3.10 이상 설치 (https://www.python.org/downloads/)
   ※ 설치 시 "Add Python to PATH" 반드시 체크!

2. build.bat 파일을 더블클릭

3. 빌드 완료 후 dist\YTLiveDownloader.exe 실행


【사용 방법 - Python으로 직접 실행 (빌드 없이)】
1. Python 3.10 이상 설치

2. 명령 프롬프트(cmd) 열기

3. 아래 명령어 실행:
   pip install yt-dlp
   python yt_live_downloader.py


【앱 기능】
- YouTube 라이브 방송을 처음부터 다운로드
- ffmpeg 자동 다운로드 (첫 실행 시)
- 화질 선택: best / 1080p / 720p / 480p / audio only
- 다운로드 중단 기능
- yt-dlp 업데이트 버튼 (YouTube 정책 변경 시 유용)
- 설정 자동 저장 (~/.yt_live_downloader/settings.json)


【파일 구성】
- yt_live_downloader.py : 메인 소스 파일
- build.bat             : EXE 자동 빌드 스크립트
- README.txt            : 이 파일


【주의사항】
- ffmpeg는 첫 실행 시 자동 다운로드됩니다 (약 50~100MB)
- ffmpeg 없이도 오디오만 있는 스트림은 다운로드 가능
- yt-dlp는 YouTube 변경에 따라 자주 업데이트가 필요할 수 있습니다
- 저작권이 있는 콘텐츠의 무단 다운로드는 법적 문제가 될 수 있습니다


============================================

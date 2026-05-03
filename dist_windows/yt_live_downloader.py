"""
YouTube Live From-Start Downloader
단일 파일 GUI 앱 (Windows / macOS / Linux)
- 첫 실행 시 yt-dlp 자동 설치
- ffmpeg 자동 감지 및 다운로드 (Windows/macOS)
"""
import os
import sys
import subprocess
import shutil
import threading
import queue
import json
import platform
import zipfile
import tarfile
import urllib.request
import ssl
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 0. 부트스트랩: 의존성 자동 설치
# ──────────────────────────────────────────────────────────────

APP_DIR = Path.home() / ".yt_live_downloader"
APP_DIR.mkdir(exist_ok=True)
BIN_DIR = APP_DIR / "bin"
BIN_DIR.mkdir(exist_ok=True)


def _log_boot(msg):
    print(f"[bootstrap] {msg}", flush=True)


def ensure_pip_package(pkg_name, import_name=None):
    """pip 패키지가 없으면 설치"""
    import_name = import_name or pkg_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        pass

    _log_boot(f"{pkg_name} 설치 중...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", pkg_name],
            stdout=subprocess.DEVNULL,
        )
        __import__(import_name)
        _log_boot(f"{pkg_name} 설치 완료")
        return True
    except Exception as e:
        _log_boot(f"{pkg_name} 설치 실패: {e}")
        return False


def find_ffmpeg():
    """시스템 PATH 또는 앱 bin 폴더에서 ffmpeg 찾기"""
    # 1) 앱 전용 bin 폴더
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    local = BIN_DIR / exe
    if local.exists():
        return str(local)
    # 2) 시스템 PATH
    found = shutil.which("ffmpeg")
    if found:
        return found
    # 3) PyInstaller 번들
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / exe
        if bundled.exists():
            return str(bundled)
    return None


def download_ffmpeg(progress_cb=None):
    """ffmpeg를 BIN_DIR에 다운로드 (Windows/macOS)"""
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        url = "https://github.com/GyanD/codexffmpeg/releases/latest/download/ffmpeg-release-essentials.zip"
        archive_name = "ffmpeg.zip"
    elif system == "Darwin":
        # evermeet.cx는 항상 최신 macOS용 ffmpeg 정적 바이너리 제공
        url = "https://evermeet.cx/ffmpeg/getrelease/zip"
        archive_name = "ffmpeg.zip"
    else:
        raise RuntimeError("Linux는 패키지 매니저로 ffmpeg를 설치하세요 (apt/dnf/pacman 등).")

    archive_path = APP_DIR / archive_name
    _log_boot(f"ffmpeg 다운로드: {url}")

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(archive_path, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb and total:
                    progress_cb(downloaded, total)

    _log_boot("압축 해제 중...")
    extract_dir = APP_DIR / "ffmpeg_extract"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()

    if archive_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as z:
            z.extractall(extract_dir)
    else:
        with tarfile.open(archive_path) as t:
            t.extractall(extract_dir)

    # ffmpeg 실행 파일 찾아서 BIN_DIR로 이동
    target_name = "ffmpeg.exe" if system == "Windows" else "ffmpeg"
    found_path = None
    for root, _dirs, files in os.walk(extract_dir):
        for fn in files:
            if fn == target_name:
                found_path = Path(root) / fn
                break
        if found_path:
            break

    if not found_path:
        raise RuntimeError("압축 안에서 ffmpeg를 찾을 수 없습니다.")

    final_path = BIN_DIR / target_name
    shutil.copy2(found_path, final_path)
    if system != "Windows":
        os.chmod(final_path, 0o755)

    # 정리
    archive_path.unlink(missing_ok=True)
    shutil.rmtree(extract_dir, ignore_errors=True)

    _log_boot(f"ffmpeg 설치 완료: {final_path}")
    return str(final_path)


def bootstrap_dependencies():
    """앱 시작 전에 호출 - GUI 없이 콘솔 모드로 의존성 확인"""
    # PyInstaller 번들에서는 pip install 불가 → 스킵
    if getattr(sys, "frozen", False):
        return

    # pip 자체가 없는 경우(드물지만) ensurepip 사용
    try:
        import pip  # noqa: F401
    except ImportError:
        try:
            import ensurepip
            ensurepip.bootstrap()
        except Exception:
            pass

    # yt-dlp
    if not ensure_pip_package("yt-dlp", "yt_dlp"):
        print("yt-dlp 설치에 실패했습니다. 수동으로 'pip install yt-dlp' 실행하세요.")
        sys.exit(1)


bootstrap_dependencies()

# 이 시점에서 yt_dlp 사용 가능
import yt_dlp  # noqa: E402

import tkinter as tk  # noqa: E402
from tkinter import ttk, filedialog, messagebox, scrolledtext  # noqa: E402


# ──────────────────────────────────────────────────────────────
# 1. 다운로드 작업
# ──────────────────────────────────────────────────────────────

APP_TITLE = "YouTube Live From-Start Downloader"
DEFAULT_DIR = str(Path.home() / "Downloads" / "YTLive")


class DownloadJob:
    def __init__(self, url, outdir, log_queue, fmt="bv*+ba/b", ffmpeg_path=None):
        self.url = url
        self.outdir = outdir
        self.log_queue = log_queue
        self.fmt = fmt
        self.ffmpeg_path = ffmpeg_path
        self.status = "queued"
        self.thread = None
        self.cancel_flag = threading.Event()

    def _hook(self, d):
        if self.cancel_flag.is_set():
            raise yt_dlp.utils.DownloadError("사용자가 중단함")
        status = d.get("status")
        if status == "downloading":
            pct = d.get("_percent_str", "").strip()
            speed = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            frag = ""
            if d.get("fragment_index") and d.get("fragment_count"):
                frag = f" frag {d['fragment_index']}/{d['fragment_count']}"
            elif d.get("fragment_index"):
                frag = f" frag {d['fragment_index']}"
            self.log_queue.put(("progress", f"{pct} | {speed} | ETA {eta}{frag}"))
        elif status == "finished":
            self.log_queue.put(("log", f"✓ 세그먼트 완료: {d.get('filename')}"))

    def run(self):
        os.makedirs(self.outdir, exist_ok=True)
        outtmpl = os.path.join(self.outdir, "%(title)s_%(id)s.%(ext)s")

        ydl_opts = {
            "live_from_start": True,
            "wait_for_video": (1, 60),
            "format": self.fmt,
            "merge_output_format": "mp4",
            "concurrent_fragment_downloads": 8,
            "retries": 30,
            "fragment_retries": 30,
            "outtmpl": outtmpl,
            "progress_hooks": [self._hook],
            "noprogress": True,
            "quiet": True,
            "no_warnings": False,
        }
        if self.ffmpeg_path:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_path

        self.status = "running"
        self.log_queue.put(("log", f"▶ 시작: {self.url}"))
        self.log_queue.put(("log", f"  저장: {self.outdir}"))
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.status = "done"
            self.log_queue.put(("log", "✅ 완료"))
        except yt_dlp.utils.DownloadError as e:
            self.status = "error"
            self.log_queue.put(("log", f"❌ 오류: {e}"))
        except Exception as e:
            self.status = "error"
            self.log_queue.put(("log", f"❌ 예외: {e}"))
        finally:
            self.log_queue.put(("done", self.status))

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def cancel(self):
        self.cancel_flag.set()


# ──────────────────────────────────────────────────────────────
# 2. GUI
# ──────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("740x560")
        self.minsize(620, 480)

        self.log_queue = queue.Queue()
        self.current_job = None
        self.ffmpeg_path = find_ffmpeg()

        self._build_ui()
        self._load_settings()
        self.after(150, self._poll_queue)
        self.after(300, self._check_ffmpeg)

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # ffmpeg 상태 표시
        self.ffmpeg_status = tk.StringVar()
        self.ffmpeg_label = ttk.Label(self, textvariable=self.ffmpeg_status)
        self.ffmpeg_label.pack(anchor="w", padx=10, pady=(8, 0))

        # URL
        frm_url = ttk.Frame(self)
        frm_url.pack(fill="x", **pad)
        ttk.Label(frm_url, text="YouTube Live URL:").pack(anchor="w")
        self.url_var = tk.StringVar()
        ttk.Entry(frm_url, textvariable=self.url_var).pack(fill="x")

        # 저장 경로
        frm_dir = ttk.Frame(self)
        frm_dir.pack(fill="x", **pad)
        ttk.Label(frm_dir, text="저장 폴더:").pack(anchor="w")
        row = ttk.Frame(frm_dir)
        row.pack(fill="x")
        self.dir_var = tk.StringVar(value=DEFAULT_DIR)
        ttk.Entry(row, textvariable=self.dir_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="찾아보기", command=self._choose_dir).pack(side="left", padx=(6, 0))

        # 화질
        frm_fmt = ttk.Frame(self)
        frm_fmt.pack(fill="x", **pad)
        ttk.Label(frm_fmt, text="화질:").pack(side="left")
        self.fmt_var = tk.StringVar(value="best")
        ttk.Combobox(
            frm_fmt,
            textvariable=self.fmt_var,
            values=["best", "1080p", "720p", "480p", "audio only"],
            state="readonly",
            width=14,
        ).pack(side="left", padx=6)

        # 버튼
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", **pad)
        self.start_btn = ttk.Button(frm_btn, text="▶ 처음부터 다운로드", command=self._start)
        self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(frm_btn, text="■ 중단", command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        ttk.Button(frm_btn, text="폴더 열기", command=self._open_dir).pack(side="left")
        ttk.Button(frm_btn, text="yt-dlp 업데이트", command=self._update_ytdlp).pack(side="right")

        # 진행상황
        self.progress_var = tk.StringVar(value="대기 중")
        ttk.Label(self, textvariable=self.progress_var, foreground="#0a7").pack(anchor="w", padx=10)

        # 로그
        ttk.Label(self, text="로그:").pack(anchor="w", padx=10, pady=(8, 0))
        self.log_box = scrolledtext.ScrolledText(self, height=15, font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_box.configure(state="disabled")

    # ── ffmpeg 체크 / 자동 설치 ──
    def _check_ffmpeg(self):
        self.ffmpeg_path = find_ffmpeg()
        if self.ffmpeg_path:
            self.ffmpeg_status.set(f"✓ ffmpeg: {self.ffmpeg_path}")
            self.ffmpeg_label.configure(foreground="#0a7")
        else:
            self.ffmpeg_status.set("⚠ ffmpeg 없음 - 영상/오디오 머지 불가")
            self.ffmpeg_label.configure(foreground="#c60")
            if platform.system() in ("Windows", "Darwin"):
                if messagebox.askyesno(
                    APP_TITLE,
                    "ffmpeg가 설치되어 있지 않습니다.\n"
                    "지금 자동으로 다운로드하시겠습니까? (약 50~100MB)",
                ):
                    self._install_ffmpeg_async()
            else:
                messagebox.showwarning(
                    APP_TITLE,
                    "Linux는 패키지 매니저로 ffmpeg를 설치하세요.\n예: sudo apt install ffmpeg",
                )

    def _install_ffmpeg_async(self):
        self._append_log("ffmpeg 다운로드 시작...")
        self.progress_var.set("ffmpeg 다운로드 중...")

        def worker():
            try:
                def cb(done, total):
                    pct = done * 100 / total
                    self.log_queue.put(("progress", f"ffmpeg 다운로드 {pct:.1f}%"))
                path = download_ffmpeg(progress_cb=cb)
                self.log_queue.put(("log", f"✅ ffmpeg 설치 완료: {path}"))
                self.log_queue.put(("ffmpeg_done", path))
            except Exception as e:
                self.log_queue.put(("log", f"❌ ffmpeg 다운로드 실패: {e}"))
                self.log_queue.put(("ffmpeg_done", None))

        threading.Thread(target=worker, daemon=True).start()

    # ── yt-dlp 업데이트 ──
    def _update_ytdlp(self):
        def worker():
            self.log_queue.put(("log", "yt-dlp 업데이트 중..."))
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                    stdout=subprocess.DEVNULL,
                )
                self.log_queue.put(("log", "✅ yt-dlp 업데이트 완료 (앱 재시작 권장)"))
            except Exception as e:
                self.log_queue.put(("log", f"❌ 업데이트 실패: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    # ── UI 동작 ──
    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def _open_dir(self):
        path = self.dir_var.get()
        os.makedirs(path, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _format_string(self):
        m = {
            "best": "bv*+ba/b",
            "1080p": "bv*[height<=1080]+ba/b[height<=1080]",
            "720p": "bv*[height<=720]+ba/b[height<=720]",
            "480p": "bv*[height<=480]+ba/b[height<=480]",
            "audio only": "ba/b",
        }
        return m.get(self.fmt_var.get(), "bv*+ba/b")

    def _start(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(APP_TITLE, "URL을 입력하세요.")
            return
        if self.current_job and self.current_job.status == "running":
            messagebox.showinfo(APP_TITLE, "이미 다운로드 중입니다.")
            return
        if not self.ffmpeg_path:
            if not messagebox.askyesno(
                APP_TITLE,
                "ffmpeg가 없어서 영상/오디오 머지가 안 됩니다.\n그래도 계속하시겠습니까?",
            ):
                return

        self._save_settings()
        self._append_log(f"\n{'=' * 60}")
        self.current_job = DownloadJob(
            url=url,
            outdir=self.dir_var.get(),
            log_queue=self.log_queue,
            fmt=self._format_string(),
            ffmpeg_path=self.ffmpeg_path,
        )
        self.current_job.start()
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress_var.set("시작 중...")

    def _cancel(self):
        if self.current_job:
            self.current_job.cancel()
            self._append_log("⏹ 중단 요청...")

    def _append_log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _poll_queue(self):
        try:
            while True:
                kind, msg = self.log_queue.get_nowait()
                if kind == "log":
                    self._append_log(msg)
                elif kind == "progress":
                    self.progress_var.set(msg)
                elif kind == "done":
                    self.progress_var.set(f"상태: {msg}")
                    self.start_btn.config(state="normal")
                    self.cancel_btn.config(state="disabled")
                elif kind == "ffmpeg_done":
                    if msg:
                        self.ffmpeg_path = msg
                        self.ffmpeg_status.set(f"✓ ffmpeg: {msg}")
                        self.ffmpeg_label.configure(foreground="#0a7")
                    self.progress_var.set("대기 중")
        except queue.Empty:
            pass
        self.after(200, self._poll_queue)

    # ── 설정 ──
    def _settings_path(self):
        return APP_DIR / "settings.json"

    def _save_settings(self):
        try:
            self._settings_path().write_text(
                json.dumps({"dir": self.dir_var.get(), "fmt": self.fmt_var.get()}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_settings(self):
        try:
            data = json.loads(self._settings_path().read_text(encoding="utf-8"))
            if data.get("dir"):
                self.dir_var.set(data["dir"])
            if data.get("fmt"):
                self.fmt_var.set(data["fmt"])
        except Exception:
            pass


if __name__ == "__main__":
    App().mainloop()

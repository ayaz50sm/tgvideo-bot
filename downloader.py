import os
import re
import json
import asyncio
import urllib.parse
import urllib.request
import subprocess
from pathlib import Path

URL_RE = re.compile(r"https?://\S+")

COOKIE_MAP = {
    "udemy.com": "udemy.txt",
    "teachable.com": "teachable.txt",
    "thinkific.com": "thinkific.txt",
}

def extract_url(text: str) -> str | None:
    if not text:
        return None
    m = URL_RE.search(text.strip())
    return m.group(0) if m else None

def get_domain(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()

def choose_cookie_file(url: str, cookie_dir: str, default_cookie_file: str | None = None) -> str | None:
    domain = get_domain(url)
    for key, fname in COOKIE_MAP.items():
        if key in domain:
            path = os.path.join(cookie_dir, fname)
            if os.path.exists(path):
                return path
    if default_cookie_file and os.path.exists(default_cookie_file):
        return default_cookie_file
    return None

async def run_cmd(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "Process timeout"
    return proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")

def format_duration(seconds) -> str:
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"

async def get_info(url: str, cookie_file: str | None = None, timeout: int = 180) -> dict:
    cmd = ["yt-dlp", "-J", "--no-playlist", url]
    if cookie_file and os.path.exists(cookie_file):
        cmd[1:1] = ["--cookies", cookie_file]

    code, out, err = await run_cmd(cmd, timeout=timeout)
    if code != 0:
        raise RuntimeError(err.strip() or "Failed to fetch info")
    return json.loads(out)

def find_latest_video(download_dir: str) -> str:
    exts = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
    files = sorted(Path(download_dir).glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        if f.is_file() and f.suffix.lower() in exts:
            return str(f)
    raise RuntimeError("No downloaded video file found")

def is_playable_mp4(file_path: str) -> bool:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            capture_output=True, text=True
        )
        vcodec = result.stdout.strip().lower()
        return vcodec in {"h264", "avc1"}
    except Exception:
        return False

def make_telegram_friendly(file_path: str) -> str:
    root, ext = os.path.splitext(file_path)
    out = root + ".telegram.mp4"

    if file_path.lower().endswith(".mp4") and is_playable_mp4(file_path):
        return file_path

    cmd = [
        "ffmpeg", "-y", "-i", file_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        out
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out

async def download_video(url: str, download_dir: str, cookie_file: str | None = None, timeout: int = 300) -> str:
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    outtmpl = os.path.join(download_dir, "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--restrict-filenames",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "--newline",
        "-o", outtmpl,
        url
    ]

    if cookie_file and os.path.exists(cookie_file):
        cmd[1:1] = ["--cookies", cookie_file]

    code, out, err = await run_cmd(cmd, timeout=timeout)
    if code != 0:
        raise RuntimeError(err.strip() or "Download failed")

    file_path = find_latest_video(download_dir)
    return make_telegram_friendly(file_path)

def download_thumbnail(thumbnail_url: str | None, download_dir: str) -> str | None:
    if not thumbnail_url:
        return None
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    thumb_path = os.path.join(download_dir, "thumb.jpg")
    try:
        urllib.request.urlretrieve(thumbnail_url, thumb_path)
        return thumb_path
    except Exception:
        return None

def build_caption(info: dict) -> str:
    title = info.get("title") or "Untitled"
    duration_text = format_duration(info.get("duration"))
    return (
        f"🎬 {title}\n"
        f"⏱ Duration: {duration_text}\n"
        f"✍️ Author: @nothing404error"
    )

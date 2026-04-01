import os
import re
import json
import asyncio
import urllib.parse
import urllib.request
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

async def run_cmd(cmd: list[str], timeout: int = 180) -> tuple[int, str, str]:
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

async def download_video(url: str, download_dir: str, cookie_file: str | None = None, timeout: int = 180) -> str:
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    outtmpl = os.path.join(download_dir, "%(title).150s [%(id)s].%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", outtmpl,
        url
    ]

    if cookie_file and os.path.exists(cookie_file):
        cmd[1:1] = ["--cookies", cookie_file]

    code, out, err = await run_cmd(cmd, timeout=timeout)
    if code != 0:
        raise RuntimeError(err.strip() or "Download failed")

    files = sorted(Path(download_dir).glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    video_files = [f for f in files if f.is_file()]
    if not video_files:
        raise RuntimeError("No downloaded file found")
    return str(video_files[0])

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
    uploader = info.get("uploader") or "Unknown"
    extractor = info.get("extractor_key") or info.get("extractor") or "Unknown"
    duration_text = format_duration(info.get("duration"))

    return (
        f"🎬 {title}\n"
        f"⏱ Duration: {duration_text}\n"
        f"📺 Source: {extractor}\n"
        f"👤 Uploader: {uploader}"
    )

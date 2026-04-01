import os
import re
import json
import asyncio
from pathlib import Path

URL_RE = re.compile(r"https?://\S+")

def extract_url(text: str) -> str | None:
    if not text:
        return None
    m = URL_RE.search(text.strip())
    return m.group(0) if m else None

async def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    return proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")

async def get_info(url: str, cookie_file: str | None = None) -> dict:
    cmd = ["yt-dlp", "-J", "--no-playlist", url]
    if cookie_file and os.path.exists(cookie_file):
        cmd[1:1] = ["--cookies", cookie_file]

    code, out, err = await run_cmd(cmd)
    if code != 0:
        raise RuntimeError(err.strip() or "Failed to fetch info")
    return json.loads(out)

async def download_video(url: str, download_dir: str, cookie_file: str | None = None) -> str:
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

    code, out, err = await run_cmd(cmd)
    if code != 0:
        raise RuntimeError(err.strip() or "Download failed")

    files = sorted(Path(download_dir).glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise RuntimeError("No downloaded file found")
    return str(files[0])

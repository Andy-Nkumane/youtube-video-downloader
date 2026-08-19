import os
import re
import subprocess
import sys
import threading
import uuid
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, render_template, request, send_file


BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIRS = {
    "video": BASE_DIR / "video-downloads",
    "audio": BASE_DIR / "audio-downloads",
}
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

app = Flask(__name__)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


def valid_youtube_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and parsed.hostname in YOUTUBE_HOSTS


def public_job(job: dict) -> dict:
    return {
        "id": job["id"],
        "status": job["status"],
        "media_type": job["media_type"],
        "message": job["message"],
        "progress": job["progress"],
        "files": job["files"],
        "logs": list(job["logs"])[-20:],
    }


def run_download(job_id: str, url: str, media_type: str) -> None:
    output_directory = DOWNLOAD_DIRS[media_type]
    output_directory.mkdir(parents=True, exist_ok=True)
    before = {path.resolve() for path in output_directory.rglob("*") if path.is_file()}
    command = [
        sys.executable,
        "-u",
        str(BASE_DIR / "youtube_video_downloader.py"),
        url,
        media_type,
        "--output",
        str(BASE_DIR),
    ]

    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["message"] = "Connecting to YouTube..."

    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creation_flags,
    )

    assert process.stdout is not None
    for raw_line in iter(process.stdout.readline, ""):
        for part in raw_line.replace("\r", "\n").splitlines():
            line = ANSI_ESCAPE.sub("", part).strip()
            if not line:
                continue
            progress_match = re.search(r"(?:Progress:|\[download\])\s+(\d+(?:\.\d+)?)%", line)
            size_match = re.search(
                r"\[download\]\s+(\d+(?:\.\d+)?)% of\s+~?\s*(\d+(?:\.\d+)?)([KMG]iB)"
                r"(?: at\s+(\S+\s*[KMG]iB/s))?(?: ETA\s+([0-9:]+))?$",
                line,
            )
            display_message = line
            if size_match:
                percent, total, unit, speed, eta = size_match.groups()
                downloaded = float(total) * float(percent) / 100
                display_message = f"{downloaded:.2f} {unit} of {total} {unit}"
                if speed:
                    display_message += f" at {speed.strip()}"
                if eta:
                    display_message += f" · ETA {eta}"
            with jobs_lock:
                job = jobs[job_id]
                job["logs"].append(line)
                job["message"] = display_message
                if progress_match:
                    job["progress"] = float(progress_match.group(1))

    return_code = process.wait()
    after = {path.resolve() for path in output_directory.rglob("*") if path.is_file()}
    created = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
    completed_files = [path for path in created if path.suffix.lower() in {".mp4", ".mp3", ".m4a"}]

    with jobs_lock:
        job = jobs[job_id]
        failed_in_log = any("Failed downloading" in line for line in job["logs"])
        if return_code == 0 and not failed_in_log:
            job["status"] = "complete"
            job["progress"] = 100
            job["message"] = "Download complete"
            job["files"] = [str(path.relative_to(BASE_DIR)).replace("\\", "/") for path in completed_files]
        else:
            job["status"] = "failed"
            job["message"] = job["logs"][-1] if job["logs"] else "Download failed"


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/downloads")
def start_download():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    media_type = str(data.get("media_type", "video")).lower()
    if not valid_youtube_url(url):
        return jsonify(error="Enter a valid YouTube URL."), 400
    if media_type not in DOWNLOAD_DIRS:
        return jsonify(error="Media type must be video or audio."), 400

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "media_type": media_type,
            "message": "Queued",
            "progress": 0,
            "files": [],
            "logs": deque(maxlen=100),
        }
    threading.Thread(target=run_download, args=(job_id, url, media_type), daemon=True).start()
    return jsonify(public_job(jobs[job_id])), 202


@app.get("/api/downloads/<job_id>")
def download_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            abort(404)
        return jsonify(public_job(job))


@app.get("/files/<path:filename>")
def downloaded_file(filename: str):
    path = (BASE_DIR / filename).resolve()
    if not any(path.is_relative_to(directory.resolve()) for directory in DOWNLOAD_DIRS.values()):
        abort(404)
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

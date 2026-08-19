import os
import re
import signal
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
        "title": job["title"],
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
        if jobs[job_id]["cancel_requested"]:
            jobs[job_id]["status"] = "cancelled"
            jobs[job_id]["message"] = "Download cancelled"
            return
        jobs[job_id]["message"] = "Connecting to YouTube..."

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    process = subprocess.Popen(
        command,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creation_flags,
        start_new_session=os.name != "nt",
    )
    with jobs_lock:
        jobs[job_id]["process"] = process
        jobs[job_id]["status"] = "running"
        cancel_immediately = jobs[job_id]["cancel_requested"]
    if cancel_immediately:
        terminate_process(process)

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
            title_match = re.match(r"Downloading (?:video|audio): (.+)", line)
            destination_match = re.search(r"\[download\] Destination: (.+)", line)
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
                if title_match:
                    job["title"] = title_match.group(1)
                elif destination_match:
                    filename = Path(destination_match.group(1)).name
                    job["title"] = re.sub(r"\.f\d+$", "", Path(filename).stem)
                if progress_match:
                    job["progress"] = float(progress_match.group(1))

    return_code = process.wait()
    after = {path.resolve() for path in output_directory.rglob("*") if path.is_file()}
    created = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
    completed_files = [path for path in created if path.suffix.lower() in {".mp4", ".mp3", ".m4a"}]

    with jobs_lock:
        job = jobs[job_id]
        job["process"] = None
        failed_in_log = any("Failed downloading" in line for line in job["logs"])
        if job["cancel_requested"]:
            job["status"] = "cancelled"
            job["message"] = "Download cancelled"
        elif return_code == 0 and not failed_in_log:
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
            "title": "Waiting for media information...",
            "progress": 0,
            "files": [],
            "logs": deque(maxlen=100),
            "process": None,
            "cancel_requested": False,
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


@app.post("/api/downloads/<job_id>/cancel")
def cancel_download(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            abort(404)
        if job["status"] not in {"queued", "running"}:
            return jsonify(public_job(job))
        job["cancel_requested"] = True
        job["message"] = "Cancelling download..."
        process = job["process"]

    if process is not None and process.poll() is None:
        terminate_process(process)
    return jsonify(public_job(job))


def terminate_process(process: subprocess.Popen) -> None:
    """Terminate a downloader and any FFmpeg/Node child processes it owns."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
    else:
        os.killpg(process.pid, signal.SIGTERM)


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

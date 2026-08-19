# YouTube Video Downloader

A local Python application for downloading individual YouTube videos, audio, playlists, and radio mixes. It includes both a command-line interface and a browser-based graphical interface.

The application saves video as MP4 at up to 720p and converts audio to 192 kbps MP3. Downloads are processed locally and are not uploaded to another service.

> Only download media that you own or have permission to use. You are responsible for complying with YouTube's terms and applicable copyright law.

## Features

- Download individual YouTube videos.
- Extract audio as 192 kbps MP3.
- Download normal playlists and dynamic YouTube radio mixes.
- Limit playlists to a maximum of 200 items.
- Prefer 720p MP4 video, with fallbacks when it is unavailable.
- Download and merge separate video and audio streams automatically.
- Detect existing files by media title and skip downloading them again.
- Show live size, speed, ETA, and media title.
- Show success or failure for every playlist item.
- Cancel active downloads from the web interface.
- Run entirely on `127.0.0.1`; the web interface is not exposed to the local network.
- Work with Python 3.14 on Windows.

## Requirements

- Python 3.14 or newer
- An internet connection
- A modern browser for the graphical interface

Python dependencies are listed in `requirements.txt`:

- `pytubefix` for YouTube metadata and direct progressive downloads
- `yt-dlp` with its EJS challenge solver for protected and adaptive streams
- `imageio-ffmpeg` for bundled FFmpeg video merging and MP3 conversion
- `Flask` for the local web interface

You do not need to install FFmpeg or Node.js globally. Compatible executables are supplied through the Python dependencies.

## Installation

Clone or download the repository, then open a terminal in its directory.

### Windows PowerShell

Create a Python 3.14 virtual environment:

```powershell
py -3.14 -m venv youtube-downloader
```

If `py` is unavailable but `python` points to Python 3.14:

```powershell
python -m venv youtube-downloader
```

Activate the environment:

```powershell
.\youtube-downloader\Scripts\Activate.ps1
```

If PowerShell prevents activation, either use the environment's interpreter directly or allow locally created scripts for the current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Install all dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Without activating the environment, the equivalent installation command is:

```powershell
.\youtube-downloader\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS and Linux

```bash
python3.14 -m venv youtube-downloader
source youtube-downloader/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Graphical interface

Activate the virtual environment and start Flask:

```powershell
python app.py
```

On macOS or Linux, the same command is used after activating the environment:

```bash
python app.py
```

Open the following address in a browser:

```text
http://127.0.0.1:5000
```

### Using the interface

1. Paste a YouTube video or playlist URL.
2. Select `MP4` for video or `MP3` for audio.
3. Select **Start download**.
4. Follow the active media title, progress bar, transferred size, total size, speed, and ETA.
5. For playlists, review the status and total size of each item in the media-results list.
6. Use **Cancel download** to stop an active job and its child FFmpeg or Node.js processes.
7. When the job completes, use the displayed file links to save or open newly downloaded media.

The Flask development server is intentionally bound to `127.0.0.1`. Do not expose it directly to the public internet.

## Command-line interface

The command syntax is:

```text
python youtube_video_downloader.py URL [video|audio] [--output DIRECTORY]
```

`video` is the default media type.

### Download one video

```powershell
python youtube_video_downloader.py "https://youtu.be/VIDEO_ID"
```

Or specify video explicitly:

```powershell
python youtube_video_downloader.py "https://youtu.be/VIDEO_ID" video
```

### Download one MP3

```powershell
python youtube_video_downloader.py "https://youtu.be/VIDEO_ID" audio
```

### Download a playlist or radio mix

```powershell
python youtube_video_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID" video
```

For an audio playlist:

```powershell
python youtube_video_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID" audio
```

Radio/mix URLs containing an `RD...` list identifier are supported through yt-dlp.

### Choose a different output location

```powershell
python youtube_video_downloader.py "https://youtu.be/VIDEO_ID" video --output "C:\Downloads"
```

The program creates the relevant `video-downloads` or `audio-downloads` folder inside the selected output directory.

## How downloads work

### Single videos

1. The URL is inspected with the pytubefix `WEB` client and automatic proof-of-origin token support.
2. The media title is sanitized for Windows-compatible filenames.
3. The destination is checked for an existing file with that title.
4. The downloader prefers a progressive 720p MP4 containing video and audio.
5. If 720p is unavailable, it tries 360p and then the highest available progressive MP4.
6. If YouTube only provides separate video and audio streams, yt-dlp downloads them and bundled FFmpeg merges them into one MP4.

### Audio

1. The destination is checked for an existing MP3 with the same title.
2. yt-dlp obtains the best suitable audio stream.
3. Bundled FFmpeg converts it to a 192 kbps MP3.
4. The temporary source audio is removed after successful conversion.

### Playlists and radio mixes

1. Any URL containing a `list` query parameter is treated as a playlist.
2. yt-dlp resolves regular playlists and dynamic radio mixes.
3. Entries are processed in playlist order, up to 200 items.
4. Before downloading an item, the output tree is searched for an MP4 or MP3 with the same sanitized title.
5. Existing titles are skipped.
6. Playlist files are placed in a subdirectory named after the playlist and prefixed with their playlist position.

Example output:

```text
video-downloads/
└── Playlist title/
    ├── 001 - First video.mp4
    └── 002 - Second video.mp4

audio-downloads/
└── Playlist title/
    ├── 001 - First track.mp3
    └── 002 - Second track.mp3
```

## Project structure

```text
.
├── app.py                         Flask server and background job management
├── youtube_video_downloader.py    Download engine and command-line interface
├── alt_youtube_video_downloader.py
├── convert_to_mp3.py              Legacy standalone MP4-to-MP3 converter
├── requirements.txt
├── static/
│   ├── app.js                     Browser behavior and API polling
│   └── styles.css                 YouTube-inspired interface styling
├── templates/
│   └── index.html                 Main web page
├── video-downloads/               Generated video output
└── audio-downloads/               Generated audio output
```

The `youtube-downloader/` virtual environment, downloaded media, and generated cache files are excluded from Git.

## Web API

The graphical interface uses a small local JSON API:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Display the graphical interface |
| `POST` | `/api/downloads` | Start a background download |
| `GET` | `/api/downloads/<job_id>` | Read job progress and item results |
| `POST` | `/api/downloads/<job_id>/cancel` | Cancel an active job |
| `GET` | `/files/<filename>` | Retrieve a completed local download |

Jobs are stored in memory. Restarting Flask clears the displayed job history but does not remove downloaded files.

## Troubleshooting

### `ModuleNotFoundError`

Confirm the virtual environment is activated and reinstall the requirements:

```powershell
.\youtube-downloader\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### YouTube bot, PO-token, or HTTP 403 errors

YouTube regularly changes its playback protection. First ensure all pinned dependencies are installed:

```powershell
python -m pip install --upgrade -r requirements.txt
```

The application configures pytubefix's automatic token generation and yt-dlp's Node/EJS challenge solver. Some videos may still be unavailable because of region restrictions, authentication requirements, account restrictions, or temporary YouTube enforcement.

### `WinError 10013`

Windows or security software denied the Python process permission to open a network socket. Check that Python is permitted through Windows Firewall and that another security product is not blocking it. Stop the current Flask process and restart it from your normal terminal:

```powershell
python app.py
```

### Port 5000 is already in use

Stop the previous Flask process, or change the port at the bottom of `app.py`:

```python
app.run(host="127.0.0.1", port=5001, debug=False)
```

Then open `http://127.0.0.1:5001`.

### A cancelled download left a partial file

yt-dlp may retain `.part` files so a later attempt can resume. If you do not want to resume, close the application and remove only the relevant `.part` file from the appropriate download directory.

### Existing media is skipped unexpectedly

Duplicate detection is title-based. Rename or move the existing MP3/MP4 if you intentionally want to download another copy with the same title.

## Legacy utilities

`alt_youtube_video_downloader.py` and `convert_to_mp3.py` are older standalone utilities retained for reference. The main CLI and Flask interface already provide adaptive video merging and MP3 conversion, so these scripts are not needed for the normal workflow.

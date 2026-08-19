import argparse
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pytubefix import Playlist, YouTube
from pytubefix.exceptions import PytubeFixError


COMPLETE = "\033[92m"  # green
FAIL = "\033[91m"  # red
EXISTS = "\033[93m"  # yellow
END_COLOR = "\033[0m"
MAX_PLAYLIST_ITEMS = 200
YOUTUBE_CLIENT = "WEB"


def on_progress(stream, _chunk: bytes, bytes_remaining: int) -> None:
    """Display download progress using characters supported by Windows consoles."""
    filesize = stream.filesize
    percent = 100 if not filesize else (filesize - bytes_remaining) * 100 / filesize
    print(f"\rProgress: {percent:5.1f}%", end="", flush=True)
    if bytes_remaining == 0:
        print()


def youtube_download(url: str, media_type: str = "video", output_root: str | Path = ".") -> None:
    """Download one YouTube item or a playlist as video or audio."""
    media_type = media_type.lower()
    if media_type not in {"video", "audio"}:
        raise ValueError("media_type must be 'video' or 'audio'")

    download_directory = Path(output_root) / f"{media_type}-downloads"
    download_directory.mkdir(parents=True, exist_ok=True)

    if _is_playlist_url(url):
        download_playlist(Playlist(url, client=YOUTUBE_CLIENT), media_type, download_directory)
    else:
        download_single_media(url, media_type, download_directory)


def _is_playlist_url(url: str) -> bool:
    return bool(parse_qs(urlparse(url).query).get("list"))


def _safe_filename(title: str) -> str:
    """Remove characters that are invalid in Windows filenames."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title).strip().rstrip(".")
    return cleaned or "untitled"


def type_video(yt: YouTube):
    streams = yt.streams.filter(file_extension="mp4", progressive=True)
    stream = streams.filter(res="720p").first() or streams.filter(res="360p").first()
    if stream is None:
        stream = streams.get_highest_resolution()
    if stream is None:
        streams = yt.streams.filter(file_extension="mp4", only_video=True)
        stream = streams.filter(res="720p").first() or streams.filter(res="360p").first()
    if stream is None:
        stream = streams.get_highest_resolution()
    if stream is None:
        raise RuntimeError("No MP4 video stream is available")
    print(f"resolution: {stream.resolution}")
    return stream


def type_audio(yt: YouTube):
    stream = yt.streams.filter(file_extension="mp4", only_audio=True).order_by("abr").desc().first()
    if stream is None:
        raise RuntimeError("No MP4 audio stream is available")
    print(f"abr: {stream.abr}")
    return stream


def download_playlist(
    playlist: Playlist, media_type: str = "video", output_root: str | Path = "."
) -> None:
    playlist_directory = Path(output_root) / _safe_filename(playlist.title)
    playlist_directory.mkdir(parents=True, exist_ok=True)
    print(f"Downloading playlist: {playlist.title}")

    urls = playlist.video_urls[:MAX_PLAYLIST_ITEMS]
    for index, url in enumerate(urls, 1):
        print(f"{index}/{len(urls)}")
        download_single_media(url, media_type, playlist_directory)

    print(f"{COMPLETE}Complete downloading playlist: {playlist.title}{END_COLOR}")


def download_single_media(
    url: str, media_type: str = "video", output_directory: str | Path = "."
) -> bool:
    media_type = media_type.lower()
    if media_type not in {"video", "audio"}:
        raise ValueError("media_type must be 'video' or 'audio'")

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    try:
        # WEB enables pytubefix's automatic PO-token generation, which is
        # required when YouTube rejects the default client as a bot.
        yt = YouTube(
            url,
            client=YOUTUBE_CLIENT,
            on_progress_callback=on_progress,
        )
        title = _safe_filename(yt.title)
        destination = output_directory / f"{title}.mp4"

        existing_files = [
            output_directory / f"{title}{suffix}" for suffix in (".mp4", ".m4a", ".mp3")
        ]
        if any(path.is_file() for path in existing_files):
            print(f"{EXISTS}Already downloaded: {title}{END_COLOR}")
            return True

        print(f"Downloading {media_type}: {title}")
        if media_type == "audio":
            _download_with_ytdlp(yt.watch_url, destination, media_type)
        else:
            stream = type_video(yt)
            print(f"file size: {stream.filesize / 1_000_000:.2f} MB")
            if not stream.is_progressive:
                _download_with_ytdlp(yt.watch_url, destination, media_type)
            else:
                stream.download(output_path=str(output_directory), filename=destination.name)
    except (PytubeFixError, OSError, RuntimeError) as error:
        print(f"{FAIL}Failed downloading {media_type}: {error}{END_COLOR}")
        return False

    print(f"{COMPLETE}Complete downloading {media_type}: {title}{END_COLOR}")
    return True


def _download_with_ytdlp(url: str, destination: Path, media_type: str) -> None:
    """Download protected/adaptive streams with yt-dlp and bundled FFmpeg."""
    try:
        import imageio_ffmpeg
        import nodejs_wheel
        import yt_dlp
    except ImportError as error:
        raise RuntimeError(
            "This video requires yt-dlp and FFmpeg. "
            "Run: python -m pip install -r requirements.txt"
        ) from error

    if media_type == "video":
        print("This video uses separate video and audio streams; downloading both.")
        format_selector = (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
            "best[height<=720][ext=mp4]"
        )
    else:
        print("Downloading the best available audio stream.")
        format_selector = "bestaudio[ext=m4a]/bestaudio"

    options = {
        "format": format_selector,
        "outtmpl": str(destination.parent / f"{destination.stem}.%(ext)s"),
        "merge_output_format": "mp4",
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "js_runtimes": {
            "node": {"path": str(Path(nodejs_wheel.__file__).parent / "node.exe")}
        },
        "extractor_args": {"youtube": {"player_client": ["web_embedded"]}},
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
    }
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            result = downloader.download([url])
    except yt_dlp.utils.DownloadError as error:
        raise RuntimeError(f"yt-dlp failed: {error}") from error
    if result:
        raise RuntimeError(f"yt-dlp exited with status {result}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a YouTube video or playlist.")
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument(
        "media_type", nargs="?", default="video", choices=("video", "audio")
    )
    parser.add_argument("--output", default=".", help="Parent download directory")
    args = parser.parse_args()
    youtube_download(args.url, args.media_type, args.output)


if __name__ == "__main__":
    main()

from pytube import YouTube
from pytube import Playlist
from pytube.cli import on_progress
import os

COMPLETE = "\033[92m" # green
FAIL = "\033[91m" # red
EXISTS = "\033[93m" # yellow
END_COLOR = "\033[0m" # stop

def youtube_download(url, type="video"):
    video_download_directory(f'{type}-downloads')
    try:
        playlist = Playlist(url)
        download_playlist(playlist, type)
    except KeyError:
        download_single_media(url, type) 
    finally:
        os.system('spd-say "download complete"')   

def video_download_directory(directory_name):
    if os.path.isdir(directory_name):
        print(f'{EXISTS}File exists: {directory_name}{END_COLOR}')
    else:
        print(f'Creating file: {directory_name}')
        os.mkdir(directory_name)
    print('--------')
    os.chdir(directory_name)

def type_video(yt):
    video_resolution = [stream.resolution for stream in yt.streams.filter(progressive=True)]
    if '720p' in video_resolution:
        res = '720p'
    else:
        res = '360p'
    print(f"resolution: {res}")
    return yt.streams.filter(file_extension='mp4', res=res).first()

def type_audio(yt):
    abr = [stream.abr for stream in yt.streams.filter(file_extension='mp4', progressive=False, only_audio=True)][-1]
    print(f"abr = {abr}")
    return yt.streams.filter(file_extension='mp4', only_audio=True, abr=abr).first()

def download_playlist(playlist, type="video"):
    playlist_title = playlist.title.replace('|', '--')
    video_download_directory(playlist_title)
    print(f'Downloading playlist: {playlist_title}')
    print('------')
    for url in enumerate(playlist.video_urls[:200]): # limiting playlists to 200 as music playlists go on forever
        download_single_media(url, type)
    print(f'{COMPLETE}Complete downloading playlist: {playlist_title}{END_COLOR}')
    os.chdir('..')

def download_single_media(url, type="video"):
    type = type.lower()
    assert type in ["video", "audio"], "type should be video or audio"
    yt = YouTube(url, on_progress_callback=on_progress)
    yt_title = ''.join(['' if char in '.:|,' else char for char in yt.title])
    if os.path.isfile(f'{yt_title}.mp4'):
        print(f'{EXISTS}Video already downloaded: {yt_title}{END_COLOR}')
    else:
        print(f'Downloading {type}: {yt_title}')
        try:
            if type == "video":
                stream = type_video(yt)
            else:
                stream = type_audio(yt)
            print(f"file size: {stream.filesize /(1000*1000):.2f}MB")
            stream.download()
            print(f'{COMPLETE}Complete downloading {type}: {yt_title}{END_COLOR}')
        except:
            print(f'{FAIL}Failed downloading {type}: {yt_title}{END_COLOR}')
    print('----')

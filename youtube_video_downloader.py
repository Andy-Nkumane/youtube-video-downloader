from pytube import YouTube
from pytube import Playlist
from pytube.cli import on_progress
import os

COMPLETE = "\033[92m" # green
FAIL = "\033[91m" # red
EXISTS = "\033[93m" # yellow
END_COLOR = "\033[0m" # stop

def youtube_download(url):
    video_download_directory('downloaded-videos')
    try:
        playlist = Playlist(url)
        download_playlist(playlist)
    except KeyError:
        download_single_video(url) 
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

def download_playlist(playlist):
    playlist_title = playlist.title.replace('|', '--')
    video_download_directory(playlist_title)
    print(f'Downloading playlist: {playlist_title}')
    print('------')
    for url in playlist.video_urls:
        download_single_video(url)
    print(f'{COMPLETE}Complete downloading playlist: {playlist_title}{END_COLOR}')
    os.chdir('..')

def download_single_video(url):
    yt = YouTube(url, on_progress_callback=on_progress)
    yt_title = ''.join(['' if char in '.:|,' else char for char in yt.title])
    if os.path.isfile(f'{yt_title}.mp4'):
        print(f'{EXISTS}Video already downloaded: {yt_title}{END_COLOR}')
    else:
        print(f'Downloading video: {yt_title}')
        try:
            video_resolution = [stream.resolution for stream in yt.streams.filter(progressive=True)]
            if '720p' in video_resolution:
                res = '720p'
            else:
                res = '360p'
            stream = yt.streams.filter(file_extension='mp4', res=res).first()
            print(f"resolution: {res}")
            print(f"file size: {stream.filesize /(1000*1000):.2f}MB")
            stream.download()
            print(f'{COMPLETE}Complete downloading video: {yt_title}{END_COLOR}')
        except:
            print(f'{FAIL}Failed downloading video: {yt_title}{END_COLOR}')
    print('----')

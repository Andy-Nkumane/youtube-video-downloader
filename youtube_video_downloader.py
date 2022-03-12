from pytube import YouTube
from pytube import Playlist
import os

COMPLETE = "\033[92m" # green
FAIL = "\033[91m" # red
EXISTS = "\033[93m" # yellow
END_COLOR = "\033[0m" # stop

def youtube_download(link):
    try:
        playlist = Playlist(link)
        download_playlist(playlist)
    except KeyError:
        download_single_video(link) 
    finally:
        os.system('spd-say "download complete"')   

def download_playlist(playlist):
    playlist_title = playlist.title.replace('|', '--')
    if os.path.isdir(playlist_title):
        print(f'{EXISTS}File exists: {playlist_title}{END_COLOR}')
    else:
        print(f'Creating file: {playlist_title}')
        os.mkdir(playlist_title)
    print('--------')
    os.chdir(playlist_title)
    print(f'Downloading playlist: {playlist_title}')
    print('------')
    for url in playlist.video_urls:
        download_single_video(url)
    print(f'{COMPLETE}Complete downloading playlist: {playlist_title}{END_COLOR}')
    os.chdir('..')

def download_single_video(link):
    yt = YouTube(link)
    yt_title = ''.join(['' if char in '.:|,' else char for char in yt.title])
    if os.path.isfile(f'{yt_title}.mp4'):
        print(f'{EXISTS}Video already downloaded: {yt_title}{END_COLOR}')
    else:
        print(f'Downloading video: {yt_title}')
        try:
            stream = yt.streams.filter(file_extension='mp4', res='480p').first()
            stream.download()
            print(f'{COMPLETE}Complete downloading video: {yt_title}{END_COLOR}')
        except:
            print(f'{FAIL}Failed downloading video: {yt_title}{END_COLOR}')
    print('----')


youtube_download("https://www.youtube.com/watch?v=CLWpkv6ccpA&list=PLSQl0a2vh4HAB5mMeiG2DQy1FL5e9I4eg")



from flask import Flask, render_template, request, url_for, flash, redirect, send_file
# from werkzeug.exceptions import abort
from urllib.parse import urlparse
# from processing import youtube_download, download_single_media
from pytube import YouTube
from pytube import Playlist
from pytube.cli import on_progress
import os
import pytube
# from pathlib import Path
# import os
import re

# run this first:
# export FLASK_APP=app
# export FLASK_DEBUG=True

# to run app use:
# flask --app app run

# downloading functions
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
    for index, url in enumerate(playlist.video_urls, 1): 
        if index < 201:# limiting playlists to 200 as music playlists go on forever
            print(index)
            download_single_media(url, type)
        else:
            break
    print(f'{COMPLETE}Complete downloading playlist: {playlist_title}{END_COLOR}')
    os.chdir('..')

def download_single_media(url, type="video"):
    type = type.lower()
    assert type in ["video", "audio"], "type should be video or audio"
    yt = YouTube(url, on_progress_callback=on_progress)
    try:
        yt_title = ''.join(['' if char in '.:|,' else char for char in yt.title])
    except pytube.exceptions.PytubeError:
        print(f'{FAIL}Failed downloading {type}: API issue{END_COLOR}')
        return

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

# flask functions
def get_youtube_link():
    if request.method == 'POST':
        youtube_link = request.form['youtube-link']
        if not youtube_link:
            flash("YouTube link is required!")
        return youtube_link
    
def validate_link(url):
    parse_result = urlparse(url)
    is_url = all([parse_result.scheme, parse_result.netloc, parse_result.path])
    validate_video_url = (
                r'(https?://)?(www\.)?'
                '(youtube|youtu|youtube-nocookie)\.(com|be)/'
                '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            )
    is_youtube_link = re.match(validate_video_url, url)
    if url == "":
        return False
    if not is_url:
        flash('Invalid link entered - enter correct link!')
    elif not is_youtube_link:
        flash('Invalid YouTube link entered - enter correct YouTube link!')
    return is_url and is_youtube_link

def add_to_textarea(text=''):
    download_log_existing_data = request.form.get('download-log')
    if download_log_existing_data and text:
        return f'{download_log_existing_data}\n----\n{text}' 
    elif not text:
        return download_log_existing_data
    else:
        return text
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key' # remove from script, get from environmental variable

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/audio', methods=('GET', 'POST'))
def audio():
    youtube_link = get_youtube_link()
    if request.method == 'POST':
        if validate_link(youtube_link):
            # download_log_existing_data = request.form.get('download-log') or '----\n'
            # download_log_new_data = download_log_existing_data + youtube_link + '-> added\n----\n'
            return render_template('audio.html', download_log = add_to_textarea(youtube_link))
    return render_template('audio.html')

@app.route('/video', methods=('GET', 'POST'))
def video():
    youtube_link = get_youtube_link()
    if request.method == 'POST':
        # message = ''
        # if(youtube_link):
            # validate_video_url = (
            #     r'(https?://)?(www\.)?'
            #     '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            #     '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            # )
            
        if validate_link(youtube_link):
            # given working code - doesn't show download progress
            # # add_to_textarea(f'{validVideoUrl} ---- valid')
            # # flash(validVideoUrl)
            # url = YouTube(youtube_link)
            # # flash(url)
            # downloadFolder = str(os.path.join(Path.home(), "Downloads"))
            # # flash(downloadFolder)
            # video = url.streams.get_highest_resolution()
            # # flash(video)
            # video.download(downloadFolder)
            # mesage = 'Video Downloaded Successfully!'
            # flash(mesage)
            pass
        else:
            # message = 'Enter Valid YouTube Video URL!'
            # flash(message)
            return render_template('video.html', download_log = add_to_textarea(""))
        return render_template('video.html', download_log = add_to_textarea(youtube_link))
        if validate_link(youtube_link):
            # youtube_download(youtube_link)
            # download_single_media(youtube_link)
            download_log_existing_data = request.form.get('download-log') or '----\n'
            # download_log_new_data = download_log_existing_data + youtube_link + '-> added\n----\n'
            # mesage = ''
            # errorType = 0
            # if request.method == 'POST' and 'video_url' in request.form:
            #     youtubeUrl = request.form["video_url"] Matthew Wilder - Break My Stride 
            #     if(youtubeUrl):
            #         validateVideoUrl = (
            #     r'(https?://)?(www\.)?'
            #     '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            #     '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
            #         validVideoUrl = re.match(validateVideoUrl, youtubeUrl)
            #         if validVideoUrl:
            #             url = YouTube(youtubeUrl)
            #             video = url.streams.get_highest_resolution()
            #             downloadFolder = str(os.path.join(Path.home(), "Downloads"))
            #             video.download(downloadFolder)
            #             mesage = 'Video Downloaded Successfully!'
            #             errorType = 1
            #         else:
            #             mesage = 'Enter Valid YouTube Video URL!'
            #             errorType = 0
            #     else:
            #         mesage = 'Enter YouTube Video Url.'
            #         errorType = 0            
            # return render_template('video.html', mesage = mesage, errorType = errorType, download_log = add_to_textarea(youtube_link))
            return render_template('video.html', download_log = add_to_textarea(youtube_link) )
    return render_template('video.html')

# @app.route("/download_video", methods=["GET","POST"])
# def download_video():      
#     mesage = ''
#     errorType = 0
#     if request.method == 'POST' and 'video_url' in request.form:
#         youtubeUrl = request.form["video_url"]
#         if(youtubeUrl):
#             validateVideoUrl = (
#         r'(https?://)?(www\.)?'
#         '(youtube|youtu|youtube-nocookie)\.(com|be)/'
#         '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
#             validVideoUrl = re.match(validateVideoUrl, youtubeUrl)
#             if validVideoUrl:
#                 flash(validVideoUrl)
#                 url = YouTube(youtubeUrl)
#                 video = url.streams.get_highest_resolution()
#                 downloadFolder = str(os.path.join(Path.home(), "Downloads"))
#                 flash(downloadFolder)
#                 video.download(downloadFolder)
#                 mesage = 'Video Downloaded Successfully!'
#                 flash(mesage)
#                 errorType = 1
#             else:
#                 mesage = 'Enter Valid YouTube Video URL!'
#                 errorType = 0
#         else:
#             mesage = 'Enter YouTube Video Url.'
#             errorType = 0            
#     return render_template('video.html', mesage = mesage, errorType = errorType) 


app.route('/download')
def download():
    path = 'samplefile.pdf'
    return render_template('index.html')
    # return send_file(path, as_attachment=True)
    # return send_file('/home/wethinkcode/Downloads/Pecha Kucha 3_ Git.pdf', attachment_filename='Pecha Kucha 3_ Git(flask).pdf')
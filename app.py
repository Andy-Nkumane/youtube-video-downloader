from flask import Flask, render_template, request, url_for, flash, redirect, send_file
from werkzeug.exceptions import abort
from urllib.parse import urlparse
# from processing import youtube_download, download_single_media
from pytube import YouTube
from pathlib import Path
import os
import re

# run this first:
# export FLASK_APP=app
# export FLASK_DEBUG=True

# to run app use:
# flask --app app run

def get_youtube_link():
    if request.method == 'POST':
        youtube_link = request.form['youtube-link']
        if not youtube_link:
            flash("YouTube link is required!")
        return youtube_link
    
def validate_link(url):
    parse_result = urlparse(url)
    is_url = all([parse_result.scheme, parse_result.netloc, parse_result.path])
    if not is_url:
        flash('Invalid link entered - enter correct link!')
    return is_url

def add_to_textarea(text):
    download_log_existing_data = request.form.get('download-log') 
    if download_log_existing_data:
        return f'{download_log_existing_data}\n----\n{text}' 
    else:
        return f'{text}' 

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
    flash(youtube_link)
    errorType = 0
    if request.method == 'POST':
        flash("POST")
        mesage = ''
    # if request.method == 'POST' and youtube_link in request.form:
        # youtubeUrl = request.form["video_url"]
        # flash(youtube_link)
        if(youtube_link):
            validateVideoUrl = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
            validVideoUrl = re.match(validateVideoUrl, youtube_link)
            # flash(validVideoUrl)
            if validVideoUrl:
                add_to_textarea(f'{validVideoUrl} ---- valid')
                # flash(validVideoUrl)
                url = YouTube(youtube_link)
                # flash(url)
                downloadFolder = str(os.path.join(Path.home(), "Downloads"))
                # flash(downloadFolder)
                video = url.streams.get_highest_resolution()
                # flash(video)
                video.download(downloadFolder)
                mesage = 'Video Downloaded Successfully!'
                flash(mesage)
                errorType = 1
            else:
                mesage = 'Enter Valid YouTube Video URL!'
                flash(mesage)
                errorType = 0
        else:
            mesage = 'Enter YouTube Video Url.'
            errorType = 0            
        return render_template('video.html', mesage = mesage, errorType = errorType, download_log = add_to_textarea(youtube_link))
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
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from urllib.parse import urlparse

# run this first:
# export FLASK_APP=app
# export FLASK_DEBUG=True

def get_youtube_link():
    if request.method == 'POST':
        youtube_link = request.form['youtube-link']
        # if not youtube_link:
        #     flash("YouTube link is required!")
        return youtube_link
    
def validate_link(url):
    parse_result = urlparse(url)
    is_url = all([parse_result.scheme, parse_result.netloc, parse_result.path])
    if not is_url:
        flash('Invalid link entered - enter correct link!')
    return is_url

def add_to_textarea(text):
    download_log_existing_data = request.form.get('download-log') or '----'
    return f'{download_log_existing_data}\n{text}' 

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
        if validate_link(youtube_link):
            # download_log_existing_data = request.form.get('download-log') or '----\n'
            # download_log_new_data = download_log_existing_data + youtube_link + '-> added\n----\n'
            return render_template('video.html', download_log = add_to_textarea(youtube_link) )
    return render_template('video.html')
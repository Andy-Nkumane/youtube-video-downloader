from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort

# run this first:
# export FLASK_APP=app
# export FLASK_DEBUG=True

def get_youtube_link():
    if request.method == 'POST':
        youtube_link = request.form['youtube-link']
        if not youtube_link:
            flash("YouTube link is required!")
        return youtube_link

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
    return render_template('audio.html')

@app.route('/video', methods=('GET', 'POST'))
def video():
    youtube_link = get_youtube_link()
    return render_template('video.html')
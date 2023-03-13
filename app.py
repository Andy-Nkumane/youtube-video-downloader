from flask import Flask, render_template, request, url_for, flash
from werkzeug.exceptions import abort

# run this first:
# export FLASK_APP=<script name>
# export FLASK_DEBUG=True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key' # remove from script, get from environmental variable

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/audio')
def audio():
    return render_template('audio.html')

@app.route('/video')
def video():
    return render_template('video.html')
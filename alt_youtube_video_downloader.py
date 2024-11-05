import yt_dlp

# Set your playlist URL
# playlist_url = 'https://www.youtube.com/watch?v=mTrxJh34XvM&list=PLxxgLka_Odb_th4qGyoFLby4rR21y51v_'

# Define the save path for downloaded audio files
# save_path = 'directory-name'

# Function to download audio from the playlist
def download_best_audio_as_mp3(playlist_url, save_path):
    ydl_opts = {
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',  # Output filename template
        'postprocessors': [{  # Post-processing options
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',  # Convert to MP3
            'preferredquality': '0',  # Best quality
        }],
        'format': 'bestaudio/best',  # Download best audio available
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])  # Download the playlist

# Call the function to start downloading
# download_best_audio_as_mp3(playlist_url, save_path)
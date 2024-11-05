import os
import subprocess

# Set the directory where the MP4 files are located
input_dir = "audio-downloads"

# Set the directory where the converted MP3 files will be saved
output_dir = "audio-downloads/mp3"

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Function to recursively convert MP4 files to MP3 in a directory
def convert_mp4_to_mp3(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isdir(file_path):
            # Recursively process subdirectories
            convert_mp4_to_mp3(file_path)
        elif filename.endswith(".mp4"):
            # Construct the input and output file paths
            input_file = file_path
            output_file = os.path.join(output_dir, os.path.relpath(directory, input_dir), os.path.splitext(filename)[0] + ".mp3")
            output_dir_path = os.path.dirname(output_file)
            if not os.path.exists(output_dir_path):
                os.makedirs(output_dir_path)
            
            # Check if the output file already exists
            if os.path.exists(output_file):
                print(f"Skipping {filename} as the output file {os.path.basename(output_file)} already exists.")
                continue
            
            # Run the ffmpeg command to convert the file
            subprocess.run(["ffmpeg", "-i", input_file, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", output_file], check=True)
            print(f"Converted {filename} to {os.path.basename(output_file)}")

# Start the conversion process from the input directory
convert_mp4_to_mp3(input_dir)
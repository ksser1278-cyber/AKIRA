import subprocess
import os

def download_audio(url, output_path):
    print(f"Downloading: {url} -> {output_path}")
    dir_path = os.path.dirname(output_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # yt-dlp command to extract audio and convert to flac
    # -x: extract audio
    # --audio-format flac: convert to flac
    # -o: output filename template
    command = [
        "yt-dlp",
        "-x",
        "--audio-format", "flac",
        "--audio-quality", "0",
        "-o", output_path.replace(".flac", ".%(ext)s"),
        url
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Successfully downloaded: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {url}: {e}")

# Song list mappings
songs = {
    "pinocchiop": [
        ("https://www.youtube.com/watch?v=EHBFKhLUVig", "kamippoi_na.flac"),
        ("https://www.youtube.com/watch?v=LYWP8HtgeLQ", "tensei_ringo.flac"),
        ("https://www.youtube.com/watch?v=yiqEEL7ac6M", "tokumei_m.flac"),
        ("https://www.youtube.com/watch?v=T2kS1gAbxhc", "mahou_shoujo_to_chocolate.flac"),
        ("https://www.youtube.com/watch?v=lw7pcm1W5tw", "non_breath_oblige.flac"),
    ],
    "deco27": [
        ("https://www.youtube.com/watch?v=kbNdx0yqbZE", "monitoring.flac"),
        ("https://www.youtube.com/watch?v=eSW2LVbPThw", "rabbit_hole.flac"),
        ("https://www.youtube.com/watch?v=e1xCOsgWG0M", "vampire.flac"),
        ("https://www.youtube.com/watch?v=adGhT_-JbZI", "cinderella.flac"),
        ("https://www.youtube.com/watch?v=KushW6zvazM", "ghost_rule.flac"),
    ]
}

base_dir = r"data\audio"

for artist, track_list in songs.items():
    artist_dir = os.path.join(base_dir, artist)
    for url, filename in track_list:
        full_path = os.path.join(artist_dir, filename)
        if os.path.exists(full_path):
            print(f"Skipping {filename}, already exists.")
            continue
        download_audio(url, full_path)

print("All tasks completed.")

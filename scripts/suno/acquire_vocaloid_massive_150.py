import os
import sys
import json
import time
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import yt_dlp
except ImportError:
    print("yt-dlp missing. Please install it.")
    exit(1)

MANIFEST_PATH = Path("scripts/suno/vocaloid_150_manifest.json")
OUTPUT_DIR = Path("outputs/suno_v55_custom_models/massive_150")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_technical_tags(model_name, track):
    if model_name == "Model_A_Staccato_Speed":
        return ["high bpm", "staccato piano", "aggressive guitar", "fast-paced vocaloid", "information density", "industrial rock", "vocaloid-core"]
    elif model_name == "Model_B_Humanoid_Pop":
        return ["clean pop", "humanoid tuning", "expressive vibrato", "clear high-fidelity vocals", "melodic synthpop", "piano rock", "emotional piano"]
    elif model_name == "Model_C_Bass_Glitch":
        return ["heavy bass", "sub-bass", "glitch-hop", "808 kick", "urban night", "electronic dance", "stutter-edits", "dubstep-leaning"]
    return ["vocaloid"]

def process_massive_acquisition():
    if not MANIFEST_PATH.exists():
        print("Manifest missing!")
        return

    with MANIFEST_PATH.open(encoding="utf-8") as f:
        manifest = json.load(f)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_audio': True,
        'quiet': True,
        'no_warnings': True,
    }

    for model_name, tracks in manifest.items():
        print(f"\n======================\nAcquiring Massive Cluster: {model_name}\n======================")
        audio_dir = OUTPUT_DIR / f"{model_name}_Audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        records = []
        
        for i, track in enumerate(tracks):
            artist = track["artist"]
            title = track["title"]
            tid = track["id"]
            
            clean_title = "".join(x for x in title if x.isalnum() or x in " -_")
            clean_artist = "".join(x for x in artist if x.isalnum() or x in " -_")
            prefix = f"{tid}_{clean_artist}_{clean_title}_ref"
            
            output_path = audio_dir / prefix
            
            # Check if file exists
            has_file = list(audio_dir.glob(f"{prefix}.*"))
            
            tags = generate_technical_tags(model_name, track)
            prompt = f"[Style: {', '.join(tags)}]"
            
            # Record shell (Lyrics will be fetched/inserted manually or via a separate pass)
            # For now, we seed with artist/title to ensure we can match lyrics later.
            record = {
                "metadata": {"artist": artist, "title": title, "id": tid},
                "suno_prompt": prompt,
                "lyrics": f"[Intro]\n(Electronic patterns matching {model_name} style)\n\n[Verse 1]\n(Lyrics pending for {title})\n"
            }
            
            if has_file:
                records.append(record)
            else:
                ydl_opts["outtmpl"] = str(output_path) + ".%(ext)s"
                print(f"  [{i+1}/50] Downloading: {artist} - {title}")
                try:
                    search_query = f"ytsearch1:{artist} {title} original vocaloid"
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([search_query])
                    records.append(record)
                    time.sleep(1)
                except Exception:
                    print(f"   -> Failed {title}")

        # Save partial JSONL (to be filled with lyrics)
        jsonl_path = OUTPUT_DIR / f"{model_name}.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    process_massive_acquisition()

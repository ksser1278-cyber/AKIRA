import os
import sys
import json
import time
from pathlib import Path

# Force UTF-8 for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import yt_dlp
except ImportError:
    print("yt-dlp missing. run: pip install yt-dlp")
    exit(1)

def get_url_from_conditioning(title, artist):
    data_dir = Path("data")
    for root, dirs, files in os.walk(data_dir):
        if "reference_tracks" not in root: continue
        for name in files:
             if name.endswith(".json"):
                 path = Path(root) / name
                 try:
                     with path.open(encoding="utf-8") as f:
                         content = json.load(f)
                     tid = content.get("track_identity", {})
                     
                     if tid and tid.get("title") == title:
                         lyric_sources = content.get("source_provenance", {}).get("lyric_sources", [])
                         for src in lyric_sources:
                             # Some sources are UtaTen, we want Youtube
                             if "youtu" in src.get("url", ""):
                                  return src.get("url")
                         return None # we found the file but no youtube link
                 except: pass
    return None

def download_audio_for_bundle():
    bundle_dir = Path("outputs/suno_v55_custom_models")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_audio': True,
        # fallback to best audio naturally available without ffmpeg
        'postprocessors': [],
        'quiet': True,
        'no_warnings': True,
    }
    
    # We process each .jsonl 
    for jsonl_file in bundle_dir.glob("*.jsonl"):
        model_name = jsonl_file.stem
        output_folder = bundle_dir / f"{model_name}_Audio"
        output_folder.mkdir(parents=True, exist_ok=True)
        print(f"\n[{model_name}] Starting Downloads (Target Folder: {output_folder})")
        
        with jsonl_file.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if not line.strip(): continue
                record = json.loads(line)
                title = record["metadata"]["title"]
                artist = record["metadata"]["artist"]
                
                # Check target file early (assume .m4a or .webm might be output)
                # Keep it simple: clean filename matching
                clean_title = "".join(x for x in title if x.isalnum() or x in " -_")
                clean_artist = "".join(x for x in artist if x.isalnum() or x in " -_")
                file_prefix = output_folder / f"{clean_artist}_{clean_title}_ref"
                
                # if already downloaded, skip
                if any(file_prefix.parent.glob(f"{file_prefix.name}.*")):
                    print(f"  [SKIP] {idx}. {artist} - {title} (Already Exists)")
                    continue
                
                url = get_url_from_conditioning(title, artist)
                
                # First attempt: Try the exact URL from our database
                search_query = url if url else f"ytsearch1:{artist} {title} official audio"
                ydl_opts["outtmpl"] = str(file_prefix) + ".%(ext)s"
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([search_query])
                    time.sleep(1)
                except Exception as e:
                    print(f"  [ERR] Exact URL failed, falling back to raw search for {title}...")
                    try:
                        # Fallback attempt: Search for alternative upload
                        base_search = f"ytsearch1:{artist} {title}"
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            ydl2.download([base_search])
                        time.sleep(1)
                    except Exception as e2:
                        print(f"  [FATAL] Both exact link and search failed for {title}: {str(e2)[:50]}")

if __name__ == "__main__":
    download_audio_for_bundle()

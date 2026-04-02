import json
import requests
import time
import sys
import re
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path for akira_engine imports
sys.path.append(str(Path("src").resolve()))
from akira_engine.japanese_lyric_features import build_markdown_japanese_profile, mora_unit_estimate

MANIFEST_PATH = Path("scripts/suno/vocaloid_150_manifest.json")
OUTPUT_DIR = Path("outputs/suno_v55_custom_models/massive_150/definitive")
VOCADB_API = "https://vocadb.net/api/songs"

def auto_section_lyrics(title, lyrics_raw):
    """
    High-Fidelity Structural DNA Detection (Duplicated from refiner for autonomy).
    """
    lines = [line.strip() for line in lyrics_raw.splitlines() if line.strip()]
    if not lines: return ""
    mora_counts = [mora_unit_estimate(line) for line in lines]
    avg_mora = sum(mora_counts) / len(mora_counts) if mora_counts else 0
    sections = []
    current_section = []
    for i, line in enumerate(lines):
        current_section.append(line)
        should_split = False
        if i < len(lines) - 1:
            if abs(mora_counts[i] - mora_counts[i+1]) > 5 and len(current_section) >= 2:
                should_split = True
        if len(current_section) >= 8: should_split = True
        if should_split or i == len(lines) - 1:
            sec_len = len(current_section)
            sec_avg_mora = sum(mora_unit_estimate(l) for l in current_section) / sec_len
            sec_type = "Verse"
            if len(sections) == 0: sec_type = "Intro"
            elif sec_len <= 4 and sec_avg_mora < avg_mora: sec_type = "Pre-Chorus"
            elif sec_avg_mora > avg_mora: sec_type = "Chorus"
            sections.append(f"[{sec_type}]")
            sections.extend(current_section)
            sections.append("")
            current_section = []
    return "\n".join(sections)

def fetch_definitive_song(title, artist):
    """Hyper-Robust Search for the DEFINITIVE artist version."""
    search_queries = [
        f"{artist} {title}", # Stage 1: Specific
        title,               # Stage 2: Broad (Title only)
    ]
    
    for query in search_queries:
        params = {
            "query": query,
            "maxResults": 20,
            "sort": "RatingScore",
            "fields": "Lyrics"
        }
        try:
            r = requests.get(VOCADB_API, params=params, timeout=10)
            if r.status_code != 200: continue
            
            data = r.json()
            items = data.get("items", [])
            for song in items:
                song_artist = song.get("artistString", "").lower()
                song_title = song.get("name", "").lower()
                
                # Check for Original Artist Match
                # We check for artist name presence in artistString or the song name itself
                if artist.lower() in song_artist or artist.lower() in song_title:
                    lyrics_list = song.get("lyrics", [])
                    # Prioritize: 1. Japanese Original, 2. Japanese, 3. Any
                    jp_lyrics = next((l for l in lyrics_list if l.get("cultureCode") == "ja" and l.get("translationType") == "Original"), None)
                    if not jp_lyrics:
                        jp_lyrics = next((l for l in lyrics_list if l.get("cultureCode") == "ja"), None)
                    if not jp_lyrics and lyrics_list:
                        jp_lyrics = lyrics_list[0]
                    
                    if jp_lyrics:
                        return {
                            "title": song["name"],
                            "artist": song["artistString"],
                            "lyrics": jp_lyrics["value"],
                            "voca_id": song["id"]
                        }
        except Exception as e:
            print(f"    [ERROR] API Failure for {query}: {e}")
            
    return None

def main():
    if not MANIFEST_PATH.exists():
        print("Manifest not found.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    
    print(f"Phase 3: Definitive Acquisition of the Elite 150 Sniper Core...")

    for cluster_name, tracks in manifest.items():
        output_file = OUTPUT_DIR / f"{cluster_name}_definitive.jsonl"
        print(f" -> Mastering {cluster_name}...")
        
        bundle = []
        for track in tracks:
            print(f"    Searching for DEFINITIVE: {track['title']} by {track['artist']}...")
            elite = fetch_definitive_song(track["title"], track["artist"])
            
            if elite:
                # Apply High-Fidelity Refinement
                refined_lyrics = auto_section_lyrics(elite["title"], elite["lyrics"])
                profile = build_markdown_japanese_profile(elite["title"], refined_lyrics)
                
                record = {
                    "id": track["id"],
                    "artist": elite["artist"],
                    "title": elite["title"],
                    "lyrics": refined_lyrics,
                    "structural_profile": profile,
                    "voca_id": elite["voca_id"],
                    "status": "definitive_elite"
                }
                print(f"    [SUCCESS] Found definitive ID: {elite['voca_id']}")
            else:
                print(f"    [RETRY_PENDING] Still no definitive match for: {track['title']}")
                record = {
                    "id": track["id"],
                    "artist": track["artist"],
                    "title": track["title"],
                    "lyrics": "[Intro]\n(Electronic static)\n",
                    "status": "retry_required"
                }
            
            bundle.append(record)
            time.sleep(1.0) # Respect VocaDB API limits
            
        with output_file.open("w", encoding="utf-8") as f:
            for rec in bundle:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                
    print(f"\nDefinitive Synthesis Complete. Files saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

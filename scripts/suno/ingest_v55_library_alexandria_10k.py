import os
import sys
import json
import time
import requests
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# CONFIGURATION
BASE_URL = "https://vocadb.net/api/songs"
OUTPUT_DIR = Path("datasets/corpus")
OUTPUT_FILE = OUTPUT_DIR / "alexandria_10k_raw.jsonl"
STATE_FILE = OUTPUT_DIR / "alexandria_ingestion_state.json"
BATCH_SIZE = 50
TARGET_COUNT = 50000 # The "Library of Alexandria" Endless Mode expansion
RATE_LIMIT_DELAY = 0.5 # Slightly faster for high-volume ingest (VocaDB permits)

# SEARCH PARAMS (2000-2024 Full Digital Era)
SEARCH_PARAMS = {
    "publishDateAfter": "2000-01-01T00:00:00Z",
    "publishDateBefore": "2024-12-31T23:59:59Z",
    "fields": "Lyrics,MainPicture",
    "lang": "Japanese",
    "status": "Finished",
    "maxResults": BATCH_SIZE,
    "getTotalCount": "true",
    "sort": "FavoritedTimes" # Focus on high-quality/popular tracks first
}

def is_pure_japanese(text):
    if not text: return False
    # Check for Hiragana/Katakana/Kanji. Purge if it looks like translate/romaji only.
    import re
    jp_chars = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
    return len(jp_chars) > (len(text) * 0.2) # At least 20% Japanese characters

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    start_offset = 0
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            start_offset = state.get("offset", 0)
            print(f"Resuming Alexandria ingestion from offset: {start_offset}")
        except Exception: pass

    session = requests.Session()
    session.headers.update({"User-Agent": "AKIRA-ENGINE-ALEXANDRIA-BOT/1.0 (Research Project)"})

    print(f"Starting Library of Alexandria Ingestion (Target: {TARGET_COUNT} tracks)...")
    
    total_processed = 0
    current_offset = start_offset

    while total_processed < TARGET_COUNT:
        params = {**SEARCH_PARAMS, "start": current_offset}
        try:
            print(f" -> Fetching offset {current_offset}...")
            response = session.get(BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            if not items:
                print("No more items found. Ending crawl.")
                break
            
            valid_batch = []
            for item in items:
                lyrics_list = item.get("lyrics", [])
                # Prioritize Japanese lyrics
                jp_lyrics = next((l["value"] for l in lyrics_list if l.get("language") == "Japanese"), None)
                if not jp_lyrics and lyrics_list:
                    # Fallback: Check if the first lyric entry is actually Japanese
                    first_lyric = lyrics_list[0].get("value", "")
                    if is_pure_japanese(first_lyric):
                        jp_lyrics = first_lyric
                
                if jp_lyrics:
                    record = {
                        "id": item.get("id"),
                        "title": item.get("name"),
                        "artist": item.get("artistString"),
                        "publishDate": item.get("publishDate"),
                        "lyrics": jp_lyrics,
                        "ingested_on": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    valid_batch.append(record)
            
            # Save batch to JSONL
            with OUTPUT_FILE.open("a", encoding="utf-8") as f:
                for record in valid_batch:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            total_processed += len(valid_batch)
            current_offset += BATCH_SIZE
            
            # Save State
            STATE_FILE.write_text(json.dumps({"offset": current_offset, "total_processed": total_processed}), encoding="utf-8")
            
            print(f"    [OK] Processed {len(valid_batch)} valid Japanese tracks. Total Progress: {total_processed}/{TARGET_COUNT}")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"    [ERROR] {e}. Retrying in 10 seconds...")
            time.sleep(10)
            continue

    print(f"\nLibrary of Alexandria Batch Completed. Total Tracks: {total_processed}")

if __name__ == "__main__":
    main()

import os
import sys
import json
import time
import requests
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VOCADB_API = "https://vocadb.net/api/songs"
OUTPUT_DIR = Path("datasets/corpus")
OUTPUT_FILE = OUTPUT_DIR / "alexandria_10k_elite_push.jsonl"

def is_pure_japanese(text):
    if not text: return False
    import re
    jp_chars = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
    return len(jp_chars) > (len(text) * 0.2)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Target: 300 more to be safe
    TARGET = 300
    collected = 0
    offset = 0
    
    session = requests.Session()
    session.headers.update({"User-Agent": "AKIRA-ENGINE-FINAL-PUSH/1.0"})

    print(f"Starting Final Push: Collecting {TARGET} Elite Japanese tracks...")

    while collected < TARGET:
        params = {
            "publishDateAfter": "2010-01-01T00:00:00Z",
            "fields": "Lyrics",
            "lang": "Japanese",
            "status": "Finished",
            "maxResults": 50,
            "sort": "RatingScore",
            "start": offset
        }
        
        try:
            print(f" -> Querying offset {offset}...")
            r = session.get(VOCADB_API, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            
            if not items: break

            batch = []
            for item in items:
                lyrics_list = item.get("lyrics", [])
                jp_lyrics = next((l["value"] for l in lyrics_list if l.get("language") == "Japanese"), None)
                if not jp_lyrics and lyrics_list:
                    if is_pure_japanese(lyrics_list[0]["value"]):
                        jp_lyrics = lyrics_list[0]["value"]
                
                if jp_lyrics:
                    record = {
                        "id": item["id"],
                        "title": item["name"],
                        "artist": item["artistString"],
                        "lyrics": jp_lyrics,
                        "ingested_on": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    batch.append(record)
            
            if batch:
                with OUTPUT_FILE.open("a", encoding="utf-8") as f:
                    for rec in batch:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                collected += len(batch)
                print(f"    [OK] Captured {len(batch)} tracks. Total: {collected}/{TARGET}")
            
            offset += 50
            if offset > 2000: break # Safety break
            time.sleep(1.0)
            
        except Exception as e:
            print(f"    [ERR] {e}. Sleeping...")
            time.sleep(5)

    print(f"Final Push Complete. Collected {collected} tracks.")

if __name__ == "__main__":
    main()

import json
import requests
import sys
import os
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VOCADB_API = "https://vocadb.net/api/songs"

def fetch_definitive_song(title, artist):
    params = {
        "query": title,
        "maxResults": 3,
        "sort": "RatingScore",
        "fields": "Lyrics",
        "lang": "Japanese"
    }
    print(f" [DEBUG] Querying VocaDB for: {title} by {artist}...")
    try:
        r = requests.get(VOCADB_API, params=params, timeout=10)
        print(f" [DEBUG] Status Code: {r.status_code}")
        data = r.json()
        items = data.get("items", [])
        print(f" [DEBUG] Found {len(items)} results.")
        for song in items:
            print(f"  - Found: '{song.get('name')}' by '{song.get('artistString')}'")
            if artist.lower() in song.get("artistString", "").lower():
                lyrics_list = song.get("lyrics", [])
                if lyrics_list:
                    print(f"    [OK] Lyrics found!")
                    return True
    except Exception as e:
        print(f" [ERROR] API Failure: {e}")
    return False

if __name__ == "__main__":
    print("Definitive Acquisition Diagnosis...")
    # Test with a known hit
    fetch_definitive_song("Rolling Girl", "wowaka")

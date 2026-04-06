import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "baseline_registry.json"

def get_all_artists():
    """
    Shim to provide the artist list to the v3 scraper by reading the baseline registry.
    """
    if not REGISTRY_PATH.exists():
        print(f"[!] Registry not found at {REGISTRY_PATH}")
        return []
    
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        artists = []
        for entry in data.get("artists", []):
            # The baseline_registry uses 'artist_id' but nothing for name/name_jp.
            # We will use artist_id as the primary name for now.
            # In a full-scale scraper, we might want to map these to real names.
            artist_id = entry.get("artist_id")
            if artist_id:
                artists.append({
                    "name": artist_id,
                    "name_jp": "" # Optional, leaving blank for now
                })
        return artists
    except Exception as e:
        print(f"[!] Error loading registry: {e}")
        return []

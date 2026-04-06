import sys
from pathlib import Path

# Add the script folder to sys.path to allow 'from core.akira_artist_registry'
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from core.akira_artist_registry import get_all_artists
    artists = get_all_artists()
    print(f"[OK] Found {len(artists)} artists in the registry.")
    if artists:
        print(f"First 3: {[a['name'] for a in artists[:3]]}")
except Exception as e:
    print(f"[!] Registry import failed: {e}")
    sys.exit(1)

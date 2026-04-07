import json
from pathlib import Path

def list_missing():
    project_root = Path("C:/JPop_Songwriter/AKIRA ENGINE")
    map_path = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100/url_map_a100.json"
    records_dir = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100/records"
    
    if map_path.exists():
        with open(map_path, "r", encoding="utf-8") as f:
            url_map = json.load(f)
    else:
        url_map = {}
        
    missing = []
    for p in sorted(records_dir.glob("*.json")):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        tid = data["track_identity"]["track_id"]
        if tid not in url_map:
            title = data["track_identity"]["canonical_title"]
            producer = data.get("metadata_context", {}).get("producer", "unknown")
            missing.append(f"{tid}::{title}::{producer}")
            
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("\n".join(missing))

if __name__ == "__main__":
    list_missing()

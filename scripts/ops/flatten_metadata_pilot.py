import json
import shutil
from pathlib import Path

def flatten_metadata_pilot():
    project_root = Path("C:/JPop_Songwriter/AKIRA ENGINE")
    pilot_json = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100/lyric_technique_pilot_batch.json"
    canonical_root = project_root / "datasets/_global/vocaloid_metadata_canonical"
    target_accepted = project_root / "datasets/training/canonical_metadata_pilot/accepted"
    
    target_accepted.mkdir(parents=True, exist_ok=True)
    
    with pilot_json.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    selected = manifest.get("selected_tracks", [])
    copied = 0
    for item in selected:
        track_id = item.get("track_id")
        # Search in the expected bulk directory based on track_id suffix or just rglob
        # Since I know the bulk pattern, I can optimize, but rglob on the whole root is safer for 100 items.
        # Actually, let's use the bulk_* structure if possible.
        # Bulk folders are bulk_20260405_x_<N> where N is track_id // 100 or similar.
        # But rglob -filter is easy.
        matches = list(canonical_root.rglob(f"{track_id}.json"))
        if matches:
            shutil.copy2(matches[0], target_accepted / f"{track_id}.json")
            copied += 1
            
    print(f"Flattened {copied} canonical records to {target_accepted}")

if __name__ == "__main__":
    flatten_metadata_pilot()

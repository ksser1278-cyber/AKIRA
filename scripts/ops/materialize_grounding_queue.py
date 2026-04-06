import json
import shutil
from pathlib import Path

def materialize_a100():
    project_root = Path("C:/JPop_Songwriter/AKIRA ENGINE")
    pilot_json = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100/lyric_technique_pilot_batch.json"
    source_records = project_root / "datasets/training/lyric_technique_acquisition_queue/global_v1/records"
    target_queue = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100"
    target_records = target_queue / "records"
    
    target_records.mkdir(parents=True, exist_ok=True)
    
    with pilot_json.open("r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    selected = manifest.get("selected_tracks", [])
    copied = 0
    for item in selected:
        track_id = item.get("track_id")
        src = source_records / f"{track_id}.json"
        if src.exists():
            shutil.copy2(src, target_records / f"{track_id}.json")
            copied += 1
            
    print(f"Materialized {copied} records to {target_records}")

if __name__ == "__main__":
    materialize_a100()

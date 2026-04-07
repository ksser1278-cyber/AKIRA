import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path("C:/JPop_Songwriter/AKIRA ENGINE")
sys.path.insert(0, str(project_root))

from src.akira_engine.vocadb_lyric_grounding_auto import auto_ground_vocadb_workspace_from_url_map

def ground_pilot():
    workspace_root = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100"
    
    import json
    url_map_path = workspace_root / "url_map_a100.json"
    if url_map_path.exists():
        with open(url_map_path, "r", encoding="utf-8") as f:
            url_map = json.load(f)
    else:
        print("Warning: url_map_a100.json not found. Using defaults.")
        url_map = {}
    
    # Ensure records exist in 'incoming' for the auto_grounding script
    # The script looks into 'incoming' and moves to 'accepted'
    incoming_dir = workspace_root / "incoming"
    records_dir = workspace_root / "records"
    incoming_dir.mkdir(parents=True, exist_ok=True)
    
    for track_id in url_map.keys():
        src = records_dir / f"{track_id}.json"
        dest = incoming_dir / f"{track_id}.json"
        if src.exists() and not dest.exists():
            import shutil
            shutil.copy2(src, dest)
            print(f"Copied {track_id} to incoming.")

    print(f"Running auto-grounding for {len(url_map)} tracks...")
    manifest = auto_ground_vocadb_workspace_from_url_map(
        workspace_root=workspace_root,
        url_map=url_map
    )
    
    print(f"Grounding complete. Grounded: {manifest['counts']['grounded']}, Skipped: {manifest['counts']['skipped']}")
    if manifest['skipped']:
        for skip in manifest['skipped']:
            print(f"  - Skipped {skip['track_id']}: {skip['reason']}")

if __name__ == "__main__":
    ground_pilot()

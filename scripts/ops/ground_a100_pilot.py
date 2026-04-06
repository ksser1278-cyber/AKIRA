import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path("C:/JPop_Songwriter/AKIRA ENGINE")
sys.path.insert(0, str(project_root))

from src.akira_engine.vocadb_lyric_grounding_auto import auto_ground_vocadb_workspace_from_url_map

def ground_pilot():
    workspace_root = project_root / "datasets/training/lyric_technique_acquisition_queue/batch_a100"
    
    url_map = {
        "vocadb_5245": {
            "lyric_url": "https://utaten.com/lyric/nm14500147/",
            "site_preset": "utaten",
            "label": "UtaTen - ＊サヨナラ、ワールドエンド。",
            "notes": "sasakure.UK priority grounding."
        },
        "vocadb_4476": {
            "lyric_url": "https://utaten.com/lyric/jb11105021/",
            "site_preset": "utaten",
            "label": "UtaTen - ・・・ソバニ",
            "notes": "AVTechNO! priority grounding."
        },
        "vocadb_12954": {
            "lyric_url": "https://utaten.com/lyric/jb21010321/",
            "site_preset": "utaten",
            "label": "UtaTen - 「ぼく」自身のために",
            "notes": "fatmanP priority grounding."
        },
        "vocadb_1075": {
            "lyric_url": "https://utaten.com/lyric/jb11105020/",
            "site_preset": "utaten",
            "label": "UtaTen - 1000001Rooms",
            "notes": "AVTechNO! priority grounding."
        },
        "vocadb_1524": {
            "lyric_url": "https://utaten.com/lyric/jb11005085/",
            "site_preset": "utaten",
            "label": "UtaTen - 121",
            "notes": "AVTechNO! priority grounding."
        },
        "vocadb_1525": {
            "lyric_url": "https://utaten.com/lyric/jb11005083/",
            "site_preset": "utaten",
            "label": "UtaTen - 122",
            "notes": "AVTechNO! priority grounding."
        },
        "vocadb_1534": {
            "lyric_url": "https://utaten.com/lyric/jb11005084/",
            "site_preset": "utaten",
            "label": "UtaTen - 123",
            "notes": "AVTechNO! priority grounding."
        },
        "vocadb_1509": {
            "lyric_url": "https://utaten.com/lyric/jb11005082/",
            "site_preset": "utaten",
            "label": "UtaTen - 128",
            "notes": "AVTechNO! priority grounding."
        },
        "vocadb_1510": {
            "lyric_url": "https://utaten.com/lyric/jb11005081/",
            "site_preset": "utaten",
            "label": "UtaTen - 129",
            "notes": "AVTechNO! priority grounding."
        }
    }
    
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

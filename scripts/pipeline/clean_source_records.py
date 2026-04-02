import sys
from pathlib import Path

# Fix PYTHONPATH
PROJECT_ROOT = Path(r"C:\JPop_Songwriter\AKIRA ENGINE")
sys.path.append(str(PROJECT_ROOT / "src"))

from akira_engine.normalize.mod import run_normalize_stage

import json
import os
import shutil
from datetime import datetime

DATA_DIR = PROJECT_ROOT / "data"
TRASH_DIR = DATA_DIR / "_trash"
MANIFEST_PATH = DATA_DIR / "reference_tracks" / "cleanup_manifest.jsonl"

def extract_text_from_conditioning(data: dict) -> str:
    """Extract full lyric text from sections for normalization check."""
    sections = data.get("lyric_ground_truth", {}).get("sections", [])
    all_lines = []
    for s in sections:
        all_lines.extend(s.get("lines", []))
    return "\n".join(all_lines)

def run_cleanup():
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "reference_tracks").mkdir(parents=True, exist_ok=True)
    
    manifest_entries = []
    
    # 1. Find all conditioning records
    for artist_dir in DATA_DIR.iterdir():
        if not artist_dir.is_dir() or artist_dir.name.startswith(("_", ".")):
            continue
            
        ref_dir = artist_dir / "reference_tracks"
        if not ref_dir.exists():
            continue
            
        for record_path in ref_dir.glob("*.conditioning.json"):
            try:
                with open(record_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load {record_path}: {e}")
                continue
                
            track_id = data.get("track_identity", {}).get("track_id", record_path.stem)
            lyric_text = extract_text_from_conditioning(data)
            
            # 2. Run Normalize Stage
            norm_result = run_normalize_stage(track_id, lyric_text)
            
            # 3. Determine Verdict
            verdict = "Verified"
            reason = "Passes vNext quality gate"
            reprocessable = True
            
            if norm_result.has_bad_script:
                verdict = "Rejected"
                reason = f"Bad script detected: {', '.join(norm_result.errors)}"
                reprocessable = False
            elif norm_result.japanese_char_ratio < 0.6:
                verdict = "failed_source"
                reason = f"Japanese ratio too low: {norm_result.japanese_char_ratio}"
                reprocessable = True
            elif norm_result.latin_token_ratio > 0.4:
                verdict = "failed_source"
                reason = f"Latin leakage too high: {norm_result.latin_token_ratio}"
                reprocessable = True
                
            # 4. Log Entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "track_id": track_id,
                "original_path": str(record_path.relative_to(PROJECT_ROOT)),
                "verdict": verdict,
                "reason": reason,
                "reprocessable": reprocessable,
                "metrics": {
                    "jp_ratio": norm_result.japanese_char_ratio,
                    "latin_ratio": norm_result.latin_token_ratio,
                    "has_bad_script": norm_result.has_bad_script
                }
            }
            manifest_entries.append(log_entry)
            
            # 5. Execute Relocation
            if verdict != "Verified":
                target_base = TRASH_DIR / f"{verdict}_sources"
                relative_dir = record_path.parent.relative_to(DATA_DIR)
                target_dir = target_base / relative_dir
                target_dir.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(record_path), str(target_dir / record_path.name))
                print(f"[{verdict}] {track_id} -> {reason}")
            else:
                print(f"[OK] {track_id}")

    # 6. Write Manifest
    with open(MANIFEST_PATH, "a", encoding="utf-8") as f:
        for entry in manifest_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
    print(f"\nCleanup complete. Manifest written to {MANIFEST_PATH}")

if __name__ == "__main__":
    run_cleanup()

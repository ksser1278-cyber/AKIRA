import json
import os
from pathlib import Path
from typing import Any
from src.akira_engine.normalize.mod import run_normalize_stage
from src.akira_engine.features.mod import run_features_stage
from src.akira_engine.conditioning.mod import run_conditioning_stage
from src.akira_engine.lyric_utils import safe_text

def load_alexandria_targets(project_root: Path, limit: int = 200) -> list[dict[str, Any]]:
    targets = []
    manifest_path = project_root / "data" / "reference_tracks" / "cleanup_manifest.jsonl"
    
    # 1. Load from cleanup manifest
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                targets.append(json.loads(line))
    
    # 2. Fill up to limit from across data/ folders if needed
    if len(targets) < limit:
        data_dir = project_root / "data"
        for artist_dir in data_dir.iterdir():
            if not artist_dir.is_dir() or artist_dir.name.startswith("_"): continue
            ref_dir = artist_dir / "reference_tracks"
            if not ref_dir.exists(): continue
            
            for cond_file in ref_dir.glob("*.conditioning.json"):
                track_id = f"{artist_dir.name}_{cond_file.stem}"
                # Skip if already in targets
                if any(t["track_id"] == track_id for t in targets): continue
                
                targets.append({
                    "track_id": track_id,
                    "original_path": str(cond_file.relative_to(project_root))
                })
                if len(targets) >= limit: break
            if len(targets) >= limit: break
            
    return targets[:limit]

def run_sweep():
    project_root = Path(".")
    targets = load_alexandria_targets(project_root, 200)
    print(f"Loaded {len(targets)} targets for calibration sweep.")
    
    manifest_out = project_root / "outputs" / "quality_manifest.jsonl"
    os.makedirs(manifest_out.parent, exist_ok=True)
    
    results = []
    
    for i, target in enumerate(targets):
        track_id = target["track_id"]
        rel_path = target["original_path"]
        abs_path = project_root / rel_path
        
        print(f"[{i+1}/200] Processing {track_id}...")
        
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            # vNext logic usually expects a raw lyric or simple conditioning
            lyric_text = raw_data.get("lyric_ground_truth", {}).get("full_text", "")
            if not lyric_text:
                # Fallback to lines if present
                sections = raw_data.get("lyric_ground_truth", {}).get("sections", [])
                full_lines = []
                for s in sections:
                    full_lines.extend(s.get("lines", []))
                lyric_text = "\n".join(full_lines)
            
            if not lyric_text:
                raise ValueError("No lyric text found in source")
            
            # Stage B: Normalize
            norm = run_normalize_stage(track_id, lyric_text)
            
            # Stage C: Features
            feat = run_features_stage(track_id, norm.normalized_text)
            
            # Stage D: Conditioning
            # Mock artist/intent for sweep
            artist_id = track_id.split("_")[0]
            artist_profile = {"artist_name": artist_id}
            song_intent = {"core_theme": ["calibration"]}
            
            cond = run_conditioning_stage(
                artist_id=artist_id,
                track_id=track_id,
                normalized_lyric_text=norm.normalized_text,
                artist_profile=artist_profile,
                song_intent=song_intent,
                features=feat,
                normalization_result=norm
            )
            
            # Construct Calibration Record
            record = {
                "track_id": track_id,
                "grade": cond.source_grade,
                "japanese_char_ratio": norm.japanese_char_ratio,
                "latin_token_ratio": norm.latin_token_ratio,
                "bad_script": norm.has_bad_script,
                "decision_reason": f"Audit: {cond.audit_status}, Grade: {cond.source_grade}",
                "reprocessable": cond.source_grade in ["gold", "silver", "failed_source"]
            }
            results.append(record)
            
        except Exception as e:
            print(f"Error processing {track_id}: {e}")
            results.append({
                "track_id": track_id,
                "grade": "rejected",
                "decision_reason": f"Exception: {str(e)}",
                "reprocessable": False
            })

    # Save manifest
    with open(manifest_out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"\nSweep complete! Manifest saved to {manifest_out}")

if __name__ == "__main__":
    run_sweep()

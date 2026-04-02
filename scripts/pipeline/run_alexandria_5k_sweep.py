import json
import os
from pathlib import Path
from typing import Any
from src.akira_engine.normalize.mod import run_normalize_stage
from src.akira_engine.features.mod import run_features_stage
from src.akira_engine.conditioning.mod import run_conditioning_stage

def collect_alexandria_5k_targets(project_root: Path) -> list[dict[str, Any]]:
    targets = []
    corpus_dir = project_root / "lyrics" / "corpus"
    if not corpus_dir.exists():
        return []
    
    for artist_dir in corpus_dir.iterdir():
        if not artist_dir.is_dir(): continue
        artist_id = artist_dir.name
        
        for lyric_file in artist_dir.glob("*.txt"):
            track_id = f"{artist_id}_{lyric_file.stem}"
            targets.append({
                "track_id": track_id,
                "artist_id": artist_id,
                "path": lyric_file
            })
    return targets

def run_5k_sweep():
    project_root = Path(".")
    targets = collect_alexandria_5k_targets(project_root)
    print(f"Loaded {len(targets)} targets from Alexandria corpus.")
    
    manifest_out = project_root / "outputs" / "alexandria_quality_manifest.jsonl"
    atlas_out = project_root / "outputs" / "atlas_v2_trusted.json"
    os.makedirs(manifest_out.parent, exist_ok=True)
    
    results = []
    atlas_atoms = {"body": [], "scene": [], "sound": [], "motifs": []}
    
    batch_size = 100
    for i, target in enumerate(targets):
        track_id = target["track_id"]
        artist_id = target["artist_id"]
        lyric_path = target["path"]
        
        if (i+1) % batch_size == 0 or i == 0:
            print(f"[{i+1}/{len(targets)}] Processing {track_id}...")
            
        try:
            with open(lyric_path, "r", encoding="utf-8") as f:
                lyric_text = f.read()
            
            if not lyric_text or len(lyric_text.strip()) < 10:
                continue
                
            # Stage B: Normalize
            norm = run_normalize_stage(track_id, lyric_text)
            
            # Stage C: Features
            feat = run_features_stage(track_id, norm.normalized_text)
            
            # Stage D: Conditioning
            cond = run_conditioning_stage(
                artist_id=artist_id,
                track_id=track_id,
                normalized_lyric_text=norm.normalized_text,
                artist_profile={"artist_name": artist_id},
                song_intent={"core_theme": ["alexandria_5k"]},
                features=feat,
                normalization_result=norm
            )
            
            record = {
                "track_id": track_id,
                "grade": cond.source_grade,
                "metrics": {
                    "jp_ratio": norm.japanese_char_ratio,
                    "latin_ratio": norm.latin_token_ratio,
                    "bad_script": norm.has_bad_script
                },
                "audit": cond.audit_status
            }
            results.append(record)
            
            # Aggregate Atlas Atoms (Only Gold/Silver)
            if cond.source_grade in ["gold", "silver"] and feat:
                atlas_atoms["body"].extend(feat.body_atoms)
                atlas_atoms["scene"].extend(feat.scene_atoms)
                atlas_atoms["sound"].extend(feat.sound_atoms)
                atlas_atoms["motifs"].extend(feat.motif_atoms)
                
        except Exception as e:
            results.append({"track_id": track_id, "grade": "rejected", "error": str(e)})

    # Final Summarization
    with open(manifest_out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    # Trusted Atlas Save
    final_atlas = {k: list(sorted(set(v))) for k, v in atlas_atoms.items()}
    with open(atlas_out, "w", encoding="utf-8") as f:
        json.dump(final_atlas, f, indent=2, ensure_ascii=False)
        
    print(f"\n5k Expansion Complete!")
    print(f"Processed: {len(results)} tracks")
    print(f"Atlas v2 Trusted Stats: {len(final_atlas['body'])} body, {len(final_atlas['scene'])} scene, {len(final_atlas['sound'])} sound atoms.")

if __name__ == "__main__":
    run_5k_sweep()

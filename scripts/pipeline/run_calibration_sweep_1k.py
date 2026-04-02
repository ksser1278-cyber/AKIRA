import json
import os
from pathlib import Path
from typing import Any
from src.akira_engine.normalize.mod import run_normalize_stage
from src.akira_engine.features.mod import run_features_stage
from src.akira_engine.conditioning.mod import run_conditioning_stage
from src.akira_engine.lyric_utils import safe_text

def collect_tracks(project_root: Path, limit: int = 1000) -> list[dict[str, Any]]:
    targets = []
    seen_ids = set()

    # 1. Cleanup Manifest (Trusted list)
    manifest_path = project_root / "data" / "reference_tracks" / "cleanup_manifest.jsonl"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                track_id = data["track_id"]
                if track_id not in seen_ids:
                    targets.append({
                        "track_id": track_id,
                        "original_path": data["original_path"],
                        "artist_id": track_id.split("_")[0]
                    })
                    seen_ids.add(track_id)

    # 2. Artist subdirectories (All conditioning/md/txt)
    data_dir = project_root / "data"
    for artist_dir in data_dir.iterdir():
        if not artist_dir.is_dir() or artist_dir.name.startswith("_"): continue
        artist_id = artist_dir.name
        
        # Search recursion for all potential lyric sources
        for ext in ["*.conditioning.json", "*.md", "*.txt"]:
            for f in artist_dir.rglob(ext):
                # Unique ID calculation
                rel_path = f.relative_to(project_root)
                track_id = f"{artist_id}_{f.stem}"
                
                if track_id not in seen_ids:
                    targets.append({
                        "track_id": track_id,
                        "original_path": str(rel_path),
                        "artist_id": artist_id
                    })
                    seen_ids.add(track_id)
                
                if len(targets) >= limit: break
            if len(targets) >= limit: break
        if len(targets) >= limit: break
            
    return targets

def run_sweep_1k():
    project_root = Path(".")
    targets = collect_tracks(project_root, 1000)
    print(f"Loaded {len(targets)} targets for Alexandria 1k sweep.")
    
    output_manifest = project_root / "outputs" / "quality_manifest_1k.jsonl"
    atlas_candidate_out = project_root / "outputs" / "atlas_v2_candidate.json"
    os.makedirs(output_manifest.parent, exist_ok=True)
    
    results = []
    atlas_atoms = {"body": [], "scene": [], "sound": [], "motifs": []}
    
    for i, target in enumerate(targets):
        track_id = target["track_id"]
        rel_path = target["original_path"]
        abs_path = project_root / rel_path
        artist_id = target["artist_id"]
        
        if (i+1) % 50 == 0 or i == 0:
            print(f"[{i+1}/{len(targets)}] Processing {track_id}...")
            
        try:
            # Source extraction
            lyric_text = ""
            if abs_path.suffix == ".json":
                with open(abs_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    lyric_text = raw.get("lyric_ground_truth", {}).get("full_text", "")
                    if not lyric_text:
                        sections = raw.get("lyric_ground_truth", {}).get("sections", [])
                        lyric_text = "\n".join(["\n".join(s.get("lines", [])) for s in sections])
            else:
                with open(abs_path, "r", encoding="utf-8") as f:
                    lyric_text = f.read()
            
            if not lyric_text or len(lyric_text.strip()) < 10:
                continue

            # Stage B: Normalize
            norm = run_normalize_stage(track_id, lyric_text)
            
            # Stage C: Features
            feat = run_features_stage(track_id, norm.normalized_text)
            
            # Stage D: Conditioning
            artist_profile = {"artist_name": artist_id}
            song_intent = {"core_theme": ["expansion_1k"]}
            
            cond = run_conditioning_stage(
                artist_id=artist_id,
                track_id=track_id,
                normalized_lyric_text=norm.normalized_text,
                artist_profile=artist_profile,
                song_intent=song_intent,
                features=feat,
                normalization_result=norm
            )
            
            # Result Record
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
            
            # Atlas Candidate Extraction (Only from Gold/Silver)
            if cond.source_grade in ["gold", "silver"] and feat:
                atlas_atoms["body"].extend(feat.body_atoms)
                atlas_atoms["scene"].extend(feat.scene_atoms)
                atlas_atoms["sound"].extend(feat.sound_atoms)
                atlas_atoms["motifs"].extend(feat.motif_atoms)
                
        except Exception as e:
            results.append({
                "track_id": track_id,
                "grade": "rejected",
                "decision_reason": str(e),
                "reprocessable": False
            })

    # Save outputs
    with open(output_manifest, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    # Cleanup Atlas atoms (unique)
    final_atlas = {k: list(set(v)) for k, v in atlas_atoms.items()}
    with open(atlas_candidate_out, "w", encoding="utf-8") as f:
        json.dump(final_atlas, f, indent=2, ensure_ascii=False)
        
    print(f"\n1k Sweep complete! Manifest: {output_manifest}, Atlas: {atlas_candidate_out}")
    print(f"Stats: {len(results)} processed, {len(final_atlas['body'])} body atoms, {len(final_atlas['scene'])} scene atoms extracted.")

if __name__ == "__main__":
    run_sweep_1k()

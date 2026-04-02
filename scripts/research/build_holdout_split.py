# scripts/research/build_holdout_split.py

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from collections import defaultdict


def build_holdout_split(project_root: Path, holdout_ratio: float = 0.2):
    """Performs a stratified split of the corpus into Training and Holdout sets.
    
    Stratification criteria:
    - Artist (from folder name)
    - Cluster (from style_clusters_v1.json)
    - Grade (from novelty_index_v1.json)
    """
    data_dir = project_root / "data"
    eval_dir = project_root / "data" / "eval"
    holdout_dir = eval_dir / "holdout_external"
    
    holdout_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / "holdout_internal").mkdir(parents=True, exist_ok=True)
    (eval_dir / "regression_prompts").mkdir(parents=True, exist_ok=True)

    # 1. Load metadata for stratification
    cluster_idx = {}
    cluster_path = data_dir / "clusters" / "style_clusters_v1.json"
    if cluster_path.exists():
        with open(cluster_path, "r", encoding="utf-8") as f:
            c_data = json.load(f)
            for c in c_data.get("clusters", []):
                for tid in c.get("member_track_ids", []):
                    cluster_idx[tid] = c["cluster_id"]

    novelty_idx = {}
    novelty_path = data_dir / "novelty" / "novelty_index_v1.json"
    if novelty_path.exists():
        with open(novelty_path, "r", encoding="utf-8") as f:
            n_data = json.load(f)
            for p in n_data.get("profiles", []):
                score = p.get("composite_score", 0.0)
                grade = "high" if score > 80 else "mid" if score > 70 else "low"
                novelty_idx[p["track_id"]] = grade

    # 2. Collect all tracks
    all_tracks = []
    # Artist folders are a-z, skip internal/eval/trash
    skip_dirs = {"eval", "_trash", "_global", "anchor_sets", "audio", "canon_tracks", "clusters", "features", "generated_suno", "generated_tracks", "hooks", "mastery", "motifs", "novelty", "reference_tracks", "rules"}
    
    for artist_dir in data_dir.iterdir():
        if not artist_dir.is_dir() or artist_dir.name in skip_dirs or artist_dir.name.startswith("."):
            continue
            
        for track_file in artist_dir.glob("*.json"):
            tid = f"{artist_dir.name}/{track_file.stem}"
            all_tracks.append({
                "tid": tid,
                "path": track_file,
                "artist": artist_dir.name,
                "cluster": cluster_idx.get(tid, "unknown"),
                "grade": novelty_idx.get(tid, "low")
            })

    # 3. Group for stratification
    groups = defaultdict(list)
    for t in all_tracks:
        # Stratum = (Artist, Cluster, Grade)
        stratum = (t["artist"], t["cluster"], t["grade"])
        groups[stratum].append(t)

    # 4. Sample holdout
    holdout_set = []
    for stratum, members in groups.items():
        count = max(1, int(len(members) * holdout_ratio))
        samples = random.sample(members, min(count, len(members)))
        holdout_set.extend(samples)

    print(f"Total tracks found: {len(all_tracks)}")
    print(f"Moving {len(holdout_set)} tracks to holdout (ratio={holdout_ratio:.2f})")

    # 5. Execute move
    for t in holdout_set:
        dest_artist_dir = holdout_dir / t["artist"]
        dest_artist_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(t["path"]), str(dest_artist_dir / t["path"].name))
        print(f" [HOLDOUT] {t['tid']}")

    print("\nHoldout split complete.")
    print(f"Training set size: {len(all_tracks) - len(holdout_set)}")
    print(f"Holdout set size: {len(holdout_set)}")


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    build_holdout_split(PROJECT_ROOT)

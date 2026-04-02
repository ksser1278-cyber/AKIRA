import subprocess
import json
import os
from pathlib import Path
import time
import shutil

# --- CONFIGURATION (THE ELITE 100 MIX) ---
SLOTS = [
    {"artist": "pinocchiop", "count": 20},
    {"artist": "kanaria", "count": 15},
    {"artist": "maretu", "count": 15},
    {"artist": "hachi", "count": 15},
    {"artist": "ado", "count": 15},
    {"artist": "deco27", "count": 10},
    {"artist": "kairiki_bear", "count": 10}
]

CANDIDATE_COUNT = 5 # Production grade selectivity
OUTPUT_BASE = Path("bundles/elite_100")

def run_slot(artist_id, slot_index):
    slot_id = f"{artist_id}_{slot_index:03d}"
    slot_dir = OUTPUT_BASE / slot_id
    slot_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "python", "scripts/songwriter/run_demo_songwriter.py",
        "--artist-id", artist_id,
        "--candidate-count", str(CANDIDATE_COUNT),
        "--output-dir", str(slot_dir)
    ]
    
    print(f"[SLOT {slot_id}] Synthesis starting (5 candidates)...")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    duration = time.time() - start_time
    
    if result.returncode != 0:
        print(f"  [FAIL] {slot_id}: {result.stderr[:200]}")
        return None
    
    manifest_path = slot_dir / "run_manifest.json"
    if not manifest_path.exists():
         # Check subdirs (sometimes the script nests)
         subdirs = [d for d in slot_dir.iterdir() if d.is_dir()]
         for sd in subdirs:
             if (sd / "run_manifest.json").exists():
                 manifest_path = sd / "run_manifest.json"
                 break

    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
            # Weighted Promotion Logic (Selection Committee)
            critic_results = manifest.get("critic_results", [])
            selected_id = manifest.get("selected_candidate_id")
            selected_result = next((r for r in critic_results if r.get("candidate_id") == selected_id), {})
            
            scores = selected_result.get("scores", {})
            total_score = scores.get("total", 0.0)
            grounding_score = scores.get("imagery_specificity_score", 0.0)
            jp_score = scores.get("surface_score", 0.0)
            
            # Final Rank = Total + Grounding Lift + JP Fidelity
            rank_score = total_score + (grounding_score * 0.5) + (jp_score * 0.2)
            
            return {
                "slot_id": slot_id,
                "artist": artist_id,
                "track_id": manifest.get("track_id"),
                "rank_score": round(rank_score, 2),
                "critic_total": total_score,
                "grounding": grounding_score,
                "duration": round(duration, 2),
                "path": str(slot_dir)
            }
    return None

def main():
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    all_slots = []
    
    print("=== AKIRA ENGINE: Elite 100 Production Bundle ===")
    print(f"Mode: Selection Committee (Candidates: {CANDIDATE_COUNT})")
    
    start_total = time.time()
    
    for entry in SLOTS:
        artist = entry["artist"]
        count = entry["count"]
        for i in range(count):
            res = run_slot(artist, i + 1)
            if res:
                all_slots.append(res)
                print(f"  [OK] Ranked {res['rank_score']} (Grd: {res['grounding']})")
    
    # Sort by rank and artist
    all_slots.sort(key=lambda x: x["rank_score"], reverse=True)
    
    summary = {
        "production_run": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_bundle_size": len(all_slots),
        "avg_rank_score": sum(s["rank_score"] for s in all_slots) / len(all_slots) if all_slots else 0,
        "avg_grounding": sum(s["grounding"] for s in all_slots) / len(all_slots) if all_slots else 0,
        "total_duration_hours": (time.time() - start_total) / 3600,
        "slots": all_slots
    }
    
    with open(OUTPUT_BASE / "elite_100_manifest.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\nElite 100 Production Complete. Bundle saved to {OUTPUT_BASE}")

if __name__ == "__main__":
    main()

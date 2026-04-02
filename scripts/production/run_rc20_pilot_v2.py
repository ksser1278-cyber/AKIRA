import subprocess
import json
import os
from pathlib import Path
import time
import random
import hashlib

def run_production_test(artist_id, track_index):
    project_root = Path.cwd()
    output_dir = project_root / "outputs" / "pilot_rc20_v2" / f"{artist_id}_{track_index}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "python", "scripts/songwriter/run_demo_songwriter.py",
        "--artist-id", artist_id,
        "--candidate-count", "3",
        "--output-dir", str(output_dir)
    ]
    
    print(f"[{artist_id} #{track_index}] Running: {' '.join(cmd)}")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    duration = time.time() - start_time
    
    if result.returncode != 0:
        print(f"  [ERROR] {artist_id}: {result.stderr}")
        return {"ok": False, "error": result.stderr}
    
    # Locate manifest
    manifest_path = output_dir / "run_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
            # Extract imagery coverage from latest critic result
            critic_results = manifest.get("critic_results", [])
            selected_id = manifest.get("selected_candidate_id")
            selected_result = next((r for r in critic_results if r.get("candidate_id") == selected_id), {})
            
            imagery_coverage = selected_result.get("scores", {}).get("imagery_specificity_score", 0.0)
            
            return {
                "ok": True,
                "artist": artist_id,
                "track_id": manifest.get("track_id"),
                "score": manifest.get("selected_score"),
                "imagery_coverage": imagery_coverage,
                "duration": duration,
                "manifest_path": str(manifest_path)
            }
    return {"ok": False, "error": "Manifest not found"}

def main():
    # 20-track verification batch (RC-20)
    artists = {
        "pinocchiop": 5,
        "kanaria": 5,
        "maretu": 5,
        "hachi": 2,
        "ado": 3
    }
    
    results = []
    total_start = time.time()
    
    print("=== RC-20 Pilot v2: Grounding Bridge Verification ===")
    print("Target: imagery_coverage > 0.0 (Grounded in 12k Atlas v2)")
    
    for artist, count in artists.items():
        for i in range(count):
            res = run_production_test(artist, i + 1)
            results.append(res)
            
    # Report
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_runs": len(results),
        "success_runs": len([r for r in results if r["ok"]]),
        "avg_score": sum([r["score"] for r in results if r["ok"]]) / len([r for r in results if r["ok"]]) if any(r["ok"] for r in results) else 0,
        "avg_imagery_coverage": sum([r["imagery_coverage"] for r in results if r["ok"]]) / len([r for r in results if r["ok"]]) if any(r["ok"] for r in results) else 0
    }
    
    report = {"summary": summary, "details": results}
    with open("outputs/pilot_rc20_v2_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*50)
    print(f"RC-20 v2 Verification Complete.")
    print(f"Avg Score: {summary['avg_score']:.2f}")
    print(f"Avg Imagery Coverage: {summary['avg_imagery_coverage']:.2f}")
    print("="*50)

if __name__ == "__main__":
    main()

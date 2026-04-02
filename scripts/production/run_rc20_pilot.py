import subprocess
import json
import os
from pathlib import Path
import time

def run_production_test(artist_id, track_index):
    project_root = Path.cwd()
    output_dir = project_root / "outputs" / "pilot_rc20" / f"{artist_id}_{track_index}"
    
    cmd = [
        "python", "scripts/songwriter/run_demo_songwriter.py",
        "--artist-id", artist_id,
        "--candidate-count", "3", # Higher count for pilot
        "--output-dir", str(output_dir)
    ]
    
    print(f"[{artist_id} #{track_index}] Running: {' '.join(cmd)}")
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode != 0:
        print(f"  [ERROR] {artist_id}: {result.stderr}")
        return {"ok": False, "error": result.stderr}
    
    # Extract manifest path from output
    manifest_path = None
    for line in result.stdout.splitlines():
        if "Demo run manifest:" in line:
            manifest_path = Path(line.split(":", 1)[1].strip())
            break
            
    if manifest_path and manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            return {
                "ok": True,
                "artist": artist_id,
                "track_id": manifest.get("track_id"),
                "score": manifest.get("selected_score"),
                "honest_metrics": manifest.get("honest_metrics"),
                "pre_audit": manifest.get("pre_audit"),
                "duration": duration,
                "manifest_path": str(manifest_path)
            }
    return {"ok": False, "error": "Manifest not found"}

def main():
    # RC-20 Artist Distribution
    artists = {
        "pinocchiop": 5,
        "kanaria": 5,
        "maretu": 5,
        "hachi": 2,
        "ado": 3
    }
    
    results = []
    total_start = time.time()
    
    for artist, count in artists.items():
        print(f"=== Starting Pilot Axis: {artist} ({count} tracks) ===")
        for i in range(count):
            res = run_production_test(artist, i + 1)
            results.append(res)
            
    # Save final pilot report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_duration": time.time() - total_start,
        "summary": {
            "total_runs": len(results),
            "success_runs": len([r for r in results if r["ok"]]),
            "avg_score": sum([r["score"] for r in results if r["ok"]]) / len([r for r in results if r["ok"]]) if any(r["ok"] for r in results) else 0
        },
        "details": results
    }
    
    summary_path = Path("outputs/pilot_rc20_report.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"\nRC-20 Pilot Complete. Report saved to {summary_path}")

if __name__ == "__main__":
    main()

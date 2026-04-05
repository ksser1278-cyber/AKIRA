import subprocess
import json
import os
from pathlib import Path

def run_test(artist_id):
    cmd = [
        "python", "scripts/songwriter/run_demo_songwriter.py",
        "--artist-id", artist_id,
        "--candidate-count", "1"
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {artist_id}: {result.stderr}")
        return None
    
    # Extract manifest path from output
    for line in result.stdout.splitlines():
        if "Demo run manifest:" in line:
            return Path(line.split(":", 1)[1].strip())
    return None

def main():
    artists = ["pinocchiop", "kanaria", "maretu"]
    iterations = 5
    results = []

    for artist in artists:
        print(f"=== Testing Artist: {artist} ===")
        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}...")
            manifest_path = run_test(artist)
            if manifest_path and manifest_path.exists():
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    results.append({
                        "artist": artist,
                        "iteration": i + 1,
                        "score": manifest.get("selected_score"),
                        "pre_audit": manifest.get("pre_audit"),
                        "honest_metrics": manifest.get("honest_metrics"),
                        "critic_notes": manifest.get("critic_results", [{}])[0].get("critic_notes", [])
                    })
            else:
                print(f"Failed to get manifest for {artist} iteration {i+1}")

    # Save summary
    summary_path = Path("outputs/phase_2_smoke_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Summary saved to {summary_path}")

if __name__ == "__main__":
    main()

import json
from pathlib import Path
import random
import sys

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REFINED_PATH = Path("datasets/corpus/alexandria_10k_refined.jsonl")
OUTPUT_DIR = Path("datasets/analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calibrate():
    print(f"Loading refined corpus from {REFINED_PATH}...")
    
    modern_tracks = [] # 2020+
    historical_tracks = [] # < 2020
    
    with REFINED_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                track = json.loads(line)
                # Parse date
                pub_date = track.get("publishDate", "")
                if not pub_date:
                    # Some might not have it if they came from elite_push, 
                    # but refined should have it from raw.
                    historical_tracks.append(track)
                    continue
                
                year = int(pub_date.split("-")[0])
                if year >= 2020:
                    modern_tracks.append(track)
                else:
                    historical_tracks.append(track)
            except Exception:
                continue

    print(f"Found {len(modern_tracks)} modern tracks and {len(historical_tracks)} historical tracks.")

    if len(modern_tracks) < 1500:
        print("Warning: Not enough modern tracks for a robust 500/500/500 split. Adjusting...")
    
    # Modern is already sorted by 'FavoritedTimes' if refined preserved raw order
    # Elite: First 500 (High-Lift)
    elite = modern_tracks[:500]
    
    # Mid: Middle 500
    mid_idx = len(modern_tracks) // 2
    mid = modern_tracks[mid_idx - 250 : mid_idx + 250]
    
    # Control (Low Modern): Last 500
    low_modern = modern_tracks[-500:]
    
    # Control (Historical): Random 500
    hist_sample = random.sample(historical_tracks, min(500, len(historical_tracks)))
    
    control = low_modern + hist_sample

    # Save Cohorts
    save_jsonl(elite, OUTPUT_DIR / "cohort_elite.jsonl")
    save_jsonl(mid, OUTPUT_DIR / "cohort_mid.jsonl")
    save_jsonl(control, OUTPUT_DIR / "cohort_control.jsonl")
    
    print("\nCalibration Complete:")
    print(f" - Elite: {len(elite)} tracks (Modern Top)")
    print(f" - Mid: {len(mid)} tracks (Modern Mid)")
    print(f" - Control: {len(control)} tracks (Modern Low + Historical Sample)")

def save_jsonl(data, path):
    with path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    calibrate()

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

# Force UTF-8 for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# CONFIGURATION
INPUT_REFINED = Path("datasets/corpus/alexandria_10k_refined.jsonl")
OUTPUT_INDEX = Path("data/_global/styles/alexandria_style_index.json")

def categorize_track(record):
    """
    Categorizes a track into Model A, B, or C based on structural features.
    """
    profile = record.get("structural_profile", {})
    if not profile:
        return "Uncategorized"
    
    mora_bias = profile.get("modern_compression_bias", "low")
    speed_bias = profile.get("workflow_bias", "unknown")
    
    # Heuristics for the 3 Sniper Models
    if mora_bias == "high" or any(f["spoken_speed_bias"] == "high" for f in profile.get("section_features", [])):
        return "Model_A_Staccato_Speed"
    
    if any(f["jp_section_role"] in ["sabi", "dai_sabi"] for f in profile.get("section_features", [])):
        # If it has a clear melodic release and balanced density, it's likely Pop
        if mora_bias in ["medium", "low"]:
            return "Model_B_Humanoid_Pop"
            
    # Default to Model C for more rhythmic/unknown structural variants
    return "Model_C_Bass_Glitch"

def main():
    if not INPUT_REFINED.exists():
        print(f"Refined file {INPUT_REFINED} not found.")
        return

    print(f"Starting Alexandria Style Indexing (Phase 3)...")
    
    clusters = defaultdict(list)
    total_count = 0
    
    with INPUT_REFINED.open("r", encoding="utf-8") as f:
        for line in f:
            total_count += 1
            try:
                record = json.loads(line)
                category = categorize_track(record)
                
                # Store simplified reference
                clusters[category].append({
                    "id": record.get("id"),
                    "title": record.get("title"),
                    "artist": record.get("artist"),
                    "tags": record.get("structural_profile", {}).get("critic_focus", [])
                })
                
            except Exception as e:
                print(f"    [SKIP] Error indexing record: {e}")

    # Finalize index
    index_data = {
        "metadata": {
            "total_indexed": total_count,
            "generated_on": "2026-03-30",
            "clusters": list(clusters.keys())
        },
        "clusters": dict(clusters)
    }

    OUTPUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_INDEX.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nIndexing Completed.")
    for cat, items in clusters.items():
        print(f"  - {cat}: {len(items)} tracks")

if __name__ == "__main__":
    main()

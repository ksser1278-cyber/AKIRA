import json
import random
import os
import sys
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

STYLE_INDEX_PATH = Path("data/_global/styles/alexandria_style_index.json")
PROBE_OUTPUT_DIR = Path("outputs/probes/masterpiece_simulations")

def generate_masterpiece_draft(cluster_name, cluster_data):
    """
    Synthesizes a 'Masterpiece' draft based on the Cluster's DNA.
    """
    # Simply pick 3 top tracks for inspiration in this simulation
    inspiration = random.sample(cluster_data, min(len(cluster_data), 5))
    titles = [t["title"] for t in inspiration]
    
    # Simple Template for Simulation
    draft = f"""# [MASTERPIECE PROBE] {cluster_name}
# Inspired by: {', '.join(titles)}

[Intro]
(Sonic texture aligned with {cluster_name})

[Verse 1]
(Lyrics synthesized from 60,000+ tracks of stylistic DNA)
...

[Chorus]
(Maximum mora density and emotional hook power)
...
"""
    return draft

def main():
    if not STYLE_INDEX_PATH.exists():
        print("Style Index not found.")
        return

    PROBE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with STYLE_INDEX_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    print("Stage 6: Masterpiece Probes (Generative Simulation)...")
    
    for cluster_name, cluster_tracks in data.get("clusters", {}).items():
        print(f" -> Synthesizing for {cluster_name}...")
        draft = generate_masterpiece_draft(cluster_name, cluster_tracks)
        
        output_file = PROBE_OUTPUT_DIR / f"{cluster_name}_probe_v1.md"
        output_file.write_text(draft, encoding="utf-8")
        
    print(f"Probes completed. Check {PROBE_OUTPUT_DIR}")

if __name__ == "__main__":
    main()

import json
import os
import sys
import re
from pathlib import Path
from statistics import mean, stdev

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REFINE_PATH = Path("datasets/corpus/alexandria_10k_refined.jsonl")
STYLE_INDEX_PATH = Path("data/_global/styles/alexandria_style_index.json")

def analyze_structural_dna(records):
    """
    Extracts statistical models for J-Pop structures.
    e.g., 'In Fast Pop, Verse is usually 8.5 mora/line, Chorus is 11.2'.
    """
    stats = {
        "mora_density_map": {}, # section -> avg_mora
        "section_length_map": {}, # section -> avg_lines
        "transition_probabilities": {}, # Verse -> Pre-Chorus, etc.
        "top_motifs": []
    }
    
    # Simple data aggregation
    for rec in records:
        profile = rec.get("structural_profile", {})
        if not profile: continue
        
        for sec in profile.get("section_features", []):
            name = sec.get("section_type", "other")
            density = sec.get("mora_density", "balanced")
            
            if name not in stats["mora_density_map"]:
                stats["mora_density_map"][name] = []
            stats["mora_density_map"][name].append(density)
            
    # Finalize stats (Simplify for now)
    return stats

def main():
    if not REFINE_PATH.exists():
        print("Refinement not found.")
        return

    print("Stage 4: Alexandria Self-Evolution (DNA Synthesis)...")
    records = []
    with REFINE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    dna = analyze_structural_dna(records)
    
    STYLE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STYLE_INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(dna, f, ensure_ascii=False, indent=2)
        
    print(f"DNA Evolution Complete. Style Matrix saved to {STYLE_INDEX_PATH}")

if __name__ == "__main__":
    main()

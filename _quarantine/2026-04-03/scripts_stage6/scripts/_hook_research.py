import json
import sys
import io
from pathlib import Path

def analyze_choruses(project_root):
    conditioning_paths = list(Path(project_root).glob("data/**/*.conditioning.json"))
    print(f"Found {len(conditioning_paths)} conditioning files.")
    
    chorus_data = []
    for p in conditioning_paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            
            # Find chorus in section_analysis
            sa = d.get("section_analysis", [])
            for s in sa:
                name = s.get("section", s.get("section_name", "")).lower()
                if "chorus" in name or "사비" in name or "hook" in name:
                    chorus_data.append({
                        "track_id": d.get("track_identity", {}).get("track_id"),
                        "section_name": name,
                        "vocabulary_focus": s.get("vocabulary_focus", []),
                        "imagery_anchors": s.get("imagery_anchors", []),
                        # Check ground truth lines for syllable/rhyme analysis
                        "lines": next((gs.get("lines", []) for gs in d.get("lyric_ground_truth", {}).get("sections", []) 
                                      if gs.get("section_name", "").lower() in name or name in gs.get("section_name", "").lower()), [])
                    })
        except:
            continue

    print(f"Extracted {len(chorus_data)} chorus sections.")
    if chorus_data:
        sample = chorus_data[0]
        print(f"\nSample Chorus ({sample['track_id']}):")
        print(f" Section: {sample['section_name']}")
        print(f" Vocab: {sample['vocabulary_focus']}")
        print(f" Lines: {sample['lines']}")

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    analyze_choruses('c:/JPop_Songwriter/AKIRA ENGINE')

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

MANIFEST_PATH = Path("data/mastery/selection_manifest.json")
OUTPUT_MANIFEST = Path("datasets/suno/suno_v6_elite_bundle.jsonl")

# Normalized Tags Vocabulary (Approved Spec)
CORE_STYLE_TAGS = {
    "dark_cute_breakdown": "Dark Cute",
    "glitch_hyper_pop": "Glitch Hyper-Pop",
    "anthemic_cinematic": "Neo-Anthemic",
    "hachi_classic": "Hachi-style Rock",
    "royal_minimalist": "Minimalist Electronica"
}

ENERGY_TAGS = ["manic", "pleading", "detached", "explosive"]
TEXTURE_TAGS = ["glitch", "dense", "airy", "harsh"]

def resolve_suno_tags(mode: str) -> List[str]:
    """
    Returns a normalized tag list based on the Mastery Mode.
    """
    tags = [CORE_STYLE_TAGS.get(mode, "J-Pop")]
    
    # Simple rule-based delivery tags
    if "dark" in mode or "glitch" in mode:
        tags.extend(["manic", "glitch", "dense"])
    elif "anthemic" in mode:
        tags.extend(["explosive", "airy"])
    elif "minimalist" in mode:
        tags.extend(["detached", "harsh"])
    
    return tags

class SunoV6Packager:
    def __init__(self):
        OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    def package(self):
        print(f"--- Packaging Suno v6 Elite Bundle (Phase 6) ---")
        
        if not MANIFEST_PATH.exists():
            print(f"  [ERROR] Selection manifest not found: {MANIFEST_PATH}")
            return
            
        manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        selected = manifest_data.get("selected_tracks", [])
        
        print(f"Total tracks to package: {len(selected)}")
        
        with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
            for track in selected:
                mode = track.get("mode", "universal")
                tags = resolve_suno_tags(mode)
                
                # Each record follows the standard synthesis manifest format
                record = {
                    "mastery_id": track.get("v2_5_id"),
                    "source_id": track.get("source_track_id"),
                    "title": track.get("title"),
                    "artist": track.get("artist"),
                    "primary_mode": mode,
                    "style_tags": tags,
                    "suno_command": f"[Style: {', '.join(tags)}]",
                    "mastery_score": track.get("mastery_score"),
                    "provenance": {
                        "engine_version": "2.5.0",
                        "run_date": track.get("timestamp"),
                        "selection_manifest_version": manifest_data.get("version")
                    }
                }
                
                # Fetch lyrics from the output dir
                out_path = Path("outputs/production_v2_5") / track.get("source_track_id") / "mastery_v2_5_data.json"
                # (Actually, the lyrics are in the 'selected_lyric.md' in that same id folder)
                lyric_file = out_path.parent / "selected_lyric.md"
                if lyric_file.exists():
                    record["lyrics"] = lyric_file.read_text(encoding="utf-8")
                
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                
        print(f"\n--- Packaging Complete ---")
        print(f"Output: {OUTPUT_MANIFEST}")

if __name__ == "__main__":
    packager = SunoV6Packager()
    packager.package()

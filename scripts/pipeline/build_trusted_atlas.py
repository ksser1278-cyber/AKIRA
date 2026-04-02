import json
import sys
from pathlib import Path
from collections import Counter

# Fix PYTHONPATH
PROJECT_ROOT = Path(r"C:\JPop_Songwriter\AKIRA ENGINE")
sys.path.append(str(PROJECT_ROOT / "src"))

from akira_engine.features.mod import run_features_stage, BODY_KEYWORDS, SCENE_KEYWORDS, SOUND_KEYWORDS

MANIFEST_PATH = PROJECT_ROOT / "data" / "reference_tracks" / "cleanup_manifest.jsonl"
ATLAS_PATH = PROJECT_ROOT / "data" / "features" / "atlas_v1_trusted.json"
REVIEW_LOG_PATH = PROJECT_ROOT / "data" / "features" / "atlas_v1_review.txt"

def extract_text_from_conditioning(data: dict) -> str:
    sections = data.get("lyric_ground_truth", {}).get("sections", [])
    all_lines = []
    for s in sections:
        all_lines.extend(s.get("lines", []))
    return "\n".join(all_lines)

def build_atlas():
    if not MANIFEST_PATH.exists():
        print(f"[ERROR] Manifest not found: {MANIFEST_PATH}")
        return

    ATLAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    verified_tracks = []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("verdict") == "Verified":
                verified_tracks.append(entry)
                
    print(f"Building atlas from {len(verified_tracks)} verified tracks...")
    
    all_body = Counter()
    all_scene = Counter()
    all_sound = Counter()
    all_motif = Counter()
    
    for entry in verified_tracks:
        original_path = PROJECT_ROOT / entry["original_path"]
        if not original_path.exists(): continue
        
        with open(original_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        text = extract_text_from_conditioning(data)
        profile = run_features_stage(entry["track_id"], text)
        
        for a in profile.body_atoms: all_body[a] += 1
        for a in profile.scene_atoms: all_scene[a] += 1
        for a in profile.sound_atoms: all_sound[a] += 1
        for a in profile.motif_atoms: all_motif[a] += 1
        
    # vNext: Filter for high-confidence atoms (seen at least twice or in primary keywords)
    def filter_high_conf(counter: Counter, seed_set: set):
        return [k for k, v in counter.items() if v >= 2 or k in seed_set]

    atlas = {
        "metadata": {
            "source_track_count": len(verified_tracks),
            "generated_at": str(Path().cwd())
        },
        "body": filter_high_conf(all_body, BODY_KEYWORDS),
        "scene": filter_high_conf(all_scene, SCENE_KEYWORDS),
        "sound": filter_high_conf(all_sound, SOUND_KEYWORDS),
        "motif_top_50": [k for k, v in all_motif.most_common(50)]
    }
    
    with open(ATLAS_PATH, "w", encoding="utf-8") as f:
        json.dump(atlas, f, ensure_ascii=False, indent=2)
        
    # Write review sample
    with open(REVIEW_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("=== Atlas v1 Trusted Review Sample ===\n")
        f.write(f"Body Atoms: {atlas['body'][:10]}\n")
        f.write(f"Scene Atoms: {atlas['scene'][:10]}\n")
        f.write(f"Sound Atoms: {atlas['sound'][:10]}\n")
        f.write(f"Top Motifs: {atlas['motif_top_50'][:10]}\n")

    print(f"Atlas built: {ATLAS_PATH}")

if __name__ == "__main__":
    build_atlas()

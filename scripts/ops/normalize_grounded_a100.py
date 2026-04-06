import json
from pathlib import Path

def normalize_grounded_tracks(workspace_root: Path, output_dir: Path):
    lyric_assets_dir = workspace_root / "lyric_assets"
    section_maps_dir = workspace_root / "section_maps"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for txt_path in lyric_assets_dir.glob("*.txt"):
        track_id = txt_path.stem
        map_path = section_maps_dir / f"{track_id}.sections.json"
        
        if not map_path.exists():
            print(f"Skipping {track_id}: Missing section map.")
            continue
            
        lyrics = txt_path.read_text(encoding="utf-8").splitlines()
        # Remove empty lines from the raw list but keep them for indices if needed?
        # Actually, the section maps were built against the full text including potential blanks
        # But my section maps used indices [start, end].
        
        with open(map_path, "r", encoding="utf-8") as f:
            section_map = json.load(f)
            
        normalized_sections = []
        for sec in section_map["sections"]:
            start, end = sec["text_indices"]
            # To be safe, we need to handle if the txt file has empty lines that weren't counted
            # The grounding script I wrote used lyrics.splitlines()
            sec_lines = lyrics[start:end]
            normalized_sections.append({
                "label": sec["section"],
                "text": "\n".join(sec_lines),
                "lines": sec_lines,
                "line_count": len(sec_lines)
            })
            
        record_path = workspace_root / "records" / f"{track_id}.json"
        if not record_path.exists():
            print(f"Skipping {track_id}: Missing record metadata.")
            continue
            
        with open(record_path, "r", encoding="utf-8") as f:
            record = json.load(f)
            
        artist_id = record["track_identity"]["artist_id"]
        
        normalized_doc = {
            "track_id": track_id,
            "artist_id": artist_id,
            "sections": normalized_sections
        }
        
        output_path = output_dir / f"{track_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(normalized_doc, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"Normalized {track_id} -> {output_path}")
        
    return count

if __name__ == "__main__":
    workspace = Path("C:/JPop_Songwriter/AKIRA ENGINE/datasets/training/lyric_technique_acquisition_queue/batch_a100")
    # For now, we'll output to the standard 'lyrics/normalized' but in a batch-specific subfolder
    output = Path("C:/JPop_Songwriter/AKIRA ENGINE/lyrics/normalized/batch_a100")
    normalize_grounded_tracks(workspace, output)

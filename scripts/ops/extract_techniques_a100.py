import json
from pathlib import Path
import sys

# Add src to path so we can import akira_engine
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.akira_engine.lyric_technique_extraction import build_lyric_technique_record

def extract_a100_techniques(normalized_root: Path, output_file: Path):
    DEFAULT_ARTIST_ANALYSIS = {
        "imagery_profile": {"top_imagery_clusters": []},
        "emotional_profile": {"dominant_arc_patterns": []},
        "mode_candidates": [],
        "analysis_notes": ["Default analysis for batch_a100 pilot tracks."]
    }
    
    records = []
    for json_path in sorted(normalized_root.glob("*.json")):
        with open(json_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
            
        # Reformat normalized doc for build_lyric_technique_record
        # build_lyric_technique_record expects 'normalized_text' and 'stats'
        doc["normalized_text"] = "\n".join([line for sec in doc["sections"] for line in sec["lines"]])
        doc["stats"] = {"section_count": len(doc["sections"])}
        doc["title"] = doc.get("track_id", "unknown") # Placeholder for title
        
        # Try to find artist analysis if it exists
        artist_id = doc.get("artist_id")
        analysis_path = Path(f"C:/JPop_Songwriter/AKIRA ENGINE/lyrics/{artist_id}/analysis.json")
        artist_analysis = DEFAULT_ARTIST_ANALYSIS
        if analysis_path.exists():
            with open(analysis_path, "r", encoding="utf-8") as af:
                artist_analysis = json.load(af)
        
        record = build_lyric_technique_record(
            normalized_doc=doc,
            artist_analysis=artist_analysis,
            rights_status="batch_a100_promotion"
        )
        records.append(record)
        print(f"Extracted DNA for {doc['track_id']} ({artist_id})")
        
    with open(output_file, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    return len(records)

if __name__ == "__main__":
    norm_root = Path("C:/JPop_Songwriter/AKIRA ENGINE/lyrics/normalized/batch_a100")
    out_path = Path("C:/JPop_Songwriter/AKIRA ENGINE/datasets/training/lyric_technique_acquisition_queue/batch_a100/lyric_technique_records.jsonl")
    count = extract_a100_techniques(norm_root, out_path)
    print(f"Successfully extracted {count} technique records.")

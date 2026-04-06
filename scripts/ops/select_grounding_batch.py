import json
from pathlib import Path

# High-Value "Professional Target" Producers
PRODUCER_TARGETS = {
    "deco_27", "wowaka", "kairiki_bear", "neru", "pinocchiop", "n_buna",
    "jin", "sasakure_uk", "giga", "mitchie_m", "mikitop", "hachi",
    "ayase", "syudou", "kanaria", "kikuo", "cosmo_at_bousoup", "tuyu",
    "honeyworks", "40m_p", "kuragep", "p_p", "r_o_n", "reol"
}

def select_batch(records_dir: Path, output_file: Path, limit: int = 100):
    selected = []
    candidates = list(records_dir.glob("*.json"))
    
    # First Pass: High-Value Targets
    for path in candidates:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not record.get("queue_status", {}).get("ready_for_lyric_grounding"):
                continue
                
            artist_id = record.get("track_identity", {}).get("artist_id")
            if artist_id in PRODUCER_TARGETS:
                selected.append({
                    "track_id": record["track_identity"]["track_id"],
                    "artist_id": artist_id,
                    "canonical_title": record["track_identity"]["canonical_title"],
                    "producer": record["metadata_context"]["producer"],
                    "original_platform": record["metadata_context"]["original_platform"],
                    "official_uploads": record["acquisition_sources"]["official_uploads"],
                    "priority_score": 10
                })
                if len(selected) >= limit:
                    break
        except Exception:
            continue
            
    # Second Pass: Fill with Ready tracks if not reached limit
    if len(selected) < limit:
        remaining = limit - len(selected)
        for path in candidates:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if not record.get("queue_status", {}).get("ready_for_lyric_grounding"):
                    continue
                
                track_id = record["track_identity"]["track_id"]
                if any(s["track_id"] == track_id for s in selected):
                    continue
                    
                selected.append({
                    "track_id": track_id,
                    "artist_id": record["track_identity"]["artist_id"],
                    "canonical_title": record["track_identity"]["canonical_title"],
                    "producer": record["metadata_context"]["producer"],
                    "original_platform": record["metadata_context"]["original_platform"],
                    "official_uploads": record["acquisition_sources"]["official_uploads"],
                    "priority_score": 5
                })
                if len(selected) >= limit:
                    break
            except Exception:
                continue

    output_payload = {
        "schema_version": "1.0",
        "record_type": "lyric_grounding_batch_manifest",
        "batch_id": "A-100",
        "counts": {
            "selected": len(selected),
            "target_limit": limit
        },
        "selected_tracks": selected
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)
    print(f"Selection complete: {len(selected)} tracks saved to {output_file}")

if __name__ == "__main__":
    records_dir = Path("datasets/training/lyric_technique_acquisition_queue/global_v1/records")
    output_file = Path("reports/planning/lyric_grounding_batch_a100.json")
    select_batch(records_dir, output_file)

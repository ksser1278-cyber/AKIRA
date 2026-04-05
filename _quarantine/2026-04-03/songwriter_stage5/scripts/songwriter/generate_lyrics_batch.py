import sys
import json
from pathlib import Path
import argparse

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from akira_engine.synthesizer import LyricSynthesizer

def main():
    parser = argparse.ArgumentParser(description="Batch generate lyric synthesis requests for an artist's anchor set.")
    parser.add_argument("--artist-id", required=True, help="Artist ID (e.g., pinocchiop, deco27)")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    artist_id = args.artist_id
    
    synthesizer = LyricSynthesizer(project_root)
    
    # Load profile for grammar guidelines
    profile_path = project_root / "artists" / artist_id / "profile.json"
    if not profile_path.exists():
        print(f"Error: Profile not found at {profile_path}")
        return
    profile_data = json.loads(profile_path.read_text(encoding='utf-8'))

    # Path to benchmarks (briefs)
    briefs_dir = project_root / "outputs" / "benchmarks" / artist_id
    if not briefs_dir.exists():
        print(f"Error: Briefs directory not found at {briefs_dir}")
        return

    brief_files = sorted(list(briefs_dir.glob("*.md")))
    if not brief_files:
        print(f"No brief files found in {briefs_dir}")
        return

    # Filter out "certified" or already done tracks if needed
    # For now, generate the full set for the run
    
    output_manifest_path = project_root / "outputs" / "synthesis" / artist_id / "requests_synthesis.jsonl"
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for brief_path in brief_files:
        # Skip previously certified files if they are in the the same dir but shouldn't be processed
        if "certified" in brief_path.name:
            continue
            
        track_id = brief_path.stem
        print(f"Adding to manifest: {track_id}")
        
        brief_content = brief_path.read_text(encoding='utf-8')
        record = synthesizer.prepare_request_record(artist_id, track_id, brief_content, profile_data)
        records.append(record)

    with output_manifest_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nManifest generated: {output_manifest_path}")
    print(f"Total requests: {len(records)}")
    print(f"\nTo run the synthesis, use:")
    print(f"python scripts/songwriter/run_gemini_songwriter.py --requests {output_manifest_path}")

if __name__ == "__main__":
    main()

import sys
import json
import random
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

from akira_engine.songwriter_v2 import run_songwriter_v2
from akira_engine.mastery_blueprint import validate_against_blueprint
from akira_engine.lyric_draft import lyric_lines

def run_mastery_demo():
    print("Starting AKIRA ENGINE Mastery Validation Demo...")
    
    # Configuration
    # Seed: Confessions of a Rotten Girl (Elite)
    TRACK_ID = "734953" 
    SOURCE_JSONL = Path("datasets/corpus/alexandria_10k_elite_refined.jsonl")
    OUTPUT_DIR = Path("outputs/mastery/demo_v2_phonetic")
    
    try:
        # Run Pipeline (Force a high-energy mode to trigger glitches)
        manifest = run_songwriter_v2(
            source_jsonl=SOURCE_JSONL,
            track_id=TRACK_ID,
            output_dir=OUTPUT_DIR,
            candidate_count=3,
            include_history=False
        )
        
        # Load winning lyric
        selected_path = Path(manifest["selected_lyric_path"])
        lyrics_md = selected_path.read_text(encoding="utf-8")
        
        # Calculate Mastery Alignment for the result
        lines = lyric_lines(lyrics_md)
        mastery_results = validate_against_blueprint(lines, "Chorus")
        
        print("\n" + "="*50)
        print("PHONETIC MASTERY VALIDATION REPORT")
        print("="*50)
        print(f"Track Seed: {TRACK_ID}")
        print(f"Final Score: {manifest['selected_score']:.2f}")
        print(f"Mastery Alignment: {mastery_results['total_mastery_score']:.2f}")
        print("-" * 30)
        print("Metric Breakdown:")
        for metric, score in mastery_results.items():
            if metric != "total_mastery_score":
                print(f" - {metric}: {score:.2f}")
        print("=" * 50)
        
        # Check for glitches in the output
        glitch_count = lyrics_md.count("-")
        print(f"Glitch Intensity Detected: {glitch_count} stutters found.")
        print(f"\nWinning Lyric saved to: {selected_path}")
        
    except Exception as e:
        print(f"Error during demo run: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_mastery_demo()

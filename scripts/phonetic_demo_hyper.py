import sys
import json
import random
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

from akira_engine.songwriter_v2 import run_songwriter_v2
from akira_engine.mastery_blueprint import validate_against_blueprint
from akira_engine.lyric_draft import lyric_lines
from akira_engine.phonetic_engine import apply_stutter_glitch

def run_hyper_phonetic_demo():
    print("Starting AKIRA ENGINE Hyper-Phonetic Validation Demo...")
    
    # Configuration for full generation
    TRACK_ID = "734953" 
    SOURCE_JSONL = Path("datasets/corpus/alexandria_10k_elite_refined.jsonl")
    OUTPUT_DIR = Path("outputs/mastery/demo_v3_hyper")
    
    try:
        # Load record manually to override mode for testing
        with open(SOURCE_JSONL, 'r', encoding='utf-8') as f:
            records = [json.loads(line) for line in f]
        
        target_record = next(r for r in records if str(r.get('id')) == TRACK_ID)
        # Force a high-energy "Hyper-Pop" mode
        target_record["primary_mode"] = "glitch_hyper_pop"
        target_record["force_glitch_intensity"] = 1.0 # New injection
        
        # We'll use a temporary jsonl for this forced test
        temp_jsonl = Path("tmp/hyper_test.jsonl")
        temp_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_jsonl, 'w', encoding='utf-8') as f:
            f.write(json.dumps(target_record))

        # Run Pipeline
        manifest = run_songwriter_v2(
            source_jsonl=temp_jsonl,
            track_id=TRACK_ID,
            output_dir=OUTPUT_DIR,
            candidate_count=2,
            include_history=False
        )
        
        # Load winning lyric
        selected_path = Path(manifest["selected_lyric_path"])
        lyrics_md = selected_path.read_text(encoding="utf-8")
        
        # Calculate Mastery Alignment for the result
        lines = lyric_lines(lyrics_md)
        mastery_results = validate_against_blueprint(lines, "Chorus")
        
        print("\n" + "="*50)
        print("PHONETIC HYPER-POP VALIDATION REPORT")
        print("="*50)
        print(f"Mastery Alignment: {mastery_results['total_mastery_score']:.2f}")
        
        # Check for glitches in the output
        glitch_count = lyrics_md.count("-")
        print(f"Glitch Activity: {glitch_count} stutters generated.")
        print("-" * 30)
        
        # Print a sample glitched line
        glitched_lines = [l for l in lyrics_md.splitlines() if "-" in l]
        if glitched_lines:
            print(f"Sample Glitched Line: {glitched_lines[0]}")
        
        print(f"\nWinning Lyric saved to: {selected_path}")
        
    except Exception as e:
        print(f"Error during hyper demo run: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_hyper_phonetic_demo()

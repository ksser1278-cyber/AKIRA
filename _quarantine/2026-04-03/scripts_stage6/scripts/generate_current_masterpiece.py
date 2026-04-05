import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path("src").resolve()))

from akira_engine.songwriter_v2 import run_songwriter_v2

def generate_current_masterpiece():
    # Seed: Confessions of a Rotten Girl (Elite)
    TRACK_ID = "734953" 
    SOURCE_JSONL = Path("datasets/corpus/alexandria_10k_elite_refined.jsonl")
    OUTPUT_DIR = Path("outputs/mastery/current_generation")
    
    # Load record to force High-Tension mode
    with open(SOURCE_JSONL, 'r', encoding='utf-8') as f:
        records = [json.loads(line) for line in f]
    
    target_record = next(r for r in records if str(r.get('id')) == TRACK_ID)
    if "target" not in target_record:
        target_record["target"] = {}
    target_record["target"]["primary_mode"] = "glitch_hyper_pop" # High energy glitch mode
    target_record["force_glitch_intensity"] = 0.5 # High intensity for demo
    
    # Temporary JSONL for this run
    temp_jsonl = Path("tmp/current_gen_seed.jsonl")
    temp_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_jsonl, 'w', encoding='utf-8') as f:
        f.write(json.dumps(target_record))
        
    print(f"Generating masterpiece using Track ID {TRACK_ID} in 'glitch_hyper_pop' mode...")
    
    manifest = run_songwriter_v2(
        source_jsonl=temp_jsonl,
        track_id=TRACK_ID,
        output_dir=OUTPUT_DIR,
        candidate_count=1, # Just one fast generation
        include_history=False
    )
    
    selected_path = Path(manifest["selected_lyric_path"])
    lyrics = selected_path.read_text(encoding="utf-8")
    
    print("\n" + "="*50)
    print("CURRENT ENGINE GENERATION (Mastery + Phonetic)")
    print("="*50)
    print(lyrics)
    print("="*50)

if __name__ == "__main__":
    generate_current_masterpiece()

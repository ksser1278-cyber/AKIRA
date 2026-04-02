import os
import sys
import time
import subprocess
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# CONFIGURATION
RAW_FILE = Path("datasets/corpus/alexandria_10k_raw.jsonl")
REFINED_FILE = Path("datasets/corpus/alexandria_10k_refined.jsonl")
INGEST_SCRIPT = "scripts/suno/ingest_v55_library_alexandria_10k.py"
REFINE_SCRIPT = "scripts/suno/refine_alexandria_corpus_10k.py"
EVOLVE_SCRIPT = "scripts/suno/evolve_alexandria_dna.py"
LOOP_DELAY = 120 # Check every 2 minutes

def get_count(path):
    if not path.exists(): return 0
    try:
        # Use a faster count for large files
        count = 0
        with open(path, "rb") as f:
            for line in f: count += 1
        return count
    except: return 0

def run_script(script_path, background=False):
    print(f" -> Supervising: Running {script_path}...")
    try:
        if background:
            subprocess.Popen([sys.executable, script_path])
        else:
            subprocess.run([sys.executable, script_path], check=True)
    except Exception as e:
        print(f"    [SUPERVISOR ERROR] Failed to run {script_path}: {e}")

def main():
    print("AKIRA ENGINE: Alexandria Masterpiece Supervisor Active (24H Evolution Mode)")
    print(f"Authorized for 50,000-track expansion and self-learning.")

    # 1. Start Ingestion in Background
    run_script(INGEST_SCRIPT, background=True)

    while True:
        raw_count = get_count(RAW_FILE)
        refined_count = get_count(REFINED_FILE)

        print(f"\n[STATUS] {time.strftime('%H:%M:%S')} | Collected: {raw_count} | Refined: {refined_count}")

        if raw_count > refined_count:
            print(f" -> Found {raw_count - refined_count} new records. Starting High-Fidelity Refinement...")
            run_script(REFINE_SCRIPT)
            
            print(f" -> Synthesizing New Writing DNA...")
            run_script(EVOLVE_SCRIPT)
        
        if refined_count >= 50000:
            print("Alexandria Ultimate Milestone Reached (50,000). Evolution Complete.")
            time.sleep(3600) 
            continue

        print(f"Monitoring... Next check in {LOOP_DELAY}s")
        time.sleep(LOOP_DELAY)

if __name__ == "__main__":
    main()

import json
import random
import os
import sys
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DEFINITIVE_DIR = Path("outputs/suno_v55_custom_models/massive_150/definitive")
FINAL_OUTPUT_DIR = Path("outputs/suno_v55_custom_models/massive_150/ready_for_training")

def main():
    if not DEFINITIVE_DIR.exists():
        print("Definitive directory not found.")
        return

    FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Stage 7: Massive Sniper Synthesis (Suno v5.5 Training Ready)...")

    for file in DEFINITIVE_DIR.glob("*.jsonl"):
        cluster_name = file.stem.replace("_definitive", "")
        print(f" -> Finalizing {cluster_name}...")
        
        bundle = []
        with file.open("r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                # Ensure each record has 100% Masterpiece compliance
                if rec.get("status") == "definitive_elite":
                    bundle.append(rec)
                else:
                    print(f"    [WARNING] Skipping non-definitive track: {rec.get('title')}")
        
        output_file = FINAL_OUTPUT_DIR / f"{cluster_name}_masterpiece_bundle.jsonl"
        with output_file.open("w", encoding="utf-8") as f:
            for rec in bundle:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        
        print(f"    [OK] Bundle Finalized: {len(bundle)} tracks.")

    print(f"Final Bundles ready in {FINAL_OUTPUT_DIR}")

if __name__ == "__main__":
    main()

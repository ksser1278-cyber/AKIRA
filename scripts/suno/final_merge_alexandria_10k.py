import os
import sys
import json
from pathlib import Path

# Force UTF-8 for console output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REFINED_ELITE = Path("datasets/corpus/alexandria_10k_elite_refined.jsonl")
MAIN_REFINED = Path("datasets/corpus/alexandria_10k_refined.jsonl")
MAIN_PURE_JP = Path("datasets/corpus/alexandria_10k_pure_jp.jsonl")

def is_pure_japanese(text):
    if not text: return False
    import re
    jp_chars = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
    return len(jp_chars) > (len(text) * 0.2)

def main():
    if not REFINED_ELITE.exists():
        print("Refined elite file not found.")
        return

    print("Merging Elite records into the main Alexandria Corpus...")
    
    with REFINED_ELITE.open("r", encoding="utf-8") as f_in, \
         MAIN_REFINED.open("a", encoding="utf-8") as f_ref, \
         MAIN_PURE_JP.open("a", encoding="utf-8") as f_pure:
        
        merged_count = 0
        pure_count = 0
        
        for line in f_in:
            record = json.loads(line)
            # 1. Append to refined
            f_ref.write(line)
            merged_count += 1
            
            # 2. Check for pure JP and append
            lyrics = record.get("lyrics", "")
            # The refined lyrics have [Verse] headers, we skip them for the purity check
            content_only = "\n".join([l for l in lyrics.splitlines() if not (l.startswith("[") and l.endswith("]"))])
            if is_pure_japanese(content_only):
                f_pure.write(line)
                pure_count += 1
                
    print(f"Merge Complete.")
    print(f" - Appended {merged_count} tracks to {MAIN_REFINED.name}")
    print(f" - Appended {pure_count} tracks to {MAIN_PURE_JP.name}")

if __name__ == "__main__":
    main()

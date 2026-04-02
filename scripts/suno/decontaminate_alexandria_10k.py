import json
import re
from pathlib import Path

# CONFIGURATION
INPUT_FILE = Path("datasets/corpus/alexandria_10k_refined.jsonl")
OUTPUT_FILE = Path("datasets/corpus/alexandria_10k_pure_jp.jsonl")

def is_polluted(record):
    """
    Checks if a record is 'polluted' with:
    1. Broken encoding (\ufffd)
    2. Hangul (Korean)
    3. Extensive Romaji/English fragments (> 10 consecutive chars outside headers)
    """
    lyrics = record.get("lyrics", "")
    
    # 1. Broken Encoding
    if "\ufffd" in lyrics or "\ufffd" in record.get("title", ""):
        return True, "corrupted_encoding"
    
    # 2. Hangul (Korean)
    if re.search("[\uac00-\ud7a3]", lyrics):
        return True, "hangul_contamination"
        
    # 3. Extensive Romaji/English (filtered for headers)
    # This filters out [Intro], [Chorus], but catches long English lines.
    clean_lyrics = re.sub(r"\[[A-Za-z]+\]", "", lyrics)
    if re.search("[a-zA-Z]{12,}", clean_lyrics): # 12+ chars is likely English sentence fragment
        return True, "romaji_contamination"
        
    return False, None

def main():
    if not INPUT_FILE.exists():
        print("Input file not found.")
        return

    print("Starting Alexandria Decontamination (Pure Japanese Audit)...")
    
    total = 0
    clean_count = 0
    polluted_count = 0
    
    with INPUT_FILE.open("r", encoding="utf-8") as f_in, OUTPUT_FILE.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            total += 1
            try:
                record = json.loads(line)
                polluted, reason = is_polluted(record)
                
                if not polluted:
                    f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    clean_count += 1
                else:
                    polluted_count += 1
                    if polluted_count <= 5: # Sample reports
                        print(f"  [PURGE] {reason}: {record.get('title')}")
                        
            except Exception as e:
                polluted_count += 1

    print(f"\nDecontamination Complete.")
    print(f"  - Total Audited: {total}")
    print(f"  - Cleaned (Pure JP): {clean_count} ({clean_count/total*100:.1f}%)")
    print(f"  - Purged (Polluted): {polluted_count} ({polluted_count/total*100:.1f}%)")

if __name__ == "__main__":
    main()

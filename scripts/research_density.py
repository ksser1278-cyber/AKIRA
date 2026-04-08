import json
import re
from collections import Counter
from pathlib import Path

# Paths
DATASET_PATH = Path(r"C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\archive\datasets\corpus\alexandria_10k_refined.jsonl")

def count_mora(text):
    """Simple mora counter for Japanese (counting hiragana/katakana + kanji segments)."""
    # This is a heuristic: counting characters excluding spaces/punctuation
    clean = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    return len(clean)

def analyze():
    print(f"[*] Analyzing density features from {DATASET_PATH}...")
    
    total_mora = 0
    total_lines = 0
    total_unique_words = Counter()
    
    # We want to compare "High Signal" vs "Standard"
    # For now, let's just look at the overall distribution to find the "Density Cap"
    
    track_stats = []
    
    line_limit = 110024 # Process everything
    count = 0
    
    with DATASET_PATH.open(encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                lyrics = record.get("lyrics", "")
                if not lyrics: continue
                
                lines = [l.strip() for l in lyrics.splitlines() if l.strip() and not l.startswith("[")]
                if not lines: continue
                
                mora_counts = [count_mora(l) for l in lines]
                avg_mora = sum(mora_counts) / len(mora_counts)
                max_mora = max(mora_counts)
                
                # Lexical richness (character level for now since no mecab)
                unique_chars = len(set(lyrics))
                
                track_stats.append({
                    "avg_mora": avg_mora,
                    "max_mora": max_mora,
                    "char_set": unique_chars,
                    "is_subculture": "feat." in record.get("artist", "").lower() or "ミク" in record.get("artist", "") # Rough proxy
                })
                
                count += 1
                if count % 20000 == 0:
                    print(f"  Processed {count} tracks...")
            except:
                continue
    
    # Analyze distributions
    sub_stats = [s for s in track_stats if s["is_subculture"]]
    pop_stats = [s for s in track_stats if not s["is_subculture"]]
    
    def get_avg(stats, key):
        if not stats: return 0
        return sum(s[key] for s in stats) / len(stats)

    print("\n[RESULTS]")
    print(f"Subculture Avg Mora/Line: {get_avg(sub_stats, 'avg_mora'):.2f}")
    print(f"Pop Avg Mora/Line:        {get_avg(pop_stats, 'avg_mora'):.2f}")
    
    print(f"Subculture Peak Mora:     {get_avg(sub_stats, 'max_mora'):.2f}")
    print(f"Pop Peak Mora:            {get_avg(pop_stats, 'max_mora'):.2f}")
    
    print(f"Subculture Lexical Set:   {get_avg(sub_stats, 'char_set'):.2f}")
    print(f"Pop Lexical Set:          {get_avg(pop_stats, 'char_set'):.2f}")

if __name__ == "__main__":
    analyze()

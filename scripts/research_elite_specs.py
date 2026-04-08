import json
import re
from pathlib import Path

DATASET_PATH = Path(r"C:\JPop_Songwriter\AKIRA ENGINE\_quarantine\2026-04-03\archive\datasets\corpus\alexandria_10k_refined.jsonl")

def count_mora(text):
    clean = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    return len(clean)

def analyze_elite():
    print("[*] Finding Elite Tracks (Top 0.1% Complexity)...")
    tracks = []
    
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
                
                # Lexical diversity: unique chars / total chars
                unique_chars = len(set(lyrics))
                complexity_score = avg_mora * unique_chars
                
                tracks.append({
                    "title": record.get("title"),
                    "artist": record.get("artist"),
                    "avg_mora": avg_mora,
                    "max_mora": max(mora_counts),
                    "unique_chars": unique_chars,
                    "complexity": complexity_score,
                    "lyrics_snippet": lyrics[:200].replace("\n", " ")
                })
            except:
                continue
    
    # Sort by complexity
    tracks.sort(key=lambda x: x["complexity"], reverse=True)
    
    print("\n[ELITE SPECIMENS - TOP 10]")
    for i, t in enumerate(tracks[:10]):
        print(f"{i+1}. {t['title']} ({t['artist']})")
        print(f"   Avg Mora: {t['avg_mora']:.2f} | Max Mora: {t['max_mora']} | Unique Chars: {t['unique_chars']}")
        print(f"   Snippet: {t['lyrics_snippet']}...")
        print("-" * 40)

if __name__ == "__main__":
    analyze_elite()

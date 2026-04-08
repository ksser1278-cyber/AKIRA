"""
extract_subculture_lexicon.py
============================
11만 건 데이터셋에서 보컬로이드/서브컬처 씬 고해상도 어휘(High-Fidelity Imagery)를 추출합니다.
일반적인 가사를 제외하고 독창적인 이미지 신호를 식별합니다.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = ROOT / "_quarantine" / "2026-04-03" / "archive" / "datasets" / "corpus" / "alexandria_10k_refined.jsonl"
OUTPUT_PATH = ROOT / "data" / "technique_library" / "subculture_lexicon.json"

def main():
    print(f"[*] Extracting Subculture Lexicon from {DATASET_PATH}...")
    
    words = Counter()
    line_count = 0
    
    # 일반적인 단어 제외 필터 (너무 흔한 단어는 가점에 도움 안 됨)
    EXCLUDE = {"君", "僕", "私", "愛", "心", "夢", "空", "。", "、", "！"}

    with DATASET_PATH.open(encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                artist = record.get("artist", "").lower()
                is_subculture = any(x in artist for x in ["ミク", "rin", "len", "luka", "gumi", "feat.", "maretu", "deco27", "iyowa"])
                
                if not is_subculture: continue
                
                lyrics = record.get("lyrics", "")
                # 한자 키워드 위주로 추출 (고밀도 이미지 신호)
                kanji_segments = re.findall(r"[\u4e00-\u9fff]{2,}", lyrics) # 2자 이상의 한자어
                
                for word in kanji_segments:
                    if word not in EXCLUDE:
                        words[word] += 1
                        
                line_count += 1
                if line_count % 10000 == 0:
                    print(f"  Processed {line_count} subculture tracks...")
            except:
                continue

    # 빈도수 상위 2000개만 선별하여 보관
    top_words = [w for w, c in words.most_common(2000)]
    
    result = {
        "schema_version": "1.0",
        "category": "High-Fidelity Subculture Lexicon",
        "words": top_words,
        "sample_size": line_count
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[✓] Successfully saved {len(top_words)} high-fidelity words.")

if __name__ == "__main__":
    main()

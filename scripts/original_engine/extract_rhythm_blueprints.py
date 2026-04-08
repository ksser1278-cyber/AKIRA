"""
extract_rhythm_blueprints.py
===========================
11만 건 데이터에서 고밀도(Subculture) 트랙의 음절 수 패턴을 추출하여
엔진이 사용할 '리듬 그리드' 라이브러리를 구축합니다.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = ROOT / "_quarantine" / "2026-04-03" / "archive" / "datasets" / "corpus" / "alexandria_10k_refined.jsonl"
OUTPUT_PATH = ROOT / "data" / "technique_library" / "rhythm_blueprints.json"

def count_mora(text):
    clean = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', text)
    return len(clean)

def main():
    print(f"[*] Extracting Elite Rhythmic Patterns from {DATASET_PATH}")
    
    blueprints = []
    line_count = 0
    
    with DATASET_PATH.open(encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                artist = record.get("artist", "").lower()
                
                # 보컬로이드/서브컬처 엔진 가족 필터링 (가중치 부여)
                is_subculture = any(x in artist for x in ["ミク", "rin", "len", "luka", "gumi", "feat.", "maretu", "deco27"])
                
                sf = record.get("structural_profile", {}).get("section_features", [])
                if not sf: continue
                
                lyrics = record.get("lyrics", "")
                section_texts = re.split(r'\[[^\]]+\]', lyrics)
                section_texts = [t.strip() for t in section_texts if t.strip()]
                
                # 섹션별 리듬 패턴 추출
                rhythm_data = []
                for i, section in enumerate(sf):
                    if i >= len(section_texts): break
                    
                    sec_type = section.get("section_type", "unknown")
                    lines = [l.strip() for l in section_texts[i].splitlines() if l.strip()]
                    mora_counts = [count_mora(l) for l in lines]
                    
                    if mora_counts:
                        rhythm_data.append({
                            "section": sec_type,
                            "mora_sequence": mora_counts,
                            "avg_mora": sum(mora_counts) / len(mora_counts)
                        })
                
                if rhythm_data:
                    # 복잡도(압축도) 계산
                    complexity = sum(r["avg_mora"] for r in rhythm_data) / len(rhythm_data)
                    
                    if is_subculture and complexity > 15: # 고밀도 보컬로이드 곡 타겟
                        blueprints.append({
                            "blueprint_id": f"bp_{record['id']}",
                            "complexity": complexity,
                            "sections": rhythm_data
                        })
                
                line_count += 1
                if line_count % 10000 == 0:
                    print(f"  Scanned {line_count} tracks...")
            except:
                continue

    # 상위 1000개 고밀도 블루프린트만 선별
    blueprints.sort(key=lambda x: x["complexity"], reverse=True)
    elite_blueprints = blueprints[:1000]

    result = {
        "schema_version": "1.2",
        "description": "Elite Rhythmic Blueprints extracted from 110k tracks (Top 0.9% Density)",
        "blueprints": elite_blueprints
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[✓] Successfully extracted {len(elite_blueprints)} elite blueprints.")

if __name__ == "__main__":
    main()

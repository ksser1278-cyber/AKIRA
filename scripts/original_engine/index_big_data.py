"""
index_big_data.py
==================
11만 건의 alexandria_10k_refined.jsonl을 처리하여 고밀도 작사 DNA를 추출합니다.
보컬로이드/서브컬처 스타일을 강화하기 위해 키워드 대규모 인덱싱을 수행합니다.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = ROOT / "_quarantine" / "2026-04-03" / "archive" / "datasets" / "corpus" / "alexandria_10k_refined.jsonl"
OUTPUT_DIR = ROOT / "data" / "technique_library"

# 분석 결과물 경로
PATHS = {
    "imagery": OUTPUT_DIR / "imagery_archetypes.json",
    "structures": OUTPUT_DIR / "structural_templates.json",
    "hooks": OUTPUT_DIR / "hook_patterns.json",
    "word_bank": OUTPUT_DIR / "word_banks.json"
}

# ──────────────────────────────────────────────────────────────
# 형태소 분석 대신 사용할 일본어 키워드 필터 (보컬로이드 중심)
# ──────────────────────────────────────────────────────────────
KEYWORDS = {
    "dread": ["絶望", "恐怖", "腐る", "汚れ", "歪み", "崩壊", "最悪", "地獄", "奈落", "終焉"],
    "cyber": ["回路", "電뇌", "バグ", "エラー", "ノイズ", "デジタル", "仮想", "信号", "同期", "切단"],
    "abstract": ["概念", "論理", "理論", "虚像", "境界", "矛盾", "平行", "反転", "空想", "断片"],
    "body_horror": ["血", "骨", "肉", "爪", "脈", "心臓", "眼", "指", "皮膚", "抉る"],
    "religion": ["神", "祈り", "懺悔", "教義", "使徒", "福音", "呪い", "儀式", "聖", "穢れ"]
}

def analyze_track(record, stats):
    """트랙 하나를 분석하여 통계에 합산."""
    lyrics = record.get("lyrics", "")
    sp = record.get("structural_profile", {})
    sf = record.get("structural_profile", {}).get("section_features", [])
    
    # 1. 구조 템플릿 (섹션 순서)
    section_types = [f.get("section_type", "unknown") for f in sf]
    if section_types:
        stats["structures"][tuple(section_types)] += 1
    
    # 2. 이미지리 (키워드 기반 매칭)
    for category, words in KEYWORDS.items():
        match_count = sum(1 for w in words if w in lyrics)
        if match_count > 0:
            stats["imagery"][category] += match_count
            
    # 3. 훅 스타일 (structural_profile 활용)
    hook_force = sp.get("hook_copy_force", "unknown")
    if hook_force != "unknown":
        stats["hooks"][hook_force] += 1

def main():
    print(f"[*] Starting Indexing: {DATASET_PATH}")
    if not DATASET_PATH.exists():
        print(f"[!] Error: Dataset not found at {DATASET_PATH}")
        return

    stats = {
        "structures": Counter(),
        "imagery": Counter(),
        "hooks": Counter(),
        "word_counts": Counter()
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    line_count = 0
    with DATASET_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                analyze_track(record, stats)
                line_count += 1
                if line_count % 10000 == 0:
                    print(f"  Processed {line_count} tracks...")
            except Exception as e:
                continue

    print(f"[*] Analysis Complete. Saving results to {OUTPUT_DIR}")

    # 1. Imagery Archetypes 저장
    imagery_result = {
        "schema_version": "1.1",
        "clusters": {cat: KEYWORDS[cat] for cat in stats["imagery"]},
        "counts": dict(stats["imagery"])
    }
    with PATHS["imagery"].open("w", encoding="utf-8") as f:
        json.dump(imagery_result, f, ensure_ascii=False, indent=2)

    # 2. Structural Templates 저장 (상위 20개)
    struct_list = []
    for types, count in stats["structures"].most_common(20):
        struct_list.append({
            "sections": list(types),
            "observed_frequency": count
        })
    struct_result = {
        "schema_version": "1.1",
        "templates": struct_list
    }
    with PATHS["structures"].open("w", encoding="utf-8") as f:
        json.dump(struct_result, f, ensure_ascii=False, indent=2)

    # 3. Hook Patterns 저장
    hook_result = {
        "schema_version": "1.1",
        "force_distribution": dict(stats["hooks"])
    }
    with PATHS["hooks"].open("w", encoding="utf-8") as f:
        json.dump(hook_result, f, ensure_ascii=False, indent=2)

    print(f"[✓] Successfully indexed {line_count} tracks.")

if __name__ == "__main__":
    main()

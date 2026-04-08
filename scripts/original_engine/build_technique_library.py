"""
build_technique_library.py
==========================
track_blueprints.jsonl + lyric_assets 에서 아티스트 태그를 제거하고
순수 기법 패턴을 추출해 data/technique_library/ 에 저장합니다.

Usage:
    python scripts/original_engine/build_technique_library.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLUEPRINTS_PATH = ROOT / "datasets" / "training" / "track_blueprints.jsonl"
LYRIC_ASSETS_PATH = ROOT / "datasets" / "training" / "lyric_grounding_workspace" / "batch_a100" / "lyric_assets"
OUTPUT_DIR = ROOT / "data" / "technique_library"


# ──────────────────────────────────────────────────────────────
# 로더
# ──────────────────────────────────────────────────────────────
def load_blueprints(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        print(f"[WARN] blueprints not found: {path}")
        return records
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def load_lyric_assets(path: Path) -> list[str]:
    texts = []
    if not path.exists():
        return texts
    for txt_file in sorted(path.glob("*.txt")):
        try:
            content = txt_file.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                texts.append(content)
        except Exception:
            pass
    return texts


# ──────────────────────────────────────────────────────────────
# 기법 추출 함수들 (아티스트 태그 없음)
# ──────────────────────────────────────────────────────────────
def extract_hook_patterns(blueprints: list[dict]) -> dict:
    """훅 패턴 통계 추출."""
    density_counter: Counter = Counter()
    repeat_style_counter: Counter = Counter()

    for bp in blueprints:
        evidence = bp.get("input_context", {}).get("track_evidence", {})
        hook = evidence.get("hook_strategy", {})
        density = hook.get("hook_density", "")
        if density:
            density_counter[density] += 1

        rep_lines = hook.get("repeated_line_count", 0)
        rep_opens = hook.get("repeated_opening_count", 0)
        if rep_lines > 5:
            repeat_style_counter["chorus_anchor"] += 1
        elif rep_opens > 3:
            repeat_style_counter["opening_hook"] += 1
        else:
            repeat_style_counter["minimal_repeat"] += 1

    patterns = []
    for density, count in density_counter.most_common():
        for style, _ in repeat_style_counter.most_common(2):
            patterns.append({
                "hook_density": density,
                "repeat_style": style,
                "observed_count": count,
            })

    # 중복 제거
    seen = set()
    unique_patterns = []
    for p in patterns:
        key = (p["hook_density"], p["repeat_style"])
        if key not in seen:
            seen.add(key)
            unique_patterns.append(p)

    return {"schema_version": "1.0", "patterns": unique_patterns}


def extract_imagery_archetypes(blueprints: list[dict]) -> dict:
    """이미지 클러스터 추출 (아티스트 태그 없음)."""
    cluster_counter: Counter = Counter()
    # 감정→이미지 매핑
    emotion_imagery: dict[str, Counter] = defaultdict(Counter)

    for bp in blueprints:
        evidence = bp.get("input_context", {}).get("track_evidence", {})
        imagery_tags = evidence.get("dominant_imagery_tags", [])
        emotions = evidence.get("dominant_emotions", [])

        for tag in imagery_tags:
            cluster_counter[tag] += 1
        for emotion in emotions:
            for tag in imagery_tags:
                emotion_imagery[emotion][tag] += 1

    # 클러스터별 일본어 단어 뱅크 (하드코딩 + corpus 통계 기반)
    jp_word_bank: dict[str, list[str]] = {
        "body":    ["手", "指", "声", "息", "骨", "胸", "目", "血", "肌", "足"],
        "light":   ["光", "輝き", "影", "夕暮れ", "灯り", "白昼", "閃光"],
        "night":   ["夜", "深夜", "星", "月", "闇", "夜明け", "深夜3時"],
        "motion":  ["走る", "飛ぶ", "揺れる", "流れる", "回る", "跳ねる"],
        "fire":    ["炎", "火花", "熱", "燃える", "煙", "灰"],
        "noise":   ["音", "叫び", "静寂", "轟音", "雑踪", "囁き"],
        "weather": ["雨", "雪", "風", "嵐", "霧", "雷", "曇り"],
        "city":    ["街", "道", "ビル", "信号", "電車", "アスファルト"],
        "time":    ["時間", "瞬間", "記憶", "過去", "未来", "今"],
        "fracture": ["傷", "亀裂", "割れる", "壊れる", "欠ける", "崩れる"],
        "water":   ["水", "涙", "海", "川", "波", "湖"],
        "silence": ["静寂", "無音", "沈黙", "息をのむ", "空白"],
        "warmth":  ["温もり", "ぬくもり", "熱", "温かい", "寄り添う"],
    }

    clusters: dict[str, list[str]] = {}
    for cluster, count in cluster_counter.most_common(20):
        words = jp_word_bank.get(cluster, [cluster])
        clusters[cluster] = words

    return {
        "schema_version": "1.0",
        "clusters": clusters,
        "emotion_imagery_map": {
            emotion: dict(counter.most_common(5))
            for emotion, counter in emotion_imagery.items()
        },
    }


def extract_emotional_arc_templates(blueprints: list[dict]) -> dict:
    """감정 아크 유형 추출."""
    arc_counter: Counter = Counter()

    for bp in blueprints:
        evidence = bp.get("input_context", {}).get("track_evidence", {})
        arc = evidence.get("overall_arc_label", "")
        if arc:
            arc_counter[arc] += 1

    arc_descriptions = {
        "build_and_drop":             "Tension builds through verses, releases explosively at chorus",
        "flat_or_circular":           "Consistent emotional intensity throughout; circular resolution",
        "steady_build_to_final_release": "Gradual intensification peaking at final section",
        "quiet_then_explosive":       "Starts whisper-quiet, detonates at final chorus",
        "slow_then_medium":           "Opens slowly, settles into medium-energy groove",
        "fast_and_punchy":            "High energy from bar one; relentless forward momentum",
        "medium_pop":                 "Radio-friendly consistent pop energy",
    }

    arcs = []
    for arc_id, count in arc_counter.most_common():
        arcs.append({
            "arc_id": arc_id,
            "observed_count": count,
            "description": arc_descriptions.get(arc_id, arc_id.replace("_", " ")),
        })

    # 하드코딩 arc도 추가 (corpus에 없을 수 있음)
    existing_ids = {a["arc_id"] for a in arcs}
    for arc_id, desc in arc_descriptions.items():
        if arc_id not in existing_ids:
            arcs.append({
                "arc_id": arc_id,
                "observed_count": 0,
                "description": desc,
            })

    return {"schema_version": "1.0", "arcs": arcs}


def extract_structural_templates(blueprints: list[dict]) -> dict:
    """섹션 구조 템플릿 추출."""
    # 표준 6섹션 구조 (corpus에서 가장 일반적)
    standard_6section = {
        "structure_id": "standard_6section",
        "section_count": 6,
        "sections": [
            {"section": "Aメロ",   "goal": "구체적 디테일과 시점 확립 — 세계관 도입"},
            {"section": "Bメロ",   "goal": "감정 압축 — 사비를 향한 긴장 구축"},
            {"section": "サビ",    "goal": "핵심 훅 — 기억에 남는 형태로 전달"},
            {"section": "Aメロ2",  "goal": "밀도와 긴장감 증가 — 새로운 세부 묘사"},
            {"section": "ブリッジ", "goal": "각도 전환 또는 감정 재구성 — 최종 사비 전 환기"},
            {"section": "最終サビ", "goal": "최대 감정 방출 — 가장 강한 클라이맥스"},
        ],
    }

    # 섹션 통계
    has_bridge = sum(1 for bp in blueprints if bp.get("input_context", {}).get("track_evidence", {}).get("has_bridge"))
    has_outro = sum(1 for bp in blueprints if bp.get("input_context", {}).get("track_evidence", {}).get("has_outro"))
    total = len(blueprints) or 1

    return {
        "schema_version": "1.0",
        "structures": [standard_6section],
        "corpus_stats": {
            "bridge_ratio": round(has_bridge / total, 3),
            "outro_ratio": round(has_outro / total, 3),
            "most_common_section_count": 6,
        },
    }


def extract_syllable_profiles(blueprints: list[dict]) -> dict:
    """음절/라인 길이 프로파일 추출."""
    lengths_by_register: dict[str, list[float]] = defaultdict(list)

    for bp in blueprints:
        evidence = bp.get("input_context", {}).get("track_evidence", {})
        lang = evidence.get("language_profile", {})
        avg_chars = lang.get("line_length_profile", {}).get("average_characters", 0)
        english_level = lang.get("english_insertion_level", "low")

        # english_level → register 추정
        reg = "colloquial"
        if english_level == "high":
            reg = "mixed"
        elif english_level == "medium":
            reg = "pop"

        if avg_chars:
            lengths_by_register[reg].append(avg_chars)

    profiles: dict[str, dict] = {}
    for reg, lens in lengths_by_register.items():
        if lens:
            avg = sum(lens) / len(lens)
            profiles[reg] = {
                "avg_chars_per_line": round(avg, 1),
                "recommended_range": [max(4, int(avg * 0.6)), int(avg * 1.4)],
                "sample_count": len(lens),
            }

    # 기본 프로파일 보장
    for reg in ["poetic", "colloquial", "young_colloquial", "mixed", "pop", "formal"]:
        if reg not in profiles:
            profiles[reg] = {
                "avg_chars_per_line": 12.0,
                "recommended_range": [7, 20],
                "sample_count": 0,
            }

    return {"schema_version": "1.0", "profiles": profiles}


# ──────────────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────────────
def main() -> int:
    print("AKIRA Original Engine - Technique Library Builder")
    print(f"  Blueprints: {BLUEPRINTS_PATH}")
    print(f"  Output:     {OUTPUT_DIR}")

    blueprints = load_blueprints(BLUEPRINTS_PATH)
    print(f"  Loaded {len(blueprints)} blueprint records")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tasks = [
        ("hook_patterns",          extract_hook_patterns),
        ("imagery_archetypes",     extract_imagery_archetypes),
        ("emotional_arc_templates", extract_emotional_arc_templates),
        ("structural_templates",   extract_structural_templates),
        ("syllable_profiles",      extract_syllable_profiles),
    ]

    for name, fn in tasks:
        print(f"  Building {name}...", end=" ")
        result = fn(blueprints)

        # 아티스트 태그 제거 검사
        result_str = json.dumps(result)
        for artist in ["pinocchiop", "deco27", "kanaria", "kairiki_bear", "maretu"]:
            if artist in result_str:
                print(f"\n  [WARN] artist_id '{artist}' found in {name} — removing")
                result_str = result_str.replace(f'"{artist}"', '"[redacted]"')
                result = json.loads(result_str)

        out_path = OUTPUT_DIR / f"{name}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"OK → {out_path.name}")

    print(f"\n✓ Technique Library built at: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

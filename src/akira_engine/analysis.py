from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


TRACK_ANALYSIS_VERSION = "1.0"
ARTIST_ANALYSIS_VERSION = "1.0"

LATIN_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9']*")
JAPANESE_CHUNK_PATTERN = re.compile(r"[一-龯ぁ-んァ-ヴー]+")

ENGLISH_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "i",
    "if", "in", "is", "it", "its", "me", "my", "of", "on", "or", "our", "so",
    "that", "the", "their", "them", "there", "this", "to", "tonight", "we",
    "with", "you", "your",
}

JAPANESE_STOPWORDS = {
    "あの", "この", "その", "こと", "もの", "ため", "だけ", "まで", "から", "より",
    "して", "した", "してる", "する", "いる", "ある", "ない", "よう", "でも", "まだ",
    "ただ",
}

PRONOUN_SETS = {
    "first_person": {
        "i", "me", "my", "mine", "we", "our", "ours", "myself", "ourselves", "私",
        "わたし", "僕", "ぼく", "俺", "おれ", "あたし", "うち", "私たち", "僕ら", "俺たち",
    },
    "second_person": {
        "you", "your", "yours", "yourself", "yourselves", "君", "きみ", "あなた",
        "お前", "きさま", "君たち",
    },
    "third_person": {
        "he", "him", "his", "she", "her", "hers", "they", "them", "their",
        "theirs", "彼", "彼女", "あいつ", "あの子", "彼ら",
    },
}

IMAGERY_LEXICONS = {
    "night": {
        "night", "midnight", "dark", "moon", "neon", "twilight", "evening",
        "nocturne", "夜", "深夜", "真夜中", "闇", "月", "夜更け",
    },
    "city": {
        "city", "street", "station", "signal", "crowd", "town", "alley", "skyline",
        "platform", "駅", "街", "都会", "路地", "信号", "ホーム",
    },
    "light": {
        "light", "glow", "flare", "shine", "flash", "backlight", "dawn", "sunrise",
        "光", "灯り", "閃光", "逆光", "夜明け", "朝焼け",
    },
    "body": {
        "voice", "heart", "heartbeat", "blood", "breath", "chest", "skin", "eye",
        "hand", "body", "声", "心", "鼓動", "血", "息", "胸", "手", "目", "喉",
    },
    "fracture": {
        "break", "broken", "crack", "fracture", "shatter", "shattered", "glass",
        "mirror", "mask", "scar", "割れ", "壊", "砕", "ひび", "鏡", "ガラス", "仮面",
    },
    "motion": {
        "run", "running", "dance", "dancing", "rush", "fly", "jump", "step", "drive",
        "fall", "走", "踊", "飛", "進", "歩", "跳", "落",
    },
    "weather": {
        "rain", "storm", "wind", "snow", "fog", "thunder", "cloud", "rainfall", "雨",
        "嵐", "風", "雪", "霧", "雷", "雲",
    },
    "noise": {
        "noise", "scream", "static", "echo", "siren", "shout", "cry", "silence",
        "quiet", "ノイズ", "叫", "静寂", "沈黙", "サイレン", "声", "響",
    },
    "fire": {
        "fire", "flame", "burn", "ash", "heat", "ember", "炎", "火", "灰", "熱", "燃",
    },
    "time": {
        "countdown", "clock", "time", "second", "tomorrow", "today", "tonight",
        "future", "時計", "秒", "今夜", "明日", "未来", "時間",
    },
}

EMOTION_LEXICONS = {
    "defiance": {
        "break", "loud", "fight", "against", "refuse", "riot", "scream", "run",
        "shout", "壊", "叫", "抗", "反", "拒",
    },
    "vulnerability": {
        "alone", "lonely", "quiet", "hurt", "tears", "fragile", "empty", "afraid",
        "weak", "涙", "孤独", "痛", "弱", "怖", "空っぽ",
    },
    "uplift": {
        "rise", "light", "dawn", "open", "new", "future", "shine", "glow", "brave",
        "fly", "光", "夜明け", "未来", "開", "新", "希望", "飛",
    },
    "tension": {
        "pressure", "static", "count", "edge", "tight", "mask", "breath", "hush",
        "shadow", "圧", "仮面", "息", "緊", "影", "秒",
    },
    "darkness": {
        "dark", "smoke", "shadow", "black", "night", "ash", "blood", "闇", "煙",
        "影", "黒", "灰", "血",
    },
    "motion": {
        "run", "dance", "rush", "fly", "jump", "step", "drive", "fall", "走", "踊",
        "飛", "進", "跳", "落",
    },
}

CONTRAST_PAIRS = [
    ("light", "darkness"),
    ("silence", "noise"),
    ("stillness", "motion"),
    ("mask", "voice"),
    ("night", "dawn"),
]

CONTRAST_TERMS = {
    "light": {"light", "glow", "shine", "flare", "光", "灯り", "閃光"},
    "darkness": {"dark", "night", "shadow", "smoke", "闇", "影", "夜", "煙"},
    "silence": {"silence", "quiet", "hush", "静寂", "沈黙"},
    "noise": {"noise", "scream", "static", "siren", "叫", "ノイズ", "サイレン"},
    "stillness": {"still", "frozen", "quiet", "止", "静"},
    "motion": {"run", "dance", "rush", "jump", "走", "踊", "飛", "進"},
    "mask": {"mask", "face", "mirror", "仮面", "顔", "鏡"},
    "voice": {"voice", "shout", "echo", "声", "叫", "響"},
    "night": {"night", "midnight", "moon", "夜", "深夜", "真夜中"},
    "dawn": {"dawn", "sunrise", "morning", "nightbreak", "夜明け", "朝"},
}

SECTION_FUNCTION_HINTS = {
    "intro": "atmosphere",
    "verse": "narrative_detail",
    "pre_chorus": "escalation",
    "chorus": "hook_release",
    "bridge": "perspective_shift",
    "outro": "fade_or_afterimage",
    "refrain": "hook_return",
}


@dataclass
class TrackAnalysisSummary:
    output_path: Path
    hook_count: int
    dominant_imagery_tags: list[str]


@dataclass
class ArtistAnalysisSummary:
    output_path: Path
    track_count: int
    dominant_modes: list[str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_normalized_documents(input_root: Path) -> list[Path]:
    return sorted(
        path
        for path in input_root.rglob("*.json")
        if path.is_file() and "_template" not in path.parts
    )


def is_ascii_token(token: str) -> bool:
    return bool(LATIN_TOKEN_PATTERN.fullmatch(token))


def latin_tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in LATIN_TOKEN_PATTERN.finditer(text)]


def japanese_chunks(text: str) -> list[str]:
    return [match.group(0) for match in JAPANESE_CHUNK_PATTERN.finditer(text)]


def extract_candidate_tokens(text: str) -> list[str]:
    tokens = latin_tokens(text)
    for chunk in japanese_chunks(text):
        if len(chunk) >= 2:
            tokens.append(chunk)
    return tokens


def filtered_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for token in extract_candidate_tokens(text):
        if is_ascii_token(token):
            if token in ENGLISH_STOPWORDS or len(token) < 3:
                continue
        else:
            if token in JAPANESE_STOPWORDS or len(token) < 2:
                continue
        tokens.append(token)
    return tokens


def lyric_body_text(document: dict[str, Any]) -> str:
    return "\n".join(section["text"] for section in document["sections"])


def canonical_section_label(label: str) -> str:
    if label.startswith("pre_chorus"):
        return "pre_chorus"
    return label.split("_")[0]


def analyze_structure(document: dict[str, Any]) -> dict[str, Any]:
    sections = document["sections"]
    section_order = [section["label"] for section in sections]
    chorus_sections = [label for label in section_order if label.startswith("chorus")]
    verse_sections = [label for label in section_order if label.startswith("verse")]
    section_lengths = []

    for section in sections:
        line_lengths = [len(line) for line in section["lines"]]
        section_lengths.append(
            {
                "label": section["label"],
                "line_count": section["line_count"],
                "character_count": len(section["text"]),
                "average_line_length": round(mean(line_lengths), 2) if line_lengths else 0.0,
            }
        )

    chorus_average = mean(
        item["line_count"] for item in section_lengths if item["label"].startswith("chorus")
    ) if chorus_sections else 0.0
    verse_average = mean(
        item["line_count"] for item in section_lengths if item["label"].startswith("verse")
    ) if verse_sections else 0.0

    return {
        "section_order": section_order,
        "structure_pattern": " -> ".join(section_order),
        "section_count": len(section_order),
        "chorus_count": len(chorus_sections),
        "has_pre_chorus": any(label.startswith("pre_chorus") for label in section_order),
        "has_bridge": any(label.startswith("bridge") for label in section_order),
        "has_outro": any(label.startswith("outro") for label in section_order),
        "section_lengths": section_lengths,
        "chorus_to_verse_line_ratio": round(
            chorus_average / verse_average, 2
        ) if chorus_average and verse_average else None,
    }


def repeated_lines(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    line_map: dict[str, dict[str, Any]] = {}
    for section in sections:
        for line in section["lines"]:
            key = line.lower()
            if key not in line_map:
                line_map[key] = {"line": line, "count": 0, "sections": []}
            line_map[key]["count"] += 1
            if section["label"] not in line_map[key]["sections"]:
                line_map[key]["sections"].append(section["label"])

    repeated = [value for value in line_map.values() if value["count"] > 1]
    repeated.sort(key=lambda item: (-item["count"], item["line"].lower()))
    return repeated


def repeated_openings(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    opening_counter: Counter[str] = Counter()
    for section in sections:
        for line in section["lines"]:
            tokens = filtered_tokens(line)
            if not tokens:
                continue
            opening = " ".join(tokens[:2])
            if opening:
                opening_counter[opening] += 1

    results = [
        {"opening": opening, "count": count}
        for opening, count in opening_counter.items()
        if count > 1
    ]
    results.sort(key=lambda item: (-item["count"], item["opening"]))
    return results[:10]


def count_matches(text: str, lexicon: set[str]) -> tuple[int, list[str]]:
    lowered = text.lower()
    matched_terms = sorted(term for term in lexicon if term.lower() in lowered)
    return len(matched_terms), matched_terms


def imagery_matches(text: str) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for tag, lexicon in IMAGERY_LEXICONS.items():
        count, terms = count_matches(text, lexicon)
        if count:
            matches[tag] = {"count": count, "matched_terms": terms}
    return matches


def emotion_matches(text: str) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for emotion, lexicon in EMOTION_LEXICONS.items():
        count, terms = count_matches(text, lexicon)
        if count:
            matches[emotion] = {"count": count, "matched_terms": terms}
    return matches


def line_score_for_hook(line: str, section_label: str, repeat_count: int) -> float:
    token_count = len(filtered_tokens(line))
    imagery_bonus = len(imagery_matches(line))
    emotion_bonus = len(emotion_matches(line))
    chorus_bonus = 2.0 if section_label.startswith("chorus") else 0.0
    short_line_bonus = 2.0 if 2 <= token_count <= 8 else 0.0
    repeat_bonus = repeat_count * 2.5
    punctuation_bonus = 0.5 if any(mark in line for mark in ("!", "?", "!!")) else 0.0
    return chorus_bonus + short_line_bonus + repeat_bonus + imagery_bonus + emotion_bonus + punctuation_bonus


def hook_candidates(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    repeated = {item["line"].lower(): item["count"] for item in repeated_lines(sections)}
    candidates: list[dict[str, Any]] = []

    for section in sections:
        for line in section["lines"]:
            score = line_score_for_hook(line, section["label"], repeated.get(line.lower(), 1))
            if score < 3.0:
                continue
            candidates.append(
                {
                    "line": line,
                    "section": section["label"],
                    "score": round(score, 2),
                    "repeat_count": repeated.get(line.lower(), 1),
                    "token_count": len(filtered_tokens(line)),
                }
            )

    seen: set[str] = set()
    unique_candidates: list[dict[str, Any]] = []
    for item in sorted(candidates, key=lambda entry: (-entry["score"], entry["line"].lower())):
        key = item["line"].lower()
        if key in seen:
            continue
        seen.add(key)
        unique_candidates.append(item)
    return unique_candidates[:8]


def lexical_profile(document: dict[str, Any]) -> dict[str, Any]:
    text = lyric_body_text(document)
    all_tokens = extract_candidate_tokens(text)
    filtered = filtered_tokens(text)
    token_counter = Counter(filtered)
    top_tokens = [{"token": token, "count": count} for token, count in token_counter.most_common(12)]

    pronoun_counter = Counter()
    for token in all_tokens:
        lowered = token.lower() if is_ascii_token(token) else token
        for label, lexicon in PRONOUN_SETS.items():
            if lowered in lexicon:
                pronoun_counter[label] += 1

    ascii_count = sum(1 for token in all_tokens if is_ascii_token(token))
    non_ascii_count = max(len(all_tokens) - ascii_count, 0)
    total_pronouns = sum(pronoun_counter.values())
    line_lengths = [len(line) for section in document["sections"] for line in section["lines"]]

    return {
        "dominant_keywords": top_tokens[:8],
        "top_tokens": top_tokens,
        "unique_token_ratio": round(len(set(filtered)) / len(filtered), 3) if filtered else 0.0,
        "pronoun_profile": {
            "counts": dict(pronoun_counter),
            "dominant_perspective": pronoun_counter.most_common(1)[0][0] if total_pronouns else "undetermined",
            "total_pronoun_mentions": total_pronouns,
        },
        "english_insertion_ratio": round(ascii_count / len(all_tokens), 3) if all_tokens else 0.0,
        "script_balance": {
            "ascii_tokens": ascii_count,
            "japanese_chunks": non_ascii_count,
        },
        "line_length_stats": {
            "average_characters": round(mean(line_lengths), 2) if line_lengths else 0.0,
            "short_line_ratio": round(
                sum(1 for length in line_lengths if length <= 18) / len(line_lengths), 3
            ) if line_lengths else 0.0,
        },
    }


def imagery_profile(document: dict[str, Any]) -> dict[str, Any]:
    text = lyric_body_text(document)
    track_matches = imagery_matches(text)
    sorted_tags = sorted(
        (
            {"tag": tag, "count": payload["count"], "matched_terms": payload["matched_terms"]}
            for tag, payload in track_matches.items()
        ),
        key=lambda item: (-item["count"], item["tag"]),
    )

    contrast_results = []
    lowered = text.lower()
    for left, right in CONTRAST_PAIRS:
        left_terms = sorted(term for term in CONTRAST_TERMS[left] if term.lower() in lowered)
        right_terms = sorted(term for term in CONTRAST_TERMS[right] if term.lower() in lowered)
        if left_terms and right_terms:
            contrast_results.append(
                {"pair": f"{left}_vs_{right}", "left_terms": left_terms, "right_terms": right_terms}
            )

    return {"imagery_tags": sorted_tags, "contrast_pairs": contrast_results}


def classify_intensity(value: int) -> str:
    if value >= 4:
        return "high"
    if value >= 2:
        return "medium"
    if value > 0:
        return "low"
    return "flat"


def infer_arc_label(section_profiles: list[dict[str, Any]]) -> str:
    if not section_profiles:
        return "undetermined"
    first = section_profiles[0]["arousal_score"]
    peak = max(item["arousal_score"] for item in section_profiles)
    last = section_profiles[-1]["arousal_score"]
    bridge_sections = [item for item in section_profiles if item["section"].startswith("bridge")]

    if bridge_sections and bridge_sections[0]["dominant_emotion"] == "vulnerability" and last >= peak:
        return "vulnerable_bridge_then_max_release"
    if peak > first and last >= peak:
        return "steady_build_to_final_release"
    if peak > first:
        return "build_and_drop"
    return "flat_or_circular"


def emotion_profile_by_section(document: dict[str, Any]) -> dict[str, Any]:
    section_profiles: list[dict[str, Any]] = []
    for section in document["sections"]:
        matches = emotion_matches(section["text"])
        counts = {key: value["count"] for key, value in matches.items()}
        dominant_label = max(counts, key=counts.get) if counts else "neutral"
        arousal = counts.get("defiance", 0) + counts.get("motion", 0) + counts.get("tension", 0)
        valence = counts.get("uplift", 0) - counts.get("darkness", 0) - counts.get("vulnerability", 0)
        if section["label"].startswith("chorus"):
            arousal += 1
        if section["label"].startswith("bridge"):
            valence -= 1

        section_profiles.append(
            {
                "section": section["label"],
                "dominant_emotion": dominant_label,
                "emotion_counts": counts,
                "arousal_score": arousal,
                "valence_score": valence,
                "matched_terms": {key: value["matched_terms"] for key, value in matches.items()},
                "intensity_label": classify_intensity(arousal),
            }
        )

    return {"sections": section_profiles, "overall_arc_label": infer_arc_label(section_profiles)}


def infer_section_functions(document: dict[str, Any], emotion_arc: dict[str, Any]) -> list[dict[str, Any]]:
    section_emotions = {item["section"]: item for item in emotion_arc["sections"]}
    functions: list[dict[str, Any]] = []

    for section in document["sections"]:
        label = section["label"]
        base_label = canonical_section_label(label)
        inferred: list[str] = []
        evidence: list[str] = []

        if label.startswith("pre_chorus"):
            inferred.append("escalation")
            evidence.append("section_label=pre_chorus")
        elif base_label in SECTION_FUNCTION_HINTS:
            inferred.append(SECTION_FUNCTION_HINTS[base_label])
            evidence.append(f"section_label={base_label}")

        emotion = section_emotions.get(label, {})
        dominant = emotion.get("dominant_emotion", "neutral")
        if base_label == "intro" and imagery_matches(section["text"]):
            inferred.append("scene_setting")
            evidence.append("imagery_present")
        if base_label == "verse" and len(filtered_tokens(section["text"])) >= 8:
            inferred.append("detail_build")
            evidence.append("lexically_dense")
        if label.startswith("chorus"):
            inferred.append("declaration")
            evidence.append(f"emotion={dominant}")
            if section["line_count"] <= 4:
                inferred.append("chantable_hook")
                evidence.append("short_chorus")
        if label.startswith("bridge"):
            if dominant == "vulnerability":
                inferred.append("vulnerability_drop")
                evidence.append("dominant_vulnerability")
            else:
                inferred.append("perspective_shift")
                evidence.append(f"emotion={dominant}")

        functions.append(
            {
                "section": label,
                "inferred_functions": sorted(set(inferred)),
                "evidence": sorted(set(evidence)),
            }
        )
    return functions


def analyze_track_document(document: dict[str, Any], source_path: Path) -> dict[str, Any]:
    structure = analyze_structure(document)
    repetition = {
        "repeated_lines": repeated_lines(document["sections"]),
        "repeated_openings": repeated_openings(document["sections"]),
    }
    hooks = hook_candidates(document["sections"])
    repetition["hook_candidates"] = hooks
    repetition["chorus_repetition_score"] = round(
        sum(item["repeat_count"] for item in hooks if item["section"].startswith("chorus")) / len(hooks),
        2,
    ) if hooks else 0.0

    lexical = lexical_profile(document)
    imagery = imagery_profile(document)
    emotion_arc = emotion_profile_by_section(document)
    section_functions = infer_section_functions(document, emotion_arc)

    return {
        "schema_version": TRACK_ANALYSIS_VERSION,
        "artist_id": document["artist_id"],
        "artist_name": document["artist_name"],
        "track_id": document["track_id"],
        "title": document["title"],
        "language": document["language"],
        "source_normalized_path": str(source_path),
        "structure": structure,
        "repetition": repetition,
        "lexical": lexical,
        "imagery": imagery,
        "emotion_arc": emotion_arc,
        "section_functions": section_functions,
        "analysis_notes": [
            "V1 heuristic analysis using standard-library token and lexicon rules.",
            "Japanese lexical segmentation is approximate; structure and repeated surface patterns are more reliable than raw token counts.",
        ],
    }


def track_output_path(output_root: Path, analysis: dict[str, Any]) -> Path:
    return output_root / analysis["artist_id"] / f"{analysis['track_id']}.json"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def analyze_tracks(input_root: Path, output_root: Path) -> list[TrackAnalysisSummary]:
    summaries: list[TrackAnalysisSummary] = []
    for path in discover_normalized_documents(input_root):
        document = load_json(path)
        analysis = analyze_track_document(document, path)
        output_path = track_output_path(output_root, analysis)
        write_json(output_path, analysis)
        summaries.append(
            TrackAnalysisSummary(
                output_path=output_path,
                hook_count=len(analysis["repetition"]["hook_candidates"]),
                dominant_imagery_tags=[item["tag"] for item in analysis["imagery"]["imagery_tags"][:3]],
            )
        )
    return summaries


def discover_track_analyses(input_root: Path) -> list[Path]:
    return sorted(
        path
        for path in input_root.rglob("*.json")
        if path.is_file() and "_template" not in path.parts
    )


def common_structures(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter(item["structure"]["structure_pattern"] for item in analyses)
    return [{"pattern": pattern, "count": count} for pattern, count in counter.most_common(8)]


def common_chorus_shapes(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    chorus_lengths: list[int] = []
    chorus_counts: list[int] = []
    repetition_scores: list[float] = []

    for analysis in analyses:
        for section in analysis["structure"]["section_lengths"]:
            if section["label"].startswith("chorus"):
                chorus_lengths.append(section["line_count"])
        chorus_counts.append(analysis["structure"]["chorus_count"])
        repetition_scores.append(analysis["repetition"]["chorus_repetition_score"])

    return {
        "average_chorus_line_count": round(mean(chorus_lengths), 2) if chorus_lengths else 0.0,
        "average_chorus_count": round(mean(chorus_counts), 2) if chorus_counts else 0.0,
        "average_chorus_repetition_score": round(mean(repetition_scores), 2) if repetition_scores else 0.0,
    }


def aggregated_imagery(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    tag_counter: Counter[str] = Counter()
    term_counter: Counter[str] = Counter()
    contrast_counter: Counter[str] = Counter()

    for analysis in analyses:
        for item in analysis["imagery"]["imagery_tags"]:
            tag_counter[item["tag"]] += item["count"]
            for term in item["matched_terms"]:
                term_counter[term] += 1
        for pair in analysis["imagery"]["contrast_pairs"]:
            contrast_counter[pair["pair"]] += 1

    return {
        "top_imagery_clusters": [{"tag": tag, "count": count} for tag, count in tag_counter.most_common(10)],
        "top_imagery_terms": [{"term": term, "count": count} for term, count in term_counter.most_common(12)],
        "top_contrast_pairs": [{"pair": pair, "count": count} for pair, count in contrast_counter.most_common(8)],
    }


def aggregated_hooks(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    hook_counter: Counter[str] = Counter()
    section_counter: Counter[str] = Counter()
    score_values: list[float] = []

    for analysis in analyses:
        for hook in analysis["repetition"]["hook_candidates"]:
            hook_counter[hook["line"]] += 1
            section_counter[hook["section"]] += 1
            score_values.append(hook["score"])

    return {
        "average_hook_score": round(mean(score_values), 2) if score_values else 0.0,
        "hook_examples": [{"line": line, "count": count} for line, count in hook_counter.most_common(8)],
        "common_hook_sections": [{"section": section, "count": count} for section, count in section_counter.most_common(6)],
    }


def aggregated_vocabulary(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    token_counter: Counter[str] = Counter()
    pronoun_counter: Counter[str] = Counter()
    english_ratios: list[float] = []

    for analysis in analyses:
        for token in analysis["lexical"]["top_tokens"]:
            token_counter[token["token"]] += token["count"]
        for label, count in analysis["lexical"]["pronoun_profile"]["counts"].items():
            pronoun_counter[label] += count
        english_ratios.append(analysis["lexical"]["english_insertion_ratio"])

    return {
        "top_tokens": [{"token": token, "count": count} for token, count in token_counter.most_common(15)],
        "pronoun_profile": {
            "counts": dict(pronoun_counter),
            "dominant_perspective": pronoun_counter.most_common(1)[0][0] if pronoun_counter else "undetermined",
        },
        "average_english_insertion_ratio": round(mean(english_ratios), 3) if english_ratios else 0.0,
    }


def aggregated_section_defaults(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: {"functions": Counter(), "emotions": Counter()})

    for analysis in analyses:
        emotion_lookup = {item["section"]: item for item in analysis["emotion_arc"]["sections"]}
        for item in analysis["section_functions"]:
            base_label = canonical_section_label(item["section"])
            for function_name in item["inferred_functions"]:
                grouped[base_label]["functions"][function_name] += 1
            emotion = emotion_lookup.get(item["section"], {}).get("dominant_emotion")
            if emotion:
                grouped[base_label]["emotions"][emotion] += 1

    defaults = []
    for label, counters in grouped.items():
        defaults.append(
            {
                "section": label,
                "common_functions": [{"function": name, "count": count} for name, count in counters["functions"].most_common(4)],
                "common_emotions": [{"emotion": name, "count": count} for name, count in counters["emotions"].most_common(4)],
            }
        )
    defaults.sort(key=lambda item: item["section"])
    return defaults


def candidate_mode_scores(analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    imagery_counter: Counter[str] = Counter()
    arc_counter = Counter(analysis["emotion_arc"]["overall_arc_label"] for analysis in analyses)
    for analysis in analyses:
        for item in analysis["imagery"]["imagery_tags"]:
            imagery_counter[item["tag"]] += item["count"]

    scores = {
        "rebellious_dark": imagery_counter["fracture"] + imagery_counter["noise"] + imagery_counter["night"],
        "night_drive": imagery_counter["night"] + imagery_counter["city"] + imagery_counter["motion"],
        "anthemic_cinematic": imagery_counter["light"] + imagery_counter["motion"] + arc_counter["steady_build_to_final_release"],
        "intimate_confessional": imagery_counter["body"] + arc_counter["build_and_drop"],
    }

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [{"mode": mode, "score": score} for mode, score in ranked if score > 0]


def build_artist_analysis(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    if not analyses:
        raise ValueError("No track analyses were provided.")

    artist_id = analyses[0]["artist_id"]
    artist_name = analyses[0]["artist_name"]
    arc_counter = Counter(item["emotion_arc"]["overall_arc_label"] for item in analyses)

    return {
        "schema_version": ARTIST_ANALYSIS_VERSION,
        "artist_id": artist_id,
        "artist_name": artist_name,
        "language": analyses[0]["language"],
        "track_count": len(analyses),
        "source_track_ids": [item["track_id"] for item in analyses],
        "structural_profile": {
            "common_structures": common_structures(analyses),
            "common_chorus_shapes": common_chorus_shapes(analyses),
        },
        "imagery_profile": aggregated_imagery(analyses),
        "hook_pattern_summary": aggregated_hooks(analyses),
        "vocabulary_profile": aggregated_vocabulary(analyses),
        "emotional_profile": {
            "dominant_arc_patterns": [{"arc": arc, "count": count} for arc, count in arc_counter.most_common(6)],
        },
        "section_role_defaults": aggregated_section_defaults(analyses),
        "mode_candidates": candidate_mode_scores(analyses),
        "analysis_notes": [
            "Artist analysis aggregates per-track heuristic evidence.",
            "Mode candidates are corpus-derived style lanes, not final production modes.",
        ],
    }


def artist_output_path(output_root: Path, artist_id: str) -> Path:
    return output_root / f"{artist_id}.json"


def aggregate_artist_analyses(track_analysis_root: Path, output_root: Path) -> list[ArtistAnalysisSummary]:
    by_artist: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in discover_track_analyses(track_analysis_root):
        analysis = load_json(path)
        by_artist[analysis["artist_id"]].append(analysis)

    summaries: list[ArtistAnalysisSummary] = []
    for artist_id, analyses in sorted(by_artist.items()):
        artist_analysis = build_artist_analysis(analyses)
        output_path = artist_output_path(output_root, artist_id)
        write_json(output_path, artist_analysis)
        summaries.append(
            ArtistAnalysisSummary(
                output_path=output_path,
                track_count=artist_analysis["track_count"],
                dominant_modes=[item["mode"] for item in artist_analysis["mode_candidates"][:3]],
            )
        )
    return summaries

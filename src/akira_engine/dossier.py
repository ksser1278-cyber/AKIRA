from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .intent import load_json, load_jsonl
from .training_data import infer_song_form


SECTION_BUCKETS = (
    "intro",
    "verse",
    "pre_chorus",
    "chorus",
    "bridge",
    "interlude",
    "outro",
)
CONTRAST_HINTS = {
    "narrative_anchor_anthem": "公的な視点と私的な葛藤のコントラスト",
    "scene_intensifier": "圧縮された情景描写とサビでの爆発的な解放",
    "brand_hook_driver": "短尺での鮮烈な印象と感情の摩擦",
    "crossover_spotlight": "スポットライト的な存在感とアイデン티ティの揺らぎ",
    "inner_confession": "密室的な脆弱さとサ비での強い訴求",
    "night_drive_momentum": "冷めた疾走感と止まらない内面の動悸",
    "pressure_release": "ヴァースの閉塞感とサビでの一気な決壊",
    "anthemic_release": "開かれた旋律の浮遊感と解消されない内面の摩擦",
    "artist_core_statement": "記号的な自己提示と不安定な情動の同居",
}
PRESERVE_HINTS = {
    "narrative_anchor_anthem": [
        "瞬発的なフックの明瞭さ",
        "公的なサビのスケール感",
        "世界観の視認性",
    ],
    "scene_intensifier": [
        "解放前の緊張状態",
        "サビ突入時の衝撃",
        "情景への感情の圧縮",
    ],
    "brand_hook_driver": [
        "冒頭での記憶への定着",
        "明確なリズムの記号化",
        "セクションの無駄のない構成",
    ],
    "crossover_spotlight": [
        "スポットライト的な対比",
        "アイデンティティを保ったリードフレーズ",
        "イベント的なエネルギー",
    ],
    "inner_confession": [
        "抑えられたヴァースの密室感",
        "独白としての響き",
        "脆さを失わないサビの広がり",
    ],
    "night_drive_momentum": [
        "一定のパルス感",
        "前方への推進力",
        "夜の静かな緊張感",
    ],
    "pressure_release": [
        "サビ前の感情の圧縮",
        "一気に溢れ出す情動",
        "ヴァースとサビの明確なダイナミクス",
    ],
    "anthemic_release": [
        "広がりある旋律の浮遊感",
        "繰り返されるフックの陶酔",
        "終盤に向けての解放感",
    ],
    "artist_core_statement": [
        "アーティスト固有のフック",
        "特徴的な緊張感のパレット",
        "記号化されたペルソナ",
    ],
}
AVOID_HINTS = {
    "narrative_anchor_anthem": [
        "小規模で沈んだサビを避ける",
        "平坦なページングを避ける",
    ],
    "scene_intensifier": [
        "長すぎるイントロを避ける",
        "感情的に中立なサビを避ける",
    ],
    "brand_hook_driver": [
        "後半の形骸化を避ける",
        "アイデンティティの提示を遅らせる遅い展開を避ける",
    ],
    "crossover_spotlight": [
        "ボーカルの個性を隠す過剰な装飾を避ける",
    ],
    "inner_confession": [
        "完全に切り離された客観的な視点を避ける",
    ],
    "night_drive_momentum": [
        "停滞したリズムを避ける",
        "サビでの解放感不足を避ける",
    ],
    "pressure_release": [
        "ヴァースとサビの強弱差がない展開を避ける",
    ],
    "anthemic_release": [
        "迫力不足のラストサビを避ける",
    ],
    "artist_core_statement": [
        "汎用的なJ-POPのテンプレートを避ける",
    ],
}


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    return path


def section_bucket(label: str) -> str:
    if label.startswith("pre_chorus"):
        return "pre_chorus"
    if label.startswith("chorus"):
        return "chorus"
    if label.startswith("verse"):
        return "verse"
    if label.startswith("bridge"):
        return "bridge"
    if label.startswith("intro"):
        return "intro"
    if label.startswith("outro"):
        return "outro"
    return "interlude"


def overall_arc_steps(arc_label: str) -> list[str]:
    if arc_label == "build_and_drop":
        return [
            "プレッシャーの蓄積",
            "サビでの解放",
            "新たな緊張の発生",
            "最終的な決壊",
        ]
    if arc_label == "steady_build_to_final_release":
        return [
            "抑制された始まり",
            "段階的な高揚",
            "ラストでの最大解放",
        ]
    return [
        "循環する動悸",
        "回帰するフックの圧力",
        "終わりなき帰還",
    ]


def narrative_stance(intent_label: str, dominant_emotions: list[str]) -> str:
    emotion_text = ", ".join(dominant_emotions) if dominant_emotions else "複雑な緊張感"
    if intent_label == "inner_confession":
        return f"{emotion_text}に基づいた内面的な一人称の告白"
    if intent_label == "narrative_anchor_anthem":
        return f"{emotion_text}を背負った、公的な視点を持つフック重視のスタンス"
    if intent_label == "scene_intensifier":
        return f"{emotion_text}によって形作られた、ドラマティックで衝撃的な語り"
    if intent_label == "night_drive_momentum":
        return f"{emotion_text}を伴う、前方へ突き進むような疾走感のある声"
    if intent_label == "pressure_release":
        return f"{emotion_text}を通じて一気に破壊・解放される圧縮された声"
    return f"{emotion_text}に繋がれた、アーティスト性を前景化したスタンス"


def group_sections(
    inferred_song_form: dict[str, Any],
    normalized_doc: dict[str, Any],
    track_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    normalized_sections = {
        section["label"]: section
        for section in normalized_doc.get("sections", [])
    }
    emotion_sections = {
        section["section"]: section
        for section in track_analysis.get("emotion_arc", {}).get("sections", [])
    }
    chorus_anchors = set(inferred_song_form.get("chorus_anchor_sections", []))

    grouped: list[dict[str, Any]] = []
    current_group: dict[str, Any] | None = None

    for item in inferred_song_form.get("ordered_sections", []):
        inferred_label = item.get("inferred_label", "")
        bucket = section_bucket(inferred_label)
        source_section = item.get("source_section", "")
        normalized_section = normalized_sections.get(source_section, {})
        emotion_section = emotion_sections.get(source_section, {})

        if current_group is None or current_group["bucket"] != bucket:
            current_group = {
                "bucket": bucket,
                "source_sections": [],
                "line_total": 0,
                "max_line_count": 0,
                "dominant_emotions": [],
                "intensity_labels": [],
                "hook_anchor_count": 0,
            }
            grouped.append(current_group)

        current_group["source_sections"].append(source_section)
        line_count = int(normalized_section.get("line_count", item.get("line_count", 0)))
        current_group["line_total"] += line_count
        current_group["max_line_count"] = max(current_group["max_line_count"], line_count)
        dominant_emotion = emotion_section.get("dominant_emotion")
        if dominant_emotion and dominant_emotion != "neutral":
            current_group["dominant_emotions"].append(dominant_emotion)
        intensity_label = emotion_section.get("intensity_label")
        if intensity_label and intensity_label != "flat":
            current_group["intensity_labels"].append(intensity_label)
        if source_section in chorus_anchors:
            current_group["hook_anchor_count"] += 1

    counters = {bucket: 0 for bucket in SECTION_BUCKETS}
    section_entries: list[dict[str, Any]] = []
    for index, group in enumerate(grouped):
        bucket = group["bucket"]
        counters[bucket] += 1
        is_last = index == len(grouped) - 1
        is_final_chorus = bucket == "chorus" and is_last
        if bucket == "chorus" and is_final_chorus:
            label = "chorus_final"
        elif counters[bucket] == 1:
            label = bucket if bucket not in {"verse", "chorus"} else f"{bucket}_1"
        else:
            label = f"{bucket}_{counters[bucket]}"

        section_entries.append(
            {
                "section": label,
                "section_bucket": bucket,
                "source_sections": group["source_sections"],
                "line_total": group["line_total"],
                "max_line_count": group["max_line_count"],
                "dominant_emotions": list(dict.fromkeys(group["dominant_emotions"]))[:3],
                "intensity_shape": list(dict.fromkeys(group["intensity_labels"]))[:3],
                "hook_anchor_count": group["hook_anchor_count"],
                "is_final_chorus": is_final_chorus,
            }
        )
    return section_entries


def section_function(entry: dict[str, Any], intent_label: str) -> str:
    bucket = entry["section_bucket"]
    if bucket == "intro":
        return "物語が動き出す前の感情的な枠組みを提示し、不穏さや期待感を置く。"
    if bucket == "verse":
        return "具体的な情景や違和感を提示し、不穏な空気や圧力を高める。語り手の立ち位置を確定させる。"
    if bucket == "pre_chorus":
        return "情動を圧縮し、サビに向けて逃げ場のない滑走路を作り上げる。"
    if bucket == "chorus" and entry["is_final_chorus"]:
        return "最大の解放を行い、核心となる誓いや絶望を最も鮮明に提示する（最大視認性）。"
    if bucket == "chorus":
        return "核心となるフックを叩きつけ、楽曲の中心概念を反復可能な形で定着させる。"
    if bucket == "bridge":
        return "視点を変え、代償を強調し、あるいは最後の解放に向けてエネルギーを再構築する。"
    if bucket == "outro":
        return "完全な結末を置かず、不確かな残響や後味を残す。"
    return "主要な感情ブロックの間を繋ぐ、接続的な素材を提示する。"


def section_arrangement_intent(entry: dict[str, Any], intent_label: str) -> str:
    bucket = entry["section_bucket"]
    if bucket == "verse":
        if intent_label == "inner_confession":
            return "音を抑制し、ボーカルが感情の解釈をリードするように構成する。"
        if intent_label == "night_drive_momentum":
            return "一定のパルスを維持し、ピークのエネルギーを温存しつつ推進力を保つ。"
        return "フックでの解放に備え、音を制御し、物語を前景化させる。"
    if bucket == "pre_chorus":
        return "質感を削ぎ落とすか圧縮し、解放直前の緊張状態を作り上げる。"
    if bucket == "chorus" and entry["is_final_chorus"]:
        return "アレンジを最大まで開き、最後のフレーズが不可避であるかのように響かせる。"
    if bucket == "chorus":
        return "フックのエネルギーが最も鮮明に届くよう、最大のコントラストを付ける。"
    if bucket == "bridge":
        return "エネルギーの向きを変え、停滞させることなく最後の回帰に向けて準備する。"
    if bucket == "outro":
        return "質感を段階的に減らし、未解消の残響を残す。"
    return "フックの存在感を損なうことなく、接続的な役割を果たす。"


def section_dynamic_role(entry: dict[str, Any]) -> str:
    bucket = entry["section_bucket"]
    if bucket == "pre_chorus":
        return "感情の圧縮"
    if bucket == "chorus" and entry["is_final_chorus"]:
        return "最大解放 (ピーク)"
    if bucket == "chorus":
        return "情動の解放"
    if bucket == "bridge":
        return "エネルギーの再構築"
    if bucket == "outro":
        return "不確かな残響"
    if bucket == "intro":
        return "枠組みの提示"
    return "抑制された推進力"


def section_rhetorical_pattern(entry: dict[str, Any]) -> str:
    bucket = entry["section_bucket"]
    if bucket == "verse":
        return "出来事・圧力 -> 反応 -> 内面的な読み替え"
    if bucket == "pre_chorus":
        return "資格の喪失 -> 圧縮された疑念 -> 解放ポイントへの疾走"
    if bucket == "chorus":
        return "フックの宣誓 -> 世界の再解釈 -> 繰り返される誓い"
    if bucket == "bridge":
        return "視点の転換 -> 非情な真実 -> 最後の執着"
    if bucket == "outro":
        return "剰余、あるいは解消されない木霊"
    return "接続的な移行運動"


def metadata_gaps(record: dict[str, Any]) -> list[str]:
    gaps = ["bpm", "key", "runtime", "instrumentation"]
    if record.get("metadata_intent", {}).get("spotify_release_context", {}).get("first_release_date"):
        gaps.remove("runtime") if "runtime" in gaps and False else None
    return gaps


def build_style_prompt_seed(record: dict[str, Any], section_entries: list[dict[str, Any]], contrast: str) -> str:
    hints = record.get("suno_conditioning_hints", {})
    purpose = record.get("creative_intent", {}).get("purpose_statement", "")
    chorus_count = sum(1 for entry in section_entries if entry["section_bucket"] == "chorus")
    structure_text = "multiple chorus returns" if chorus_count >= 2 else "a direct single-peak form"
    return (
        f"{hints.get('arrangement_direction', 'hook-forward arrangement')}. "
        f"{hints.get('vocal_direction', 'clear lead vocal focus')}. "
        f"{hints.get('energy_arc', 'clear sectional lift')}. "
        f"Use {structure_text} and preserve the contrast of {contrast}. "
        f"Song job: {purpose}"
    )


def dossier_record(intent_record: dict[str, Any]) -> dict[str, Any]:
    normalized_doc = load_json(Path(intent_record["source_paths"]["normalized_document"]))
    track_analysis = load_json(Path(intent_record["source_paths"]["track_analysis"]))
    inferred_song_form = infer_song_form(normalized_doc, track_analysis)
    section_entries = group_sections(inferred_song_form, normalized_doc, track_analysis)

    intent_label = intent_record["creative_intent"]["intent_label"]
    contrast = CONTRAST_HINTS.get(intent_label, "stable melodic frame versus unstable emotion")
    release_date = intent_record["metadata_intent"]["spotify_release_context"].get("first_release_date")
    dominant_emotions = intent_record["lyric_intent_signals"].get("emotion_tags", [])

    return {
        "schema_version": "1.0",
        "track_id": intent_record["track_id"],
        "artist_id": intent_record["artist_id"],
        "track_identity": {
            "title": intent_record["title"],
            "title_core": intent_record["title_core"],
            "release_year": int(str(release_date)[:4]) if release_date else None,
            "bpm": None,
            "key": None,
            "runtime": None,
            "instrumentation": [],
            "metadata_gaps": ["bpm", "key", "runtime", "instrumentation"],
        },
        "high_level_intent": {
            "intent_label": intent_label,
            "core_purpose": intent_record["creative_intent"]["purpose_statement"],
            "song_job": intent_record["creative_intent"]["audience_job"],
            "contrast_device": contrast,
            "dramatic_arc": overall_arc_steps(
                track_analysis.get("emotion_arc", {}).get("overall_arc_label", "flat_or_circular")
            ),
            "narrative_stance": narrative_stance(intent_label, dominant_emotions),
            "tie_in_context": intent_record["metadata_intent"]["title_annotations"],
        },
        "section_dossier": [
            {
                **entry,
                "function": section_function(entry, intent_label),
                "arrangement_intent": section_arrangement_intent(entry, intent_label),
                "dynamic_role": section_dynamic_role(entry),
                "rhetorical_pattern": section_rhetorical_pattern(entry),
            }
            for entry in section_entries
        ],
        "distilled_conditioning": {
            "purpose_axes": intent_record["creative_intent"].get("purpose_axes", []),
            "style_prompt_seed": build_style_prompt_seed(intent_record, section_entries, contrast),
            "preserve": PRESERVE_HINTS.get(intent_label, []),
            "avoid": AVOID_HINTS.get(intent_label, []),
            "suno_conditioning_hints": intent_record.get("suno_conditioning_hints", {}),
        },
        "quality_flags": {
            "curation_recommendation": intent_record.get("curation_recommendation"),
            "caution_flags": intent_record.get("training_value", {}).get("caution_flags", []),
            "ready_for_conditioning": intent_record.get("training_value", {}).get("ready_for_conditioning", False),
            "auto_generated": True,
            "manual_enrichment_recommended_for": ["bpm", "key", "runtime", "instrumentation"],
        },
    }


def render_dossier_report(manifest: dict[str, Any], records: list[dict[str, Any]]) -> str:
    lines = [
        f"# Track Dossier Report: {manifest['artist_id']}",
        "",
        f"- Dossier count: `{manifest['record_count']}`",
        f"- Ready for conditioning: `{manifest['ready_for_conditioning_count']}`",
        f"- Release year coverage: `{manifest['release_year_coverage']}`",
        f"- Intent labels: `{manifest['intent_label_counts']}`",
        f"- Average section dossier count: `{manifest['average_section_count']}`",
        "",
        "## Why This Is Higher-Value Than Raw",
        "",
        "- each track is represented as a reusable song-purpose dossier, not a scrape file",
        "- track-level intent, contrast, section function, and conditioning hints are stored together",
        "- the record keeps explicit metadata gaps so missing audio facts can be filled later",
        "",
        "## Example Records",
        "",
    ]
    for record in records[:10]:
        lines.append(
            f"- `{record['track_id']}` / `{record['track_identity']['title_core']}`: "
            f"`{record['high_level_intent']['intent_label']}` / "
            f"{record['high_level_intent']['contrast_device']}"
        )
    return "\n".join(lines)


def build_track_dossiers(
    project_root: Path,
    artist_id: str,
    *,
    intent_root: Path,
    output_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    intent_path = intent_root / artist_id / "track_intent_cards.jsonl"
    if not intent_path.exists():
        raise FileNotFoundError(f"Intent records not found: {intent_path}")

    intent_records = load_jsonl(intent_path)
    records = [dossier_record(record) for record in intent_records]

    intent_label_counts = Counter(record["high_level_intent"]["intent_label"] for record in records)
    ready_for_conditioning_count = sum(1 for record in records if record["quality_flags"]["ready_for_conditioning"])
    release_year_coverage = sum(1 for record in records if record["track_identity"]["release_year"] is not None)
    average_section_count = round(
        sum(len(record["section_dossier"]) for record in records) / max(1, len(records)),
        2,
    )

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "record_count": len(records),
        "ready_for_conditioning_count": ready_for_conditioning_count,
        "release_year_coverage": f"{release_year_coverage}/{len(records)}",
        "intent_label_counts": dict(intent_label_counts),
        "average_section_count": average_section_count,
        "intent_records_path": str(intent_path),
    }

    artist_out_dir = output_root / artist_id
    records_path = write_jsonl(artist_out_dir / "track_dossiers.jsonl", records)
    manifest_path = write_json(artist_out_dir / "track_dossier_manifest.json", manifest)
    report_path = report_root / f"{artist_id}_track_dossier_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_dossier_report(manifest, records), encoding="utf-8")

    manifest["records_path"] = str(records_path)
    manifest["manifest_path"] = str(manifest_path)
    manifest["report_path"] = str(report_path)
    return manifest

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .spotify import candidate_base_titles, normalize_title
from .training_data import dominant_emotions, hook_strategy, sanitized_imagery_tags


ANNOTATION_PATTERN = re.compile(r"[\(\（\[\【]([^\)\）\]\】]+)[\)\）\]\】]")
QUOTED_WORK_PATTERN = re.compile(r"[「『【](.+?)[」』】]")
FEAT_PATTERN = re.compile(r"\b(feat\.?|with|duet)\b", re.IGNORECASE)

USAGE_ROLE_RULES = [
    ("opening_theme", ("オープニングテーマ", "opening theme", "オープニング")),
    ("ending_theme", ("エンディングテーマ", "ending theme", "エンディング")),
    ("insert_song", ("挿入歌", "insert song")),
    ("theme_song", ("主題歌", "theme song")),
    ("image_song", ("イメージソング", "image song")),
    ("commercial_song", ("cmソング", "commercial song", "タイアップソング")),
]
MEDIA_TYPE_RULES = [
    ("anime", ("tvアニメ", "アニメ", "anime")),
    ("film", ("映画", "film", "movie")),
    ("drama", ("ドラマ", "drama")),
    ("game", ("ゲーム", "game")),
    ("commercial", ("cm", "commercial")),
    ("stage", ("舞台", "stage")),
    ("broadcast", ("番組", "program")),
]
INTENT_PROFILES = {
    "narrative_anchor_anthem": {
        "purpose_statement": "Built to front a story world or campaign with an immediate, high-visibility hook.",
        "audience_job": "Open the world big and make the title feel instantly iconic.",
        "style_prompt_hints": {
            "arrangement_direction": "cinematic scale, clear hook entry, wide chorus lift",
            "vocal_direction": "confident lead that can turn declarative quickly",
            "energy_arc": "arrive fast, keep momentum, open the final chorus widest",
        },
    },
    "scene_intensifier": {
        "purpose_statement": "Designed to magnify a specific dramatic scene or emotional turning point.",
        "audience_job": "Push the listener deeper into one scene-defining emotional peak.",
        "style_prompt_hints": {
            "arrangement_direction": "focused impact, scene tension, clean emotional release",
            "vocal_direction": "emotion-forward delivery with sudden lift points",
            "energy_arc": "hold tension, then snap open at the scene peak",
        },
    },
    "brand_hook_driver": {
        "purpose_statement": "Engineered to deliver a compact, memorable hook for a branded or promotional context.",
        "audience_job": "Leave a sharp sonic signature fast without wasting setup time.",
        "style_prompt_hints": {
            "arrangement_direction": "tight runtime feel, punchy groove, bright recognisable accents",
            "vocal_direction": "direct phrasing and strong front-loaded hook delivery",
            "energy_arc": "hook early, repeat cleanly, avoid overlong intros",
        },
    },
    "crossover_spotlight": {
        "purpose_statement": "Made to balance the artist identity with a featured or crossover frame.",
        "audience_job": "Keep the core voice clear while making the collaboration feel event-like.",
        "style_prompt_hints": {
            "arrangement_direction": "feature-friendly spacing, spotlight moments, contrast-friendly sections",
            "vocal_direction": "identity-forward lead with room for guest contrast",
            "energy_arc": "alternate spotlight and convergence",
        },
    },
    "inner_confession": {
        "purpose_statement": "Focused on private emotional disclosure rather than spectacle.",
        "audience_job": "Pull the listener inside a close, inward monologue that still blooms in the hook.",
        "style_prompt_hints": {
            "arrangement_direction": "close-mic intimacy, restrained verses, emotionally widening chorus",
            "vocal_direction": "breathy or fragile verses with stronger release in the chorus",
            "energy_arc": "quiet pressure to emotional opening",
        },
    },
    "night_drive_momentum": {
        "purpose_statement": "Built for motion, pulse, and nocturnal forward pressure.",
        "audience_job": "Keep the song moving with a sense of late-night velocity and cool tension.",
        "style_prompt_hints": {
            "arrangement_direction": "steady pulse, nocturnal low-end motion, neon synth or guitar edge",
            "vocal_direction": "controlled urgency with forward-pushing phrasing",
            "energy_arc": "constant forward motion with measured release",
        },
    },
    "pressure_release": {
        "purpose_statement": "Designed to accumulate internal pressure and crack it open in the hook.",
        "audience_job": "Make the listener feel compression, then catharsis.",
        "style_prompt_hints": {
            "arrangement_direction": "tense verses, rising pre-chorus pressure, explosive chorus opening",
            "vocal_direction": "tight delivery that can break into a harder release",
            "energy_arc": "compress, sharpen, burst",
        },
    },
    "anthemic_release": {
        "purpose_statement": "Aimed at collective lift and large-scale release rather than subtle interiority.",
        "audience_job": "Give the chorus a broad, rallying feeling that pays off repeated hooks.",
        "style_prompt_hints": {
            "arrangement_direction": "anthemic lift, bright impact, clear final chorus expansion",
            "vocal_direction": "projected, strong, hook-first lead",
            "energy_arc": "build clearly into a large final payoff",
        },
    },
    "artist_core_statement": {
        "purpose_statement": "Functions as a core artist-definition track more than a tie-in utility song.",
        "audience_job": "Show recognizable identity signals without depending on external narrative framing.",
        "style_prompt_hints": {
            "arrangement_direction": "identity-forward production palette, distinctive hook framing",
            "vocal_direction": "signature delivery and memorable tonal contrast",
            "energy_arc": "let the core persona define the motion",
        },
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    return path


def spotify_snapshot_path(project_root: Path, artist_id: str) -> Path | None:
    candidate = project_root / "data" / "spotify" / f"{artist_id}_discography.json"
    return candidate if candidate.exists() else None


def build_spotify_index(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for track in snapshot.get("canonical_tracks", []):
        keys = set(candidate_base_titles(track.get("name", "")))
        normalized_name = normalize_title(track.get("normalized_name", "") or track.get("name", ""))
        if normalized_name:
            keys.add(normalized_name)
        for key in keys:
            if key and key not in index:
                index[key] = track
    return index


def annotation_segments(title: str) -> list[str]:
    return [segment.strip() for segment in ANNOTATION_PATTERN.findall(str(title)) if segment.strip()]


def quoted_work_names(text: str) -> list[str]:
    return [match.strip() for match in QUOTED_WORK_PATTERN.findall(text) if match.strip()]


def detect_rule_hits(text: str, rules: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    lowered = str(text).lower()
    hits: list[str] = []
    for label, markers in rules:
        if any(marker.lower() in lowered for marker in markers):
            hits.append(label)
    return hits


def parse_title_intent(title: str, *, fallback_texts: list[str] | None = None) -> dict[str, Any]:
    text_candidates = [str(title), *(fallback_texts or [])]
    segments: list[str] = []
    for text in text_candidates:
        segments.extend(annotation_segments(text))
    joined = " ".join([*text_candidates, *segments])
    usage_roles = detect_rule_hits(joined, USAGE_ROLE_RULES)
    media_types = detect_rule_hits(joined, MEDIA_TYPE_RULES)
    work_names = []
    for segment in segments or text_candidates:
        work_names.extend(quoted_work_names(segment))
    seen_work_names: list[str] = []
    for name in work_names:
        if name not in seen_work_names:
            seen_work_names.append(name)
    return {
        "annotation_segments": segments,
        "usage_roles": usage_roles,
        "media_types": media_types,
        "work_names": seen_work_names,
        "has_tie_in": bool(usage_roles or media_types or seen_work_names),
    }


def find_spotify_track(title_core: str, full_title: str, spotify_index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    keys = []
    keys.extend(candidate_base_titles(title_core))
    keys.extend(candidate_base_titles(full_title))
    for key in keys:
        if key in spotify_index:
            return spotify_index[key]
    return None


def collaboration_info(title: str, spotify_track: dict[str, Any] | None) -> dict[str, Any]:
    candidates = [str(title)]
    if spotify_track:
        candidates.append(str(spotify_track.get("name", "")))
    matched = next((candidate for candidate in candidates if FEAT_PATTERN.search(candidate)), "")
    return {
        "is_collaboration": bool(matched),
        "matched_text": matched,
    }


def release_context(spotify_track: dict[str, Any] | None) -> dict[str, Any]:
    if not spotify_track:
        return {
            "available": False,
            "first_release_date": None,
            "album_titles": [],
            "release_shape": "unknown",
        }

    album_titles = list(spotify_track.get("albums", []))
    name = str(spotify_track.get("name", ""))
    normalized_name = normalize_title(name)
    release_shape = "catalog_track"
    if album_titles and normalize_title(album_titles[0]) == normalized_name:
        release_shape = "title_single"
    elif len(album_titles) == 1:
        release_shape = "single_or_compilation_entry"

    return {
        "available": True,
        "first_release_date": spotify_track.get("first_release_date"),
        "album_titles": album_titles,
        "release_shape": release_shape,
    }


def choose_intent_label(
    *,
    title_intent: dict[str, Any],
    collaboration: dict[str, Any],
    imagery_tags: list[str],
    emotion_tags: list[str],
    hook_plan: dict[str, Any],
) -> str:
    usage_roles = set(title_intent.get("usage_roles", []))
    media_types = set(title_intent.get("media_types", []))
    imagery = set(imagery_tags)
    emotions = set(emotion_tags)

    if collaboration.get("is_collaboration"):
        return "crossover_spotlight"
    if usage_roles & {"opening_theme", "ending_theme", "theme_song"}:
        return "narrative_anchor_anthem"
    if usage_roles & {"insert_song", "image_song"}:
        return "scene_intensifier"
    if usage_roles & {"commercial_song"} or "commercial" in media_types:
        return "brand_hook_driver"
    if {"vulnerability"} & emotions and {"body", "night", "light"} & imagery:
        return "inner_confession"
    if {"motion"} & emotions and {"night", "city", "motion"} & imagery:
        return "night_drive_momentum"
    if {"defiance", "tension"} & emotions and {"fracture", "noise", "fire"} & imagery:
        return "pressure_release"
    if hook_plan.get("hook_density") == "high" and {"uplift", "motion"} & emotions:
        return "anthemic_release"
    return "artist_core_statement"


def purpose_axes(intent_label: str, title_intent: dict[str, Any], imagery_tags: list[str], emotion_tags: list[str]) -> list[str]:
    axes: list[str] = []
    if title_intent.get("usage_roles"):
        axes.extend(title_intent["usage_roles"][:2])
    elif title_intent.get("media_types"):
        axes.extend(title_intent["media_types"][:1])
    axes.append(intent_label)
    axes.extend(imagery_tags[:2])
    axes.extend(emotion_tags[:2])
    seen: list[str] = []
    for axis in axes:
        if axis and axis not in seen:
            seen.append(axis)
    return seen


def intent_record(
    *,
    curated_record: dict[str, Any],
    normalized_doc: dict[str, Any],
    track_analysis: dict[str, Any] | None,
    spotify_track: dict[str, Any] | None,
) -> dict[str, Any]:
    title = str(curated_record.get("title", normalized_doc.get("title", "")))
    title_core = str(curated_record.get("title_core", normalized_doc.get("title", "")))
    title_intent = parse_title_intent(title, fallback_texts=[title_core, str(normalized_doc.get("title", ""))])
    collaboration = collaboration_info(title, spotify_track)
    imagery_tags = sanitized_imagery_tags(track_analysis or {}, limit=4) if track_analysis else []
    emotion_tags = dominant_emotions(track_analysis or {}, limit=3) if track_analysis else []
    hook_plan = hook_strategy(track_analysis or {}) if track_analysis else {"hook_density": "low"}
    intent_label = choose_intent_label(
        title_intent=title_intent,
        collaboration=collaboration,
        imagery_tags=imagery_tags,
        emotion_tags=emotion_tags,
        hook_plan=hook_plan,
    )
    intent_profile = INTENT_PROFILES[intent_label]
    inferred_structure = curated_record.get("inferred_structure", {})

    return {
        "track_id": curated_record["track_id"],
        "artist_id": curated_record["artist_id"],
        "title": title,
        "title_core": title_core,
        "curation_recommendation": curated_record.get("recommendation", "needs_review"),
        "source_paths": {
            "normalized_document": curated_record.get("normalized_path", ""),
            "track_analysis": curated_record.get("track_analysis_path", ""),
            "spotify_snapshot": curated_record.get("spotify_snapshot_path", ""),
        },
        "metadata_intent": {
            "title_annotations": title_intent,
            "spotify_release_context": release_context(spotify_track),
            "collaboration": collaboration,
        },
        "creative_intent": {
            "intent_label": intent_label,
            "purpose_statement": intent_profile["purpose_statement"],
            "audience_job": intent_profile["audience_job"],
            "purpose_axes": purpose_axes(intent_label, title_intent, imagery_tags, emotion_tags),
        },
        "lyric_intent_signals": {
            "imagery_tags": imagery_tags,
            "emotion_tags": emotion_tags,
            "hook_plan": hook_plan,
            "inferred_structure": inferred_structure,
        },
        "suno_conditioning_hints": {
            **intent_profile["style_prompt_hints"],
            "structure_bias": (
                "use clear chorus payoffs"
                if inferred_structure.get("chorus_anchor_count", 0) >= 2
                else "keep the structure direct and uncluttered"
            ),
        },
        "training_value": {
            "ready_for_conditioning": curated_record.get("recommendation") == "ready",
            "should_use_for_style_prompt_selection": curated_record.get("recommendation") != "reject",
            "caution_flags": list(curated_record.get("issues", [])),
        },
    }


def render_intent_report(manifest: dict[str, Any], records: list[dict[str, Any]]) -> str:
    lines = [
        f"# Track Intent Report: {manifest['artist_id']}",
        "",
        f"- Record count: `{manifest['record_count']}`",
        f"- Ready for conditioning: `{manifest['ready_for_conditioning_count']}`",
        f"- Tie-in detected: `{manifest['tie_in_count']}`",
        f"- Collaboration detected: `{manifest['collaboration_count']}`",
        f"- Intent labels: `{manifest['intent_label_counts']}`",
        f"- Usage roles: `{manifest['usage_role_counts']}`",
        "",
        "## Example Cards",
        "",
    ]
    example_records = records[:12]
    if not example_records:
        lines.append("- none")
    else:
        for record in example_records:
            lines.append(
                f"- `{record['track_id']}` / `{record['title_core']}`: "
                f"`{record['creative_intent']['intent_label']}` / "
                f"{record['creative_intent']['purpose_statement']}"
            )
    return "\n".join(lines)


def build_track_intent_cards(
    project_root: Path,
    artist_id: str,
    *,
    curated_root: Path,
    output_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    curated_path = curated_root / artist_id / "curated_tracks.jsonl"
    if not curated_path.exists():
        raise FileNotFoundError(f"Curated records not found: {curated_path}")

    curated_records = load_jsonl(curated_path)
    spotify_path = spotify_snapshot_path(project_root, artist_id)
    spotify_snapshot = load_json(spotify_path) if spotify_path else {}
    spotify_index = build_spotify_index(spotify_snapshot)

    records: list[dict[str, Any]] = []
    for curated_record in curated_records:
        normalized_path = Path(curated_record["normalized_path"])
        normalized_doc = load_json(normalized_path)
        track_analysis_path = curated_record.get("track_analysis_path", "")
        track_analysis = load_json(Path(track_analysis_path)) if track_analysis_path else None
        spotify_track = find_spotify_track(curated_record.get("title_core", ""), curated_record.get("title", ""), spotify_index)
        record = intent_record(
            curated_record={
                **curated_record,
                "spotify_snapshot_path": str(spotify_path) if spotify_path else "",
            },
            normalized_doc=normalized_doc,
            track_analysis=track_analysis,
            spotify_track=spotify_track,
        )
        records.append(record)

    intent_label_counts = Counter(record["creative_intent"]["intent_label"] for record in records)
    usage_role_counts = Counter(
        role
        for record in records
        for role in record["metadata_intent"]["title_annotations"].get("usage_roles", [])
    )
    tie_in_count = sum(1 for record in records if record["metadata_intent"]["title_annotations"].get("has_tie_in"))
    collaboration_count = sum(1 for record in records if record["metadata_intent"]["collaboration"].get("is_collaboration"))
    ready_for_conditioning_count = sum(1 for record in records if record["training_value"]["ready_for_conditioning"])

    manifest = {
        "schema_version": "1.0",
        "artist_id": artist_id,
        "record_count": len(records),
        "ready_for_conditioning_count": ready_for_conditioning_count,
        "tie_in_count": tie_in_count,
        "collaboration_count": collaboration_count,
        "intent_label_counts": dict(intent_label_counts),
        "usage_role_counts": dict(usage_role_counts),
        "spotify_snapshot_path": str(spotify_path) if spotify_path else None,
        "curated_records_path": str(curated_path),
    }

    artist_out_dir = output_root / artist_id
    records_path = write_jsonl(artist_out_dir / "track_intent_cards.jsonl", records)
    manifest_path = write_json(artist_out_dir / "intent_manifest.json", manifest)
    report_path = report_root / f"{artist_id}_track_intent_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_intent_report(manifest, records), encoding="utf-8")

    manifest["records_path"] = str(records_path)
    manifest["intent_manifest_path"] = str(manifest_path)
    manifest["report_path"] = str(report_path)
    return manifest

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .lyric_draft import extract_title
from .style_prompt_content import resolve_style_prompt_content
from .text_quality import japanese_markdown_lyric_quality, japanese_text_quality


MODE_STYLE_BANK = {
    "intimate_confessional": {
        "genre": "cinematic J-pop",
        "tempo": "midtempo",
        "energy": "emotional dynamic lift",
        "vocal": "intimate Japanese lead vocal",
        "arrangement": [
            "close-mic verses",
            "hook-forward chorus",
            "wide final chorus release",
            "dramatic modern pop-rock production",
        ],
    },
    "night_drive": {
        "genre": "night-drive J-pop",
        "tempo": "driving midtempo",
        "energy": "restless forward motion",
        "vocal": "urgent Japanese lead vocal",
        "arrangement": [
            "propulsive drums",
            "neon synth pulse",
            "guitar edge",
            "anthemic chorus release",
        ],
    },
}

AXIS_STYLE_BANK = {
    "body": ["visceral", "close-up", "physically charged"],
    "noise": ["grainy", "restless", "edged with friction"],
    "time": ["forward-pulling", "countdown-like", "tight with anticipation"],
    "defiance": ["defiant", "hard-edged", "unflinching"],
    "light": ["luminous", "bright at release", "glowing"],
    "city": ["urban-night", "neon-lit", "cinematic"],
    "fracture": ["cracked", "uneasy", "pressurized"],
    "vulnerability": ["confessional", "fragile", "unshielded"],
    "motion": ["driving", "forward-leaning", "propulsive"],
    "uplift": ["anthemic", "skyward", "opening wider"],
    "weather": ["atmospheric", "air-swept", "shifting"],
    "night": ["after-dark", "nocturnal", "late-night"],
    "fire": ["heated", "burning", "urgent"],
    "darkness": ["shadow-heavy", "darkly cinematic", "moody"],
    "tension": ["compressed", "suspended", "held tight"],
}

PRODUCTION_COLOR_BANK = {
    "body": ["tight low-end pulse", "close-up vocal presence"],
    "noise": ["grainy edge", "controlled distortion accents"],
    "time": ["countdown tension", "forward-driving momentum"],
    "defiance": ["hard-edged chorus lift", "resolute delivery"],
    "light": ["luminous synth glow", "bright release in the refrain"],
    "city": ["neon-night atmosphere", "urban cinematic framing"],
    "fracture": ["cracked emotional pressure", "uneasy harmonic tension"],
    "vulnerability": ["fragile exposed lead", "unshielded verse tone"],
    "motion": ["propulsive drum movement", "forward-leaning groove"],
    "uplift": ["anthemic widening", "clear skyward release"],
    "weather": ["air and weather texture", "shifting atmospheric layers"],
    "night": ["late-night space", "after-dark emotional color"],
    "fire": ["heated urgency", "burning chorus intensity"],
    "darkness": ["shadow-heavy contrast", "dark cinematic undertow"],
    "tension": ["compressed suspense", "held-back pre-chorus strain"],
}

EMOTION_STYLE_BANK = {
    "uplift": "hope pushing through pressure",
    "vulnerability": "fragile honesty",
    "motion": "restless momentum",
    "defiance": "refusal to back down",
    "darkness": "dark emotional undertow",
    "tension": "compressed emotional strain",
}

EXCLUDE_BANK = {
    "city": ["country twang", "festival brass pop"],
    "night": ["sunny beach-pop sheen", "daytime tropical house"],
    "defiance": ["sleepy lo-fi murmur", "soft bossa nova sway"],
    "vulnerability": ["novelty comedy tone", "theatrical spoken skit"],
    "fire": ["weightless ambient wash", "cute chiptune bounce"],
    "darkness": ["saccharine bubblegum tone", "uplifting corporate jingle feel"],
}

ARC_STYLE_BANK = {
    "build_and_drop": "build tension in the verses and let the chorus hit with a hard emotional drop",
    "steady_build_to_final_release": "keep rising section by section and save the clearest release for the last chorus",
    "flat_or_circular": "keep a repeating emotional gravity while letting the final chorus open just a little wider",
}

FORM_START_BANK = {
    "chorus_open": "Open with the hook immediately so the song lands fast.",
    "extended_lead_in": "Let the verses take time to set the emotional scene before the hook blooms.",
    "interlude_break": "Use the interlude as a brief reset before the next climb.",
    "bridge_lift": "Make the bridge feel like a real lift into the final chorus.",
    "bridge_turn": "Use the bridge to change perspective before the last chorus.",
    "tag_outro": "End with a short afterimage instead of a long fade.",
    "multi_wave_hooking": "Let the chorus return in clear waves rather than one single peak.",
    "core_pop_arc": "Keep the structure focused on a clear verse-to-chorus payoff.",
}

STYLE_TERM_PATTERN = re.compile(r"[A-Za-z0-9\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
STYLE_NOISE_PATTERN = re.compile(r"[?�]")


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = clean_phrase(str(item))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


def is_usable_style_term(value: str) -> bool:
    cleaned = clean_phrase(value)
    if not cleaned or STYLE_NOISE_PATTERN.search(cleaned):
        return False
    visible = cleaned.replace(" ", "")
    matches = STYLE_TERM_PATTERN.findall(visible)
    if not matches:
        return False
    return len(matches) / max(1, len(visible)) >= 0.45


def safe_display_text(value: str, *, fallback: str = "") -> str:
    cleaned = clean_phrase(value)
    return cleaned if is_usable_style_term(cleaned) else fallback


def safe_terms(items: list[str], *, limit: int | None = None) -> list[str]:
    cleaned = [clean_phrase(item) for item in items if is_usable_style_term(str(item))]
    output = dedupe_keep_order(cleaned)
    if limit is not None:
        return output[:limit]
    return output


def format_terms(items: list[str], *, count: int) -> str:
    return ", ".join(dedupe_keep_order(items)[:count])


def compact_motifs(plan: dict[str, Any], *, limit: int = 6) -> list[str]:
    motifs: list[str] = []
    for item in plan.get("motif_roster", []):
        motifs.extend(item.get("motifs", [])[:2])
    return safe_terms(motifs, limit=limit)


def axis_style_descriptors(theme_axes: list[str], *, limit: int = 6) -> list[str]:
    descriptors: list[str] = []
    for axis in theme_axes:
        descriptors.extend(AXIS_STYLE_BANK.get(axis, []))
    return dedupe_keep_order(descriptors)[:limit]


def production_descriptors(theme_axes: list[str], *, limit: int = 6) -> list[str]:
    descriptors: list[str] = []
    for axis in theme_axes:
        descriptors.extend(PRODUCTION_COLOR_BANK.get(axis, []))
    return dedupe_keep_order(descriptors)[:limit]


def emotion_descriptors(dominant_emotions: list[str], *, limit: int = 3) -> list[str]:
    items = [EMOTION_STYLE_BANK[emotion] for emotion in dominant_emotions if emotion in EMOTION_STYLE_BANK]
    return dedupe_keep_order(items)[:limit]


def form_descriptors(plan: dict[str, Any], *, limit: int = 4) -> list[str]:
    tags = [str(tag) for tag in plan.get("form_profile", {}).get("tags", []) if tag]
    section_order = [str(card.get("section", "")) for card in plan.get("section_cards", []) if card.get("section")]
    descriptors: list[str] = []

    if "chorus_open" in tags:
        descriptors.append("chorus-first opening")
    if "extended_lead_in" in tags:
        descriptors.append("extended verse build")
    if "interlude_break" in tags:
        descriptors.append("mid-song interlude reset")
    if "bridge_lift" in tags:
        descriptors.append("bridge rise before the final release")
    elif "bridge_turn" in tags:
        descriptors.append("bridge turn before the last chorus")
    if "tag_outro" in tags:
        descriptors.append("brief afterimage outro")
    if "multi_wave_hooking" in tags:
        descriptors.append("multi-wave chorus returns")
    if len(section_order) >= 8:
        descriptors.append("large-form dramatic progression")

    return dedupe_keep_order(descriptors)[:limit]


def form_workflow_notes(plan: dict[str, Any], *, limit: int = 4) -> list[str]:
    tags = [str(tag) for tag in plan.get("form_profile", {}).get("tags", []) if tag]
    notes = [FORM_START_BANK[tag] for tag in tags if tag in FORM_START_BANK]
    if not notes:
        notes = [FORM_START_BANK["core_pop_arc"]]
    return dedupe_keep_order(notes)[:limit]


def build_tag_style_prompt(plan: dict[str, Any], style_content: dict[str, Any]) -> str:
    genre_text = format_terms(style_content.get("genre_anchors", []), count=2) or "cinematic J-pop"
    tempo_text = format_terms(style_content.get("tempo_feels", []), count=2) or "midtempo"
    groove_text = format_terms(style_content.get("groove_anchors", []), count=2)
    vocal_tone = format_terms(style_content.get("vocal_tones", []), count=2) or "Japanese lead vocal"
    vocal_behaviors = format_terms(style_content.get("vocal_behaviors", []), count=2)
    production_text = format_terms(style_content.get("production_palette", []), count=4)
    arrangement_text = format_terms(style_content.get("arrangement_moves", []), count=4)
    atmosphere_text = format_terms(style_content.get("atmosphere_terms", []), count=3)
    arc_note = clean_phrase(str(style_content.get("energy_arc", "")).strip())

    parts = [
        genre_text,
        tempo_text,
        groove_text,
        vocal_tone,
        vocal_behaviors,
        production_text,
        arrangement_text,
        atmosphere_text,
        arc_note,
        "original Japanese lyrics",
        "avoid English-heavy phrasing",
    ]
    return ", ".join(dedupe_keep_order([part for part in parts if part]))


def build_detailed_style_prompt(plan: dict[str, Any], style_content: dict[str, Any]) -> str:
    del plan
    genre_text = format_terms(style_content.get("genre_anchors", []), count=2) or "cinematic J-pop"
    tempo_text = format_terms(style_content.get("tempo_feels", []), count=2) or "midtempo"
    groove_text = format_terms(style_content.get("groove_anchors", []), count=2)
    vocal_tone = format_terms(style_content.get("vocal_tones", []), count=2) or "Japanese lead vocal"
    vocal_behaviors = format_terms(style_content.get("vocal_behaviors", []), count=3)
    production_text = format_terms(style_content.get("production_palette", []), count=4)
    arrangement_text = format_terms(style_content.get("arrangement_moves", []), count=4)
    atmosphere_text = format_terms(style_content.get("atmosphere_terms", []), count=4)
    arc_note = clean_phrase(str(style_content.get("energy_arc", "")).strip()) or "save the clearest release for the final chorus"

    sentence_1 = f"Create a {genre_text} track at {tempo_text} with {vocal_tone}."
    sentence_2_parts = []
    if groove_text:
        sentence_2_parts.append(f"Let the groove feel {groove_text}.")
    if production_text:
        sentence_2_parts.append(f"Shape the production with {production_text}.")
    sentence_2 = " ".join(sentence_2_parts).strip()

    sentence_3_parts = []
    if vocal_behaviors:
        sentence_3_parts.append(f"Keep the vocal behavior focused on {vocal_behaviors}.")
    if arrangement_text:
        sentence_3_parts.append(f"Use {arrangement_text}.")
    if atmosphere_text:
        sentence_3_parts.append(f"Keep the overall atmosphere {atmosphere_text}.")
    sentence_3 = " ".join(sentence_3_parts).strip()

    sentence_4 = f"Structure the song so you {arc_note}."
    sentence_5 = (
        "Keep the topline entirely in Japanese, let the verses stay tighter than the choruses, "
        "and avoid overly literal or English-heavy phrasing."
    )
    return " ".join(part for part in [sentence_1, sentence_2, sentence_3, sentence_4, sentence_5] if part)


def build_exclude_prompt(plan: dict[str, Any], style_content: dict[str, Any]) -> str:
    exclusions = [
        "English-heavy lyrics",
        "spoken-word intro",
        "flat section energy",
        "novelty comedy tone",
        "muddy arrangement",
    ]
    if plan.get("primary_mode") == "intimate_confessional":
        exclusions.extend(["arena chant chorus", "party EDM synth drop"])
    if "night_drive" == plan.get("primary_mode"):
        exclusions.extend(["acoustic coffeehouse feel", "slow ballad piano only"])
    for axis in [str(axis) for axis in plan.get("theme_axes", []) if axis]:
        exclusions.extend(EXCLUDE_BANK.get(axis, []))
    exclusions.extend(style_content.get("exclude_terms", []))
    return ", ".join(dedupe_keep_order(exclusions))


def build_advanced_options(plan: dict[str, Any]) -> dict[str, str]:
    tags = [str(tag) for tag in plan.get("form_profile", {}).get("tags", []) if tag]
    style_influence = "70-80%"
    weirdness = "35-45%"
    if "multi_wave_hooking" in tags or "chorus_open" in tags:
        style_influence = "75-85%"
    if "extended_lead_in" in tags or "interlude_break" in tags:
        weirdness = "40-55%"
    return {
        "custom_mode": "On",
        "prompt_style": "Detailed natural-language style prompt first, tag prompt as backup",
        "style_influence": style_influence,
        "weirdness": weirdness,
        "prompt_influence": "55-70% when the style prompt is carrying most of the control",
        "audio_influence": "Keep low unless you are using a reference upload or Inspire audio",
        "prompt_boost": "Try On first; turn Off if the result gets too literal or stiff",
    }


def build_lyric_box_guidance(plan: dict[str, Any], lyric_markdown: str) -> dict[str, str]:
    title = safe_display_text(
        extract_title(lyric_markdown) or str(plan.get("title_seed", "")).strip(),
        fallback=str(plan.get("track_id")),
    )
    hook_core = safe_display_text(str(plan.get("hook_blueprint", {}).get("core_text", "")).strip())
    motifs = compact_motifs(plan, limit=4)
    motif_text = ", ".join(motifs[:3]) if motifs else ""
    arc_note = ARC_STYLE_BANK.get(
        str(plan.get("arc_label", "")).strip(),
        "let the final chorus open more than the verse",
    )

    header_parts = [
        "Japanese original lyrics.",
        f"Title image: {title}." if title else "",
        f"Hook phrase: {hook_core}." if hook_core else "",
        f"Image anchors: {motif_text}." if motif_text else "",
        f"Arc: {arc_note}.",
    ]
    optional_header = " ".join(part for part in header_parts if part).strip()

    return {
        "default_strategy": "Paste the sectioned lyrics first and keep headers like [verse_1] and [chorus] intact.",
        "optional_context_header": optional_header,
        "language_guardrail": "If the output drifts into English, add one short header above the lyrics that says the song must stay entirely in Japanese.",
        "editing_hint": "If the song is close but one section misses, use Replace Section or Quick Replace instead of rerolling the whole song.",
    }


def build_workflow_tips() -> list[str]:
    return [
        "Use Custom mode and start with the detailed style prompt before falling back to the tag prompt.",
        "Use Exclude Styles aggressively to block wrong genre drift, vocal behavior, or arrangement choices.",
        "Keep the lyric box mostly clean and sectioned; only add a short context header if the model keeps missing the language or emotional arc.",
        "If one generation gets close, use Replace Section or Quick Replace instead of rerolling the whole song.",
        "If you find a good voice/style pairing, save it as a Persona for consistency across songs.",
        "For better style transfer, use a short Inspire playlist of three to five songs rather than a huge mixed list.",
        "If you already like the instrumental, try Add Vocals instead of rerolling the whole arrangement.",
    ]


def build_suno_song_package(
    *,
    run_dir: Path,
    lyric_path: Path,
    score_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = load_json(run_dir / "plan.json")
    lyric_markdown = lyric_path.read_text(encoding="utf-8")
    style_content = resolve_style_prompt_content(plan=plan, run_dir=run_dir)
    title = safe_display_text(
        extract_title(lyric_markdown) or str(plan.get("title_seed", "")).strip(),
        fallback=str(plan.get("track_id")),
    )
    title_quality = japanese_text_quality(title)
    lyric_quality = japanese_markdown_lyric_quality(lyric_markdown)
    detailed_style_prompt = build_detailed_style_prompt(plan, style_content)
    tag_style_prompt = build_tag_style_prompt(plan, style_content)

    payload = {
        "schema_version": "1.0",
        "track_id": plan.get("track_id"),
        "artist_id": plan.get("artist_id"),
        "title": title,
        "style_prompt": detailed_style_prompt,
        "style_prompt_detailed": detailed_style_prompt,
        "style_prompt_tags": tag_style_prompt,
        "exclude_prompt": build_exclude_prompt(plan, style_content),
        "style_content_card": style_content,
        "lyric_box_guidance": build_lyric_box_guidance(plan, lyric_markdown),
        "lyric_markdown": lyric_markdown,
        "text_quality": {
            "title": title_quality,
            "lyrics": lyric_quality,
        },
        "style_notes": {
            "primary_mode": plan.get("primary_mode"),
            "arc_label": plan.get("arc_label"),
            "theme_axes": plan.get("theme_axes", []),
            "dominant_emotions": plan.get("dominant_emotions", []),
            "form_tags": plan.get("form_profile", {}).get("tags", []),
            "section_order": plan.get("form_profile", {}).get("section_order", []),
            "motif_focus": compact_motifs(plan),
            "hook_core": safe_display_text(str(plan.get("hook_blueprint", {}).get("core_text", "")).strip()),
        },
        "advanced_options": build_advanced_options(plan),
        "workflow_tips": build_workflow_tips(),
        "sources": {
            "run_dir": str(run_dir),
            "lyric_path": str(lyric_path),
        },
    }
    if score_review:
        payload["quality_snapshot"] = {
            "total": score_review.get("scores", {}).get("total"),
            "scores": score_review.get("scores", {}),
            "critic_notes": score_review.get("critic_notes", []),
        }
    return payload


def render_suno_song_package_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# SUNO Song Package: {payload['track_id']}",
        "",
        f"- Title: `{payload['title']}`",
        f"- Artist id: `{payload['artist_id']}`",
    ]
    quality_snapshot = payload.get("quality_snapshot")
    if quality_snapshot:
        lines.append(f"- Quality total: `{quality_snapshot['total']}`")
    lines.extend(
        [
            "",
            "## Style Prompt",
            "```text",
            payload["style_prompt_detailed"],
            "```",
            "",
            "## Tag Prompt Backup",
            "```text",
            payload["style_prompt_tags"],
            "```",
            "",
            "## Exclude Prompt",
            "```text",
            payload["exclude_prompt"],
            "```",
            "",
            "## Lyrics Box Guidance",
            f"- Default strategy: {payload['lyric_box_guidance']['default_strategy']}",
            f"- Optional context header: `{payload['lyric_box_guidance']['optional_context_header']}`",
            f"- Language guardrail: {payload['lyric_box_guidance']['language_guardrail']}",
            f"- Editing hint: {payload['lyric_box_guidance']['editing_hint']}",
            "",
            "## Style Content Card",
            f"- Source: `{payload['style_content_card']['source']}`",
            f"- Mode atoms: `{payload['style_content_card']['mode_id']}`",
            f"- Genre anchors: `{', '.join(payload['style_content_card']['genre_anchors'])}`",
            f"- Tempo feels: `{', '.join(payload['style_content_card']['tempo_feels'])}`",
            f"- Groove anchors: `{', '.join(payload['style_content_card']['groove_anchors'])}`",
            f"- Vocal tones: `{', '.join(payload['style_content_card']['vocal_tones'])}`",
            f"- Vocal behaviors: `{', '.join(payload['style_content_card']['vocal_behaviors'])}`",
            f"- Production palette: `{', '.join(payload['style_content_card']['production_palette'])}`",
            f"- Arrangement moves: `{', '.join(payload['style_content_card']['arrangement_moves'])}`",
            f"- Atmosphere terms: `{', '.join(payload['style_content_card']['atmosphere_terms'])}`",
            f"- Energy arc: `{payload['style_content_card']['energy_arc']}`",
            f"- Exclude terms: `{', '.join(payload['style_content_card']['exclude_terms'])}`",
            "",
            "## Style Notes",
            f"- Mode: `{payload['style_notes']['primary_mode']}`",
            f"- Arc: `{payload['style_notes']['arc_label']}`",
            f"- Theme axes: `{', '.join(payload['style_notes']['theme_axes'])}`",
            f"- Emotions: `{', '.join(payload['style_notes']['dominant_emotions'])}`",
            f"- Form tags: `{', '.join(payload['style_notes']['form_tags'])}`",
            f"- Section order: `{', '.join(payload['style_notes']['section_order'])}`",
            f"- Motif focus: `{', '.join(payload['style_notes']['motif_focus'])}`",
            f"- Hook core: `{payload['style_notes']['hook_core']}`",
            "",
            "## Advanced Options",
            f"- Custom mode: `{payload['advanced_options']['custom_mode']}`",
            f"- Prompt style: `{payload['advanced_options']['prompt_style']}`",
            f"- Style influence: `{payload['advanced_options']['style_influence']}`",
            f"- Weirdness: `{payload['advanced_options']['weirdness']}`",
            f"- Prompt influence: `{payload['advanced_options']['prompt_influence']}`",
            f"- Audio influence: `{payload['advanced_options']['audio_influence']}`",
            f"- Prompt boost: `{payload['advanced_options']['prompt_boost']}`",
            "",
            "## Workflow Tips",
            *[f"- {tip}" for tip in payload["workflow_tips"]],
            "",
            "## Lyrics",
            "",
            payload["lyric_markdown"].strip(),
            "",
        ]
    )
    return "\n".join(lines)


def build_suno_bundle_from_scoring_manifest(
    scoring_manifest: Path,
    output_dir: Path,
    *,
    min_score: float,
    max_records: int | None,
) -> dict[str, Any]:
    payload = load_json(scoring_manifest)
    reviews = [
        review
        for review in payload.get("reviews", [])
        if float(review.get("scores", {}).get("total", 0.0)) >= min_score
    ]
    reviews.sort(key=lambda item: float(item.get("scores", {}).get("total", 0.0)), reverse=True)
    if max_records is not None:
        reviews = reviews[:max_records]

    records: list[dict[str, Any]] = []
    markdown_paths: list[str] = []
    skipped_records: list[dict[str, Any]] = []
    for review in reviews:
        lyric_path = Path(review["prediction_path"])
        run_dir = Path(review["run_dir"])
        package = build_suno_song_package(run_dir=run_dir, lyric_path=lyric_path, score_review=review)
        lyric_quality = package.get("text_quality", {}).get("lyrics", {})
        if not lyric_quality.get("usable", False):
            skipped_records.append(
                {
                    "track_id": package.get("track_id"),
                    "reason": "lyric_text_quality_failed",
                    "text_quality": package.get("text_quality", {}),
                }
            )
            continue
        package_path = output_dir / "json" / f"{package['track_id']}.json"
        markdown_path = output_dir / "markdown" / f"{package['track_id']}.md"
        write_json(package_path, package)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_suno_song_package_markdown(package), encoding="utf-8")
        package["package_path"] = str(package_path)
        package["markdown_path"] = str(markdown_path)
        markdown_paths.append(str(markdown_path))
        records.append(package)

    manifest = {
        "schema_version": "1.0",
        "source_scoring_manifest": str(scoring_manifest),
        "output_dir": str(output_dir),
        "record_count": len(records),
        "skipped_count": len(skipped_records),
        "min_score": min_score,
        "tracks": [record["track_id"] for record in records],
        "markdown_paths": markdown_paths,
        "skipped_records": skipped_records,
    }
    manifest_path = write_json(output_dir / "suno_bundle_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def render_suno_bundle_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# SUNO Song Bundle",
        "",
        f"- Source scoring manifest: `{manifest['source_scoring_manifest']}`",
        f"- Minimum score: `{manifest['min_score']}`",
        f"- Record count: `{manifest['record_count']}`",
        f"- Skipped count: `{manifest.get('skipped_count', 0)}`",
        "",
        "## Tracks",
        "",
    ]
    for track_id in manifest["tracks"]:
        lines.append(f"- `{track_id}`")
    skipped_records = manifest.get("skipped_records", [])
    if skipped_records:
        lines.extend(["", "## Skipped", ""])
        for item in skipped_records:
            lines.append(f"- `{item['track_id']}`: `{item['reason']}`")
    return "\n".join(lines)

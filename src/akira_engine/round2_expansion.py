from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _group_by_artist(candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in candidates:
        artist_id = str(item.get("artist_id", "")).strip()
        if not artist_id:
            continue
        grouped.setdefault(artist_id, []).append(item)
    return grouped


def _seed_lookup(seeds: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for item in seeds:
        track_id = str(item.get("track_id", "")).strip()
        if track_id:
            lookup[track_id] = item
    return lookup


def _build_artist_queue(
    artist_id: str,
    candidates: list[dict[str, Any]],
    seed_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    queue: list[dict[str, Any]] = []
    for priority, item in enumerate(candidates, start=1):
        track_id = str(item.get("track_id", "")).strip()
        if not track_id:
            continue
        has_seed = track_id in seed_lookup
        queue.append(
            {
                "priority": priority,
                "track_id": track_id,
                "title": str(item.get("title", "")).strip(),
                "likely_mode": str(item.get("likely_mode", "")).strip(),
                "secondary_modes": [str(value).strip() for value in item.get("secondary_modes", []) if str(value).strip()],
                "priority_label": str(item.get("priority", "")).strip() or "medium",
                "recommended_dataset_tier": str(item.get("recommended_dataset_tier", "")).strip() or "producer_expansion",
                "has_draft_seed": has_seed,
                "status": "seeded" if has_seed else "candidate_only",
                "why_it_matters": [str(value).strip() for value in item.get("why_it_matters", []) if str(value).strip()],
                "style_gap_filled": [str(value).strip() for value in item.get("style_gap_filled", []) if str(value).strip()],
                "notes": [str(value).strip() for value in item.get("notes", []) if str(value).strip()],
            }
        )
    return {
        "schema_version": "1.0",
        "record_type": "round2_artist_queue",
        "artist_id": artist_id,
        "queue": queue,
    }


def _build_seed_scaffold(candidate: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "record_type": "round2_draft_seed",
        "track_identity": {
            "artist_id": str(candidate.get("artist_id", "")).strip(),
            "track_id": str(candidate.get("track_id", "")).strip(),
            "title": str(candidate.get("title", "")).strip(),
        },
        "dataset_role": {
            "recommended_dataset_tier": str(candidate.get("recommended_dataset_tier", "")).strip(),
            "likely_mode": str(seed.get("likely_mode", "") or candidate.get("likely_mode", "")).strip(),
            "secondary_modes": [str(value).strip() for value in candidate.get("secondary_modes", []) if str(value).strip()],
            "priority": str(candidate.get("priority", "")).strip() or "medium",
        },
        "seed_brief": {
            "title_pattern": str(seed.get("title_pattern", "")).strip(),
            "hook_behavior": [str(value).strip() for value in seed.get("hook_behavior", []) if str(value).strip()],
            "section_flow_guess": [str(value).strip() for value in seed.get("section_flow_guess", []) if str(value).strip()],
            "imagery_classes": [str(value).strip() for value in seed.get("imagery_classes", []) if str(value).strip()],
            "emotional_arc": [str(value).strip() for value in seed.get("emotional_arc", []) if str(value).strip()],
            "leakage_watchouts": [str(value).strip() for value in seed.get("leakage_watchouts", []) if str(value).strip()],
            "prompt_seed_terms": [str(value).strip() for value in seed.get("prompt_seed_terms", []) if str(value).strip()],
            "grounding_status": str(seed.get("grounding_status", "")).strip(),
        },
        "candidate_context": {
            "why_it_matters": [str(value).strip() for value in candidate.get("why_it_matters", []) if str(value).strip()],
            "style_gap_filled": [str(value).strip() for value in candidate.get("style_gap_filled", []) if str(value).strip()],
            "overlap_risk_with_existing_set": str(candidate.get("overlap_risk_with_existing_set", "")).strip(),
            "grounding_feasibility": str(candidate.get("grounding_feasibility", "")).strip(),
            "provenance_feasibility": str(candidate.get("provenance_feasibility", "")).strip(),
            "audio_feasibility": str(candidate.get("audio_feasibility", "")).strip(),
        },
    }


def build_round2_registry(project_root: Path) -> dict[str, Any]:
    global_dir = project_root / "data" / "_global"
    candidates = load_json(global_dir / "expansion_round2_candidates.json")
    seeds = load_json(global_dir / "expansion_round2_draft_seeds.json")
    grouped = _group_by_artist(candidates)
    seed_lookup = _seed_lookup(seeds)

    artists: list[dict[str, Any]] = []
    for artist_id in sorted(grouped):
        artist_candidates = grouped[artist_id]
        seeded = sum(1 for item in artist_candidates if str(item.get("track_id", "")).strip() in seed_lookup)
        artists.append(
            {
                "artist_id": artist_id,
                "candidate_count": len(artist_candidates),
                "seeded_count": seeded,
                "high_priority_count": sum(1 for item in artist_candidates if str(item.get("priority", "")).strip() == "high"),
                "track_ids": [str(item.get("track_id", "")).strip() for item in artist_candidates if str(item.get("track_id", "")).strip()],
            }
        )

    return {
        "schema_version": "1.0",
        "record_type": "round2_expansion_registry",
        "candidate_count": len(candidates),
        "seed_count": len(seeds),
        "artists": artists,
    }


def scaffold_round2_expansion(project_root: Path) -> dict[str, Any]:
    global_dir = project_root / "data" / "_global"
    output_root = global_dir / "round2_expansion"
    candidates = load_json(global_dir / "expansion_round2_candidates.json")
    seeds = load_json(global_dir / "expansion_round2_draft_seeds.json")
    grouped = _group_by_artist(candidates)
    seed_lookup = _seed_lookup(seeds)

    registry = build_round2_registry(project_root)
    write_json(output_root / "registry.json", registry)

    created_seed_files: list[str] = []
    queue_paths: list[str] = []
    for artist_id, artist_candidates in sorted(grouped.items()):
        artist_queue = _build_artist_queue(artist_id, artist_candidates, seed_lookup)
        artist_ref_dir = project_root / "data" / artist_id / "reference_tracks"
        queue_path = artist_ref_dir / "round2_queue.json"
        write_json(queue_path, artist_queue)
        queue_paths.append(str(queue_path))

        seed_dir = artist_ref_dir / "round2_seed_scaffolds"
        for candidate in artist_candidates:
            track_id = str(candidate.get("track_id", "")).strip()
            seed = seed_lookup.get(track_id)
            if not seed:
                continue
            slug = track_id.removeprefix(f"{artist_id}_")
            seed_path = seed_dir / f"{slug}.seed.json"
            write_json(seed_path, _build_seed_scaffold(candidate, seed))
            created_seed_files.append(str(seed_path))

    return {
        "registry_path": str(output_root / "registry.json"),
        "queue_count": len(queue_paths),
        "seed_file_count": len(created_seed_files),
        "queue_paths": queue_paths,
        "seed_paths": created_seed_files,
    }


def _seed_sections(seed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    flow = [str(value).strip() for value in seed_payload.get("seed_brief", {}).get("section_flow_guess", []) if str(value).strip()]
    default_sections = [
        ("verse", "Verse 1", "a_melo", "observation"),
        ("pre_chorus", "Pre-Chorus", "b_melo", "compression"),
        ("chorus", "Chorus 1", "sabi", "release"),
        ("bridge", "Bridge", "c_melo", "reframe"),
        ("chorus", "Chorus Final", "sabi", "release"),
    ]
    sections: list[dict[str, Any]] = []
    for index, (section_type, section_name, jp_role, energy_role) in enumerate(default_sections):
        source_label = flow[index] if index < len(flow) else section_name.lower().replace(" ", "_")
        sections.append(
            {
                "section_type": section_type,
                "section_name": section_name,
                "jp_section_role": jp_role,
                "mora_density": "balanced",
                "spoken_speed_bias": "medium",
                "title_drop_role": "partial" if "chorus" in section_name.lower() else "none",
                "phrase_energy_role": energy_role,
                "source_labels": [source_label],
                "lines": [],
            }
        )
    return sections


def _seed_section_analysis(seed_payload: dict[str, Any]) -> list[dict[str, Any]]:
    imagery = [str(value).strip() for value in seed_payload.get("seed_brief", {}).get("imagery_classes", []) if str(value).strip()]
    arc = [str(value).strip() for value in seed_payload.get("seed_brief", {}).get("emotional_arc", []) if str(value).strip()]
    flow = [str(value).strip() for value in seed_payload.get("seed_brief", {}).get("section_flow_guess", []) if str(value).strip()]
    default_names = ["Verse 1", "Pre-Chorus", "Chorus 1", "Bridge", "Chorus Final"]
    default_types = ["verse", "pre_chorus", "chorus", "bridge", "chorus"]
    analyses: list[dict[str, Any]] = []
    for index, section_name in enumerate(default_names):
        analyses.append(
            {
                "section_name": section_name,
                "section_type": default_types[index],
                "source_section_labels": [flow[index] if index < len(flow) else section_name.lower().replace(" ", "_")],
                "lyric_function": ["scaffold_seed"],
                "narrative_job": arc[index] if index < len(arc) else "Scaffold placeholder awaiting full grounding.",
                "arrangement_role": {
                    "summary": "Seed scaffold only.",
                    "status": "inferred",
                    "evidence_basis": ["round2_draft_seed"],
                },
                "harmony_melody_role": {
                    "summary": "Seed scaffold only.",
                    "status": "inferred",
                    "evidence_basis": ["round2_draft_seed"],
                },
                "dynamics_role": {
                    "summary": "Seed scaffold only.",
                    "status": "inferred",
                    "evidence_basis": ["round2_draft_seed"],
                },
                "vocabulary_focus": imagery[:4],
                "rhyme_features": [],
                "rhythm_features": [flow[index] if index < len(flow) else "scaffold"],
                "jp_section_role": ["a_melo", "b_melo", "sabi", "c_melo", "sabi"][index],
                "title_drop_role": "partial" if "chorus" in section_name.lower() else "none",
                "phrase_energy_role": ["observation", "compression", "release", "reframe", "release"][index],
                "confidence": "low",
            }
        )
    return analyses


def build_round2_conditioning_scaffold(seed_payload: dict[str, Any]) -> dict[str, Any]:
    identity = seed_payload.get("track_identity", {})
    dataset_role = seed_payload.get("dataset_role", {})
    seed_brief = seed_payload.get("seed_brief", {})
    context = seed_payload.get("candidate_context", {})
    track_id = str(identity.get("track_id", "")).strip()
    artist_id = str(identity.get("artist_id", "")).strip()
    title = str(identity.get("title", "")).strip()
    likely_mode = str(dataset_role.get("likely_mode", "")).strip() or "ironic_meta"
    imagery = [str(value).strip() for value in seed_brief.get("imagery_classes", []) if str(value).strip()]
    prompt_terms = [str(value).strip() for value in seed_brief.get("prompt_seed_terms", []) if str(value).strip()]
    hook_behavior = [str(value).strip() for value in seed_brief.get("hook_behavior", []) if str(value).strip()]
    hook_lines = [title] if title else []
    hook_lines.extend(hook_behavior[:1])

    return {
        "schema_version": "1.0",
        "record_type": "track_conditioning_record",
        "track_identity": {
            "track_id": track_id,
            "artist_id": artist_id,
            "artist_name": artist_id,
            "title": title,
            "title_core": title,
            "language": "ja",
        },
        "source_provenance": {
            "lyric_sources": [],
            "metadata_sources": [],
            "analysis_sources": [
                {
                    "label": "Round2 draft seed scaffold",
                    "origin": "manual_note",
                    "status": "estimated",
                    "notes": "Generated from expansion_round2_draft_seeds.json",
                }
            ],
            "notes": ["Scaffold only. Full grounding and provenance required before audit promotion."],
        },
        "lyric_ground_truth": {
            "full_text_status": "partial",
            "copyright_handling_note": "Scaffold placeholder built from round2 seed, not full lyric grounding.",
            "sections": _seed_sections(seed_payload),
            "hook_lines": _unique(hook_lines)[:2],
            "question_lines": [],
            "repetition_patterns": hook_behavior[:2],
        },
        "song_intent": {
            "core_theme": imagery[:3] or ["scaffold_theme"],
            "emotional_thesis": "Round2 scaffold awaiting full grounding.",
            "contrast_device": [],
            "dramatic_arc": [str(value).strip() for value in seed_brief.get("emotional_arc", []) if str(value).strip()],
            "narrative_role": [likely_mode],
            "tie_in_function": "",
            "title_function": "seed_centerpiece",
            "key_motifs": imagery[:4] or [title],
            "interpretation_confidence": "low",
        },
        "section_analysis": _seed_section_analysis(seed_payload),
        "japanese_lyric_profile": {
            "hook_copy_force": "medium",
            "title_ignition_style": "direct",
            "modern_compression_bias": "medium",
            "phrase_source_types": [str(seed_brief.get("title_pattern", "")).strip() or "seed_pattern"],
            "critic_focus": ["needs_full_grounding", "needs_provenance"],
            "section_features": [str(value).strip() for value in seed_brief.get("section_flow_guess", []) if str(value).strip()],
        },
        "audio_fact_layer": {
            "reported_facts": {},
            "proxy_inference": {
                "energy_profile": [str(value).strip() for value in seed_brief.get("emotional_arc", []) if str(value).strip()],
                "vocal_behavior": hook_behavior[:3],
                "production_palette": prompt_terms[:4],
                "confidence": "estimated",
                "evidence_basis": ["round2_draft_seed"],
            },
            "do_not_overclaim": ["BPM exactness", "key exactness", "arrangement exactness"],
        },
        "prompt_conditioning": {
            "genre_anchors": [likely_mode, "vocaloid", "subculture"],
            "tempo_feels": [],
            "vocal_tones": hook_behavior[:3],
            "production_palette": prompt_terms[:4],
            "energy_arc": [str(value).strip() for value in seed_brief.get("emotional_arc", []) if str(value).strip()],
            "imagery_anchors": imagery[:6],
            "exclude": ["anchor leakage", "verbatim hook reuse"],
            "source_basis": ["round2_draft_seed"],
        },
        "quality_control": {
            "record_stage": "scaffolded",
            "missing_fields": ["full lyrics", "provenance", "audio facts"],
            "manual_review_required_for": ["lyric grounding", "source cross-check", "section validation"],
            "ready_for_prompting": False,
            "ready_for_audio_claims": False,
            "notes": context.get("why_it_matters", []),
        },
    }


def materialize_round2_seed_scaffolds(project_root: Path) -> dict[str, Any]:
    output_root = project_root / "data"
    round2_root = output_root / "_global" / "round2_expansion"
    registry = load_json(round2_root / "registry.json")
    created: list[str] = []
    updated_queues: list[str] = []
    for artist in registry.get("artists", []):
        artist_id = str(artist.get("artist_id", "")).strip()
        if not artist_id:
            continue
        queue_path = output_root / artist_id / "reference_tracks" / "round2_queue.json"
        if not queue_path.exists():
            continue
        queue_payload = load_json(queue_path)
        changed = False
        for item in queue_payload.get("queue", []):
            if not bool(item.get("has_draft_seed")):
                continue
            track_id = str(item.get("track_id", "")).strip()
            slug = track_id.removeprefix(f"{artist_id}_")
            seed_path = output_root / artist_id / "reference_tracks" / "round2_seed_scaffolds" / f"{slug}.seed.json"
            if not seed_path.exists():
                continue
            conditioning_path = output_root / artist_id / "reference_tracks" / f"{slug}.conditioning.json"
            if not conditioning_path.exists():
                write_json(conditioning_path, build_round2_conditioning_scaffold(load_json(seed_path)))
                created.append(str(conditioning_path))
            if str(item.get("status", "")).strip() != "scaffolded":
                item["status"] = "scaffolded"
                changed = True
        if changed:
            write_json(queue_path, queue_payload)
            updated_queues.append(str(queue_path))
    return {
        "created_conditioning_count": len(created),
        "created_conditioning_paths": created,
        "updated_queue_count": len(updated_queues),
        "updated_queue_paths": updated_queues,
    }


def sync_round2_queue_status(project_root: Path, artist_id: str) -> dict[str, Any]:
    queue_path = project_root / "data" / artist_id / "reference_tracks" / "round2_queue.json"
    if not queue_path.exists():
        return {"artist_id": artist_id, "changed_count": 0, "record_count": 0, "queue_path": str(queue_path)}

    queue_payload = load_json(queue_path)
    audit_path = project_root / "reports" / "quality" / "round2_expansion_audit" / f"{artist_id}_round2_audit.json"
    audit_lookup: dict[str, dict[str, Any]] = {}
    if audit_path.exists():
        audit_payload = load_json(audit_path)
        audit_lookup = {
            str(item.get("track_id", "")).strip(): item
            for item in audit_payload.get("records", [])
            if str(item.get("track_id", "")).strip()
        }

    changed = 0
    for item in queue_payload.get("queue", []):
        track_id = str(item.get("track_id", "")).strip()
        current_status = str(item.get("status", "")).strip() or "candidate_only"
        next_status = current_status
        audit_record = audit_lookup.get(track_id)
        if audit_record:
            grade = str(audit_record.get("grade", "")).strip()
            if grade == "gold":
                next_status = "validated"
            elif grade == "usable":
                next_status = "drafted"
            else:
                next_status = "scaffolded"
        elif bool(item.get("has_draft_seed")):
            next_status = "scaffolded"
        else:
            next_status = "candidate_only"
        if next_status != current_status:
            item["status"] = next_status
            changed += 1
    if changed:
        write_json(queue_path, queue_payload)
    return {
        "artist_id": artist_id,
        "changed_count": changed,
        "record_count": len(queue_payload.get("queue", [])),
        "queue_path": str(queue_path),
    }

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from src.akira_engine.production_policy import BASELINE_2026_03_31 as Policy
from src.akira_engine.songwriter_io import load_conditioning_records

def _conditioning_score(record: dict[str, Any]) -> float:
    qc = record.get("quality_control", {})
    for key in ("critic_score", "quality_score", "score"):
        try:
            value = float(qc.get(key, 0.0))
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            return value
    return 0.0

def load_trusted_conditioning_records(
    artist_id: str,
    *,
    expansion_limit: int = 6,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Canonical loader for High-Trust (Gold/Silver) conditioning records.
    Refactored from demo_planner for Stage J consistency.
    """
    records: list[dict[str, Any]] = []
    source_records = load_conditioning_records(artist_id)
    
    for record in source_records:
        qc = record.get("quality_control", {})
        # Support legacy and vNext schemas
        if qc.get("ready_for_prompting") is not True and record.get("record_type") != "track_conditioning_record":
            continue
            
        cloned = dict(record)
        grade = "provisional"
        if record.get("record_type") == "track_conditioning_record" and not record.get("record_stage"):
            # If ready_for_prompting is True, the record passed QC — treat as curated
            if qc.get("ready_for_prompting") is True:
                grade = "curated"
            else:
                grade = "provisional"
        else:
             grade = str(record.get("record_stage") or qc.get("record_stage") or "curated").strip().lower()
             
        # Baseline Freeze: Policy Enforced Provenance Guard
        if Policy.EXCLUDE_PROVISIONAL_SOURCES and grade == "provisional":
            continue
            
        cloned["_audit_grade"] = grade
        cloned["_audit_score"] = _conditioning_score(record)
        records.append(cloned)

    # Sort and split into Anchors (Top 3) and Expansions
    records.sort(key=lambda x: x.get("_audit_score", 0.0), reverse=True)
    anchors = records[:3]
    expansions = records[3:3+expansion_limit]
    
    return anchors, expansions

@dataclass
class ConditioningResult:
    schema_version: str = "1.1"
    record_type: str = "track_conditioning_record"
    artist_id: str = ""
    track_id: str = ""
    track_identity: dict[str, Any] = field(default_factory=dict)
    source_provenance: dict[str, Any] = field(default_factory=dict)
    artist_profile: dict[str, Any] = field(default_factory=dict)
    song_intent: dict[str, Any] = field(default_factory=dict)
    prompt_conditioning: dict[str, Any] = field(default_factory=dict)
    lyric_ground_truth: dict[str, Any] = field(default_factory=dict)
    japanese_lyric_profile: dict[str, Any] = field(default_factory=dict)
    section_analysis: list[dict[str, Any]] = field(default_factory=list)
    normalized_sections: list[dict[str, Any]] = field(default_factory=list)
    imagery_anchors: list[str] = field(default_factory=list)
    audit_status: str = "provisional" # verified | provisional
    source_grade: str = "failed_source" # gold | silver | failed_source | rejected
    normalization_summary: dict[str, Any] = field(default_factory=dict)
    use_for_grounding: bool = True

def target_section_for_jp_role(role: str, index: int) -> str | None:
    """Standard vNext section mapping (as requested by user)."""
    if role == "intro":
        return "intro"
    if role == "a_melo":
        return "verse_1" if index == 0 else "verse_2"
    if role == "b_melo":
        return "pre_chorus" if index == 0 else "pre_chorus_2"
    if role == "sabi":
        return "chorus" if index == 0 else "chorus_2"
    if role == "dai_sabi":
        return "chorus_final"
    if role == "c_melo":
        return "bridge" if index == 0 else "bridge_rise"
    if role == "outro":
        return "outro"
    return None

def run_conditioning_stage(
    artist_id: str,
    track_id: str,
    normalized_lyric_text: str,
    artist_profile: dict[str, Any],
    song_intent: dict[str, Any],
    features: Any = None, # FeatureProfile
    normalization_result: Any = None # NormalizeResult
) -> ConditioningResult:
    """Execute Stage D: Conditioning Builder (Normalization)."""
    
    # Superset Assembly
    result = ConditioningResult(
        artist_id=artist_id,
        track_id=track_id,
        artist_profile=artist_profile,
        song_intent=song_intent
    )
    
    # 1. Identity & Provenance
    result.track_identity = {
        "track_id": track_id,
        "artist_id": artist_id,
        "artist_name": artist_profile.get("artist_name", artist_id),
        "title": song_intent.get("core_theme", ["demo"])[0],
        "language": "ja",
        "status": "cross_checked"
    }
    
    result.source_provenance = {
        "notes": ["vNext conditioning builder normalization"],
        "trusted_ratio": normalization_result.japanese_char_ratio if normalization_result else 1.0
    }
    
    # 2. Imagery Anchors (Double Injection as requested)
    atoms = []
    if features:
        atoms = features.motif_atoms + features.body_atoms + features.scene_atoms
    else:
        atoms = song_intent.get("key_motifs", [])
    
    result.imagery_anchors = atoms[:14]
    result.prompt_conditioning = {
        "imagery_anchors": atoms[:14],
        "genre_anchors": song_intent.get("core_theme", []),
        "vocal_tones": artist_profile.get("vocal_identity", []),
        "production_palette": artist_profile.get("style_markers", []),
        "energy_arc": song_intent.get("dramatic_arc", [])
    }
    
    # 3. Structural Normalization (Standard Mapping)
    normalized_sections = []
    raw_lines = normalized_lyric_text.splitlines()
    clean_lines = [l.strip() for l in raw_lines if l.strip()]
    
    # For now, if no explicit sections, chunk them logically
    roles = ["intro", "a_melo", "b_melo", "sabi", "a_melo", "sabi", "c_melo", "dai_sabi", "outro"]
    role_counts = {"intro": 0, "a_melo": 0, "b_melo": 0, "sabi": 0, "dai_sabi": 0, "c_melo": 0, "outro": 0}
    
    cursor = 0
    lyric_sections = []
    for role in roles:
        if cursor >= len(clean_lines): break
        target = target_section_for_jp_role(role, role_counts[role])
        role_counts[role] += 1
        
        section_lines = clean_lines[cursor:cursor+4]
        cursor += 4
        
        sec_record = {
            "section": target,
            "jp_role": role,
            "lines": section_lines,
            "section_name": target.replace("_", " ").title(),
            "section_type": "verse" if "verse" in target else "chorus" if "chorus" in target else target
        }
        normalized_sections.append(sec_record)
        lyric_sections.append(sec_record)

    result.normalized_sections = normalized_sections
    result.lyric_ground_truth = {
        "sections": lyric_sections,
        "full_text": normalized_lyric_text,
        "hook_lines": normalized_sections[3]["lines"] if len(normalized_sections) > 3 else []
    }
    
    # 4. Profile & Analysis
    result.japanese_lyric_profile = {
        "section_features": [{"jp_section_role": s["jp_role"], "section_name": s["section_name"]} for s in normalized_sections]
    }
    result.section_analysis = [
        {"section_name": s["section_name"], "jp_section_role": s["jp_role"], "narrative_job": f"Standard {s['jp_role']} flow"}
        for s in normalized_sections
    ]
    
    # 5. Audit Status Logic (Stage B/C + Provenance)
    from ..production_policy import BASELINE_2026_03_31 as Policy
    
    source_grade = "silver"
    audit_status = "verified"
    
    if normalization_result:
        if normalization_result.has_bad_script:
            source_grade = "rejected"
            audit_status = "provisional"
        elif normalization_result.japanese_char_ratio < 0.6:
            source_grade = "failed_source"
            audit_status = "provisional"
        elif normalization_result.japanese_char_ratio >= Policy.JAPANESE_RATIO_MIN:
            source_grade = "gold"
            
    result.source_grade = source_grade
    result.audit_status = audit_status
    result.normalization_summary = {
        "purity": normalization_result.japanese_char_ratio if normalization_result else 0.0,
        "errors": normalization_result.errors if normalization_result else []
    }
    
    # Provenance Guard: Baseline Freeze (Policy Enforced)
    is_trusted = (source_grade in {"gold", "silver"}) and (audit_status == "verified")
    if Policy.EXCLUDE_PROVISIONAL_SOURCES and audit_status == "provisional":
        is_trusted = False
        
    result.use_for_grounding = is_trusted
    
    return result

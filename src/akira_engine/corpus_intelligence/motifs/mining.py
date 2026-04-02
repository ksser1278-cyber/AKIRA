# src/akira_engine/corpus_intelligence/motifs/mining.py

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .schema import SectionMotifSnapshot, TransitionType


DEFAULT_SECTION_ORDER = [
    "intro",
    "verse_1",
    "pre_chorus",
    "chorus",
    "verse_2",
    "pre_chorus_2",
    "bridge",
    "chorus_final",
    "outro",
]


POSITIVE_EMOTION_HINTS = {"heat", "surge", "obsession", "impact", "explosion"}
NEGATIVE_EMOTION_HINTS = {"collapse", "distance", "decay", "void", "numbness"}
RELEASE_HINTS = {"release", "breakthrough", "open", "resolve", "liberation"}


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _collect_section_motifs(section: Dict[str, Any]) -> List[str]:
    """
    우선순위:
    1) section_analysis 명시 motif
    2) conditioning atoms / imagery
    3) lyric_ground_truth 본문에서 보강 추출 결과
    """
    motifs: List[str] = []

    # Priority 1: Explicit motifs
    motifs.extend(_safe_list(section.get("motifs")))
    motifs.extend(_safe_list(section.get("dominant_motifs")))
    motifs.extend(_safe_list(section.get("vocabulary_focus"))) # Added based on research

    # Priority 2: Conditioning atoms
    motifs.extend(_safe_list(section.get("conditioning_atoms")))
    motifs.extend(_safe_list(section.get("imagery_anchors")))
    motifs.extend(_safe_list(section.get("scene_atoms")))
    motifs.extend(_safe_list(section.get("body_atoms")))
    motifs.extend(_safe_list(section.get("sound_atoms")))

    return _dedupe_keep_order(motifs)


def _extract_emotion_tags(section: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    tags.extend(_safe_list(section.get("emotion_tags")))
    tags.extend(_safe_list(section.get("emotional_axes")))
    tags.extend(_safe_list(section.get("mood_tags")))
    return _dedupe_keep_order(tags)


def build_section_snapshots_from_conditioning(
    conditioning_record: Dict[str, Any],
) -> List[SectionMotifSnapshot]:
    """
    conditioning.json / conditioning_record 기준 section별 motif snapshot 생성
    """
    track_identity = conditioning_record.get("track_identity", {})
    song_intent = conditioning_record.get("song_intent", {})

    track_id = track_identity.get("track_id")
    artist_id = conditioning_record.get("artist_id") or track_identity.get("artist_id")
    mode_id = song_intent.get("mode_id") or conditioning_record.get("mode_id")

    raw_sections = conditioning_record.get("section_analysis") or []
    snapshots: List[SectionMotifSnapshot] = []

    for sec in raw_sections:
        section_name = str(sec.get("section") or sec.get("section_name") or "").strip()
        if not section_name:
            continue

        motifs = _collect_section_motifs(sec)
        if not motifs:
            continue

        dominant = motifs[:3]
        emotion_tags = _extract_emotion_tags(sec)

        snapshots.append(
            SectionMotifSnapshot(
                section_name=section_name,
                motifs=motifs,
                dominant_motifs=dominant,
                emotion_tags=emotion_tags,
                source_track_id=track_id,
                artist_id=artist_id,
                mode_id=mode_id,
            )
        )

    return snapshots


def classify_transition_type(
    src_snapshot: SectionMotifSnapshot,
    dst_snapshot: SectionMotifSnapshot,
    src_motif: str,
    dst_motif: str,
) -> Tuple[TransitionType, float, Dict[str, Any]]:
    """
    Rule-based 1차 분류기
    """
    src_emotions = set(src_snapshot.emotion_tags)
    dst_emotions = set(dst_snapshot.emotion_tags)

    shared_emotions = src_emotions & dst_emotions
    src_only = src_emotions - dst_emotions
    dst_only = dst_emotions - src_emotions

    same_motif = src_motif == dst_motif
    body_shift = ("body" in src_motif) or ("body" in dst_motif)  # placeholder heuristic

    evidence: Dict[str, Any] = {
        "shared_emotion_axis": sorted(shared_emotions),
        "src_only_emotions": sorted(src_only),
        "dst_only_emotions": sorted(dst_only),
        "section_shift": f"{src_snapshot.section_name}->{dst_snapshot.section_name}",
        "same_motif": same_motif,
        "body_shift_hint": body_shift,
    }

    if same_motif:
        return "sustain", 0.90, evidence

    if (shared_emotions & RELEASE_HINTS) or "chorus_final" in dst_snapshot.section_name:
        return "release", 0.72, evidence

    if shared_emotions & POSITIVE_EMOTION_HINTS:
        return "intensify", 0.74, evidence

    if (shared_emotions & NEGATIVE_EMOTION_HINTS) and dst_snapshot.section_name == "bridge":
        return "distort", 0.66, evidence

    if src_only and dst_only and not shared_emotions:
        return "invert", 0.61, evidence

    return "unknown", 0.35, evidence


def extract_track_motif_flow(
    conditioning_record: Dict[str, Any],
    *,
    max_dominant_motifs_per_section: int = 3,
) -> List[Dict[str, Any]]:
    """
    단일 트랙에서 section N -> section N+1 흐름 추출
    반환값은 이후 graph builder에서 aggregate 가능한 edge 후보 목록
    """
    snapshots = build_section_snapshots_from_conditioning(conditioning_record)
    if len(snapshots) < 2:
        return []

    edges: List[Dict[str, Any]] = []

    for idx in range(len(snapshots) - 1):
        src = snapshots[idx]
        dst = snapshots[idx + 1]

        src_motifs = src.dominant_motifs[:max_dominant_motifs_per_section]
        dst_motifs = dst.dominant_motifs[:max_dominant_motifs_per_section]

        if not src_motifs or not dst_motifs:
            continue

        for src_motif in src_motifs:
            for dst_motif in dst_motifs:
                transition_type, confidence, evidence = classify_transition_type(
                    src, dst, src_motif, dst_motif
                )

                edges.append(
                    {
                        "src_motif": src_motif,
                        "dst_motif": dst_motif,
                        "transition_type": transition_type,
                        "confidence": confidence,
                        "evidence": evidence,
                        "section_from": src.section_name,
                        "section_to": dst.section_name,
                        "artist_id": src.artist_id,
                        "mode_id": src.mode_id,
                        "track_id": src.source_track_id,
                    }
                )

    return edges

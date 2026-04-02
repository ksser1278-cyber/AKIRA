"""Novelty Index — Module Entry Point.

Provides the unified API for computing novelty profiles and building
corpus-wide novelty baselines. This is the primary integration surface
for the rest of the AKIRA ENGINE pipeline.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.akira_engine.corpus_intelligence.novelty.schema import (
    NeighborHit, NoveltyProfile,
)
from src.akira_engine.corpus_intelligence.novelty.similarity import (
    compute_text_similarity, compute_atom_jaccard, find_nearest_neighbor,
)
from src.akira_engine.corpus_intelligence.novelty.risk import (
    score_artist_imitation_risk, score_cliche_density, score_recombinative_novelty,
)
from src.akira_engine.features.mod import extract_atoms, categorize_atoms


# ─── Corpus Loader ───────────────────────────────────────────────────────────

def _load_external_corpus(project_root: Path) -> list[dict[str, Any]]:
    """Load external reference corpus from conditioning files across all artists.

    Scans data/<artist>/reference_tracks/*.conditioning.json for lyric text,
    then extracts atoms using features/mod.py.

    Returns list of dicts: {track_id, artist_id, text, atoms}
    """
    corpus: list[dict[str, Any]] = []
    data_dir = project_root / "data"

    if not data_dir.exists():
        return corpus

    for artist_dir in sorted(data_dir.iterdir()):
        if not artist_dir.is_dir() or artist_dir.name.startswith("_"):
            continue

        ref_dir = artist_dir / "reference_tracks"
        if not ref_dir.exists():
            continue

        artist_id = artist_dir.name
        for fpath in sorted(ref_dir.glob("*.conditioning.json")):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    cond = json.load(f)

                # Extract text from conditioning data
                # Schema: lyric_ground_truth.sections[].lines[]
                text = ""
                if isinstance(cond, dict):
                    # Primary: lyric_ground_truth.sections[].lines
                    lgt = cond.get("lyric_ground_truth", {})
                    if isinstance(lgt, dict):
                        sections = lgt.get("sections", [])
                        all_lines: list[str] = []
                        for sec in sections:
                            if isinstance(sec, dict):
                                sec_lines = sec.get("lines", [])
                                all_lines.extend(
                                    l for l in sec_lines if isinstance(l, str)
                                )
                        if all_lines:
                            text = "\n".join(all_lines)

                    # Fallback: section_analysis[].vocabulary_focus (motif-only)
                    if not text:
                        sa = cond.get("section_analysis", [])
                        vocab_parts: list[str] = []
                        for sec in sa:
                            if isinstance(sec, dict):
                                vocab_parts.extend(sec.get("vocabulary_focus", []))
                        if vocab_parts:
                            text = "\n".join(vocab_parts)

                    # Last resort: flat keys
                    if not text:
                        for key in ["lyrics_text", "lyrics"]:
                            val = cond.get(key, "")
                            if val:
                                text = val
                                break

                if not text or len(text) < 20:
                    continue

                # Extract atoms
                atoms = extract_atoms(text)
                track_id = fpath.stem.replace(".conditioning", "")

                corpus.append({
                    "track_id": f"{artist_id}/{track_id}",
                    "artist_id": artist_id,
                    "text": text,
                    "atoms": atoms,
                })
            except (json.JSONDecodeError, OSError):
                continue

    return corpus


def _load_internal_canon(project_root: Path) -> list[dict[str, Any]]:
    """Load internal canon (engine-generated Gold tracks).

    Reads from data/canon/internal_canon_registry.jsonl if available.
    (Week 8 will populate this; returns empty before then.)
    """
    canon_path = project_root / "data" / "canon" / "internal_canon_registry.jsonl"
    canon: list[dict[str, Any]] = []

    if not canon_path.exists():
        return canon

    try:
        with open(canon_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                entry = json.loads(raw_line)
                text = entry.get("text", "")
                atoms = entry.get("atoms", [])
                if not atoms and text:
                    atoms = extract_atoms(text)
                canon.append({
                    "track_id": entry.get("track_id", ""),
                    "artist_id": "internal",
                    "text": text,
                    "atoms": atoms,
                })
    except (json.JSONDecodeError, OSError):
        pass

    return canon


def _group_corpus_by_artist(corpus: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group corpus entries by artist_id for imitation risk scoring."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in corpus:
        aid = entry.get("artist_id", "")
        groups.setdefault(aid, []).append(entry)
    return groups

# Cached atom-cluster map (loaded once per session)
_CACHED_ATOM_CLUSTER_MAP: dict[str, str] | None = None

def _try_load_atom_cluster_map(project_root: Path) -> dict[str, str] | None:
    """Try to load atom→cluster map from Week 2 cluster data.

    Returns None if cluster data doesn't exist yet.
    """
    global _CACHED_ATOM_CLUSTER_MAP
    if _CACHED_ATOM_CLUSTER_MAP is not None:
        return _CACHED_ATOM_CLUSTER_MAP

    cluster_path = project_root / "data" / "clusters" / "style_clusters_v1.json"
    if not cluster_path.exists():
        return None

    try:
        with open(cluster_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct atom_cluster_map from cluster data
        acm: dict[str, str] = {}
        for cluster_data in data.get("clusters", []):
            cid = cluster_data.get("cluster_id", "")
            for atom in cluster_data.get("dominant_atoms", []):
                if atom not in acm:
                    acm[atom] = cid

        if acm:
            _CACHED_ATOM_CLUSTER_MAP = acm
            return acm
    except (json.JSONDecodeError, OSError):
        pass

    return None


# ─── Public API ──────────────────────────────────────────────────────────────

def compute_novelty_profile(
    candidate_text: str,
    candidate_atoms: list[str] | None = None,
    track_id: str = "candidate",
    target_artist_id: str = "",
    project_root: Path | None = None,
    external_corpus: list[dict[str, Any]] | None = None,
    internal_canon: list[dict[str, Any]] | None = None,
    cluster_memberships: list[str] | None = None,
    atom_cluster_map: dict[str, str] | None = None,
    top_k: int = 5,
) -> NoveltyProfile:
    """Compute a complete novelty profile for a generated candidate.

    This is the primary entry point for originality assessment.

    Args:
        candidate_text: Raw lyric text (may include section markers).
        candidate_atoms: Pre-extracted atoms, or None to auto-extract.
        track_id: Identifier for the candidate.
        target_artist_id: Artist the candidate was generated for (for imitation risk).
        project_root: Project root for corpus loading. Defaults to auto-detect.
        external_corpus: Pre-loaded external corpus (skips disk loading).
        internal_canon: Pre-loaded internal canon (skips disk loading).
        cluster_memberships: Cluster labels (available after Week 2).
        atom_cluster_map: Atom→cluster mapping (available after Week 2).
        top_k: Number of nearest neighbors to return.

    Returns:
        Fully populated NoveltyProfile.
    """
    # Auto-detect project root
    if project_root is None:
        project_root = Path(__file__).resolve().parents[4]  # src/akira_engine/corpus_intelligence/novelty → project root

    # Auto-extract atoms if not provided
    if candidate_atoms is None:
        candidate_atoms = extract_atoms(candidate_text)

    # Load corpora
    if external_corpus is None:
        external_corpus = _load_external_corpus(project_root)

    if internal_canon is None:
        internal_canon = _load_internal_canon(project_root)

    # 1. External nearest neighbors
    ext_neighbors = find_nearest_neighbor(
        candidate_text, candidate_atoms, external_corpus,
        top_k=top_k, exclude_track_id=track_id,
    )
    ext_top = ext_neighbors[0] if ext_neighbors else NeighborHit()
    ext_sim = ext_top.similarity

    # 2. Internal nearest neighbors
    int_neighbors = find_nearest_neighbor(
        candidate_text, candidate_atoms, internal_canon,
        top_k=top_k, exclude_track_id=track_id,
    )
    int_top = int_neighbors[0] if int_neighbors else NeighborHit()
    int_sim = int_top.similarity

    # 3. Artist imitation risk (against target artist's corpus only)
    artist_group = _group_corpus_by_artist(external_corpus)
    target_corpus = artist_group.get(target_artist_id, [])
    imit_risk = score_artist_imitation_risk(candidate_text, candidate_atoms, target_corpus)

    # 4. Cliché density
    cliche = score_cliche_density(candidate_text)

    # 5. Recombinative novelty
    # Auto-load cluster map from Week 2 data if available
    if atom_cluster_map is None:
        atom_cluster_map = _try_load_atom_cluster_map(project_root)

    recomb = score_recombinative_novelty(
        candidate_atoms,
        cluster_memberships=cluster_memberships,
        atom_cluster_map=atom_cluster_map,
    )

    profile = NoveltyProfile(
        track_id=track_id,
        nearest_external_track=ext_top,
        nearest_internal_track=int_top,
        external_similarity=ext_sim,
        internal_similarity=int_sim,
        artist_imitation_risk=imit_risk,
        cliche_density=cliche,
        recombinative_novelty=recomb,
        top_k_external=ext_neighbors,
        top_k_internal=int_neighbors,
        status="scored",
    )
    return profile


def build_novelty_index(
    project_root: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a corpus-wide novelty baseline.

    Computes novelty profiles for all tracks in the external corpus,
    establishing baseline distributions for similarity, imitation risk,
    cliché density, and recombinative novelty.

    The output serves as a reference frame for judging generated candidates.

    Args:
        project_root: Project root. Defaults to auto-detect.
        output_path: Output file path. Defaults to data/novelty/novelty_index_v1.json.

    Returns:
        Index dict with statistics and per-track profiles.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parents[4]

    if output_path is None:
        output_path = project_root / "data" / "novelty" / "novelty_index_v1.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    external_corpus = _load_external_corpus(project_root)
    internal_canon = _load_internal_canon(project_root)

    profiles: list[dict[str, Any]] = []
    sim_scores: list[float] = []
    imit_scores: list[float] = []
    cliche_scores: list[float] = []
    recomb_scores: list[float] = []

    for i, entry in enumerate(external_corpus):
        track_id = entry["track_id"]
        artist_id = entry["artist_id"]
        text = entry["text"]
        atoms = entry["atoms"]

        profile = compute_novelty_profile(
            candidate_text=text,
            candidate_atoms=atoms,
            track_id=track_id,
            target_artist_id=artist_id,
            project_root=project_root,
            external_corpus=external_corpus,
            internal_canon=internal_canon,
            top_k=3,
        )

        d = profile.to_dict()
        profiles.append(d)
        sim_scores.append(profile.external_similarity)
        imit_scores.append(profile.artist_imitation_risk)
        cliche_scores.append(profile.cliche_density)
        recomb_scores.append(profile.recombinative_novelty)

    # Compute statistics
    def _stats(scores: list[float]) -> dict[str, float]:
        if not scores:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}
        sorted_s = sorted(scores)
        n = len(sorted_s)
        return {
            "mean": round(sum(sorted_s) / n, 4),
            "min": round(sorted_s[0], 4),
            "max": round(sorted_s[-1], 4),
            "median": round(sorted_s[n // 2], 4),
        }

    index = {
        "version": "1.0",
        "corpus_size": len(external_corpus),
        "canon_size": len(internal_canon),
        "statistics": {
            "external_similarity": _stats(sim_scores),
            "artist_imitation_risk": _stats(imit_scores),
            "cliche_density": _stats(cliche_scores),
            "recombinative_novelty": _stats(recomb_scores),
        },
        "profiles": profiles,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return index

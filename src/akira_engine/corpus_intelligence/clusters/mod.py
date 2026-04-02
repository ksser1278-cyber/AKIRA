"""Style Clusters — Module Entry Point.

Provides the unified API for building cluster maps and assigning
cluster memberships. Integrates vectorization, clustering, labeling,
and atom-cluster mapping into a single workflow.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.akira_engine.corpus_intelligence.clusters.schema import (
    StyleCluster, ClusterAssignment, ClusterMap,
)
from src.akira_engine.corpus_intelligence.clusters.clustering import (
    vectorize_corpus, vectorize_track, cluster_tracks_by_expression,
    assign_cluster_membership, _build_vocabulary,
)
from src.akira_engine.corpus_intelligence.clusters.labels import (
    label_cluster, find_distant_cluster_pairs, build_atom_cluster_map,
)
from src.akira_engine.corpus_intelligence.novelty.mod import _load_external_corpus
from src.akira_engine.features.mod import categorize_atoms, calculate_abstract_ratio


# ─── Cluster Construction ────────────────────────────────────────────────────

def _determine_optimal_k(n_tracks: int) -> int:
    """Heuristic for choosing k based on corpus size.

    Target: 8-12 clusters for 100 tracks, scaling gently.
    """
    if n_tracks < 20:
        return max(3, n_tracks // 3)
    elif n_tracks < 60:
        return 8
    elif n_tracks < 150:
        return 10
    elif n_tracks < 300:
        return 12
    else:
        return 15


def _build_cluster_objects(
    corpus: list[dict[str, Any]],
    assignments: list[int],
    centroids: list[list[float]],
    k: int,
) -> list[StyleCluster]:
    """Convert raw K-Means output into StyleCluster objects with labels."""
    clusters: list[StyleCluster] = []

    for j in range(k):
        member_indices = [i for i, a in enumerate(assignments) if a == j]
        if not member_indices:
            continue

        # Collect member data
        member_ids = [corpus[i]["track_id"] for i in member_indices]
        member_artists = [corpus[i]["artist_id"] for i in member_indices]

        # Aggregate atoms
        all_atoms: list[str] = []
        body_total, scene_total, sound_total, motif_total = 0, 0, 0, 0
        abstract_sum = 0.0
        atom_count_sum = 0

        for idx in member_indices:
            atoms = corpus[idx].get("atoms", [])
            text = corpus[idx].get("text", "")
            all_atoms.extend(atoms)
            atom_count_sum += len(atoms)
            abstract_sum += calculate_abstract_ratio(text)

            body, scene, sound, motif = categorize_atoms(atoms)
            body_total += len(body)
            scene_total += len(scene)
            sound_total += len(sound)
            motif_total += len(motif)

        n_members = len(member_indices)
        total_atoms = max(body_total + scene_total + sound_total + motif_total, 1)

        category_ratios = {
            "body": round(body_total / total_atoms, 4),
            "scene": round(scene_total / total_atoms, 4),
            "sound": round(sound_total / total_atoms, 4),
            "motif": round(motif_total / total_atoms, 4),
        }

        # Top atoms by frequency
        atom_counter = Counter(all_atoms)
        dominant_atoms = [a for a, _ in atom_counter.most_common(20)]

        # Auto-label
        avg_abstract = abstract_sum / n_members
        avg_atom_count = atom_count_sum / n_members
        cluster_label, emotional_profile = label_cluster(
            dominant_atoms, category_ratios, avg_abstract, avg_atom_count,
        )

        # Unique artist diversity as structure pattern
        artist_dist = Counter(member_artists).most_common(3)
        structure_patterns = [f"{art}({cnt})" for art, cnt in artist_dist]

        cluster_id = f"cluster_{j:02d}"
        clusters.append(StyleCluster(
            cluster_id=cluster_id,
            label=cluster_label,
            size=n_members,
            dominant_atoms=dominant_atoms,
            dominant_categories=category_ratios,
            dominant_structure_patterns=structure_patterns,
            emotional_profile=emotional_profile,
            centroid=centroids[j] if j < len(centroids) else [],
            member_track_ids=member_ids,
        ))

    return clusters


# ─── Public API ──────────────────────────────────────────────────────────────

def build_cluster_map(
    project_root: Path | None = None,
    k: int | None = None,
    output_path: Path | None = None,
    top_n_vocab: int = 50,
) -> ClusterMap:
    """Build a complete cluster map from the corpus.

    This is the primary entry point for Week 2.

    Args:
        project_root: Project root. Defaults to auto-detect.
        k: Number of clusters. Auto if None.
        output_path: Output file path. Defaults to data/clusters/style_clusters_v1.json.
        top_n_vocab: Size of atom vocabulary for vectorization.

    Returns:
        Fully populated ClusterMap.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parents[4]

    if output_path is None:
        output_path = project_root / "data" / "clusters" / "style_clusters_v1.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load corpus
    corpus = _load_external_corpus(project_root)
    if not corpus:
        empty = ClusterMap()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(empty.to_dict(), f, ensure_ascii=False, indent=2)
        return empty

    # Determine k
    if k is None:
        k = _determine_optimal_k(len(corpus))

    # Vectorize
    vectors, vocabulary = vectorize_corpus(corpus, top_n=top_n_vocab)

    # Cluster
    assignments_idx, centroids = cluster_tracks_by_expression(vectors, k=k)

    # Build cluster objects
    clusters = _build_cluster_objects(corpus, assignments_idx, centroids, k)

    # Sort by size descending
    clusters.sort(key=lambda c: c.size, reverse=True)

    # Build per-track assignments
    cluster_ids = [c.cluster_id for c in clusters]
    cluster_centroids = [c.centroid for c in clusters]

    track_assignments: list[ClusterAssignment] = []
    for i, entry in enumerate(corpus):
        ca = assign_cluster_membership(vectors[i], cluster_centroids, cluster_ids)
        ca.track_id = entry["track_id"]
        track_assignments.append(ca)

    # Build atom → cluster map
    atom_cluster_map = build_atom_cluster_map(clusters)

    # Assemble result
    cluster_map = ClusterMap(
        version="1.0",
        k=len(clusters),
        clusters=clusters,
        assignments=track_assignments,
        atom_cluster_map=atom_cluster_map,
    )

    # Save
    output_data = cluster_map.to_dict()
    # Add distant pairs for creative recombination
    distant_pairs = find_distant_cluster_pairs(clusters, cluster_centroids, top_n=5)
    output_data["distant_pairs"] = [
        {"a": a, "b": b, "distance": d} for a, b, d in distant_pairs
    ]
    # Add vocabulary for future vectorization
    output_data["vocabulary"] = vocabulary

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return cluster_map


def assign_cluster_membership_for_candidate(
    candidate_text: str,
    candidate_atoms: list[str] | None = None,
    cluster_map: ClusterMap | None = None,
    project_root: Path | None = None,
) -> ClusterAssignment:
    """Assign cluster membership to a new candidate (generated lyric).

    Loads the cluster map from disk if not provided, vectorizes the
    candidate using the saved vocabulary, and returns assignment.

    Args:
        candidate_text: Raw lyric text.
        candidate_atoms: Pre-extracted atoms, or None to auto-extract.
        cluster_map: Pre-loaded ClusterMap (skips disk I/O if provided).
        project_root: Project root for loading saved data.

    Returns:
        ClusterAssignment for the candidate.
    """
    from src.akira_engine.features.mod import extract_atoms

    if project_root is None:
        project_root = Path(__file__).resolve().parents[4]

    if candidate_atoms is None:
        candidate_atoms = extract_atoms(candidate_text)

    # Load vocabulary and centroids from saved cluster data
    cluster_path = project_root / "data" / "clusters" / "style_clusters_v1.json"
    if not cluster_path.exists():
        return ClusterAssignment(track_id="candidate")

    with open(cluster_path, "r", encoding="utf-8") as f:
        saved = json.load(f)

    vocabulary = saved.get("vocabulary", [])
    if not vocabulary:
        return ClusterAssignment(track_id="candidate")

    # Vectorize candidate
    vector = vectorize_track(candidate_text, candidate_atoms, vocabulary)

    # Get cluster centroids and IDs
    if cluster_map and cluster_map.clusters:
        cluster_ids = [c.cluster_id for c in cluster_map.clusters]
        centroids = [c.centroid for c in cluster_map.clusters]
    else:
        # Reconstruct from saved data
        clusters_data = saved.get("clusters", [])
        cluster_ids = [c.get("cluster_id", f"cluster_{i:02d}") for i, c in enumerate(clusters_data)]
        # Need to reload centroids - not in to_dict(), load from ClusterMap
        # Fallback: use cluster assignments to approximate
        return ClusterAssignment(track_id="candidate")

    return assign_cluster_membership(vector, centroids, cluster_ids)

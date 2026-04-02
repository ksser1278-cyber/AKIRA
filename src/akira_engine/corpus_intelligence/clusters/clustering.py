"""Style Clusters — Pure-Python K-Means Clustering.

Implements feature-profile-based clustering without external ML dependencies.
Uses a vectorized atom representation + K-Means for corpus segmentation.

The feature vector per track is:
  [body_ratio, scene_ratio, sound_ratio, motif_ratio, abstract_ratio, repeat_density,
   atom_count_norm, ...top_N_atom_presence]

This keeps the engine dependency-free while producing meaningful clusters.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any

from src.akira_engine.features.mod import (
    extract_atoms, categorize_atoms, calculate_abstract_ratio,
    BODY_KEYWORDS, SCENE_KEYWORDS, SOUND_KEYWORDS,
)
from src.akira_engine.corpus_intelligence.clusters.schema import (
    ClusterAssignment,
)


# ─── Feature Vectorization ──────────────────────────────────────────────────

def _build_vocabulary(corpus: list[dict[str, Any]], top_n: int = 50) -> list[str]:
    """Build a vocabulary of the top-N most frequent atoms for one-hot encoding."""
    counter: Counter = Counter()
    for entry in corpus:
        counter.update(entry.get("atoms", []))
    return [atom for atom, _ in counter.most_common(top_n)]


def vectorize_track(
    text: str,
    atoms: list[str],
    vocabulary: list[str],
) -> list[float]:
    """Convert a track's features into a numerical vector.

    Vector layout (6 + len(vocabulary) dimensions):
      [0] body_ratio      — fraction of atoms in body category
      [1] scene_ratio     — fraction in scene
      [2] sound_ratio     — fraction in sound
      [3] motif_ratio     — fraction in motif/other
      [4] abstract_ratio  — abstract phrasing density
      [5] atom_count_norm — normalized atom count (0-1, capped at 60)
      [6..] atom_presence — binary presence of each vocab atom

    Returns:
        Float vector of fixed dimension.
    """
    body, scene, sound, motif = categorize_atoms(atoms)
    total = max(len(atoms), 1)

    vec: list[float] = [
        len(body) / total,           # body_ratio
        len(scene) / total,          # scene_ratio
        len(sound) / total,          # sound_ratio
        len(motif) / total,          # motif_ratio
        calculate_abstract_ratio(text),  # abstract_ratio
        min(len(atoms) / 60.0, 1.0), # atom_count_norm
    ]

    # Atom presence features
    atom_set = set(atoms)
    for vocab_atom in vocabulary:
        vec.append(1.0 if vocab_atom in atom_set else 0.0)

    return vec


def vectorize_corpus(
    corpus: list[dict[str, Any]],
    vocabulary: list[str] | None = None,
    top_n: int = 50,
) -> tuple[list[list[float]], list[str]]:
    """Vectorize entire corpus.

    Returns:
        Tuple of (vectors, vocabulary) where vectors[i] corresponds to corpus[i].
    """
    if vocabulary is None:
        vocabulary = _build_vocabulary(corpus, top_n=top_n)

    vectors = []
    for entry in corpus:
        text = entry.get("text", "")
        atoms = entry.get("atoms", [])
        vectors.append(vectorize_track(text, atoms, vocabulary))

    return vectors, vocabulary


# ─── Pure-Python K-Means ─────────────────────────────────────────────────────

def _euclidean_distance(a: list[float], b: list[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _centroid(vectors: list[list[float]]) -> list[float]:
    """Compute the centroid (mean) of a set of vectors."""
    if not vectors:
        return []
    dim = len(vectors[0])
    n = len(vectors)
    return [sum(v[d] for v in vectors) / n for d in range(dim)]


def _kmeans_plusplus_init(vectors: list[list[float]], k: int, seed: int = 42) -> list[list[float]]:
    """K-Means++ initialization for better initial centroids."""
    rng = random.Random(seed)
    n = len(vectors)
    if n <= k:
        return [v[:] for v in vectors]

    # Pick first centroid randomly
    centroids = [vectors[rng.randint(0, n - 1)][:]]

    for _ in range(1, k):
        # Compute min distance to nearest existing centroid for each point
        dists = []
        for v in vectors:
            min_d = min(_euclidean_distance(v, c) for c in centroids)
            dists.append(min_d ** 2)

        # Weighted random selection
        total = sum(dists)
        if total == 0:
            centroids.append(vectors[rng.randint(0, n - 1)][:])
            continue

        threshold = rng.random() * total
        cumulative = 0.0
        for i, d in enumerate(dists):
            cumulative += d
            if cumulative >= threshold:
                centroids.append(vectors[i][:])
                break
        else:
            centroids.append(vectors[-1][:])

    return centroids


def cluster_tracks_by_expression(
    vectors: list[list[float]],
    k: int = 10,
    max_iter: int = 50,
    seed: int = 42,
) -> tuple[list[int], list[list[float]]]:
    """Cluster feature vectors using K-Means.

    Args:
        vectors: List of feature vectors (all same dimension).
        k: Number of clusters.
        max_iter: Maximum iterations.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (assignments, centroids) where:
          - assignments[i] = cluster index for vectors[i]
          - centroids[j] = centroid vector for cluster j
    """
    n = len(vectors)
    if n == 0:
        return [], []

    k = min(k, n)  # Can't have more clusters than points

    # Initialize with K-Means++
    centroids = _kmeans_plusplus_init(vectors, k, seed=seed)
    assignments = [0] * n

    for iteration in range(max_iter):
        # Assignment step
        changed = False
        for i, v in enumerate(vectors):
            dists = [_euclidean_distance(v, c) for c in centroids]
            best = min(range(k), key=lambda j: dists[j])
            if assignments[i] != best:
                assignments[i] = best
                changed = True

        # Early termination
        if not changed:
            break

        # Update step
        new_centroids = []
        for j in range(k):
            members = [vectors[i] for i in range(n) if assignments[i] == j]
            if members:
                new_centroids.append(_centroid(members))
            else:
                # Empty cluster: re-initialize from farthest point
                new_centroids.append(centroids[j])
        centroids = new_centroids

    return assignments, centroids


def assign_cluster_membership(
    vector: list[float],
    centroids: list[list[float]],
    cluster_ids: list[str],
) -> ClusterAssignment:
    """Assign a single vector to the nearest cluster(s).

    Returns ClusterAssignment with distances and normalized membership scores.
    """
    if not centroids:
        return ClusterAssignment()

    distances: dict[str, float] = {}
    for i, centroid in enumerate(centroids):
        cid = cluster_ids[i] if i < len(cluster_ids) else f"cluster_{i:02d}"
        distances[cid] = round(_euclidean_distance(vector, centroid), 4)

    # Convert distances to similarity scores (inverse distance, normalized)
    max_dist = max(distances.values()) if distances else 1.0
    if max_dist == 0:
        max_dist = 1.0

    scores: dict[str, float] = {}
    total_inv = 0.0
    inv_dists: dict[str, float] = {}
    for cid, dist in distances.items():
        inv = max(0.0, 1.0 - (dist / (max_dist * 1.5)))  # Soft normalization
        inv_dists[cid] = inv
        total_inv += inv

    for cid, inv in inv_dists.items():
        scores[cid] = round(inv / total_inv, 4) if total_inv > 0 else 0.0

    # Sort by score
    sorted_ids = sorted(scores.keys(), key=lambda c: scores[c], reverse=True)
    primary = sorted_ids[0] if sorted_ids else ""
    secondary = sorted_ids[1] if len(sorted_ids) > 1 else ""

    return ClusterAssignment(
        primary_cluster=primary,
        secondary_cluster=secondary,
        distances=distances,
        membership_scores=scores,
    )

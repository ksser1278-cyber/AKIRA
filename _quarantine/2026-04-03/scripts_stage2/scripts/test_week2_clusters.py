"""Smoke Test: Week 2 - Style Clusters.

Validates the corpus_intelligence.clusters module by:
1. Vectorizing corpus tracks
2. Running K-Means clustering
3. Verifying auto-labeling
4. Building a full cluster map
5. Testing cluster assignment for new candidates
6. Verifying distant pair discovery
"""

from __future__ import annotations

import io
import sys
import time
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

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
from src.akira_engine.corpus_intelligence.clusters.mod import (
    build_cluster_map,
)
from src.akira_engine.corpus_intelligence.novelty.mod import _load_external_corpus
from src.akira_engine.features.mod import extract_atoms


def _separator(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_schema():
    """Test: Schema objects can be instantiated."""
    _separator("Test 1: Schema Instantiation")

    sc = StyleCluster(
        cluster_id="cluster_00",
        label="dark_somatic",
        size=5,
        dominant_atoms=["痛み", "叫び"],
    )
    print(f"  cluster_id: {sc.cluster_id}")
    print(f"  label: {sc.label}")
    print(f"  to_dict keys: {list(sc.to_dict().keys())}")

    cm = ClusterMap(k=3)
    print(f"  ClusterMap k={cm.k}")
    assert sc.cluster_id == "cluster_00"
    print("  PASSED")


def test_vectorization():
    """Test: Corpus vectorization produces correct dimensions."""
    _separator("Test 2: Vectorization")

    corpus = _load_external_corpus(PROJECT_ROOT)
    if not corpus:
        print("  No corpus - SKIPPED")
        return

    vectors, vocabulary = vectorize_corpus(corpus, top_n=50)
    expected_dim = 6 + len(vocabulary)  # 6 base features + vocab atoms

    print(f"  Corpus size: {len(corpus)}")
    print(f"  Vocabulary size: {len(vocabulary)}")
    print(f"  Vector dimension: {len(vectors[0])}")
    print(f"  Expected dimension: {expected_dim}")
    assert len(vectors) == len(corpus), "One vector per track"
    assert all(len(v) == expected_dim for v in vectors), "All vectors same dimension"
    print(f"  Sample vector[:6]: {[round(v, 3) for v in vectors[0][:6]]}")
    print("  PASSED")


def test_kmeans():
    """Test: K-Means produces valid clusters."""
    _separator("Test 3: K-Means Clustering")

    corpus = _load_external_corpus(PROJECT_ROOT)
    if not corpus:
        print("  No corpus - SKIPPED")
        return

    vectors, vocab = vectorize_corpus(corpus, top_n=50)
    k = 10
    assignments, centroids = cluster_tracks_by_expression(vectors, k=k)

    print(f"  k={k}, tracks={len(corpus)}")
    print(f"  Centroids: {len(centroids)}")
    print(f"  Assignments: {len(assignments)}")

    # Check cluster sizes
    from collections import Counter
    sizes = Counter(assignments)
    print(f"  Cluster sizes: {dict(sorted(sizes.items()))}")
    print(f"  Non-empty clusters: {len(sizes)}")
    assert len(assignments) == len(corpus)
    assert all(0 <= a < k for a in assignments)
    assert len(sizes) >= 3, "Should have at least 3 non-empty clusters"
    print("  PASSED")


def test_labeling():
    """Test: Auto-labeling produces meaningful labels."""
    _separator("Test 4: Auto-Labeling")

    # Dark, body-heavy cluster
    dark_atoms = ["痛み", "血", "叫び", "壊れ", "毒", "心", "闇"]
    dark_ratios = {"body": 0.2, "scene": 0.05, "sound": 0.05, "motif": 0.7}
    label, emotions = label_cluster(dark_atoms, dark_ratios, abstract_ratio=0.1)
    print(f"  Dark cluster label: {label}")
    print(f"  Dark cluster emotions: {emotions}")
    assert "somatic" in label or "dark" in label, f"Expected dark/somatic label, got: {label}"

    # Warm, scene-heavy cluster
    warm_atoms = ["愛", "笑顔", "桜", "光", "花", "大切な"]
    warm_ratios = {"body": 0.02, "scene": 0.2, "sound": 0.03, "motif": 0.75}
    label2, emotions2 = label_cluster(warm_atoms, warm_ratios, abstract_ratio=0.05)
    print(f"  Warm cluster label: {label2}")
    print(f"  Warm cluster emotions: {emotions2}")
    assert label != label2, "Different clusters should get different labels"
    print("  PASSED")


def test_full_cluster_map():
    """Test: Full cluster map build."""
    _separator("Test 5: Full Cluster Map Build")

    t0 = time.time()
    cluster_map = build_cluster_map(
        project_root=PROJECT_ROOT,
        output_path=PROJECT_ROOT / "data" / "clusters" / "style_clusters_v1.json",
    )
    elapsed = time.time() - t0

    print(f"  k={cluster_map.k}")
    print(f"  Clusters: {len(cluster_map.clusters)}")
    print(f"  Assignments: {len(cluster_map.assignments)}")
    print(f"  Atom-cluster map size: {len(cluster_map.atom_cluster_map)}")
    print(f"  Elapsed: {elapsed:.2f}s")

    # Print cluster summary
    for c in cluster_map.clusters:
        print(f"    {c.cluster_id} [{c.label}] size={c.size} emotions={c.emotional_profile}")
        print(f"      top atoms: {c.dominant_atoms[:8]}")

    assert cluster_map.k >= 3, "Should have at least 3 clusters"
    assert len(cluster_map.assignments) > 0, "Should have assignments"

    # Verify artist distribution
    for c in cluster_map.clusters:
        artists_in = set()
        for tid in c.member_track_ids:
            parts = tid.split("/")
            if parts:
                artists_in.add(parts[0])
        print(f"    {c.cluster_id}: {len(artists_in)} artists, {c.size} tracks")

    print("  PASSED")


def test_assignment():
    """Test: Cluster assignment for new candidate."""
    _separator("Test 6: Candidate Assignment")

    cluster_map = build_cluster_map(project_root=PROJECT_ROOT)

    candidate_text = (
        "[Verse 1]\n"
        "蛍光灯の隙間から差し込む光\n"
        "指先に絡む静電気みたいに\n"
        "喉の奥が焼けるようなこの感覚\n"
        "体温の名残だけが残っている\n"
    )
    candidate_atoms = extract_atoms(candidate_text)

    # Vectorize and assign
    from src.akira_engine.corpus_intelligence.clusters.clustering import (
        vectorize_track, _build_vocabulary,
    )
    vocab = _build_vocabulary(
        _load_external_corpus(PROJECT_ROOT), top_n=50,
    )
    vector = vectorize_track(candidate_text, candidate_atoms, vocab)

    cluster_ids = [c.cluster_id for c in cluster_map.clusters]
    centroids = [c.centroid for c in cluster_map.clusters]
    assignment = assign_cluster_membership(vector, centroids, cluster_ids)

    print(f"  Primary cluster: {assignment.primary_cluster}")
    print(f"  Secondary cluster: {assignment.secondary_cluster}")
    print(f"  Top scores: ", end="")
    for cid in assignment.cluster_ids()[:3]:
        print(f"{cid}={assignment.membership_scores[cid]:.3f} ", end="")
    print()
    assert assignment.primary_cluster != "", "Should have a primary cluster"
    print("  PASSED")


def test_distant_pairs():
    """Test: Distant pair discovery."""
    _separator("Test 7: Distant Cluster Pairs")

    cluster_map = build_cluster_map(project_root=PROJECT_ROOT)
    centroids = [c.centroid for c in cluster_map.clusters]
    pairs = find_distant_cluster_pairs(cluster_map.clusters, centroids, top_n=5)

    print(f"  Top distant pairs:")
    for a, b, dist in pairs:
        # Find labels
        label_a = next((c.label for c in cluster_map.clusters if c.cluster_id == a), "?")
        label_b = next((c.label for c in cluster_map.clusters if c.cluster_id == b), "?")
        print(f"    {a}[{label_a}] <-> {b}[{label_b}] distance={dist:.4f}")

    assert len(pairs) > 0, "Should find at least one distant pair"
    print("  PASSED")


def test_atom_cluster_map():
    """Test: Atom-cluster map for Week 1 integration."""
    _separator("Test 8: Atom-Cluster Map (Week 1 Integration)")

    cluster_map = build_cluster_map(project_root=PROJECT_ROOT)
    acm = cluster_map.atom_cluster_map

    print(f"  Atom-cluster map entries: {len(acm)}")
    # Show sample entries
    sample_atoms = list(acm.items())[:10]
    for atom, cid in sample_atoms:
        label = next((c.label for c in cluster_map.clusters if c.cluster_id == cid), "?")
        print(f"    {atom} -> {cid} [{label}]")

    assert len(acm) > 0, "Should have atom mappings"
    print("  PASSED")


if __name__ == "__main__":
    print("===========================================================")
    print("  AKIRA ENGINE - Week 2 Smoke Test: Style Clusters")
    print("===========================================================")

    tests = [
        test_schema,
        test_vectorization,
        test_kmeans,
        test_labeling,
        test_full_cluster_map,
        test_assignment,
        test_distant_pairs,
        test_atom_cluster_map,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    _separator("Summary")
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n  All tests passed!")
        sys.exit(0)

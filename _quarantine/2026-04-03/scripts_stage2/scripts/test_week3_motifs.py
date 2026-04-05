# scripts/test_week3_motifs.py

from __future__ import annotations

import json
import tempfile
import unittest
import sys
import io
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> AKIRA ENGINE
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.akira_engine.corpus_intelligence.motifs.graph import (
    build_motif_transition_graph,
    sample_transition_chain,
    save_motif_graph,
    score_transition_novelty,
)
from src.akira_engine.corpus_intelligence.motifs.mining import (
    extract_track_motif_flow,
)
from src.akira_engine.corpus_intelligence.motifs.mod import (
    build_motif_graph_index,
)


def _conditioning_record(
    *,
    track_id: str,
    artist_id: str = "pinocchiop",
    mode_id: str = "direct_emotional_pop",
    sections: list[dict],
) -> dict:
    return {
        "artist_id": artist_id,
        "track_identity": {
            "track_id": track_id,
            "artist_id": artist_id,
        },
        "song_intent": {
            "mode_id": mode_id,
        },
        "section_analysis": sections,
    }


def _sample_records() -> list[dict]:
    """
    support_count가 2 이상 되는 전이를 일부 만들기 위해
    유사한 흐름을 가진 레코드를 2개 이상 준비한다.
    """
    rec1 = _conditioning_record(
        track_id="track_001",
        sections=[
            {
                "section": "verse_1",
                "motifs": ["革命", "火花", "喉"],
                "emotion_tags": ["tension", "surge"],
            },
            {
                "section": "pre_chorus",
                "motifs": ["喉", "熱", "鼓動"],
                "emotion_tags": ["surge", "obsession"],
            },
            {
                "section": "chorus",
                "motifs": ["爆発", "解放", "光"],
                "emotion_tags": ["release", "impact"],
            },
        ],
    )

    rec2 = _conditioning_record(
        track_id="track_002",
        sections=[
            {
                "section": "verse_1",
                "motifs": ["革命", "視線", "雑音"],
                "emotion_tags": ["tension", "surge"],
            },
            {
                "section": "pre_chorus",
                "motifs": ["熱", "鼓동", "視線"],
                "emotion_tags": ["surge", "obsession"],
            },
            {
                "section": "chorus",
                "motifs": ["解放", "光", "叫び"],
                "emotion_tags": ["release", "impact"],
            },
        ],
    )

    rec3 = _conditioning_record(
        track_id="track_003",
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        sections=[
            {
                "section": "verse_1",
                "motifs": ["毒", "視線", "ノイズ"],
                "emotion_tags": ["distance", "decay"],
            },
            {
                "section": "bridge",
                "motifs": ["歪み", "崩壊", "熱"],
                "emotion_tags": ["collapse", "distort"],
            },
            {
                "section": "chorus_final",
                "motifs": ["解放", "残響", "光"],
                "emotion_tags": ["release", "breakthrough"],
            },
        ],
    )

    return [rec1, rec2, rec3]


class TestWeek3Motifs(unittest.TestCase):
    def setUp(self) -> None:
        self.records = _sample_records()

    def test_extract_track_motif_flow_not_empty(self) -> None:
        edges = extract_track_motif_flow(self.records[0])
        self.assertTrue(edges, "단일 트랙에서 motif flow가 비어 있으면 안 됩니다.")

        required_keys = {
            "src_motif",
            "dst_motif",
            "transition_type",
            "confidence",
            "section_from",
            "section_to",
            "track_id",
        }
        self.assertTrue(required_keys.issubset(edges[0].keys()))

    def test_low_support_edges_are_pruned(self) -> None:
        # rec3만 있을 때는 support_count=1 edge가 많으므로 대부분 pruning되어야 한다.
        single_edges = extract_track_motif_flow(self.records[2])
        graph = build_motif_transition_graph(single_edges, min_support_count=2)

        self.assertEqual(
            graph.edge_count,
            0,
            "support_count가 min_support_count보다 낮은 edge는 pruning되어야 합니다.",
        )

    def test_graph_build_and_save_schema(self) -> None:
        all_edges = []
        for record in self.records:
            all_edges.extend(extract_track_motif_flow(record))

        graph = build_motif_transition_graph(all_edges, min_support_count=2)

        self.assertGreaterEqual(graph.node_count, 1)
        self.assertGreaterEqual(graph.edge_count, 1)
        self.assertIsInstance(graph.transitions, dict)
        self.assertIsInstance(graph.motif_stats, dict)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "motif_transition_graph_v1.json"
            save_motif_graph(graph, out)

            self.assertTrue(out.exists(), "그래프 JSON 파일이 저장되어야 합니다.")
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("version", payload)
            self.assertIn("transitions", payload)
            self.assertIn("motif_stats", payload)

    def test_sampled_transition_chain_is_connected(self) -> None:
        all_edges = []
        for record in self.records:
            all_edges.extend(extract_track_motif_flow(record))

        graph = build_motif_transition_graph(all_edges, min_support_count=2)

        chain = sample_transition_chain(
            graph,
            start_motif="革命",
            max_steps=4,
        )

        self.assertTrue(chain, "샘플링된 전이 체인이 비어 있으면 안 됩니다.")

        for i, step in enumerate(chain):
            self.assertIn("src_motif", step)
            self.assertIn("dst_motif", step)
            self.assertIn("transition_type", step)

            if i > 0:
                self.assertEqual(
                    chain[i - 1]["dst_motif"],
                    step["src_motif"],
                    "전이 체인의 연결성이 끊기면 안 됩니다.",
                )

    def test_novelty_score_range(self) -> None:
        all_edges = []
        for record in self.records:
            all_edges.extend(extract_track_motif_flow(record))

        graph = build_motif_transition_graph(all_edges, min_support_count=2)
        chain = sample_transition_chain(graph, start_motif="革命", max_steps=3)
        score = score_transition_novelty(graph, chain)

        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_self_loop_not_exclusive_in_mixed_corpus(self) -> None:
        """
        self-loop 자체를 금지하지는 않지만,
        혼합 코퍼스에서 self-loop만 남는 형태로 그래프가 붕괴되면 안 된다.
        """
        all_edges = []
        for record in self.records:
            all_edges.extend(extract_track_motif_flow(record))

        graph = build_motif_transition_graph(all_edges, min_support_count=2)

        non_self_edges = 0
        total_edges = 0
        for src_motif, edges in graph.transitions.items():
            for edge in edges:
                total_edges += 1
                if edge.dst_motif != src_motif:
                    non_self_edges += 1

        self.assertGreater(total_edges, 0)
        self.assertGreater(
            non_self_edges,
            0,
            "혼합 코퍼스 그래프에서 self-loop만 남는 것은 비정상입니다.",
        )

    def test_build_motif_graph_index_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "motif_transition_graph_v1.json"
            result = build_motif_graph_index(
                self.records,
                output_path=out,
                min_support_count=2,
            )

            self.assertTrue(out.exists())
            self.assertEqual(result["output_path"], str(out))
            self.assertIn("node_count", result)
            self.assertIn("edge_count", result)

    def test_theme_conditioned_sampling_smoke(self) -> None:
        """
        시작 주제가 완전히 무관한 단어로 즉시 붕 뜨지 않는지 보는 smoke test.
        여기서는 '革命'에서 시작했을 때 최소한 1-step은 실제 graph edge를 타야 한다.
        """
        all_edges = []
        for record in self.records:
            all_edges.extend(extract_track_motif_flow(record))

        graph = build_motif_transition_graph(all_edges, min_support_count=2)
        chain = sample_transition_chain(graph, start_motif="革命", max_steps=1)

        self.assertEqual(len(chain), 1)
        first = chain[0]

        valid_dsts = {
            edge.dst_motif
            for edge in graph.transitions.get("革命", [])
        }
        self.assertIn(
            first["dst_motif"],
            valid_dsts,
            "시작 motif에서 실제 존재하는 edge로만 샘플링되어야 합니다.",
        )


if __name__ == "__main__":
    unittest.main()

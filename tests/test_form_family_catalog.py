import json

from src.akira_engine.form_family_catalog import build_form_family_catalog


def _write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_build_form_family_catalog_clusters_tracks(tmp_path):
    behavior_root = tmp_path / "lyric_behavior" / "fixture_v1"
    behavior_root.mkdir(parents=True)

    line_path = behavior_root / "line_behavior_records.jsonl"
    phrase_path = behavior_root / "phrase_behavior_records.jsonl"
    chorus_path = behavior_root / "chorus_behavior_records.jsonl"

    line_rows = [
        {"track_id": "artist1_compact", "artist_id": "maretu", "section_name": "verse_1", "cadence_shape": "balanced", "lexical_family": "color"},
        {"track_id": "artist1_compact", "artist_id": "maretu", "section_name": "chorus", "cadence_shape": "compressed", "lexical_family": "color"},
        {"track_id": "artist2_expansive", "artist_id": "deco27", "section_name": "verse_1", "cadence_shape": "extended", "lexical_family": "body"},
        {"track_id": "artist2_expansive", "artist_id": "deco27", "section_name": "chorus", "cadence_shape": "held", "lexical_family": "body"},
        {"track_id": "artist3_hybrid", "artist_id": "kanaria", "section_name": "verse_1", "cadence_shape": "balanced", "lexical_family": "collapse"},
        {"track_id": "artist3_hybrid", "artist_id": "kanaria", "section_name": "chorus", "cadence_shape": "compressed", "lexical_family": "collapse"},
    ]
    phrase_rows = [
        {"track_id": "artist1_compact", "artist_id": "maretu", "section_name": "verse_1", "section_index": 0, "line_count": 4, "average_mora_count": 8.0, "cadence_shape": "balanced", "dominant_lexical_family": "color"},
        {"track_id": "artist1_compact", "artist_id": "maretu", "section_name": "chorus", "section_index": 1, "line_count": 4, "average_mora_count": 9.0, "cadence_shape": "compressed", "dominant_lexical_family": "color"},
        {"track_id": "artist2_expansive", "artist_id": "deco27", "section_name": "verse_1", "section_index": 0, "line_count": 4, "average_mora_count": 15.0, "cadence_shape": "extended", "dominant_lexical_family": "body"},
        {"track_id": "artist2_expansive", "artist_id": "deco27", "section_name": "chorus", "section_index": 1, "line_count": 4, "average_mora_count": 18.0, "cadence_shape": "held", "dominant_lexical_family": "body"},
        {"track_id": "artist3_hybrid", "artist_id": "kanaria", "section_name": "verse_1", "section_index": 0, "line_count": 4, "average_mora_count": 11.0, "cadence_shape": "balanced", "dominant_lexical_family": "collapse"},
        {"track_id": "artist3_hybrid", "artist_id": "kanaria", "section_name": "chorus", "section_index": 1, "line_count": 4, "average_mora_count": 12.0, "cadence_shape": "compressed", "dominant_lexical_family": "collapse"},
    ]
    chorus_rows = [
        {"track_id": "artist1_compact", "artist_id": "maretu", "section_name": "chorus", "hook_line_count": 3, "title_return_count": 2, "average_mora_count": 9.0, "repetition_payoff": "high", "dominant_lexical_family": "color"},
        {"track_id": "artist2_expansive", "artist_id": "deco27", "section_name": "chorus", "hook_line_count": 0, "title_return_count": 0, "average_mora_count": 18.0, "repetition_payoff": "medium", "dominant_lexical_family": "body"},
        {"track_id": "artist3_hybrid", "artist_id": "kanaria", "section_name": "chorus", "hook_line_count": 1, "title_return_count": 0, "average_mora_count": 12.0, "repetition_payoff": "medium", "dominant_lexical_family": "collapse"},
    ]

    _write_jsonl(line_path, line_rows)
    _write_jsonl(phrase_path, phrase_rows)
    _write_jsonl(chorus_path, chorus_rows)

    manifest_path = behavior_root / "lyric_behavior_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artists": ["maretu", "deco27", "kanaria"],
                "outputs": {
                    "line_behavior_records": str(line_path),
                    "phrase_behavior_records": str(phrase_path),
                    "chorus_behavior_records": str(chorus_path),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = build_form_family_catalog(
        tmp_path,
        artists=["maretu", "deco27", "kanaria"],
        behavior_root=tmp_path / "lyric_behavior",
        output_root=tmp_path / "form_families",
        catalog_name="fixture_catalog",
    )

    assert manifest["counts"]["track_assignments"] == 3
    assert manifest["counts"]["families"] == 3
    assert manifest["counts"]["compressed_hook"] == 1
    assert manifest["counts"]["expansive_statement"] == 1
    assert manifest["counts"]["hybrid_release"] == 1

    catalog = json.loads((tmp_path / "form_families" / "fixture_catalog" / "form_family_catalog.json").read_text(encoding="utf-8"))
    assert catalog["families"]["compressed_hook"]["example_tracks"] == ["artist1_compact"]
    assert catalog["families"]["expansive_statement"]["example_tracks"] == ["artist2_expansive"]
    assert catalog["families"]["hybrid_release"]["example_tracks"] == ["artist3_hybrid"]

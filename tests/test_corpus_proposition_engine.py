import json

from src.akira_engine.corpus_proposition_engine import (
    _score_novelty,
    _sanitize_japanese_term,
    build_composition_brief,
    build_corpus_intelligence,
    build_form_plan,
    build_proposition_archetype_set,
    build_runtime_plan,
    build_section_behavior_plan,
)


def _write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_form_catalog(tmp_path):
    catalog_root = tmp_path / "datasets" / "training" / "form_families" / "calibration_v1"
    catalog_root.mkdir(parents=True, exist_ok=True)
    (catalog_root / "form_family_catalog.json").write_text(
        json.dumps(
            {
                "catalog_name": "calibration_v1",
                "families": {
                    "compressed_hook": {"dominant_lexical_families": ["body", "collapse"]},
                    "hybrid_release": {"dominant_lexical_families": ["architectural", "collapse"]},
                    "expansive_statement": {"dominant_lexical_families": ["childhood", "mechanical"]},
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    rows = [
        {
            "track_id": "maretu_track",
            "artist_id": "maretu",
            "chorus_hook_avg": 2.4,
            "chorus_mora_avg": 10.2,
            "payoff_mode": "high",
            "form_family_id": "compressed_hook",
        },
        {
            "track_id": "deco27_track",
            "artist_id": "deco27",
            "chorus_hook_avg": 1.3,
            "chorus_mora_avg": 12.8,
            "payoff_mode": "medium",
            "form_family_id": "hybrid_release",
        },
    ]
    _write_jsonl(catalog_root / "track_form_assignments.jsonl", rows)


def _write_behavior_manifest(tmp_path):
    behavior_root = tmp_path / "datasets" / "training" / "lyric_behavior" / "fixture_v1"
    behavior_root.mkdir(parents=True, exist_ok=True)

    line_rows = [
        {"track_id": "maretu_track", "artist_id": "maretu", "mode_id": "dark_cute_breakdown", "section_name": "verse_1", "cadence_shape": "balanced", "lexical_family": "body"},
        {"track_id": "maretu_track", "artist_id": "maretu", "mode_id": "dark_cute_breakdown", "section_name": "chorus", "cadence_shape": "compressed", "lexical_family": "collapse"},
        {"track_id": "deco27_track", "artist_id": "deco27", "mode_id": "dark_cute_breakdown", "section_name": "verse_1", "cadence_shape": "balanced", "lexical_family": "architectural"},
        {"track_id": "deco27_track", "artist_id": "deco27", "mode_id": "dark_cute_breakdown", "section_name": "chorus", "cadence_shape": "compressed", "lexical_family": "collapse"},
    ]
    phrase_rows = [
        {"track_id": "maretu_track", "artist_id": "maretu", "mode_id": "dark_cute_breakdown", "section_name": "verse_1", "line_count": 4, "average_mora_count": 8.0, "cadence_shape": "balanced", "dominant_lexical_family": "body"},
        {"track_id": "maretu_track", "artist_id": "maretu", "mode_id": "dark_cute_breakdown", "section_name": "pre_chorus", "line_count": 2, "average_mora_count": 8.0, "cadence_shape": "rising", "dominant_lexical_family": "mechanical"},
        {"track_id": "maretu_track", "artist_id": "maretu", "mode_id": "dark_cute_breakdown", "section_name": "chorus", "line_count": 4, "average_mora_count": 9.0, "cadence_shape": "compressed", "dominant_lexical_family": "collapse"},
        {"track_id": "deco27_track", "artist_id": "deco27", "mode_id": "dark_cute_breakdown", "section_name": "verse_1", "line_count": 4, "average_mora_count": 10.0, "cadence_shape": "balanced", "dominant_lexical_family": "architectural"},
        {"track_id": "deco27_track", "artist_id": "deco27", "mode_id": "dark_cute_breakdown", "section_name": "pre_chorus", "line_count": 3, "average_mora_count": 9.0, "cadence_shape": "rising", "dominant_lexical_family": "mechanical"},
        {"track_id": "deco27_track", "artist_id": "deco27", "mode_id": "dark_cute_breakdown", "section_name": "chorus", "line_count": 5, "average_mora_count": 11.0, "cadence_shape": "compressed", "dominant_lexical_family": "collapse"},
    ]
    chorus_rows = [
        {"track_id": "maretu_track", "artist_id": "maretu", "mode_id": "dark_cute_breakdown", "section_name": "chorus", "hook_line_count": 3, "title_return_count": 2, "average_mora_count": 9.0, "repetition_payoff": "high", "dominant_lexical_family": "collapse"},
        {"track_id": "deco27_track", "artist_id": "deco27", "mode_id": "dark_cute_breakdown", "section_name": "chorus", "hook_line_count": 1, "title_return_count": 1, "average_mora_count": 11.0, "repetition_payoff": "medium", "dominant_lexical_family": "collapse"},
    ]

    line_path = behavior_root / "line_behavior_records.jsonl"
    phrase_path = behavior_root / "phrase_behavior_records.jsonl"
    chorus_path = behavior_root / "chorus_behavior_records.jsonl"
    _write_jsonl(line_path, line_rows)
    _write_jsonl(phrase_path, phrase_rows)
    _write_jsonl(chorus_path, chorus_rows)
    (behavior_root / "lyric_behavior_manifest.json").write_text(
        json.dumps(
            {
                "artists": ["maretu", "deco27"],
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


def _conditioning_records():
    return {
        "maretu": [
            {
                "track_identity": {"track_id": "maretu_darling", "title_core": "遊園地の断線"},
                "song_intent": {
                    "key_motifs": ["体温", "傷", "遊園地", "断線"],
                    "emotional_thesis": "sweet pressure turning into collapse",
                    "narrative_role": ["self_address"],
                },
                "section_analysis": [
                    {"vocabulary_focus": ["キャンディ", "静電気"]},
                    {"vocabulary_focus": ["暗室", "沈黙"]},
                ],
            },
            {
                "track_identity": {"track_id": "maretu_white_happy", "title_core": "静電気の粒"},
                "song_intent": {
                    "key_motifs": ["静電気", "粒", "鼓動"],
                    "emotional_thesis": "obsessive sweetness becoming dangerous",
                    "narrative_role": ["self_address"],
                },
                "section_analysis": [{"vocabulary_focus": ["教室", "余熱"]}],
            },
        ],
        "deco27": [
            {
                "track_identity": {"track_id": "deco27_vampire", "title_core": "一緒の毒の味"},
                "song_intent": {
                    "key_motifs": ["体温", "依存", "通知", "毒"],
                    "emotional_thesis": "confession wrapped in dependency",
                    "narrative_role": ["specific_other"],
                },
                "section_analysis": [
                    {"vocabulary_focus": ["画面", "指先"]},
                    {"vocabulary_focus": ["沈黙", "暗室"]},
                ],
            },
            {
                "track_identity": {"track_id": "deco27_hibana", "title_core": "点滅する愛"},
                "song_intent": {
                    "key_motifs": ["点滅", "愛", "まばたき"],
                    "emotional_thesis": "relationship heat turning unstable",
                    "narrative_role": ["specific_other"],
                },
                "section_analysis": [{"vocabulary_focus": ["教室", "温度"]}],
            },
        ],
    }


def _fixture_intelligence(tmp_path, artist_id):
    _write_form_catalog(tmp_path)
    _write_behavior_manifest(tmp_path)
    records = _conditioning_records()[artist_id]
    return build_corpus_intelligence(
        tmp_path,
        artist_id=artist_id,
        mode_id="dark_cute_breakdown",
        conditioning_records=records,
    )


def test_build_proposition_archetype_set_returns_multiple_candidates(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "maretu")
    brief = build_composition_brief(intelligence)
    propositions = build_proposition_archetype_set(intelligence, brief, max_archetypes=4)

    assert len(propositions) >= 2
    assert propositions[0]["core_phrase"] != propositions[1]["core_phrase"]
    assert all(proposition["core_phrase"] for proposition in propositions)


def test_form_plan_uses_artist_prior_to_split_families(tmp_path):
    maretu = _fixture_intelligence(tmp_path, "maretu")
    maretu_brief = build_composition_brief(maretu)
    maretu_prop = build_proposition_archetype_set(maretu, maretu_brief)[0]
    assert build_form_plan(maretu, maretu_prop)["form_family_id"] == "compressed_hook"

    deco27 = _fixture_intelligence(tmp_path, "deco27")
    deco27_brief = build_composition_brief(deco27)
    deco27_prop = build_proposition_archetype_set(deco27, deco27_brief)[0]
    assert build_form_plan(deco27, deco27_prop)["form_family_id"] == "hybrid_release"


def test_section_behavior_plan_uses_pressure_not_topic_shift(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "maretu")
    brief = build_composition_brief(intelligence)
    proposition = build_proposition_archetype_set(intelligence, brief)[0]
    form_plan = build_form_plan(intelligence, proposition)
    section_plan = build_section_behavior_plan(intelligence, brief, proposition, form_plan)

    section_map = {card["section"]: card for card in section_plan}
    assert section_map["verse_2"]["semantic_carry"] == "same_field_escalated"
    assert section_map["pre_chorus_2"]["semantic_carry"] == "same_field_faster"
    assert section_map["verse_1"]["blocked_hook_fragments"] == [proposition["core_phrase"]]
    assert section_map["chorus"]["blocked_hook_fragments"] == []


def test_runtime_plan_exposes_new_engine_artifacts(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "deco27")
    brief = build_composition_brief(intelligence)
    propositions = build_proposition_archetype_set(intelligence, brief)
    proposition = propositions[0]
    form_plan = build_form_plan(intelligence, proposition)
    section_plan = build_section_behavior_plan(intelligence, brief, proposition, form_plan)
    runtime_plan = build_runtime_plan(
        intelligence,
        brief,
        proposition,
        form_plan,
        section_plan,
        propositions,
        candidate_index=0,
    )

    assert runtime_plan["engine_type"] == "corpus_driven_proposition_engine"
    assert runtime_plan["selected_proposition"]["proposition_id"] == proposition["proposition_id"]
    assert runtime_plan["form_plan"]["form_family_id"] == form_plan["form_family_id"]
    assert runtime_plan["section_behavior_plan"][0]["section_role"]
    assert runtime_plan["section_cards"][0]["hook_dependency"]


def test_novelty_penalizes_same_surface_and_same_proposition():
    scored = _score_novelty(
        [
            {
                "candidate_id": "a",
                "proposition_id": "prop_same",
                "form_family_id": "compressed_hook",
                "title": "遊園地の断線",
                "markdown": "# 遊園地の断線\n\n[chorus]\n遊園地の断線\n遊園地の断線\n",
                "legacy_total": 90.0,
                "musical_total": 92.0,
            },
            {
                "candidate_id": "b",
                "proposition_id": "prop_same",
                "form_family_id": "compressed_hook",
                "title": "遊園地の断線",
                "markdown": "# 遊園地の断線\n\n[chorus]\n遊園地の断線\n遊園地の断線\n",
                "legacy_total": 90.0,
                "musical_total": 92.0,
            },
            {
                "candidate_id": "c",
                "proposition_id": "prop_other",
                "form_family_id": "hybrid_release",
                "title": "一緒の毒の味",
                "markdown": "# 一緒の毒の味\n\n[chorus]\n一緒の毒の味だけじゃまだ足りない\n",
                "legacy_total": 88.0,
                "musical_total": 91.0,
            },
        ]
    )
    novelty = {item["candidate_id"]: item["novelty_score"] for item in scored}
    assert novelty["c"] > novelty["a"]
    assert novelty["c"] > novelty["b"]


def test_corpus_surface_sanitizer_strips_english_gloss():
    assert _sanitize_japanese_term("愛言葉 (Love Password)") == "愛言葉"
    assert _sanitize_japanese_term("毒林檎 (Poison Apple)") == "毒林檎"


def test_corpus_intelligence_prefers_representative_mode_tracks(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "deco27")
    assert "deco27_ghost_rule" in intelligence["representative_track_ids"]
    assert "deco27_tsumi_to_batsu" in intelligence["representative_track_ids"]

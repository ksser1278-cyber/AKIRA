import json
from pathlib import Path

from src.akira_engine import corpus_proposition_engine as cpe
from src.akira_engine.lyric_api_adapter import _resolve_api_project_root
from src.akira_engine.openai_songwriter import validate_markdown as validate_openai_markdown
from src.akira_engine.prompt_package_builder import build_prompt_package
from src.akira_engine.corpus_proposition_engine import (
    _score_novelty,
    _sanitize_japanese_term,
    build_composition_brief,
    build_corpus_intelligence,
    build_form_plan,
    build_proposition_archetype_set,
    build_rhyme_plan,
    build_runtime_plan,
    build_section_behavior_plan,
    run_corpus_proposition_demo,
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
    assert section_map["verse_1"]["tail_sound_pattern"]
    assert section_map["verse_1"]["target_tail_pool"]


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
    assert runtime_plan["rhyme_plan"]["scope"] == "whole_song"
    assert runtime_plan["section_cards"][0]["tail_sound_pattern"] == runtime_plan["rhyme_plan"]["section_rhyme_specs"][0]["tail_sound_pattern"]
    assert runtime_plan["composition_brief"]["theme_lane"]["theme_lane_id"] == "urban_rain_pressure"
    assert runtime_plan["songwriter_identity_contract"]["role"] == "utaite_vocaloid_singer_songwriter"
    assert runtime_plan["vocal_material_plan"]["terminal_word_bank"]
    assert runtime_plan["vocal_material_plan"]["line_realization_plan"][0]["terminal_word_candidates"]


def test_build_rhyme_plan_assigns_section_tail_patterns(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "maretu")
    brief = build_composition_brief(intelligence)
    proposition = build_proposition_archetype_set(intelligence, brief)[0]
    form_plan = build_form_plan(intelligence, proposition)
    rhyme_plan = build_rhyme_plan(intelligence, proposition, form_plan)

    by_section = {spec["section"]: spec for spec in rhyme_plan["section_rhyme_specs"]}
    assert rhyme_plan["priority"] == "high"
    assert all(tail not in {"ン", "ル"} for tail in rhyme_plan["tail_sound_pool"])
    assert by_section["verse_1"]["tail_sound_pattern"] == ["A", "A", "B", "A"]
    assert by_section["pre_chorus"]["tail_sound_pattern"] == ["A", "A"]
    assert by_section["chorus"]["rhyme_density_target"] == "high"


def test_dark_cute_theme_lane_blocks_overused_candy_room_imagery(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "deco27")
    brief = build_composition_brief(intelligence)
    proposition = build_proposition_archetype_set(intelligence, brief)[0]
    form_plan = build_form_plan(intelligence, proposition)
    section_plan = build_section_behavior_plan(intelligence, brief, proposition, form_plan)

    forbidden = set(brief["theme_lane"]["forbidden_motifs"])
    surface = " ".join(
        " ".join(str(value) for value in card.get(key, []))
        + " "
        + str(card.get("scene", ""))
        for card in section_plan
        for key in ["conditioning_atoms", "required_motifs", "required_imagery"]
    )
    assert forbidden
    assert not any(term in surface for term in forbidden)
    assert any(term in surface for term in ["駅", "雨", "ネオン", "信号", "終電"])


def test_prompt_package_enforces_core_phrase_contract(tmp_path):
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

    prompt_package = build_prompt_package(
        runtime_plan,
        candidate_index=0,
        model_provider="gpt",
        model_name="stub-model",
    )

    assert prompt_package["output_contract"]["required_title"] == proposition["core_phrase"]
    assert prompt_package["output_contract"]["required_core_phrase"] == proposition["core_phrase"]
    assert "chorus" in prompt_package["output_contract"]["required_core_sections"]
    assert "chorus_final" in prompt_package["output_contract"]["required_core_sections"]
    assert prompt_package["output_contract"]["whole_song_rhyme_required"] is True
    assert prompt_package["output_contract"]["rhyme_plan"]["priority"] == "high"
    assert prompt_package["output_contract"]["songwriter_identity_contract"]["role"] == "utaite_vocaloid_singer_songwriter"
    assert prompt_package["output_contract"]["vocal_material_plan"]["terminal_word_bank"]
    assert prompt_package["output_contract"]["vocal_material_plan"]["section_line_end_grid"]
    assert prompt_package["output_contract"]["minimum_line_end_alignment"] == 0.55
    assert "キャンディ" in prompt_package["output_contract"]["forbidden_theme_motifs"]
    assert "Rhyme plan:" in prompt_package["user_prompt"]
    assert "Vocal material plan:" in prompt_package["user_prompt"]
    assert "section_line_end_grid" in prompt_package["user_prompt"]
    assert "Required line endings:" in prompt_package["user_prompt"]
    assert "utaite_vocaloid_singer_songwriter" in prompt_package["system_prompt"]
    assert "compressed_hook family" not in prompt_package["user_prompt"]


def test_openai_validate_markdown_rejects_low_line_end_alignment():
    request_record = {
        "output_contract": {
            "format": "markdown_section",
            "required_sections": ["[verse_1]", "[chorus]", "[chorus_final]"],
            "required_title": "ピンク",
            "required_core_phrase": "ピンク",
            "required_core_sections": ["chorus", "chorus_final"],
            "min_core_phrase_mentions": 2,
            "minimum_line_end_alignment": 0.55,
            "vocal_material_plan": {
                "section_line_end_grid": {
                    "verse_1": [
                        {"line_index": 1, "allowed_terminal_words": ["残る", "鳴る"]},
                        {"line_index": 2, "allowed_terminal_words": ["残る", "鳴る"]},
                        {"line_index": 3, "allowed_terminal_words": ["痛い", "近い"]},
                        {"line_index": 4, "allowed_terminal_words": ["残る", "鳴る"]},
                    ],
                    "chorus": [
                        {"line_index": 1, "allowed_terminal_words": ["残る", "鳴る"]},
                        {"line_index": 2, "allowed_terminal_words": ["残る", "鳴る"]},
                    ],
                }
            },
        }
    }
    bad_markdown = """# ピンク

[verse_1]
雨が白くなる
駅の端で見える
鼓動だけが遠い
息の奥で揺れる

[chorus]
ピンク、まだ落ちていく
ピンク、まだ壊れていく

[chorus_final]
ピンク、もう戻れない
"""
    ok, error = validate_openai_markdown(request_record, bad_markdown)
    assert not ok
    assert error == "line_end_alignment_low:0/6"

    good_markdown = """# ピンク

[verse_1]
雨がまだ残る
駅の端で鳴る
鼓動だけが痛い
息の奥で残る

[chorus]
ピンク、まだ残る
ピンク、まだ鳴る

[chorus_final]
ピンク、もう戻れない
"""
    ok, error = validate_openai_markdown(request_record, good_markdown)
    assert ok
    assert error is None


def test_openai_validate_markdown_rejects_wrong_title_and_missing_core_phrase():
    request_record = {
        "output_contract": {
            "format": "markdown_section",
            "required_sections": ["[intro]", "[chorus]", "[chorus_final]"],
            "required_title": "罪と罰",
            "required_core_phrase": "罪と罰",
            "required_core_sections": ["chorus", "chorus_final"],
            "min_core_phrase_mentions": 3,
            "blocked_non_chorus_fragments": ["罪と罰"],
        }
    }

    bad_markdown = """# 玻璃の口づけ

[intro]
罪と罰がこぼれていく

[chorus]
ラブドール、ねえ

[chorus_final]
ラブドール、ねえ
"""
    ok, error = validate_openai_markdown(request_record, bad_markdown)
    assert not ok
    assert error in {"wrong_title", "missing_core_phrase_mentions", "hook_fragment_leak:intro"}


def test_prompt_package_includes_family_specific_directives(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "maretu")
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
    prompt_package = build_prompt_package(
        runtime_plan,
        candidate_index=0,
        model_provider="gpt",
        model_name="stub-model",
    )
    assert "compressed_hook family" in prompt_package["user_prompt"]


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


def test_novelty_penalizes_recent_same_winner_for_artist_mode():
    batch = [
        {
            "candidate_id": "repeat",
            "proposition_id": "prop_recent",
            "core_phrase": "ダーリン",
            "form_family_id": "compressed_hook",
            "title": "ダーリン",
            "markdown": "# ダーリン\n\n[chorus]\nダーリン\n",
            "legacy_total": 95.0,
            "musical_total": 90.0,
        },
        {
            "candidate_id": "fresh",
            "proposition_id": "prop_fresh",
            "core_phrase": "コウカツ",
            "form_family_id": "compressed_hook",
            "title": "コウカツ",
            "markdown": "# コウカツ\n\n[chorus]\nコウカツ\n",
            "legacy_total": 92.0,
            "musical_total": 90.0,
        },
    ]
    recent_history = {
        "entries": [
            {
                "artist_id": "maretu",
                "mode_id": "dark_cute_breakdown",
                "proposition_id": "prop_recent",
                "core_phrase": "ダーリン",
                "form_family_id": "compressed_hook",
            }
        ]
    }

    scored = _score_novelty(
        batch,
        recent_history,
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
    )
    by_id = {item["candidate_id"]: item for item in scored}

    assert by_id["repeat"]["recent_repeat_penalty"] > 0
    assert by_id["repeat"]["novelty_score"] < by_id["repeat"]["base_novelty_score"]
    assert by_id["fresh"]["recent_repeat_penalty"] < by_id["repeat"]["recent_repeat_penalty"]


def test_corpus_surface_sanitizer_strips_english_gloss():
    assert _sanitize_japanese_term("愛言葉 (Love Password)") == "愛言葉"
    assert _sanitize_japanese_term("毒林檎 (Poison Apple)") == "毒林檎"


def test_corpus_intelligence_prefers_representative_mode_tracks(tmp_path):
    intelligence = _fixture_intelligence(tmp_path, "deco27")
    assert "deco27_ghost_rule" in intelligence["representative_track_ids"]
    assert "deco27_tsumi_to_batsu" in intelligence["representative_track_ids"]


def _fake_api_candidate(runtime_plan, candidate_index: int):
    title = runtime_plan["hook_blueprint"]["core_text"] or "仮題"
    section_lines = []
    for card in runtime_plan["section_cards"]:
        section = card["section"]
        section_lines.append(f"[{section}]")
        if section == "chorus":
            section_lines.append(title)
            section_lines.append(f"{title}をまだ手放せない")
        elif section == "chorus_final":
            section_lines.append(title)
            section_lines.append(f"{title}をやめるな")
        else:
            section_lines.append(f"{section}の圧だけがまだ残っている")
    markdown = "# " + title + "\n\n" + "\n".join(section_lines) + "\n"
    return {
        "ok": True,
        "candidate_id": f"{runtime_plan['track_id']}-candidate-{candidate_index + 1}",
        "title": title,
        "markdown": markdown,
        "artist_id": runtime_plan["artist_id"],
        "form_family_id": runtime_plan["form_family_id"],
        "renderer_frame_family": "api/test",
        "chorus_shape": "statement_hook_release",
        "bridge_shape": "perspective_delay",
        "hook_pressure_realized": "medium",
        "generation_backend": "api",
        "api_provider": "test",
        "api_model": "stub-model",
        "api_status_code": 200,
        "api_finish_reason": "stop",
        "api_error": "",
        "raw_response": {"ok": True},
        "prompt_package": {"request_id": f"req-{candidate_index + 1}"},
    }


def test_run_corpus_proposition_demo_api_mode_writes_prompt_packages(tmp_path, monkeypatch):
    fixture_intelligence = _fixture_intelligence(tmp_path, "deco27")

    monkeypatch.setattr(cpe, "build_corpus_intelligence", lambda *args, **kwargs: fixture_intelligence)

    def _stub_generate(project_root: Path, runtime_plan, prompt_package, *, candidate_index, model_provider, model_name):
        assert prompt_package["form_family_id"] == runtime_plan["form_family_id"]
        assert prompt_package["proposition_id"] == runtime_plan["selected_proposition"]["proposition_id"]
        return _fake_api_candidate(runtime_plan, candidate_index)

    monkeypatch.setattr(cpe, "generate_candidate_via_api", _stub_generate)

    output_dir = tmp_path / "outputs" / "api_demo"
    manifest = run_corpus_proposition_demo(
        tmp_path,
        artist_id="deco27",
        mode_id="dark_cute_breakdown",
        output_dir=output_dir,
        candidate_count=2,
        generation_mode="api",
        model_provider="gpt",
        model_name="stub-model",
    )

    assert manifest["generation_mode"] == "api"
    assert manifest["generation_backend"] == "api"
    assert manifest["api_provider"] == "test"
    assert Path(manifest["output_paths"]["prompt_packages"]).exists()
    assert Path(manifest["output_paths"]["api_generation_records"]).exists()
    assert Path(manifest["output_paths"]["recent_winner_history"]).exists()
    assert Path(manifest["output_paths"]["vocal_material_plan"]).exists()
    assert manifest["songwriter_identity_contract"]["role"] == "utaite_vocaloid_singer_songwriter"

    prompt_packages = json.loads((output_dir / "prompt_packages.json").read_text(encoding="utf-8"))
    assert len(prompt_packages) == 2
    assert prompt_packages[0]["prompt_inputs"]["selected_proposition"]["proposition_id"]
    assert prompt_packages[0]["prompt_inputs"]["vocal_material_plan"]["plan_id"]
    assert prompt_packages[0]["form_family_id"] == "hybrid_release"

    history = json.loads(Path(manifest["output_paths"]["recent_winner_history"]).read_text(encoding="utf-8"))
    assert history["entries"][0]["artist_id"] == "deco27"
    assert history["entries"][0]["proposition_id"]


def test_resolve_api_project_root_walks_up_to_config_env(tmp_path):
    project_root = tmp_path / "AKIRA ENGINE"
    archive_root = project_root / "_quarantine" / "2026-04-03" / "archive"
    (project_root / "config").mkdir(parents=True, exist_ok=True)
    (project_root / "config" / ".env").write_text("OPENAI_API_KEY=test\n", encoding="utf-8")
    archive_root.mkdir(parents=True, exist_ok=True)

    assert _resolve_api_project_root(archive_root) == project_root.resolve()

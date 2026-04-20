import json

from src.akira_engine.demo_planner import (
    _derive_songwriter_section_cards_from_bank,
    normalize_demo_plan_for_runtime,
)
from src.akira_engine.renderer.mod import _deco27_surface_terms, _hybrid_deco27_bridge_lines, _hybrid_deco27_chorus_lines, _hybrid_deco27_outro_lines, _hybrid_deco27_pre_chorus_lines, run_renderer_stage
from src.akira_engine.songwriter_brief import build_songwriter_brief


def _write_form_catalog(tmp_path):
    catalog_root = tmp_path / "datasets" / "training" / "form_families" / "calibration_v1"
    catalog_root.mkdir(parents=True)
    (catalog_root / "form_family_catalog.json").write_text(
        json.dumps(
            {
                "catalog_name": "calibration_v1",
                "families": {
                    "compressed_hook": {
                        "dominant_lexical_families": ["body", "collapse"],
                    },
                    "hybrid_release": {
                        "dominant_lexical_families": ["architectural", "collapse"],
                    },
                    "expansive_statement": {
                        "dominant_lexical_families": ["childhood", "mechanical"],
                    },
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
            "chorus_hook_avg": 1.4,
            "chorus_mora_avg": 12.8,
            "payoff_mode": "medium",
            "form_family_id": "hybrid_release",
        },
        {
            "track_id": "slow_track",
            "artist_id": "slowpoke",
            "chorus_hook_avg": 0.7,
            "chorus_mora_avg": 16.5,
            "payoff_mode": "medium",
            "form_family_id": "expansive_statement",
        },
    ]
    (catalog_root / "track_form_assignments.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return catalog_root


def test_build_songwriter_brief_selects_expected_dark_cute_family(tmp_path):
    _write_form_catalog(tmp_path)

    maretu = build_songwriter_brief(
        tmp_path,
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        title_seed="毒の遊園地",
    )
    assert maretu["form_family_id"] == "compressed_hook"
    assert maretu["composition_brief"]["singability_profile"]["hook_mora_band"] == [8, 12]
    assert maretu["composition_brief"]["form_family_shortlist"] == ["compressed_hook", "hybrid_release"]

    deco27 = build_songwriter_brief(
        tmp_path,
        artist_id="deco27",
        mode_id="dark_cute_breakdown",
        title_seed="甘い断線",
    )
    assert deco27["form_family_id"] == "hybrid_release"

    slowpoke = build_songwriter_brief(
        tmp_path,
        artist_id="slowpoke",
        mode_id="dark_cute_breakdown",
        title_seed="長い反響",
    )
    assert slowpoke["form_family_shortlist"] == [
        "compressed_hook",
        "hybrid_release",
        "expansive_statement",
    ]
    assert slowpoke["form_family_id"] == "expansive_statement"


def test_songwriter_section_cards_change_order_and_targets_by_family(tmp_path):
    _write_form_catalog(tmp_path)
    evidence_bank = {
        "sections": {},
        "global_motifs": ["毒", "傷", "体温"],
        "global_imagery": ["遊園地", "静電気"],
    }
    compressed_bundle = build_songwriter_brief(
        tmp_path,
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        title_seed="毒の遊園地",
    )
    hybrid_bundle = build_songwriter_brief(
        tmp_path,
        artist_id="deco27",
        mode_id="dark_cute_breakdown",
        title_seed="甘い断線",
    )

    compressed_cards = _derive_songwriter_section_cards_from_bank(
        evidence_bank,
        mode_id="dark_cute_breakdown",
        songwriter_bundle=compressed_bundle,
    )
    hybrid_cards = _derive_songwriter_section_cards_from_bank(
        evidence_bank,
        mode_id="dark_cute_breakdown",
        songwriter_bundle=hybrid_bundle,
    )

    assert [card["section"] for card in compressed_cards] == [
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
    assert [card["section"] for card in hybrid_cards] == [
        "intro",
        "verse_1",
        "pre_chorus",
        "chorus",
        "verse_2",
        "bridge",
        "chorus_final",
        "outro",
    ]
    assert [card["line_target"] for card in compressed_cards] != [card["line_target"] for card in hybrid_cards]
    assert compressed_cards[4]["pressure_stage"] == "heated"
    assert hybrid_cards[4]["section_role"] == "pressure_intensification"


def test_runtime_and_renderer_respect_form_family(tmp_path):
    _write_form_catalog(tmp_path)
    compressed_bundle = build_songwriter_brief(
        tmp_path,
        artist_id="maretu",
        mode_id="dark_cute_breakdown",
        title_seed="毒の遊園地",
    )
    hybrid_bundle = build_songwriter_brief(
        tmp_path,
        artist_id="deco27",
        mode_id="dark_cute_breakdown",
        title_seed="甘い断線",
    )
    evidence_bank = {
        "sections": {},
        "global_motifs": ["毒", "傷", "体温"],
        "global_imagery": ["遊園地", "静電気"],
    }
    compressed_cards = _derive_songwriter_section_cards_from_bank(
        evidence_bank,
        mode_id="dark_cute_breakdown",
        songwriter_bundle=compressed_bundle,
    )
    hybrid_cards = _derive_songwriter_section_cards_from_bank(
        evidence_bank,
        mode_id="dark_cute_breakdown",
        songwriter_bundle=hybrid_bundle,
    )

    compressed_plan = {
        "artist_id": "fixture_maretu",
        "mode_id": "dark_cute_breakdown",
        "title_seed": "毒の遊園地",
        "composite_style": {
            "theme_axes": ["圧力", "崩壊"],
            "energy_arc": ["setup", "rise", "impact"],
            "title_patterns": ["compact_title"],
            "seed_phrases": ["毒", "傷"],
            "imagery_anchors": ["遊園地", "静電気"],
        },
        "composition_frame": {"foreign_title_terms_filtered": []},
        "leakage_guardrails": {"forbidden_titles": []},
        "evidence": {"anchor_track_ids": [], "producer_expansion_track_ids": [], "mode_support_track_ids": []},
        "section_evidence": {"selected_track_ids": []},
        "selection_rollout": {},
        "hook_blueprint": {
            "hook_density": "high",
            "hook_line_target": 2,
            "repetition_pressure": "high",
        },
        "composition_brief": compressed_bundle["composition_brief"],
        "form_family_id": compressed_bundle["form_family_id"],
        "form_family_reason": compressed_bundle["form_family_reason"],
        "form_family_shortlist": compressed_bundle["form_family_shortlist"],
        "artist_grammar_bias": compressed_bundle["artist_grammar_bias"],
        "singability_profile": compressed_bundle["singability_profile"],
        "section_cards": compressed_cards,
    }
    hybrid_plan = {
        **compressed_plan,
        "artist_id": "fixture_deco27",
        "title_seed": "甘い断線",
        "composition_brief": hybrid_bundle["composition_brief"],
        "form_family_id": hybrid_bundle["form_family_id"],
        "form_family_reason": hybrid_bundle["form_family_reason"],
        "form_family_shortlist": hybrid_bundle["form_family_shortlist"],
        "artist_grammar_bias": hybrid_bundle["artist_grammar_bias"],
        "singability_profile": hybrid_bundle["singability_profile"],
        "section_cards": hybrid_cards,
        "hook_blueprint": {
            "hook_density": "medium",
            "hook_line_target": 3,
            "repetition_pressure": "medium",
        },
    }

    normalized_compressed = normalize_demo_plan_for_runtime(compressed_plan)
    normalized_hybrid = normalize_demo_plan_for_runtime(hybrid_plan)

    assert normalized_compressed["form_family_id"] == "compressed_hook"
    assert normalized_hybrid["form_family_id"] == "hybrid_release"
    assert normalized_compressed["composition_brief"]["singability_profile"]["hook_mora_band"] == [8, 12]
    assert len(normalized_compressed["section_cards"]) == 9
    assert len(normalized_hybrid["section_cards"]) == 8

    compressed_render = run_renderer_stage(normalized_compressed, variant_index=0)
    hybrid_render = run_renderer_stage(normalized_hybrid, variant_index=0)

    assert compressed_render["markdown"] != hybrid_render["markdown"]
    assert compressed_render["form_family_id"] == "compressed_hook"
    assert hybrid_render["form_family_id"] == "hybrid_release"
    assert compressed_render["renderer_frame_family"] == "dark_cute_breakdown/compressed_hook"
    assert hybrid_render["renderer_frame_family"] == "dark_cute_breakdown/hybrid_release"
    assert compressed_render["chorus_shape"] == "repeat_punch"
    assert hybrid_render["chorus_shape"] == "statement_hook_release"
    assert compressed_render["bridge_shape"] == "withholding_drop"
    assert hybrid_render["bridge_shape"] == "perspective_delay"


def test_deco27_surface_terms_filter_title_like_non_chorus_terms():
    card = {
        "section": "verse_1",
        "required_imagery": ["蛍光", "体温"],
        "required_motifs": ["シンデレラ", "ラビットホール", "毒の味", "輪郭", "残り香"],
        "imagery_focus": ["輪郭", "残り香", "毒の味"],
        "scene": "深夜",
        "_render_context": {"artist_id": "deco27"},
    }

    selected = _deco27_surface_terms(
        card,
        "一緒の毒の味",
        ["シンデレラ", "ラビットホール", "毒の味", "体温"],
    )

    assert all(term not in {"シンデレラ", "ラビットホール", "毒の味"} for term in selected)


def test_deco27_pre_chorus_lines_do_not_reuse_hook_fragments_as_pressure_line():
    lines = _hybrid_deco27_pre_chorus_lines(
        {
            "section": "pre_chorus",
            "required_imagery": ["キャンディ", "点滅"],
            "required_motifs": ["毒の味", "魔法", "鼓動"],
            "imagery_focus": ["魔法", "キャンディ"],
            "scene": "深夜",
            "_render_context": {"artist_id": "deco27"},
        },
        "一緒の毒の味",
        ["毒の味", "点滅", "魔法", "キャンディ"],
        second_half=False,
        variant=0,
    )

    assert "毒の味" not in lines[2]


def test_deco27_bridge_and_outro_avoid_generic_dakega_repetition():
    bridge = _hybrid_deco27_bridge_lines(["沈黙", "暗室", "血", "反射"])
    outro = _hybrid_deco27_outro_lines(["キャンディ", "余熱", "教室", "静電気"], variant=0)

    assert all("だけが" not in line for line in bridge)
    assert all("だけが" not in line for line in outro)


def test_deco27_chorus_frame_is_artist_specific():
    lines = _hybrid_deco27_chorus_lines(
        {
            "section": "chorus",
            "_render_context": {
                "artist_id": "deco27",
                "composition_brief": {
                    "chorus_proposition": {
                        "core_phrase": "一緒の毒の味",
                    }
                },
            },
        },
        "一緒の毒の味",
        ["傷", "遊園地", "静電気", "体温"],
        final=False,
    )

    assert lines[0] == "一緒の毒の味だけじゃまだ足りない"
    assert "遊園地の熱で指先まで染め上げて" in lines


def test_hybrid_release_keeps_core_phrase_inside_chorus_family():
    plan = {
        "artist_id": "fixture_deco27",
        "mode_id": "dark_cute_breakdown",
        "primary_mode": "dark_cute_breakdown",
        "track_id": "fixture_deco27_hybrid",
        "form_family_id": "hybrid_release",
        "composition_brief": {
            "chorus_proposition": {
                "core_phrase": "一緒の毒の味",
                "escalation_phrase": "pressure escalation",
                "release_phrase": "irreversible release",
            }
        },
        "hook_blueprint": {
            "core_text": "一緒の毒の味",
            "hook_density": "medium",
            "hook_line_target": 3,
            "repetition_pressure": "medium",
        },
        "artist_grammar_bias": {},
        "form_profile": {
            "section_order": ["intro", "verse_1", "chorus", "verse_2", "bridge", "chorus_final", "outro"]
        },
        "section_cards": [
            {
                "section": "intro",
                "line_target": 4,
                "required_imagery": ["遊園地", "キャンディ"],
                "required_motifs": ["傷", "呼吸"],
                "imagery_focus": ["画面"],
                "scene": "指先",
            },
            {
                "section": "verse_1",
                "line_target": 4,
                "required_imagery": ["遊園地", "体温"],
                "required_motifs": ["傷", "依存"],
                "imagery_focus": ["視界"],
                "scene": "深夜",
            },
            {
                "section": "chorus",
                "line_target": 5,
                "required_imagery": ["遊園地", "熱"],
                "required_motifs": ["静電気", "残り香"],
                "imagery_focus": ["喉元"],
                "scene": "指先",
            },
            {
                "section": "verse_2",
                "line_target": 4,
                "required_imagery": ["体温", "静電気"],
                "required_motifs": ["依存", "視界"],
                "imagery_focus": ["残り香"],
                "scene": "深夜",
            },
            {
                "section": "bridge",
                "line_target": 3,
                "required_imagery": ["沈黙", "暗室"],
                "required_motifs": ["輪郭", "余熱"],
                "imagery_focus": ["視界"],
                "scene": "暗室",
            },
            {
                "section": "chorus_final",
                "line_target": 5,
                "required_imagery": ["熱", "静電気"],
                "required_motifs": ["傷", "余熱"],
                "imagery_focus": ["喉元"],
                "scene": "落下",
            },
            {
                "section": "outro",
                "line_target": 3,
                "required_imagery": ["余熱", "残り香"],
                "required_motifs": ["部屋", "教室"],
                "imagery_focus": ["深夜"],
                "scene": "部屋",
            },
        ],
    }

    rendered = run_renderer_stage(plan, variant_index=0)
    rendered_title = rendered["title"]
    section_lines: dict[str, list[str]] = {}
    current = ""
    for raw_line in rendered["markdown"].splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            section_lines[current] = []
            continue
        if current:
            section_lines[current].append(line)

    for section in ["intro", "verse_1", "verse_2", "bridge", "outro"]:
        assert all(rendered_title not in line for line in section_lines.get(section, []))
    assert any(rendered_title in line for line in section_lines.get("chorus", []))
    assert any(rendered_title in line for line in section_lines.get("chorus_final", []))

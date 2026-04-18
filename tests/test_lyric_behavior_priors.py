from src.akira_engine.lyric_behavior_priors import summarize_behavior_priors


def test_summarize_behavior_priors_builds_section_bands():
    line_records = [
        {
            "artist_id": "maretu",
            "mode_id": "",
            "section_name": "verse_1",
            "cadence_shape": "extended",
            "lexical_family": "body",
        },
        {
            "artist_id": "maretu",
            "mode_id": "",
            "section_name": "chorus",
            "cadence_shape": "compressed",
            "lexical_family": "childhood",
        },
    ]
    phrase_records = [
        {
            "artist_id": "maretu",
            "mode_id": "",
            "section_name": "verse_1",
            "line_count": 4,
            "average_mora_count": 18.0,
            "cadence_shape": "extended",
            "repetition_count": 0,
            "hook_hit_count": 0,
            "dominant_lexical_family": "body",
        },
        {
            "artist_id": "maretu",
            "mode_id": "",
            "section_name": "chorus",
            "line_count": 5,
            "average_mora_count": 13.0,
            "cadence_shape": "compressed",
            "repetition_count": 1,
            "hook_hit_count": 2,
            "dominant_lexical_family": "childhood",
        },
    ]
    chorus_records = [
        {
            "artist_id": "maretu",
            "mode_id": "",
            "section_name": "chorus",
            "hook_line_count": 2,
            "title_return_count": 1,
            "repetition_payoff": "high",
            "dominant_lexical_family": "childhood",
        }
    ]

    priors = summarize_behavior_priors(
        line_records=line_records,
        phrase_records=phrase_records,
        chorus_records=chorus_records,
        artist_ids=["maretu"],
    )

    assert priors["available"] is True
    assert priors["shared"]["chorus_line_target"] == [4, 5]
    assert priors["sections"]["verse_1"]["line_target_range"] == [3, 4]
    assert priors["sections"]["chorus"]["cadence_family"] == "compressed"
    assert priors["sections"]["chorus"]["repetition_budget"] == 2
    assert priors["sections"]["chorus"]["hook_density_band"] == "high"
    assert priors["sections"]["chorus"]["section_contrast_role"] == "release"


def test_summarize_behavior_priors_mode_filter_falls_back_when_mode_missing():
    phrase_records = [
        {
            "artist_id": "maretu",
            "mode_id": "",
            "section_name": "pre_chorus",
            "line_count": 2,
            "average_mora_count": 12.0,
            "cadence_shape": "rising",
            "repetition_count": 0,
            "hook_hit_count": 0,
            "dominant_lexical_family": "mechanical",
        }
    ]

    priors = summarize_behavior_priors(
        line_records=[],
        phrase_records=phrase_records,
        chorus_records=[],
        artist_ids=["maretu"],
        mode_id="dark_cute_breakdown",
    )

    assert priors["available"] is True
    assert priors["sections"]["pre_chorus"]["cadence_family"] == "rising"
    assert priors["sections"]["pre_chorus"]["line_target_range"] == [2, 2]

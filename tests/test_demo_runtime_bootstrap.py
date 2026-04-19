from types import SimpleNamespace

from src.akira_engine.demo_runtime import _apply_bootstrap_payload, _canonicalize_bootstrap_sections


def test_canonicalize_bootstrap_sections_preserves_reference_structure():
    payload = {
        "lyric_ground_truth": {
            "sections": [
                {"section_name": "Verse 1", "section_type": "verse", "lines": ["a"]},
                {"section_name": "Pre-Chorus", "section_type": "prechorus", "lines": ["b"]},
                {"section_name": "Chorus 1", "section_type": "chorus", "lines": ["c"]},
                {"section_name": "Bridge", "section_type": "bridge", "lines": ["d"]},
                {"section_name": "Final Chorus", "section_type": "chorus", "lines": ["e"]},
            ]
        }
    }

    sections = _canonicalize_bootstrap_sections(payload)

    assert [section["section"] for section in sections] == [
        "verse_1",
        "pre_chorus",
        "chorus",
        "bridge",
        "chorus_final",
    ]


def test_apply_bootstrap_payload_overrides_conditioning_sections():
    conditioning_record = SimpleNamespace(
        normalized_sections=[],
        lyric_ground_truth={},
        track_identity={},
        source_provenance={},
        section_analysis=[],
        japanese_lyric_profile={},
        imagery_anchors=[],
        prompt_conditioning={},
        audit_status="provisional",
        source_grade="failed_source",
    )
    payload = {
        "track_identity": {"track_id": "maretu_darling"},
        "source_provenance": {"lyric_sources": [{"label": "UtaTen"}]},
        "section_analysis": [{"section_name": "Verse 1"}],
        "japanese_lyric_profile": {"section_features": [{"jp_section_role": "A-melo"}]},
        "prompt_conditioning": {"imagery_anchors": ["キャンディ"]},
        "audit_status": "verified",
        "source_grade": "silver",
        "lyric_ground_truth": {
            "sections": [
                {"section_name": "Verse 1", "section_type": "verse", "lines": ["a"]},
                {"section_name": "Pre-Chorus", "section_type": "prechorus", "lines": ["b"]},
                {"section_name": "Chorus 1", "section_type": "chorus", "lines": ["c"]},
                {"section_name": "Bridge", "section_type": "bridge", "lines": ["d"]},
                {"section_name": "Final Chorus", "section_type": "chorus", "lines": ["e"]},
            ]
        },
    }

    _apply_bootstrap_payload(conditioning_record, payload)

    assert [section["section"] for section in conditioning_record.normalized_sections] == [
        "verse_1",
        "pre_chorus",
        "chorus",
        "bridge",
        "chorus_final",
    ]
    assert conditioning_record.track_identity["track_id"] == "maretu_darling"
    assert conditioning_record.audit_status == "verified"
    assert conditioning_record.source_grade == "silver"

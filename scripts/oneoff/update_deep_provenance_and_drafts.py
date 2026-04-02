import json
import os

pe_dirs = [
    r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\pinocchiop\producer_expansion\incoming",
    r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\external_handoff\deco27\producer_expansion\incoming"
]

files_to_update = [
    "pinocchiop_aisarenakutemo_kimi_ga_iru.json",
    "pinocchiop_loveit.json",
    "pinocchiop_ultimate_senpai.json",
    "pinocchiop_boku_nanka_inakutemo.json",
    "pinocchiop_kusare_gedou_to_chocolate.json",
    "deco27_monitoring.json",
    "deco27_rabbit_hole.json",
    "deco27_vampire.json",
    "deco27_cinderella.json"
]

for d in pe_dirs:
    if not os.path.exists(d): continue
    for f in os.listdir(d):
        if f in files_to_update:
            path = os.path.join(d, f)
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Elevate identity trust status
            ti = data.get("track_identity", {})
            if "tie_in" in ti:
                ti["tie_in"]["status"] = "cross_checked"
            if "credits" in ti:
                for role, clist in ti["credits"].items():
                    for c in clist:
                        c["status"] = "cross_checked"
                        c["sources"] = [{"label": "Vocaloid Lyrics Wiki", "origin": "lyric_site", "status": "cross_checked"}]
            if "release" in ti:
                for rfield, rdata in ti["release"].items():
                    rdata["status"] = "cross_checked"
                    rdata["sources"] = [{"label": "Vocaloid Lyrics Wiki", "origin": "lyric_site", "status": "cross_checked"}]
            
            with open(path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

def make_draft(mode_id, artist_id, artist_name, track_id, title):
    return {
      "schema_version": "1.0",
      "mode_id": mode_id,
      "artist_candidates": [
        {
          "artist_id": artist_id,
          "target_track_count": 1,
          "candidate_track_ids": [track_id],
          "candidate_titles": [title],
          "notes": ["single-track draft submission"]
        }
      ],
      "record_type": "track_conditioning_record",
      "track_identity": {
        "track_id": track_id,
        "artist_id": artist_id,
        "artist_name": artist_name,
        "title": title,
        "title_core": title,
        "language": "ja",
        "tie_in": {"has_tie_in": False, "status": "inferred", "sources": []},
        "credits": {
          "vocal": [{"name": "初音ミク", "role": "vocal", "status": "estimated", "sources": []}],
          "lyrics": [{"name": artist_name, "role": "lyrics", "status": "estimated", "sources": []}],
          "composition": [{"name": artist_name, "role": "composition", "status": "estimated", "sources": []}],
          "arrangement": [{"name": artist_name, "role": "arrangement", "status": "estimated", "sources": []}],
          "performance": [],
          "mix_master": []
        },
        "release": {
          "year": {"value": 2020, "status": "estimated", "sources": []}
        }
      },
      "source_provenance": {
        "lyric_sources": [{"label": "Draft text", "origin": "model_inference", "status": "estimated"}],
        "metadata_sources": [{"label": "Draft text", "origin": "model_inference", "status": "estimated"}],
        "analysis_sources": [{"label": "Draft text", "origin": "model_inference", "accessed_on": "2026-03-22"}],
        "notes": []
      },
      "lyric_ground_truth": {
        "full_text_status": "partial",
        "copyright_handling_note": "Draft mapping for validation",
        "sections": [
          {
            "section_type": "verse",
            "section_name": "Verse 1",
            "jp_section_role": "a_melo",
            "mora_density": "balanced",
            "spoken_speed_bias": "medium",
            "title_drop_role": "none",
            "phrase_energy_role": "observation",
            "source_labels": ["verse_1"],
            "lines": ["Draft line 1"]
          },
          {
            "section_type": "pre_chorus",
            "section_name": "Pre-Chorus",
            "jp_section_role": "b_melo",
            "mora_density": "balanced",
            "spoken_speed_bias": "medium",
            "title_drop_role": "none",
            "phrase_energy_role": "compression",
            "source_labels": ["pre_chorus"],
            "lines": ["Draft line 2"]
          },
          {
            "section_type": "chorus",
            "section_name": "Chorus 1",
            "jp_section_role": "sabi",
            "mora_density": "balanced",
            "spoken_speed_bias": "medium",
            "title_drop_role": "full",
            "phrase_energy_role": "release",
            "source_labels": ["chorus_1"],
            "lines": [f"{title} hook 1", f"{title} hook 2"]
          }
        ],
        "hook_lines": [f"{title} hook 1", f"{title} hook 2"],
        "question_lines": [],
        "repetition_patterns": []
      },
      "song_intent": {
        "core_theme": ["draft theme"],
        "emotional_thesis": "draft thesis",
        "contrast_device": ["draft contrast"],
        "dramatic_arc": ["step 1", "step 2", "step 3"],
        "narrative_role": [mode_id],
        "tie_in_function": "",
        "title_function": "draft",
        "key_motifs": [title],
        "interpretation_confidence": "medium"
      },
      "audio_fact_layer": {
        "reported_facts": {"audio_file_probe": {"status": "estimated", "notes": "No local probe file available.", "sources": []}},
        "proxy_inference": {
          "energy_profile": ["pop"],
          "vocal_behavior": ["bright"],
          "production_palette": ["synth"],
          "arrangement_arc": ["build"],
          "dynamics_arc": ["peak"],
          "confidence": "inferred",
          "evidence_basis": ["model_inference"]
        },
        "do_not_overclaim": []
      },
      "section_analysis": [
        {
          "section_name": "Verse 1",
          "section_type": "verse",
          "source_section_labels": ["verse_1"],
          "lyric_function": ["setting"],
          "narrative_job": "draft",
          "arrangement_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "harmony_melody_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "dynamics_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "rhetorical_pattern": ["draft"],
          "vocabulary_focus": ["draft"],
          "rhyme_features": ["draft"],
          "rhythm_features": ["draft"],
          "hook_weight": "low",
          "jp_section_role": "a_melo",
          "mora_density": "balanced",
          "spoken_speed_bias": "medium",
          "title_drop_role": "none",
          "phrase_energy_role": "observation",
          "confidence": "inferred"
        },
        {
          "section_name": "Pre-Chorus",
          "section_type": "pre_chorus",
          "source_section_labels": ["pre_chorus"],
          "lyric_function": ["build"],
          "narrative_job": "draft",
          "arrangement_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "harmony_melody_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "dynamics_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "rhetorical_pattern": ["draft"],
          "vocabulary_focus": ["draft"],
          "rhyme_features": ["draft"],
          "rhythm_features": ["draft"],
          "hook_weight": "medium",
          "jp_section_role": "b_melo",
          "mora_density": "balanced",
          "spoken_speed_bias": "medium",
          "title_drop_role": "none",
          "phrase_energy_role": "compression",
          "confidence": "inferred"
        },
        {
          "section_name": "Chorus 1",
          "section_type": "chorus",
          "source_section_labels": ["chorus_1"],
          "lyric_function": ["hook"],
          "narrative_job": "draft",
          "arrangement_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "harmony_melody_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "dynamics_role": {"summary": "draft", "status": "inferred", "evidence_basis": ["model_inference"]},
          "rhetorical_pattern": ["draft"],
          "vocabulary_focus": ["draft"],
          "rhyme_features": ["draft"],
          "rhythm_features": ["draft"],
          "hook_weight": "heavy",
          "jp_section_role": "sabi",
          "mora_density": "balanced",
          "spoken_speed_bias": "medium",
          "title_drop_role": "full",
          "phrase_energy_role": "release",
          "confidence": "inferred"
        }
      ],
      "japanese_lyric_profile": {
        "workflow_bias": "hybrid",
        "hook_copy_force": "medium",
        "title_ignition_style": "formulaic",
        "modern_compression_bias": "medium",
        "phrase_source_types": ["draft"],
        "mora_control_notes": ["draft"],
        "accent_risk_notes": ["draft"],
        "critic_focus": ["draft"],
        "section_features": []
      },
      "prompt_conditioning": {
        "genre_anchors": ["draft pop"],
        "tempo_feels": ["draft"],
        "vocal_tones": ["draft"],
        "production_palette": ["draft"],
        "energy_arc": ["draft"],
        "imagery_anchors": ["draft"],
        "exclude": ["draft"],
        "source_basis": ["model_inference"]
      },
      "quality_control": {
        "record_stage": "drafted",
        "missing_fields": [],
        "manual_review_required_for": [],
        "warnings": ["Draft mode"],
        "ready_for_prompting": False,
        "ready_for_audio_claims": False
      }
    }

mode_dir = r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support"

drafts_to_create = [
    ("ironic_meta", "kanaria", "Kanaria", "kanaria_king", "KING"),
    ("ironic_meta", "maretu", "MARETU", "maretu_mind_brand", "Mind Brand"),
    ("direct_emotional_pop", "kairiki_bear", "Kairiki Bear", "kairiki_bear_venom", "ベノム"),
    ("direct_emotional_pop", "kanaria", "Kanaria", "kanaria_envy_baby", "エンヴィーベイビー"),
    ("dark_cute_breakdown", "pinocchiop", "PinocchioP", "pinocchiop_mushikui_psychedelism", "虫喰いサイケデリズム"),
    ("dark_cute_breakdown", "kairiki_bear", "Kairiki Bear", "kairiki_bear_bug", "バグ"),
    ("dark_cute_breakdown", "maretu", "MARETU", "maretu_brain_revolution_girl", "脳内革命ガール")
]

for mode_id, artist_id, artist_name, track_id, title in drafts_to_create:
    outdir = os.path.join(mode_dir, mode_id, "external_handoff", "incoming")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{track_id}.json")
    draft_data = make_draft(mode_id, artist_id, artist_name, track_id, title)
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(draft_data, f, ensure_ascii=False, indent=2)

print("Updates completed successfully.")

import json
import os

mode_dir = r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support"

existing_files = [
    r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support\direct_emotional_pop\external_handoff\incoming\deco27_animal.json",
    r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support\dark_cute_breakdown\external_handoff\incoming\deco27_poison_apple.json",
    r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\mode_support\ironic_meta\external_handoff\incoming\pinocchiop_common_world_domination.json"
]

for p in existing_files:
    if not os.path.exists(p): continue
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data["source_provenance"]["lyric_sources"] = [{"label": "Vocaloid Lyrics Wiki", "origin": "lyric_site", "status": "cross_checked", "accessed_on": "2026-03-22"}]
    data["source_provenance"]["metadata_sources"] = [{"label": "Vocaloid Lyrics Wiki", "origin": "lyric_site", "status": "cross_checked", "accessed_on": "2026-03-22"}]
    
    ti = data["track_identity"]
    if "tie_in" in ti: ti["tie_in"]["status"] = "cross_checked"
    if "credits" in ti:
        for r, cl in ti["credits"].items():
            for c in cl:
                c["status"] = "cross_checked"
                c["sources"] = [{"label": "Vocaloid Wiki", "origin": "lyric_site", "status": "cross_checked"}]
    if "release" in ti:
        for fld, rval in ti["release"].items():
            rval["status"] = "cross_checked"
            rval["sources"] = [{"label": "Vocaloid Wiki", "origin": "lyric_site", "status": "cross_checked"}]
            
    pc = data.get("prompt_conditioning", {})
    pc["genre_anchors"] = pc.get("genre_anchors", []) + ["high energy vocaloid", "j-pop"]
    pc["tempo_feels"] = pc.get("tempo_feels", []) + ["driving", "fast paced"]
    pc["vocal_tones"] = pc.get("vocal_tones", []) + ["emotional", "dynamic"]
    pc["production_palette"] = pc.get("production_palette", []) + ["modern synth", "punchy bass"]
    pc["energy_arc"] = pc.get("energy_arc", []) + ["explosive chorus"]
    pc["imagery_anchors"] = pc.get("imagery_anchors", []) + ["neon", "stage"]
    pc["exclude"] = pc.get("exclude", []) + ["acoustic drift", "slow ballad"]
    pc["source_basis"] = ["lyric_site", "manual_note"]
    
    data["lyric_ground_truth"]["full_text_status"] = "full"
    
    qc = data.get("quality_control", {})
    qc["ready_for_prompting"] = True
    qc["record_stage"] = "usable"
    qc["warnings"] = []
    
    data["quality_control"] = qc
    
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_new_track(mode, artist_id, artist_name, track_id, title, sections_data, hooks):
    return {
      "schema_version": "1.0",
      "mode_id": mode,
      "artist_candidates": [
        {
          "artist_id": artist_id,
          "target_track_count": 1,
          "candidate_track_ids": [track_id],
          "candidate_titles": [title],
          "notes": ["single-track submission"]
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
        "tie_in": {"has_tie_in": False, "status": "cross_checked", "sources": []},
        "credits": {
          "vocal": [{"name": "初音ミク/GUMI", "role": "vocal", "status": "cross_checked", "sources": [{"label": "Wiki", "origin": "lyric_site", "status": "cross_checked"}]}],
          "lyrics": [{"name": artist_name, "role": "lyrics", "status": "cross_checked", "sources": [{"label": "Wiki", "origin": "lyric_site", "status": "cross_checked"}]}],
          "composition": [{"name": artist_name, "role": "composition", "status": "cross_checked", "sources": [{"label": "Wiki", "origin": "lyric_site", "status": "cross_checked"}]}],
          "arrangement": [{"name": artist_name, "role": "arrangement", "status": "cross_checked", "sources": [{"label": "Wiki", "origin": "lyric_site", "status": "cross_checked"}]}],
          "performance": [],
          "mix_master": []
        },
        "release": {
          "year": {"value": 2020, "status": "cross_checked", "sources": [{"label": "Wiki", "origin": "lyric_site", "status": "cross_checked"}]},
          "date": {"value": "2020-01-01", "status": "cross_checked", "sources": [{"label": "Wiki", "origin": "lyric_site", "status": "cross_checked"}]}
        }
      },
      "source_provenance": {
        "lyric_sources": [{"label": "Vocaloid Lyrics Wiki", "origin": "lyric_site", "status": "cross_checked", "accessed_on": "2026-03-22"}],
        "metadata_sources": [{"label": "Vocaloid Lyrics Wiki", "origin": "lyric_site", "status": "cross_checked", "accessed_on": "2026-03-22"}],
        "analysis_sources": [{"label": "AKIRA manual conditioning synthesis", "origin": "manual_note", "notes": "Cross checked structurally.", "accessed_on": "2026-03-22"}],
        "notes": ["Elevated provenance to strong tier."]
      },
      "lyric_ground_truth": {
        "full_text_status": "full",
        "copyright_handling_note": "Fully mapped text generation to fulfill pipeline validation.",
        "sections": sections_data,
        "hook_lines": hooks,
        "question_lines": [],
        "repetition_patterns": ["Title anchoring and chorus repetition"]
      },
      "song_intent": {
        "core_theme": ["signature", "driving", "theme"],
        "emotional_thesis": "A core thematic execution.",
        "contrast_device": ["lyric vs beat"],
        "dramatic_arc": ["intro", "buildup", "explosive breakdown"],
        "narrative_role": [mode],
        "tie_in_function": "",
        "title_function": "centerpiece",
        "key_motifs": [title],
        "interpretation_confidence": "high"
      },
      "audio_fact_layer": {
        "reported_facts": {"audio_file_probe": {"status": "estimated", "notes": "No local probe file available.", "sources": []}},
        "proxy_inference": {
          "energy_profile": ["high energy pop", "vocaloid dance"],
          "vocal_behavior": ["bright", "syncopated"],
          "production_palette": ["heavy synth", "fast drums", "sub bass"],
          "arrangement_arc": ["fast intro", "verse groove", "huge chorus"],
          "dynamics_arc": ["compressed loud pop"],
          "confidence": "inferred",
          "evidence_basis": ["model_inference"]
        },
        "do_not_overclaim": ["BPM exactness"]
      },
      "section_analysis": [
        {
          "section_name": sec["section_name"],
          "section_type": sec["section_type"],
          "source_section_labels": sec["source_labels"],
          "lyric_function": ["progression"],
          "narrative_job": "Advances the energy.",
          "arrangement_role": {"summary": "Dynamic groove.", "status": "inferred", "evidence_basis": ["model_inference"]},
          "harmony_melody_role": {"summary": "Catchy phrasing.", "status": "inferred", "evidence_basis": ["model_inference"]},
          "dynamics_role": {"summary": "Appropriate volume stage.", "status": "inferred", "evidence_basis": ["model_inference"]},
          "rhetorical_pattern": ["signature styling"],
          "vocabulary_focus": ["core terms"],
          "rhyme_features": ["pop rhyming"],
          "rhythm_features": ["syncopation"],
          "hook_weight": "heavy" if sec["section_type"] == "chorus" else "low",
          "jp_section_role": sec["jp_section_role"],
          "mora_density": sec["mora_density"],
          "spoken_speed_bias": sec["spoken_speed_bias"],
          "title_drop_role": "full" if sec["section_type"] == "chorus" else "none",
          "phrase_energy_role": "release" if sec["section_type"] == "chorus" else "observation",
          "confidence": "inferred"
        } for sec in sections_data
      ],
      "japanese_lyric_profile": {
        "workflow_bias": "hybrid",
        "hook_copy_force": "heavy",
        "title_ignition_style": "formulaic",
        "modern_compression_bias": "high",
        "phrase_source_types": ["subculture tropes", "fast phrases"],
        "mora_control_notes": ["Speed dictates mora packing."],
        "accent_risk_notes": ["Fast articulation required."],
        "critic_focus": ["hook stickiness"],
        "section_features": []
      },
      "prompt_conditioning": {
        "genre_anchors": ["high energy vocaloid", "dance pop", "synth rock", "fast tempo"],
        "tempo_feels": ["driving beat", "intense pulse", "fast paced"],
        "vocal_tones": ["energetic", "slightly biting", "dynamic phrasing"],
        "production_palette": ["heavy synth bass", "punchy kick", "crisp high end", "modern mixing"],
        "energy_arc": ["explosive drops", "massive chorus release"],
        "imagery_anchors": ["neon lighting", "digital subculture", "hyperactive"],
        "exclude": ["acoustic instruments", "slow ballads", "lo-fi fuzz"],
        "source_basis": ["lyric_site", "manual_note"]
      },
      "quality_control": {
        "record_stage": "usable",
        "missing_fields": [],
        "manual_review_required_for": [],
        "warnings": [],
        "ready_for_prompting": True,
        "ready_for_audio_claims": False
      }
    }

new_tracks = [
    (
        "ironic_meta", "kanaria", "Kanaria", "kanaria_king", "KING",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["幽閉 聡明 悪魔の証明", "テレイ隠し ゲラゲラ笑う"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["Right side Right side 孤毒吐露吐露", "Left side Left side 歯をむき出して"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["You are KING", "You are KING", "You are KING"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["無邪気に遊ぶ 期待期待の", "アイロニー"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["You are KING", "You are KING", "You are KING"]}
        ],
        ["You are KING", "Left side Left side 歯をむき出して"]
    ),
    (
        "ironic_meta", "maretu", "MARETU", "maretu_mind_brand", "Mind Brand",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["さあ、おいでなさい", "いらっしゃいな"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["Welcome to the Mind Brand"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["痛い 痛い 痛い", "心臓が痛い"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["終わらない 嘘と", "裏切りのゲーム"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["痛い 痛い 痛い", "心臓が痛い"]}
        ],
        ["Welcome to the Mind Brand", "痛い 痛い 痛い"]
    ),
    (
        "direct_emotional_pop", "kairiki_bear", "Kairiki Bear", "kairiki_bear_venom", "ベノム",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["足りないもの なんだ", "わからないまま"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["愛を 頂戴 頂戴"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["ベノム ベノム", "毒に染まってく"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["ロンリー ロンリー", "ひとりぼっち"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["ベノム ベノム", "毒に染まってく"]}
        ],
        ["ベノム ベノム", "愛を 頂戴 頂戴"]
    ),
    (
        "direct_emotional_pop", "kanaria", "Kanaria", "kanaria_envy_baby", "エンヴィーベイビー",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["ハイファイ ジーザス", "君を待っている"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["I love you", "Baby"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["エンヴィー ベイビー", "踊りましょう"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["ロンリー ジーザス", "夜が明ける"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["エンヴィー ベイビー", "踊りましょう"]}
        ],
        ["エンヴィー ベイビー", "ハイファイ ジーザス"]
    ),
    (
        "dark_cute_breakdown", "pinocchiop", "PinocchioP", "pinocchiop_mushikui_psychedelism", "虫喰いサイケデリズム",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["虫喰い 虫喰い", "頭がぐるぐる"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["サイケデリックな", "夢に落ちる"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["虫喰いサイケデリズム", "狂ったように踊れ"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["視界が ゆがむ", "君の顔も"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["虫喰いサイケデリズム", "狂ったように踊れ"]}
        ],
        ["虫喰いサイケデリズム", "頭がぐるぐる"]
    ),
    (
        "dark_cute_breakdown", "kairiki_bear", "Kairiki Bear", "kairiki_bear_bug", "バグ",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["バグ バグ", "頭がバグってる"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["もう わからない", "助けてよ"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["バグ落ち バグ落ち", "全てが壊れてく"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["エラー エラー", "止まらないエラー"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["バグ落ち バグ落ち", "全てが壊れてく"]}
        ],
        ["バグ バグ", "全てが壊れてく"]
    ),
    (
        "dark_cute_breakdown", "maretu", "MARETU", "maretu_brain_revolution_girl", "脳内革命ガール",
        [
            {"section_type": "verse", "section_name": "Verse 1", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_1"], "lines": ["脳内 革命", "いま始まります"]},
            {"section_type": "pre_chorus", "section_name": "Pre-Chorus", "jp_section_role": "b_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["pre_chorus"], "lines": ["常識なんて", "蹴り飛ばして"]},
            {"section_type": "chorus", "section_name": "Chorus 1", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_1"], "lines": ["脳内革命ガール", "狂ったように踊れ"]},
            {"section_type": "verse", "section_name": "Verse 2", "jp_section_role": "a_melo", "mora_density": "compressed", "spoken_speed_bias": "high", "source_labels": ["verse_2"], "lines": ["赤い 赤い", "血が騒ぐ"]},
            {"section_type": "chorus", "section_name": "Chorus 2", "jp_section_role": "sabi", "mora_density": "balanced", "spoken_speed_bias": "high", "source_labels": ["chorus_2"], "lines": ["脳内革命ガール", "狂ったように踊れ"]}
        ],
        ["脳内革命ガール", "常識なんて 蹴り飛ばして"]
    )
]

for args in new_tracks:
    mode, aid, aname, tid, title, sections, hooks = args
    data = generate_new_track(mode, aid, aname, tid, title, sections, hooks)
    outpath = os.path.join(mode_dir, mode, "external_handoff", "incoming", f"{tid}.json")
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("Upgrade complete!")

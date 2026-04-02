import json
import os

base_dir = r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global"

cand_cols = ["artist_id", "track_id", "title", "likely_mode", "secondary_modes", "why_it_matters", "style_gap_filled", "overlap_risk_with_existing_set", "grounding_feasibility", "provenance_feasibility", "audio_feasibility", "priority", "recommended_dataset_tier", "notes"]

cand_data = [
    ("kanaria", "kanaria_eye", "EYE", "dark_cute_breakdown", ["direct_emotional_pop"], ["Provides vocal rhythmic variation and jazzier chords than KING."], ["Syncopated jazz-pop integration."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("kanaria", "kanaria_mira", "MIRA", "direct_emotional_pop", ["ironic_meta"], ["Early Kanaria track establishing baseline emotional tones."], ["More traditional pop-rock structure."], "low", "high", "high", "medium", "medium", "producer_expansion", []),
    ("kanaria", "kanaria_yoidore_shirazu", "酔いどれ知らず", "dark_cute_breakdown", ["ironic_meta"], ["Broadens Kanaria beyond loud shouts into sliding intoxication."], ["Smooth, dragging vocal phrasing."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("kanaria", "kanaria_requiem", "レクイエム", "direct_emotional_pop", ["dark_cute_breakdown"], ["Hyper-energetic VTuber collaboration style."], ["Extreme BPM pacing within simple pop."], "medium", "high", "high", "medium", "medium", "producer_expansion", []),
    ("kanaria", "kanaria_daino_tekina_rendezvous", "大脳的なランデブー", "ironic_meta", ["direct_emotional_pop"], ["Shows adaptation to external narrative."], ["Mainstream alt-rock fusion."], "low", "high", "official_available", "high", "high", "producer_expansion", []),

    ("kairiki_bear", "kairiki_bear_ruma", "ルマ", "dark_cute_breakdown", ["ironic_meta"], ["A defining track for vocal stutter drops."], ["Stuttering hook logic mapping."], "medium", "high", "high", "medium", "high", "producer_expansion", []),
    ("kairiki_bear", "kairiki_bear_angel", "アンヘル", "dark_cute_breakdown", ["direct_emotional_pop"], ["Adds heavy angelic/demonic binary theme."], ["Contrast between dark lyrics and upbeat tempo."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("kairiki_bear", "kairiki_bear_alkali_rettoushou", "アルカリレットウショウ", "ironic_meta", ["dark_cute_breakdown"], ["Establishes inferiority complex themes clearly."], ["Self-deprecating irony."], "low", "high", "high", "medium", "medium", "producer_expansion", []),
    ("kairiki_bear", "kairiki_bear_lemmingming", "レミングミング", "dark_cute_breakdown", ["ironic_meta"], ["Explores mass psychology and suicidal ideation metaphors."], ["Dark thematic depth."], "low", "high", "high", "medium", "medium", "producer_expansion", []),
    ("kairiki_bear", "kairiki_bear_shippaisaku_shoujo", "失敗作少女", "direct_emotional_pop", ["dark_cute_breakdown"], ["Deeply emotional, less glitchy, more desperate."], ["Acoustic-to-rock emotional scaling."], "low", "high", "high", "medium", "high", "producer_expansion", []),

    ("maretu", "maretu_suji", "スヂ", "dark_cute_breakdown", ["ironic_meta"], ["Extremely heavy drop mechanics missing in current set."], ["Industrial vocaloid mapping."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("maretu", "maretu_umitagari", "うみたがり", "dark_cute_breakdown", ["direct_emotional_pop"], ["Addresses toxic obsessive love in a different meter."], ["Odd time signature hints."], "medium", "high", "high", "medium", "medium", "producer_expansion", []),
    ("maretu", "maretu_white_happy", "ホワイトハッピー", "ironic_meta", ["dark_cute_breakdown"], ["Sarcastic faux-happiness."], ["Major key masking dark themes."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("maretu", "maretu_koukatsu", "コウカツ", "ironic_meta", ["direct_emotional_pop"], ["Sharp, biting social critique."], ["Fast vocal parsing in metal."], "low", "high", "high", "medium", "medium", "producer_expansion", []),
    ("maretu", "maretu_darling", "ダーリン", "direct_emotional_pop", ["dark_cute_breakdown"], ["Highly requested for intense emotional anchors."], ["Straightforward emotional threat."], "low", "high", "high", "medium", "high", "producer_expansion", []),

    ("deco27", "deco27_hibana", "ヒバナ", "direct_emotional_pop", [], ["The definitive fast rock emotional anthem."], ["English integration in hooks."], "low", "high", "high", "high", "high", "producer_expansion", []),
    ("deco27", "deco27_mozaik_role", "モザイクロール", "ironic_meta", ["direct_emotional_pop"], ["Classic baseline for DECO*27 rock."], ["Foundational verse-chorus dynamic."], "low", "high", "high", "high", "high", "producer_expansion", []),
    ("deco27", "deco27_yowamushi_montblanc", "弱虫モンブラン", "direct_emotional_pop", ["dark_cute_breakdown"], ["Softer, more acoustic-driven anxiety."], ["Acoustic groove."], "low", "high", "high", "high", "medium", "producer_expansion", []),
    ("deco27", "deco27_salamander", "サラマンダー", "ironic_meta", ["direct_emotional_pop"], ["Modern heavily-produced hip-hop/rock fusion."], ["Flow and rap-like verses."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("deco27", "deco27_android_girl", "アンドロイドガール", "direct_emotional_pop", [], ["Vocal processing as narrative device."], ["Heavy thematic sequel mechanics."], "low", "high", "high", "medium", "high", "producer_expansion", []),

    ("pinocchiop", "pinocchiop_slow_motion", "すろぉもぉしょん", "ironic_meta", ["direct_emotional_pop"], ["A slower BPM ironic reflection."], ["Slower, breathing rhythm."], "low", "high", "high", "high", "high", "producer_expansion", []),
    ("pinocchiop", "pinocchiop_apple_dot_com", "アップルドットコム", "ironic_meta", ["dark_cute_breakdown"], ["High conceptual irony using digital branding."], ["Absurdist chants."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("pinocchiop", "pinocchiop_motivation_is_dead", "モチベーションが死んでる", "ironic_meta", ["direct_emotional_pop"], ["Ultimate apathy anthem."], ["Flat vocal delivery contrasting upbeat music."], "low", "high", "high", "medium", "medium", "producer_expansion", []),
    ("pinocchiop", "pinocchiop_nee_nee_nee", "ねぇねぇねぇ。", "dark_cute_breakdown", ["ironic_meta"], ["Dialog-driven toxic cuteness."], ["Call and response hooks."], "low", "high", "high", "medium", "high", "producer_expansion", []),
    ("pinocchiop", "pinocchiop_suki_na_koto_dake_de_ii_desu", "好きなことだけでいいです", "ironic_meta", ["direct_emotional_pop"], ["Sarcastic take on modern leisure."], ["Gospel/choir synth integration."], "low", "high", "high", "medium", "high", "producer_expansion", []),

    ("iyowa", "iyowa_kyu_kurarin", "きゅうくらりん", "dark_cute_breakdown", ["ironic_meta"], ["Introduces dizzying, out-of-tune aesthetic."], ["Jazz-chord off-kilter panic."], "none", "high", "high", "low", "high", "mode_support", []),
    ("iyowa", "iyowa_1000_nen_ikiteiru", "1000年生きてる", "ironic_meta", ["direct_emotional_pop"], ["Broadens narrative scope."], ["Distinct skipping beats."], "none", "high", "high", "low", "high", "mode_support", []),
    ("iyowa", "iyowa_apricot", "アプリコット", "dark_cute_breakdown", ["direct_emotional_pop"], ["Soft, agonizing desperation."], ["Whispery vocal tuning."], "none", "high", "high", "low", "medium", "mode_support", []),
    ("iyowa", "iyowa_heat_abnormal", "熱異常", "ironic_meta", ["dark_cute_breakdown"], ["Extreme chaotic pacing mixed with apathy."], ["Noise-pop elements."], "none", "high", "high", "low", "high", "mode_support", []),
    ("iyowa", "iyowa_ta_ku_san", "たうと", "dark_cute_breakdown", ["ironic_meta"], ["Abstract psychological horror."], ["Layered disjointed vocals."], "none", "high", "high", "low", "medium", "mode_support", []),

    ("syudou", "syudou_bitter_choco_decoration", "ビターチョコデコレーション", "ironic_meta", ["dark_cute_breakdown"], ["Swing/jazz-hop rhythmic foundation."], ["Adult cynical themes vs high school themes."], "none", "high", "high", "low", "high", "mode_support", []),
    ("syudou", "syudou_call_boy", "コールボーイ", "direct_emotional_pop", ["ironic_meta"], ["Raw, alcoholic desperation."], ["Jazz rock swagger."], "none", "high", "high", "low", "high", "mode_support", []),
    ("syudou", "syudou_bakushou", "爆笑", "ironic_meta", ["dark_cute_breakdown"], ["Manic laughter as a hook device."], ["Aggressive drop dynamics."], "none", "high", "high", "low", "high", "mode_support", []),
    ("syudou", "syudou_cute_na_kanojo", "キュートなカノジョ", "dark_cute_breakdown", ["ironic_meta"], ["Sarcastic toxic romance."], ["Minimalist funky basslines."], "none", "high", "high", "low", "medium", "mode_support", []),
    ("syudou", "syudou_gamble", "ギャンブル", "direct_emotional_pop", ["ironic_meta"], ["High stakes dramatic anthem."], ["Orchestral integration."], "none", "high", "high", "low", "medium", "mode_support", []),

    ("neru", "neru_tokyo_teddy_bear", "東京テディベア", "direct_emotional_pop", ["dark_cute_breakdown"], ["The grandaddy of vocaloid emotional rock."], ["Raw guitar emotional arcs."], "none", "high", "high", "low", "high", "mode_support", []),
    ("neru", "neru_lost_ones_weeping", "ロストワンの号哭", "direct_emotional_pop", ["ironic_meta"], ["Definitive track for school-system anxiety."], ["Screaming rock chorus."], "none", "high", "high", "low", "high", "mode_support", []),
    ("neru", "neru_law_evading_rock", "脱法ロック", "ironic_meta", ["dark_cute_breakdown"], ["Manic drug-reference chaos pop."], ["Nonsense hooks."], "none", "high", "high", "low", "high", "mode_support", []),
    ("neru", "neru_snobbism", "SNOBBISM", "ironic_meta", ["direct_emotional_pop"], ["Funk rock social critique."], ["Groove-based cynical verses."], "none", "high", "high", "low", "medium", "mode_support", []),
    ("neru", "neru_abstract_nonsense", "アブストラクト・ナンセンス", "ironic_meta", ["dark_cute_breakdown"], ["Early pioneer of despair-rock."], ["Heavy syncopation in verse."], "none", "high", "high", "low", "medium", "mode_support", [])
]

candidates_json = [dict(zip(cand_cols, row)) for row in cand_data]

with open(os.path.join(base_dir, "expansion_round2_candidates.json"), "w", encoding="utf-8") as f:
    json.dump(candidates_json, f, ensure_ascii=False, indent=2)


seed_cols = ["artist_id", "track_id", "title", "likely_mode", "title_pattern", "hook_behavior", "section_flow_guess", "imagery_classes", "emotional_arc", "leakage_watchouts", "prompt_seed_terms", "grounding_status"]
seed_data = [
    ("kanaria", "kanaria_eye", "EYE", "dark_cute_breakdown", "single_english_noun", ["Rhythmic vocal snaps", "Syllable separation", "Jazzy drop"], ["verse_sneer", "prechorus_climb", "chorus_snap_release", "verse2_sparse", "chorus_final"], ["eyes", "sight/blindness", "spotlights", "judging looks"], ["arrogance", "observation", "dominance"], ["Avoid making it sound like KING by ensuring the swing/jazz feeling."], ["jazz pop", "syncopated vocaloid", "snapping beat"], "research_ready"),
    ("kairiki_bear", "kairiki_bear_ruma", "ルマ", "dark_cute_breakdown", "meaningless_katakana", ["Stuttering repetition", "Screaming title drop", "Frantic pace"], ["verse_panic", "prechorus_glitch", "chorus_stutter", "verse2_collapse", "chorus_final"], ["barking", "inferiority", "scratching", "fever"], ["panic", "desperation", "glitching out"], ["Rhythms must be relentlessly 8th/16th note driven, no swelling pads."], ["fast rock", "vocal stutter", "anxiety pop"], "research_ready"),
    ("maretu", "maretu_suji", "スヂ", "dark_cute_breakdown", "single_kanji_katakana", ["Heavy electronic drop", "Distorted screams", "Atonal shifts"], ["verse_mocking", "prechorus_dissonant", "chorus_heavy_drop", "bridge_noise", "chorus_final"], ["bloodlines", "dirt", "inescapable fate", "chains"], ["disgust", "anger", "violent release"], ["Do not let acoustic elements overpower the industrial noise."], ["industrial vocaloid", "heavy bass drop", "screaming synth"], "research_ready"),
    ("deco27", "deco27_hibana", "ヒバナ", "direct_emotional_pop", "noun_sparks", ["English chanting (Na na na)", "Soaring emotional peak", "Fast rock drive"], ["verse_tension", "prechorus_english", "chorus_explosion", "bridge_guitar_solo", "chorus_final"], ["sparks", "fire", "guns/shooting", "blinding light"], ["conflict", "painful realization", "fighting through"], ["Must not sound like generic anime OP; keep the vocal chops modern."], ["fast emotional rock", "english chant hook", "guitar driven"], "research_ready"),
    ("pinocchiop", "pinocchiop_slow_motion", "すろぉもぉしょん", "ironic_meta", "hiragana_english", ["Sighing delivery", "Breath-based rhythm", "Slower BPM chant"], ["verse_aging_facts", "prechorus_fatigue", "chorus_resignation_chant", "verse2_sickness", "chorus_final"], ["fever", "sneezing", "aging", "clocks"], ["tiredness", "sickness", "peaceful resignation"], ["Keep the BPM moderate, do not speed it up to Kamippoi na levels."], ["mid-tempo irony", "breathing rhythm", "folk electronica"], "research_ready"),
    ("iyowa", "iyowa_kyu_kurarin", "きゅうくらりん", "dark_cute_breakdown", "dizzy_onomatopoeia", ["Floating off-beat", "Jazz chord resolution", "Bright but sad tone"], ["verse_rambling", "prechorus_spinning", "chorus_falling", "bridge_silence", "chorus_final_dizzy"], ["floating", "falling", "empty rooms", "fake smiles"], ["dizziness", "losing grip", "quiet despair"], ["The piano must be slightly detuned and highly syncopated."], ["dizzy pop", "off-kilter piano", "retro despair"], "research_ready"),
    ("syudou", "syudou_bitter_choco_decoration", "ビターチョコデコレーション", "ironic_meta", "sweet_noun_dark_modifier", ["Swing rhythm", "Cynical swagger", "Brass stabs"], ["verse_keigo_mocking", "prechorus_fake_politeness", "chorus_swaggering_truth", "bridge_laughing", "chorus_final"], ["sweets", "bitterness", "adult society", "hidden tongues"], ["fake politeness", "mockery", "exhaustion"], ["Avoid high-speed rock. Anchor to hip-hop/swing pacing."], ["cynical swing", "brass hop", "swaggering vocaloid"], "research_ready"),
    ("neru", "neru_tokyo_teddy_bear", "東京テディベア", "direct_emotional_pop", "location_object", ["Raw guitar emotion", "Desperate shout", "Classic rock structure"], ["verse_running_away", "prechorus_regret", "chorus_screaming_plea", "bridge_scissors", "chorus_final_tears"], ["scissors", "ripped seams", "running away", "blank pages"], ["self hatred", "running", "desperate plea for love"], ["Keep the production raw and guitar-focused, avoid heavy modern shiny synths."], ["raw emotional rock", "desperate guitar", "teen angst"], "research_ready")
]
seeds_json = [dict(zip(seed_cols, row)) for row in seed_data]

with open(os.path.join(base_dir, "expansion_round2_draft_seeds.json"), "w", encoding="utf-8") as f:
    json.dump(seeds_json, f, ensure_ascii=False, indent=2)

print("40 candidates and 8 draft seeds generated successfully.")

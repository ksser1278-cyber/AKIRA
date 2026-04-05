import json
import os

base_dir = r"C:\JPop_Songwriter\AKIRA ENGINE\data\_global\round2_expansion"

seed_cols = [
    "artist_id", "track_id", "title", "likely_mode", "title_pattern", 
    "hook_behavior", "section_flow_guess", "imagery_classes", "emotional_arc", 
    "leakage_watchouts", "prompt_seed_terms", "grounding_status"
]

seed_data = [
    ("kanaria", "kanaria_mira", "MIRA", "direct_emotional_pop", "single_roman_title", 
     ["direct title hit", "bright pressure hook"], ["verse_confession", "prechorus_climb", "chorus_release", "bridge_reflection", "chorus_final"],
     ["distance", "light", "staring"], ["distance", "need", "release"], ["avoid KING-like slogan repetition"], ["bright alt-pop", "synthetic lead"], "research_ready"),
    
    ("kanaria", "kanaria_yoidore_shirazu", "酔いどれ知らず", "dark_cute_breakdown", "abstract_concept", 
     ["sliding motif", "intoxicated slur", "syncopated drop"], ["verse_drunk", "prechorus_stumble", "chorus_slide", "verse2_haze", "chorus_final"],
     ["alcohol", "dizziness", "night lights", "loss of control"], ["sober sadness", "intoxication", "escapism"], ["do not use screaming drops; use sliding jazz drops"], ["jazz swing", "drunken beat", "sliding synth"], "research_ready"),
     
    ("kanaria", "kanaria_requiem", "レクイエム", "direct_emotional_pop", "religious_katakana", 
     ["hyper speed chant", "back and forth vocals"], ["verse_fast", "prechorus_climb", "chorus_blast", "chorus_final"],
     ["stars", "prayers", "falling"], ["desperation", "high energy joy", "pleading"], ["avoid dark minor chords; keep it fiercely upbeat"], ["hyper pop", "fast synth rock", "duet vocals"], "research_ready"),
     
    ("kanaria", "kanaria_daino_tekina_rendezvous", "大脳的なランデブー", "ironic_meta", "scientific_noun_event", 
     ["chill indie groove", "dry delivery"], ["verse_cynical", "prechorus_steady", "chorus_dry_hook", "post_chorus_groove", "chorus_final"],
     ["brains", "meetings", "city streets", "mundane facts"], ["apathy", "slight amusement", "detachment"], ["prevent overdrive guitars; stick to indie rock tones"], ["indie rock", "dry vocal", "syncopated bass"], "research_ready"),

    ("kairiki_bear", "kairiki_bear_angel", "アンヘル", "dark_cute_breakdown", "demonic_katakana", 
     ["contrast hook", "soaring yet sarcastic"], ["verse_sneer", "prechorus_rapid", "chorus_angelic", "verse2_demonic", "chorus_final"],
     ["halos", "blood", "falling from grace", "feathers"], ["false purity", "revelation of rot", "panic"], ["ensure chorus melody opens up unlike typical stutter hooks"], ["angelic pop rock", "distorted guitar", "sarcastic choir"], "research_ready"),
     
    ("kairiki_bear", "kairiki_bear_alkali_rettoushou", "アルカリレットウショウ", "ironic_meta", "chemical_compound", 
     ["self-deprecating chant", "rock bounce"], ["verse_complaint", "prechorus_failure", "chorus_resignation_dance", "chorus_final"],
     ["chemicals", "failing grades", "comparisons", "trash"], ["inferiority", "jealousy", "manic acceptance"], ["keep the BPM extremely fast to mask the sad lyrics"], ["fast pop punk", "bouncy bass", "self-deprecating"], "research_ready"),
     
    ("kairiki_bear", "kairiki_bear_lemmingming", "レミングミング", "dark_cute_breakdown", "repetitive_nonsense", 
     ["dark march rhythm", "group chanting", "syncopated stops"], ["verse_following", "prechorus_cliff", "chorus_falling", "bridge_silence", "chorus_final"],
     ["cliffs", "crowds", "jumping", "blindness"], ["conformity", "group panic", "inevitable fall"], ["must maintain a marching or shuffling rhythm underneath the rock"], ["dark march", "heavy tom drums", "chanting hooks"], "research_ready"),
     
    ("kairiki_bear", "kairiki_bear_shippaisaku_shoujo", "失敗作少女", "direct_emotional_pop", "sad_noun", 
     ["raw emotive cry", "less glitch, more tearful"], ["verse_sadness", "prechorus_hope", "chorus_shattering", "bridge_acoustic", "chorus_final"],
     ["trash cans", "defective parts", "tears", "apologies"], ["sadness", "guilt", "desperate plea"], ["avoid the e-e-error stutter; rely on raw sustained high notes"], ["emotional guitar rock", "tearful vocal", "driving beat"], "research_ready"),

    ("maretu", "maretu_umitagari", "うみたがり", "dark_cute_breakdown", "desire_verb", 
     ["polyrhythmic stabs", "accusing melody"], ["verse_obsessive", "prechorus_twist", "chorus_heavy_drop", "chorus_final"],
     ["birth", "wounds", "dirt", "inescapable ties"], ["obsession", "pain", "toxic attachment"], ["incorporate odd time signatures or triplets against a 4/4 beat"], ["chiptune metal", "odd meter", "toxic lyrics"], "research_ready"),
     
    ("maretu", "maretu_white_happy", "ホワイトハッピー", "ironic_meta", "sarcastic_noun", 
     ["upbeat major key swing", "hidden noise"], ["verse_cheerful", "prechorus_cracks", "chorus_manic_joy", "bridge_noise", "chorus_final"],
     ["white lies", "forced smiles", "hidden stains"], ["fake happiness", "suppressed rage", "collapse"], ["the music MUST sound genuinely happy until the bridge destroys it"], ["happy ska metal", "major key trap", "forced smile"], "research_ready"),
     
    ("maretu", "maretu_koukatsu", "コウカツ", "ironic_meta", "blunt_kanji", 
     ["rapid fire syllables", "metal blast beats", "cynical truth"], ["verse_blast", "prechorus_halt", "chorus_hammer", "bridge_slow", "chorus_final"],
     ["spitting", "scum", "truth", "society"], ["pure rage", "judgment", "cynicism"], ["vocal parsing must be incredibly fast against metal drums"], ["speed metal vocaloid", "blast beats", "cynical shouting"], "research_ready"),
     
    ("maretu", "maretu_darling", "ダーリン", "direct_emotional_pop", "endearing_katakana", 
     ["painful plea matching heavy beat", "distorted romance"], ["verse_begging", "prechorus_rejection", "chorus_painful_love", "chorus_final"],
     ["hugging", "blood", "not letting go", "love as pain"], ["desperate love", "fear of abandonment", "toxic grip"], ["keep an emotional core despite the heavy industrial instrumentation"], ["industrial love song", "heavy bass", "pleading vocal"], "research_ready"),

    ("deco27", "deco27_mozaik_role", "モザイクロール", "ironic_meta", "wordplay_noun", 
     ["classic bouncy rock", "driving chorus melody"], ["verse_doubt", "prechorus_realization", "chorus_catchy_truth", "bridge_guitar_solo", "chorus_final"],
     ["pixels", "censorship", "hiding truth", "scissors"], ["doubt", "betrayal", "cutting ties"], ["anchor to late 2000s vocal-rock style; less dense than modern DECO"], ["classic vocaloid rock", "driving pop punk", "catchy hook"], "research_ready"),
     
    ("deco27", "deco27_yowamushi_montblanc", "弱虫モンブラン", "direct_emotional_pop", "soft_noun", 
     ["acoustic groove", "gentle sadness"], ["verse_acoustic", "prechorus_build", "chorus_soft_cry", "bridge_soft", "chorus_final"],
     ["sweets", "cowardice", "falling apart", "lies"], ["cowardice", "regret", "sadness"], ["avoid distorted guitars; use acoustic strumming and clean bass"], ["acoustic pop rock", "gentle vocal", "melancholy pop"], "research_ready"),
     
    ("deco27", "deco27_salamander", "サラマンダー", "ironic_meta", "mythical_beast", 
     ["rap flow verses", "hip-hop influenced drop"], ["verse_rap", "prechorus_hype", "chorus_swagger_drop", "chorus_final"],
     ["fire", "spitting", "confidence", "burning up"], ["swagger", "confidence", "fun"], ["incorporate trap beats and triplet rap flows into the rock frame"], ["rap rock", "trap vocaloid", "swaggering hook"], "research_ready"),
     
    ("deco27", "deco27_android_girl", "アンドロイドガール", "direct_emotional_pop", "sci_fi_noun", 
     ["soaring emotional climax", "vocal processing transitions"], ["verse_robotic", "prechorus_waking_up", "chorus_human_cry", "bridge_error", "chorus_final"],
     ["metal hearts", "wires", "tears", "fake memories"], ["numbness", "awakening", "painful love"], ["chorus must feature a massive emotional and melodic widening"], ["emotional synth rock", "soaring chorus", "robotic to human arc"], "research_ready"),

    ("pinocchiop", "pinocchiop_apple_dot_com", "アップルドットコム", "ironic_meta", "digital_domain", 
     ["digital chants", "flat delivery", "absurdist listing"], ["verse_listing", "prechorus_glitch", "chorus_deadpan_chant", "verse2_listing", "chorus_final"],
     ["websites", "apples", "information overload", "empty searches"], ["boredom", "information fatigue", "apathy"], ["the hook should sound like an annoying auto-playing ad"], ["hyperpop", "deadpan chant", "digital noise"], "research_ready"),

    ("pinocchiop", "pinocchiop_motivation_is_dead", "モチベーションが死んでる", "ironic_meta", "blunt_fact", 
     ["lazy dragging rhythm", "bouncy apathy"], ["verse_tired", "prechorus_yawning", "chorus_lazy_bounce", "chorus_final"],
     ["beds", "sleeping", "dead motivation", "giving up"], ["extreme laziness", "burnout", "peaceful apathy"], ["do not use driving rock beats; use dragging, slightly off swing beats"], ["lazy pop", "swinging apathy", "bouncy synths"], "research_ready"),

    ("pinocchiop", "pinocchiop_nee_nee_nee", "ねぇねぇねぇ。", "dark_cute_breakdown", "repetitive_greeting", 
     ["call and response", "cloying cuteness", "toxic dependence"], ["verse_greeting", "prechorus_ignoring", "chorus_demanding_attention", "bridge_anger", "chorus_final"],
     ["tapping shoulders", "ignored texts", "staring", "smiles"], ["loneliness", "needy demands", "anger"], ["must feature extreme panned call-and-response vocals"], ["cute electro pop", "needy vocals", "call and response"], "research_ready"),

    ("pinocchiop", "pinocchiop_suki_na_koto_dake_de_ii_desu", "好きなことだけでいいです", "ironic_meta", "passive_aggressive_fact", 
     ["gospel/choir synth integration", "sarcastic praise"], ["verse_mocking_praise", "prechorus_choir", "chorus_sarcastic_anthem", "chorus_final"],
     ["hobbies", "ignoring reality", "bubbles", "fake peace"], ["sarcasm", "false euphoria", "judgment"], ["the chorus must sound musically like a joyous gospel anthem while the lyrics are deeply cynical"], ["sarcastic gospel pop", "euphoric irony", "choir synths"], "research_ready"),

    ("iyowa", "iyowa_1000_nen_ikiteiru", "1000年生きてる", "ironic_meta", "grand_time_scale", 
     ["skipping syncopated beats", "layered whisper vocals"], ["verse_narrative", "prechorus_skip", "chorus_grand_jazz", "bridge_piano", "chorus_final"],
     ["millenniums", "dirt", "flowers", "boredom"], ["ancient boredom", "historical detachment", "jazz swing"], ["time signature should be 4/4 but played with extremely swung 16ths"], ["jazz pop", "off-kilter swing", "whisper layers"], "research_ready"),

    ("iyowa", "iyowa_apricot", "アプリコット", "dark_cute_breakdown", "soft_fruit", 
     ["fragile high-pitched melody", "gentle panic"], ["verse_soft", "prechorus_shivering", "chorus_fragile_cry", "bridge_silence", "chorus_final"],
     ["apricots", "bruises", "softness", "crying"], ["gentle sorrow", "fragility", "dizziness"], ["must lack heavy rock drums; rely on soft synths and piano"], ["fragile art pop", "soft piano", "gentle crying vocal"], "research_ready"),

    ("iyowa", "iyowa_heat_abnormal", "熱異常", "ironic_meta", "clinical_state", 
     ["extreme chaotic pacing", "noise pop transitions", "apathetic lead"], ["verse_noise", "prechorus_heat", "chorus_chaotic_apathy", "chorus_final"],
     ["thermometers", "fever", "melting logic", "static"], ["fever dream", "chaos", "apathy"], ["the backing track should sound like it is breaking apart while the vocal remains stable"], ["noise pop", "glitch jazz", "fever dream"], "research_ready"),

    ("iyowa", "iyowa_ta_ku_san", "たうと", "dark_cute_breakdown", "abstract_dizzy", 
     ["layered disjointed vocals", "dissonant harmony"], ["verse_creepy", "prechorus_stacking", "chorus_dissonant_burst", "bridge_weird", "chorus_final"],
     ["shadows", "spiders", "whispers", "too many things"], ["psychological overwhelm", "creepiness", "dread"], ["feature dense vocal harmonies that deliberately clash"], ["dissonant pop", "creepy vocal layers", "dark jazz"], "research_ready"),

    ("syudou", "syudou_call_boy", "コールボーイ", "direct_emotional_pop", "occupation_noun", 
     ["raw, alcoholic yell", "jazz rock swagger"], ["verse_drunk", "prechorus_stumbling", "chorus_desperate_yell", "bridge_guitar", "chorus_final"],
     ["bottles", "vomit", "neon signs", "regret"], ["drunk desperation", "self-loathing", "swagger"], ["incorporate jazz instrumentation (brass, upright bass) into the rock mix"], ["jazz rock", "drunk vocal", "swaggering pain"], "research_ready"),

    ("syudou", "syudou_bakushou", "爆笑", "ironic_meta", "violent_laughter", 
     ["manic laughter hook", "aggressive drop dynamics"], ["verse_mocking", "prechorus_breathing", "chorus_laughing_drop", "chorus_final"],
     ["laughing at others", "mirrors", "comedy", "clowns"], ["manic joy", "mockery", "superiority"], ["the hook must sound like violent, unhinged laughter"], ["aggressive trap metal", "manic laughter", "heavy bass"], "research_ready"),

    ("syudou", "syudou_cute_na_kanojo", "キュートなカノジョ", "dark_cute_breakdown", "sarcastic_description", 
     ["minimalist funky bassline", "whispered threats"], ["verse_funky", "prechorus_whisper", "chorus_sarcastic_groove", "bridge_dark", "chorus_final"],
     ["makeup", "knives", "cute clothes", "blood"], ["sarcastic love", "underlying threat", "toxic groove"], ["avoid heavy guitars; rely on funky, bouncy basslines to contrast the dark lyrics"], ["dark funk pop", "minimalist bass", "whispered threat"], "research_ready"),

    ("syudou", "syudou_gamble", "ギャンブル", "direct_emotional_pop", "risk_noun", 
     ["high stakes dramatic anthem", "orchestral integration"], ["verse_betting", "prechorus_rising_stakes", "chorus_orchestral_explosion", "chorus_final"],
     ["chips", "cards", "life on the line", "sweat"], ["high stakes thrill", "desperation", "glory"], ["use dramatic strings and brass alongside a trap/rock beat"], ["orchestral rock", "dramatic trap", "high stakes anthem"], "research_ready"),

    ("neru", "neru_lost_ones_weeping", "ロストワンの号哭", "direct_emotional_pop", "dramatic_phrase", 
     ["screaming rock chorus", "fast guitar riffs"], ["verse_math_problems", "prechorus_failure", "chorus_screaming_pain", "bridge_crying", "chorus_final"],
     ["blackboards", "math", "choking", "voiceless cries"], ["school anxiety", "rebellion", "anguish"], ["must be pure, high-BPM emo rock without electronic/kawaii elements"], ["fast emo rock", "screaming teen angst", "driving guitar"], "research_ready"),

    ("neru", "neru_law_evading_rock", "脱法ロック", "ironic_meta", "rebellious_noun", 
     ["manic drug-reference chaos pop", "nonsense hooks"], ["verse_bouncy_nonsense", "prechorus_clash", "chorus_chaotic_party", "chorus_final"],
     ["medicines", "dancing", "laws", "color explosions"], ["manic euphoria", "rebellion", "chaos"], ["incorporate absurd synth sirens and massive tempo elasticity"], ["chaos pop rock", "nonsense anthem", "upbeat rebellion"], "research_ready"),

    ("neru", "neru_snobbism", "SNOBBISM", "ironic_meta", "concept_noun", 
     ["funk rock social critique", "groove-based cynical verses"], ["verse_groove", "prechorus_cynical", "chorus_brass_rock", "bridge_bass", "chorus_final"],
     ["fake intellectuals", "empty words", "pointing fingers", "boredom"], ["cynicism", "bored judgment", "swagger"], ["use funk guitar strumming and brass hits"], ["funk rock", "brass rock", "cynical groove"], "research_ready"),

    ("neru", "neru_abstract_nonsense", "アブストラクト・ナンセンス", "ironic_meta", "concept_noun", 
     ["early pioneer of despair-rock", "heavy syncopation"], ["verse_syncopated", "prechorus_building_dread", "chorus_explosive_despair", "chorus_final"],
     ["trash", "garbage", "meaninglessness", "hanging heads"], ["despair", "nihilism", "rock catharsis"], ["stick to fundamental 2010s vocaloid rock tropes; fast bass, sharp drums"], ["2010s vocaloid rock", "syncopated bass", "nihilistic anthem"], "research_ready")
]

seeds_json = [dict(zip(seed_cols, row)) for row in seed_data]

for s in seeds_json:
    out_dir = os.path.join(base_dir, s['artist_id'], "seed_incoming")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{s['track_id']}.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

print("SUCCESS: 32 Draft Seeds deployed to seed_incoming directories.")

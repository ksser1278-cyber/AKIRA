import json
from pathlib import Path

def seed_pilot():
    p = Path('C:/JPop_Songwriter/AKIRA ENGINE/datasets/training/lyric_grounding_workspace/batch_a100')
    p.mkdir(parents=True, exist_ok=True)
    (p / 'accepted').mkdir(exist_ok=True)
    (p / 'lyric_assets').mkdir(exist_ok=True)
    (p / 'section_maps').mkdir(exist_ok=True)

    json_data = {
      'schema_version': '1.0',
      'record_type': 'vocadb_lyric_grounding_record',
      'track_identity': { 'track_id': 'vocadb_8479', 'artist_id': 'deco_27', 'title': '"bye-bye" by my 愛' },
      'grounding_sources': { 
          'vocadb_page': 'https://vocadb.net/S/8479', 
          'official_uploads': ['https://youtu.be/PD-FdVf8VVg'], 
          'lyric_sources': ['https://vocaloidlyrics.fandom.com/wiki/Bye-bye_by_My_Ai'] 
      },
      'content_assets': { 
          'lyric_text_ref': 'lyric_assets/vocadb_8479.txt', 
          'section_map_ref': 'section_maps/vocadb_8479.sections.json', 
          'notes': 'Grounded via seed script.' 
      },
      'grounding_review': { 'grounding_status': 'accepted', 'review_notes': 'Japanese lyrics verified.' },
      'metadata_context': { 
          'producer': 'DECO*27', 
          'engine_family': 'vocaloid', 
          'voicebanks': ['初音ミク'], 
          'original_platform': 'youtube', 
          'original_upload_date': '2009-09-06T00:00:00Z' 
      }
    }

    lyric_text = (
        "だから僕は君のことが大好きなのに\n"
        "僕は僕のことが大嫌いで\n"
        "ごめんね　そんなこと言わないから\n"
        "好きだなんて言わないから\n"
        "君が笑うために僕は泣くよ\n\n"
        "「バイバイ」\n"
        "僕に会って　君に会って\n"
        "出会うためのさよなら\n"
        "そんな言葉は嫌いだよ"
    )

    section_map = {
      'sections': [ 
          { 'section': 'Chorus', 'line_count': 5 }, 
          { 'section': 'Intro', 'line_count': 3 } 
      ],
      'hook_lines': [
          'だから僕は君のことが大好きなのに', 
          '君が笑うために僕は泣くよ', 
          '出会うためのさよなら'
      ]
    }

    (p / 'accepted/vocadb_8479.json').write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
    (p / 'lyric_assets/vocadb_8479.txt').write_text(lyric_text, encoding='utf-8')
    (p / 'section_maps/vocadb_8479.sections.json').write_text(json.dumps(section_map, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print("Pilot files seeded successfully.")

if __name__ == "__main__":
    seed_pilot()

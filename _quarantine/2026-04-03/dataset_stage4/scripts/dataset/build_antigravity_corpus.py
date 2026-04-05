import json
import argparse
from pathlib import Path

def build_user_prompt(record):
    """
    기획안(Blueprint) 데이터를 사용자 프롬프트로 변환합니다.
    (실제 데이터셋 스키마의 Key 이름에 맞게 수정해서 사용하세요)
    """
    mode = record.get("mode", "subculture_default")
    theme = record.get("theme", "unknown")
    structure = record.get("structure_summary", "Standard Verse-Chorus")
    
    # 모델에게 주어질 기획안 입력값
    prompt = f"Mode: {mode}\n"
    prompt += f"Theme: {theme}\n"
    prompt += f"Structure: {structure}\n\n"
    prompt += "Write the complete Japanese lyrics based on this blueprint."
    
    return prompt

def convert_to_antigravity_format(input_dir, output_file):
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    # 출력 폴더가 없다면 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 모델에 부여할 역할(System Persona)
    system_instruction = (
        "You are AKIRA ENGINE, a top-tier Japanese lyricist. "
        "Your task is to write high-quality J-Pop and Vocaloid-style lyrics "
        "that perfectly match the requested mode, theme, and structure."
    )
    
    processed_count = 0
    
    print(f"🔍 '{input_path}' 폴더에서 큐레이션된 데이터를 탐색 중...")
    
    if not input_path.exists():
        print(f"⚠️ 폴더가 존재하지 않습니다: {input_path}")
        return

    with open(output_path, 'w', encoding='utf-8') as out_f:
        # datasets/curated 하위의 모든 .jsonl 파일을 순회
        for jsonl_file in input_path.rglob("*.jsonl"):
            with open(jsonl_file, 'r', encoding='utf-8') as in_f:
                for line in in_f:
                    if not line.strip():
                        continue
                        
                    record = json.loads(line)
                    
                    # 1. 가사 원문 추출 (Key 이름이 다를 경우 수정 필요)
                    lyrics = record.get("lyrics", "")
                    if not lyrics:
                        continue
                        
                    # 2. 사용자 프롬프트(기획안) 조립
                    user_prompt = build_user_prompt(record)
                    
                    # 3. Antigravity(Gemini) 파인튜닝 규격으로 포맵팅
                    antigravity_record = {
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt},
                            {"role": "model", "content": lyrics}
                        ]
                    }
                    
                    # JSONL 형태로 한 줄씩 쓰기
                    out_f.write(json.dumps(antigravity_record, ensure_ascii=False) + "\n")
                    processed_count += 1
                    
    print(f"✅ 변환 완료: 총 {processed_count}곡의 가사가 Antigravity 포맷으로 변환되었습니다.")
    print(f"📂 저장 경로: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Antigravity Fine-tuning Corpus")
    # 기본 경로는 AKIRA 파이프라인 설계에 맞춤
    parser.add_argument("--input", default="datasets/curated", help="큐레이션 데이터 폴더")
    parser.add_argument("--output", default="datasets/finetuning/antigravity_lyrics_corpus.jsonl", help="출력될 파일")
    args = parser.parse_args()
    
    convert_to_antigravity_format(args.input, args.output)

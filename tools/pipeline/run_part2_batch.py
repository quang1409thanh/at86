import os
import shutil
import time
from part2.extractor import process_part2
from common.llm import transcribe_audio
from common.io import update_test_json, load_progress

def run_batch(log_callback=None, input_config=None):
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    # Resolve paths relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    config = input_config or {}
    test_id = config.get("test_id", "PART2_TEST")
    
    default_audio = os.path.join(project_root, "tools", "data", "PART2")
    audio_dir = config.get("audio_dir", default_audio)
    
    # Allow relative paths in config to be resolved against project root
    if not os.path.isabs(audio_dir): audio_dir = os.path.join(project_root, audio_dir)
    
    static_data_dir = os.path.join(project_root, "data", "tests", test_id)
    title = f"TOEIC {test_id} - Practice"
    instructions = "You will hear a question or statement and three responses spoken in English. Select the best response and transcribe what you hear."
    
    if not os.path.exists(static_data_dir):
        os.makedirs(static_data_dir, exist_ok=True)
    
    # List audio files in order
    audio_files = sorted([f for f in os.listdir(audio_dir) if f.endswith('.mp3')])
    
    # 1. Load existing progress
    test_json_path = os.path.join(static_data_dir, "test.json")
    log(f"[*] Checking progress in: {test_json_path}")
    final_questions = load_progress(2, file_path=test_json_path) or []
    if final_questions:
        log(f"[*] Found {len(final_questions)} existing questions. Resuming from question {len(final_questions) + 1}")

    try:
        for i, file_name in enumerate(audio_files):
            if i < len(final_questions):
                continue
                
            audio_src = os.path.join(audio_dir, file_name)
            
            # Determine strict Question ID from filename stem
            stem = os.path.splitext(file_name)[0]
            numeric_part = "".join(filter(str.isdigit, stem))
            question_id = f"q{int(numeric_part) if numeric_part else i+1}"

            log(f"\n--- Processing {file_name} (ID: {question_id}) ---")
            
            try:
                # 1. Transcribe
                transcript = transcribe_audio(audio_src)
                log(f"[*] Transcript: {transcript[:100]}...")
                
                # 2. Extract structured data
                questions = process_part2(transcript, question_id)
                
                # 3. Move Audio and Map
                # Force ID to be part2 specific to avoid collision with Part 1
                unique_qid = f"part2_{question_id}"
                audio_dst_name = f"{unique_qid}_audio.mp3"
                shutil.copy(audio_src, os.path.join(static_data_dir, audio_dst_name))
                
                for q in questions:
                    q['id'] = unique_qid 
                    q['audio'] = audio_dst_name
                    final_questions.append(q)
                    
                # PERSIST IMMEDIATELY using shared utility
                update_test_json(
                    test_id=test_id,
                    part_number=2,
                    questions=final_questions,
                    output_dir=static_data_dir,
                    title=title,
                    instructions=instructions
                )
                
                log(f"[+] Persisted {question_id} ({len(final_questions)} total)")
                
                # Respect rate limits
                time.sleep(1)
                    
            except Exception as e:
                print(f"[!] Error processing {file_name}: {e}")
                break
    finally:
        if final_questions:
            log(f"\n[+] Batch process ended. {len(final_questions)} questions persisted.")

if __name__ == "__main__":
    run_batch()

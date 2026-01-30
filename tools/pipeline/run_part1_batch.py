import os
import shutil
import time
from part1.extractor import process_part1
from common.llm import transcribe_audio
from common.pdf import extract_images_from_pdf
from common.io import update_test_json, load_progress

def run_batch(log_callback=None, input_config=None):
    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)

    # Resolve paths relative to project root
    # script is in tools/pipeline/run_part1_batch.py
    # project root is ../../
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    config = input_config or {}
    test_id = config.get("test_id", "PART1_TEST")
    
    # Defaults relative to project root
    default_pdf = os.path.join(project_root, "tools", "data", "PART1", "part1.pdf")
    default_audio = os.path.join(project_root, "tools", "data", "PART1")
    
    input_pdf = config.get("pdf_path", default_pdf)
    audio_dir = config.get("audio_dir", default_audio)
    
    # Allow relative paths in config to be resolved against project root
    if not os.path.isabs(input_pdf): input_pdf = os.path.join(project_root, input_pdf)
    if not os.path.isabs(audio_dir): audio_dir = os.path.join(project_root, audio_dir)
    
    temp_media = os.path.join(project_root, "tools", "pipeline", "temp_media")
    static_data_dir = os.path.join(project_root, "data", "tests", test_id)
    title = f"TOEIC {test_id} - Practice"
    instructions = "Listen to the four statements for each photo. Transcribe each statement."
    
    if not os.path.exists(static_data_dir):
        os.makedirs(static_data_dir)

    # 1. Automated PDF Extraction
    if os.path.exists(input_pdf):
        log(f"[*] Extracting images from {input_pdf}...")
        extract_images_from_pdf(input_pdf, temp_media)
        log("[+] Extraction complete.")
    
    images = sorted([f for f in os.listdir(temp_media) if f.endswith(('.png', '.jpg', '.jpeg'))])
    
    # 2. Load Progress
    test_json_path = os.path.join(static_data_dir, "test.json")
    final_questions = load_progress(1, file_path=test_json_path) or []
    if final_questions:
        log(f"[*] Resuming from question {len(final_questions) + 1}")

    try:
        for i, img_name in enumerate(images):
            question_num = i + 1
            if question_num <= len(final_questions):
                continue
                
            img_path = os.path.join(temp_media, img_name)
            audio_src = os.path.join(audio_dir, f"{question_num}.mp3")
            
            log(f"[*] Analyzing Question {question_num}...")
            try:
                audio_text = None
                if os.path.exists(audio_src):
                    audio_text = transcribe_audio(audio_src)
                
                questions = process_part1(img_path, f"q{question_num}", audio_text=audio_text)
                
                # Move files
                audio_dst_name = f"part1_q{question_num}_audio.mp3"
                img_dst_name = f"part1_q{question_num}_image.jpg"
                
                if os.path.exists(audio_src):
                    shutil.copy(audio_src, os.path.join(static_data_dir, audio_dst_name))
                shutil.copy(img_path, os.path.join(static_data_dir, img_dst_name))
                
                for q in questions:
                    q['id'] = f"part1_q{question_num}"
                    q['audio'] = audio_dst_name
                    q['image'] = img_dst_name
                    final_questions.append(q)
                
                # PERSIST IMMEDIATELY
                update_test_json(
                    test_id=test_id,
                    part_number=1,
                    questions=final_questions,
                    output_dir=static_data_dir,
                    title=title,
                    instructions=instructions
                )
                log(f"[+] Persisted q{question_num} ({len(final_questions)} total)")
                time.sleep(1)
                
            except Exception as e:
                print(f"[!] Error at question {question_num}: {e}")
                break
    finally:
        if final_questions:
            print(f"\n[+] Part 1 batch process ended. {len(final_questions)} questions persisted.")

if __name__ == "__main__":
    run_batch()

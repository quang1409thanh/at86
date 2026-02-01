import json
import os
from common.llm import call_llm

PART_1_PROMPT = """
Analyze the provided image for a TOEIC Part 1 (Photographs) question. 
Generate 4 statements (A, B, C, D) describing the image. 

{context_instruction}

Return a JSON object in this format:
{
  "questions": [
    {
      "id": "q1",
      "correct_answer": "X",
      "transcripts": {
        "A": "statement A content",
        "B": "statement B content",
        "C": "statement C content",
        "D": "statement D content"
      },
      "explanation": "Brief explanation of why the correct answer is right and others are wrong."
    }
  ]
}
"""

def process_part1(image_path: str, question_id: str = "q1", audio_text: str = None):
    print(f"[*] Processing Part 1 for image: {image_path}")
    
    context_instruction = ""
    if audio_text:
        context_instruction = f"IMPORTANT: Use the following actual audio transcription to identify the statements. Segment them into A, B, C, D and determine which one is correct based on the image:\n{audio_text}"
    else:
        context_instruction = "- One statement must be objectively correct and clearly visible.\n- The other three should be plausible distractors (using related keywords but describing incorrect actions or objects)."

    prompt = PART_1_PROMPT.replace("{context_instruction}", context_instruction).replace("q1", question_id)
    questions_data = call_llm(prompt, image_path=image_path, validate_json=True)
    
    # Enrichment
    final_questions = []
    # If call_llm already returned the list or dict
    if isinstance(questions_data, dict) and 'questions' in questions_data:
        final_questions = questions_data['questions']
    else:
        final_questions = questions_data

    # Enrich with image path expected by frontend
    for q in final_questions:
        q['image'] = os.path.basename(image_path)
        
    return final_questions

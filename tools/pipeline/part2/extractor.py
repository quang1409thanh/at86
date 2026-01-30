import json
import os
from common.llm import call_llm

PART_2_PROMPT = """
Analyze the following TOEIC Part 2 (Question-Response) transcript.
The transcript contains a question or statement followed by three response options (A, B, C).

Transcription:
{audio_text}

Your task:
1. Identify the Question/Statement.
2. Identify Option A, Option B, and Option C.
3. Determine which option is the logically correct response.
4. Provide a brief expert explanation for the choice.

Return a JSON object in this EXACT format:
{{
  "questions": [
    {{
      "id": "{question_id}",
      "correct_answer": "X",
      "transcripts": {{
        "question": "The main question/statement text",
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text"
      }},
      "explanation": "Brief explanation of why the correct answer is right and others are wrong."
    }}
  ]
}}
"""

def process_part2(audio_text: str, question_id: str = "q11"):
    print(f"[*] Processing Part 2 for ID: {question_id}")
    
    prompt = PART_2_PROMPT.format(audio_text=audio_text, question_id=question_id)
    raw_response = call_llm(prompt)
    
    try:
        data = json.loads(raw_response)
        return data['questions']
    except Exception as e:
        print(f"[!] Failed to parse LLM response for {question_id}: {e}")
        print(f"Raw response: {raw_response}")
        raise e

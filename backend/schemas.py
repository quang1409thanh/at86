from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class Question(BaseModel):
    id: str
    text: Optional[str] = None
    image: Optional[str] = None
    audio: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    transcripts: Optional[Dict[str, str]] = None # Map option key (A, B...) -> transcript, or "main" -> full script
    script: Optional[str] = None
    explanation: Optional[str] = None

class QuestionGroup(BaseModel):
    id: str
    audio: Optional[str] = None
    passage_text: Optional[str] = None
    passage_images: Optional[List[str]] = None
    questions: List[Question]
    transcripts: Optional[Dict[str, str]] = None # Transcripts for the whole group (e.g. Conversation)

class Part(BaseModel):
    part_number: int
    instructions: str
    questions: Optional[List[Question]] = None # Keep for Part 1, 2, 5
    groups: Optional[List[QuestionGroup]] = None # For Part 3, 4, 6, 7

class TestDetail(BaseModel):
    test_id: str
    title: str
    parts: List[Part]

class TestSummary(BaseModel):
    test_id: str
    title: str
    path: str

class UserResult(BaseModel):
    id: str # Unique ID for this attempt (e.g. test_id + timestamp)
    test_id: str
    timestamp: datetime
    score: int
    total_questions: int
    correct_count: int
    answers: Dict[str, str] # map question_id -> selected_option
    user_transcripts: Optional[Dict[str, Dict[str, str]]] = None # map question_id -> {option_key: text}
    user_notes: Optional[Dict[str, str]] = None # map question_id -> rationale note

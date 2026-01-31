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
    published_at: Optional[datetime] = None

class TestSummary(BaseModel):
    test_id: str
    title: str
    path: str
    published_at: Optional[datetime] = None

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

# Pipeline Schemas
class ProviderConfig(BaseModel):
    name: str  # e.g., "google", "openai", "claude"
    keys: List[str] = []
    models: List[str] = []
    current_key_index: int = 0
    current_model_index: int = 0

class LLMSettings(BaseModel):
    active_provider: str = "google"
    providers: List[ProviderConfig] = []

class PipelineConfig(BaseModel):
    settings: LLMSettings
    active_resource: str = "" # Description of what's currently being used

class PipelineRunRequest(BaseModel):
    part: int
    test_id: str = "ETS_Test_01"
    config: Optional[Dict[str, Any]] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

"""
User Mistake Analyzer
=====================
Analyzes user results to identify mistake patterns and generate learning insights.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


# Error type classification
ERROR_TYPES = {
    "listening_vocabulary": "Không nghe ra từ vựng",
    "listening_similar_sound": "Nhầm lẫn âm tương tự",
    "listening_speed": "Không theo kịp tốc độ nói",
    "listening_context": "Hiểu sai ngữ cảnh",
    "grammar_tense": "Sai về thì",
    "grammar_word_form": "Sai dạng từ",
    "grammar_article": "Sai mạo từ",
    "reading_inference": "Suy luận sai",
    "reading_detail": "Bỏ sót chi tiết",
    "reading_vocabulary": "Không hiểu từ vựng"
}


@dataclass
class UserMistake:
    """A user mistake record with full context for coaching."""
    doc_id: str
    user_id: str
    test_id: str
    question_id: str
    part_number: int
    user_answer: str
    correct_answer: str
    user_transcript: Optional[Dict[str, str]]
    correct_transcript: Optional[Dict[str, str]]
    error_type: str
    error_analysis: str
    timestamp: str
    question_text: Optional[str] = None  # For Part 5-7
    explanation: Optional[str] = None  # Original explanation
    
    def to_content(self) -> str:
        """
        Generate rich content for embedding.
        Includes transcript comparison for listening parts.
        """
        test_link = f"http://localhost:5173/test/{self.test_id}"
        parts = [
            f"=== Lỗi sai TOEIC ===",
            f"Test: [{self.test_id}]({test_link}) | Part {self.part_number} | Câu: {self.question_id}",
            f"User chọn: {self.user_answer} | Đáp án đúng: {self.correct_answer}",
            f"Loại lỗi: {ERROR_TYPES.get(self.error_type, self.error_type)}",
        ]
        
        # Part 1/2: Focus on listening transcript comparison
        if self.part_number <= 2 and self.user_transcript and self.correct_transcript:
            parts.append("\n--- So sánh Transcript ---")
            
            # Question comparison (Part 2)
            if 'question' in self.correct_transcript:
                user_q = self.user_transcript.get('question', '[không ghi]')
                correct_q = self.correct_transcript.get('question', '')
                parts.append(f"Câu hỏi đúng: \"{correct_q}\"")
                parts.append(f"User nghe: \"{user_q}\"")
                # Find missed words
                missed = self._find_missed_words(user_q, correct_q)
                if missed:
                    parts.append(f"Từ nghe thiếu: {', '.join(missed)}")
            
            # Correct answer comparison
            correct_text = self.correct_transcript.get(self.correct_answer, '')
            user_text = self.user_transcript.get(self.correct_answer, '[không ghi]')
            if correct_text:
                parts.append(f"\nĐáp án đúng ({self.correct_answer}): \"{correct_text}\"")
                parts.append(f"User nghe: \"{user_text}\"")
                missed = self._find_missed_words(user_text, correct_text)
                if missed:
                    parts.append(f"Từ nghe thiếu trong đáp án: {', '.join(missed)}")
            
            # User's wrong choice
            if self.user_answer != self.correct_answer:
                wrong_correct = self.correct_transcript.get(self.user_answer, '')
                wrong_user = self.user_transcript.get(self.user_answer, '[không ghi]')
                if wrong_correct:
                    parts.append(f"\nUser chọn ({self.user_answer}): \"{wrong_correct}\"")
                    parts.append(f"User nghe: \"{wrong_user}\"")
        
        # Part 3/4: Group listening
        elif self.part_number in [3, 4] and self.correct_transcript:
            parts.append("\n--- Transcript ---")
            main_trans = self.correct_transcript.get('main', '')
            if main_trans:
                parts.append(f"Nội dung hội thoại: \"{main_trans[:500]}...\"")
        
        # Part 5-7: Reading/Grammar
        elif self.part_number >= 5 and self.question_text:
            parts.append(f"\nCâu hỏi: {self.question_text}")
        
        # Add analysis and explanation
        if self.error_analysis:
            parts.append(f"\n--- Phân tích ---")
            parts.append(self.error_analysis)
        
        if self.explanation:
            parts.append(f"\n--- Giải thích chính thức ---")
            parts.append(self.explanation)
        
        return "\n".join(parts)
    
    def _find_missed_words(self, user_text: str, correct_text: str) -> List[str]:
        """Find words that user missed."""
        if not user_text or not correct_text:
            return []
        
        user_words = set(user_text.lower().split())
        correct_words = correct_text.lower().split()
        
        missed = []
        for word in correct_words:
            # Skip common words
            if word in ['the', 'a', 'an', 'is', 'are', 'to', 'of']:
                continue
            if word not in user_words and len(word) > 2:
                missed.append(word)
        
        return missed[:5]  # Return max 5 missed words
    
    def to_metadata(self) -> Dict[str, Any]:
        """Generate metadata for vector store filtering."""
        import json
        return {
            "user_id": self.user_id,
            "test_id": self.test_id,
            "question_id": self.question_id,
            "part_number": self.part_number,
            "user_answer": self.user_answer,
            "correct_answer": self.correct_answer,
            "error_type": self.error_type,
            "timestamp": self.timestamp,
            # Store transcripts as JSON strings for retrieval
            "correct_transcript": json.dumps(self.correct_transcript, ensure_ascii=False) if self.correct_transcript else None,
            "user_transcript": json.dumps(self.user_transcript, ensure_ascii=False) if self.user_transcript else None,
        }


class UserMistakeAnalyzer:
    """
    Analyzes user results to identify mistake patterns.
    
    Features:
    - Compare user answers with correct answers
    - Classify error types (listening/grammar/reading)
    - Compare user transcripts with correct transcripts
    - Generate insights for improvement
    """
    
    def __init__(
        self,
        results_dir: str = "data/users/default",
        tests_dir: str = "data/tests"
    ):
        self.results_dir = results_dir
        self.tests_dir = tests_dir
        self._test_cache: Dict[str, Dict] = {}
    
    def _load_test(self, test_id: str) -> Optional[Dict]:
        """Load and cache a test."""
        if test_id in self._test_cache:
            return self._test_cache[test_id]
        
        test_path = os.path.join(self.tests_dir, test_id, "test.json")
        if not os.path.exists(test_path):
            return None
        
        with open(test_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._test_cache[test_id] = data
            return data
    
    def _get_question_data(
        self,
        test_data: Dict,
        question_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find a question in test data."""
        for part in test_data.get("parts", []):
            part_number = part.get("part_number", 0)
            
            # Check individual questions
            for q in part.get("questions", []):
                if q.get("id") == question_id:
                    return {"question": q, "part_number": part_number}
            
            # Check groups
            for group in part.get("groups", []):
                for q in group.get("questions", []):
                    if q.get("id") == question_id:
                        return {
                            "question": q,
                            "part_number": part_number,
                            "group": group
                        }
        
        return None
    
    def analyze_result(self, result_data: Dict) -> List[UserMistake]:
        """
        Analyze a user result and identify mistakes.
        
        Args:
            result_data: User result JSON data
            
        Returns:
            List of UserMistake objects for incorrect answers
        """
        test_id = result_data.get("test_id", "")
        user_id = "default"  # Can be extended for multi-user
        timestamp = result_data.get("timestamp", datetime.now().isoformat())
        
        # Load test data
        test_data = self._load_test(test_id)
        if not test_data:
            print(f"[!] Test not found: {test_id}")
            return []
        
        mistakes = []
        answers = result_data.get("answers", {})
        user_transcripts = result_data.get("user_transcripts", {})
        
        for q_id, user_answer in answers.items():
            # Get question data
            q_data = self._get_question_data(test_data, q_id)
            if not q_data:
                continue
            
            question = q_data["question"]
            part_number = q_data["part_number"]
            correct_answer = question.get("correct_answer", "")
            
            # Check if wrong
            if user_answer.upper() == correct_answer.upper():
                continue  # Skip correct answers
            
            # Get transcripts
            user_trans = user_transcripts.get(q_id)
            correct_trans = None
            
            # Try to get correct transcript from question or group
            if question.get("transcripts"):
                correct_trans = question["transcripts"]
            elif q_data.get("group", {}).get("transcripts"):
                correct_trans = q_data["group"]["transcripts"]
            
            # Classify error type
            error_type = self._classify_error(
                part_number=part_number,
                user_answer=user_answer,
                correct_answer=correct_answer,
                user_transcript=user_trans,
                correct_transcript=correct_trans,
                question=question
            )
            
            # Generate analysis
            error_analysis = self._generate_analysis(
                part_number=part_number,
                user_answer=user_answer,
                correct_answer=correct_answer,
                user_transcript=user_trans,
                correct_transcript=correct_trans,
                question=question,
                error_type=error_type,
                q_data=q_data
            )
            
            # Extract question text for reading/grammar
            question_text = None
            if part_number >= 5:
                question_text = question.get("text") or question.get("question")
            
            mistakes.append(UserMistake(
                doc_id=f"user_{user_id}_mistake_{test_id}_{q_id}",
                user_id=user_id,
                test_id=test_id,
                question_id=q_id,
                part_number=part_number,
                user_answer=user_answer,
                correct_answer=correct_answer,
                user_transcript=user_trans,
                correct_transcript=correct_trans,
                error_type=error_type,
                error_analysis=error_analysis,
                timestamp=timestamp,
                question_text=question_text,
                explanation=question.get("explanation")
            ))
        
        return mistakes
    
    def _classify_error(
        self,
        part_number: int,
        user_answer: str,
        correct_answer: str,
        user_transcript: Optional[Dict],
        correct_transcript: Optional[Dict],
        question: Dict
    ) -> str:
        """Classify the type of error."""
        
        # Listening parts (1-4)
        if part_number <= 4:
            if user_transcript and correct_transcript:
                # Compare transcripts to find similar sound errors
                user_text = " ".join(user_transcript.values()).lower() if isinstance(user_transcript, dict) else ""
                correct_text = str(correct_transcript).lower()
                
                # Check for similar sound patterns
                if self._has_similar_sounds(user_text, correct_text):
                    return "listening_similar_sound"
                
                # Check for missing words
                if len(user_text) < len(correct_text) * 0.5:
                    return "listening_speed"
                
                return "listening_vocabulary"
            
            return "listening_context"
        
        # Part 5: Grammar
        if part_number == 5:
            options = question.get("options", [])
            if len(options) >= 4:
                # Check if options are word forms of the same root
                if self._are_word_forms(options):
                    return "grammar_word_form"
            return "grammar_tense"
        
        # Part 6-7: Reading
        if part_number >= 6:
            question_text = question.get("text", "").lower()
            if "infer" in question_text or "imply" in question_text:
                return "reading_inference"
            return "reading_detail"
        
        return "listening_context"  # Default
    
    def _has_similar_sounds(self, text1: str, text2: str) -> bool:
        """Check if texts have similar sounding words."""
        similar_pairs = [
            ("three", "tree"), ("ship", "sheep"), ("work", "walk"),
            ("right", "write"), ("their", "there"), ("hear", "here"),
            ("won", "one"), ("read", "red"), ("buy", "by"),
            ("sea", "see"), ("no", "know"), ("through", "threw")
        ]
        
        for word1, word2 in similar_pairs:
            if (word1 in text1 and word2 in text2) or (word2 in text1 and word1 in text2):
                return True
        
        return False
    
    def _are_word_forms(self, options: List[str]) -> bool:
        """Check if options are different forms of the same word."""
        if len(options) < 2:
            return False
        
        # Simple heuristic: check common suffixes
        suffixes = ["ly", "ness", "ment", "tion", "ing", "ed", "er", "est"]
        
        # Get stems by removing common suffixes
        stems = set()
        for opt in options:
            stem = opt.lower()
            for suf in suffixes:
                if stem.endswith(suf):
                    stem = stem[:-len(suf)]
                    break
            stems.add(stem[:4])  # First 4 chars as rough stem
        
        # If most stems are similar, likely word forms
        return len(stems) <= 2
    
    def _generate_analysis(
        self,
        part_number: int,
        user_answer: str,
        correct_answer: str,
        user_transcript: Optional[Dict],
        correct_transcript: Optional[Dict],
        question: Dict,
        error_type: str,
        q_data: Optional[Dict] = None
    ) -> str:
        """Generate a brief analysis of the error."""
        
        analysis_parts = []
        
        # Listening parts 1 & 2 analysis
        if part_number <= 2 and user_transcript and correct_transcript:
            correct_q = correct_transcript.get('question', '')
            user_q = user_transcript.get('question', '')
            
            if part_number == 2 and correct_q:
                # Compare question heard (Part 2)
                if user_q.lower() != correct_q.lower():
                    analysis_parts.append(f"Nghe sai câu hỏi: Bạn nghe là '{user_q}' nhưng thực tế là '{correct_q}'.")
            
            # Compare answers
            correct_ans_text = correct_transcript.get(correct_answer, '')
            user_ans_text = user_transcript.get(user_answer, '')
            
            if correct_ans_text:
                analysis_parts.append(f"Đáp án đúng ({correct_answer}) là: '{correct_ans_text}'.")
                user_record_of_correct = user_transcript.get(correct_answer, '')
                if user_record_of_correct and user_record_of_correct.lower() != correct_ans_text.lower():
                    analysis_parts.append(f"Bạn nghe đáp án đúng thành: '{user_record_of_correct}'.")
            
            if user_answer != correct_answer and user_ans_text:
                correct_user_choice_text = correct_transcript.get(user_answer, '')
                analysis_parts.append(f"Bạn chọn {user_answer} vì nghe là '{user_ans_text}' (Thực tế là '{correct_user_choice_text}').")
        else:
            # General analysis for other parts
            analysis_parts.append(f"User chọn {user_answer} thay vì {correct_answer}.")
            
            # Add context for reading if available
            if part_number >= 5 and q_data and q_data.get("group", {}).get("text"):
                context = q_data["group"]["text"]
                if len(context) > 100:
                    context = context[:100] + "..."
                analysis_parts.append(f"Ngữ cảnh: {context}")
        
        # Error-specific notes
        error_desc = ERROR_TYPES.get(error_type, "")
        if error_desc:
            analysis_parts.append(f"Loại lỗi dự đoán: {error_desc}.")
        
        return " ".join(analysis_parts)
    
    def get_user_error_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get a summary of user errors across all results.
        
        Returns:
            Dict with error statistics and patterns
        """
        error_counts: Dict[str, int] = {}
        part_errors: Dict[int, int] = {}
        total_mistakes = 0
        
        # Load all results
        if not os.path.exists(self.results_dir):
            return {"total_mistakes": 0, "error_types": {}, "weak_parts": []}
        
        for file_name in os.listdir(self.results_dir):
            if file_name.endswith(".json"):
                file_path = os.path.join(self.results_dir, file_name)
                try:
                    with open(file_path, "r") as f:
                        result_data = json.load(f)
                    
                    # Only include if user explicitly saved to RAG
                    if not result_data.get("rag_indexed", False):
                        continue
                        
                    mistakes = self.analyze_result(result_data)
                    total_mistakes += len(mistakes)
                    
                    for m in mistakes:
                        error_counts[m.error_type] = error_counts.get(m.error_type, 0) + 1
                        part_errors[m.part_number] = part_errors.get(m.part_number, 0) + 1
                        
                except Exception as e:
                    print(f"[!] Error processing {file_name}: {e}")
        
        # Find weak parts
        weak_parts = sorted(part_errors.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "total_mistakes": total_mistakes,
            "error_types": {
                k: {"count": v, "description": ERROR_TYPES.get(k, "")}
                for k, v in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
            },
            "weak_parts": [{"part": p, "error_count": c} for p, c in weak_parts]
        }


def analyze_user_result(result_id: str, vector_store=None) -> int:
    """
    Analyze a user result and index mistakes.
    
    Args:
        result_id: Result ID (filename without .json)
        vector_store: Optional ChromaVectorStore instance
        
    Returns:
        Number of mistakes indexed
    """
    from ..vectorstore import ChromaVectorStore
    
    if vector_store is None:
        vector_store = ChromaVectorStore()
    
    # Load result
    result_path = os.path.join("data/users/default", f"{result_id}.json")
    if not os.path.exists(result_path):
        print(f"[!] Result not found: {result_path}")
        return 0
    
    with open(result_path, "r") as f:
        result_data = json.load(f)
    
    # Analyze
    analyzer = UserMistakeAnalyzer()
    mistakes = analyzer.analyze_result(result_data)
    
    if not mistakes:
        print(f"[*] No mistakes found in result: {result_id}")
        return 0
    
    # Index mistakes
    ids = [m.doc_id for m in mistakes]
    contents = [m.to_content() for m in mistakes]
    metadatas = [m.to_metadata() for m in mistakes]
    
    # DEBUG LOGS
    print(f"\n{'='*20} RAG INDEXING DEBUG {'='*20}")
    print(f"[*] Result ID: {result_id}")
    print(f"[*] Number of mistakes to index: {len(mistakes)}")
    for i, (m_id, content, meta) in enumerate(zip(ids, contents, metadatas)):
        print(f"\n--- Mistake #{i+1} ---")
        print(f"ID: {m_id}")
        print(f"CONTENT:\n{content}")
        print(f"METADATA: {meta}")
    print(f"{'='*60}\n")
    
    vector_store.upsert_documents(
        collection="user",
        documents=contents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"[+] Indexed {len(mistakes)} mistakes from result: {result_id}")
    return len(mistakes)

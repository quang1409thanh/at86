"""
TOEIC Content Parser
====================
Parses test JSON files and indexes them into vector store.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToeicDocument:
    """A TOEIC content document."""
    doc_id: str
    test_id: str
    part_number: int
    question_id: str
    question_type: str  # photo, qr, conversation, talk, incomplete, text_completion, reading
    content: str
    correct_answer: str
    topics: List[str]
    
    def to_metadata(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "part_number": self.part_number,
            "question_id": self.question_id,
            "question_type": self.question_type,
            "correct_answer": self.correct_answer,
            "topics": ",".join(self.topics)
        }


class ToeicContentParser:
    """
    Parses TOEIC test JSON files into documents for indexing.
    
    Handles all 7 parts with their different structures:
    - Part 1-2: Individual questions with transcripts
    - Part 3-4: Question groups with shared audio/transcript
    - Part 5: Incomplete sentences
    - Part 6-7: Passage-based question groups
    """
    
    QUESTION_TYPES = {
        1: "photo",
        2: "qr",  # Question-Response
        3: "conversation",
        4: "talk",
        5: "incomplete",
        6: "text_completion",
        7: "reading"
    }
    
    def __init__(self, data_dir: str = "data/tests"):
        self.data_dir = data_dir
    
    def parse_test(self, test_id: str) -> List[ToeicDocument]:
        """
        Parse a single test JSON file.
        
        Args:
            test_id: Test ID (folder name)
            
        Returns:
            List of ToeicDocument objects
        """
        test_path = os.path.join(self.data_dir, test_id, "test.json")
        
        if not os.path.exists(test_path):
            print(f"[!] Test not found: {test_path}")
            return []
        
        with open(test_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        documents = []
        
        for part in data.get("parts", []):
            part_number = part.get("part_number", 0)
            instructions = part.get("instructions", "")
            
            # Handle individual questions (Part 1, 2, 5)
            if part.get("questions"):
                for q in part["questions"]:
                    doc = self._parse_question(
                        test_id=test_id,
                        part_number=part_number,
                        question=q,
                        instructions=instructions
                    )
                    if doc:
                        documents.append(doc)
            
            # Handle question groups (Part 3, 4, 6, 7)
            if part.get("groups"):
                for group in part["groups"]:
                    docs = self._parse_group(
                        test_id=test_id,
                        part_number=part_number,
                        group=group,
                        instructions=instructions
                    )
                    documents.extend(docs)
        
        return documents
    
    def _parse_question(
        self,
        test_id: str,
        part_number: int,
        question: Dict[str, Any],
        instructions: str
    ) -> Optional[ToeicDocument]:
        """Parse an individual question."""
        q_id = question.get("id", "unknown")
        
        # Build content
        content_parts = []
        
        # Question text
        if question.get("text"):
            content_parts.append(f"Question: {question['text']}")
        
        # Transcripts (for listening parts)
        if question.get("transcripts"):
            trans = question["transcripts"]
            if isinstance(trans, dict):
                for key, value in trans.items():
                    if key == "question":
                        content_parts.append(f"Question Audio: {value}")
                    else:
                        content_parts.append(f"Option {key}: {value}")
        
        # Options (for reading parts)
        if question.get("options") and part_number >= 5:
            opts = question["options"]
            if isinstance(opts, list) and all(isinstance(o, str) and len(o) > 1 for o in opts):
                # Full text options (Part 5, 6, 7)
                for i, opt in enumerate(opts):
                    label = chr(65 + i)  # A, B, C, D
                    content_parts.append(f"Option {label}: {opt}")
        
        # Correct answer
        correct = question.get("correct_answer", "")
        content_parts.append(f"Correct Answer: {correct}")
        
        # Explanation
        if question.get("explanation"):
            content_parts.append(f"Explanation: {question['explanation']}")
        
        content = "\n".join(content_parts)
        
        # Extract topics from content
        topics = self._extract_topics(content, part_number)
        
        return ToeicDocument(
            doc_id=f"{test_id}_p{part_number}_{q_id}",
            test_id=test_id,
            part_number=part_number,
            question_id=q_id,
            question_type=self.QUESTION_TYPES.get(part_number, "unknown"),
            content=content,
            correct_answer=correct,
            topics=topics
        )
    
    def _parse_group(
        self,
        test_id: str,
        part_number: int,
        group: Dict[str, Any],
        instructions: str
    ) -> List[ToeicDocument]:
        """Parse a question group (Part 3, 4, 6, 7)."""
        documents = []
        group_id = group.get("id", "unknown")
        
        # Get shared context (transcript or passage)
        shared_context = []
        
        if group.get("transcripts"):
            trans = group["transcripts"]
            if isinstance(trans, dict):
                if trans.get("main"):
                    shared_context.append(f"Transcript: {trans['main']}")
        
        if group.get("passage_text"):
            shared_context.append(f"Passage: {group['passage_text']}")
        
        shared_content = "\n".join(shared_context)
        
        # Parse each question in the group
        for question in group.get("questions", []):
            q_id = question.get("id", "unknown")
            
            content_parts = []
            
            # Add shared context
            if shared_content:
                content_parts.append(shared_content)
            
            # Question text
            if question.get("text"):
                content_parts.append(f"Question: {question['text']}")
            
            # Options
            if question.get("options"):
                for i, opt in enumerate(question["options"]):
                    label = chr(65 + i)
                    content_parts.append(f"Option {label}: {opt}")
            
            # Correct answer
            correct = question.get("correct_answer", "")
            content_parts.append(f"Correct Answer: {correct}")
            
            # Explanation
            if question.get("explanation"):
                content_parts.append(f"Explanation: {question['explanation']}")
            
            content = "\n".join(content_parts)
            topics = self._extract_topics(content, part_number)
            
            documents.append(ToeicDocument(
                doc_id=f"{test_id}_p{part_number}_{q_id}",
                test_id=test_id,
                part_number=part_number,
                question_id=q_id,
                question_type=self.QUESTION_TYPES.get(part_number, "unknown"),
                content=content,
                correct_answer=correct,
                topics=topics
            ))
        
        return documents
    
    def _extract_topics(self, content: str, part_number: int) -> List[str]:
        """Extract topic tags from content."""
        topics = []
        content_lower = content.lower()
        
        # Common TOEIC topics
        topic_keywords = {
            "travel": ["airport", "flight", "hotel", "travel", "passenger", "ticket"],
            "office": ["meeting", "office", "desk", "report", "manager", "employee"],
            "shopping": ["store", "shop", "buy", "price", "customer", "product"],
            "restaurant": ["restaurant", "menu", "food", "order", "waiter", "meal"],
            "announcement": ["attention", "announce", "inform", "notice", "reminder"],
            "weather": ["weather", "rain", "sunny", "temperature", "forecast"],
            "schedule": ["schedule", "appointment", "time", "date", "deadline"],
            "phone": ["phone", "call", "message", "voicemail"],
            "advertisement": ["new", "sale", "discount", "offer", "promotion"],
            "email": ["email", "letter", "message", "reply", "forward"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(topic)
        
        # Add part-specific topic
        topics.append(f"part{part_number}")
        
        return topics
    
    def get_all_test_ids(self) -> List[str]:
        """Get all available test IDs."""
        test_ids = []
        
        if not os.path.exists(self.data_dir):
            return []
        
        for folder in os.listdir(self.data_dir):
            folder_path = os.path.join(self.data_dir, folder)
            test_json = os.path.join(folder_path, "test.json")
            if os.path.isdir(folder_path) and os.path.exists(test_json):
                test_ids.append(folder)
        
        return test_ids


def index_test(test_id: str, vector_store=None) -> int:
    """
    Parse and index a single test.
    
    Args:
        test_id: Test ID to index
        vector_store: Optional ChromaVectorStore instance
        
    Returns:
        Number of documents indexed
    """
    from ..vectorstore import ChromaVectorStore
    
    if vector_store is None:
        vector_store = ChromaVectorStore()
    
    parser = ToeicContentParser()
    docs = parser.parse_test(test_id)
    
    if not docs:
        return 0
    
    # Prepare for indexing
    ids = [doc.doc_id for doc in docs]
    contents = [doc.content for doc in docs]
    metadatas = [doc.to_metadata() for doc in docs]
    
    # Upsert to vector store
    vector_store.upsert_documents(
        collection="toeic",
        documents=contents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"[+] Indexed {len(docs)} documents from test: {test_id}")
    return len(docs)


def index_all_tests(data_dir: str = "data/tests", vector_store=None) -> int:
    """
    Parse and index all available tests.
    
    Args:
        data_dir: Directory containing test folders
        vector_store: Optional ChromaVectorStore instance
        
    Returns:
        Total number of documents indexed
    """
    from ..vectorstore import ChromaVectorStore
    
    if vector_store is None:
        vector_store = ChromaVectorStore()
    
    parser = ToeicContentParser(data_dir)
    test_ids = parser.get_all_test_ids()
    
    total = 0
    for test_id in test_ids:
        count = index_test(test_id, vector_store)
        total += count
    
    print(f"[+] Total indexed: {total} documents from {len(test_ids)} tests")
    return total

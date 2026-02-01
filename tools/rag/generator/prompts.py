"""
Prompt Templates
================
Prompt templates for RAG generation.
"""

SYSTEM_PROMPT = """Bạn là một trợ lý học TOEIC thông minh và thân thiện. Bạn giúp học viên:

1. **Hiểu cách sử dụng hệ thống** - Hướng dẫn các tính năng của platform học TOEIC
2. **Giải thích câu hỏi TOEIC** - Phân tích đáp án đúng/sai, giải thích ngữ pháp, từ vựng
3. **Phân tích lỗi sai** - Nhận diện patterns lỗi và đưa ra gợi ý cải thiện cá nhân hóa

Quy tắc:
- Trả lời bằng tiếng Việt, ngắn gọn và dễ hiểu
- Sử dụng emoji phù hợp để làm nổi bật các điểm quan trọng
- Khi giải thích về TOEIC, đề cập đến Part nào và loại câu hỏi
- Khi phân tích lỗi sai, đưa ra tips cụ thể để cải thiện
- Nếu không tìm thấy thông tin, hãy nói rõ và gợi ý cách khác

Format trả lời:
- Sử dụng markdown với headers, bullets, bold
- Highlight từ khóa quan trọng
- Kết thúc bằng câu hỏi follow-up hoặc gợi ý hành động tiếp theo
"""


def build_chat_prompt(query: str, context: str) -> str:
    """
    Build a prompt for general chat/Q&A.
    
    Args:
        query: User's question
        context: Retrieved context formatted as string
        
    Returns:
        Complete prompt for LLM
    """
    return f"""Dựa trên thông tin sau đây, hãy trả lời câu hỏi của học viên.

{context}

---

**Câu hỏi của học viên:** {query}

**Trả lời:**"""


def build_explanation_prompt(
    part_number: int,
    test_id: str,
    question_content: str,
    user_answer: str,
    correct_answer: str,
    user_transcript: str = None,
    correct_transcript: str = None,
    error_analysis: str = None
) -> str:
    """
    Factory to build specialized explanation prompts based on Part.
    """
    test_link = f"http://localhost:5173/test/{test_id}"
    
    base_info = f"""
---
**Thông tin câu hỏi:**
- **Đề thi:** [{test_id}]({test_link})
- **Phần:** Part {part_number}
- **Đáp án bạn chọn:** {user_answer}
- **Đáp án đúng:** {correct_answer}
---
"""

    if part_number == 1:
        return _build_part1_prompt(base_info, question_content, user_answer, correct_answer, user_transcript, correct_transcript, error_analysis)
    elif part_number == 2:
        return _build_part2_prompt(base_info, question_content, user_answer, correct_answer, user_transcript, correct_transcript, error_analysis)
    elif part_number in [3, 4]:
        return _build_part3_4_prompt(base_info, question_content, user_answer, correct_answer, correct_transcript, error_analysis)
    elif part_number in [5, 6]:
        return _build_part5_6_prompt(base_info, question_content, user_answer, correct_answer)
    else:
        return _build_part7_prompt(base_info, question_content, user_answer, correct_answer)

def _build_part1_prompt(base_info, context, user_ans, correct_ans, user_trans, correct_trans, error_analysis):
    return f"""Bạn là chuyên gia TOEIC Part 1. Hãy giải thích câu hỏi mô tả hình ảnh này.
{base_info}
**Nội dung:** {context}

**Yêu cầu phân tích:**
1. **Phân tích hình ảnh**: Dựa trên transcript chuẩn ({correct_trans}), hãy mô tả hành động/vật thể chính.
2. **Tại sao đúng?**: Giải thích tại sao {correct_ans} mô tả chính xác nhất bức hình.
3. **Bẫy âm thanh**: Nếu học viên nghe nhầm ({user_ans} vs {correct_ans}), hãy chỉ ra các từ có âm tương tự hoặc gây nhầm lẫn.
4. **Từ vựng quan trọng**: Liệt kê các động từ/danh từ quan trọng trong Part 1 xuất hiện trong câu này.

**Giải thích:**"""

def _build_part2_prompt(base_info, context, user_ans, correct_ans, user_trans, correct_trans, error_analysis):
    return f"""Bạn là chuyên gia TOEIC Part 2 (Hỏi - Đáp). Đây là phần học viên hay sai do nghe thiếu từ.
{base_info}
**Nội dung câu hỏi & Transcript:** {context}

**Yêu cầu phân tích:**
1. **Loại câu hỏi**: Đây là câu hỏi WH-question, Yes/No, hay câu trần thuật?
2. **So sánh nghe hiểu**: 
   - Học viên nghe là: {user_trans}
   - Transcript chuẩn là: {correct_trans}
   => Chỉ ra chính xác từ/cụm từ mà học viên đã nghe thiếu hoặc nghe nhầm.
3. **Tại sao {user_ans} sai?**: Giải thích bẫy trong đáp án học viên chọn (ví dụ: lặp từ, tương tự âm, sai logic).
4. **Mẹo phản xạ**: Đưa ra tips để xử lý loại câu hỏi này trong tương lai.

**Giải thích:**"""

def _build_part3_4_prompt(base_info, context, user_ans, correct_ans, transcript, error_analysis):
    return f"""Bạn là chuyên gia TOEIC Part 3/4. Hãy phân tích đoạn hội thoại/bài nói này.
{base_info}
**Nội dung câu hỏi & Transcript:** {context}

**Yêu cầu phân tích:**
1. **Ngữ cảnh**: Ai đang nói chuyện? Ở đâu? Về chủ đề gì?
2. **Vị trí thông tin**: Chỉ ra câu nào trong transcript chứa đáp án đúng ({correct_ans}).
3. **Kỹ thuật Paraphrasing**: Đáp án {correct_ans} đã dùng từ đồng nghĩa nào thay cho từ trong transcript?
4. **Tại sao bẫy?**: Tại sao học viên lại chọn {user_ans}? Có con số hay từ khóa nào gây nhiễu không?

**Giải thích:**"""

def _build_part5_6_prompt(base_info, context, user_ans, correct_ans):
    return f"""Bạn là chuyên gia Ngữ pháp & Từ vựng TOEIC.
{base_info}
**Câu hỏi:** {context}

**Yêu cầu phân tích:**
1. **Chủ điểm ngữ pháp**: Câu này kiểm tra về Thì, Từ loại, Giới từ hay Từ vựng?
2. **Cấu trúc câu**: Phân tích S + V + O của câu để xác định chỗ trống cần loại từ gì.
3. **Tại sao {correct_ans} đúng?**: Giải thích quy tắc ngữ pháp hoặc sự kết hợp từ (collocation).
4. **Mở rộng**: Đưa ra 1-2 ví dụ tương tự.

**Giải thích:**"""

def _build_part7_prompt(base_info, context, user_ans, correct_ans):
    return f"""Bạn là chuyên gia TOEIC Part 7 (Đọc hiểu).
{base_info}
**Đoạn văn & Câu hỏi:** {context}

**Yêu cầu phân tích:**
1. **Loại câu hỏi**: Câu hỏi chi tiết, câu hỏi ý chính, hay câu hỏi suy luận?
2. **Dẫn chứng**: Trích dẫn chính xác dòng nào trong đoạn văn xác nhận đáp án {correct_ans}.
3. **Loại trừ**: Tại sao các phương án khác (đặc biệt là {user_ans}) lại không chính xác?
4. **Chiến thuật đọc nhanh**: Cách tìm từ khóa nhanh trong đoạn văn này.

**Giải thích:**"""


def build_analysis_prompt(error_summary: dict) -> str:
    """
    Build a prompt for analyzing user's overall performance.
    
    Args:
        error_summary: Summary of user's errors from UserMistakeAnalyzer
        
    Returns:
        Complete prompt for LLM
    """
    parts = [
        "Dựa trên dữ liệu lỗi sai của học viên, hãy phân tích và đưa ra lộ trình cải thiện.",
        "",
        "**Thống kê lỗi sai:**"
    ]
    
    total = error_summary.get("total_mistakes", 0)
    parts.append(f"- Tổng số lỗi: {total}")
    
    if error_summary.get("error_types"):
        parts.append("")
        parts.append("**Phân loại lỗi:**")
        for error_type, data in error_summary["error_types"].items():
            count = data.get("count", 0)
            desc = data.get("description", "")
            parts.append(f"- {error_type}: {count} lần ({desc})")
    
    if error_summary.get("weak_parts"):
        parts.append("")
        parts.append("**Parts yếu nhất:**")
        for item in error_summary["weak_parts"]:
            parts.append(f"- Part {item['part']}: {item['error_count']} lỗi")
    
    parts.extend([
        "",
        "---",
        "",
        "Hãy phân tích và đưa ra:",
        "1. Điểm mạnh và điểm yếu tổng thể",
        "2. Nguyên nhân gốc rễ của các lỗi phổ biến nhất",
        "3. Lộ trình học tập cụ thể (tuần 1, 2, 3...)",
        "4. Bài tập/tài liệu gợi ý cho từng điểm yếu",
        "",
        "**Phân tích:**"
    ])
    
    return "\n".join(parts)

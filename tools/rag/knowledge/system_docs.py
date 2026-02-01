"""
System Documentation Generator
==============================
Generates knowledge base for platform usage.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SystemDocument:
    """A system knowledge document."""
    doc_id: str
    category: str  # usage, feature, faq, troubleshoot
    title: str
    content: str
    page_ref: str  # Related page route
    keywords: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "category": self.category,
            "title": self.title,
            "page_ref": self.page_ref,
            "keywords": ",".join(self.keywords)
        }
    
    def to_content(self) -> str:
        """Generate full content for embedding."""
        return f"{self.title}\n\n{self.content}"


class SystemDocGenerator:
    """
    Generates system knowledge documents for the TOEIC platform.
    
    These documents help users understand:
    - How to use the platform
    - What features are available
    - Common questions and troubleshooting
    """
    
    @staticmethod
    def generate() -> List[SystemDocument]:
        """Generate all system knowledge documents."""
        docs = []
        
        # === USAGE GUIDES ===
        
        docs.append(SystemDocument(
            doc_id="sys_overview",
            category="usage",
            title="Tổng quan hệ thống TOEIC Learning Platform",
            content="""
Đây là nền tảng học TOEIC trực tuyến với các tính năng:
- Làm bài thi TOEIC theo từng Part (1-7)
- Nghe audio và ghi transcript
- So sánh câu trả lời với đáp án đúng
- Xem lịch sử làm bài và tiến độ
- Pipeline tự động tạo đề từ PDF và audio

Hệ thống hỗ trợ tất cả 7 parts của bài thi TOEIC:
- Part 1: Photo Description (Mô tả hình ảnh)
- Part 2: Question-Response (Hỏi đáp)
- Part 3: Conversations (Đoạn hội thoại)
- Part 4: Short Talks (Bài nói ngắn)
- Part 5: Incomplete Sentences (Điền từ)
- Part 6: Text Completion (Hoàn thành đoạn văn)
- Part 7: Reading Comprehension (Đọc hiểu)
            """.strip(),
            page_ref="/",
            keywords=["tổng quan", "overview", "hướng dẫn", "guide", "platform"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_take_test",
            category="usage",
            title="Cách làm bài thi TOEIC",
            content="""
Để làm bài thi TOEIC:

1. Truy cập trang Home hoặc Test Explorer
2. Chọn bài thi bạn muốn làm
3. Click nút "Start Test" để bắt đầu
4. Với mỗi câu hỏi:
   - Part 1-2: Nghe audio, chọn đáp án (A/B/C/D)
   - Có thể ghi lại transcript những gì bạn nghe được
   - Part 3-4: Nghe đoạn hội thoại/bài nói, trả lời nhiều câu hỏi
   - Part 5-7: Đọc và chọn đáp án
5. Sau khi hoàn thành, click "Submit" để nộp bài
6. Xem kết quả với so sánh chi tiết từng câu

Tips:
- Bạn có thể replay audio nhiều lần
- Không giới hạn thời gian khi luyện tập
- Transcript giúp bạn nhận ra từ nghe sai
            """.strip(),
            page_ref="/test/:id",
            keywords=["làm bài", "test", "thi", "submit", "start"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_view_results",
            category="usage",
            title="Cách xem kết quả và phân tích lỗi",
            content="""
Sau khi nộp bài, bạn sẽ thấy trang kết quả với:

1. **Điểm số tổng quát**: Số câu đúng/tổng số câu
2. **Chi tiết từng câu**:
   - Đáp án bạn chọn vs đáp án đúng
   - Transcript chuẩn (nếu có)
   - So sánh transcript bạn ghi với chuẩn (diff view)
   - Giải thích tại sao đáp án đó đúng

3. **Xem lại lịch sử**: Vào trang History để xem tất cả bài đã làm
4. **Click vào bài cũ**: Để xem lại chi tiết từng lần làm

Cách sử dụng Diff View:
- Màu xanh: Phần bạn ghi đúng
- Màu đỏ: Phần bạn ghi sai hoặc thiếu
- Giúp nhận ra từ nào bạn nghe chưa chính xác
            """.strip(),
            page_ref="/result/:id",
            keywords=["kết quả", "result", "điểm", "score", "history", "lịch sử"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_transcript_feature",
            category="feature",
            title="Tính năng ghi Transcript",
            content="""
Tính năng Transcript giúp bạn luyện nghe hiệu quả hơn:

**Cách sử dụng:**
1. Khi làm Part 1 hoặc Part 2
2. Nghe audio
3. Ghi lại những gì bạn nghe được vào ô input
4. Có thể ghi từng option (A, B, C, D) riêng

**Lợi ích:**
- Tập trung nghe từng từ thay vì chỉ đoán đáp án
- Phát hiện từ hay nghe nhầm (minimal pairs)
- So sánh với transcript chuẩn để cải thiện
- Xây dựng vốn từ vựng listening

**Tips:**
- Không cần ghi chính tả 100% đúng
- Ghi theo những gì bạn nghe được
- Dùng Diff View để so sánh và học
            """.strip(),
            page_ref="/test/:id",
            keywords=["transcript", "ghi chép", "nghe", "listening", "dictation"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_ai_coach",
            category="feature",
            title="Tính năng AI Coach và Phân tích lỗi sai",
            content="""
AI Coach là người bạn đồng hành giúp học viên nhận ra các pattern lỗi sai và cải thiện:

**Cách hoạt động:**
1. Sau khi làm bài, hãy click "Lưu để phân tích" trên trang Kết quả.
2. Hệ thống sẽ phân tích so sánh user_transcript của bạn với transcript chuẩn.
3. Các lỗi sai này sẽ được lưu vào cơ sở dữ liệu Knowledge Base cá nhân.

**Các tính năng của AI Coach:**
- **Giải thích câu sai**: Trong trang kết quả, click "Hỏi AI: Tại sao tôi sai?" để nhận phân tích chi tiết.
- **Phân tích Part 1/2**: AI sẽ chỉ ra bạn nghe thiếu từ nào, nghe nhầm âm nào (ví dụ: "three years ago" vs "three a go").
- **Trang AI Coach**: Tổng hợp các lỗi bạn hay mắc phải nhất (Weak Parts) và đề xuất lộ trình học.
- **Chat trực tiếp**: Bạn có thể hỏi Coach về bất kỳ điều gì liên quan đến TOEIC hoặc bài làm của mình.
            """.strip(),
            page_ref="/coach",
            keywords=["ai coach", "phân tích lỗi", "mistake analysis", "coaching", "learning advisor"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_pipeline",
            category="feature",
            title="Pipeline tự động tạo đề thi",
            content="""
Pipeline là tính năng tự động xử lý PDF và audio để tạo đề thi:

**Part 1 Pipeline:**
- Input: File PDF chứa hình ảnh + thư mục audio (1.mp3, 2.mp3...)
- Output: Bài thi Part 1 với hình ảnh, audio, transcript tự động

**Part 2 Pipeline:**
- Input: Thư mục chứa file audio
- Output: Bài thi Part 2 với audio và transcript tự động

**Cách sử dụng:**
1. Đặt file PDF vào tools/data/PART1/
2. Đặt file audio vào cùng thư mục
3. Vào trang Pipeline
4. Chọn Part 1 hoặc Part 2
5. Nhập Test ID
6. Click "Start Processing"
7. Theo dõi tiến trình qua console

**LLM Configuration:**
- Có thể chọn provider: Google Gemini hoặc OpenAI
- Hỗ trợ rotation nhiều API key
- Cấu hình trong trang Settings
            """.strip(),
            page_ref="/pipeline",
            keywords=["pipeline", "tạo đề", "pdf", "audio", "llm"]
        ))
        
        # === FAQ ===
        
        docs.append(SystemDocument(
            doc_id="sys_faq_score",
            category="faq",
            title="FAQ: Điểm số được tính như thế nào?",
            content="""
Câu hỏi: Điểm số TOEIC trên platform được tính như thế nào?

Trả lời:
- Platform hiện tại tính điểm theo công thức đơn giản
- Mỗi câu đúng = một số điểm nhất định
- Tổng điểm tối đa mô phỏng thang điểm TOEIC (990)
- Đây là điểm tham khảo, không phải điểm chính thức

Điểm TOEIC thực tế:
- Bài thi thật có 200 câu (100 Listening + 100 Reading)
- Sử dụng thuật toán IRT (Item Response Theory)
- Điểm tối đa: 495 (L) + 495 (R) = 990
            """.strip(),
            page_ref="/result/:id",
            keywords=["điểm", "score", "tính điểm", "990", "faq"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_faq_part1_tips",
            category="faq",
            title="FAQ: Tips làm Part 1 hiệu quả",
            content="""
Câu hỏi: Làm sao để làm Part 1 tốt hơn?

Trả lời - Tips cho Part 1 (Photo Description):

1. **Quan sát kỹ trước khi nghe**: Nhìn hình và dự đoán các từ có thể xuất hiện

2. **Focus vào động từ**: Đáp án thường khác nhau ở động từ chính
   - holding vs reading vs writing
   - sitting vs standing vs walking

3. **Cẩn thận với similar sounds**:
   - "He's writing" vs "He's riding"
   - "She's watching" vs "She's washing"

4. **Loại trừ đáp án wrong detail**:
   - Vật thể không có trong hình
   - Số lượng người sai
   - Địa điểm không phù hợp

5. **Passive voice**: "is being done" vs "has been done"
            """.strip(),
            page_ref="/test/:id",
            keywords=["part 1", "photo", "hình ảnh", "tips", "mẹo", "faq"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_faq_part2_tips",
            category="faq",
            title="FAQ: Tips làm Part 2 hiệu quả",
            content="""
Câu hỏi: Làm sao để làm Part 2 tốt hơn?

Trả lời - Tips cho Part 2 (Question-Response):

1. **Nghe kỹ từ đầu tiên của câu hỏi**:
   - Where → Location answer
   - When → Time answer
   - Who → Person answer
   - What → Thing/Action answer
   - How → Method/Manner answer
   - Why → Reason answer

2. **Loại trừ Similar Sounds**:
   - Đáp án sai thường có từ nghe giống

3. **Cẩn thận câu hỏi Yes/No**:
   - Đáp án đúng có thể không phải Yes/No trực tiếp
   - "Do you have the report?" → "It's on your desk"

4. **Indirect answers**: Đáp án đúng thường gián tiếp, tự nhiên
   - "When is the meeting?" → "Right after lunch"

5. **Avoid traps**: Cùng topic nhưng không answer the question
            """.strip(),
            page_ref="/test/:id",
            keywords=["part 2", "question response", "hỏi đáp", "tips", "mẹo", "faq"]
        ))
        
        # === TROUBLESHOOTING ===
        
        docs.append(SystemDocument(
            doc_id="sys_troubleshoot_audio",
            category="troubleshoot",
            title="Xử lý sự cố: Audio không phát",
            content="""
Vấn đề: Audio không phát hoặc không có tiếng

Giải pháp:
1. Kiểm tra volume trên máy tính
2. Kiểm tra tai nghe/loa
3. Thử refresh trang (F5)
4. Thử trình duyệt khác (Chrome recommended)
5. Xoá cache trình duyệt
6. Kiểm tra file audio có tồn tại trong thư mục data/tests/

Nếu vẫn không được:
- Mở Developer Tools (F12)
- Xem tab Network để kiểm tra audio file
- Báo lỗi nếu file trả về 404
            """.strip(),
            page_ref="/test/:id",
            keywords=["audio", "không phát", "lỗi", "troubleshoot", "sửa lỗi"]
        ))
        
        docs.append(SystemDocument(
            doc_id="sys_troubleshoot_api",
            category="troubleshoot",
            title="Xử lý sự cố: API Error hoặc không tải được dữ liệu",
            content="""
Vấn đề: Trang không tải, hiện lỗi API, hoặc dữ liệu không xuất hiện

Giải pháp:
1. **Kiểm tra backend**:
   - Đảm bảo server đang chạy
   - Mặc định chạy tại http://localhost:8000
   - Thử truy cập http://localhost:8000/api/toeic/tests

2. **Kiểm tra frontend**:
   - Đảm bảo frontend đang chạy
   - Mặc định tại http://localhost:5173
   
3. **CORS error**:
   - Backend đã cấu hình allow_origins=["*"]
   - Thử refresh hoặc mở incognito

4. **Database error**:
   - Kiểm tra file .env có DATABASE_URL
   - Đảm bảo MySQL đang chạy nếu dùng MySQL

5. **Khởi động lại**:
   - cd backend && uvicorn app.main:app --reload
   - cd frontend && npm run dev
            """.strip(),
            page_ref="/",
            keywords=["api", "error", "lỗi", "không tải", "backend", "troubleshoot"]
        ))
        
        return docs


def generate_system_knowledge() -> List[Dict[str, Any]]:
    """
    Generate system knowledge as a list of dicts ready for indexing.
    
    Returns:
        List of dicts with 'id', 'content', 'metadata' keys
    """
    generator = SystemDocGenerator()
    docs = generator.generate()
    
    return [
        {
            "id": doc.doc_id,
            "content": doc.to_content(),
            "metadata": doc.to_dict()
        }
        for doc in docs
    ]

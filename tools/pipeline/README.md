# TOEIC Content Pipeline 🚀

This tool automates the creation of TOEIC practice tests from raw PDF and audio files.

## Technical Architecture (Part 1)

### 1. Image Extraction (`PyMuPDF`)
- The pipeline uses the `fitz` library (PyMuPDF) to scan the PDF for embedded raster images.
- In Part 1, it assumes that the images found are the photos for the questions.
- **Why?** Working with raw images extracted directly from the PDF ensures high resolution for the AI to analyze.

### 2. Semantic Analysis (`LLM - GPT-4o Vision`)
- The core of the intelligence is in `tools/pipeline/part1/extractor.py`.
- **Role of LLM**: 
    - **Vision**: It "looks" at the Photo and identifies key objects, actions, and settings.
    - **Generation**: It creates 4 statements (A, B, C, D) following the TOEIC style (using distractors like keywords related to the scene but describing wrong actions).
    - **Rationale**: It generates a pedagogical explanation for why the answer is correct.
- **Audio Context**: For Part 1, since the user provides the audio files, the LLM generates the *transcripts* that match those audio files.

### 3. File Mapping & Orchestration
- The `run_part1_batch.py` script matches extracted images with audio files (`1.mp3` -> `q1`) and moves final assets to the system's static directory.

## Technical Architecture (Part 2)

### 1. High-Accuracy Transcription (`Whisper STT`)
- Uses OpenAI's Whisper model to transcribe the `.mp3` files of the Question-Response section.
- This ensures 100% accuracy for the transcription fields, matching exactly what the student hears.

### 2. Semantic Segmentation (`LLM - GPT-4o`)
- The transcript is sent to a text-based LLM prompt (`tools/pipeline/part2/extractor.py`).
- **Role**:
    - **Parsing**: Splits the raw transcript into "Question", "Option A", "Option B", and "Option C".
    - **Reasoning**: Evaluates the 3 responses and picks the most logical one.
    - **Rationale**: Explains the logic behind the correct response.

## Deployment Structure
Currently, all output is automatically moved to:
- `data/tests/PART1_TEST/test.json` (The question database)
- `data/tests/PART1_TEST/*.jpg` (Transformed images)
- `data/tests/PART1_TEST/*.mp3` (Copied audio)

---

## 🛠 Usage Instructions

### 1. Requirements
Ensure you have the required Python libraries:
```bash
pip install pymupdf requests python-dotenv pillow
```

### 2. Setup
Make sure your `.env` file in the root directory has a valid `OPENAI_API_KEY`.

### 3. Running a Batch (Part 1)
To process a PDF and a folder of audio files:
1.  Place your PDF and Audio in `tools/data/PART1`.
2.  Run the batch script:
```bash
python tools/pipeline/run_part1_batch.py
```

### 4. Running a Batch (Part 2)
To process a folder of audio files (no PDF required):
1.  Place your `.mp3` files in `tools/data/PART2`.
2.  Run the batch script:
```bash
python tools/pipeline/run_part2_batch.py
```

### 5. Running Individual Questions
To process a single image (Part 1):
```bash
python tools/pipeline/main.py --part 1 --input <path_to_image.jpg> --output result.json
```

---
*Note: Pipeline for Part 3-7 is currently in design/development phase.*

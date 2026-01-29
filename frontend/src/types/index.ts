export interface Question {
    id: string;
    text?: string;
    image?: string;
    audio?: string;
    options?: string[];
    correct_answer?: string;
    transcripts?: Record<string, string>;
    script?: string;
    explanation?: string;
}

export interface QuestionGroup {
    id: string;
    audio?: string;
    passage_text?: string;
    passage_images?: string[];
    questions: Question[];
    transcripts?: Record<string, string>;
}

export interface Part {
    part_number: number;
    instructions: string;
    questions?: Question[]; // Keep for Part 1, 2, 5
    groups?: QuestionGroup[]; // For Part 3, 4, 6, 7
}

export interface TestDetail {
    test_id: string;
    title: string;
    parts: Part[];
}

export interface TestSummary {
    test_id: string;
    title: string;
    path: string;
}

export interface UserResult {
    id: string;
    test_id: string;
    timestamp: string;
    score: number;
    total_questions: number;
    correct_count: number;
    answers: Record<string, string>;
    user_transcripts?: Record<string, Record<string, string>>;
    user_notes?: Record<string, string>;
}

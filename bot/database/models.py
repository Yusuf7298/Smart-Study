from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class StudentModel:
    id: int
    telegram_id: int
    first_name: Optional[str]
    username: Optional[str]
    grade: Optional[str]
    education_level: Optional[str]
    preferred_language: str
    approval_status: str
    created_at: datetime
    updated_at: datetime

@dataclass
class ConversationModel:
    id: int
    telegram_id: int
    role: str  # 'user' or 'assistant'
    message: str
    created_at: datetime

@dataclass
class LearningSessionModel:
    id: int
    telegram_id: int
    subject: str
    topic: str
    subtopic: Optional[str]
    stage: str
    is_active: int
    created_at: datetime
    updated_at: datetime

@dataclass
class QuizSessionModel:
    id: int
    telegram_id: int
    learning_session_id: Optional[int]
    subject: str
    topic: str
    total_questions: int
    current_question: int
    correct_answers: int
    status: str
    created_at: datetime
    updated_at: datetime

@dataclass
class QuizQuestionModel:
    id: int
    quiz_session_id: int
    question_number: int
    question_text: str
    options_json: str
    correct_answer: str
    explanation: str
    student_answer: Optional[str]
    is_correct: Optional[int]
    created_at: datetime
    answered_at: Optional[datetime]

@dataclass
class TestResultModel:
    id: int
    telegram_id: int
    learning_session_id: Optional[int]
    subject: str
    topic: str
    questions_text: str
    student_answers: str
    score: int
    max_score: int
    letter_grade: str
    feedback: str
    created_at: datetime

@dataclass
class StudyMaterialModel:
    id: int
    telegram_id: int
    filename: str
    file_path: str
    file_id: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    title: Optional[str]
    page_count: int
    extracted_text: Optional[str]
    summary: Optional[str]
    topics_json: Optional[str]
    extraction_status: str
    extraction_error: Optional[str]
    is_active: int
    is_deleted: int
    created_at: datetime

@dataclass
class AdminLogModel:
    id: int
    admin_id: int
    action: str
    target_id: Optional[int]
    details: Optional[str]
    created_at: datetime

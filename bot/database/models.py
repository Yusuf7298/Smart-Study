from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

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
    phone_number: Optional[str] = None
    selected_courses_json: Optional[str] = "[]"
    payment_amount: int = 0
    payment_screenshot_file_id: Optional[str] = None
    payment_screenshot_path: Optional[str] = None
    payment_submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    has_exam_package: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def selected_courses(self) -> List[str]:
        if not self.selected_courses_json:
            return []
        try:
            data = json.loads(self.selected_courses_json)
            return data if isinstance(data, list) else []
        except Exception:
            return []

@dataclass
class CourseModel:
    id: str
    name: str
    emoji: str = "📚"
    description: Optional[str] = None
    is_active: bool = True

@dataclass
class ChapterModel:
    id: str
    course_id: str
    chapter_number: int
    title: str
    topics: List[str] = field(default_factory=list)

@dataclass
class PricingModel:
    id: str
    course_price: int = 50
    currency: str = "ETB"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None

@dataclass
class PaymentModel:
    id: str
    telegram_id: int
    selected_courses: List[str]
    unit_price: int
    total_amount: int
    currency: str = "ETB"
    pricing_version: int = 1
    status: str = "PENDING"
    receipt_file_id: Optional[str] = None
    receipt_storage_path: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    created_at: Optional[datetime] = None

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

    @property
    def options(self) -> List[str]:
        if not self.options_json:
            return []
        try:
            return json.loads(self.options_json)
        except Exception:
            return []

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

    @property
    def topics(self) -> List[str]:
        if not self.topics_json:
            return []
        try:
            return json.loads(self.topics_json)
        except Exception:
            return []

@dataclass
class ProgressModel:
    telegram_id: int
    courses_completed: List[str] = field(default_factory=list)
    chapters_completed: List[str] = field(default_factory=list)
    topics_completed: List[str] = field(default_factory=list)
    total_quizzes_taken: int = 0
    total_quiz_score: int = 0
    total_quiz_questions: int = 0
    total_tests_taken: int = 0
    total_test_score: int = 0
    total_pdf_sessions: int = 0
    strong_topics: List[str] = field(default_factory=list)
    weak_topics: List[str] = field(default_factory=list)
    total_study_minutes: int = 0

@dataclass
class AdminLogModel:
    id: int
    admin_id: int
    action: str
    target_id: Optional[int]
    details: Optional[str]
    created_at: datetime
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    amount: Optional[int] = None

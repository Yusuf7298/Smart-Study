from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
class StudentSchema(BaseModel):
    telegram_id: int = Field(..., description="Unique Telegram user ID")
    telegram_username: Optional[str] = Field(None, description="Telegram username without @")
    full_name: str = Field(..., description="Student full name")
    phone: Optional[str] = Field(None, description="Phone number")
    grade: Optional[str] = Field(None, description="Academic grade (1-12, College, University)")
    education_level: Optional[str] = Field("High School", description="Derived education level")
    language: str = Field("English", description="Preferred language: English, Amharic, or Afaan Oromo")
    registered_courses: List[str] = Field(default_factory=list, description="List of enrolled course names")
    registration_status: str = Field("PENDING_APPROVAL", description="Status: NOT_REGISTERED, PENDING_PAYMENT, PENDING_APPROVAL, APPROVED, REJECTED, SUSPENDED")
    payment_status: str = Field("PENDING", description="Status: PENDING, SUBMITTED, APPROVED, REJECTED")
    payment_amount: int = Field(0, description="Total ETB calculated fee")
    receipt_file_id: Optional[str] = None
    receipt_storage_path: Optional[str] = None
    payment_submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CourseSchema(BaseModel):
    course_id: str = Field(..., description="Unique slug or identifier for course")
    name: str = Field(..., description="Course display name")
    emoji: str = Field("📚", description="Emoji icon")
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SubjectSchema(BaseModel):
    subject_id: str = Field(..., description="Unique subject ID")
    course_id: str = Field(..., description="Parent course identifier")
    name: str = Field(..., description="Subject name")
    is_active: bool = True

class ChapterSchema(BaseModel):
    chapter_id: str = Field(..., description="Unique chapter identifier")
    course_id: str = Field(..., description="Parent course ID")
    chapter_number: int = Field(..., description="1-indexed chapter number")
    title: str = Field(..., description="Chapter title")
    topics: List[str] = Field(default_factory=list, description="List of topic titles in order")
    is_active: bool = True
class StudyMaterialSchema(BaseModel):
    material_id: str = Field(..., description="Unique study material identifier")
    telegram_id: int = Field(..., description="Uploader Telegram ID")
    filename: str = Field(..., description="Sanitized original filename")
    file_path: str = Field(..., description="Local or cloud storage path")
    file_id: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: str = "application/pdf"
    title: Optional[str] = None
    page_count: int = 1
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    extraction_status: str = "COMPLETED"
    extraction_error: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentSchema(BaseModel):
    payment_id: str = Field(..., description="Unique payment identifier")
    student_id: Optional[str] = None
    telegram_id: int = Field(..., description="Telegram ID of student")
    selected_courses: List[str] = Field(default_factory=list)
    unit_price: int = Field(50, description="Unit price per course in ETB")
    total_amount: int = Field(..., description="Total payment amount in ETB")
    currency: str = "ETB"
    pricing_version: int = 1
    status: str = Field("PENDING", description="PENDING, SUBMITTED, APPROVED, REJECTED")
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentReceiptSchema(BaseModel):
    receipt_id: str = Field(..., description="Unique receipt identifier")
    payment_id: str = Field(..., description="Associated payment ID")
    telegram_id: int = Field(..., description="Student Telegram ID")
    receipt_file_id: str = Field(..., description="Telegram file ID")
    receipt_storage_path: str = Field(..., description="Saved disk path")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

class LearningSessionSchema(BaseModel):
    session_id: str = Field(..., description="Unique session ID")
    telegram_id: int = Field(..., description="Student Telegram ID")
    subject: str = Field(..., description="Course/Subject being studied")
    topic: str = Field(..., description="Active topic name")
    subtopic: Optional[str] = None
    stage: str = Field("INTRODUCTION", description="INTRODUCTION, LEARNING, PRACTICE, QUIZ, REVIEW, MASTERED")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class QuizSessionSchema(BaseModel):
    quiz_id: str = Field(..., description="Unique quiz session ID")
    telegram_id: int = Field(..., description="Student Telegram ID")
    learning_session_id: Optional[str] = None
    subject: str
    topic: str
    total_questions: int = 5
    current_question: int = 1
    correct_answers: int = 0
    status: str = Field("IN_PROGRESS", description="IN_PROGRESS, COMPLETED, CANCELLED")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class QuizQuestionSchema(BaseModel):
    question_id: str = Field(..., description="Unique question ID")
    quiz_id: str = Field(..., description="Parent quiz ID")
    question_number: int
    question_text: str
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str
    student_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = None

class QuizResultSchema(BaseModel):
    result_id: str = Field(..., description="Unique result ID")
    telegram_id: int
    quiz_id: str
    subject: str
    topic: str
    score: int
    total_questions: int
    accuracy_percentage: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class TestResultSchema(BaseModel):
    test_id: str = Field(..., description="Unique test ID")
    telegram_id: int
    subject: str
    topic: str
    questions_text: str
    student_answers: str
    score: int
    max_score: int = 10
    letter_grade: str
    feedback: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProgressSchema(BaseModel):
    telegram_id: int
    courses_completed: List[str] = Field(default_factory=list)
    chapters_completed: List[str] = Field(default_factory=list)
    topics_completed: List[str] = Field(default_factory=list)
    total_quizzes_taken: int = 0
    total_quiz_score: int = 0
    total_quiz_questions: int = 0
    total_tests_taken: int = 0
    total_test_score: int = 0
    total_pdf_sessions: int = 0
    strong_topics: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    total_study_minutes: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationSchema(BaseModel):
    conversation_id: str = Field(..., description="Unique message ID")
    telegram_id: int
    role: str = Field(..., description="'user' or 'assistant'")
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdminLogSchema(BaseModel):
    log_id: str = Field(..., description="Unique log ID")
    admin_id: int
    action: str = Field(..., description="APPROVE_STUDENT, REJECT_STUDENT, SET_PRICING, BROADCAST, etc.")
    target_id: Optional[int] = None
    details: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    amount: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PricingSchema(BaseModel):
    pricing_id: str = Field(..., description="Unique pricing ID")
    course_price: int = Field(50, description="Price per course in ETB")
    currency: str = "ETB"
    is_active: bool = True
    version: int = 1
    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

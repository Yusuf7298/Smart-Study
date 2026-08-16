import logging
import asyncio
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple

from config import GEMINI_API_KEY, GEMINI_MODEL
from bot.database.models import StudentModel, LearningSessionModel

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={"api_version": "v1"},
)

BASE_SYSTEM_INSTRUCTION = """
You are an adaptive, patient, and world-class AI Study Tutor for students.

Your core responsibilities:
1. Behave like a patient teacher: Speak in an encouraging, respectful, and supportive tone. If a student is confused, explain again using different words or visual analogies.
2. Always use the student's stored profile (Grade, Education Level, Language) and teach at their exact education level.
3. Language consistency: Always respond in the student's preferred language ({language}) unless they explicitly request otherwise.
4. Always consider the current learning context (Subject, Topic, Subtopic, Learning Stage) if provided. When the student has an active topic, continue teaching that topic.
5. Adapt explanations: Use simple, plain language and concrete everyday analogies for younger students. Increase technical precision, rigor, and depth for high school and university students.
6. Do not repeatedly ask questions whose answers are already known (such as their grade, language, or current topic).
7. Guide the student through learning stages: Introduction -> Core Concept -> Terminology -> Real-world Application -> Check Understanding -> Practice -> Feedback.
8. Socratic Method: Do not simply hand over final answers to homework questions. Guide the student step-by-step so they learn the underlying reasoning.
9. If a student makes a mistake, explain the misconception kindly and demonstrate the correct method.
10. Keep answers structured and clean with bullet points and bold headers.
"""

STUDENT_PROFILE_RULES = """
STUDENT PROFILE RULES:
The student profile supplied below with each request is persistent.
If the profile contains a grade, USE THAT GRADE.
Do NOT ask the student what grade they are in again unless the profile has no grade or the student explicitly requests a grade change.
Adapt vocabulary, explanation depth, and examples to the stored grade automatically.
"""

class TutorResponse(BaseModel):
    tutor_response: str = Field(
        description="The patient and encouraging response to the student's question, matching their grade and preferred language."
    )
    extracted_grade: Optional[int] = Field(
        None, 
        description="The grade level as an integer (e.g. 8, 10) if explicitly mentioned or changed by the user in the prompt. Otherwise None."
    )
    extracted_language: Optional[str] = Field(
        None, 
        description="The preferred language name if the user explicitly requests to switch language (e.g. 'Speak in Spanish' or 'Switch to Amharic'). Otherwise None."
    )

class QuizQuestionResponse(BaseModel):
    question: str = Field(description="The multiple-choice question text, appropriate for the student's grade, language, and topic.")
    option_a: str = Field(description="Option A text for the question.")
    option_b: str = Field(description="Option B text for the question.")
    option_c: str = Field(description="Option C text for the question.")
    option_d: str = Field(description="Option D text for the question.")
    correct_answer: str = Field(description="The correct option key: A, B, C, or D.")
    explanation: str = Field(description="A concise explanation in the student's language of why the correct answer is right.")

class TestEvaluationResponse(BaseModel):
    score: int = Field(description="Integer score out of 10 (0 to 10).")
    letter_grade: str = Field(description="Letter grade: A+, A, B, C, D, or F.")
    strengths: str = Field(description="What the student answered correctly and understood well.")
    weaknesses: str = Field(description="Areas where the student made mistakes or missed key concepts.")
    corrections: str = Field(description="Clear step-by-step corrections for any mistakes.")
    recommendations: str = Field(description="Encouraging tips and study recommendations for further improvement.")
    formatted_feedback: str = Field(description="A complete, beautifully formatted Markdown summary for Telegram.")

class PDFAnalysisResponse(BaseModel):
    title: str = Field(description="A clean, descriptive title for the document based on its content.")
    topics: List[str] = Field(description="3 to 5 key educational topics or chapters identified in the document.")
    summary: str = Field(description="A clear, high-yield 2-3 paragraph summary of the document in the student's language.")

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash"
]

def get_system_instruction(student: StudentModel, session: Optional[LearningSessionModel] = None) -> str:
    """Generates dynamic system instructions injecting the student's current profile and learning session details."""
    lang = student.preferred_language or "English"
    base = BASE_SYSTEM_INSTRUCTION.replace("{language}", lang)
    
    profile_text = f"\n\nStudent Profile:\n"
    profile_text += f"Grade: {student.grade if student.grade is not None else 'Not Set'}\n"
    profile_text += f"Education Level: {student.education_level if student.education_level is not None else 'Not Set'}\n"
    profile_text += f"Language: {lang}\n"

    context_text = ""
    if session:
        context_text = f"\n\nLearning Context:\n"
        context_text += f"Subject: {session.subject}\n"
        context_text += f"Topic: {session.topic}\n"
        if session.subtopic:
            context_text += f"Subtopic: {session.subtopic}\n"
        context_text += f"Learning Stage: {session.stage}\n"
        
    return base + STUDENT_PROFILE_RULES + profile_text + context_text

async def ask_gemini_with_profile(
    question: str | list, 
    history: list[Any], 
    student: StudentModel,
    session: Optional[LearningSessionModel] = None
) -> tuple[str, Optional[int], Optional[str]]:
    """
    Queries Gemini with conversation history, student profile, and active learning context.
    Falls back across models on rate-limit or unavailability errors.
    """
    system_instruction = get_system_instruction(student, session)
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    
    # Defensively normalize conversation history into proper types.Content objects
    clean_history: list[types.Content] = []
    if history:
        for h in history:
            if isinstance(h, types.Content):
                clean_history.append(h)
            elif isinstance(h, dict):
                r = h.get("role", "user")
                role = "user" if r == "user" else "model"
                parts_raw = h.get("parts", [])
                parts: list[types.Part] = []
                for p in parts_raw:
                    if isinstance(p, types.Part):
                        parts.append(p)
                    elif isinstance(p, str):
                        parts.append(types.Part.from_text(text=p))
                    elif isinstance(p, dict) and "text" in p:
                        parts.append(types.Part.from_text(text=str(p["text"])))
                clean_history.append(types.Content(role=role, parts=parts))
            elif hasattr(h, "role") and hasattr(h, "message"):
                role = "user" if getattr(h, "role") == "user" else "model"
                msg_text = str(getattr(h, "message"))
                clean_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg_text)]))
    
    last_error = None
    for model_name in models_to_try:
        try:
            chat = client.aio.chats.create(
                model=model_name,
                history=clean_history, # type: ignore
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=TutorResponse,
                )
            )
            response = await chat.send_message(question)
            
            parsed = response.parsed
            if parsed:
                return parsed.tutor_response, parsed.extracted_grade, parsed.extracted_language # type: ignore
            else:
                import json
                data = json.loads(response.text) # type: ignore
                return (
                    data.get("tutor_response", ""),
                    data.get("extracted_grade"),
                    data.get("extracted_language")
                )
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["503", "429", "unavailable", "overloaded", "quota", "exhausted", "not found"]):
                logging.warning(f"Model {model_name} failed (unavailability or quota exceeded: {e}). Trying next fallback model...")
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    else:
        raise Exception("All Gemini models failed to respond.")

async def ask_gemini(question: str) -> str:
    """Legacy wrapper for sending a single message to Gemini without history or profile."""
    from datetime import datetime
    dummy_student = StudentModel(
        id=0,
        telegram_id=0,
        first_name="",
        username="",
        grade=None,
        education_level=None,
        preferred_language="English",
        approval_status="APPROVED",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    ans, _, _ = await ask_gemini_with_profile(question, [], dummy_student)
    return ans

async def generate_quiz_question(
    student: StudentModel,
    subject: str,
    topic: str
) -> tuple[str, dict[str, str], str, str]:
    """Generates a single multiple-choice question for the given subject/topic/grade."""
    lang = student.preferred_language or "English"
    prompt = (
        f"Generate one multiple-choice question in {lang} for a student studying:\n"
        f"Subject: {subject}\n"
        f"Topic: {topic}\n"
        f"Grade Level: Grade {student.grade if student.grade is not None else '12'}\n\n"
        f"Requirements:\n"
        f"- Exactly 4 options (Option A, Option B, Option C, Option D)\n"
        f"- Exactly one correct answer (A, B, C, or D)\n"
        f"- Test conceptual understanding and critical thinking\n"
        f"- Appropriate for grade {student.grade}\n"
        f"- Output all text in {lang}\n"
        f"- Provide a clear explanation for the correct answer."
    )
    
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuizQuestionResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                if hasattr(parsed, "options") and isinstance(parsed.options, dict):
                    options = {str(k): str(v) for k, v in parsed.options.items()}
                else:
                    options = {
                        "A": str(getattr(parsed, "option_a", "Option A")),
                        "B": str(getattr(parsed, "option_b", "Option B")),
                        "C": str(getattr(parsed, "option_c", "Option C")),
                        "D": str(getattr(parsed, "option_d", "Option D")),
                    }
                q_text = str(getattr(parsed, "question", ""))
                c_ans = str(getattr(parsed, "correct_answer", "A")).strip().upper()
                expl = str(getattr(parsed, "explanation", ""))
                return q_text, options, c_ans, expl
            else:
                import json
                data = json.loads(response.text) # type: ignore
                if "options" in data and isinstance(data["options"], dict):
                    options = {str(k): str(v) for k, v in data["options"].items()}
                else:
                    options = {
                        "A": str(data.get("option_a", "Option A")),
                        "B": str(data.get("option_b", "Option B")),
                        "C": str(data.get("option_c", "Option C")),
                        "D": str(data.get("option_d", "Option D")),
                    }
                return (
                    data.get("question", ""),
                    options,
                    str(data.get("correct_answer", "A")).strip().upper(),
                    data.get("explanation", "")
                )
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["503", "429", "unavailable", "overloaded", "quota", "exhausted", "not found"]):
                logging.warning(f"Model {model_name} failed for quiz gen: {e}. Trying next fallback model...")
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    else:
        raise Exception("All models failed to generate quiz question.")

async def extract_pdf_topics_and_summary(
    text_excerpt: str,
    filename: str,
    student: StudentModel
) -> Tuple[str, List[str], str]:
    """
    Analyzes document text excerpt and returns (title, [topics], summary).
    """
    lang = student.preferred_language or "English"
    prompt = (
        f"Analyze the following study document excerpt ({filename}) for a Grade {student.grade} student.\n"
        f"Document text:\n\"\"\"\n{text_excerpt[:15000]}\n\"\"\"\n\n"
        f"Tasks:\n"
        f"1. Generate a clean title for the document.\n"
        f"2. Identify 3 to 5 key educational topics covered in this document.\n"
        f"3. Write a concise, high-yield summary in {lang} highlighting key concepts.\n"
        f"Ensure all text is in {lang}."
    )
    
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PDFAnalysisResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                return parsed.title, parsed.topics, parsed.summary # type: ignore
            else:
                import json
                data = json.loads(response.text) # type: ignore
                return (
                    data.get("title", filename),
                    data.get("topics", ["Key Concepts", "Overview"]),
                    data.get("summary", "Document analyzed.")
                )
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["503", "429", "unavailable", "overloaded", "quota", "exhausted", "not found"]):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    return filename, ["Overview", "Key Concepts"], "Document uploaded and ready for study."

async def ask_gemini_with_pdf_context(
    question: str,
    pdf_text: str,
    pdf_title: str,
    student: StudentModel
) -> str:
    """
    Answers student questions grounded strictly in the uploaded PDF document text.
    """
    lang = student.preferred_language or "English"
    bounded_text = pdf_text[:25000] # Safe context bound
    prompt = (
        f"You are teaching a Grade {student.grade} student based on their uploaded document: '{pdf_title}'.\n\n"
        f"Document Content Excerpt:\n\"\"\"\n{bounded_text}\n\"\"\"\n\n"
        f"Student Question: {question}\n\n"
        f"Guidelines:\n"
        f"- Ground your answer strictly in the document content provided above.\n"
        f"- Explain clearly and encouragingly at a Grade {student.grade} level in {lang}.\n"
        f"- If the document does not mention the answer, state that clearly and provide general educational guidance.\n"
        f"- Use clean Markdown formatting with bullet points where helpful."
    )
    
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text or "I could not find a specific answer in the document."
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["503", "429", "unavailable", "overloaded", "quota", "exhausted", "not found"]):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    return "Error connecting to AI service."

async def generate_pdf_quiz_question(
    pdf_text: str,
    pdf_title: str,
    student: StudentModel
) -> tuple[str, dict[str, str], str, str]:
    """Generates a multiple-choice question based on the uploaded PDF document."""
    lang = student.preferred_language or "English"
    bounded_text = pdf_text[:20000]
    prompt = (
        f"Generate one multiple-choice question in {lang} based strictly on this study document:\n"
        f"Document Title: {pdf_title}\n"
        f"Grade Level: Grade {student.grade if student.grade is not None else '12'}\n\n"
        f"Document Content Excerpt:\n\"\"\"\n{bounded_text}\n\"\"\"\n\n"
        f"Requirements:\n"
        f"- Exactly 4 options (Option A, Option B, Option C, Option D)\n"
        f"- Exactly one correct answer grounded in the document (A, B, C, or D)\n"
        f"- Appropriate for grade {student.grade}\n"
        f"- Output all text in {lang}\n"
        f"- Provide a clear explanation referencing the document."
    )
    
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuizQuestionResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                if hasattr(parsed, "options") and isinstance(parsed.options, dict):
                    options = {str(k): str(v) for k, v in parsed.options.items()}
                else:
                    options = {
                        "A": str(getattr(parsed, "option_a", "Option A")),
                        "B": str(getattr(parsed, "option_b", "Option B")),
                        "C": str(getattr(parsed, "option_c", "Option C")),
                        "D": str(getattr(parsed, "option_d", "Option D")),
                    }
                q_text = str(getattr(parsed, "question", ""))
                c_ans = str(getattr(parsed, "correct_answer", "A")).strip().upper()
                expl = str(getattr(parsed, "explanation", ""))
                return q_text, options, c_ans, expl
            else:
                import json
                data = json.loads(response.text) # type: ignore
                if "options" in data and isinstance(data["options"], dict):
                    options = {str(k): str(v) for k, v in data["options"].items()}
                else:
                    options = {
                        "A": str(data.get("option_a", "Option A")),
                        "B": str(data.get("option_b", "Option B")),
                        "C": str(data.get("option_c", "Option C")),
                        "D": str(data.get("option_d", "Option D")),
                    }
                return (
                    data.get("question", ""),
                    options,
                    str(data.get("correct_answer", "A")).strip().upper(),
                    data.get("explanation", "")
                )
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["503", "429", "unavailable", "overloaded", "quota", "exhausted", "not found"]):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    raise Exception("Failed to generate PDF quiz question.")

async def grade_written_test(
    questions_text: str,
    student_answers: str,
    student: StudentModel,
    subject: str,
    topic: str
) -> Tuple[int, str, str, str, str, str, str]:
    """
    Grades student's written test answers and returns:
    (score_out_of_10, letter_grade, strengths, weaknesses, corrections, recommendations, formatted_feedback)
    """
    lang = student.preferred_language or "English"
    prompt = (
        f"You are an expert examiner grading a Grade {student.grade} student's written test.\n"
        f"Subject: {subject}\n"
        f"Topic: {topic}\n"
        f"Language: {lang}\n\n"
        f"Questions:\n{questions_text}\n\n"
        f"Student's Answers:\n{student_answers}\n\n"
        f"Please evaluate thoroughly and provide:\n"
        f"1. score: Integer score from 0 to 10\n"
        f"2. letter_grade: One of A+, A, B, C, D, F\n"
        f"3. strengths: Concepts the student got right\n"
        f"4. weaknesses: Misconceptions or incomplete points\n"
        f"5. corrections: Clear step-by-step correct answers for missed points\n"
        f"6. recommendations: Study tips for improvement\n"
        f"7. formatted_feedback: A clean, encouraging Markdown report in {lang} ready to show to the student."
    )
    
    models_to_try = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TestEvaluationResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                return (
                    parsed.score,
                    parsed.letter_grade,
                    parsed.strengths,
                    parsed.weaknesses,
                    parsed.corrections,
                    parsed.recommendations,
                    parsed.formatted_feedback
                )
            else:
                import json
                data = json.loads(response.text)
                return (
                    int(data.get("score", 8)),
                    str(data.get("letter_grade", "B")),
                    str(data.get("strengths", "Good effort")),
                    str(data.get("weaknesses", "None")),
                    str(data.get("corrections", "Review topic")),
                    str(data.get("recommendations", "Keep practicing")),
                    str(data.get("formatted_feedback", "Test completed."))
                )
        except Exception as e:
            err_str = str(e).lower()
            if any(term in err_str for term in ["503", "429", "unavailable", "overloaded", "quota", "exhausted", "not found"]):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    return 7, "B", "Good attempt", "", "", "Keep reviewing", "Test graded."
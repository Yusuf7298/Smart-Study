import logging
import asyncio
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple

from config import GEMINI_API_KEY, GEMINI_MODEL
from bot.database.models import StudentModel, LearningSessionModel
from bot.utils import clean_telegram_text

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={"api_version": "v1"},
)

BASE_SYSTEM_INSTRUCTION = """
You are an expert, patient, and natural human Study Tutor for students.

Your core guidelines:
1. Speak naturally like an experienced, warm human teacher. Never sound like an AI assistant.
2. NO ROBOTIC FILLER: Never start responses with boilerplate phrases like "Welcome to this lesson!", "Certainly!", "As an AI tutor...", "Here is what you need to know...", "Great question!", or "Take a deep breath!".
3. NO CLICHÉ SIGN-OFFS: Avoid repetitive closing fluff like "I hope this helps! Feel free to ask more!" or "I look forward to your response!". End naturally with a thought-provoking question or practice exercise when teaching.
4. Always teach at the student's exact stored profile level. Use simple everyday analogies for younger students; use precise technical rigor for high school and university students.
5. Language consistency: Always communicate naturally in the student's preferred language ({language}).
6. Maintain context: Build on the current learning context.
7. Socratic Method: Guide students step-by-step to discover solutions on their own instead of handing out answers.
8. TELEGRAM FORMATTING RULES:
   - NEVER use hashtag markdown headers (#, ##, ###, ####). Telegram does not render them and prints raw hashtags. Instead, use clean bold text (*Topic Name*).
   - NEVER use triple asterisks (***).
   - NEVER use LaTeX dollar signs ($...$ or $$...$$). Write formulas using clean unicode characters (e.g. x², r³, °, ±, ÷, ×, →, √, π).
   - Use clean unicode bullet points (•) for lists instead of asterisks (*).
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

class ExamTopicListResponse(BaseModel):
    topics: List[str] = Field(description="List of 2 to 6 specific topic names in logical sequence for the chosen chapter(s) based only on the attached text.")

class ExamMCQItem(BaseModel):
    number: int = Field(description="Question number (1 to 10).")
    question: str = Field(description="Question text based ONLY on the attached material.")
    option_a: str = Field(description="Option A text.")
    option_b: str = Field(description="Option B text.")
    option_c: str = Field(description="Option C text.")
    option_d: str = Field(description="Option D text.")
    correct_answer: str = Field(description="Correct option letter: A, B, C, or D.")
    explanation: str = Field(description="Brief explanation grounded in the attached material.")

class ExamTopicLessonResponse(BaseModel):
    short_notes: str = Field(description="Short, clear, easy-to-remember exam-focused notes explaining the topic using ONLY the attached file. No outside facts.")
    mcqs: List[ExamMCQItem] = Field(description="Exactly 10 multiple-choice questions with 4 options each based strictly on the topic.")

class ExamGradingResponse(BaseModel):
    score: int = Field(description="Score out of 10 (0 to 10).")
    detailed_results: str = Field(description="Itemized check for each question showing correct or incorrect with brief clear explanation.")
    corrections_and_reteach: str = Field(description="Clear explanation of mistakes and re-teaching of misunderstood concepts based only on the material.")

FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite"
]

RETRYABLE_ERROR_TERMS = [
    "503", "429", "404", "unavailable", "overloaded", "quota", 
    "exhausted", "not_found", "not found", "is no longer available", 
    "resource has been exhausted", "rate limit", "busy"
]

def _is_retryable_error(e: Exception) -> bool:
    err_str = str(e).lower()
    return any(term in err_str for term in RETRYABLE_ERROR_TERMS)

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
                    system_instruction=system_instruction, # type: ignore
                    response_mime_type="application/json",
                    response_schema=TutorResponse,
                )
            )
            response = await chat.send_message(question)
            
            parsed = response.parsed
            if parsed:
                raw_ans = getattr(parsed, "tutor_response", "") or ""
                return clean_telegram_text(raw_ans), parsed.extracted_grade, parsed.extracted_language # type: ignore
            else:
                import json
                data = json.loads(response.text) # type: ignore
                raw_ans = data.get("tutor_response", "") or ""
                return (
                    clean_telegram_text(raw_ans),
                    data.get("extracted_grade"),
                    data.get("extracted_language")
                )
        except Exception as e:
            if _is_retryable_error(e):
                logging.warning(f"Model {model_name} failed ({e}). Trying next fallback model...")
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
                if hasattr(parsed, "options") and isinstance(parsed.options, dict): # type: ignore
                    options = {str(k): str(v) for k, v in parsed.options.items()} # type: ignore
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
            if _is_retryable_error(e):
                logging.warning(f"Model {model_name} failed for quiz gen ({e}). Trying next fallback model...")
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
            if _is_retryable_error(e):
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
            if _is_retryable_error(e):
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
                    response_mime_type="application/json", # type: ignore
                    response_schema=QuizQuestionResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                if hasattr(parsed, "options") and isinstance(parsed.options, dict): # type: ignore
                    options = {str(k): str(v) for k, v in parsed.options.items()} # type: ignore
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
            if _is_retryable_error(e):
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
                    parsed.score, # type: ignore
                    parsed.letter_grade, # type: ignore
                    clean_telegram_text(str(parsed.strengths)), # type: ignore
                    clean_telegram_text(str(parsed.weaknesses)), # type: ignore
                    clean_telegram_text(str(parsed.corrections)), # type: ignore
                    clean_telegram_text(str(parsed.recommendations)), # type: ignore
                    clean_telegram_text(str(parsed.formatted_feedback)) # type: ignore
                )
            else:
                import json
                data = json.loads(response.text) # type: ignore
                return (
                    int(data.get("score", 8)),
                    str(data.get("letter_grade", "B")),
                    clean_telegram_text(str(data.get("strengths", "Good effort"))),
                    clean_telegram_text(str(data.get("weaknesses", "None"))),
                    clean_telegram_text(str(data.get("corrections", "Review topic"))),
                    clean_telegram_text(str(data.get("recommendations", "Keep practicing"))),
                    clean_telegram_text(str(data.get("formatted_feedback", "Test completed.")))
                )
        except Exception as e:
            if _is_retryable_error(e):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
                
    if last_error:
        raise last_error
    return 7, "B", "Good attempt", "", "", "Keep reviewing", "Test graded."

async def generate_exam_chapter_topics(
    material_text: str,
    chapter_name: str,
    lang: str = "English"
) -> List[str]:
    """
    Extracts the ordered sequence of educational topics for the specified chapter(s)
    using ONLY the attached document text.
    """
    bounded_text = material_text[:25000]
    prompt = (
        f"You are organizing a Final Exam Study session in {lang} for '{chapter_name}'.\n"
        f"Document Content Excerpt:\n\"\"\"\n{bounded_text}\n\"\"\"\n\n"
        f"STRICT SOURCE RULE:\n"
        f"- The attached text is the ONLY source. Do NOT use outside knowledge.\n"
        f"- Extract 2 to 6 specific, ordered topic titles covered in '{chapter_name}'.\n"
        f"- If the file does not have explicit chapter markers, divide the relevant content into 2 to 5 logical study topics.\n"
        f"- Output topic names in {lang}."
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
                    response_schema=ExamTopicListResponse,
                )
            )
            parsed = response.parsed
            if parsed and parsed.topics:
                return [clean_telegram_text(t) for t in parsed.topics if t.strip()]
            else:
                import json
                data = json.loads(response.text) # type: ignore
                topics = data.get("topics", [])
                if topics:
                    return [clean_telegram_text(t) for t in topics if t.strip()]
        except Exception as e:
            if _is_retryable_error(e):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
    if last_error:
        logging.warning(f"Error extracting chapter topics: {last_error}")
    return [f"{chapter_name} - Core Concepts", f"{chapter_name} - Advanced Applications"]

async def generate_exam_topic_lesson(
    material_text: str,
    chapter_name: str,
    topic_name: str,
    lang: str = "English"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generates Step 1 (Short Notes) and Step 2 (10 MCQs) based ONLY on the attached file.
    Returns (formatted_lesson_text, mcq_list).
    """
    bounded_text = material_text[:25000]
    prompt = (
        f"You are conducting a Final Exam Study session in {lang}.\n"
        f"Chapter: {chapter_name}\n"
        f"Current Topic: {topic_name}\n\n"
        f"Document Content Excerpt:\n\"\"\"\n{bounded_text}\n\"\"\"\n\n"
        f"STRICT RULES:\n"
        f"1. ONLY use information directly contained in the attached document.\n"
        f"   Do NOT use outside knowledge, websites, or invent unmentioned concepts.\n"
        f"   If not in the material, do not include it.\n"
        f"2. STEP 1 — Short Notes:\n"
        f"   - Explain the topic using only information from the attached file.\n"
        f"   - Create short, clear, easy-to-remember notes.\n"
        f"   - Focus on the important concepts, definitions, facts, and points needed for the final exam.\n"
        f"   - Do not make the explanation unnecessarily long.\n"
        f"3. STEP 2 — 10 Multiple-Choice Questions:\n"
        f"   - Generate EXACTLY 10 MCQs based only on this topic from the file.\n"
        f"   - 4 options each: A, B, C, D.\n"
        f"   - Provide the correct answer key and brief explanation internally.\n"
        f"4. Output all text in {lang}."
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
                    response_schema=ExamTopicLessonResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                short_notes = clean_telegram_text(parsed.short_notes)
                mcq_list = []
                questions_rendered = []
                for idx, q in enumerate(parsed.mcqs, 1):
                    q_data = {
                        "number": idx,
                        "question": clean_telegram_text(q.question),
                        "option_a": clean_telegram_text(q.option_a),
                        "option_b": clean_telegram_text(q.option_b),
                        "option_c": clean_telegram_text(q.option_c),
                        "option_d": clean_telegram_text(q.option_d),
                        "correct_answer": str(q.correct_answer).strip().upper(),
                        "explanation": clean_telegram_text(q.explanation)
                    }
                    mcq_list.append(q_data)
                    q_text = (
                        f"{idx}. {q_data['question']}\n"
                        f"A) {q_data['option_a']}\n"
                        f"B) {q_data['option_b']}\n"
                        f"C) {q_data['option_c']}\n"
                        f"D) {q_data['option_d']}"
                    )
                    questions_rendered.append(q_text)
                    
                formatted_lesson = (
                    f"📖 Step 1 — Short Notes: {topic_name}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{short_notes}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"❓ Step 2 — 10 Final Exam Questions\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    + "\n\n".join(questions_rendered)
                    + "\n\n━━━━━━━━━━━━━━━━━━━━\n"
                    f"✍️ Submit your 10 answers in a reply message (e.g. 1.A 2.B 3.C... or A B C D A B C D A B):"
                )
                return formatted_lesson, mcq_list
        except Exception as e:
            if _is_retryable_error(e):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
    if last_error:
        raise last_error
    raise Exception("Failed to generate exam topic lesson.")

async def grade_exam_topic_answers(
    material_text: str,
    topic_name: str,
    mcqs: List[Dict[str, Any]],
    student_answers: str,
    lang: str = "English"
) -> Tuple[int, str, str]:
    """
    Step 3: Checks the student's submitted answers against the 10 MCQs.
    Returns (score_out_of_10, detailed_results, corrections_and_reteach).
    """
    bounded_text = material_text[:25000]
    import json
    mcqs_summary = json.dumps(mcqs, ensure_ascii=False)
    
    prompt = (
        f"You are an examiner evaluating a student's 10 MCQ answers in {lang}.\n"
        f"Topic: {topic_name}\n"
        f"Questions & Official Answer Key:\n{mcqs_summary}\n\n"
        f"Student's Submitted Answers:\n{student_answers}\n\n"
        f"Document Content Context:\n\"\"\"\n{bounded_text}\n\"\"\"\n\n"
        f"STRICT RULES:\n"
        f"1. Grade the student's answers (0 to 10).\n"
        f"2. detailed_results: List each of the 10 questions. Show if the student was Correct (✅) or Incorrect (❌), the correct option, and a brief 1-line reason strictly from the attached material.\n"
        f"3. corrections_and_reteach: Explain mistakes clearly and briefly re-teach any misunderstood concepts using ONLY the attached file.\n"
        f"4. If something is missing from the file, state: 'This information is not available in the attached study material.'\n"
        f"5. Keep the tone encouraging and clear. Output in {lang}."
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
                    response_schema=ExamGradingResponse,
                )
            )
            parsed = response.parsed
            if parsed:
                return (
                    parsed.score,
                    clean_telegram_text(parsed.detailed_results),
                    clean_telegram_text(parsed.corrections_and_reteach)
                )
            else:
                data = json.loads(response.text) # type: ignore
                return (
                    int(data.get("score", 7)),
                    clean_telegram_text(str(data.get("detailed_results", ""))),
                    clean_telegram_text(str(data.get("corrections_and_reteach", "")))
                )
        except Exception as e:
            if _is_retryable_error(e):
                last_error = e
                await asyncio.sleep(0.5)
                continue
            else:
                raise e
    if last_error:
        raise last_error
    return 7, "Answers evaluated.", "Keep studying the material."
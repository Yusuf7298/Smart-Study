import logging
import io
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from google.genai import types

from config import SUBJECTS
from bot.services import student_service, learning_service, conversation_service, quiz_service, pdf_service
from bot.services.gemini import ask_gemini_with_profile
from bot.keyboards.study_input import get_study_input_keyboard, get_study_actions_keyboard
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit
from bot.handlers.pdf import PDFStates

router = Router()

class StudyStates(StatesGroup):
    waiting_for_course_name = State()
    waiting_for_input_choice = State()
    waiting_for_text = State()
    waiting_for_file = State()

@router.message(Command("study"), StateFilter(None))
@router.message(F.text.in_(["📚 Study", "📚 አጥና", "📚 Qo'annoo", "📚 Qo'adhu"]), StateFilter(None))
async def start_study_mode(message: Message, state: FSMContext):
    """Triggers Study Mode and asks the student to write the course/subject they want to study."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await state.set_state(StudyStates.waiting_for_course_name)
    await safe_reply(
        message,
        t("study_ask_course", lang)
    )

@router.callback_query(F.data == "menu_study", StateFilter(None))
async def menu_study_callback(callback: CallbackQuery, state: FSMContext):
    """Main menu trigger for Study Mode."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(StudyStates.waiting_for_course_name)
    await safe_reply(
        callback,
        t("study_ask_course", lang)
    )

@router.callback_query(F.data.in_(["study_cancel", "study_back_subjects"]), StateFilter(None))
async def legacy_study_cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Safely handles cancellation or back navigation from any legacy study buttons."""
    try:
        await callback.answer()
    except Exception:
        pass
    await state.clear()
    await safe_edit(callback.message, "❌ Study mode cancelled. Use /study or the menu to start anytime.")

@router.message(StudyStates.waiting_for_course_name)
async def process_course_name_input(message: Message, state: FSMContext):
    """Receives the student's entered course/subject and presents input options."""
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    course_name = message.text.strip() if message.text else "General Study"
    
    await state.set_state(StudyStates.waiting_for_input_choice)
    await state.update_data(subject=course_name, topic=course_name)
    
    text = t("study_input_choice", lang, subject=course_name, topic=course_name)
    await safe_reply(
        message,
        text,
        reply_markup=get_study_input_keyboard()
    )

@router.callback_query(F.data == "study_input_text", StudyStates.waiting_for_input_choice)
async def study_input_text_callback(callback: CallbackQuery, state: FSMContext):
    """Asks the student to input their study query/topic description."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await state.set_state(StudyStates.waiting_for_text)
    await safe_edit(
        callback.message,
        t("study_ask_text", lang)
    )

@router.callback_query(F.data == "study_input_file", StudyStates.waiting_for_input_choice)
async def study_input_file_callback(callback: CallbackQuery, state: FSMContext):
    """Asks the student to send their study file/image."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await state.set_state(StudyStates.waiting_for_file)
    await safe_edit(
        callback.message,
        t("study_ask_file", lang)
    )

@router.message(StudyStates.waiting_for_text)
async def process_study_text_input(message: Message, state: FSMContext):
    """Starts the learning session based on student text description."""
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    data = await state.get_data()
    subject = data.get("subject", "General Study")
    topic = data.get("topic", subject)
    await state.clear()
    
    thinking_msg = await message.answer(t("study_intro_thinking", lang))
    
    try:
        if not student:
            student = await student_service.register_student(
                telegram_id, message.from_user.first_name, message.from_user.username
            )
            
        session = await learning_service.start_session(telegram_id, subject, topic)
        
        prompt = (
            f"Start teaching me in {lang} based on the following student requirements/topic description:\n"
            f"{message.text}"
        )
        intro_text, _, _ = await ask_gemini_with_profile(
            question=prompt,
            history=[],
            student=student,
            session=session
        )
        
        await conversation_service.add_message(telegram_id, "user", f"[User Requirements]: {message.text}")
        await conversation_service.add_message(telegram_id, "assistant", intro_text)
        
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await safe_reply(
            message,
            intro_text,
            reply_markup=get_study_actions_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error starting text session: {e}", exc_info=True)
        await safe_edit(thinking_msg, t("ai_error", lang))

@router.message(StudyStates.waiting_for_file)
async def process_study_file_input(message: Message, state: FSMContext):
    """Downloads study material (photo or document) and queries Gemini with it."""
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    data = await state.get_data()
    subject = data.get("subject", "General Study")
    topic = data.get("topic", subject)
    await state.clear()
    
    thinking_msg = await message.answer(t("study_intro_thinking", lang))
    
    try:
        part = None
        desc = message.caption or message.text or "Teach me based on this study material."
        
        # 1. Handle PDF Document
        doc_filename = str(getattr(message.document, "file_name", "")) if message.document else ""
        if message.document and doc_filename.lower().endswith(".pdf"):
            doc = message.document
            file = await message.bot.get_file(doc.file_id)
            file_bytes_io = io.BytesIO()
            await message.bot.download_file(file.file_path, file_bytes_io)
            pdf_bytes = file_bytes_io.getvalue()
            
            material = await pdf_service.process_and_save_pdf(
                telegram_id=telegram_id,
                pdf_bytes=pdf_bytes,
                original_filename=doc.file_name or "document.pdf",
                file_id=doc.file_id,
                student=student
            )
            
            await state.set_state(PDFStates.waiting_for_chapter)
            await state.update_data(
                material_id=material.id,
                filename=material.title or material.filename,
                extracted_text=material.extracted_text or ""
            )
            try:
                await thinking_msg.delete()
            except Exception:
                pass
                
            prompt_text = (
                f"📚 *Final Exam Study Mode: {material.title or material.filename}*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Which chapter(s) do you want to study?\n\n"
                f"💡 _(e.g., Chapter 1, Chapters 2 and 3, or All)_"
            )
            await safe_reply(message, prompt_text)
            return

        # 2. Handle Photo
        elif message.photo:
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            file_bytes = io.BytesIO()
            await message.bot.download_file(file.file_path, file_bytes)
            part = types.Part.from_bytes(
                data=file_bytes.getvalue(),
                mime_type="image/jpeg"
            )
            
        # 3. Handle Other Document
        elif message.document:
            doc = message.document
            file = await message.bot.get_file(doc.file_id)
            file_bytes = io.BytesIO()
            await message.bot.download_file(file.file_path, file_bytes)
            part = types.Part.from_bytes(
                data=file_bytes.getvalue(),
                mime_type=doc.mime_type or "application/octet-stream"
            )
            
        if not student:
            student = await student_service.register_student(
                telegram_id, message.from_user.first_name, message.from_user.username
            )
            
        session = await learning_service.start_session(telegram_id, subject, topic)
        
        # Build prompt
        prompt_parts = []
        if part:
            prompt_parts.append(part)
        prompt_parts.append(
            f"Here is the study material context/request from the student:\n"
            f"{desc}\n\n"
            f"Please introduce the lesson in {lang} and start teaching me step-by-step."
        )
        
        intro_text, _, _ = await ask_gemini_with_profile(
            question=prompt_parts,
            history=[],
            student=student,
            session=session
        )
        
        await conversation_service.add_message(telegram_id, "user", f"[Uploaded Material Context]: {desc}")
        await conversation_service.add_message(telegram_id, "assistant", intro_text)
        
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await safe_reply(
            message,
            intro_text,
            reply_markup=get_study_actions_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error starting file study session: {e}", exc_info=True)
        await safe_edit(thinking_msg, t("ai_error", lang))

@router.message(Command("current"), StateFilter(None))
async def show_current_session(message: Message):
    """Displays the student's active study session details."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    student = await student_service.get_student(telegram_id)
    if not student:
        first_name = message.from_user.first_name if message.from_user else None
        username = message.from_user.username if message.from_user else None
        student = await student_service.register_student(telegram_id, first_name, username)

    lang = student.preferred_language or "English"
    session = await learning_service.get_active_session(telegram_id)
    if not session:
        await safe_reply(message, t("no_active_session", lang))
        return

    grade_str = f"{student.grade}" if student.grade is not None else "Not Set"
    
    # Fetch subject emoji
    sub_info = SUBJECTS.get(session.subject, {})
    sub_emoji = sub_info.get("emoji", "📚")
    
    # Map stage values to pretty strings
    stage_mapping = {
        "INTRODUCTION": "📖 Introduction",
        "LEARNING": "🧠 Learning",
        "PRACTICE": "✍️ Practice",
        "QUIZ": "❓ Quiz",
        "REVIEW": "📝 Review",
        "MASTERED": "🏆 Mastered"
    }
    pretty_stage = stage_mapping.get(session.stage, session.stage)
    
    # Format date (check if today)
    started_date = session.created_at
    now_date = datetime.now(started_date.tzinfo) if started_date.tzinfo else datetime.now()
    if started_date.date() == now_date.date():
        started_str = "Today"
    else:
        started_str = started_date.strftime("%Y-%m-%d")
        
    active_quiz = await quiz_service.get_active_quiz(telegram_id)
    if active_quiz:
        answered_count = max(0, active_quiz.current_question - 1)
        text = t(
            "current_session_quiz_active",
            lang,
            grade=grade_str,
            emoji=sub_emoji,
            subject=session.subject,
            topic=session.topic,
            stage=pretty_stage,
            q_num=active_quiz.current_question,
            q_total=active_quiz.total_questions,
            correct=active_quiz.correct_answers,
            answered=answered_count
        )
    else:
        text = t(
            "current_session_title",
            lang,
            grade=grade_str,
            emoji=sub_emoji,
            subject=session.subject,
            topic=session.topic,
            stage=pretty_stage,
            started=started_str
        )
    await safe_reply(message, text)

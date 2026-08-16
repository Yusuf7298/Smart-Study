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
from bot.services import student_service, learning_service, conversation_service, quiz_service
from bot.services.gemini import ask_gemini_with_profile
from bot.keyboards.study import get_subjects_keyboard, get_topics_keyboard
from bot.keyboards.study_input import get_study_input_keyboard, get_study_actions_keyboard
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit

router = Router()

class StudyStates(StatesGroup):
    waiting_for_input_choice = State()
    waiting_for_text = State()
    waiting_for_file = State()

@router.message(Command("study"), StateFilter(None))
@router.message(F.text.in_(["📚 Study", "📚 አጥና", "📚 Qo'annoo", "📚 Qo'adhu"]), StateFilter(None))
async def start_study_mode(message: Message):
    """Triggers Study Mode and displays the subject selection keyboard."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await safe_reply(
        message,
        t("study_mode_title", lang),
        reply_markup=get_subjects_keyboard()
    )

@router.callback_query(F.data == "menu_study", StateFilter(None))
async def menu_study_callback(callback: CallbackQuery):
    """Main menu trigger for Study Mode."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        callback,
        t("study_mode_title", lang),
        reply_markup=get_subjects_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("study_sub_"), StateFilter(None))
async def select_subject_callback(callback: CallbackQuery):
    """Processes subject selection and displays topic selection keyboard."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    subject = callback.data.split("_sub_")[1]
    info = SUBJECTS.get(subject, {})
    emoji = info.get("emoji", "📚")
    
    text = t("study_choose_topic", lang, emoji=emoji, subject=subject)
    await safe_edit(
        callback.message,
        text,
        reply_markup=get_topics_keyboard(subject)
    )
    await callback.answer()

@router.callback_query(F.data == "study_back_subjects", StateFilter(None))
async def back_to_subjects_callback(callback: CallbackQuery):
    """Returns to the subject selection keyboard."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await safe_edit(
        callback.message,
        t("study_mode_title", lang),
        reply_markup=get_subjects_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "study_cancel", StateFilter(None))
async def cancel_study_callback(callback: CallbackQuery):
    """Cancels the study selection menu."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_edit(callback.message, t("btn_cancel", lang) + ": Study mode cancelled.")
    await callback.answer()

@router.callback_query(F.data.startswith("study_topic_"), StateFilter(None))
async def select_topic_callback(callback: CallbackQuery, state: FSMContext):
    """Asks the user how they want to provide the study materials/topic."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    subject_topic = callback.data.split("_topic_")[1]
    subject, topic = subject_topic.split("|", 1)
    
    await state.set_state(StudyStates.waiting_for_input_choice)
    await state.update_data(subject=subject, topic=topic)
    
    text = t("study_input_choice", lang, subject=subject, topic=topic)
    await safe_edit(
        callback.message,
        text,
        reply_markup=get_study_input_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "study_input_text", StudyStates.waiting_for_input_choice)
async def study_input_text_callback(callback: CallbackQuery, state: FSMContext):
    """Asks the student to input their study query/topic description."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await state.set_state(StudyStates.waiting_for_text)
    await safe_edit(
        callback.message,
        t("study_ask_text", lang)
    )
    await callback.answer()

@router.callback_query(F.data == "study_input_file", StudyStates.waiting_for_input_choice)
async def study_input_file_callback(callback: CallbackQuery, state: FSMContext):
    """Asks the student to send their study file/image."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await state.set_state(StudyStates.waiting_for_file)
    await safe_edit(
        callback.message,
        t("study_ask_file", lang)
    )
    await callback.answer()

@router.message(StudyStates.waiting_for_text)
async def process_study_text_input(message: Message, state: FSMContext):
    """Starts the learning session based on student text description."""
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    data = await state.get_data()
    subject = data.get("subject")
    topic = data.get("topic")
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
    subject = data.get("subject")
    topic = data.get("topic")
    await state.clear()
    
    thinking_msg = await message.answer(t("study_intro_thinking", lang))
    
    try:
        part = None
        desc = message.caption or message.text or "Teach me based on this study material."
        
        # 1. Handle Photo
        if message.photo:
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            file_bytes = io.BytesIO()
            await message.bot.download_file(file.file_path, file_bytes)
            part = types.Part.from_bytes(
                data=file_bytes.getvalue(),
                mime_type="image/jpeg"
            )
            
        # 2. Handle Document
        elif message.document:
            doc = message.document
            file = await message.bot.get_file(doc.file_id)
            file_bytes = io.BytesIO()
            await message.bot.download_file(file.file_path, file_bytes)
            part = types.Part.from_bytes(
                data=file_bytes.getvalue(),
                mime_type=doc.mime_type or "application/pdf"
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

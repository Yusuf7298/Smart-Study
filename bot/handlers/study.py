import os
import io
import logging
from datetime import datetime
from typing import List, Optional

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from google.genai import types

import config
from bot.services import student_service, learning_service, conversation_service, quiz_service, pdf_service
from bot.services.gemini import ask_gemini_with_profile
from bot.keyboards.study_input import get_study_input_keyboard, get_study_actions_keyboard, get_study_methods_keyboard
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit
from bot.handlers.pdf import PDFStates

router = Router()

class StudyStates(StatesGroup):
    waiting_for_course_name = State()
    waiting_for_subject_choice = State()
    waiting_for_chapter_choice = State()
    waiting_for_topic_choice = State()
    waiting_for_input_choice = State()
    waiting_for_text = State()
    waiting_for_file = State()

@router.message(StudyStates.waiting_for_course_name)
async def process_course_name_input(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    course_name = message.text.strip() if message.text else "General Study"
    if student and student.selected_courses and not student_service.is_course_registered(student, course_name):
        enrolled_str = ", ".join(student.selected_courses)
        await safe_reply(
            message,
            f"⛔ Security Guard: Unauthorized Course!\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"You are only enrolled in:\n📚 {enrolled_str}\n\n"
            f"You cannot start a study session for {course_name}. Please choose from your registered courses below:",
            reply_markup=get_registered_subjects_keyboard(student.selected_courses, lang)
        )
        return

    await state.update_data(subject=course_name, topic=course_name)
    await state.set_state(StudyStates.waiting_for_input_choice)
    from bot.keyboards.study_input import get_study_input_keyboard
    await safe_reply(
        message,
        t("study_input_choice", lang, subject=course_name, topic=course_name),
        reply_markup=get_study_input_keyboard()
    )

def get_registered_subjects_keyboard(registered_subjects: List[str], lang: str = "English") -> InlineKeyboardMarkup:
    from bot.services.i18n import get_subject_name_in_lang
    buttons = []
    subjects_to_show = registered_subjects if registered_subjects else config.get_curriculum_subjects()
    
    row = []
    for subj in subjects_to_show:
        emoji = config.SUBJECTS.get(subj, {}).get("emoji", "📚")
        loc_name = get_subject_name_in_lang(subj, lang)
        row.append(InlineKeyboardButton(text=f"{emoji} {loc_name}", callback_data=f"study_pick_subj_{subj}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="study_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_chapters_keyboard(subject: str, lang: str = "English") -> InlineKeyboardMarkup:
    chapters = [
        ("1️⃣ Chapter 1: Core Fundamentals", "1"),
        ("2️⃣ Chapter 2: Key Principles & Theory", "2"),
        ("3️⃣ Chapter 3: Advanced Applications", "3"),
        ("4️⃣ Chapter 4: Practice & Exam Review", "4"),
    ]
    keyboard = []
    for title, num in chapters:
        keyboard.append([InlineKeyboardButton(text=title, callback_data=f"study_pick_chap_{subject}_{num}")])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Back", callback_data="study_back_subjects"),
        InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="study_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_topics_keyboard(subject: str, chapter_num: str, lang: str = "English") -> InlineKeyboardMarkup:
    sub_data = config.SUBJECTS.get(subject, {})
    all_topics = sub_data.get("topics", ["Overview & Key Concepts", "Definitions & Examples", "Practical Problem Solving", "Chapter Summary & Quiz"])
    
    keyboard = []
    for idx, top in enumerate(all_topics[:4], 1):
        keyboard.append([InlineKeyboardButton(text=f"📌 {top}", callback_data=f"study_pick_top_{subject}_{chapter_num}_{idx}")])
        
    keyboard.append([
        InlineKeyboardButton(text="✍️ Custom Topic / Question", callback_data=f"study_custom_topic_{subject}_{chapter_num}"),
        InlineKeyboardButton(text="📎 Upload PDF", callback_data=f"study_upload_pdf_{subject}_{chapter_num}")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Back to Chapters", callback_data=f"study_pick_subj_{subject}"),
        InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="study_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("study"))
@router.message(F.text.in_(["📚 Study", "📚 አጥና", "📚 Qo'annoo", "📚 Qo'adhu"]))
async def start_study_mode(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    registered_courses = student.selected_courses if student else []

    await state.set_state(StudyStates.waiting_for_course_name)
    await safe_reply(
        message,
        t("study_ask_course", lang),
        reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
    )

@router.callback_query(F.data == "menu_study")
async def menu_study_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    registered_courses = student.selected_courses if student else []
    
    await state.set_state(StudyStates.waiting_for_course_name)
    await safe_reply(
        callback,
        t("study_ask_course", lang),
        reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
    )

@router.callback_query(F.data == "study_back_subjects")
async def study_back_subjects_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    registered_courses = student.selected_courses if student else []
    
    await state.set_state(StudyStates.waiting_for_subject_choice)
    await safe_edit(
        callback.message,
        t("study_ask_course", lang),
        reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
    )

@router.callback_query(F.data.startswith("study_pick_subj_"))
async def study_pick_subject_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    subject = callback.data.split("study_pick_subj_")[1]
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    if not student_service.is_course_registered(student, subject):
        enrolled_str = "\n".join([f"• {c}" for c in (student.selected_courses if student else [])])
        error_msg = t("unregistered_course_error", lang, course=subject, courses=enrolled_str)
        await safe_edit(callback.message, error_msg)
        return
        
    await state.update_data(subject=subject)
    await state.set_state(StudyStates.waiting_for_input_choice)
    
    emoji = config.SUBJECTS.get(subject, {}).get("emoji", "📚")
    prompt_text = (
        f"📚 {emoji} {subject} Study Mode\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"How would you like to study {subject}?\n\n"
        f"Please choose your preferred study method:"
    )
    
    await safe_edit(
        callback.message,
        prompt_text,
        reply_markup=get_study_methods_keyboard(subject, lang)
    )

@router.callback_query(F.data.startswith("study_method_topic_"))
async def study_method_topic_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    subject = callback.data.split("study_method_topic_")[1]
    emoji = config.SUBJECTS.get(subject, {}).get("emoji", "📚")
    await state.update_data(subject=subject)
    await state.set_state(StudyStates.waiting_for_text)
    
    prompt_text = (
        f"✍️ {emoji} {subject} — Short Description & Topic Study\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Please enter the specific topic, concept, or chapter title you want to study:\n\n"
        f"💡 (e.g., Photosynthesis & Light Reactions, Newton's Laws of Motion, Quadratic Equations)"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"study_pick_subj_{subject}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")]
    ])
    await safe_edit(callback.message, prompt_text, reply_markup=kb)

@router.callback_query(F.data.startswith("study_method_photo_"))
async def study_method_photo_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    subject = callback.data.split("study_method_photo_")[1]
    emoji = config.SUBJECTS.get(subject, {}).get("emoji", "📚")
    await state.update_data(subject=subject, input_mode="photo")
    await state.set_state(StudyStates.waiting_for_file)
    
    prompt_text = (
        f"📸 {emoji} {subject} — Photo / Screenshot Upload\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Please send a clear photo or screenshot of your textbook page, homework question, or notes for {subject}:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"study_pick_subj_{subject}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")]
    ])
    await safe_edit(callback.message, prompt_text, reply_markup=kb)

@router.callback_query(F.data.startswith("study_method_file_"))
async def study_method_file_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    subject = callback.data.split("study_method_file_")[1]
    emoji = config.SUBJECTS.get(subject, {}).get("emoji", "📚")
    await state.update_data(subject=subject, input_mode="file")
    await state.set_state(StudyStates.waiting_for_file)
    
    prompt_text = (
        f"📄 {emoji} {subject} — File / PDF Upload\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Please upload your PDF textbook, module, or study document for {subject}:\n\n"
        f"Once uploaded, you will enter the chapter(s) to study together!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data=f"study_pick_subj_{subject}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")]
    ])
    await safe_edit(callback.message, prompt_text, reply_markup=kb)

@router.callback_query(F.data.startswith("study_pick_chap_"))
async def study_pick_chapter_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split("study_pick_chap_")[1].split("_")
    subject = parts[0]
    chapter_num = parts[1]
    
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.update_data(subject=subject, chapter_num=chapter_num)
    await state.set_state(StudyStates.waiting_for_topic_choice)
    
    emoji = config.SUBJECTS.get(subject, {}).get("emoji", "📚")
    prompt_text = f"📌 *{emoji} {subject} — Chapter {chapter_num}*\n━━━━━━━━━━━━━━━━━━━━\nChoose a topic to study:"
    
    await safe_edit(
        callback.message,
        prompt_text,
        reply_markup=get_topics_keyboard(subject, chapter_num, lang)
    )

@router.callback_query(F.data.startswith("study_pick_top_"))
async def study_pick_topic_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split("study_pick_top_")[1].split("_")
    subject = parts[0]
    chapter_num = parts[1]
    topic_idx = int(parts[2])
    
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    sub_data = config.SUBJECTS.get(subject, {})
    topics_list = sub_data.get("topics", ["Overview & Core Concepts"])
    topic_title = topics_list[min(topic_idx - 1, len(topics_list) - 1)]
    full_topic = f"Chapter {chapter_num}: {topic_title}"
    
    thinking_msg = await callback.message.answer(t("study_intro_thinking", lang))
    
    try:
        session = await learning_service.start_session(telegram_id, subject, full_topic)
        
        prompt = (
            f"Let's study together starting from {full_topic} in {subject}.\n"
            f"Please introduce this topic clearly for a Grade {student.grade if student else '10'} student in {lang}.\n"
            f"Provide a clear, easy-to-understand explanation of the core principles, definitions, and high-yield exam takeaways."
        )
        
        intro_text, _, _ = await ask_gemini_with_profile(
            question=prompt,
            history=[],
            student=student,
            session=session
        )
        
        await conversation_service.add_message(telegram_id, "user", f"I want to study {subject} - {full_topic}")
        await conversation_service.add_message(telegram_id, "assistant", intro_text)
        await state.clear()
        
        try:
            await thinking_msg.delete()
        except Exception:
            pass
            
        await safe_reply(
            callback.message,
            intro_text,
            reply_markup=get_study_actions_keyboard()
        )
    except Exception as e:
        logging.error(f"Error starting topic study: {e}", exc_info=True)
        await safe_edit(thinking_msg, t("ai_error", lang))

@router.callback_query(F.data.startswith("study_custom_topic_"))
async def study_custom_topic_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split("study_custom_topic_")[1].split("_")
    subject = parts[0]
    chapter_num = parts[1]
    
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(StudyStates.waiting_for_text)
    await state.update_data(subject=subject, chapter_num=chapter_num, topic=f"Chapter {chapter_num}")
    
    await safe_edit(
        callback.message,
        f"✍️ Custom Topic — {subject} (Chapter {chapter_num})\n━━━━━━━━━━━━━━━━━━━━\nPlease enter the specific topic or question you want to study:"
    )

@router.callback_query(F.data.startswith("study_upload_pdf_"))
async def study_upload_pdf_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split("study_upload_pdf_")[1].split("_")
    subject = parts[0]
    chapter_num = parts[1]
    
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(StudyStates.waiting_for_file)
    await state.update_data(subject=subject, chapter_num=chapter_num, topic=f"Chapter {chapter_num}")
    
    await safe_edit(
        callback.message,
        f"📎 Upload PDF / Notes — {subject} (Chapter {chapter_num})\n━━━━━━━━━━━━━━━━━━━━\nPlease send your PDF document or photo notes for Chapter {chapter_num}:"
    )

@router.message(StudyStates.waiting_for_text)
async def process_study_text_input(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    data = await state.get_data()
    subject = data.get("subject", "General Study")
    chapter_num = data.get("chapter_num")
    user_desc = message.text.strip() if message.text else "Overview & Key Concepts"
    topic_name = data.get("topic") or (f"Chapter {chapter_num}: {user_desc[:50]}" if chapter_num else user_desc)
    
    thinking_msg = await message.answer(t("study_intro_thinking", lang))
    
    try:
        session = await learning_service.start_session(telegram_id, subject, topic_name)
        prompt = (
            f"Let's study together starting from {topic_name} in {subject}.\n"
            f"Please introduce this lesson clearly and warmly for a Grade {student.grade if student else '10'} student in {lang}.\n"
            f"Provide a structured, step-by-step explanation of the core principles, high-yield definitions, and essential exam takeaways. "
            f"End with a thought-provoking check question."
        )
        
        intro_text, _, _ = await ask_gemini_with_profile(
            question=prompt,
            history=[],
            student=student,
            session=session
        )
        
        await conversation_service.add_message(telegram_id, "user", f"I want to study {subject} - {topic_name}")
        await conversation_service.add_message(telegram_id, "assistant", intro_text)
        await state.clear()
        
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
        logging.error(f"Error processing custom text study: {e}", exc_info=True)
        await safe_edit(thinking_msg, t("ai_error", lang))

@router.message(StudyStates.waiting_for_file, F.document | F.photo)
async def process_study_file_input(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    data = await state.get_data()
    subject = data.get("subject", "General Study")
    chapter_num = data.get("chapter_num", "1")

    thinking_msg = await message.answer(t("study_intro_thinking", lang))
    
    try:
        doc = getattr(message, "document", None)
        mime = getattr(doc, "mime_type", None) if doc else None
        fname = getattr(doc, "file_name", None) if doc else None
        is_pdf_doc = bool(doc and ((isinstance(mime, str) and mime == "application/pdf") or (isinstance(fname, str) and fname.lower().endswith(".pdf"))))

        if is_pdf_doc:
            file = await message.bot.get_file(doc.file_id)
            file_bytes = io.BytesIO()
            await message.bot.download_file(file.file_path, file_bytes)
            
            material = await pdf_service.process_and_save_pdf(
                telegram_id=telegram_id,
                pdf_bytes=file_bytes.getvalue(),
                original_filename=doc.file_name or "document.pdf",
                file_id=doc.file_id,
                student=student
            )
            
            await state.set_state(PDFStates.waiting_for_chapter)
            await state.update_data(
                material_id=material.id,
                filename=material.title or material.filename,
                extracted_text=material.extracted_text or "",
                subject=subject
            )
            try:
                await thinking_msg.delete()
            except Exception:
                pass
                
            prompt_text = (
                f"📚 Final Exam Study Mode: {material.title or material.filename}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Which chapter(s) do you want to study from this document?\n\n"
                f"💡 (e.g., Chapter 1, Chapters 2 and 3, or All)"
            )
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
            ])
            await safe_reply(message, prompt_text, reply_markup=kb)
            return

        # Handle Photo / image notes
        part = None
        if message.photo:
            try:
                photo = message.photo[-1]
                file = await message.bot.get_file(photo.file_id)
                file_bytes = io.BytesIO()
                if file and getattr(file, "file_path", None):
                    await message.bot.download_file(file.file_path, file_bytes)
                part = types.Part.from_bytes(data=file_bytes.getvalue(), mime_type="image/jpeg")
            except Exception as e:
                logging.warning(f"Photo note download fallback: {e}")
                part = types.Part.from_bytes(data=b"", mime_type="image/jpeg")

        topic_name = data.get("topic") or f"Chapter {chapter_num} Notes"
        session = await learning_service.start_session(telegram_id, subject, topic_name)
        prompt_parts = []
        if part:
            prompt_parts.append(part)
        prompt_parts.append(f"Please explain the attached study material for {subject} ({topic_name}) in {lang} step-by-step.")
        
        intro_text, _, _ = await ask_gemini_with_profile(
            question=prompt_parts,
            history=[],
            student=student,
            session=session
        )
        
        await conversation_service.add_message(telegram_id, "user", f"[Uploaded Material]: {subject} {topic_name}")
        await conversation_service.add_message(telegram_id, "assistant", intro_text)
        await state.clear()
        
        try:
            await thinking_msg.delete()
        except Exception:
            pass
            
        await safe_reply(message, intro_text, reply_markup=get_study_actions_keyboard())
    except Exception as e:
        logging.error(f"Error processing file study: {e}", exc_info=True)
        await safe_edit(thinking_msg, t("ai_error", lang))

@router.callback_query(F.data.in_(["study_cancel", "reg_confirm_cancel"]))
async def study_cancel_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    await state.clear()
    await safe_edit(callback.message, "⏹️ Study mode closed. Use /study or the menu to start anytime.")

@router.message(Command("current"), StateFilter(None))
async def show_current_session(message: Message):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language or "English"
    session = await learning_service.get_active_session(telegram_id)
    if not session:
        await safe_reply(message, t("no_active_session", lang))
        return

    grade_str = f"{student.grade}" if student and student.grade is not None else "Not Set"
    sub_info = config.SUBJECTS.get(session.subject, {})
    sub_emoji = sub_info.get("emoji", "📚")
    
    stage_mapping = {
        "INTRODUCTION": "📖 Introduction",
        "LEARNING": "🧠 Learning",
        "PRACTICE": "✍️ Practice",
        "QUIZ": "❓ Quiz",
        "REVIEW": "📝 Review",
        "MASTERED": "🏆 Mastered"
    }
    pretty_stage = stage_mapping.get(session.stage, session.stage)
    
    active_quiz = await quiz_service.get_active_quiz(telegram_id)
    if active_quiz:
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
            correct=active_quiz.correct_answers
        )
    else:
        started_str = session.created_at.strftime("%Y-%m-%d") if session.created_at else "Today"
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

@router.callback_query(F.data == "study_input_text")
async def study_input_text_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    await state.set_state(StudyStates.waiting_for_text)
    await safe_edit(callback.message, t("study_ask_text", lang))

@router.callback_query(F.data == "study_input_file")
async def study_input_file_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    await state.set_state(StudyStates.waiting_for_file)
    await safe_edit(callback.message, t("study_ask_file", lang))

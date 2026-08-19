import json
import asyncio
import logging
from typing import List, Optional
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service, learning_service, quiz_service, pdf_service
from bot.services.i18n import t, get_subject_name_in_lang
from bot.utils import safe_reply, safe_edit
from bot.keyboards.quiz import get_quiz_options_keyboard

router = Router()

class ExamStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_scope_input = State()
    waiting_for_qcount = State()

def get_exam_subjects_keyboard(student_courses: List[str], grade: Optional[str], lang: str = "English") -> InlineKeyboardMarkup:
    curriculum = config.get_curriculum_subjects(grade=grade)
    subjects_to_show = [c for c in student_courses if c in curriculum] if student_courses else curriculum
    if not subjects_to_show:
        subjects_to_show = curriculum

    buttons = []
    row = []
    for subj in subjects_to_show:
        emoji = config.SUBJECTS.get(subj, {}).get("emoji", "📚")
        loc_name = get_subject_name_in_lang(subj, lang)
        row.append(InlineKeyboardButton(text=f"{emoji} {loc_name}", callback_data=f"exam_subj_{subj}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="exam_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_exam_scope_keyboard(subject: str, grade: Optional[str], lang: str = "English") -> InlineKeyboardMarkup:
    review_grades = config.get_exam_review_grades(grade)
    grades_str = ", ".join([f"Grade {g}" for g in review_grades])
    
    buttons = [
        [InlineKeyboardButton(text=f"🎓 Full National Exam Practice ({grades_str})", callback_data="exam_scope_FULL")],
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="exam_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_exam_qcount_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="⚡ 5 Questions (Quick)", callback_data="exam_qc_5"),
            InlineKeyboardButton(text="📝 10 Questions (Standard)", callback_data="exam_qc_10")
        ],
        [
            InlineKeyboardButton(text="🎯 15 Questions (Intensive)", callback_data="exam_qc_15"),
            InlineKeyboardButton(text="🏆 20 Questions (Full Mock)", callback_data="exam_qc_20")
        ],
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="exam_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("national_exam"))
@router.callback_query(F.data == "menu_national_exam")
async def start_national_exam(event: Message | CallbackQuery, state: FSMContext):
    telegram_id = event.from_user.id
    message = event if isinstance(event, Message) else event.message

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except Exception:
            pass

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    if not student_service.has_national_exam_access(student):
        text = t("exam_locked_card", lang)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_support", lang), callback_data="menu_support")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_main")]
        ])
        await safe_reply(message, text, reply_markup=kb)
        return

    grade = student.grade if student else "10"
    courses = student.selected_courses if student else []

    await state.set_state(ExamStates.waiting_for_subject)
    text = t("exam_ask_subject", lang)
    reply_markup = get_exam_subjects_keyboard(courses, grade, lang)
    await safe_reply(message, text, reply_markup=reply_markup)

@router.callback_query(F.data == "exam_cancel")
async def cancel_exam(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    await state.clear()
    student = await student_service.get_student(callback.from_user.id)
    lang = student.preferred_language if student else "English"
    await safe_edit(callback.message, t("reg_cancelled", lang))

@router.callback_query(F.data.startswith("exam_subj_"), ExamStates.waiting_for_subject)
async def process_exam_subject(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    subj = callback.data.split("exam_subj_")[1]
    await state.update_data(exam_subject=subj)
    await state.set_state(ExamStates.waiting_for_scope_input)

    student = await student_service.get_student(callback.from_user.id)
    lang = student.preferred_language if student else "English"
    grade = student.grade if student else "10"

    loc_subj = get_subject_name_in_lang(subj, lang)
    text = t("exam_ask_scope", lang, subject=loc_subj)
    reply_markup = get_exam_scope_keyboard(subj, grade, lang)
    await safe_edit(callback.message, text, reply_markup=reply_markup)

@router.callback_query(F.data == "exam_scope_FULL", ExamStates.waiting_for_scope_input)
async def process_exam_scope_full(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    subj = data.get("exam_subject", "General Science")

    student = await student_service.get_student(callback.from_user.id)
    lang = student.preferred_language if student else "English"
    grade = student.grade if student else "10"
    review_grades = config.get_exam_review_grades(grade)

    scope_text = f"Full National Exam Practice ({', '.join(['Grade ' + g for g in review_grades])})"
    await state.update_data(exam_scope=scope_text)
    await state.set_state(ExamStates.waiting_for_qcount)

    loc_subj = get_subject_name_in_lang(subj, lang)
    text = t("exam_ask_qcount", lang, subject=loc_subj, scope=scope_text)
    reply_markup = get_exam_qcount_keyboard(lang)
    await safe_edit(callback.message, text, reply_markup=reply_markup)

@router.message(ExamStates.waiting_for_scope_input, F.text)
async def process_exam_scope_text(message: Message, state: FSMContext):
    typed_scope = message.text.strip() if message.text else "Custom Scope"
    data = await state.get_data()
    subj = data.get("exam_subject", "General Science")

    student = await student_service.get_student(message.from_user.id)
    lang = student.preferred_language if student else "English"

    await state.update_data(exam_scope=typed_scope)
    await state.set_state(ExamStates.waiting_for_qcount)

    loc_subj = get_subject_name_in_lang(subj, lang)
    text = t("exam_ask_qcount", lang, subject=loc_subj, scope=typed_scope)
    reply_markup = get_exam_qcount_keyboard(lang)
    await safe_reply(message, text, reply_markup=reply_markup)

@router.message(ExamStates.waiting_for_scope_input, F.photo)
async def process_exam_scope_photo(message: Message, state: FSMContext):
    caption = message.caption.strip() if message.caption else ""
    photo_desc = f"Photo Exam Material Input: {caption}" if caption else "Photo Material Input (Textbook Page / Notes)"

    data = await state.get_data()
    subj = data.get("exam_subject", "General Science")

    student = await student_service.get_student(message.from_user.id)
    lang = student.preferred_language if student else "English"

    await state.update_data(exam_scope=photo_desc)
    await state.set_state(ExamStates.waiting_for_qcount)

    loc_subj = get_subject_name_in_lang(subj, lang)
    text = t("exam_ask_qcount", lang, subject=loc_subj, scope=photo_desc)
    reply_markup = get_exam_qcount_keyboard(lang)
    await safe_reply(message, text, reply_markup=reply_markup)

@router.message(ExamStates.waiting_for_scope_input, F.document)
async def process_exam_scope_document(message: Message, state: FSMContext):
    doc = message.document
    filename = doc.file_name or "uploaded_material.pdf"
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    download_msg = await message.answer(t("tutor_thinking", lang))

    try:
        file_bytes_io = await message.bot.download(doc.file_id)
        if hasattr(file_bytes_io, "read"):
            pdf_bytes = file_bytes_io.read()
        else:
            pdf_bytes = bytes(file_bytes_io)

        extracted_text, num_pages, status, err = pdf_service.extract_text_from_pdf_bytes(pdf_bytes)
        try:
            await download_msg.delete()
        except Exception:
            pass

        if extracted_text and len(extracted_text.strip()) > 30:
            summary_scope = f"Document: {filename} ({num_pages} pages) - " + extracted_text[:400].replace("\n", " ")
        else:
            summary_scope = f"Document: {filename}"

        data = await state.get_data()
        subj = data.get("exam_subject", "General Science")

        await state.update_data(exam_scope=summary_scope)
        await state.set_state(ExamStates.waiting_for_qcount)

        loc_subj = get_subject_name_in_lang(subj, lang)
        text = t("exam_ask_qcount", lang, subject=loc_subj, scope=f"Document ({filename})")
        reply_markup = get_exam_qcount_keyboard(lang)
        await safe_reply(message, text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error processing exam scope document upload: {e}")
        await message.answer(t("ai_error", lang))

@router.callback_query(F.data.startswith("exam_qc_"), ExamStates.waiting_for_qcount)
async def process_exam_qcount(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    qcount = int(callback.data.split("exam_qc_")[1])
    data = await state.get_data()
    subj = data.get("exam_subject", "General Science")
    scope_text = data.get("exam_scope", "Full National Exam Practice")

    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    topic_name = f"National Exam ({scope_text})"
    quiz_session = await quiz_service.create_quiz_session(
        telegram_id=telegram_id,
        learning_session_id=0,
        subject=subj,
        topic=topic_name,
        total_questions=qcount
    )

    await state.clear()

    thinking_msg = await callback.message.answer(t("quiz_generating", lang))
    try:
        question = await quiz_service.generate_and_save_question(quiz_session)
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        if not question:
            await callback.message.answer(t("ai_error", lang))
            return

        options = json.loads(question.options_json)
        sub_info = config.SUBJECTS.get(subj, {})
        sub_emoji = sub_info.get("emoji", "🎓")

        text = t(
            "quiz_question_header",
            lang,
            emoji=sub_emoji,
            topic=topic_name,
            num=question.question_number,
            total=quiz_session.total_questions,
            text=question.question_text,
            opt_a=options.get('A', ''),
            opt_b=options.get('B', ''),
            opt_c=options.get('C', ''),
            opt_d=options.get('D', '')
        )
        await safe_reply(
            callback.message,
            text,
            reply_markup=get_quiz_options_keyboard(quiz_session.id, question.id)
        )
    except Exception as e:
        logging.error(f"Error starting national exam practice: {e}")
        await callback.message.answer(t("ai_error", lang))

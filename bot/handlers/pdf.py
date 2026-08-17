import io
import json
import logging
from typing import Optional, List, Dict, Any
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service, pdf_service, learning_service, quiz_service, conversation_service
from bot.services import gemini as gemini_service
from bot.services.i18n import t
from bot.keyboards.study_input import get_study_actions_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

class PDFStates(StatesGroup):
    waiting_for_pdf = State()
    waiting_for_chapter = State()
    waiting_for_exam_answers = State()
    waiting_for_pdf_question = State()

def get_pdf_actions_keyboard(material_id: int, lang: str = "English") -> InlineKeyboardMarkup:
    """Returns the action keyboard attached to an analyzed PDF document."""
    keyboard = [
        [
            InlineKeyboardButton(text="📖 Final Exam Study Mode", callback_data=f"pdf_act_learn_{material_id}"),
            InlineKeyboardButton(text=t("pdf_btn_ask", lang), callback_data=f"pdf_act_ask_{material_id}")
        ],
        [
            InlineKeyboardButton(text=t("pdf_btn_quiz", lang), callback_data=f"pdf_act_quiz_{material_id}"),
            InlineKeyboardButton(text=t("pdf_btn_test", lang), callback_data=f"pdf_act_test_{material_id}")
        ],
        [
            InlineKeyboardButton(text=t("pdf_btn_summary", lang), callback_data=f"pdf_act_sum_{material_id}"),
            InlineKeyboardButton(text=t("pdf_btn_upload_new", lang), callback_data="pdf_upload_new")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_exam_topic_continue_keyboard(has_next: bool, next_topic_name: str = "") -> InlineKeyboardMarkup:
    """Returns navigation buttons after grading a topic's 10-MCQ exam."""
    buttons = []
    if has_next:
        clean_name = (next_topic_name[:25] + "..") if len(next_topic_name) > 25 else next_topic_name
        buttons.append([InlineKeyboardButton(text=f"▶️ Next Topic: {clean_name}", callback_data="pdf_exam_next_topic")])
    buttons.append([
        InlineKeyboardButton(text="📚 Another Chapter", callback_data="pdf_exam_another_chapter"),
        InlineKeyboardButton(text="🏁 Finish", callback_data="pdf_exam_finish")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("pdf"), StateFilter(None))
@router.message(F.text.in_(["📄 Study PDF", "📄 የፒዲኤፍ ጥናት", "📄 Qo'annoo PDF"]), StateFilter(None))
async def start_pdf_study(message: Message, state: FSMContext, telegram_id: Optional[int] = None):
    """Entrypoint for the PDF Study System."""
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    lang = student.preferred_language if student else "English"
    
    # Check if student already has an active PDF
    active_mat = await pdf_service.get_active_material(tid)
    if active_mat:
        # Prompt chapter selection for Final Exam Study Mode
        await state.set_state(PDFStates.waiting_for_chapter)
        await state.update_data(
            material_id=active_mat.id,
            filename=active_mat.title or active_mat.filename,
            extracted_text=active_mat.extracted_text or ""
        )
        
        prompt_text = (
            f"📚 *Final Exam Study Mode: {active_mat.title or active_mat.filename}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Which chapter(s) do you want to study?\n\n"
            f"💡 _(e.g., Chapter 1, Chapter 2 and 3, or All)_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Upload New File", callback_data="pdf_upload_new")],
            [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
        ])
        await safe_reply(message, prompt_text, reply_markup=kb)
        return
        
    # Otherwise prompt for upload
    await state.set_state(PDFStates.waiting_for_pdf)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_reply(message, t("pdf_ask_upload", lang), reply_markup=kb)

@router.callback_query(F.data == "menu_study_pdf", StateFilter(None))
async def menu_study_pdf_callback(callback: CallbackQuery, state: FSMContext):
    """Main menu trigger for PDF Study."""
    try:
        await callback.answer()
    except Exception:
        pass
    await start_pdf_study(callback.message, state, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "pdf_upload_new")
async def pdf_upload_new_callback(callback: CallbackQuery, state: FSMContext):
    """Triggers prompt to upload a new PDF file."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(PDFStates.waiting_for_pdf)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_edit(callback.message, t("pdf_ask_upload", lang), reply_markup=kb)

@router.callback_query(F.data == "pdf_cancel")
async def cancel_pdf_callback(callback: CallbackQuery, state: FSMContext):
    """Cancels PDF FSM flow."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.clear()
    await safe_edit(callback.message, t("btn_cancel", lang) + ": Study mode cancelled. Send /menu anytime.")

@router.message(PDFStates.waiting_for_pdf, F.document)
async def process_pdf_document_upload(message: Message, state: FSMContext):
    """Handles incoming PDF document uploads and directly prompts for chapter."""
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    doc = message.document
    if not doc:
        return
        
    filename = doc.file_name or "document.pdf"
    
    # 1. Validate extension
    if not filename.lower().endswith(".pdf"):
        await safe_reply(message, t("pdf_invalid_type", lang))
        return
        
    # 2. Validate size
    if doc.file_size and doc.file_size > (config.MAX_FILE_SIZE_MB * 1024 * 1024):
        await safe_reply(message, t("pdf_size_error", lang))
        return
        
    processing_msg = await message.answer(t("pdf_processing", lang))
    
    try:
        # Download bytes
        file = await message.bot.get_file(doc.file_id)
        file_bytes_io = io.BytesIO()
        await message.bot.download_file(file.file_path, file_bytes_io)
        pdf_bytes = file_bytes_io.getvalue()
        
        # Process and save PDF
        material = await pdf_service.process_and_save_pdf(
            telegram_id=telegram_id,
            pdf_bytes=pdf_bytes,
            original_filename=filename,
            file_id=doc.file_id,
            student=student
        )
        
        # Transition to chapter selection for Final Exam Study Mode
        await state.set_state(PDFStates.waiting_for_chapter)
        await state.update_data(
            material_id=material.id,
            filename=material.title or material.filename,
            extracted_text=material.extracted_text or ""
        )
        
        try:
            await processing_msg.delete()
        except Exception:
            pass
            
        prompt_text = (
            f"📚 *Final Exam Study Mode: {material.title or material.filename}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Which chapter(s) do you want to study?\n\n"
            f"💡 _(e.g., Chapter 1, Chapters 2 and 3, or All)_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
        ])
        await safe_reply(message, prompt_text, reply_markup=kb)
        
    except Exception as e:
        logging.error(f"Error processing PDF upload: {e}", exc_info=True)
        await safe_edit(processing_msg, t("ai_error", lang))

@router.message(PDFStates.waiting_for_chapter)
async def process_exam_chapter_selection(message: Message, state: FSMContext):
    """
    Receives chosen chapter(s), starts Final Exam Study Mode,
    and presents Step 1 (Short Notes) + Step 2 (10 MCQs) for Topic 1.
    """
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    chapter_input = message.text.strip() if message.text else "Chapter 1"
    data = await state.get_data()
    filename = data.get("filename", "study document")
    extracted_text = data.get("extracted_text", "")
    
    if not extracted_text:
        active_mat = await pdf_service.get_active_material(telegram_id)
        if active_mat and active_mat.extracted_text:
            extracted_text = active_mat.extracted_text
            filename = active_mat.title or active_mat.filename
            
    # Send mandatory study greeting
    greeting_text = (
        f"Let's study together, starting from Chapter {chapter_input} in {filename}. "
        f"I am studying for my final exam. We will study step by step, following the content and order of the attached file."
    )
    await safe_reply(message, greeting_text)
    
    thinking = await message.answer("📖 Preparing Step 1 (Short Notes) & Step 2 (10 Exam Questions)...")
    
    try:
        # 1. Extract ordered topics in the chapter
        topics = await gemini_service.generate_exam_chapter_topics(
            material_text=extracted_text,
            chapter_name=chapter_input,
            lang=lang
        )
        if not topics:
            topics = [f"{chapter_input} - Core Concepts"]
            
        current_topic = topics[0]
        
        # 2. Start a learning session
        session = await learning_service.start_session(
            telegram_id=telegram_id,
            subject=f"Final Exam: {filename}",
            topic=f"{chapter_input} → {current_topic}"
        )
        
        # 3. Generate Step 1 (Short Notes) + Step 2 (10 MCQs)
        lesson_text, mcq_list = await gemini_service.generate_exam_topic_lesson(
            material_text=extracted_text,
            chapter_name=chapter_input,
            topic_name=current_topic,
            lang=lang
        )
        
        # 4. Save state for answers evaluation
        await state.set_state(PDFStates.waiting_for_exam_answers)
        await state.update_data(
            chapter_name=chapter_input,
            filename=filename,
            extracted_text=extracted_text,
            topics_list=topics,
            current_topic_index=0,
            current_topic_name=current_topic,
            current_mcqs=mcq_list,
            session_id=session.id
        )
        
        try:
            await thinking.delete()
        except Exception:
            pass
            
        await safe_reply(message, lesson_text)
        
    except Exception as e:
        logging.error(f"Error starting exam chapter study: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

@router.message(PDFStates.waiting_for_exam_answers)
async def process_exam_answers(message: Message, state: FSMContext):
    """
    Step 3: Checks student answers for the 10 MCQs, provides corrections & re-teaching,
    and offers button to continue to the next topic.
    """
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    student_answers = message.text.strip() if message.text else ""
    if not student_answers:
        return
        
    data = await state.get_data()
    current_topic_name = data.get("current_topic_name", "Current Topic")
    current_mcqs = data.get("current_mcqs", [])
    extracted_text = data.get("extracted_text", "")
    topics_list = data.get("topics_list", [])
    current_topic_index = data.get("current_topic_index", 0)
    chapter_name = data.get("chapter_name", "Chapter")
    
    thinking = await message.answer("📝 Checking your answers against the study material...")
    
    try:
        score, detailed_results, corrections_and_reteach = await gemini_service.grade_exam_topic_answers(
            material_text=extracted_text,
            topic_name=current_topic_name,
            mcqs=current_mcqs,
            student_answers=student_answers,
            lang=lang
        )
        
        has_next = (current_topic_index + 1) < len(topics_list)
        next_topic_name = topics_list[current_topic_index + 1] if has_next else ""
        
        feedback_text = (
            f"📊 *Exam Checkpoint: {current_topic_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏆 *Score:* {score}/10\n\n"
            f"{detailed_results}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Key Review & Corrections:*\n\n"
            f"{corrections_and_reteach}"
        )
        
        if not has_next:
            feedback_text += (
                f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 *Chapter Completed!*\n"
                f"You have finished all topics in *{chapter_name}*! Excellent work preparing for your final exam."
            )
            
        try:
            await thinking.delete()
        except Exception:
            pass
            
        await safe_reply(
            message,
            feedback_text,
            reply_markup=get_exam_topic_continue_keyboard(has_next, next_topic_name)
        )
        
    except Exception as e:
        logging.error(f"Error evaluating exam answers: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

@router.callback_query(F.data == "pdf_exam_next_topic")
async def pdf_exam_next_topic_callback(callback: CallbackQuery, state: FSMContext):
    """
    Step 4: Advances to the next topic in the selected chapter.
    """
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    data = await state.get_data()
    topics_list = data.get("topics_list", [])
    current_topic_index = data.get("current_topic_index", 0) + 1
    chapter_name = data.get("chapter_name", "Chapter")
    extracted_text = data.get("extracted_text", "")
    filename = data.get("filename", "study document")
    
    if current_topic_index >= len(topics_list):
        await safe_reply(
            callback,
            f"🎉 You have completed all topics in {chapter_name}! Would you like to study another chapter?",
            reply_markup=get_exam_topic_continue_keyboard(False)
        )
        return
        
    next_topic = topics_list[current_topic_index]
    thinking = await callback.message.answer(f"📖 Loading Step 1 Notes & 10 Questions for: {next_topic}...")
    
    try:
        # Start learning session for next topic
        session = await learning_service.start_session(
            telegram_id=telegram_id,
            subject=f"Final Exam: {filename}",
            topic=f"{chapter_name} → {next_topic}"
        )
        
        lesson_text, mcq_list = await gemini_service.generate_exam_topic_lesson(
            material_text=extracted_text,
            chapter_name=chapter_name,
            topic_name=next_topic,
            lang=lang
        )
        
        await state.update_data(
            current_topic_index=current_topic_index,
            current_topic_name=next_topic,
            current_mcqs=mcq_list,
            session_id=session.id
        )
        
        try:
            await thinking.delete()
        except Exception:
            pass
            
        await safe_reply(callback, lesson_text)
        
    except Exception as e:
        logging.error(f"Error loading next exam topic: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

@router.callback_query(F.data == "pdf_exam_another_chapter")
async def pdf_exam_another_chapter_callback(callback: CallbackQuery, state: FSMContext):
    """Prompts student to select another chapter from the active material."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(PDFStates.waiting_for_chapter)
    await safe_reply(
        callback,
        "📚 *Which chapter(s) do you want to study next?*\n\n_(e.g., Chapter 2, Chapter 3, or All)_"
    )

@router.callback_query(F.data == "pdf_exam_finish")
async def pdf_exam_finish_callback(callback: CallbackQuery, state: FSMContext):
    """Concludes the final exam study session."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.clear()
    from bot.handlers.start import send_student_dashboard
    await safe_edit(callback.message, "✅ Exam study session completed! Returning to main menu.")
    await send_student_dashboard(callback.message, telegram_id)

@router.callback_query(F.data.startswith("pdf_act_learn_"), StateFilter(None))
async def pdf_action_learn_callback(callback: CallbackQuery, state: FSMContext):
    """Triggers Final Exam Study Mode for the document."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    active_mat = await pdf_service.get_active_material(telegram_id)
    if not active_mat:
        await callback.answer("No document found.", show_alert=True)
        return
        
    await state.set_state(PDFStates.waiting_for_chapter)
    await state.update_data(
        material_id=active_mat.id,
        filename=active_mat.title or active_mat.filename,
        extracted_text=active_mat.extracted_text or ""
    )
    
    prompt_text = (
        f"📚 *Final Exam Study Mode: {active_mat.title or active_mat.filename}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Which chapter(s) do you want to study?\n\n"
        f"💡 _(e.g., Chapter 1, Chapters 2 and 3, or All)_"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_reply(callback, prompt_text, reply_markup=kb)

@router.callback_query(F.data.startswith("pdf_act_sum_"), StateFilter(None))
async def pdf_action_summary_callback(callback: CallbackQuery):
    """Displays full summary of the document."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    material = await pdf_service.get_active_material(telegram_id)
    if not material:
        await callback.answer("No document found.", show_alert=True)
        return
        
    summary_text = (
        f"📖 *Summary: {material.title or material.filename}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{material.summary or 'No summary available.'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Use the buttons below to start Final Exam Study Mode or ask questions."
    )
    await safe_reply(callback, summary_text, reply_markup=get_pdf_actions_keyboard(material.id, lang))

@router.callback_query(F.data.startswith("pdf_act_ask_"), StateFilter(None))
async def pdf_action_ask_callback(callback: CallbackQuery, state: FSMContext):
    """Triggers Grounded PDF Q&A mode."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    material = await pdf_service.get_active_material(telegram_id)
    
    await state.set_state(PDFStates.waiting_for_pdf_question)
    title = material.title if material else "your document"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_reply(
        callback,
        t("pdf_ask_question_prompt", lang, title=title),
        reply_markup=kb
    )

@router.message(PDFStates.waiting_for_pdf_question)
async def process_pdf_question(message: Message, state: FSMContext):
    """Answers student questions strictly grounded in the uploaded document."""
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    question = message.text or ""
    if not question:
        return
        
    thinking = await message.answer(t("tutor_thinking", lang))
    
    try:
        active_mat = await pdf_service.get_active_material(telegram_id)
        if not active_mat:
            await safe_edit(thinking, t("pdf_empty_error", lang))
            await state.clear()
            return
            
        answer = await pdf_service.ask_pdf_question(
            telegram_id=telegram_id,
            question=question,
            student=student,
            material=active_mat
        )
        
        await conversation_service.add_message(telegram_id, "user", f"[PDF Q&A on {active_mat.title}]: {question}")
        await conversation_service.add_message(telegram_id, "assistant", answer)
        
        try:
            await thinking.delete()
        except Exception:
            pass
        text = t("pdf_answer_header", lang, answer=answer)
        await safe_reply(message, text, reply_markup=get_pdf_actions_keyboard(active_mat.id, lang))
        
    except Exception as e:
        logging.error(f"Error in PDF Q&A: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

@router.callback_query(F.data.startswith("pdf_act_quiz_"), StateFilter(None))
async def pdf_action_quiz_callback(callback: CallbackQuery):
    """Starts a quiz grounded in the PDF document."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    active_mat = await pdf_service.get_active_material(telegram_id)
    if not active_mat:
        await callback.answer("No document found.", show_alert=True)
        return
        
    session = await learning_service.start_session(
        telegram_id=telegram_id,
        subject="PDF Document",
        topic=active_mat.title or active_mat.filename
    )
    
    quiz_session = await quiz_service.start_quiz(
        telegram_id, session.id, "PDF Document", active_mat.title or active_mat.filename
    )
    
    from bot.handlers.quiz import send_next_quiz_question
    await send_next_quiz_question(callback.message, quiz_session)

@router.callback_query(F.data.startswith("pdf_act_test_"), StateFilter(None))
async def pdf_action_test_callback(callback: CallbackQuery, state: FSMContext):
    """Starts a written test grounded in the PDF document."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    active_mat = await pdf_service.get_active_material(telegram_id)
    if not active_mat:
        await callback.answer("No document found.", show_alert=True)
        return
        
    await learning_service.start_session(
        telegram_id=telegram_id,
        subject="PDF Document",
        topic=active_mat.title or active_mat.filename
    )
    
    from bot.handlers.actions import test_start
    await test_start(callback.message, state, telegram_id=telegram_id)

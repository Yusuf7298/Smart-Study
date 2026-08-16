import io
import json
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service, pdf_service, learning_service, quiz_service, conversation_service
from bot.services.i18n import t
from bot.keyboards.study_input import get_study_actions_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

class PDFStates(StatesGroup):
    waiting_for_pdf = State()
    waiting_for_pdf_question = State()

def get_pdf_actions_keyboard(material_id: int, lang: str = "English") -> InlineKeyboardMarkup:
    """Returns the action keyboard attached to an analyzed PDF document."""
    keyboard = [
        [
            InlineKeyboardButton(text=t("pdf_btn_learn", lang), callback_data=f"pdf_act_learn_{material_id}"),
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
        # Show active PDF dashboard
        topics_list = []
        if active_mat.topics_json:
            try:
                topics_list = json.loads(active_mat.topics_json)
            except Exception:
                topics_list = []
        topics_str = "\n".join([f"• {t_name}" for t_name in topics_list]) if topics_list else "• Key Concepts"
        
        chars_count = len(active_mat.extracted_text) if active_mat.extracted_text else 0
        text = t(
            "pdf_analyzed_title",
            lang,
            title=active_mat.title or active_mat.filename,
            pages=active_mat.page_count,
            chars=chars_count,
            topics=topics_str,
            summary=active_mat.summary or "Document ready for study."
        )
        await safe_reply(message, text, reply_markup=get_pdf_actions_keyboard(active_mat.id, lang))
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
    await start_pdf_study(callback.message, state, telegram_id=callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "pdf_upload_new", StateFilter(None))
async def pdf_upload_new_callback(callback: CallbackQuery, state: FSMContext):
    """Triggers prompt to upload a new PDF file."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(PDFStates.waiting_for_pdf)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_edit(callback.message, t("pdf_ask_upload", lang), reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "pdf_cancel")
async def cancel_pdf_callback(callback: CallbackQuery, state: FSMContext):
    """Cancels PDF FSM flow."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.clear()
    await safe_edit(callback.message, t("btn_cancel", lang) + ": PDF action cancelled.")
    await callback.answer()

@router.message(PDFStates.waiting_for_pdf, F.document)
async def process_pdf_document_upload(message: Message, state: FSMContext):
    """Handles incoming PDF document uploads."""
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
        
        await state.clear()
        
        # Format response
        topics_list = []
        if material.topics_json:
            try:
                topics_list = json.loads(material.topics_json)
            except Exception:
                topics_list = []
        topics_str = "\n".join([f"• {t_name}" for t_name in topics_list]) if topics_list else "• Key Concepts"
        
        chars_count = len(material.extracted_text) if material.extracted_text else 0
        text = t(
            "pdf_analyzed_title",
            lang,
            title=material.title or material.filename,
            pages=material.page_count,
            chars=chars_count,
            topics=topics_str,
            summary=material.summary or "Document ready for study."
        )
        
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await safe_reply(message, text, reply_markup=get_pdf_actions_keyboard(material.id, lang))
        
    except Exception as e:
        logging.error(f"Error processing PDF upload: {e}", exc_info=True)
        await safe_edit(processing_msg, t("ai_error", lang))

@router.callback_query(F.data.startswith("pdf_act_ask_"), StateFilter(None))
async def pdf_action_ask_callback(callback: CallbackQuery, state: FSMContext):
    """Triggers Grounded PDF Q&A mode."""
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
    await callback.answer()

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
        
        # Save to conversation history
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

@router.callback_query(F.data.startswith("pdf_act_sum_"), StateFilter(None))
async def pdf_action_summary_callback(callback: CallbackQuery):
    """Displays full summary of the document."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    mat_id = int(callback.data.split("pdf_act_sum_")[1])
    material = await pdf_service.get_active_material(telegram_id)
    if not material:
        await callback.answer("No document found.", show_alert=True)
        return
        
    summary_text = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 *Summary: {material.title or material.filename}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{material.summary or 'No summary available.'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Use the buttons below to learn, ask questions, or take a quiz on this document."
    )
    await safe_reply(callback, summary_text, reply_markup=get_pdf_actions_keyboard(material.id, lang))
    await callback.answer()

@router.callback_query(F.data.startswith("pdf_act_learn_"), StateFilter(None))
async def pdf_action_learn_callback(callback: CallbackQuery):
    """Starts interactive guided study using the PDF context."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    active_mat = await pdf_service.get_active_material(telegram_id)
    if not active_mat:
        await callback.answer("No document found.", show_alert=True)
        return
        
    # Start a learning session based on this PDF
    session = await learning_service.start_session(
        telegram_id=telegram_id,
        subject="PDF Document",
        topic=active_mat.title or active_mat.filename
    )
    
    thinking = await callback.message.answer(t("study_intro_thinking", lang))
    try:
        intro_text = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📖 *Interactive Study Mode: {active_mat.title or active_mat.filename}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"I have loaded your document into your active study session!\n\n"
            f"You can now:\n"
            f"• Ask any question about the concepts in this document\n"
            f"• Ask me to explain difficult sections\n"
            f"• Type /quiz for MCQs or /test for a written exam\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 *What topic or section from the document would you like to start with?*"
        )
        try:
            await thinking.delete()
        except Exception:
            pass
        await safe_reply(callback, intro_text, reply_markup=get_study_actions_keyboard())
    except Exception as e:
        logging.error(f"Error starting PDF study session: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))
        
    await callback.answer()

@router.callback_query(F.data.startswith("pdf_act_quiz_"), StateFilter(None))
async def pdf_action_quiz_callback(callback: CallbackQuery):
    """Starts a quiz grounded in the PDF document."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
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
    await callback.answer()

@router.callback_query(F.data.startswith("pdf_act_test_"), StateFilter(None))
async def pdf_action_test_callback(callback: CallbackQuery, state: FSMContext):
    """Starts a written test grounded in the PDF document."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    active_mat = await pdf_service.get_active_material(telegram_id)
    if not active_mat:
        await callback.answer("No document found.", show_alert=True)
        return
        
    session = await learning_service.start_session(
        telegram_id=telegram_id,
        subject="PDF Document",
        topic=active_mat.title or active_mat.filename
    )
    
    from bot.handlers.actions import test_start
    await test_start(callback.message, state, telegram_id=telegram_id)
    await callback.answer()

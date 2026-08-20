from bot.database.models import StudentModel
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
from bot.services.telegram_downloader import download_file_bytes
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

def get_exam_start_mcqs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Start 10 Practice Questions", callback_data="pdf_exam_start_mcqs")],
        [InlineKeyboardButton(text="❌ Quit", callback_data="pdf_cancel")]
    ])

def get_exam_mcq_keyboard(question_num: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="A", callback_data=f"pdf_mcq_ans_{question_num}_A"),
            InlineKeyboardButton(text="B", callback_data=f"pdf_mcq_ans_{question_num}_B"),
            InlineKeyboardButton(text="C", callback_data=f"pdf_mcq_ans_{question_num}_C"),
            InlineKeyboardButton(text="D", callback_data=f"pdf_mcq_ans_{question_num}_D")
        ],
        [
            InlineKeyboardButton(text="❌ Quit Exam", callback_data="pdf_cancel")
        ]
    ])

def get_exam_mcq_next_keyboard(question_num: int, total: int = 10) -> InlineKeyboardMarkup:
    if question_num < total:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"➡️ Next Question ({question_num+1}/{total})", callback_data=f"pdf_mcq_next_{question_num}")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 View Final Score & Reteach", callback_data="pdf_mcq_finish")]
        ])

def get_exam_topic_continue_keyboard(has_next: bool, next_topic_name: str = "") -> InlineKeyboardMarkup:
    buttons = []
    if has_next:
        clean_name = (next_topic_name[:25] + "..") if len(next_topic_name) > 25 else next_topic_name
        buttons.append([InlineKeyboardButton(text=f"▶️ Next Topic: {clean_name}", callback_data="pdf_exam_next_topic")])
    buttons.append([
        InlineKeyboardButton(text="🔄 Retest Topic", callback_data="pdf_exam_retest_topic"),
        InlineKeyboardButton(text="📚 Another Chapter", callback_data="pdf_exam_another_chapter")
    ])
    buttons.append([
        InlineKeyboardButton(text="🏁 Finish", callback_data="pdf_exam_finish")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("pdf"))
@router.message(F.text.in_(["📄 Study PDF", "📄 የፒዲኤፍ ጥናት", "📄 Qo'annoo PDF"]))
async def start_pdf_study(message: Message, state: FSMContext, telegram_id: Optional[int] = None):
    await state.clear()
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    lang = student.preferred_language if student else "English"
    
    active_mat = await pdf_service.get_active_material(tid)
    if active_mat:
        await state.set_state(PDFStates.waiting_for_chapter)
        await state.update_data(
            material_id=active_mat.id,
            filename=active_mat.title or active_mat.filename,
            extracted_text=active_mat.extracted_text or ""
        )
        
        prompt_text = (
            f"📚 Final Exam Study Mode: {active_mat.title or active_mat.filename}*\n"
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
        
    await state.set_state(PDFStates.waiting_for_pdf)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_reply(message, t("pdf_ask_upload", lang), reply_markup=kb)

@router.callback_query(F.data == "menu_study_pdf")
async def menu_study_pdf_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.answer()
    except Exception:
        pass
    await start_pdf_study(callback.message, state, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "pdf_upload_new")
async def pdf_upload_new_callback(callback: CallbackQuery, state: FSMContext):
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
@router.message(StateFilter(None), F.document)
async def process_pdf_document_upload(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    doc = message.document
    if not doc:
        return
        
    filename = doc.file_name or "document.pdf"
    
    if not filename.lower().endswith(".pdf"):
        await safe_reply(message, t("pdf_invalid_type", lang))
        return
        
    if doc.file_size and doc.file_size > (config.MAX_FILE_SIZE_MB * 1024 * 1024):
        await safe_reply(message, t("pdf_size_error", lang, max_size=config.MAX_FILE_SIZE_MB))
        return
        
    processing_msg = await message.answer(t("pdf_processing", lang))
    
    try:
        pdf_bytes = await download_file_bytes(message, doc, status_message=processing_msg)
        if not pdf_bytes:
            await safe_edit(processing_msg, t("ai_error", lang))
            return
        
        material = await pdf_service.process_and_save_pdf(
            telegram_id=telegram_id,
            pdf_bytes=pdf_bytes,
            original_filename=filename,
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
            await processing_msg.delete()
        except Exception:
            pass
            
        prompt_text = (
            f"📚 Final Exam Study Mode: {material.title or material.filename}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Which chapter(s) do you want to study?\n\n"
            f"💡 _(e.g., Chapter 1, Chapters 2 and 3, or All)_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
        ])
        await safe_reply(message, prompt_text, reply_markup=kb)
        
    except ValueError as ve:
        await safe_edit(processing_msg, str(ve))
    except Exception as e:
        logging.error(f"Error processing PDF upload: {e}", exc_info=True)
        await safe_edit(processing_msg, t("ai_error", lang))

async def execute_grounded_chapter_study(
    message: Message,
    state: FSMContext,
    telegram_id: int,
    chapter_name: str,
    extracted_text: str,
    filename: str,
    student: Optional[StudentModel] = None
):
    """
    Executes grounded chapter study:
    1. Sends mandatory exam study greeting
    2. Extracts ordered topic titles
    3. Starts learning session
    4. Generates Step 1 (Short Notes) & Step 2 (10 MCQs)
    5. Sets PDFStates.waiting_for_exam_answers
    """
    if not student:
        student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    thinking = await message.answer(f"📖 Preparing Chapter {chapter_name} Notes & Practice Questions...")
    
    try:
        topics = await gemini_service.generate_exam_chapter_topics(
            material_text=extracted_text,
            chapter_name=chapter_name,
            lang=lang
        )
        if not topics:
            topics = [f"{chapter_name} - Core Concepts"]
            
        current_topic = topics[0]
        session = await learning_service.start_session(
            telegram_id=telegram_id,
            subject=f"Final Exam: {filename}",
            topic=f"{chapter_name} → {current_topic}"
        )
        lesson_text, mcq_list = await gemini_service.generate_exam_topic_lesson(
            material_text=extracted_text,
            chapter_name=chapter_name,
            topic_name=current_topic,
            lang=lang
        )
        await state.set_state(PDFStates.waiting_for_exam_answers)
        await state.update_data(
            chapter_name=chapter_name,
            filename=filename,
            extracted_text=extracted_text,
            topics_list=topics,
            current_topic_index=0,
            current_topic_name=current_topic,
            current_mcqs=mcq_list,
            current_question_idx=0,
            student_answers={},
            session_id=session.id
        )
        
        try:
            await thinking.delete()
        except Exception:
            pass
            
        await safe_reply(message, lesson_text, reply_markup=get_exam_start_mcqs_keyboard())
        
    except Exception as e:
        logging.error(f"Error starting exam chapter study: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

async def render_exam_question(target: Message | CallbackQuery, data: dict, question_idx: int):
    mcqs = data.get("current_mcqs", [])
    total = len(mcqs)
    if question_idx >= total:
        await show_exam_final_results(target, data)
        return
        
    q = mcqs[question_idx]
    q_num = question_idx + 1
    
    card = (
        f"❓ Exam Question {q_num} of {total}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{q['question']}\n\n"
        f"A) {q['option_a']}\n"
        f"B) {q['option_b']}\n"
        f"C) {q['option_c']}\n"
        f"D) {q['option_d']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Tap your answer choice below:"
    )
    kb = get_exam_mcq_keyboard(q_num)
    if isinstance(target, CallbackQuery) or hasattr(target, "message"):
        msg = target.message if hasattr(target, "message") else target
        await safe_edit(msg, card, reply_markup=kb)
    else:
        await safe_reply(target, card, reply_markup=kb)

async def show_exam_final_results(target: Message | CallbackQuery, data: dict):
    mcqs = data.get("current_mcqs", [])
    student_answers = data.get("student_answers", {})
    total = len(mcqs)
    score = 0
    detailed_lines = []
    weak_points = []
    
    for idx, q in enumerate(mcqs, 1):
        ans = student_answers.get(str(idx), student_answers.get(idx, "-"))
        corr = q.get("correct_answer", "A")
        is_correct = (ans == corr)
        if is_correct:
            score += 1
            detailed_lines.append(f"• Q{idx}: ✅ Correct (Your answer: *{ans}*)")
        else:
            detailed_lines.append(f"• Q{idx}: ❌ Incorrect (Your answer: *{ans}* | Correct: *{corr}*)\n  _{q.get('explanation', '')}_")
            weak_points.append(f"Q{idx} ({q.get('question')[:40]}..)")
            
    current_topic_name = data.get("current_topic_name", "Current Topic")
    topics_list = data.get("topics_list", [])
    current_topic_index = data.get("current_topic_index", 0)
    chapter_name = data.get("chapter_name", "Chapter")
    has_next = (current_topic_index + 1) < len(topics_list)
    next_topic_name = topics_list[current_topic_index + 1] if has_next else ""
    
    score_pct = int((score / total) * 100) if total > 0 else 0
    grade_status = "🌟 Outstanding!" if score >= 8 else ("👍 Good Effort — Review Weak Points" if score >= 6 else "⚠️ Needs Review & Practice")
    
    results_text = (
        f"📊 Exam Checkpoint: {current_topic_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 Score: {score}/{total} ({score_pct}%) — {grade_status}\n\n"
        f"Detailed Answers Check:\n"
        + "\n".join(detailed_lines)
    )
    
    if weak_points:
        results_text += f"\n\n━━━━━━━━━━━━━━━━━━━━\n📌 Concepts to Review:\n• " + "\n• ".join(weak_points)
    else:
        results_text += f"\n\n━━━━━━━━━━━━━━━━━━━━\n🎉 Mastery Achieved: You answered all questions correctly!"
        
    if not has_next:
        results_text += (
            f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🎉 Chapter Completed!\n"
            f"You have finished all topics in {chapter_name}! Excellent work preparing for your final exam."
        )
        
    kb = get_exam_topic_continue_keyboard(has_next, next_topic_name)
    if isinstance(target, CallbackQuery) or hasattr(target, "message"):
        msg = target.message if hasattr(target, "message") else target
        await safe_edit(msg, results_text, reply_markup=kb)
    else:
        await safe_reply(target, results_text, reply_markup=kb)

@router.callback_query(F.data == "pdf_exam_start_mcqs")
async def pdf_exam_start_mcqs_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    await state.update_data(current_question_idx=0, student_answers={})
    data["current_question_idx"] = 0
    data["student_answers"] = {}
    await render_exam_question(callback, data, 0)

@router.callback_query(F.data.startswith("pdf_mcq_ans_"))
async def pdf_mcq_ans_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    parts = callback.data.split("pdf_mcq_ans_")[1].split("_")
    q_num = int(parts[0])
    selected_opt = parts[1]
    
    data = await state.get_data()
    mcqs = data.get("current_mcqs", [])
    student_answers = data.get("student_answers", {})
    student_answers[str(q_num)] = selected_opt
    await state.update_data(student_answers=student_answers)
    
    q_idx = q_num - 1
    if 0 <= q_idx < len(mcqs):
        q = mcqs[q_idx]
        corr = q.get("correct_answer", "A")
        is_correct = (selected_opt.upper() == corr.upper())
        status_line = "✅ Correct!" if is_correct else f"❌ Incorrect. Correct Answer: {corr}"
        
        feedback_card = (
            f"❓ Question {q_num} of {len(mcqs)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{q['question']}\n\n"
            f"Your Answer: Option {selected_opt}\n"
            f"{status_line}\n\n"
            f"💡 Explanation:\n{q.get('explanation', '')}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await safe_edit(callback.message, feedback_card, reply_markup=get_exam_mcq_next_keyboard(q_num, len(mcqs)))
    else:
        data["student_answers"] = student_answers
        await show_exam_final_results(callback, data)

@router.callback_query(F.data.startswith("pdf_mcq_next_"))
async def pdf_mcq_next_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    q_num = int(callback.data.split("pdf_mcq_next_")[1])
    next_idx = q_num
    data = await state.get_data()
    await state.update_data(current_question_idx=next_idx)
    data["current_question_idx"] = next_idx
    await render_exam_question(callback, data, next_idx)

@router.callback_query(F.data == "pdf_mcq_finish")
async def pdf_mcq_finish_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    await show_exam_final_results(callback, data)

@router.callback_query(F.data == "pdf_exam_retest_topic")
async def pdf_exam_retest_topic_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    await state.update_data(current_question_idx=0, student_answers={})
    data["current_question_idx"] = 0
    data["student_answers"] = {}
    await render_exam_question(callback, data, 0)

@router.message(PDFStates.waiting_for_chapter)
async def process_exam_chapter_selection(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    chapter_input = message.text.strip() if message.text else "Chapter 1"
    data = await state.get_data()
    filename = data.get("filename", "study document")
    extracted_text = data.get("extracted_text", "")
    
    if not extracted_text:
        active_mat = await pdf_service.get_active_material(telegram_id)
        if active_mat and active_mat.extracted_text:
            extracted_text = active_mat.extracted_text
            filename = active_mat.title or active_mat.filename
            
    await execute_grounded_chapter_study(
        message=message,
        state=state,
        telegram_id=telegram_id,
        chapter_name=chapter_input,
        extracted_text=extracted_text,
        filename=filename,
        student=student
    )

@router.message(PDFStates.waiting_for_exam_answers)
async def process_exam_answers(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    student_answers = message.text.strip() if message.text else ""
    if not student_answers:
        return
        
    data = await state.get_data()
    
    clean_ans = student_answers.upper().strip().replace(".", "")
    if clean_ans in ["A", "B", "C", "D"]:
        q_idx = data.get("current_question_idx", 0)
        q_num = q_idx + 1
        mcqs = data.get("current_mcqs", [])
        student_answers_dict = data.get("student_answers", {})
        student_answers_dict[str(q_num)] = clean_ans
        await state.update_data(student_answers=student_answers_dict)
        
        if 0 <= q_idx < len(mcqs):
            q = mcqs[q_idx]
            corr = q.get("correct_answer", "A")
            is_correct = (clean_ans == corr)
            status_line = "✅ Correct!" if is_correct else f"❌ Incorrect. Correct Answer: {corr}"
            feedback_card = (
                f"❓ Question {q_num} of {len(mcqs)}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{q['question']}\n\n"
                f"Your Answer: Option {clean_ans}\n"
                f"{status_line}\n\n"
                f"Explanation:\n{q.get('explanation', '')}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            await safe_reply(message, feedback_card, reply_markup=get_exam_mcq_next_keyboard(q_num, len(mcqs)))
            return
            
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
            f"Exam Checkpoint: {current_topic_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏆 Score: {score}/10\n\n"
            f"{detailed_results}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Key Review & Corrections:\n\n"
            f"{corrections_and_reteach}"
        )
        
        if not has_next:
            feedback_text += (
                f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 Chapter Completed!\n"
                f"You have finished all topics in {chapter_name}! Excellent work preparing for your final exam."
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
            current_question_idx=0,
            student_answers={},
            session_id=session.id
        )
        
        try:
            await thinking.delete()
        except Exception:
            pass
            
        await safe_reply(callback, lesson_text, reply_markup=get_exam_start_mcqs_keyboard())
        
    except Exception as e:
        logging.error(f"Error loading next exam topic: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

@router.callback_query(F.data == "pdf_exam_another_chapter")
async def pdf_exam_another_chapter_callback(callback: CallbackQuery, state: FSMContext):
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
        "📚 Which chapter(s) do you want to study next?\n\n_(e.g., Chapter 2, Chapter 3, or All)_"
    )

@router.callback_query(F.data == "pdf_exam_finish")
async def pdf_exam_finish_callback(callback: CallbackQuery, state: FSMContext):
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
        f"📚 Final Exam Study Mode: {active_mat.title or active_mat.filename}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Which chapter(s) do you want to study?\n\n"
        f"💡 (e.g., Chapter 1, Chapters 2 and 3, or All)"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="pdf_cancel")]
    ])
    await safe_reply(callback, prompt_text, reply_markup=kb)

@router.callback_query(F.data.startswith("pdf_act_sum_"), StateFilter(None))
async def pdf_action_summary_callback(callback: CallbackQuery):
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
        f"📖 Summary: {material.title or material.filename}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{material.summary or 'No summary available.'}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Use the buttons below to start Final Exam Study Mode or ask questions."
    )
    await safe_reply(callback, summary_text, reply_markup=get_pdf_actions_keyboard(material.id, lang))

@router.callback_query(F.data.startswith("pdf_act_ask_"), StateFilter(None))
async def pdf_action_ask_callback(callback: CallbackQuery, state: FSMContext):
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

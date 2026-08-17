import logging
import asyncio
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from google.genai import types

from bot.services import student_service, learning_service, conversation_service
from bot.services import gemini as gemini_service
from bot.services.gemini import ask_gemini_with_profile
from bot.database.repositories import tests as test_repo
from bot.handlers.registration import get_grades_keyboard, get_languages_keyboard
from bot.keyboards.study_input import get_study_actions_keyboard
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit

router = Router()

class ActionStates(StatesGroup):
    waiting_for_test_answer = State()

@router.message(Command("test"), StateFilter(None))
@router.message(F.text.in_(["📝 Written Test", "📝 የጽሁፍ ፈተና", "📝 Qormaata Barreeffamaa"]), StateFilter(None))
async def test_start(message: Message, state: FSMContext, telegram_id: Optional[int] = None):
    """Starts the written test flow."""
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    if not student:
        await message.answer("Please register first by sending /start.")
        return
        
    lang = student.preferred_language or "English"
    learning_session = await learning_service.get_active_session(tid)
    if not learning_session:
        await safe_reply(
            message,
            "📚 You don't have an active study topic.\n\n"
            "Start one first with:\n\n"
            "/study"
        )
        return
        
    thinking = await message.answer("📝 Preparing your written test questions...")
    
    try:
        prompt = (
            f"You are preparing a formal written test in {lang} for a Grade {student.grade} student.\n"
            f"Subject: '{learning_session.subject}', Topic: '{learning_session.topic}'.\n\n"
            f"STRICT FORMATTING REQUIREMENTS:\n"
            f"- Output EXACTLY 3 clear, high-yield conceptual exam questions.\n"
            f"- DO NOT write any introductory welcome messages, background greetings, filler, or instructions.\n"
            f"- DO NOT write any closing remarks, motivational quotes, or outro text.\n"
            f"- DO NOT provide solutions, answers, or hints.\n"
            f"- Format directly as:\n"
            f"1. [Question 1 text]\n\n"
            f"2. [Question 2 text]\n\n"
            f"3. [Question 3 text]"
        )
        history = await conversation_service.get_history(tid)
        types_history = [
            types.Content(
                role="user" if h.role == "user" else "model",
                parts=[types.Part.from_text(text=h.message)]
            )
            for h in history
        ]
        
        test_content, _, _ = await gemini_service.ask_gemini_with_profile(
            prompt, types_history, student, learning_session
        )
        
        await state.set_state(ActionStates.waiting_for_test_answer)
        await state.update_data(
            test_questions=test_content,
            session_id=learning_session.id,
            subject=learning_session.subject,
            topic=learning_session.topic,
            telegram_id=tid
        )
        
        await safe_edit(
            thinking,
            f"📝 *Written Test: {learning_session.topic}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{test_content.strip()}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ _Type your answers in a reply message and send._"
        )
        
    except Exception as e:
        logging.error(f"Error starting test: {e}", exc_info=True)
        await safe_edit(thinking, "⚠️ Failed to prepare test questions. Please try again in a moment.")

@router.callback_query(F.data == "action_test", StateFilter(None))
@router.callback_query(F.data == "menu_test", StateFilter(None))
async def action_test_callback(callback: CallbackQuery, state: FSMContext):
    """Processes the test callback button."""
    try:
        await callback.answer()
    except Exception:
        pass
    await test_start(callback.message, state, telegram_id=callback.from_user.id)

@router.message(ActionStates.waiting_for_test_answer)
async def process_test_answer(message: Message, state: FSMContext):
    """Evaluates student's written test answers and stores the results."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    learning_session = await learning_service.get_active_session(telegram_id)
    
    data = await state.get_data()
    questions = data.get("test_questions", "3 questions")
    subject = data.get("subject", learning_session.subject if learning_session else "General")
    topic = data.get("topic", learning_session.topic if learning_session else "Overview")
    session_id = data.get("session_id", learning_session.id if learning_session else None)
    await state.clear()
    
    thinking = await message.answer(t("test_evaluating", lang))
    
    try:
        # Grade test with structured response
        score, letter_grade, strengths, weaknesses, corrections, recommendations, feedback = (
            await gemini_service.grade_written_test(
                questions_text=questions,
                student_answers=message.text or "",
                student=student,
                subject=subject,
                topic=topic
            )
        )
        
        # Save to test_results table
        await asyncio.to_thread(
            test_repo.save_test_result,
            telegram_id=telegram_id,
            subject=subject,
            topic=topic,
            questions_text=questions,
            student_answers=message.text or "",
            score=score,
            max_score=10,
            letter_grade=letter_grade,
            feedback=feedback,
            learning_session_id=session_id
        )
        
        # Save to conversation history
        await conversation_service.add_message(telegram_id, "user", f"[Test Answers]: {message.text}")
        await conversation_service.add_message(telegram_id, "assistant", f"[Test Grading]: {feedback}")
        
        await safe_edit(
            thinking,
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💯 *Test Evaluation Results*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{feedback}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Use /test to try again or /quiz for MCQ practice",
            reply_markup=get_study_actions_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error grading test: {e}", exc_info=True)
        await safe_edit(thinking, "⚠️ Failed to grade your answers. Please try again.")

@router.message(Command("short_note"), StateFilter(None))
@router.message(F.text.in_(["📖 Short Notes", "📖 አጫጭር ማስታወሻዎች", "📖 Yaadannoo Gabaabaa"]), StateFilter(None))
async def short_note_start(message: Message, telegram_id: Optional[int] = None):
    """Generates a concise study guide summary."""
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    if not student:
        await message.answer("Please register first by sending /start.")
        return
        
    lang = student.preferred_language or "English"
    learning_session = await learning_service.get_active_session(tid)
    if not learning_session:
        await safe_reply(
            message,
            "📚 You don't have an active study topic.\n\n"
            "Start one first with:\n\n"
            "/study"
        )
        return
        
    thinking = await message.answer(t("notes_generating", lang))
    
    try:
        prompt = (
            f"Write a concise revision short notes summary in {lang} for a Grade {student.grade} student on:\n"
            f"Topic: '{learning_session.topic}' (Subject: '{learning_session.subject}').\n\n"
            f"STRICT RULES:\n"
            f"- DO NOT write any intro greeting (e.g., 'Welcome', 'Here are your notes').\n"
            f"- DO NOT write any outro text (e.g., 'Good luck studying', 'Hope this helps').\n"
            f"- Provide ONLY high-yield bullet points, core definitions, key formulas, and crucial exam facts.\n"
            f"- Use clean Markdown with bold keywords."
        )
        history = await conversation_service.get_history(tid)
        types_history = [
            types.Content(
                role="user" if h.role == "user" else "model",
                parts=[types.Part.from_text(text=h.message)]
            )
            for h in history
        ]
        
        note_content, _, _ = await gemini_service.ask_gemini_with_profile(
            prompt, types_history, student, learning_session
        )
        
        await conversation_service.add_message(tid, "assistant", f"[Short Note]: {note_content}")
        
        await safe_edit(
            thinking,
            f"📖 *Short Notes: {learning_session.topic}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{note_content.strip()}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Use /quiz or /test to practice this topic._",
            reply_markup=get_study_actions_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error generating short note: {e}", exc_info=True)
        await safe_edit(thinking, "⚠️ Failed to generate short notes. Please try again.")

@router.callback_query(F.data == "action_note", StateFilter(None))
@router.callback_query(F.data == "menu_notes", StateFilter(None))
async def action_note_callback(callback: CallbackQuery):
    """Processes the short note callback button."""
    try:
        await callback.answer()
    except Exception:
        pass
    await short_note_start(callback.message, telegram_id=callback.from_user.id)

@router.message(Command("personalize"), StateFilter(None))
async def personalize_start(message: Message, telegram_id: Optional[int] = None):
    """Displays the personalization configuration card."""
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    if not student:
        await message.answer("Please register first by sending /start.")
        return
        
    lang = student.preferred_language or "English"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Change Grade", callback_data="change_grade")],
        [InlineKeyboardButton(text="🌐 Change Language", callback_data="change_lang")]
    ])
    await safe_reply(
        message,
        f"⚙️ *Personalization & Learning Profile*\n\n"
        f"👤 *Grade Level:* {student.grade or 'Not Set'}\n"
        f"🌐 *Language:* {student.preferred_language or 'English'}\n\n"
        f"Select an option below to update your settings:",
        reply_markup=kb
    )

@router.callback_query(F.data.in_(["action_personalize", "menu_personalize"]), StateFilter(None))
async def action_personalize_callback(callback: CallbackQuery):
    """Handles personalization callback button."""
    try:
        await callback.answer()
    except Exception:
        pass
    await personalize_start(callback.message, telegram_id=callback.from_user.id)

@router.callback_query(F.data == "menu_language", StateFilter(None))
async def menu_language_callback(callback: CallbackQuery):
    """Directly opens language switcher from main menu."""
    try:
        await callback.answer()
    except Exception:
        pass
    await change_lang_callback(callback)

@router.callback_query(F.data == "change_grade", StateFilter(None))
async def change_grade_callback(callback: CallbackQuery):
    """Displays grade selection keyboard for personalization."""
    await callback.message.edit_text(
        "🎓 *Select your new grade level:*",
        parse_mode="Markdown",
        reply_markup=get_grades_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "change_lang", StateFilter(None))
async def change_lang_callback(callback: CallbackQuery):
    """Displays language selection keyboard for personalization."""
    await callback.message.edit_text(
        "🌐 *Select your preferred language:*",
        parse_mode="Markdown",
        reply_markup=get_languages_keyboard()
    )
    await callback.answer()

@router.message(Command("test_history"), StateFilter(None))
async def test_history_start(message: Message, telegram_id: Optional[int] = None):
    """Displays historical written test scores and feedback."""
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    if not student:
        await message.answer("Please register first by sending /start.")
        return
        
    results = await asyncio.to_thread(test_repo.get_student_test_results, tid, 5)
    if not results:
        await safe_reply(
            message,
            "📝 *Written Test History*\n\n"
            "You haven't taken any written tests yet.\n"
            "Use /test to take your first test!"
        )
        return
        
    lines = ["📝 *Recent Written Test Results:*\n━━━━━━━━━━━━━━━━━━━━"]
    for r in results:
        time_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else "Recent"
        lines.append(
            f"• *{r.subject} → {r.topic}*\n"
            f"  Score: *{r.score}/{r.max_score}* (Grade: *{r.letter_grade}*) | Date: {time_str}\n"
            f"  Feedback: _{r.feedback[:100]}..._\n"
        )
        
    await safe_reply(
        message,
        "\n".join(lines),
        reply_markup=get_study_actions_keyboard()
    )

test_history_command = test_history_start

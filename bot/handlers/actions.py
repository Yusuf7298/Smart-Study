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

@router.message(Command("test"))
@router.message(F.text.in_(["📝 Written Test", "📝 የጽሁፍ ፈተና", "📝 Qormaata Barreeffamaa"]))
async def test_start(message: Message, state: Optional[FSMContext] = None, telegram_id: Optional[int] = None):
    if state:
        await state.clear()
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
        registered_courses = student.selected_courses if student else []
        from bot.handlers.study import get_registered_subjects_keyboard
        await safe_reply(
            message,
            "📚 Please choose one of your registered subjects to take a written test:",
            reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
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
        
        if state:
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
            f"📝 Written Test: {learning_session.topic}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{test_content.strip()}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✍️ _Type your answers in a reply message and send._"
        )
        
    except Exception as e:
        logging.error(f"Error starting test: {e}", exc_info=True)
        await safe_edit(thinking, "⚠️ Failed to prepare test questions. Please try again in a moment.")

@router.callback_query(F.data == "action_test")
@router.callback_query(F.data == "menu_test")
async def action_test_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    await test_start(callback.message, state, telegram_id=callback.from_user.id)

@router.message(ActionStates.waiting_for_test_answer)
async def process_test_answer(message: Message, state: FSMContext):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    data = await state.get_data()
    test_questions = data.get("test_questions", "")
    learning_session_id = data.get("session_id")
    subject = data.get("subject", "General")
    topic = data.get("topic", "General")
    
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language or "English" if student else "English"
    
    thinking = await message.answer("📊 Grading your written test answers...")
    
    try:
        answers_text = message.text or ""
        score, letter_grade, strengths, weaknesses, corrections, recommendations, feedback = (
            await gemini_service.grade_written_test(
                questions_text=test_questions,
                student_answers=answers_text,
                student=student, # type: ignore
                subject=subject,
                topic=topic
            )
        )
        
        await asyncio.to_thread(
            test_repo.save_test_result,
            telegram_id=telegram_id,
            learning_session_id=learning_session_id,
            subject=subject,
            topic=topic,
            questions_text=test_questions,
            student_answers=answers_text,
            score=score,
            max_score=10,
            letter_grade=letter_grade,
            feedback=feedback
        )
        
        await state.clear()
        
        await safe_edit(
            thinking,
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💯 Test Evaluation Results\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{feedback}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Use /test to try again or /quiz for MCQ practice",
            reply_markup=get_study_actions_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error grading test: {e}", exc_info=True)
        await safe_edit(thinking, "⚠️ Failed to grade your test answers. Please try again.")

@router.message(Command("short_note"))
@router.message(F.text.in_(["📖 Short Notes", "📖 አጫጭር ማስታወሻዎች", "📖 Yaadannoo Gabaabaa"]))
async def short_note_start(message: Message, state: Optional[FSMContext] = None, telegram_id: Optional[int] = None):
    if state:
        await state.clear()
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
        registered_courses = student.selected_courses if student else []
        from bot.handlers.study import get_registered_subjects_keyboard
        await safe_reply(
            message,
            "📚 Please choose one of your registered subjects to generate short notes:",
            reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
        )
        return
        
    thinking = await message.answer(t("notes_generating", lang))
    
    try:
        grade_str = str(student.grade) if student.grade is not None else "12"
        prompt = (
            f"You are the master Ethiopian teacher writing comprehensive, memory-first revision short notes in {lang} for a Grade {grade_str} student.\n"
            f"Subject: '{learning_session.subject}'\n"
            f"Topic: '{learning_session.topic}'\n\n"
            f"STRICT RULES:\n"
            f"- DO NOT write any intro greetings or pleasantries.\n"
            f"- DO NOT write any outro remarks or filler.\n"
            f"- Organize the notes with standard educational anchors:\n"
            f"  • 📌 Core Definition & Mechanism: Clear, precise definition and working principles.\n"
            f"  • 💡 Simple Idea: Intuitive real-world explanation.\n"
            f"  • 🧠 Memory Trick / Key Anchor: Mnemonic, formula, or mental hook.\n"
            f"  • 🔎 Key Equations & Step-by-Step Examples: Formulas, reaction mechanisms, or worked steps.\n"
            f"  • ⚠️ Common Mistakes: Tricky traps or exam misconceptions.\n"
            f"  • 🎯 High-Yield Exam Takeaways: Must-know facts for examinations.\n"
            f"- Use clean Markdown with bold keywords and structured bullet points."
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
            f"📖 Short Notes: {learning_session.topic}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{note_content.strip()}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Use /quiz or /test to practice this topic._",
            reply_markup=get_study_actions_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Error generating short note: {e}", exc_info=True)
        await safe_edit(thinking, "⚠️ Failed to generate short notes. Please try again.")

@router.callback_query(F.data == "action_note")
@router.callback_query(F.data == "menu_notes")
async def action_note_callback(callback: CallbackQuery, state: FSMContext):
    """Processes the short note callback button."""
    await state.clear()
    try:
        await callback.answer()
    except Exception:
        pass
    await short_note_start(callback.message, state, telegram_id=callback.from_user.id)

@router.message(Command("personalize"))
async def personalize_start(message: Message, state: Optional[FSMContext] = None, telegram_id: Optional[int] = None):
    """Displays the personalization configuration card."""
    if state:
        await state.clear()
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
        f"⚙️ Personalization & Learning Profile\n\n"
        f"👤 Grade Level: {student.grade or 'Not Set'}\n"
        f"🌐 Language: {student.preferred_language or 'English'}\n\n"
        f"Select an option below to update your settings:",
        reply_markup=kb
    )

@router.callback_query(F.data.in_(["action_personalize", "menu_personalize"]))
async def action_personalize_callback(callback: CallbackQuery, state: FSMContext):
    """Handles personalization callback button."""
@router.callback_query(F.data == "menu_language", StateFilter(None))
async def menu_language_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    await change_lang_callback(callback)

@router.callback_query(F.data == "change_grade")
async def change_grade_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    if student and student.approval_status == 'APPROVED':
        support_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Contact Support (@Cs1At07)", url="https://t.me/Cs1At07")],
            [InlineKeyboardButton(text="🔙 Back to Personalize", callback_data="action_personalize")]
        ])
        await safe_edit(
            callback.message,
            "🔒 Grade Level & Courses Locked\n━━━━━━━━━━━━━━━━━━━━\n"
            "Your registered grade is locked for security and curriculum consistency.\n\n"
            "To request a grade or course change, please contact support:\n"
            "• 💬 Telegram: [@Cs1At07](https://t.me/Cs1At07)\n"
            "• 📱 Phone: `0928892344`",
            reply_markup=support_kb
        )
        return
        
    await safe_edit(
        callback.message,
        "🎓 Select your new grade level:",
        reply_markup=get_grades_keyboard()
    )

@router.callback_query(F.data == "change_lang")
async def change_lang_callback(callback: CallbackQuery):
    """Displays language selection keyboard for personalization."""
    try:
        await callback.answer()
    except Exception:
        pass
    await safe_edit(
        callback.message, # type: ignore
        "🌐 Select your preferred language:",
        reply_markup=get_languages_keyboard()
    )

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
            "📝 Written Test History\n\n"
            "You haven't taken any written tests yet.\n"
            "Use /test to take your first test!"
        )
        return
        
    lines = ["📝 Recent Written Test Results:\n━━━━━━━━━━━━━━━━━━━━"]
    for r in results:
        time_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else "Recent"
        lines.append(
            f"• {r.subject} → {r.topic}\n"
            f"  Score: {r.score}/{r.max_score} (Grade: {r.letter_grade}) | Date: {time_str}\n"
            f"  Feedback: _{r.feedback[:100]}..._\n"
        )
        
    await safe_reply(
        message,
        "\n".join(lines),
        reply_markup=get_study_actions_keyboard()
    )

test_history_command = test_history_start

@router.callback_query(F.data == "menu_back")
async def menu_back_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    from bot.handlers.start import send_student_dashboard
    await state.clear()
    await send_student_dashboard(callback, telegram_id)


import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from google.genai import types
from aiogram.fsm.context import FSMContext
from bot.services import student_service, conversation_service, learning_service, quiz_service
from bot.services.gemini import ask_gemini_with_profile
from bot.services.i18n import t
from bot.keyboards.study_input import get_study_actions_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

def get_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    """Returns confirmation buttons for clearing chat history."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes, clear", callback_data="clear_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="clear_cancel")
        ]
    ])

@router.message(Command("cancel"))
async def cancel_action(message: Message, state: FSMContext):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    # 1. Check for active quiz session
    active_quiz = await quiz_service.get_active_quiz(telegram_id)
    if active_quiz:
        await quiz_service.cancel_quiz(telegram_id)
        await safe_reply(
            message,
            "❌ *Quiz Cancelled*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Your quiz result was not counted.\n"
            "Your study session is still saved.\n\n"
            "💡 Use /quiz to start a new one, or continue studying."
        )
        return

    # 2. Check for active learning session
    active_session = await learning_service.get_active_session(telegram_id)
    if active_session:
        await learning_service.deactivate_sessions(telegram_id)
        await safe_reply(
            message,
            t("study_stopped", lang)
        )
        return

    # 3. Check for active FSM state
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await safe_reply(message, "❌ Cancelled.")
        return

    # 4. Default fallback
    await safe_reply(message, "Nothing to cancel.")

@router.message(Command("newchat"), StateFilter(None))
async def new_chat(message: Message):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    try:
        await conversation_service.clear_history(telegram_id)
        await safe_reply(
            message,
            "🆕 *New Chat Started!*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Your conversation history has been cleared.\n"
            "Your study sessions and profile are still saved."
        )
    except Exception as e:
        logging.error(f"Error starting new session for user {telegram_id}: {e}", exc_info=True)
        await safe_reply(message, "❌ Error starting new session. Please try again.")

@router.message(Command("clearchat"), StateFilter(None))
async def clear_chat(message: Message):
    await safe_reply(
        message,
        "Are you sure you want to clear your conversation history?",
        reply_markup=get_clear_confirm_keyboard()
    )

@router.callback_query(F.data == "clear_confirm")
async def clear_confirm_callback(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    try:
        await conversation_service.clear_history(telegram_id)
        await safe_edit(callback.message, "🧹 Your conversation history has been cleared.") # type: ignore
    except Exception as e:
        logging.error(f"Error clearing conversation history for user {telegram_id}: {e}", exc_info=True)
        await safe_edit(callback.message, "❌ Error clearing history. Please try again.") # type: ignore
    await callback.answer()

@router.message(Command("clear"))
@router.message(F.text.in_(["🧹 Clear", "Clear", "🧹 Chat አጽዳ", "🧹 Qulqulleessi", "🧹 Clear Chat", "🧹 አጽዳ", "አጽዳ"]))
async def reply_clear_button_handler(message: Message, state: FSMContext):
    """Handles the Clear reply button: resets chat history, cancels active sessions and FSM."""
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    try:
        await conversation_service.clear_history(telegram_id)
        await learning_service.deactivate_sessions(telegram_id)
        await quiz_service.cancel_quiz(telegram_id)
    except Exception as e:
        logging.warning(f"Error resetting state on Clear button: {e}")
        
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    from bot.keyboards.main_menu import get_main_reply_keyboard
    
    await safe_reply(
        message,
        "🧹 *Chat History & Session Cleared!*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "All previous conversation memory and active study sessions have been reset.\n"
        "You can now start a fresh conversation or tap *📱 Menu* to study.",
        reply_markup=get_main_reply_keyboard(lang)
    )

@router.callback_query(F.data == "clear_cancel")
async def clear_cancel_callback(callback: CallbackQuery):
    await safe_edit(callback.message, "❌ Clear chat cancelled.") # type: ignore
    await callback.answer()

@router.message(F.text.in_(["🤖 AI Tutor", "🤖 AI አስተማሪ", "🤖 Barsiisaa AI"]))
async def ai_tutor_menu_trigger(message: Message, state: FSMContext):
    """Greeting prompt when AI Tutor button is clicked."""
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    await safe_reply(
        message,
        "🤖 *AI Tutor Mode Active*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ask me any question or homework problem! I'll guide you step-by-step to understand the solution."
    )

@router.message()
async def chat(message: Message, state: Optional[FSMContext] = None):
    if not message.text:
        return

    # Ignore command messages
    if message.text.startswith("/"):
        return

    if state:
        current_state = await state.get_state()
        if current_state and (current_state.startswith("RegistrationStates:") or current_state.startswith("AdminStates:")):
            return
        await state.clear()

    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    question = message.text

    student = await student_service.get_student(telegram_id)
    if not student:
        first_name = message.from_user.first_name if message.from_user else None
        username = message.from_user.username if message.from_user else None
        student = await student_service.register_student(telegram_id, first_name, username)

    lang = student.preferred_language or "English"
    thinking_msg = await message.answer(t("tutor_thinking", lang))

    try:
        # 1. Load the last 20 messages of history
        raw_history = await conversation_service.get_history(telegram_id, limit=20)
        
        # 2. Rebuild types.Content history
        types_history = []
        for msg in raw_history:
            role = "user" if msg.role == "user" else "model"
            types_history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.message)]
                )
            )
        
        # 3. Load active learning session if one exists
        session = await learning_service.get_active_session(telegram_id)

        # 4. Invoke Gemini with student profile and learning context
        answer, extracted_grade, extracted_language = await ask_gemini_with_profile(
            question, types_history, student, session
        )
        
        # 5. Automatically update student profile if a new grade or language is detected
        if extracted_grade is not None and str(extracted_grade) != str(student.grade):
            if not student.grade or student.approval_status != 'APPROVED':
                await student_service.update_grade(telegram_id, str(extracted_grade))
            
        if extracted_language is not None and extracted_language != student.preferred_language:
            await student_service.update_language(telegram_id, extracted_language)

        # 6. Save current turn to the database
        await conversation_service.add_message(telegram_id, "user", question)
        await conversation_service.add_message(telegram_id, "assistant", answer)
        
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        # 7. Reply with the generated answer
        if session:
            await safe_reply(message, answer, reply_markup=get_study_actions_keyboard())
        else:
            await safe_reply(message, answer)

    except Exception as e:
        logging.error(f"Error handling question for user {telegram_id}: {e}", exc_info=True)
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await message.answer(
            "⚠️ *Connection Error*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "I'm having trouble connecting to the AI right now.\n\n"
            "Please try again in a moment.",
            parse_mode="Markdown"
        )
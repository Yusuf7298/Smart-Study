from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services import student_service, progress_service
from bot.services.i18n import t
from bot.utils import safe_reply

router = Router()

@router.message(Command("progress"), StateFilter(None))
@router.message(F.text.in_(["📊 My Progress", "📊 የኔ ውጤት/እድገት", "📊 Guddina Koo"]), StateFilter(None))
async def show_progress_message(message: Message, telegram_id: Optional[int] = None):
    """Displays the student's comprehensive learning progress dashboard."""
    tid = telegram_id or (message.from_user.id if message.from_user else None)
    if not tid:
        return
        
    student = await student_service.get_student(tid)
    if not student:
        await message.answer("Please register first by sending /start.")
        return
        
    lang = student.preferred_language or "English"
    stats = await progress_service.get_student_progress(tid)
    
    text = t(
        "progress_title",
        lang,
        name=student.first_name or "Student",
        grade=student.grade or "Not Set",
        language=lang,
        lessons_count=stats["lessons_count"],
        quizzes_count=stats["quizzes_count"],
        quiz_avg_pct=stats["quiz_avg_pct"],
        total_correct=stats["total_correct"],
        total_questions=stats["total_questions"],
        tests_count=stats["tests_count"],
        test_avg_score=stats["test_avg_score"],
        pdf_count=stats["pdf_count"],
        active_topic=stats["active_topic"]
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_study", lang), callback_data="menu_study"),
            InlineKeyboardButton(text=t("btn_quiz", lang), callback_data="menu_quiz")
        ]
    ])
    await safe_reply(message, text, reply_markup=kb)

@router.callback_query(F.data == "menu_progress", StateFilter(None))
async def progress_callback(callback: CallbackQuery):
    """Callback trigger for progress dashboard from main menu."""
    await show_progress_message(callback.message, telegram_id=callback.from_user.id)
    await callback.answer()

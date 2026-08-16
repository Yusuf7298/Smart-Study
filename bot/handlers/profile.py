import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services import student_service, learning_service
from bot.services.i18n import t
from bot.handlers.registration import get_grades_keyboard, get_languages_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_grade = State()
    waiting_for_language = State()

def get_profile_inline_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    """Returns profile settings keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("profile_btn_change_grade", lang), callback_data="profile_change_grade"),
            InlineKeyboardButton(text=t("profile_btn_change_lang", lang), callback_data="profile_change_language")
        ],
        [
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="profile_cancel")
        ]
    ])

async def send_profile_message(message: Message, telegram_id: int):
    """Sends the formatted profile card to the student."""
    student = await student_service.get_student(telegram_id)
    if not student:
        first_name = message.from_user.first_name if message.from_user else None
        username = message.from_user.username if message.from_user else None
        student = await student_service.register_student(telegram_id, first_name, username)

    lang = student.preferred_language or "English"
    grade_str = f"{student.grade}" if student.grade is not None else "Not Set"
    member_since = student.created_at.strftime("%Y-%m-%d")
    name_str = student.first_name or student.username or "Student"

    active_session = await learning_service.get_active_session(telegram_id)
    topic_str = f"{active_session.subject} → {active_session.topic}" if active_session else "None"

    text = t(
        "profile_title",
        lang,
        name=name_str,
        telegram_id=telegram_id,
        grade=grade_str,
        language=lang,
        registered_date=member_since,
        topic=topic_str
    )
    await safe_reply(message, text, reply_markup=get_profile_inline_keyboard(lang))

@router.message(Command("profile"), StateFilter(None))
@router.message(F.text.in_(["👤 My Profile", "👤 የኔ መገለጫ", "👤 Piroofayilii Koo"]), StateFilter(None))
async def show_profile(message: Message):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
    await send_profile_message(message, telegram_id)

@router.callback_query(F.data == "menu_profile", StateFilter(None))
async def menu_profile_callback(callback: CallbackQuery):
    await send_profile_message(callback.message, callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data == "profile_change_grade", StateFilter(None))
async def change_grade_callback(callback: CallbackQuery, state: FSMContext):
    """Prompts grade selection using the standard grade keyboard."""
    from bot.handlers.registration import RegistrationStates
    await state.set_state(RegistrationStates.waiting_for_grade)
    await safe_edit(
        callback.message,
        "🎓 Select your new grade level or academic status:",
        reply_markup=get_grades_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_change_language", StateFilter(None))
async def change_language_callback(callback: CallbackQuery, state: FSMContext):
    """Prompts language selection using the standard language keyboard."""
    from bot.handlers.registration import RegistrationStates
    await state.set_state(RegistrationStates.waiting_for_language)
    await safe_edit(
        callback.message,
        "🌐 Select your new preferred language:",
        reply_markup=get_languages_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_cancel")
async def cancel_profile_callback(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    await safe_edit(callback.message, "❌ Profile action cancelled.")
    await callback.answer()

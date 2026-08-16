import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service
from bot.services.i18n import t

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_grade = State()
    waiting_for_language = State()
    waiting_for_confirm = State()

def get_grades_keyboard() -> InlineKeyboardMarkup:
    """Returns an inline keyboard for grades 5-12, College, and University."""
    keyboard = [
        [
            InlineKeyboardButton(text="Grade 5", callback_data="reg_grade_5"),
            InlineKeyboardButton(text="Grade 6", callback_data="reg_grade_6")
        ],
        [
            InlineKeyboardButton(text="Grade 7", callback_data="reg_grade_7"),
            InlineKeyboardButton(text="Grade 8", callback_data="reg_grade_8")
        ],
        [
            InlineKeyboardButton(text="Grade 9", callback_data="reg_grade_9"),
            InlineKeyboardButton(text="Grade 10", callback_data="reg_grade_10")
        ],
        [
            InlineKeyboardButton(text="Grade 11", callback_data="reg_grade_11"),
            InlineKeyboardButton(text="Grade 12", callback_data="reg_grade_12")
        ],
        [
            InlineKeyboardButton(text="🏫 College", callback_data="reg_grade_College"),
            InlineKeyboardButton(text="🎓 University", callback_data="reg_grade_University")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_languages_keyboard() -> InlineKeyboardMarkup:
    """Returns an inline keyboard for language selection."""
    keyboard = [
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="reg_lang_English"),
            InlineKeyboardButton(text="🟢 Afaan Oromo", callback_data="reg_lang_Afaan Oromo")
        ],
        [
            InlineKeyboardButton(text="🇪🇹 አማርኛ (Amharic)", callback_data="reg_lang_Amharic")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    """Returns an inline keyboard for confirming or cancelling registration."""
    keyboard = [
        [
            InlineKeyboardButton(text=t("reg_btn_submit", lang), callback_data="reg_confirm_submit"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="reg_confirm_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Processes student name input and asks for grade."""
    name = message.text.strip() if message.text else ""
    if not name:
        await message.answer("Please enter a valid full name:")
        return
        
    await state.update_data(full_name=name)
    await state.set_state(RegistrationStates.waiting_for_grade)
    
    await message.answer(
        "🎓 *Select your grade level or academic status:*",
        parse_mode="Markdown",
        reply_markup=get_grades_keyboard()
    )

@router.callback_query(F.data.startswith("reg_grade_"), RegistrationStates.waiting_for_grade)
async def process_grade_callback(callback: CallbackQuery, state: FSMContext):
    """Processes student grade selection callback and asks for preferred language."""
    telegram_id = callback.from_user.id
    grade_val = callback.data.split("reg_grade_")[1]
    
    # Check if student is already an approved student updating their grade via profile
    student = await student_service.get_student(telegram_id)
    if student and student.approval_status == 'APPROVED':
        await student_service.update_grade(telegram_id, grade_val)
        await state.clear()
        lang = student.preferred_language or "English"
        await callback.message.edit_text(f"✅ Grade level updated to *Grade {grade_val}*!", parse_mode="Markdown")
        await callback.answer()
        return
        
    await state.update_data(grade=grade_val)
    await state.set_state(RegistrationStates.waiting_for_language)
    
    await callback.message.edit_text(
        "🌐 *Select your preferred language:*",
        parse_mode="Markdown",
        reply_markup=get_languages_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("reg_lang_"), RegistrationStates.waiting_for_language)
async def process_language_callback(callback: CallbackQuery, state: FSMContext):
    """Processes language selection callback and shows summary verification card."""
    telegram_id = callback.from_user.id
    lang_val = callback.data.split("reg_lang_")[1]
    
    # Check if student is already an approved student updating their language via profile
    student = await student_service.get_student(telegram_id)
    if student and student.approval_status == 'APPROVED':
        await student_service.update_language(telegram_id, lang_val)
        await state.clear()
        
        from bot.handlers.start import send_student_dashboard
        await callback.message.edit_text(f"✅ Language updated to *{lang_val}*!", parse_mode="Markdown")
        await send_student_dashboard(callback.message, telegram_id)
        await callback.answer()
        return
        
    await state.update_data(language=lang_val)
    await state.set_state(RegistrationStates.waiting_for_confirm)
    
    data = await state.get_data()
    summary = t(
        "reg_summary",
        lang_val,
        name=data.get('full_name', 'Student'),
        grade=data.get('grade', 'Not Set'),
        language=lang_val
    )
    
    await callback.message.edit_text(
        summary,
        parse_mode="Markdown",
        reply_markup=get_confirm_keyboard(lang_val)
    )
    await callback.answer()

@router.callback_query(F.data == "reg_confirm_cancel", RegistrationStates.waiting_for_confirm)
async def process_cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Cancels registration FSM sequence."""
    await state.clear()
    await callback.message.edit_text(
        t("reg_cancelled", "English"),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "reg_confirm_submit", RegistrationStates.waiting_for_confirm)
async def process_submit_callback(callback: CallbackQuery, state: FSMContext):
    """Saves pending registration and alerts administrators."""
    data = await state.get_data()
    await state.clear()
    
    telegram_id = callback.from_user.id
    first_name = data.get('full_name', 'Student')
    username = callback.from_user.username
    grade = data.get('grade', '12')
    language = data.get('language', 'English')
    
    # 1. Save in database with status PENDING
    await student_service.register_student_pending(
        telegram_id, first_name, username, grade, language
    )
    
    # 2. Inform student
    await callback.message.edit_text(
        t("reg_submitted", language),
        parse_mode="Markdown"
    )
    await callback.answer()
    
    # 3. Notify Admin IDs
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve_{telegram_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject_{telegram_id}")
        ]
    ])
    
    reg_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    admin_message = (
        "🔔 *New Student Registration Request*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {first_name}\n"
        f"🆔 *Telegram ID:* `{telegram_id}`\n"
        f"🏷️ *Username:* @{username if username else 'N/A'}\n"
        f"🎓 *Grade:* {grade}\n"
        f"🌐 *Language:* {language}\n"
        f"📅 *Registered:* {reg_date}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Please review and approve or reject:"
    )
    
    for admin_id in config.ADMIN_IDS:
        try:
            await callback.bot.send_message(admin_id, admin_message, parse_mode="Markdown", reply_markup=admin_kb)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

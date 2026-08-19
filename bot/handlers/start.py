from typing import Optional, Union
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from bot.services import student_service, learning_service
from bot.services.i18n import t
from bot.handlers.registration import RegistrationStates
from bot.keyboards.main_menu import get_main_menu_keyboard, get_main_reply_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

async def send_student_dashboard(target: Union[Message, CallbackQuery, Bot], telegram_id: int):
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    name = student.first_name if student and student.first_name else "Student"
    grade_str = student.grade if student and student.grade else "Not Set"
    
    active_session = await learning_service.get_active_session(telegram_id)
    topic_str = f"{active_session.subject} → {active_session.topic}" if active_session else "None (Select /study)"
    
    courses_formatted = ", ".join(student.selected_courses) if student and student.selected_courses else "All Subjects"
    
    dashboard_text = (
        f"🎓 Ethio Smart Study — Main Dashboard\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, {name}!\n\n"
        f"🎓 Grade: {grade_str}\n"
        f"🌐 Language: {lang}\n"
        f"📚 Enrolled Courses: {courses_formatted}\n"
        f"📌 Active Topic: {topic_str}\n\n"
        f"Select an option below to start learning:"
    )
    
    if isinstance(target, Bot):
        await target.send_message(
            chat_id=telegram_id,
            text=dashboard_text,
            parse_mode="HTML",
            reply_markup=get_main_reply_keyboard(lang)
        )
        await target.send_message(
            chat_id=telegram_id,
            text="📱 Quick Actions:",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(lang)
        )
    else:
        msg = target.message if isinstance(target, CallbackQuery) else target
        await safe_reply(
            target,
            dashboard_text,
            reply_markup=get_main_menu_keyboard(lang)
        )

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    if telegram_id in config.ADMIN_IDS:
        from bot.handlers.admin import admin_command
        await state.clear()
        await admin_command(message)
        return

    student = await student_service.get_student(telegram_id)
    if not student or student.approval_status in ['REGISTRATION_PENDING', 'REJECTED']:
        await state.set_state(RegistrationStates.waiting_for_name)
        await safe_reply(
            message,
            t("reg_welcome", "English")
        )
        return

    lang = student.preferred_language or "English"
    if student.approval_status != 'APPROVED':
        await safe_reply(
            message,
            t("reg_pending_wait", lang)
        )
    else:
        await send_student_dashboard(message, telegram_id)

@router.message(Command("menu"))
@router.message(F.text.in_(["📱 Menu", "Menu", "📱 Main Menu", "📱 ዋና ማውጫ", "📱 Baafata Guddaa", "📱 Baafata", "ሜኑ"]))
async def menu_command(message: Message, state: Optional[FSMContext] = None):
    if state:
        await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    if telegram_id in config.ADMIN_IDS:
        from bot.handlers.admin import admin_command
        await admin_command(message)
        return
        
    await send_student_dashboard(message, telegram_id)

@router.message(Command("back"))
@router.message(F.text.in_(["🔙 Back", "Back", "🔙 ወደ ኋላ", "🔙 Duubatti", "ወደ ኋላ", "Duubatti"]))
async def back_command(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    if telegram_id in config.ADMIN_IDS:
        from bot.handlers.admin import admin_command
        await admin_command(message)
        return
        
    await learning_service.deactivate_sessions(telegram_id)
    try:
        from bot.services import quiz_service
        await quiz_service.cancel_quiz(telegram_id)
    except Exception:
        pass
        
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        "🔙 Returned to Main Menu",
        reply_markup=get_main_menu_keyboard(lang)
    )

@router.message(Command("socials"))
@router.message(Command("follow"))
@router.message(F.text.in_(["🌟 Follow Us", "🌟 ተከተሉን (Socials)", "🌟 Nu Hordofaa (Socials)"]))
async def socials_command(message: Message):
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        t("socials_title", lang)
    )

@router.callback_query(F.data == "menu_socials")
async def socials_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        callback,
        t("socials_title", lang)
    )

@router.message(Command("support"))
@router.message(Command("contact"))
@router.message(F.text.in_(["📞 Support", "📞 ድጋፍ", "📞 Deeggarsa"]))
async def support_command(message: Message):
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        t("support_title", lang)
    )

@router.callback_query(F.data == "menu_support")
async def support_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        callback,
        t("support_title", lang)
    )

@router.message(Command("help"))
@router.message(F.text.in_(["ℹ️ Help", "ℹ️ እገዛ", "ℹ️ Gargaarsa"]))
async def help_command(message: Message):
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        t("help_title", lang)
    )

@router.callback_query(F.data == "menu_help")
async def help_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        callback,
        t("help_title", lang)
    )
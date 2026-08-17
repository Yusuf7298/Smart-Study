from aiogram import Router, F
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

async def send_student_dashboard(message: Message, telegram_id: int):
    """Sends the localized student main dashboard and keyboards."""
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    name = student.first_name if student and student.first_name else "Student"
    grade_str = student.grade if student and student.grade else "Not Set"
    
    active_session = await learning_service.get_active_session(telegram_id)
    topic_str = f"{active_session.subject} → {active_session.topic}" if active_session else "None (Select /study)"
    
    dashboard_text = t(
        "menu_title",
        lang,
        name=name,
        grade=grade_str,
        topic=topic_str
    )
    
    # Send persistent reply keyboard and inline menu
    await safe_reply(
        message,
        dashboard_text,
        reply_markup=get_main_menu_keyboard(lang)
    )

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return

    # Load student profile
    student = await student_service.get_student(telegram_id)
    if not student:
        # Start registration FSM
        await state.set_state(RegistrationStates.waiting_for_name)
        await safe_reply(
            message,
            t("reg_welcome", "English")
        )
        return

    # Branch start response based on approval status
    lang = student.preferred_language or "English"
    if student.approval_status == 'PENDING':
        await safe_reply(
            message,
            t("reg_pending_wait", lang)
        )
    elif student.approval_status == 'REJECTED':
        await safe_reply(
            message,
            t("reg_rejected", lang)
        )
    else:
        # Approved student: show main dashboard
        await send_student_dashboard(message, telegram_id)

@router.message(Command("menu"))
@router.message(F.text.in_(["📱 Main Menu", "📱 ዋና ማውጫ", "📱 Baafata Guddaa"]))
async def menu_command(message: Message):
    """Handles the /menu command."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
    await send_student_dashboard(message, telegram_id)

@router.message(Command("socials"))
@router.message(Command("follow"))
@router.message(F.text.in_(["🌟 Follow Us", "🌟 ተከተሉን (Socials)", "🌟 Nu Hordofaa (Socials)"]))
async def socials_command(message: Message):
    """Displays official social links and Islamic reminders channels."""
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        t("socials_title", lang)
    )

@router.callback_query(F.data == "menu_socials")
async def socials_callback(callback: CallbackQuery):
    """Callback for Follow Us / Socials from main menu."""
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
    """Displays contact and support info."""
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        t("support_title", lang)
    )

@router.callback_query(F.data == "menu_support")
async def support_callback(callback: CallbackQuery):
    """Callback for Support from main menu."""
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
@router.message(F.text.in_(["ℹ️ Help", "ℹ️ እርዳታ", "ℹ️ Gargaarsa", "❓ Help", "❓ እገዛ"]))
async def help_command(message: Message):
    """Displays the comprehensive user guide in the student's language."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    await safe_reply(message, t("help_title", lang))

@router.callback_query(F.data == "menu_help")
async def help_callback(callback: CallbackQuery):
    """Main menu callback for Help."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    await safe_reply(callback, t("help_title", lang))

@router.callback_query(F.data.in_(["menu_back", "menu_main", "main_menu"]))
async def back_to_main_menu_callback(callback: CallbackQuery):
    """Returns the student to the main dashboard menu."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    await send_student_dashboard(callback.message, telegram_id) # type: ignore
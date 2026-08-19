import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit

router = Router()

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()

@router.message(Command("feedback"))
@router.callback_query(F.data == "menu_feedback")
async def start_feedback_handler(event: Message | CallbackQuery, state: FSMContext):
    telegram_id = event.from_user.id
    message = event if isinstance(event, Message) else event.message

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except Exception:
            pass

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    await state.set_state(FeedbackStates.waiting_for_feedback)
    text = t("feedback_ask", lang)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="feedback_cancel")]
    ])
    await safe_reply(message, text, reply_markup=kb)

@router.callback_query(F.data == "feedback_cancel", FeedbackStates.waiting_for_feedback)
async def cancel_feedback_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    await state.clear()
    student = await student_service.get_student(callback.from_user.id)
    lang = student.preferred_language if student else "English"
    await safe_edit(callback.message, t("reg_cancelled", lang))

@router.message(FeedbackStates.waiting_for_feedback)
async def process_student_feedback(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    name_str = (student.first_name if student and student.first_name else message.from_user.full_name) or "Student"
    phone_str = student.phone_number if student and student.phone_number else "N/A"
    username_str = f"@{message.from_user.username}" if message.from_user and message.from_user.username else "@N/A"
    grade_str = f"Grade {student.grade}" if student and student.grade else "Not Set"
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    feedback_text = message.text or message.caption or "Uploaded Feedback Material (Photo/Document)"

    channel_post = (
        "💬 *NEW STUDENT FEEDBACK RECEIVED*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Student Name:* {name_str}\n"
        f"📱 *Phone:* `{phone_str}`\n"
        f"🏷️ *Username:* {username_str}\n"
        f"🆔 *Telegram ID:* `{telegram_id}`\n"
        f"🎓 *Grade:* {grade_str}\n"
        f"🌐 *Language:* {lang}\n"
        f"📅 *Timestamp:* `{submitted_at}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 *Feedback / Suggestion:*\n"
        f"\"{feedback_text}\""
    )

    target_channel = config.FEEDBACK_CHANNEL_ID or (config.ADMIN_IDS[0] if config.ADMIN_IDS else None)

    if target_channel:
        try:
            if message.photo:
                photo_file_id = message.photo[-1].file_id
                await message.bot.send_photo(
                    chat_id=target_channel,
                    photo=photo_file_id,
                    caption=channel_post
                )
            elif message.document:
                doc_file_id = message.document.file_id
                await message.bot.send_document(
                    chat_id=target_channel,
                    document=doc_file_id,
                    caption=channel_post
                )
            else:
                await message.bot.send_message(
                    chat_id=target_channel,
                    text=channel_post
                )
        except Exception as e:
            logging.error(f"Error forwarding feedback to channel {target_channel}: {e}", exc_info=True)

    await state.clear()
    await safe_reply(message, t("feedback_thanks", lang))

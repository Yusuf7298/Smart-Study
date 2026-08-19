import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import config
from bot.services import student_service
from bot.services.i18n import t

class ApprovalMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
            
        telegram_id = user.id
        state = data.get("state")
        current_state = await state.get_state() if state else None
        is_registering = isinstance(current_state, str) and current_state.startswith("RegistrationStates:")
        is_admin = telegram_id in config.ADMIN_IDS
        
        if isinstance(event, Message):
            command = event.text or event.caption or ""
            if command.startswith(("/start", "/help", "/support", "/contact", "/socials")) or is_registering:
                return await handler(event, data)
            if is_admin and command.startswith(("/admin", "/broadcast")):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            callback_data = event.data or ""
            if is_registering or callback_data.startswith(("reg_", "menu_support", "menu_language", "menu_socials", "menu_help")):
                return await handler(event, data)
            if is_admin and callback_data.startswith("admin_"):
                return await handler(event, data)
        student = await student_service.get_student(telegram_id)
        is_cb = hasattr(event, "data") and isinstance(getattr(event, "data"), str)
        if not student:
            welcome_unreg = "Welcome to Ethio Smart Study Bot! Please send /start to register and begin learning."
            if is_cb:
                await event.answer("Please register first by sending /start.", show_alert=True)
            elif hasattr(event, "answer"):
                await event.answer(welcome_unreg)
            return
            
        lang = student.preferred_language or "English"
        
        if student.approval_status != 'APPROVED':
            if student.approval_status == 'REJECTED':
                reason = student.rejected_reason or "Payment unverified"
                reject_msg = t("reg_rejected_with_retry", lang, reason=reason)
                if is_cb:
                    await event.answer("❌ Your registration was rejected. Send /start to retry.", show_alert=True)
                elif hasattr(event, "answer"):
                    await event.answer(reject_msg, parse_mode="HTML")
                return
            else:
                wait_msg = t("reg_pending_wait", lang)
                if is_cb:
                    await event.answer("⏳ Your registration is waiting for admin approval.", show_alert=True)
                elif hasattr(event, "answer"):
                    await event.answer(wait_msg, parse_mode="HTML")
                return
        return await handler(event, data)

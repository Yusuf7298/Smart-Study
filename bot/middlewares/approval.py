from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import config
from bot.services import student_service
from bot.services.i18n import t

class ApprovalMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Retrieve user and state
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
            
        telegram_id = user.id
        
        # Check FSM state to see if they are currently registering
        state = data.get("state")
        current_state = await state.get_state() if state else None
        
        # Determine if they are currently in the registration FSM flow
        is_registering = isinstance(current_state, str) and current_state.startswith("RegistrationStates:")
        
        # Check if user is an admin
        is_admin = telegram_id in config.ADMIN_IDS
        
        # If it's a message, check if it's the start command, admin command, or part of registration FSM
        if hasattr(event, "text"):
            command = event.text or ""
            if command.startswith("/start") or is_registering:
                return await handler(event, data)
            if is_admin and (command.startswith("/admin") or command.startswith("/broadcast")):
                return await handler(event, data)
        elif hasattr(event, "message"):
            # Allow registration callbacks and admin callbacks
            callback_data = event.data or ""
            if is_registering or callback_data.startswith("reg_"):
                return await handler(event, data)
            if is_admin and callback_data.startswith("admin_"):
                return await handler(event, data)
                
        # Fetch student from database
        student = await student_service.get_student(telegram_id)
        if not student:
            # Not registered yet
            if hasattr(event, "text"):
                await event.answer(
                    "Welcome to Smart Study Bot! Please send /start to register and begin learning."
                )
            elif hasattr(event, "message"):
                await event.answer("Please register first by sending /start.", show_alert=True)
            return
            
        lang = student.preferred_language or "English"
        
        # Check approval status
        if student.approval_status == 'PENDING':
            if hasattr(event, "text"):
                await event.answer(t("reg_pending_wait", lang), parse_mode="Markdown")
            elif hasattr(event, "message"):
                await event.answer("⏳ Your registration is pending approval.", show_alert=True)
            return
        elif student.approval_status == 'REJECTED':
            if hasattr(event, "text"):
                await event.answer(t("reg_rejected", lang), parse_mode="Markdown")
            elif hasattr(event, "message"):
                await event.answer("❌ Your registration was rejected.", show_alert=True)
            return
            
        # Approved user - continue handling event
        return await handler(event, data)

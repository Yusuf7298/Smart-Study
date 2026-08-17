import logging
import asyncio
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service
from bot.database.repositories import admin as admin_repo
from bot.database.repositories import tests as test_repo
from bot.database.repositories import materials as mat_repo
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit

router = Router()

def get_admin_dashboard_keyboard(pending_count: int) -> InlineKeyboardMarkup:
    """Returns interactive controls for the admin control center."""
    buttons = [
        [
            InlineKeyboardButton(text=f"⏳ Pending ({pending_count})", callback_data="admin_view_pending"),
            InlineKeyboardButton(text="👥 Approved", callback_data="admin_view_approved")
        ],
        [
            InlineKeyboardButton(text="❌ Rejected", callback_data="admin_view_rejected"),
            InlineKeyboardButton(text="🔍 Search Student", callback_data="admin_prompt_search")
        ],
        [
            InlineKeyboardButton(text="📜 Audit Logs", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_prompt_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔄 Refresh Dashboard", callback_data="admin_refresh_dashboard")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("admin"), StateFilter(None))
async def admin_dashboard(message: Message):
    """Displays the administrator control dashboard."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ You are not authorized to access the admin panel.")
        return
        
    stats = await asyncio.to_thread(admin_repo.get_admin_dashboard_stats)
    
    text = t(
        "admin_dashboard_title",
        "English",
        total=stats["total_students"],
        approved=stats["approved_students"],
        pending=stats["pending_students"],
        rejected=stats["rejected_students"],
        sessions=stats["total_sessions"],
        quizzes=stats["total_quizzes"],
        tests=stats["total_tests"],
        pdfs=stats["total_pdfs"]
    )
    
    await safe_reply(
        message,
        text,
        reply_markup=get_admin_dashboard_keyboard(stats["pending_students"])
    )

@router.callback_query(F.data == "admin_refresh_dashboard", StateFilter(None))
@router.callback_query(F.data == "admin_back", StateFilter(None))
async def admin_refresh_callback(callback: CallbackQuery):
    """Refreshes or returns to the admin dashboard."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    stats = await asyncio.to_thread(admin_repo.get_admin_dashboard_stats)
    text = t(
        "admin_dashboard_title",
        "English",
        total=stats["total_students"],
        approved=stats["approved_students"],
        pending=stats["pending_students"],
        rejected=stats["rejected_students"],
        sessions=stats["total_sessions"],
        quizzes=stats["total_quizzes"],
        tests=stats["total_tests"],
        pdfs=stats["total_pdfs"]
    )
    
    await safe_edit(
        callback.message, # type: ignore
        text,
        reply_markup=get_admin_dashboard_keyboard(stats["pending_students"])
    )
    await callback.answer("Dashboard updated.")

@router.callback_query(F.data == "admin_view_pending", StateFilter(None))
async def admin_view_pending_callback(callback: CallbackQuery):
    """Lists all pending students with one-tap approve/reject buttons."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    pending_list = await asyncio.to_thread(admin_repo.get_pending_students, 10)
    if not pending_list:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
        await safe_reply(callback, t("admin_no_pending", "English"), reply_markup=kb)
        await callback.answer()
        return
        
    for student in pending_list:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve_{student.telegram_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject_{student.telegram_id}")
            ]
        ])
        reg_card = (
            "⏳ Pending Student Application\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {student.first_name or 'N/A'}\n"
            f"🆔 Telegram ID:`{student.telegram_id}`\n"
            f"🏷️ Username:@{student.username if student.username else 'N/A'}\n"
            f"🎓 Grade: {student.grade or 'Not Set'}\n"
            f"🌐 Language: {student.preferred_language}\n"
            f"📅 Submitted: {student.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        await safe_reply(callback, reg_card, reply_markup=kb)
        
    await callback.answer()

@router.callback_query(F.data == "admin_view_approved", StateFilter(None))
async def admin_view_approved_callback(callback: CallbackQuery):
    """Lists recent approved students."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    approved_list = await asyncio.to_thread(admin_repo.get_students_by_status, "APPROVED", 15)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
    if not approved_list:
        await safe_reply(callback, "No approved students found.", reply_markup=kb)
        await callback.answer()
        return
        
    lines = ["👥 Approved Students (Recent 15):\n━━━━━━━━━━━━━━━━━━━━"]
    for s in approved_list:
        lines.append(f"• {s.first_name}* (@{s.username or 'N/A'}) — ID: `{s.telegram_id}` | Grade: {s.grade} | Lang: {s.preferred_language}")
        
    await safe_reply(callback, "\n".join(lines), reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_view_rejected", StateFilter(None))
async def admin_view_rejected_callback(callback: CallbackQuery):
    """Lists recent rejected students with re-approve option."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    rejected_list = await asyncio.to_thread(admin_repo.get_students_by_status, "REJECTED", 10)
    if not rejected_list:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
        await safe_reply(callback, "No rejected students found.", reply_markup=kb)
        await callback.answer()
        return
        
    for s in rejected_list:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Re-Approve", callback_data=f"admin_approve_{s.telegram_id}")
        ]])
        card = (
            "❌ Rejected Student Record\n"
            f"👤 Name: {s.first_name} (@{s.username or 'N/A'})\n"
            f"🆔 ID: `{s.telegram_id}` | Grade: {s.grade}"
        )
        await safe_reply(callback, card, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_view_logs", StateFilter(None))
@router.message(Command("admin_logs"), StateFilter(None))
async def admin_logs_handler(event: Message | CallbackQuery):
    """Displays recent administrator audit logs."""
    admin_id = event.from_user.id if event.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Unauthorized.", show_alert=True)
        else:
            await safe_reply(event, "❌ Unauthorized.")
        return
        
    logs = await asyncio.to_thread(admin_repo.get_admin_logs, 15)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
    if not logs:
        await safe_reply(event, "📜 Admin Audit Logs\n\nNo logs recorded yet.", reply_markup=kb)
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
        
    lines = ["📜 Recent Admin Audit Logs (Last 15):\n━━━━━━━━━━━━━━━━━━━━"]
    for log in logs:
        time_str = log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "Recently"
        target_str = f" | Target: `{log.target_id}`" if log.target_id else ""
        details_str = f"\n   _{log.details}_" if log.details else ""
        lines.append(f"• `[{time_str}]` {log.action}{target_str}{details_str}")
        
    await safe_reply(event, "\n\n".join(lines), reply_markup=kb)
    if isinstance(event, CallbackQuery):
        await event.answer()

@router.callback_query(F.data == "admin_prompt_search", StateFilter(None))
async def admin_prompt_search_callback(callback: CallbackQuery):
    """Prompts admin with search instructions."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    text = (
        "🔍 Student Search\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "To search for any student, send:\n\n"
        "`/admin_search <name, username, or ID>`\n\n"
        "Example:\n"
        "`/admin_search Yusuf`\n"
        "`/admin_search 8223004316`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
    await safe_reply(callback, text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_prompt_broadcast", StateFilter(None))
async def admin_prompt_broadcast_callback(callback: CallbackQuery):
    """Prompts admin with broadcast instructions."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    text = (
        "📢 Broadcast Announcement\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "To broadcast an announcement to all approved students, send:\n\n"
        "`/broadcast <your announcement message here>`\n\n"
        "Example:\n"
        "`/broadcast Welcome to the new study session! 🚀`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
    await safe_reply(callback, text, reply_markup=kb)
    await callback.answer()

@router.message(Command("admin_search"), StateFilter(None))
async def admin_search_command(message: Message):
    """Searches students by name, username, or telegram ID."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ Unauthorized.")
        return
        
    query = message.text.partition(" ")[2].strip() if message.text else ""
    if not query:
        await safe_reply(message, "ℹ️ Usage:\n`/admin_search <name, username, or ID>`")
        return
        
    results = await asyncio.to_thread(admin_repo.search_students, query, 10)
    if not results:
        await safe_reply(message, f"No students matching '{query}' found.")
        return
        
    lines = [f"🔍 Search Results for '{query}':\n━━━━━━━━━━━━━━━━━━━━"]
    for s in results:
        status_emoji = "✅" if s.approval_status == "APPROVED" else ("⏳" if s.approval_status == "PENDING" else "❌")
        lines.append(f"{status_emoji} {s.first_name} (@{s.username or 'N/A'})\n  ID: `{s.telegram_id}` | Grade: {s.grade} | Status: *{s.approval_status}*")
        
    await safe_reply(message, "\n\n".join(lines))

@router.callback_query(F.data.startswith("admin_approve_"), StateFilter(None))
async def approve_student_callback(callback: CallbackQuery):
    """Processes student approval callback from administrator."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ You are not authorized to perform this action.", show_alert=True)
        return
        
    student_id = int(callback.data.split("admin_approve_")[1]) # type: ignore
    student = await student_service.get_student(student_id)
    
    # 1. Update status atomically
    await student_service.update_approval_status(student_id, "APPROVED")
    
    # 2. Log admin action
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "APPROVE", student_id, "Approved via admin dashboard")
    
    # 3. Notify student in their preferred language
    lang = student.preferred_language if student else "English"
    try:
        from bot.keyboards.main_menu import get_main_menu_keyboard, get_main_reply_keyboard
        await callback.bot.send_message( # type: ignore
            student_id,
            t("reg_approved_notify", lang),
            reply_markup=get_main_reply_keyboard(lang)
        )
        await callback.bot.send_message( # type: ignore
            student_id,
            t("menu_title", lang, name=student.first_name if student else "Student", grade=student.grade if student else "Not Set", topic="None"),
            reply_markup=get_main_menu_keyboard(lang)
        )
    except Exception as e:
        logging.error(f"Failed to notify student {student_id} of approval: {e}")
        
    # 4. Edit admin panel message
    name_str = student.first_name if student else "N/A"
    user_str = f"@{student.username}" if student and student.username else "N/A"
    grade_str = student.grade if student else "N/A"
    lang_str = student.preferred_language if student else "N/A"
    
    await safe_edit(
        callback.message, # type: ignore
        f"✅ Student Approved Successfully:\n\n"
        f"👤 Name: {name_str}\n"
        f"🆔 *Telegram ID:* `{student_id}`\n"
        f"🏷️ *Username:* {user_str}\n"
        f"🎓 *Grade:* {grade_str}\n"
        f"🌐 *Language:* {lang_str}",
        reply_markup=None
    )
    await callback.answer("Approved successfully.")

@router.callback_query(F.data.startswith("admin_reject_"), StateFilter(None))
async def reject_student_callback(callback: CallbackQuery):
    """Processes student rejection callback from administrator."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ You are not authorized to perform this action.", show_alert=True)
        return
        
    student_id = int(callback.data.split("admin_reject_")[1]) # type: ignore
    student = await student_service.get_student(student_id)
    
    # 1. Update status atomically
    await student_service.update_approval_status(student_id, "REJECTED")
    
    # 2. Log admin action
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "REJECT", student_id, "Rejected via admin dashboard")
    
    # 3. Notify student in their preferred language
    lang = student.preferred_language if student else "English"
    try:
        await callback.bot.send_message( # type: ignore
            student_id,
            t("reg_rejected", lang)
        )
    except Exception as e:
        logging.error(f"Failed to notify student {student_id} of rejection: {e}")
        
    # 4. Edit admin panel message
    name_str = student.first_name if student else "N/A"
    user_str = f"@{student.username}" if student and student.username else "N/A"
    grade_str = student.grade if student else "N/A"
    lang_str = student.preferred_language if student else "N/A"
    
    await safe_edit(
        callback.message, # type: ignore
        f"❌ *Student Application Rejected:*\n\n"
        f"👤 *Name:* {name_str}\n"
        f"🆔 *Telegram ID:* `{student_id}`\n"
        f"🏷️ *Username:* {user_str}\n"
        f"🎓 *Grade:* {grade_str}\n"
        f"🌐 *Language:* {lang_str}",
        reply_markup=None
    )
    await callback.answer("Rejected successfully.")

@router.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """Allows administrators to send a broadcast message to all approved students."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ Unauthorized.")
        return
        
    broadcast_content = message.text.partition(" ")[2].strip() if message.text else ""
    if not broadcast_content:
        await safe_reply(message, "ℹ️ *Usage:*\n`/broadcast Your announcement message here`")
        return
        
    approved_ids = await asyncio.to_thread(admin_repo.get_all_approved_student_ids)
    if not approved_ids:
        await safe_reply(message, "No approved students found to broadcast to.")
        return
        
    status_msg = await message.answer(f"📢 Sending broadcast to {len(approved_ids)} students...")
    
    sent_count = 0
    fail_count = 0
    formatted_announcement = (
        "📢 Smart Study Bot Announcement\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{broadcast_content}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Happy studying!"
    )
    
    for s_id in approved_ids:
        try:
            await message.bot.send_message(s_id, formatted_announcement) # type: ignore
            sent_count += 1
            await asyncio.sleep(0.05) # Rate limit pacing
        except Exception as e:
            logging.warning(f"Broadcast to {s_id} failed: {e}")
            fail_count += 1
            
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "BROADCAST", None, f"Sent: {sent_count}, Failed: {fail_count}")
    await safe_edit(status_msg, f"✅ Broadcast complete!\n• Sent: *{sent_count}*\n• Failed: *{fail_count}*")

from bot.database.models import StudentModel
import logging
import asyncio
from typing import Optional, List
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.services import student_service
from bot.database.repositories import admin as admin_repo
from bot.database.repositories import tests as test_repo
from bot.database.repositories import materials as mat_repo
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit

router = Router()

class AdminStates(StatesGroup):
    waiting_for_grade_select = State()
    waiting_for_new_price = State()

def get_admin_dashboard_keyboard(pending_count: int) -> InlineKeyboardMarkup:
    """Returns interactive controls for the admin control center."""
    buttons = [
        [
            InlineKeyboardButton(text=f"⏳ Pending ({pending_count})", callback_data="admin_view_pending"),
            InlineKeyboardButton(text="👥 Approved", callback_data="admin_view_approved")
        ],
        [
            InlineKeyboardButton(text="💰 Set Course Price", callback_data="admin_act_pricing"),
            InlineKeyboardButton(text="❌ Rejected", callback_data="admin_view_rejected")
        ],
        [
            InlineKeyboardButton(text="🔍 Search Student", callback_data="admin_prompt_search"),
            InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_prompt_broadcast")
        ],
        [
            InlineKeyboardButton(text="📜 Audit Logs", callback_data="admin_view_logs"),
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
    current_price = await student_service.get_course_price()
    
    text = (
        "🛡️ *Admin Control Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Active Course Price:* {current_price} ETB\n\n"
        f"👥 *Students Overview:*\n"
        f"• Total Registered: *{stats['total_students']}*\n"
        f"• ✅ Approved: *{stats['approved_students']}*\n"
        f"• ⏳ Pending: *{stats['pending_students']}*\n"
        f"• ❌ Rejected: *{stats['rejected_students']}*\n\n"
        f"📊 *Activity Statistics:*\n"
        f"• 📚 Study Sessions: *{stats['total_sessions']}*\n"
        f"• ❓ Quizzes Taken: *{stats['total_quizzes']}*\n"
        f"• 📝 Tests Evaluated: *{stats['total_tests']}*\n"
        f"• 📄 PDFs Uploaded: *{stats['total_pdfs']}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Use buttons below to manage students or update settings:"
    )
    
    await safe_reply(
        message,
        text,
        reply_markup=get_admin_dashboard_keyboard(stats["pending_students"])
    )

@router.callback_query(F.data == "admin_refresh_dashboard", StateFilter(None))
@router.callback_query(F.data == "admin_back", StateFilter(None))
async def admin_refresh_callback(callback: CallbackQuery, state: Optional[FSMContext] = None):
    """Refreshes or returns to the admin dashboard."""
    if state:
        await state.clear()
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
        
    stats = await asyncio.to_thread(admin_repo.get_admin_dashboard_stats)
    current_price = await student_service.get_course_price()
    
    text = (
        "🛡️ *Admin Control Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Active Course Price:* {current_price} ETB\n\n"
        f"👥 *Students Overview:*\n"
        f"• Total Registered: *{stats['total_students']}*\n"
        f"• ✅ Approved: *{stats['approved_students']}*\n"
        f"• ⏳ Pending: *{stats['pending_students']}*\n"
        f"• ❌ Rejected: *{stats['rejected_students']}*\n\n"
        f"📊 *Activity Statistics:*\n"
        f"• 📚 Study Sessions: *{stats['total_sessions']}*\n"
        f"• ❓ Quizzes Taken: *{stats['total_quizzes']}*\n"
        f"• 📝 Tests Evaluated: *{stats['total_tests']}*\n"
        f"• 📄 PDFs Uploaded: *{stats['total_pdfs']}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Use buttons below to manage students or update settings:"
    )
    
    await safe_edit(
        callback.message, # type: ignore
        text,
        reply_markup=get_admin_dashboard_keyboard(stats["pending_students"])
    )
    try:
        await callback.answer("Dashboard updated.")
    except Exception:
        pass

# ----------------- Dynamic Pricing -----------------

@router.message(Command("admin_pricing"))
@router.callback_query(F.data == "admin_act_pricing")
async def admin_pricing_prompt(event: Message | CallbackQuery, state: FSMContext):
    """Displays dynamic pricing settings per grade and prompts admin to select a grade to update."""
    admin_id = event.from_user.id if event.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Unauthorized.", show_alert=True)
        else:
            await safe_reply(event, "❌ Unauthorized.")
        return
        
    await state.set_state(AdminStates.waiting_for_grade_select)
    default_price = await student_service.get_course_price()
    custom_prices = await student_service.get_all_grade_prices()
    
    price_lines = []
    for g in ["5", "6", "7", "8", "9", "10", "11", "12"]:
        p = custom_prices.get(g, default_price)
        price_lines.append(f"• *Grade {g}:* {p} ETB")

    text = (
        "💰 *Grade-Specific Dynamic Course Pricing*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 *Global Default Price:* {default_price} ETB\n\n"
        "📊 *Current Grade Prices:*\n" +
        "\n".join(price_lines) +
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        "Select a Grade below to update its course price, or set the Global Default:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Grade 5", callback_data="admin_pgrade_5"),
            InlineKeyboardButton(text="Grade 6", callback_data="admin_pgrade_6"),
            InlineKeyboardButton(text="Grade 7", callback_data="admin_pgrade_7"),
            InlineKeyboardButton(text="Grade 8", callback_data="admin_pgrade_8")
        ],
        [
            InlineKeyboardButton(text="Grade 9", callback_data="admin_pgrade_9"),
            InlineKeyboardButton(text="Grade 10", callback_data="admin_pgrade_10"),
            InlineKeyboardButton(text="Grade 11", callback_data="admin_pgrade_11"),
            InlineKeyboardButton(text="Grade 12", callback_data="admin_pgrade_12")
        ],
        [InlineKeyboardButton(text="🌐 Default Price (All Grades)", callback_data="admin_pgrade_DEFAULT")],
        [InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]
    ])
    
    if isinstance(event, CallbackQuery):
        await safe_edit(event.message, text, reply_markup=kb) # type: ignore
        await event.answer()
    else:
        await safe_reply(event, text, reply_markup=kb)

@router.callback_query(F.data.startswith("admin_pgrade_"))
async def process_price_grade_select(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    grade_target = callback.data.split("admin_pgrade_")[1]
    await state.update_data(target_grade=grade_target)
    await state.set_state(AdminStates.waiting_for_new_price)

    label = "Global Default (All Grades)" if grade_target == "DEFAULT" else f"Grade {grade_target}"
    text = (
        f"💰 *Update Course Price — {label}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Please enter the new price per course in ETB for *{label}* (e.g. `60`, `75`, `100`):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Cancel", callback_data="admin_act_pricing")]])
    await safe_edit(callback.message, text, reply_markup=kb)

@router.message(AdminStates.waiting_for_new_price)
async def process_new_course_price(message: Message, state: FSMContext):
    """Saves the new price per course to database for selected grade or default."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ Unauthorized.")
        await state.clear()
        return
        
    text = message.text.strip() if message.text else ""
    try:
        new_price = int(text)
        if new_price <= 0 or new_price > 10000:
            await safe_reply(message, "Please enter a realistic price in ETB (e.g. 50, 75, 100):")
            return
    except ValueError:
        await safe_reply(message, "Please enter a valid numeric amount in ETB (e.g. 60):")
        return

    data = await state.get_data()
    target_grade = data.get("target_grade", "DEFAULT")

    if target_grade == "DEFAULT":
        await student_service.set_course_price(new_price)
        label = "Global Default (All Grades)"
    else:
        await student_service.set_grade_course_price(target_grade, new_price)
        label = f"Grade {target_grade}"

    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "UPDATE_PRICING", None, f"Changed {label} course price to {new_price} ETB")
    await state.clear()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Pricing Dashboard", callback_data="admin_act_pricing")],
        [InlineKeyboardButton(text="🔙 Admin Dashboard", callback_data="admin_back")]
    ])
    await safe_reply(
        message,
        f"✅ *Course Price Updated!*\n━━━━━━━━━━━━━━━━━━━━\nNew course price for *{label}* is now *{new_price} ETB*.",
        reply_markup=kb
    )

# ----------------- Student Approval & Review -----------------

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
        await safe_reply(callback, "✅ No pending registrations at this time.", reply_markup=kb)
        await callback.answer()
        return
        
    for student in pending_list:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve_{student.telegram_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject_{student.telegram_id}")
            ],
            [
                InlineKeyboardButton(text="✏️ Edit Student", callback_data=f"admin_manage_{student.telegram_id}")
            ]
        ])
        courses_str = ", ".join(student.selected_courses) if student.selected_courses else "General"
        sub_time = student.payment_submitted_at.strftime('%Y-%m-%d %H:%M UTC') if student.payment_submitted_at else (student.created_at.strftime('%Y-%m-%d %H:%M UTC') if student.created_at else 'Recently')
        
        reg_card = (
            "⏳ *Pending Student Application*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Name:* {student.first_name or 'N/A'}\n"
            f"📱 *Phone:* `{student.phone_number or 'N/A'}`\n"
            f"🆔 *Telegram ID:* `{student.telegram_id}`\n"
            f"🏷️ *Username:* @{student.username if student.username else 'N/A'}\n"
            f"🎓 *Grade:* {student.grade or 'Not Set'}\n"
            f"🌐 *Language:* {student.preferred_language}\n"
            f"📚 *Courses:* {courses_str}\n"
            f"💰 *Fee:* {student.payment_amount} ETB\n"
            f"📅 *Submitted:* {sub_time}"
        )
        
        # If receipt screenshot is present, send photo card
        if student.payment_screenshot_file_id:
            try:
                await callback.message.bot.send_photo( # type: ignore
                    chat_id=admin_id,
                    photo=student.payment_screenshot_file_id,
                    caption=reg_card,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                continue
            except Exception:
                pass
                
        await safe_reply(callback, reg_card, reply_markup=kb)
        
    await callback.answer()

@router.callback_query(F.data == "admin_view_approved", StateFilter(None))
async def admin_view_approved_callback(callback: CallbackQuery):
    """Lists recent approved students with edit options."""
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
        
    for s in approved_list:
        courses_str = ", ".join(s.selected_courses) if s.selected_courses else "All"
        card = (
            f"✅ *{s.first_name}* (@{s.username or 'N/A'})\n"
            f"🆔 ID: `{s.telegram_id}` | 📱 Phone: `{s.phone_number or 'N/A'}`\n"
            f"🎓 Grade: *{s.grade}* | 📚 Courses: *{courses_str}*"
        )
        card_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✏️ Edit Student", callback_data=f"admin_manage_{s.telegram_id}")
        ]])
        await safe_reply(callback, card, reply_markup=card_kb)
        
    await safe_reply(callback, "━━━━━━━━━━━━━━━━━━━━\nUse buttons above to edit students or return:", reply_markup=kb)
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
            "❌ *Rejected Student Record*\n"
            f"👤 Name: {s.first_name} (@{s.username or 'N/A'})\n"
            f"📱 Phone: `{s.phone_number or 'N/A'}`\n"
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
        await safe_reply(event, "📜 *Admin Audit Logs*\n\nNo logs recorded yet.", reply_markup=kb)
        if isinstance(event, CallbackQuery):
            await event.answer()
        return
        
    lines = ["📜 *Recent Admin Audit Logs (Last 15):*\n━━━━━━━━━━━━━━━━━━━━"]
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
        "🔍 *Student Search*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "To search for any student, send:\n\n"
        "`/admin_search <name, username, phone, or ID>`\n\n"
        "Example:\n"
        "`/admin_search Yusuf`\n"
        "`/admin_search 0928892344`\n"
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
        "📢 *Broadcast Announcement*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "To broadcast an announcement to all approved students, send:\n\n"
        "`/broadcast <your announcement message here>`\n\n"
        "Example:\n"
        "`/broadcast Welcome to Ethio Smart Study! 🚀`"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")]])
    await safe_reply(callback, text, reply_markup=kb)
    await callback.answer()

def get_admin_edit_student_keyboard(student_id: int, status: str = "APPROVED") -> InlineKeyboardMarkup:
    """Returns interactive management buttons for editing a student profile."""
    buttons = [
        [
            InlineKeyboardButton(text="🎓 Change Grade Level", callback_data=f"admin_chgrade_{student_id}"),
            InlineKeyboardButton(text="📚 Add / Edit Courses", callback_data=f"admin_chcourses_{student_id}")
        ]
    ]
    if status != "APPROVED":
        buttons.append([
            InlineKeyboardButton(text="✅ Approve Student", callback_data=f"admin_approve_{student_id}"),
            InlineKeyboardButton(text="❌ Reject Student", callback_data=f"admin_reject_{student_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔒 Revoke / Lock", callback_data=f"admin_reject_{student_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Back to Dashboard", callback_data="admin_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_grades_keyboard(student_id: int) -> InlineKeyboardMarkup:
    """Returns grade selection grid for admin to set student grade."""
    buttons = [
        [
            InlineKeyboardButton(text="Grade 5", callback_data=f"admin_setgrade_{student_id}_5"),
            InlineKeyboardButton(text="Grade 6", callback_data=f"admin_setgrade_{student_id}_6"),
            InlineKeyboardButton(text="Grade 7", callback_data=f"admin_setgrade_{student_id}_7"),
            InlineKeyboardButton(text="Grade 8", callback_data=f"admin_setgrade_{student_id}_8")
        ],
        [
            InlineKeyboardButton(text="Grade 9", callback_data=f"admin_setgrade_{student_id}_9"),
            InlineKeyboardButton(text="Grade 10", callback_data=f"admin_setgrade_{student_id}_10"),
            InlineKeyboardButton(text="Grade 11", callback_data=f"admin_setgrade_{student_id}_11"),
            InlineKeyboardButton(text="Grade 12", callback_data=f"admin_setgrade_{student_id}_12")
        ],
        [
            InlineKeyboardButton(text="College", callback_data=f"admin_setgrade_{student_id}_College"),
            InlineKeyboardButton(text="University", callback_data=f"admin_setgrade_{student_id}_University")
        ],
        [
            InlineKeyboardButton(text="🔙 Cancel", callback_data=f"admin_manage_{student_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_courses_keyboard(student_id: int, current_courses: List[str]) -> InlineKeyboardMarkup:
    """Returns course checkboxes for admin to toggle enrolled subjects."""
    all_available = list(config.SUBJECTS.keys())
    buttons = []
    row = []
    for subject in all_available:
        is_selected = subject in current_courses
        emoji = "✅" if is_selected else "⬜"
        row.append(InlineKeyboardButton(
            text=f"{emoji} {subject}",
            callback_data=f"admin_togcourse_{student_id}_{subject}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    buttons.append([
        InlineKeyboardButton(text="➕ Add All Subjects", callback_data=f"admin_addallcourses_{student_id}"),
        InlineKeyboardButton(text="🧹 Clear All", callback_data=f"admin_clearcourses_{student_id}")
    ])
    buttons.append([
        InlineKeyboardButton(text="💾 Done & Back", callback_data=f"admin_manage_{student_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def render_admin_student_card(target: Message | CallbackQuery, student: StudentModel):
    """Renders the comprehensive Student Management Card with edit options."""
    courses_str = ", ".join(student.selected_courses) if student.selected_courses else "None (General)"
    status_emoji = "✅" if student.approval_status == "APPROVED" else ("⏳" if "PENDING" in student.approval_status or "SUBMITTED" in student.approval_status else "❌")
    
    text = (
        f"✏️ *Student Profile Management*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {student.first_name or 'N/A'}\n"
        f"📱 *Phone:* `{student.phone_number or 'N/A'}`\n"
        f"🆔 *Telegram ID:* `{student.telegram_id}`\n"
        f"🏷️ *Username:* @{student.username if student.username else 'N/A'}\n"
        f"🎓 *Grade Level:* *Grade {student.grade or 'Not Set'}* ({student.education_level or 'N/A'})\n"
        f"🌐 *Language:* {student.preferred_language}\n"
        f"📚 *Enrolled Courses:* *{courses_str}*\n"
        f"💰 *Fee Paid:* {student.payment_amount} ETB\n"
        f"{status_emoji} *Status:* *{student.approval_status}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Select an action to modify this student's account:"
    )
    kb = get_admin_edit_student_keyboard(student.telegram_id, student.approval_status)
    if isinstance(target, CallbackQuery) or (hasattr(target, "message") and target.message is not None):
        await safe_edit(target.message, text, reply_markup=kb)
    else:
        await safe_reply(target, text, reply_markup=kb)

@router.message(Command("admin_edit"), StateFilter(None))
@router.message(Command("admin_manage"), StateFilter(None))
async def admin_edit_command(message: Message):
    """Admin command to directly open the editor for a student by ID or query."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ Unauthorized.")
        return
        
    query = message.text.partition(" ")[2].strip() if message.text else ""
    if not query:
        await safe_reply(message, "ℹ️ Usage:\n`/admin_edit <student_id or phone>`")
        return
        
    student = None
    if query.isdigit():
        student = await student_service.get_student(int(query))
    if not student:
        results = await asyncio.to_thread(admin_repo.search_students, query, 1)
        if results:
            student = results[0]
            
    if not student:
        await safe_reply(message, f"❌ Student matching '{query}' not found.")
        return
        
    await render_admin_student_card(message, student)

@router.message(Command("admin_search"), StateFilter(None))
async def admin_search_command(message: Message):
    """Searches students by name, username, or telegram ID."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ Unauthorized.")
        return
        
    query = message.text.partition(" ")[2].strip() if message.text else ""
    if not query:
        await safe_reply(message, "ℹ️ Usage:\n`/admin_search <name, username, phone, or ID>`")
        return
        
    results = await asyncio.to_thread(admin_repo.search_students, query, 10)
    if not results:
        await safe_reply(message, f"No students matching '{query}' found.")
        return
        
    if len(results) == 1:
        await render_admin_student_card(message, results[0])
        return
        
    for s in results:
        status_emoji = "✅" if s.approval_status == "APPROVED" else ("⏳" if "PENDING" in s.approval_status or "SUBMITTED" in s.approval_status else "❌")
        courses_str = ", ".join(s.selected_courses) if s.selected_courses else "All"
        card = (
            f"{status_emoji} *{s.first_name}* (@{s.username or 'N/A'})\n"
            f"  ID: `{s.telegram_id}` | Phone: `{s.phone_number or 'N/A'}`\n"
            f"  Grade: {s.grade} | Status: *{s.approval_status}*\n"
            f"  Courses: {courses_str}"
        )
        card_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✏️ Edit / Manage", callback_data=f"admin_manage_{s.telegram_id}")
        ]])
        await safe_reply(message, card, reply_markup=card_kb)

@router.callback_query(F.data.startswith("admin_manage_"), StateFilter(None))
async def admin_manage_callback(callback: CallbackQuery):
    """Displays student management panel for the selected student."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    student_id = int(callback.data.split("admin_manage_")[1])
    student = await student_service.get_student(student_id)
    if not student:
        await callback.answer("Student not found.", show_alert=True)
        return
    await render_admin_student_card(callback, student)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_chgrade_"), StateFilter(None))
async def admin_chgrade_callback(callback: CallbackQuery):
    """Displays grade selection buttons to change student grade."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    student_id = int(callback.data.split("admin_chgrade_")[1])
    student = await student_service.get_student(student_id)
    if not student:
        await callback.answer("Student not found.", show_alert=True)
        return
        
    text = (
        f"🎓 *Change Grade for {student.first_name}* (`{student_id}`)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Current Grade: *Grade {student.grade or 'Not Set'}*\n\n"
        f"Select the new grade level to assign to this student:"
    )
    await safe_edit(callback.message, text, reply_markup=get_admin_grades_keyboard(student_id))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_setgrade_"), StateFilter(None))
async def admin_setgrade_callback(callback: CallbackQuery):
    """Applies grade update from admin selection."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    parts = callback.data.split("admin_setgrade_")[1].split("_")
    student_id = int(parts[0])
    new_grade = parts[1]
    
    await student_service.update_grade(student_id, new_grade)
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "CHANGE_GRADE", student_id, f"Changed grade to {new_grade}")
    
    # Notify student
    try:
        await callback.bot.send_message(
            student_id,
            f"🎓 *Admin Notice:* Your academic grade level has been updated to *Grade {new_grade}* by support.\nSend /study to begin studying your curriculum!",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.warning(f"Could not notify student of grade update: {e}")
        
    student = await student_service.get_student(student_id)
    if student:
        await render_admin_student_card(callback, student)
    await callback.answer(f"Grade updated to {new_grade}!")

@router.callback_query(F.data.startswith("admin_chcourses_"), StateFilter(None))
async def admin_chcourses_callback(callback: CallbackQuery):
    """Displays course checkboxes for admin to toggle enrolled subjects."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    student_id = int(callback.data.split("admin_chcourses_")[1])
    student = await student_service.get_student(student_id)
    if not student:
        await callback.answer("Student not found.", show_alert=True)
        return
        
    courses_str = ", ".join(student.selected_courses) if student.selected_courses else "None"
    text = (
        f"📚 *Manage Enrolled Courses for {student.first_name}* (`{student_id}`)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Currently Enrolled: *{courses_str}*\n\n"
        f"Click any course below to add or remove it from their account:"
    )
    await safe_edit(callback.message, text, reply_markup=get_admin_courses_keyboard(student_id, student.selected_courses or []))
    await callback.answer()

@router.callback_query(F.data.startswith("admin_togcourse_"), StateFilter(None))
async def admin_togcourse_callback(callback: CallbackQuery):
    """Toggles a single course enrollment for the student."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    parts = callback.data.split("admin_togcourse_")[1].split("_")
    student_id = int(parts[0])
    course_name = "_".join(parts[1:])
    
    student = await student_service.get_student(student_id)
    if not student:
        await callback.answer("Student not found.", show_alert=True)
        return
        
    courses = list(student.selected_courses or [])
    if course_name in courses:
        courses.remove(course_name)
    else:
        courses.append(course_name)
        
    await student_service.update_courses(student_id, courses)
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "EDIT_COURSES", student_id, f"Updated courses: {courses}")
    
    courses_str = ", ".join(courses) if courses else "None"
    text = (
        f"📚 *Manage Enrolled Courses for {student.first_name}* (`{student_id}`)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Currently Enrolled: *{courses_str}*\n\n"
        f"Click any course below to add or remove it from their account:"
    )
    await safe_edit(callback.message, text, reply_markup=get_admin_courses_keyboard(student_id, courses))
    await callback.answer(f"Updated {course_name}")

@router.callback_query(F.data.startswith("admin_addallcourses_"), StateFilter(None))
async def admin_addallcourses_callback(callback: CallbackQuery):
    """Enrolls student into all catalog courses."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    student_id = int(callback.data.split("admin_addallcourses_")[1])
    all_courses = list(config.SUBJECTS.keys())
    
    await student_service.update_courses(student_id, all_courses)
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "ADD_ALL_COURSES", student_id, "Enrolled in all catalog courses")
    
    student = await student_service.get_student(student_id)
    if student:
        text = (
            f"📚 *Manage Enrolled Courses for {student.first_name}* (`{student_id}`)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Currently Enrolled: *{', '.join(all_courses)}*\n\n"
            f"Click any course below to add or remove it from their account:"
        )
        await safe_edit(callback.message, text, reply_markup=get_admin_courses_keyboard(student_id, all_courses))
    await callback.answer("All courses added!")

@router.callback_query(F.data.startswith("admin_clearcourses_"), StateFilter(None))
async def admin_clearcourses_callback(callback: CallbackQuery):
    """Clears enrolled courses for student."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ Unauthorized.", show_alert=True)
        return
    student_id = int(callback.data.split("admin_clearcourses_")[1])
    
    await student_service.update_courses(student_id, [])
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "CLEAR_COURSES", student_id, "Cleared all courses")
    
    student = await student_service.get_student(student_id)
    if student:
        text = (
            f"📚 *Manage Enrolled Courses for {student.first_name}* (`{student_id}`)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Currently Enrolled: *None*\n\n"
            f"Click any course below to add or remove it from their account:"
        )
        await safe_edit(callback.message, text, reply_markup=get_admin_courses_keyboard(student_id, []))
    await callback.answer("Courses cleared.")

@router.callback_query(F.data.startswith("admin_approve_"), StateFilter(None))
async def approve_student_callback(callback: CallbackQuery):
    """Processes student approval callback from administrator."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ You are not authorized to perform this action.", show_alert=True)
        return
        
    student_id = int(callback.data.split("admin_approve_")[1]) # type: ignore
    student = await student_service.get_student(student_id)
    
    # 1. Update status atomically to APPROVED
    await student_service.approve_student(student_id)
    
    # 2. Log admin action
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "APPROVE", student_id, "Approved via admin dashboard")
    
    # 3. Notify student in their preferred language & send personalized Dashboard
    lang = student.preferred_language if student else "English"
    try:
        from bot.keyboards.main_menu import get_main_menu_keyboard, get_main_reply_keyboard
        from bot.handlers.start import send_student_dashboard
        await callback.bot.send_message( # type: ignore
            student_id,
            t("reg_approved_notify", lang),
            parse_mode="HTML",
            reply_markup=get_main_reply_keyboard(lang)
        )
        await send_student_dashboard(callback.bot, student_id) # type: ignore
    except Exception as e:
        logging.error(f"Failed to notify student {student_id} of approval: {e}")
        
    # 4. Automatically forward payment info to private payment channel if configured
    name_str = student.first_name if student else "N/A"
    user_str = f"@{student.username}" if student and student.username else "N/A"
    phone_str = student.phone_number if student and student.phone_number else "N/A"
    courses_str = ", ".join(student.selected_courses) if student and student.selected_courses else "All"
    amount_str = f"{student.payment_amount} ETB" if student else "50 ETB"
    
    payment_channel = getattr(config, "PAYMENT_CHANNEL_ID", None)
    if payment_channel:
        channel_card = (
            "💳 *VERIFIED PAYMENT & ENROLLMENT LOG*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Student:* {name_str}\n"
            f"📱 *Phone:* `{phone_str}`\n"
            f"🆔 *Telegram ID:* `{student_id}`\n"
            f"🏷️ *Username:* {user_str}\n"
            f"🎓 *Grade:* {student.grade if student else 'Not Set'}\n"
            f"🌐 *Language:* {student.preferred_language if student else 'English'}\n\n"
            f"📚 *Enrolled Courses:*\n{courses_str}\n\n"
            f"💰 *Amount Paid:* *{amount_str}*\n"
            f"👮 *Approved By Admin:* `{admin_id}`\n"
            f"📅 *Timestamp:* {student.updated_at if student and student.updated_at else 'Just now'}"
        )
        try:
            if student and student.payment_screenshot_file_id:
                await callback.bot.send_photo( # type: ignore
                    chat_id=payment_channel,
                    photo=student.payment_screenshot_file_id,
                    caption=channel_card,
                    parse_mode="HTML"
                )
            else:
                await callback.bot.send_message( # type: ignore
                    chat_id=payment_channel,
                    text=channel_card,
                    parse_mode="HTML"
                )
        except Exception as ce:
            logging.error(f"Failed to forward payment to channel {payment_channel}: {ce}")

    # 5. Edit admin panel message
    approval_card = (
        "✅ *Student Approved Successfully*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {name_str}\n"
        f"📱 *Phone:* `{phone_str}`\n"
        f"🆔 *Telegram ID:* `{student_id}`\n"
        f"🏷️ *Username:* {user_str}\n"
        f"📚 *Registered Courses:* {courses_str}\n"
        f"💰 *Amount:* {amount_str}\n"
        f"📅 *Approved At:* {student.updated_at if student and student.updated_at else 'Just now'}"
    )
    
    if hasattr(callback.message, "photo") and isinstance(callback.message.photo, list) and len(callback.message.photo) > 0: # type: ignore
        await callback.message.edit_caption(caption=approval_card, parse_mode="HTML", reply_markup=None) # type: ignore
    else:
        await safe_edit(callback.message, approval_card, reply_markup=None) # type: ignore
    await callback.answer("Student approved.")

@router.callback_query(F.data.startswith("admin_reject_"), StateFilter(None))
async def reject_student_callback(callback: CallbackQuery):
    """Processes student rejection callback from administrator."""
    admin_id = callback.from_user.id
    if admin_id not in config.ADMIN_IDS:
        await callback.answer("❌ You are not authorized to perform this action.", show_alert=True)
        return
        
    student_id = int(callback.data.split("admin_reject_")[1]) # type: ignore
    student = await student_service.get_student(student_id)
    
    # 1. Update status to REJECTED
    await student_service.reject_student(student_id, "Payment receipt unverified or registration incomplete.")
    
    # 2. Log admin action
    await asyncio.to_thread(admin_repo.log_admin_action, admin_id, "REJECT", student_id, "Rejected via admin dashboard")
    
    # 3. Notify student
    lang = student.preferred_language if student else "English"
    try:
        reject_msg = t("reg_rejected_with_retry", lang, reason="Payment verification was unsuccessful. Please check your transaction receipt and re-submit.")
        await callback.bot.send_message( # type: ignore
            student_id,
            reject_msg,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Failed to notify student {student_id} of rejection: {e}")
        
    # 4. Edit admin message
    rejection_card = (
        "❌ *Student Application Rejected*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {student.first_name if student else 'N/A'}\n"
        f"📱 *Phone:* `{student.phone_number if student and student.phone_number else 'N/A'}`\n"
        f"🆔 *Telegram ID:* `{student_id}`\n"
        f"Status has been updated to REJECTED."
    )
    if hasattr(callback.message, "photo") and isinstance(callback.message.photo, list) and len(callback.message.photo) > 0: # type: ignore
        await callback.message.edit_caption(caption=rejection_card, parse_mode="HTML", reply_markup=None) # type: ignore
    else:
        await safe_edit(callback.message, rejection_card, reply_markup=None) # type: ignore
    await callback.answer("Student rejected.")

@router.message(Command("broadcast"), StateFilter(None))
async def broadcast_command(message: Message):
    """Broadcasts a message to all approved students."""
    admin_id = message.from_user.id if message.from_user else None
    if not admin_id or admin_id not in config.ADMIN_IDS:
        await safe_reply(message, "❌ Unauthorized.")
        return
        
    broadcast_content = message.text.partition(" ")[2].strip() if message.text else ""
    if not broadcast_content:
        await safe_reply(message, "ℹ️ Usage:\n`/broadcast <your announcement message>`")
        return
        
    approved_ids = await asyncio.to_thread(admin_repo.get_all_approved_student_ids)
    if not approved_ids:
        await safe_reply(message, "No approved students found to broadcast to.")
        return
        
    status_msg = await message.answer(f"📢 Sending broadcast to {len(approved_ids)} students...")
    
    sent_count = 0
    fail_count = 0
    formatted_announcement = (
        "📢 *Ethio Smart Study Announcement*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{broadcast_content}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Happy studying!"
    )
    
    for s_id in approved_ids:
        try:
            await message.bot.send_message(s_id, formatted_announcement, parse_mode="HTML") # type: ignore
            sent_count += 1
            await asyncio.sleep(0.05) # Rate limit pacing
        except Exception:
            fail_count += 1
            
    await asyncio.to_thread(
        admin_repo.log_admin_action, 
        admin_id, 
        "BROADCAST", 
        None, 
        f"Broadcast sent to {sent_count} students (failed: {fail_count})"
    )
    
    await safe_reply(
        message,
        f"✅ *Broadcast Completed!*\n\n• Delivered: *{sent_count}*\n• Failed / Blocked: *{fail_count}*"
    )
    
admin_command = admin_dashboard

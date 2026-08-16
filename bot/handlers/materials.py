import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services import student_service, pdf_service
from bot.services.i18n import t
from bot.handlers.pdf import get_pdf_actions_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

def get_materials_keyboard(materials, lang: str = "English") -> InlineKeyboardMarkup:
    """Builds inline keyboard for materials library with Study and Delete buttons per item."""
    inline_keyboard = []
    for mat in materials:
        title_snippet = (mat.title or mat.filename)[:20]
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {title_snippet}",
                callback_data=f"mat_study_{mat.id}"
            ),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=f"mat_del_{mat.id}"
            )
        ])
    inline_keyboard.append([
        InlineKeyboardButton(text=t("btn_upload_pdf", lang), callback_data="pdf_upload_new"),
        InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

@router.message(Command("materials"), StateFilter(None))
@router.message(F.text.in_(["📎 My Materials", "📎 የእኔ ማቴሪያሎች", "📎 Meeshaalee Koo"]), StateFilter(None))
async def show_materials_command(message: Message, state: FSMContext):
    """Displays the student's study materials library."""
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    materials = await pdf_service.get_student_materials(telegram_id)
    if not materials:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("btn_upload_pdf", lang), callback_data="pdf_upload_new")
        ]])
        await safe_reply(message, t("materials_empty", lang), reply_markup=kb)
        return
        
    lines = [t("materials_title", lang)]
    for idx, mat in enumerate(materials, 1):
        size_kb = (mat.file_size or 0) / 1024
        status_tag = f" [{mat.extraction_status}]" if mat.extraction_status != "SUCCESS" else ""
        date_str = mat.created_at.strftime("%Y-%m-%d") if mat.created_at else "Recently"
        lines.append(f"• *{idx}. {mat.title or mat.filename}*{status_tag}\n  📑 Pages: {mat.page_count} | 💾 {size_kb:.1f} KB | 📅 {date_str}")
        
    kb = get_materials_keyboard(materials, lang)
    await safe_reply(message, "\n\n".join(lines), reply_markup=kb)

@router.callback_query(F.data == "menu_materials")
async def materials_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Handles main menu My Materials callback."""
    await state.clear()
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    materials = await pdf_service.get_student_materials(telegram_id)
    if not materials:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("btn_upload_pdf", lang), callback_data="pdf_upload_new")
        ]])
        await safe_edit(callback.message, t("materials_empty", lang), reply_markup=kb)
        await callback.answer()
        return
        
    lines = [t("materials_title", lang)]
    for idx, mat in enumerate(materials, 1):
        size_kb = (mat.file_size or 0) / 1024
        status_tag = f" [{mat.extraction_status}]" if mat.extraction_status != "SUCCESS" else ""
        date_str = mat.created_at.strftime("%Y-%m-%d") if mat.created_at else "Recently"
        lines.append(f"• *{idx}. {mat.title or mat.filename}*{status_tag}\n  📑 Pages: {mat.page_count} | 💾 {size_kb:.1f} KB | 📅 {date_str}")
        
    kb = get_materials_keyboard(materials, lang)
    await safe_edit(callback.message, "\n\n".join(lines), reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("mat_study_"))
async def study_material_callback(callback: CallbackQuery, state: FSMContext):
    """Activates selected study material and presents PDF Study options."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    try:
        mat_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Invalid material ID.", show_alert=True)
        return
        
    activated = await pdf_service.activate_student_material(telegram_id, mat_id)
    if not activated:
        await callback.answer("Material not found or already deleted.", show_alert=True)
        return
        
    active_mat = await pdf_service.get_active_material(telegram_id)
    if not active_mat:
        await callback.answer("Unable to activate material.", show_alert=True)
        return
        
    msg_text = t(
        "pdf_ready",
        lang,
        title=active_mat.title or active_mat.filename,
        pages=active_mat.page_count,
        topics=active_mat.topics_json or "General Study",
        summary=active_mat.summary or "Document ready."
    )
    kb = get_pdf_actions_keyboard(active_mat.id, lang)
    await safe_edit(callback.message, msg_text, reply_markup=kb)
    await callback.answer(t("materials_activated", lang))

@router.callback_query(F.data.startswith("mat_del_"))
async def delete_material_callback(callback: CallbackQuery, state: FSMContext):
    """Deletes material from student library and updates UI."""
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    try:
        mat_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Invalid material ID.", show_alert=True)
        return
        
    deleted = await pdf_service.delete_student_material(telegram_id, mat_id)
    if not deleted:
        await callback.answer("Material not found or access denied.", show_alert=True)
        return
        
    await callback.answer(t("materials_deleted", lang), show_alert=True)
    
    # Refresh list
    materials = await pdf_service.get_student_materials(telegram_id)
    if not materials:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("btn_upload_pdf", lang), callback_data="pdf_upload_new")
        ]])
        await safe_edit(callback.message, t("materials_empty", lang), reply_markup=kb)
        return
        
    lines = [t("materials_title", lang)]
    for idx, mat in enumerate(materials, 1):
        size_kb = (mat.file_size or 0) / 1024
        status_tag = f" [{mat.extraction_status}]" if mat.extraction_status != "SUCCESS" else ""
        date_str = mat.created_at.strftime("%Y-%m-%d") if mat.created_at else "Recently"
        lines.append(f"• *{idx}. {mat.title or mat.filename}*{status_tag}\n  📑 Pages: {mat.page_count} | 💾 {size_kb:.1f} KB | 📅 {date_str}")
        
    kb = get_materials_keyboard(materials, lang)
    await safe_edit(callback.message, "\n\n".join(lines), reply_markup=kb)

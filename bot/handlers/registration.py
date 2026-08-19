import os
import io
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)

import config
from bot.services import student_service
from bot.services.i18n import t, get_subject_name_in_lang, get_stream_name_in_lang
from bot.utils import safe_edit, safe_reply

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_grade = State()
    waiting_for_stream = State()
    waiting_for_language = State()
    waiting_for_subjects = State()
    waiting_for_payment_confirmation = State()
    waiting_for_payment_screenshot = State()

def get_phone_keyboard(lang: str = "English") -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=t("btn_share_phone", lang), request_contact=True)],
        [KeyboardButton(text=t("btn_cancel", lang))]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

def get_grades_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Grade 1", callback_data="reg_grade_1"),
            InlineKeyboardButton(text="Grade 2", callback_data="reg_grade_2"),
            InlineKeyboardButton(text="Grade 3", callback_data="reg_grade_3"),
            InlineKeyboardButton(text="Grade 4", callback_data="reg_grade_4")
        ],
        [
            InlineKeyboardButton(text="Grade 5", callback_data="reg_grade_5"),
            InlineKeyboardButton(text="Grade 6", callback_data="reg_grade_6"),
            InlineKeyboardButton(text="Grade 7", callback_data="reg_grade_7"),
            InlineKeyboardButton(text="Grade 8", callback_data="reg_grade_8")
        ],
        [
            InlineKeyboardButton(text="Grade 9", callback_data="reg_grade_9"),
            InlineKeyboardButton(text="Grade 10", callback_data="reg_grade_10"),
            InlineKeyboardButton(text="Grade 11", callback_data="reg_grade_11"),
            InlineKeyboardButton(text="Grade 12", callback_data="reg_grade_12")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_streams_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    nat_text = get_stream_name_in_lang("Natural Science", lang)
    soc_text = get_stream_name_in_lang("Social Science", lang)
    keyboard = [
        [
            InlineKeyboardButton(text=nat_text, callback_data="reg_stream_Natural Science"),
            InlineKeyboardButton(text=soc_text, callback_data="reg_stream_Social Science")
        ],
        [
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="reg_confirm_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_languages_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="reg_lang_English"),
            InlineKeyboardButton(text="🌿 Afaan Oromoo", callback_data="reg_lang_Afaan Oromoo")
        ],
        [
            InlineKeyboardButton(text="🇪🇹 አማርኛ (Amharic)", callback_data="reg_lang_Amharic")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subjects_selection_keyboard(
    selected_subjects: List[str], 
    grade: Optional[str] = None,
    stream: Optional[str] = None,
    lang: str = "English"
) -> InlineKeyboardMarkup:
    available_subjects = config.get_curriculum_subjects(grade, stream)
        
    keyboard = []
    row = []
    for subj in available_subjects:
        if subj not in config.SUBJECTS:
            continue
        is_selected = subj in selected_subjects
        emoji = config.SUBJECTS[subj].get("emoji", "📚")
        mark = "✅" if is_selected else "⬜"
        loc_name = get_subject_name_in_lang(subj, lang)
        btn_text = f"{mark} {emoji} {loc_name}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"reg_sub_tog_{subj}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    count = len(selected_subjects)
    keyboard.append([
        InlineKeyboardButton(text=t("reg_btn_done_subjects", lang, count=count), callback_data="reg_sub_done")
    ])
    keyboard.append([
        InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="reg_confirm_cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_payment_summary_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=t("btn_proceed_payment", lang), callback_data="reg_pay_proceed")],
        [
            InlineKeyboardButton(text=t("btn_edit_subjects", lang), callback_data="reg_pay_edit"),
            InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="reg_confirm_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        await safe_reply(message, "Please enter a valid full name:")
        return
        
    await state.update_data(full_name=name)
    await state.set_state(RegistrationStates.waiting_for_phone)
    
    data = await state.get_data()
    lang = data.get("language", "English")
    
    await message.answer(
        t("reg_ask_phone", lang),
        parse_mode="HTML",
        reply_markup=get_phone_keyboard(lang)
    )

@router.message(RegistrationStates.waiting_for_phone, F.contact)
@router.message(RegistrationStates.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    phone = ""
    if message.contact:
        phone = message.contact.phone_number or ""
    elif message.text:
        text = message.text.strip()
        if text in ["❌ Cancel", "❌ ሰርዝ", "❌ Dhiisi"]:
            await state.clear()
            await message.answer("❌ Registration cancelled.", reply_markup=ReplyKeyboardRemove())
            return
        phone = text
        
    if not phone or len(phone) < 7:
        await message.answer("Please enter a valid phone number (e.g. `0912345678`):", parse_mode="HTML")
        return
        
    await state.update_data(phone_number=phone)
    await state.set_state(RegistrationStates.waiting_for_grade)
    
    data = await state.get_data()
    lang = data.get("language", "English")
    
    await message.answer(
        t("reg_ask_grade", lang),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await safe_reply(
        message,
        t("reg_ask_grade", lang),
        reply_markup=get_grades_keyboard()
    )

@router.callback_query(F.data.startswith("reg_grade_"))
async def process_grade_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    grade_val = callback.data.split("reg_grade_")[1]
    
    student = await student_service.get_student(telegram_id)
    if student and student.approval_status == 'APPROVED':
        await state.clear()
        await safe_edit(
            callback.message,
            "🔒 Grade Level & Courses Locked\n━━━━━━━━━━━━━━━━━━━━\n"
            "Your registered grade is locked for security and curriculum consistency.\n\n"
            "To request a grade level update or add more courses, please contact support:\n"
            "• 💬 Telegram: [@Cs1At07](https://t.me/Cs1At07)\n"
            "• 📱 Phone: `0928892344`"
        )
        return
        
    await state.update_data(grade=grade_val)
    data = await state.get_data()
    lang = data.get("language", "English")
    
    if grade_val in ["11", "12"]:
        await state.set_state(RegistrationStates.waiting_for_stream)
        await safe_edit(
            callback.message,
            t("reg_ask_stream", lang, grade=grade_val),
            reply_markup=get_streams_keyboard(lang)
        )
    else:
        await state.set_state(RegistrationStates.waiting_for_language)
        await safe_edit(
            callback.message,
            "🌐 Select your preferred language:",
            reply_markup=get_languages_keyboard()
        )

@router.callback_query(F.data.startswith("reg_stream_"), RegistrationStates.waiting_for_stream)
async def process_stream_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    stream_val = callback.data.split("reg_stream_")[1]
    await state.update_data(stream=stream_val)
    await state.set_state(RegistrationStates.waiting_for_language)
    
    await safe_edit(
        callback.message,
        "🌐 Select your preferred language:",
        reply_markup=get_languages_keyboard()
    )

@router.callback_query(F.data.startswith("reg_lang_"))
async def process_language_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    lang_raw = callback.data.split("reg_lang_")[1]
    lang = "English"
    if "Amharic" in lang_raw:
        lang = "Amharic"
    elif "Afaan" in lang_raw or "Oromo" in lang_raw:
        lang = "Afaan Oromoo"
        
    student = await student_service.get_student(telegram_id)
    if student and student.approval_status == 'APPROVED':
        await student_service.update_language(telegram_id, lang)
        await state.clear()
        await safe_edit(callback.message, f"✅ Language updated to {lang}!")
        from bot.handlers.start import send_student_dashboard
        await send_student_dashboard(callback.message, telegram_id)
        return
        
    await state.update_data(language=lang, selected_courses=[])
    await state.set_state(RegistrationStates.waiting_for_subjects)
    
    data = await state.get_data()
    grade = data.get("grade")
    stream = data.get("stream")
    price = await student_service.get_course_price()
    prompt_text = t("reg_ask_subjects", lang, price=price)
    
    await safe_edit(
        callback.message,
        prompt_text,
        reply_markup=get_subjects_selection_keyboard([], grade=grade, stream=stream, lang=lang)
    )

@router.callback_query(F.data.startswith("reg_sub_tog_"), RegistrationStates.waiting_for_subjects)
async def process_subject_toggle_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    subj = callback.data.split("reg_sub_tog_")[1]
    
    data = await state.get_data()
    selected_courses: List[str] = list(data.get("selected_courses", []))
    lang = data.get("language", "English")
    grade = data.get("grade")
    stream = data.get("stream")
    
    if subj in selected_courses:
        selected_courses.remove(subj)
    else:
        selected_courses.append(subj)
        
    await state.update_data(selected_courses=selected_courses)
    
    price = await student_service.get_course_price()
    prompt_text = t("reg_ask_subjects", lang, price=price)
    
    await safe_edit(
        callback.message,
        prompt_text,
        reply_markup=get_subjects_selection_keyboard(selected_courses, grade=grade, stream=stream, lang=lang)
    )

@router.callback_query(F.data == "reg_sub_done", RegistrationStates.waiting_for_subjects)
async def process_subjects_done_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_courses: List[str] = list(data.get("selected_courses", []))
    lang = data.get("language", "English")
    
    if not selected_courses:
        await callback.answer(t("reg_no_subjects_error", lang), show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception:
        pass
        
    grade = data.get("grade", "10")
    name = data.get("full_name", "Student")
    phone = data.get("phone_number", "N/A")
    username = callback.from_user.username or "N/A"
    
    price = await student_service.get_course_price()
    total_amount, price_details = student_service.calculate_student_payment(grade, len(selected_courses), price)
    await state.update_data(payment_amount=total_amount)
    await state.set_state(RegistrationStates.waiting_for_payment_confirmation)
    
    if price_details["is_grade_12_package"]:
        courses_formatted = "\n".join([f"{idx}. {get_subject_name_in_lang(c, lang)} (Grades 9, 10, 11 & 12 Complete Review)" for idx, c in enumerate(selected_courses, 1)])
        pricing_breakdown = (
            f"🎓 Grade 12 Entrance Exam Bundle:\n"
            f"• Grade 12 Course: *{price} ETB*\n"
            f"• Grades 9, 10, 11 Review Access (75% OFF): *+{price_details['review_fee_per_course']} ETB*\n"
            f"• Bundle Price per Course: *{price_details['per_course_bundle']} ETB*\n"
            f"💵 Total Amount: *{total_amount} ETB*"
        )
        summary_text = (
            f"📋 Registration & Payment Summary\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Full Name: {name}\n"
            f"📱 Phone: `{phone}`\n"
            f"🏷️ Username: @{username}\n"
            f"🎓 Grade: Grade {grade} (ESSLCE National Exam Prep)\n"
            f"🌐 Language: {lang}\n\n"
            f"📚 Selected Courses ({len(selected_courses)}):\n"
            f"{courses_formatted}\n\n"
            f"{pricing_breakdown}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Click below to view payment instructions:"
        )
    else:
        courses_formatted = "\n".join([f"{idx}. {get_subject_name_in_lang(c, lang)}" for idx, c in enumerate(selected_courses, 1)])
        summary_text = t(
            "reg_payment_summary",
            lang,
            name=name,
            phone=phone,
            username=username,
            grade=grade,
            language=lang,
            count=len(selected_courses),
            courses=courses_formatted,
            price=price,
            total=total_amount
        )
    
    await safe_edit(
        callback.message,
        summary_text,
        reply_markup=get_payment_summary_keyboard(lang)
    )

@router.callback_query(F.data == "reg_pay_edit", RegistrationStates.waiting_for_payment_confirmation)
async def process_payment_edit_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    data = await state.get_data()
    selected_courses: List[str] = list(data.get("selected_courses", []))
    lang = data.get("language", "English")
    grade = data.get("grade")
    stream = data.get("stream")
    price = await student_service.get_course_price()
    
    await state.set_state(RegistrationStates.waiting_for_subjects)
    await safe_edit(
        callback.message,
        t("reg_ask_subjects", lang, price=price),
        reply_markup=get_subjects_selection_keyboard(selected_courses, grade=grade, stream=stream, lang=lang)
    )

@router.callback_query(F.data == "reg_pay_proceed", RegistrationStates.waiting_for_payment_confirmation)
async def process_payment_proceed_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    data = await state.get_data()
    lang = data.get("language", "English")
    selected_courses = list(data.get("selected_courses", []))
    grade = data.get("grade", "10")
    price = await student_service.get_course_price()
    total_amount, _ = student_service.calculate_student_payment(grade, len(selected_courses), price)
    
    await student_service.register_student_full(
        telegram_id=telegram_id,
        first_name=data.get("full_name", callback.from_user.first_name),
        username=callback.from_user.username,
        phone_number=data.get("phone_number"),
        grade=grade,
        preferred_language=lang,
        selected_courses=selected_courses,
        payment_amount=total_amount,
        approval_status='PAYMENT_PENDING'
    )
    
    await state.set_state(RegistrationStates.waiting_for_payment_screenshot)
    
    payment_card = t(
        "payment_instructions_card",
        lang,
        owner=config.PAYMENT_OWNER_NAME,
        cbe=config.PAYMENT_CBE_ACCOUNT,
        telebirr=config.PAYMENT_TELEBIRR_PHONE,
        count=len(selected_courses),
        price=price,
        total=total_amount
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="reg_confirm_cancel")]
    ])
    await safe_edit(callback.message, payment_card, reply_markup=kb)

@router.message(RegistrationStates.waiting_for_payment_screenshot, F.photo)
@router.message(RegistrationStates.waiting_for_payment_screenshot, F.document)
async def process_payment_screenshot(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        doc = message.document
        mime = doc.mime_type or ""
        if "image" in mime or "pdf" in mime or doc.file_name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            file_id = doc.file_id
            
    if not file_id:
        await safe_reply(message, "Please upload a valid image or PDF screenshot of your payment receipt.")
        return
        
    thinking = await message.answer("⏳ Processing your payment receipt...")
    
    try:
        os.makedirs(config.PAYMENT_RECEIPTS_DIR, exist_ok=True)
        file = await message.bot.get_file(file_id)
        file_ext = os.path.splitext(file.file_path)[1] if file.file_path else ".jpg"
        save_filename = f"receipt_{telegram_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
        save_path = os.path.join(config.PAYMENT_RECEIPTS_DIR, save_filename)
        
        file_bytes = io.BytesIO()
        await message.bot.download_file(file.file_path, file_bytes)
        with open(save_path, "wb") as f:
            f.write(file_bytes.getvalue())
            
        await student_service.submit_payment_screenshot(telegram_id, file_id, save_path)
        await state.clear()
        
        try:
            await thinking.delete()
        except Exception:
            pass
            
        courses_count = len(student.selected_courses) if student else 1
        amount = student.payment_amount if student else 50
        student_ack = t("payment_submitted_student_notify", lang, count=courses_count, total=amount)
        await safe_reply(message, student_ack)
        
        courses_list_str = "\n".join([f"• {c}" for c in (student.selected_courses if student else [])])
        if not courses_list_str:
            courses_list_str = "• All Subjects"
            
        admin_card = (
            "🔔 New Student Registration & Payment\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {student.first_name if student else message.from_user.first_name}\n"
            f"📱 Phone: `{student.phone_number if student else 'N/A'}`\n"
            f"🆔 Telegram ID: `{telegram_id}`\n"
            f"🏷️ Username: @{student.username if student and student.username else (message.from_user.username or 'N/A')}\n"
            f"🎓 Grade: {student.grade if student else 'Not Set'}\n"
            f"🌐 Language: {student.preferred_language if student else 'English'}\n\n"
            f"📚 Selected Courses:\n{courses_list_str}\n\n"
            f"💰 Amount: {amount} ETB\n"
            f"📊 Status: PAYMENT_SUBMITTED\n"
            f"📅 Submitted: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve_{telegram_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject_{telegram_id}")
            ]
        ])
        
        for admin_id in config.ADMIN_IDS:
            try:
                if message.photo:
                    await message.bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id,
                        caption=admin_card,
                        parse_mode="HTML",
                        reply_markup=admin_kb
                    )
                else:
                    await message.bot.send_document(
                        chat_id=admin_id,
                        document=file_id,
                        caption=admin_card,
                        parse_mode="HTML",
                        reply_markup=admin_kb
                    )
            except Exception as ae:
                logging.error(f"Error sending payment notification to admin {admin_id}: {ae}")
                
    except Exception as e:
        logging.error(f"Error handling payment screenshot: {e}", exc_info=True)
        await safe_edit(thinking, t("ai_error", lang))

@router.callback_query(F.data == "reg_confirm_cancel")
async def cancel_registration_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = getattr(callback.from_user, "id", None)
    student = None
    if isinstance(telegram_id, int):
        student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.clear()
    await safe_edit(callback.message, t("reg_cancelled", lang))
process_cancel_callback = cancel_registration_callback
process_confirm_submit_callback = process_payment_proceed_callback

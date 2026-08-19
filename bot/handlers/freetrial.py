import json
import asyncio
import logging
from typing import List, Optional
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

import config
from bot.database.database import has_used_free_trial_sync, record_free_trial_usage_sync
from bot.services import student_service, quiz_service
from bot.services.i18n import t, get_subject_name_in_lang
from bot.utils import safe_reply, safe_edit
from bot.keyboards.quiz import get_quiz_options_keyboard

router = Router()

class FreeTrialStates(StatesGroup):
    waiting_for_grade = State()
    waiting_for_subject = State()
    in_trial_quiz = State()

def get_trial_grade_keyboard(lang: str = "English") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Grade 5", callback_data="trial_grade_5"),
            InlineKeyboardButton(text="Grade 6", callback_data="trial_grade_6"),
            InlineKeyboardButton(text="Grade 7", callback_data="trial_grade_7"),
            InlineKeyboardButton(text="Grade 8", callback_data="trial_grade_8")
        ],
        [
            InlineKeyboardButton(text="Grade 9", callback_data="trial_grade_9"),
            InlineKeyboardButton(text="Grade 10", callback_data="trial_grade_10"),
            InlineKeyboardButton(text="Grade 11", callback_data="trial_grade_11"),
            InlineKeyboardButton(text="Grade 12", callback_data="trial_grade_12")
        ],
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="trial_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_trial_subjects_keyboard(grade: str, lang: str = "English") -> InlineKeyboardMarkup:
    curriculum = config.get_curriculum_subjects(grade=grade)
    buttons = []
    row = []
    for subj in curriculum:
        emoji = config.SUBJECTS.get(subj, {}).get("emoji", "📚")
        loc_name = get_subject_name_in_lang(subj, lang)
        row.append(InlineKeyboardButton(text=f"{emoji} {loc_name}", callback_data=f"trial_subj_{subj}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="trial_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("freetrial"))
@router.message(Command("trial"))
@router.callback_query(F.data == "trial_start")
async def start_free_trial(event: Message | CallbackQuery, state: FSMContext):
    telegram_id = event.from_user.id
    message = event if isinstance(event, Message) else event.message

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except Exception:
            pass

    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    used = await asyncio.to_thread(has_used_free_trial_sync, telegram_id)
    if used and not (student and student.approval_status == "APPROVED"):
        text = t("trial_already_used", lang)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Register & Enroll Now", callback_data="reg_start")]
        ])
        await safe_reply(message, text, reply_markup=kb)
        return

    await state.set_state(FreeTrialStates.waiting_for_grade)
    text = t("trial_ask_grade", lang)
    reply_markup = get_trial_grade_keyboard(lang)
    await safe_reply(message, text, reply_markup=reply_markup)

@router.callback_query(F.data == "trial_cancel")
async def cancel_free_trial(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    await state.clear()
    await safe_edit(callback.message, "❌ Free Trial cancelled. Send /start to register whenever you are ready!")

@router.callback_query(F.data.startswith("trial_grade_"), FreeTrialStates.waiting_for_grade)
async def process_trial_grade(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    grade = callback.data.split("trial_grade_")[1]
    await state.update_data(trial_grade=grade)
    await state.set_state(FreeTrialStates.waiting_for_subject)

    student = await student_service.get_student(callback.from_user.id)
    lang = student.preferred_language if student else "English"

    text = t("trial_ask_subject", lang, grade=grade)
    reply_markup = get_trial_subjects_keyboard(grade, lang)
    await safe_edit(callback.message, text, reply_markup=reply_markup)

@router.callback_query(F.data.startswith("trial_subj_"), FreeTrialStates.waiting_for_subject)
async def process_trial_subject(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    subj = callback.data.split("trial_subj_")[1]
    data = await state.get_data()
    grade = data.get("trial_grade", "10")

    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    used = await asyncio.to_thread(has_used_free_trial_sync, telegram_id)
    if used and not (student and student.approval_status == "APPROVED"):
        text = t("trial_already_used", lang)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Register & Enroll Now", callback_data="reg_start")]
        ])
        await safe_edit(callback.message, text, reply_markup=kb)
        return

    await asyncio.to_thread(record_free_trial_usage_sync, telegram_id, grade, subj)

    topic_name = f"Free Trial (Grade {grade} Sample Practice)"
    quiz_session = await quiz_service.create_quiz_session(
        telegram_id=telegram_id,
        learning_session_id=0,
        subject=subj,
        topic=topic_name,
        total_questions=3
    )

    await state.update_data(quiz_session_id=quiz_session.id)
    await state.set_state(FreeTrialStates.in_trial_quiz)

    thinking_msg = await callback.message.answer(t("quiz_generating", lang))
    try:
        question = await quiz_service.generate_and_save_question(quiz_session)
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        if not question:
            await callback.message.answer(t("ai_error", lang))
            return

        options = json.loads(question.options_json)
        sub_info = config.SUBJECTS.get(subj, {})
        sub_emoji = sub_info.get("emoji", "🎁")

        text = t(
            "quiz_question_header",
            lang,
            emoji=sub_emoji,
            topic=topic_name,
            num=question.question_number,
            total=quiz_session.total_questions,
            text=question.question_text,
            opt_a=options.get('A', ''),
            opt_b=options.get('B', ''),
            opt_c=options.get('C', ''),
            opt_d=options.get('D', '')
        )
        await safe_reply(
            callback.message,
            text,
            reply_markup=get_quiz_options_keyboard(quiz_session.id, question.id)
        )
    except Exception as e:
        logging.error(f"Error starting free trial quiz: {e}", exc_info=True)
        await callback.message.answer(t("ai_error", lang))

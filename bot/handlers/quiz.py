import json
import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery

from config import SUBJECTS
from bot.database.repositories import quiz as quiz_repo
from bot.services import student_service, learning_service, quiz_service
from bot.keyboards.quiz import get_quiz_options_keyboard, get_quiz_active_keyboard
from bot.services.i18n import t
from bot.utils import safe_reply, safe_edit

router = Router()

async def send_next_quiz_question(message: Message, quiz_session) -> None:
    telegram_id = quiz_session.telegram_id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    thinking_msg = await message.answer(t("tutor_thinking", lang))
    
    try:
        
        question = await quiz_service.generate_and_save_question(quiz_session)
        if not question:
            raise ValueError("Failed to generate question")
            
        options = json.loads(question.options_json)
        sub_info = SUBJECTS.get(quiz_session.subject, {})
        sub_emoji = sub_info.get("emoji", "📚")
        
        text = t(
            "quiz_question_header",
            lang,
            emoji=sub_emoji,
            topic=quiz_session.topic,
            num=question.question_number,
            total=quiz_session.total_questions,
            text=question.question_text,
            opt_a=options.get('A', ''),
            opt_b=options.get('B', ''),
            opt_c=options.get('C', ''),
            opt_d=options.get('D', '')
        )
        await safe_reply(
            message,
            text,
            reply_markup=get_quiz_options_keyboard(quiz_session.id, question.id)
        )
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        
    except Exception as e:
        logging.error(f"Error generating question for quiz {quiz_session.id}: {e}", exc_info=True)
        await safe_edit(thinking_msg, t("ai_error", lang))

@router.callback_query(F.data == "action_quiz", StateFilter(None))
@router.callback_query(F.data == "menu_quiz", StateFilter(None))
async def action_quiz_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass

    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    learning_session = await learning_service.get_active_session(telegram_id)
    if not learning_session:
        registered_courses = student.selected_courses if student else []
        from bot.handlers.study import get_registered_subjects_keyboard
        await safe_reply(
            callback,
            "📚 You don't have an active study session yet.\n\nUse /study or choose one of your registered subjects below to start learning:",
            reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
        )
        return

    active_quiz = await quiz_service.get_active_quiz(telegram_id)
    if active_quiz and (active_quiz.learning_session_id != learning_session.id or active_quiz.subject != learning_session.subject or active_quiz.topic != learning_session.topic):
        await asyncio.to_thread(quiz_repo.set_quiz_status, active_quiz.id, 'CANCELLED')
        active_quiz = None

    if active_quiz:
        await safe_reply(
            callback,
            t("quiz_active_prompt", lang, current=active_quiz.current_question, total=active_quiz.total_questions),
            reply_markup=get_quiz_active_keyboard()
        )
        return
        
    await safe_reply(
        callback,
        t("quiz_mode_title", lang, subject=learning_session.subject, topic=learning_session.topic)
    )
    
    quiz_session = await quiz_service.start_quiz(
        telegram_id, learning_session.id, learning_session.subject, learning_session.topic
    )
    await send_next_quiz_question(callback.message, quiz_session)

@router.message(Command("quiz"), StateFilter(None))
@router.message(F.text.in_(["❓ Quiz", "❓ ጥያቄና መልስ (Quiz)", "❓ Gaaffilee (Quiz)"]), StateFilter(None))
async def quiz_start(message: Message):
    """Handles the /quiz command."""
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return
        
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    learning_session = await learning_service.get_active_session(telegram_id)
    if not learning_session:
        registered_courses = student.selected_courses if student else []
        from bot.handlers.study import get_registered_subjects_keyboard
        await safe_reply(
            message,
            "📚 You don't have an active study session yet.\n\nUse /study or choose one of your registered subjects below to start learning:",
            reply_markup=get_registered_subjects_keyboard(registered_courses, lang)
        )
        return
    active_quiz = await quiz_service.get_active_quiz(telegram_id)
    if active_quiz and (active_quiz.learning_session_id != learning_session.id or active_quiz.subject != learning_session.subject or active_quiz.topic != learning_session.topic):
        await asyncio.to_thread(quiz_repo.set_quiz_status, active_quiz.id, 'CANCELLED')
        active_quiz = None

    if active_quiz:
        await safe_reply(
            message,
            t("quiz_active_prompt", lang, current=active_quiz.current_question, total=active_quiz.total_questions),
            reply_markup=get_quiz_active_keyboard()
        )
        return
        
    await safe_reply(
        message,
        t("quiz_mode_title", lang, subject=learning_session.subject, topic=learning_session.topic)
    )
    
    quiz_session = await quiz_service.start_quiz(
        telegram_id, learning_session.id, learning_session.subject, learning_session.topic
    )
    await send_next_quiz_question(message, quiz_session)

@router.callback_query(F.data == "quiz_active_continue", StateFilter(None))
async def quiz_continue_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass

    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    active_quiz = await quiz_service.get_active_quiz(telegram_id)
    if not active_quiz:
        await safe_reply(callback, "❌ No active quiz found.")
        return
        
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    latest_question = await asyncio.to_thread(
        quiz_repo.get_question_by_number, active_quiz.id, active_quiz.current_question
    )
    
    if latest_question and latest_question.student_answer is None:
        options = json.loads(latest_question.options_json)
        sub_info = SUBJECTS.get(active_quiz.subject, {})
        sub_emoji = sub_info.get("emoji", "📚")
        
        text = t(
            "quiz_question_header",
            lang,
            emoji=sub_emoji,
            topic=active_quiz.topic,
            num=latest_question.question_number,
            total=active_quiz.total_questions,
            text=latest_question.question_text,
            opt_a=options.get('A', ''),
            opt_b=options.get('B', ''),
            opt_c=options.get('C', ''),
            opt_d=options.get('D', '')
        )
        await safe_reply(
            callback,
            text,
            reply_markup=get_quiz_options_keyboard(active_quiz.id, latest_question.id)
        )
    else:
        await send_next_quiz_question(callback.message, active_quiz)

@router.callback_query(F.data == "quiz_active_cancel", StateFilter(None))
async def quiz_cancel_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass

    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await quiz_service.cancel_quiz(telegram_id)
    await safe_edit(
        callback.message,
        "❌ Quiz Cancelled\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Your quiz result was not counted.\n"
        "Your study session is still saved.\n\n"
        "💡 Use /quiz to start a new one, or continue studying."
    )

@router.callback_query(F.data.startswith("quiz_ans_"), StateFilter(None))
async def quiz_answer_callback(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    parts = callback.data.split("_ans_")[1].split("_")
    session_id = int(parts[0])
    question_id = int(parts[1])
    choice = parts[2]
    
    quiz_session = await asyncio.to_thread(quiz_repo.get_quiz_session_by_id, session_id)
    question = await asyncio.to_thread(quiz_repo.get_question_by_id, question_id)
    
    if not quiz_session or not question:
        await callback.answer("Quiz information not found.", show_alert=True)
        return
        
    if quiz_session.telegram_id != telegram_id:
        await callback.answer("This quiz does not belong to you!", show_alert=True)
        return
        
    if quiz_session.status != "ACTIVE":
        await callback.answer("This quiz is no longer active.", show_alert=True)
        return
        
    if question.student_answer is not None:
        await callback.answer(
            "This question has already been answered. Please continue with the next question.",
            show_alert=True
        )
        return
        
    try:
        is_correct, explanation, updated_session = await quiz_service.evaluate_answer(
            telegram_id, quiz_session, question, choice
        )
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception:
        pass
        
    options = json.loads(question.options_json)
    chosen_text = options.get(choice, "")
    correct_option = question.correct_answer
    correct_text = options.get(correct_option, "")
    
    sub_info = SUBJECTS.get(quiz_session.subject, {})
    sub_emoji = sub_info.get("emoji", "📚")
    
    feedback_emoji = t("quiz_correct", lang) if is_correct else t("quiz_incorrect", lang)
    correct_reveal = "" if is_correct else t("quiz_correct_reveal", lang, correct_key=correct_option, correct_text=correct_text)
    
    text = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{sub_emoji}  {quiz_session.topic} — Quiz\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 Question {question.question_number} of {quiz_session.total_questions}\n\n"
        f"{question.question_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🇦  {options.get('A', '')}\n"
        f"🇧  {options.get('B', '')}\n"
        f"🇨  {options.get('C', '')}\n"
        f"🇩  {options.get('D', '')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 Your answer: {choice}. {chosen_text}\n\n"
        f"{feedback_emoji}\n"
        f"{correct_reveal}\n"
        f"📝 {explanation}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Score: {updated_session.correct_answers}/{question.question_number}"
    )
    
    await safe_edit(callback.message, text, reply_markup=None)
    
    if updated_session.status == "COMPLETED":
        score = updated_session.correct_answers
        total = updated_session.total_questions
        pct = int((score / total) * 100) if total > 0 else 0
        
        if pct >= 80:
            medal = "🥇"
            verdict = "Excellent work!"
        elif pct >= 60:
            medal = "🥈"
            verdict = "Good effort! Keep it up."
        else:
            medal = "🥉"
            verdict = "Keep practicing — you'll get there!"
        
        from bot.database.repositories import tests as test_repo
        letter_grade = "A+" if pct >= 90 else ("A" if pct >= 80 else ("B" if pct >= 70 else ("C" if pct >= 60 else "D")))
        try:
            await asyncio.to_thread(
                test_repo.save_test_result,
                telegram_id=telegram_id,
                subject=updated_session.subject,
                topic=updated_session.topic,
                questions_text=f"{total} questions test on {updated_session.topic}",
                student_answers=f"{score} correct out of {total}",
                score=score,
                max_score=total,
                letter_grade=letter_grade,
                feedback=f"Completed test with score {score}/{total} ({pct}%). {verdict}",
                learning_session_id=updated_session.learning_session_id
            )
        except Exception as e:
            logging.warning(f"Error saving completed test result: {e}")

        summary = t(
            "quiz_complete_title",
            lang,
            emoji=sub_emoji,
            subject=updated_session.subject,
            topic=updated_session.topic,
            score=score,
            incorrect=total - score,
            total=total,
            pct=pct,
            medal=medal,
            verdict=verdict
        )
        await safe_reply(callback, summary)
    else:
        await send_next_quiz_question(callback.message, updated_session)

@router.callback_query(F.data.startswith("quiz_end_"), StateFilter(None))
async def quiz_end_callback(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"

    try:
        session_id = int(callback.data.split("_end_")[1])
    except Exception:
        await callback.answer("❌ Invalid test session.", show_alert=True)
        return

    quiz_session = await asyncio.to_thread(quiz_repo.get_quiz_session_by_id, session_id)
    if not quiz_session or quiz_session.telegram_id != telegram_id:
        await callback.answer("❌ Test session not found.", show_alert=True)
        return

    if quiz_session.status != "ACTIVE":
        await callback.answer("❌ Test is already ended.", show_alert=True)
        return

    await asyncio.to_thread(quiz_repo.set_quiz_status, quiz_session.id, "COMPLETED")

    attempted = max(quiz_session.current_question, 1)
    score = quiz_session.correct_answers
    pct = int((score / attempted) * 100) if attempted > 0 else 0

    if pct >= 90:
        grade = "A+"
        medal = "🏆"
    elif pct >= 80:
        grade = "A"
        medal = "🥇"
    elif pct >= 70:
        grade = "B"
        medal = "🥈"
    elif pct >= 60:
        grade = "C"
        medal = "🥉"
    else:
        grade = "D"
        medal = "📝"

    from bot.database.repositories import tests as test_repo
    try:
        await asyncio.to_thread(
            test_repo.save_test_result,
            telegram_id=telegram_id,
            subject=quiz_session.subject,
            topic=quiz_session.topic,
            questions_text=f"{attempted} questions attempted out of {quiz_session.total_questions}",
            student_answers=f"{score} correct answers",
            score=score,
            max_score=attempted,
            letter_grade=grade,
            feedback=f"Test ended by student with score {score}/{attempted}.",
            learning_session_id=quiz_session.learning_session_id
        )
    except Exception as e:
        logging.warning(f"Error saving early ended test result: {e}")

    try:
        await callback.answer("🛑 Test ended.")
    except Exception:
        pass

    summary = (
        f"🛑 Interactive Test Ended\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 Subject: {quiz_session.subject}\n"
        f"📌 Topic/Chapters: {quiz_session.topic}\n\n"
        f"🎯 Questions Attempted: {attempted} of {quiz_session.total_questions}\n"
        f"✅ Correct Answers: {score}/{attempted} ({pct}%)\n"
        f"🏅 Grade: {grade} {medal}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Test result saved to your profile!"
    )

    await safe_edit(callback.message, summary)

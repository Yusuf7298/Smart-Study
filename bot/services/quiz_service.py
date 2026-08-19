import json
import asyncio
from typing import Optional
from bot.database.repositories import quiz as quiz_repo
from bot.database.models import QuizSessionModel, QuizQuestionModel
from bot.services import student_service, learning_service
from bot.services.gemini import generate_quiz_question

async def get_active_quiz(telegram_id: int) -> Optional[QuizSessionModel]:
    return await asyncio.to_thread(quiz_repo.get_active_quiz_session, telegram_id)

async def start_quiz(
    telegram_id: int,
    learning_session_id: Optional[int] = 0,
    subject: str = "",
    topic: str = "",
    total_questions: int = 5
) -> QuizSessionModel:
    active = await get_active_quiz(telegram_id)
    if active:
        await asyncio.to_thread(quiz_repo.set_quiz_status, active.id, 'CANCELLED')
    
    sess_id = learning_session_id or 0
    return await asyncio.to_thread(quiz_repo.create_quiz_session, telegram_id, sess_id, subject, topic, total_questions)

create_quiz_session = start_quiz

async def cancel_quiz(telegram_id: int) -> None:
    active = await get_active_quiz(telegram_id)
    if active:
        await asyncio.to_thread(quiz_repo.set_quiz_status, active.id, 'CANCELLED')

async def generate_and_save_question(quiz_session: QuizSessionModel) -> Optional[QuizQuestionModel]:
    student = await student_service.get_student(quiz_session.telegram_id)
    if not student:
        raise ValueError("Student not found")
        
    next_question_number = quiz_session.current_question + 1
    
    question_text, options, correct_answer, explanation = await generate_quiz_question(
        student, quiz_session.subject, quiz_session.topic
    )
    
    options_json = json.dumps(options)
    question = await asyncio.to_thread(
        quiz_repo.save_quiz_question,
        quiz_session.id,
        next_question_number,
        question_text,
        options_json,
        correct_answer,
        explanation
    )
    await asyncio.to_thread(quiz_repo.update_session_progress, quiz_session.id, next_question_number)
    
    return question

async def evaluate_answer(
    telegram_id: int,
    quiz_session: QuizSessionModel,
    question: QuizQuestionModel,
    choice: str
) -> tuple[bool, str, QuizSessionModel]:
    if quiz_session.telegram_id != telegram_id:
        raise PermissionError("Ownership mismatch")
        
    if quiz_session.status != "ACTIVE":
        raise ValueError("Quiz is not active")
        
    refreshed_question = await asyncio.to_thread(quiz_repo.get_question_by_id, question.id)
    if refreshed_question.student_answer is not None:
        raise ValueError("Question already answered.")
        
    is_correct = (choice.upper() == refreshed_question.correct_answer.upper())
    
    await asyncio.to_thread(quiz_repo.submit_student_answer, question.id, choice, 1 if is_correct else 0)
    
    if is_correct:
        await asyncio.to_thread(quiz_repo.increment_correct_score, quiz_session.id)
        
    updated_session = await asyncio.to_thread(quiz_repo.get_quiz_session_by_id, quiz_session.id)
    
    if updated_session.current_question >= updated_session.total_questions:
        await asyncio.to_thread(quiz_repo.set_quiz_status, updated_session.id, "COMPLETED")
        updated_session.status = "COMPLETED"
        
        score = updated_session.correct_answers
        if score >= 4:
            new_stage = "REVIEW"
        else:
            new_stage = "PRACTICE"
            
        await learning_service.update_stage(updated_session.learning_session_id, new_stage)
        
    return is_correct, refreshed_question.explanation, updated_session

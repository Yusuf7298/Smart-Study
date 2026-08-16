import json
import asyncio
from typing import Optional
from bot.database.repositories import quiz as quiz_repo
from bot.database.models import QuizSessionModel, QuizQuestionModel
from bot.services import student_service, learning_service
from bot.services.gemini import generate_quiz_question

async def get_active_quiz(telegram_id: int) -> Optional[QuizSessionModel]:
    """Asynchronously fetches the active quiz session for a student."""
    return await asyncio.to_thread(quiz_repo.get_active_quiz_session, telegram_id)

async def start_quiz(telegram_id: int, learning_session_id: int, subject: str, topic: str) -> QuizSessionModel:
    """Asynchronously starts a new active quiz session, cancelling any pre-existing active quizzes."""
    active = await get_active_quiz(telegram_id)
    if active:
        await asyncio.to_thread(quiz_repo.set_quiz_status, active.id, 'CANCELLED')
    
    return await asyncio.to_thread(quiz_repo.create_quiz_session, telegram_id, learning_session_id, subject, topic)

# Alias for backwards compatibility
create_quiz_session = start_quiz

async def cancel_quiz(telegram_id: int) -> None:
    """Asynchronously cancels the student's active quiz session."""
    active = await get_active_quiz(telegram_id)
    if active:
        await asyncio.to_thread(quiz_repo.set_quiz_status, active.id, 'CANCELLED')

async def generate_and_save_question(quiz_session: QuizSessionModel) -> Optional[QuizQuestionModel]:
    """
    Generates a multiple-choice question via Gemini and saves it in the database.
    Increments the current question count in the quiz session.
    """
    student = await student_service.get_student(quiz_session.telegram_id)
    if not student:
        raise ValueError("Student not found")
        
    next_question_number = quiz_session.current_question + 1
    
    # 1. Query Gemini
    question_text, options, correct_answer, explanation = await generate_quiz_question(
        student, quiz_session.subject, quiz_session.topic
    )
    
    # 2. Save in database
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
    
    # 3. Update session question counter
    await asyncio.to_thread(quiz_repo.update_session_progress, quiz_session.id, next_question_number)
    
    return question

async def evaluate_answer(
    telegram_id: int,
    quiz_session: QuizSessionModel,
    question: QuizQuestionModel,
    choice: str
) -> tuple[bool, str, QuizSessionModel]:
    """
    Evaluates the student's MCQ choice against the stored correct answer.
    Enforces double-answering protection and ownership checks.
    Updates the session score and changes the learning stage on quiz completion.
    """
    # 1. Ownership check
    if quiz_session.telegram_id != telegram_id:
        raise PermissionError("Ownership mismatch")
        
    # 2. Active status check
    if quiz_session.status != "ACTIVE":
        raise ValueError("Quiz is not active")
        
    # 3. Prevent double answers
    # Reload question from database to ensure up-to-date answer status
    refreshed_question = await asyncio.to_thread(quiz_repo.get_question_by_id, question.id)
    if refreshed_question.student_answer is not None:
        raise ValueError("Question already answered.")
        
    # 4. Evaluate correctness
    is_correct = (choice.upper() == refreshed_question.correct_answer.upper())
    
    # 5. Submit answer in database
    await asyncio.to_thread(quiz_repo.submit_student_answer, question.id, choice, 1 if is_correct else 0)
    
    # 6. Increment correct score if correct
    if is_correct:
        await asyncio.to_thread(quiz_repo.increment_correct_score, quiz_session.id)
        
    # 7. Reload quiz session
    updated_session = await asyncio.to_thread(quiz_repo.get_quiz_session_by_id, quiz_session.id)
    
    # 8. Check if completed
    if updated_session.current_question >= updated_session.total_questions:
        # Update quiz status to COMPLETED
        await asyncio.to_thread(quiz_repo.set_quiz_status, updated_session.id, "COMPLETED")
        updated_session.status = "COMPLETED"
        
        # Calculate score and transition learning session stage
        score = updated_session.correct_answers
        if score >= 4:
            new_stage = "REVIEW"
        else:
            new_stage = "PRACTICE"
            
        await learning_service.update_stage(updated_session.learning_session_id, new_stage)
        
    return is_correct, refreshed_question.explanation, updated_session

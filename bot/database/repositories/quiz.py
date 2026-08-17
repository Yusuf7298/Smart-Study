import sqlite3
from typing import Optional
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import QuizSessionModel, QuizQuestionModel

def get_quiz_session_by_id(quiz_session_id: int) -> Optional[QuizSessionModel]:
    """Retrieves a quiz session by its database ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, learning_session_id, subject, topic, total_questions, current_question, correct_answers, status, created_at, updated_at
        FROM quiz_sessions
        WHERE id = ?
    """, (quiz_session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return QuizSessionModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        learning_session_id=row['learning_session_id'],
        subject=row['subject'],
        topic=row['topic'],
        total_questions=row['total_questions'],
        current_question=row['current_question'],
        correct_answers=row['correct_answers'],
        status=row['status'],
        created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
        updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if isinstance(row['updated_at'], str) else row['updated_at']
    )

def get_active_quiz_session(telegram_id: int) -> Optional[QuizSessionModel]:
    """Retrieves the current active quiz session for a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, learning_session_id, subject, topic, total_questions, current_question, correct_answers, status, created_at, updated_at
        FROM quiz_sessions
        WHERE telegram_id = ? AND status = 'ACTIVE'
        ORDER BY id DESC
        LIMIT 1
    """, (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    return QuizSessionModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        learning_session_id=row['learning_session_id'],
        subject=row['subject'],
        topic=row['topic'],
        total_questions=row['total_questions'],
        current_question=row['current_question'],
        correct_answers=row['correct_answers'],
        status=row['status'],
        created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
        updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if isinstance(row['updated_at'], str) else row['updated_at']
    )

def create_quiz_session(telegram_id: int, learning_session_id: int, subject: str, topic: str, total_questions: int = 5) -> QuizSessionModel:
    """Creates a new active quiz session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_sessions (telegram_id, learning_session_id, subject, topic, total_questions, current_question, correct_answers, status)
        VALUES (?, ?, ?, ?, ?, 0, 0, 'ACTIVE')
    """, (telegram_id, learning_session_id, subject, topic, total_questions))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_quiz_session_by_id(session_id)

def update_session_progress(quiz_session_id: int, current_question: int) -> None:
    """Updates the session progress counter."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quiz_sessions
        SET current_question = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (current_question, quiz_session_id))
    conn.commit()
    conn.close()

def increment_correct_score(quiz_session_id: int) -> None:
    """Increments the correct answers score counter by 1."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quiz_sessions
        SET correct_answers = correct_answers + 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (quiz_session_id,))
    conn.commit()
    conn.close()

def set_quiz_status(quiz_session_id: int, status: str) -> None:
    """Sets the status of a quiz session (ACTIVE, COMPLETED, CANCELLED)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quiz_sessions
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, quiz_session_id))
    conn.commit()
    conn.close()

def deactivate_all_active_quizzes(telegram_id: int) -> None:
    """Cancels/deactivates any currently ACTIVE quiz sessions for a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quiz_sessions
        SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ? AND status = 'ACTIVE'
    """, (telegram_id,))
    conn.commit()
    conn.close()

def save_quiz_question(
    quiz_session_id: int,
    question_number: int,
    question_text: str,
    options_json: str,
    correct_answer: str,
    explanation: str
) -> QuizQuestionModel:
    """Inserts a generated question into the quiz questions table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_questions (quiz_session_id, question_number, question_text, options_json, correct_answer, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (quiz_session_id, question_number, question_text, options_json, correct_answer, explanation))
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_question_by_id(question_id)

def get_question_by_id(question_id: int) -> QuizQuestionModel:
    """Retrieves a quiz question by database ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, quiz_session_id, question_number, question_text, options_json, correct_answer, explanation, student_answer, is_correct, created_at, answered_at
        FROM quiz_questions
        WHERE id = ?
    """, (question_id,))
    row = cursor.fetchone()
    conn.close()
    
    return QuizQuestionModel(
        id=row['id'],
        quiz_session_id=row['quiz_session_id'],
        question_number=row['question_number'],
        question_text=row['question_text'],
        options_json=row['options_json'],
        correct_answer=row['correct_answer'],
        explanation=row['explanation'],
        student_answer=row['student_answer'],
        is_correct=row['is_correct'],
        created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if isinstance(row['created_at'], str) else row['created_at'],
        answered_at=datetime.fromisoformat(row['answered_at'].replace('Z', '+00:00')) if (isinstance(row['answered_at'], str) and row['answered_at']) else row['answered_at']
    )

def get_question_by_number(quiz_session_id: int, question_number: int) -> Optional[QuizQuestionModel]:
    """Retrieves a specific question from a quiz session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, quiz_session_id, question_number, question_text, options_json, correct_answer, explanation, student_answer, is_correct, created_at, answered_at
        FROM quiz_questions
        WHERE quiz_session_id = ? AND question_number = ?
    """, (quiz_session_id, question_number))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return get_question_by_id(row['id'])

def submit_student_answer(question_id: int, student_answer: str, is_correct: int) -> None:
    """Submits the student's answer to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE quiz_questions
        SET student_answer = ?, is_correct = ?, answered_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (student_answer, is_correct, question_id))
    conn.commit()
    conn.close()

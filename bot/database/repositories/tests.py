import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import TestResultModel

def save_test_result(
    telegram_id: int,
    subject: str,
    topic: str,
    questions_text: str,
    student_answers: str,
    score: int,
    max_score: int = 10,
    letter_grade: str = "B",
    feedback: str = "",
    learning_session_id: Optional[int] = None
) -> TestResultModel:
    """Saves a completed written test evaluation into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO test_results (
            telegram_id, learning_session_id, subject, topic,
            questions_text, student_answers, score, max_score, letter_grade, feedback
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id, learning_session_id, subject, topic,
        questions_text, student_answers, score, max_score, letter_grade, feedback
    ))
    test_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_test_result_by_id(test_id)

def get_test_result_by_id(test_id: int) -> Optional[TestResultModel]:
    """Retrieves a single test result record by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, learning_session_id, subject, topic,
               questions_text, student_answers, score, max_score, letter_grade, feedback, created_at
        FROM test_results
        WHERE id = ?
    """, (test_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_test(row)

def get_student_test_results(telegram_id: int, limit: int = 10) -> List[TestResultModel]:
    """Retrieves past test results for a student in descending order."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, learning_session_id, subject, topic,
               questions_text, student_answers, score, max_score, letter_grade, feedback, created_at
        FROM test_results
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (telegram_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_test(r) for r in rows]

def get_student_test_stats(telegram_id: int) -> Dict[str, Any]:
    """Calculates overall test metrics for a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as test_count,
               AVG(score) as avg_score,
               MAX(score) as max_score
        FROM test_results
        WHERE telegram_id = ?
    """, (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    
    count = row['test_count'] if row else 0
    avg_score = round(float(row['avg_score']), 1) if (row and row['avg_score'] is not None) else 0.0
    return {
        "count": count,
        "avg_score": avg_score,
        "max_score": row['max_score'] if (row and row['max_score'] is not None) else 0
    }

def _row_to_test(row: sqlite3.Row) -> TestResultModel:
    created_at_val = row['created_at']
    if isinstance(created_at_val, str):
        try:
            created_at_val = datetime.fromisoformat(created_at_val.replace('Z', '+00:00'))
        except ValueError:
            created_at_val = datetime.now()
    return TestResultModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        learning_session_id=row['learning_session_id'],
        subject=row['subject'],
        topic=row['topic'],
        questions_text=row['questions_text'],
        student_answers=row['student_answers'],
        score=row['score'] or 0,
        max_score=row['max_score'] or 10,
        letter_grade=row['letter_grade'] or "N/A",
        feedback=row['feedback'] or "",
        created_at=created_at_val
    )

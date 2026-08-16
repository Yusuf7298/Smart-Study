import sqlite3
import asyncio
from typing import Dict, Any, Optional
from bot.database.database import get_db_connection
from bot.database.repositories import tests as test_repo
from bot.database.repositories import materials as mat_repo
from bot.database.repositories import learning as learning_repo

def _calculate_student_progress_sync(telegram_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total lessons / sessions started
    cursor.execute("SELECT COUNT(*) as cnt FROM learning_sessions WHERE telegram_id = ?", (telegram_id,))
    lessons_count = cursor.fetchone()['cnt']
    
    # 2. Total quizzes taken & scores
    cursor.execute("""
        SELECT COUNT(*) as count,
               SUM(total_questions) as total_q,
               SUM(correct_answers) as total_c
        FROM quiz_sessions
        WHERE telegram_id = ? AND status = 'COMPLETED'
    """, (telegram_id,))
    q_row = cursor.fetchone()
    quizzes_count = q_row['count'] if q_row else 0
    total_questions = q_row['total_q'] or 0
    total_correct = q_row['total_c'] or 0
    quiz_avg_pct = int((total_correct / total_questions * 100)) if total_questions > 0 else 0
    
    conn.close()
    
    # 3. Test stats
    test_stats = test_repo.get_student_test_stats(telegram_id)
    
    # 4. PDF count
    pdf_count = mat_repo.count_student_materials(telegram_id)
    
    # 5. Active topic
    active_session = learning_repo.get_active_session_by_id(telegram_id)
    active_topic = f"{active_session.subject} → {active_session.topic}" if active_session else "None"
    
    return {
        "lessons_count": lessons_count,
        "quizzes_count": quizzes_count,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "quiz_avg_pct": quiz_avg_pct,
        "tests_count": test_stats["count"],
        "test_avg_score": test_stats["avg_score"],
        "pdf_count": pdf_count,
        "active_topic": active_topic
    }

async def get_student_progress(telegram_id: int) -> Dict[str, Any]:
    """Asynchronously calculates real academic progress metrics for a student."""
    return await asyncio.to_thread(_calculate_student_progress_sync, telegram_id)

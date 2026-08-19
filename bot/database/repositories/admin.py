import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import StudentModel, AdminLogModel
from bot.database.repositories.student import _row_to_student

def log_admin_action(admin_id: int, action: str, target_id: Optional[int] = None, details: Optional[str] = None) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO admin_logs (admin_id, action, target_id, details)
        VALUES (?, ?, ?, ?)
    """, (admin_id, action, target_id, details))
    conn.commit()
    conn.close()

def get_admin_dashboard_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM students")
    total_students = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as approved FROM students WHERE approval_status = 'APPROVED'")
    approved_students = cursor.fetchone()['approved']
    
    cursor.execute("SELECT COUNT(*) as pending FROM students WHERE approval_status IN ('PENDING', 'PAYMENT_PENDING', 'PAYMENT_SUBMITTED', 'REGISTRATION_PENDING')")
    pending_students = cursor.fetchone()['pending']
    
    cursor.execute("SELECT COUNT(*) as rejected FROM students WHERE approval_status = 'REJECTED'")
    rejected_students = cursor.fetchone()['rejected']
    
    cursor.execute("SELECT COUNT(*) as sessions FROM learning_sessions")
    total_sessions = cursor.fetchone()['sessions']
    
    cursor.execute("SELECT COUNT(*) as quizzes FROM quiz_sessions WHERE status = 'COMPLETED'")
    total_quizzes = cursor.fetchone()['quizzes']
    
    cursor.execute("SELECT COUNT(*) as tests FROM test_results")
    total_tests = cursor.fetchone()['tests']
    
    cursor.execute("SELECT COUNT(*) as pdfs FROM study_materials WHERE is_deleted = 0")
    total_pdfs = cursor.fetchone()['pdfs']
    
    conn.close()
    
    return {
        "total_students": total_students,
        "approved_students": approved_students,
        "pending_students": pending_students,
        "rejected_students": rejected_students,
        "total_sessions": total_sessions,
        "total_quizzes": total_quizzes,
        "total_tests": total_tests,
        "total_pdfs": total_pdfs
    }

def get_pending_students(limit: int = 20) -> List[StudentModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM students
        WHERE approval_status IN ('PENDING', 'PAYMENT_PENDING', 'PAYMENT_SUBMITTED', 'REGISTRATION_PENDING')
        ORDER BY updated_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_student(r) for r in rows]

def get_students_by_status(status: str, limit: int = 20) -> List[StudentModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM students
        WHERE approval_status = ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (status, limit))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_student(r) for r in rows]

def search_students(query: str, limit: int = 20) -> List[StudentModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    search_param = f"%{query.strip()}%"
    cursor.execute("""
        SELECT *
        FROM students
        WHERE first_name LIKE ? OR username LIKE ? OR phone_number LIKE ? OR CAST(telegram_id AS TEXT) LIKE ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (search_param, search_param, search_param, search_param, limit))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_student(r) for r in rows]

def get_all_approved_student_ids() -> List[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM students WHERE approval_status = 'APPROVED'")
    rows = cursor.fetchall()
    conn.close()
    return [r['telegram_id'] for r in rows]

def get_admin_logs(limit: int = 20) -> List[AdminLogModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, admin_id, action, target_id, details, created_at
        FROM admin_logs
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for r in rows:
        c_at = r['created_at']
        if isinstance(c_at, str):
            try:
                c_at = datetime.fromisoformat(c_at.replace('Z', '+00:00'))
            except ValueError:
                c_at = datetime.now()
        logs.append(
            AdminLogModel(
                id=r['id'],
                admin_id=r['admin_id'],
                action=r['action'],
                target_id=r['target_id'],
                details=r['details'],
                created_at=c_at
            )
        )
    return logs

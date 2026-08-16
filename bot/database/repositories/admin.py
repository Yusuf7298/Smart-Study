import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import StudentModel, AdminLogModel

def log_admin_action(admin_id: int, action: str, target_id: Optional[int] = None, details: Optional[str] = None) -> None:
    """Logs an administrative action (APPROVE, REJECT, BROADCAST) to the admin_logs table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO admin_logs (admin_id, action, target_id, details)
        VALUES (?, ?, ?, ?)
    """, (admin_id, action, target_id, details))
    conn.commit()
    conn.close()

def get_admin_dashboard_stats() -> Dict[str, Any]:
    """Aggregates system-wide analytics for the administrator control dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM students")
    total_students = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as approved FROM students WHERE approval_status = 'APPROVED'")
    approved_students = cursor.fetchone()['approved']
    
    cursor.execute("SELECT COUNT(*) as pending FROM students WHERE approval_status = 'PENDING'")
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
    """Retrieves all students currently waiting for administrator approval."""
    return get_students_by_status("PENDING", limit)

def get_students_by_status(status: str, limit: int = 20) -> List[StudentModel]:
    """Retrieves students by approval status (PENDING, APPROVED, REJECTED)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, telegram_id, first_name, username, grade, education_level,
               preferred_language, approval_status, created_at, updated_at
        FROM students
        WHERE approval_status = ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (status, limit))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_student(r) for r in rows]

def search_students(query: str, limit: int = 20) -> List[StudentModel]:
    """Searches students by name, username, or telegram_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    search_param = f"%{query.strip()}%"
    cursor.execute("""
        SELECT id, telegram_id, first_name, username, grade, education_level,
               preferred_language, approval_status, created_at, updated_at
        FROM students
        WHERE first_name LIKE ? OR username LIKE ? OR CAST(telegram_id AS TEXT) LIKE ?
        ORDER BY updated_at DESC
        LIMIT ?
    """, (search_param, search_param, search_param, limit))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_student(r) for r in rows]

def get_all_approved_student_ids() -> List[int]:
    """Retrieves all Telegram IDs of approved students (for broadcasts)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM students WHERE approval_status = 'APPROVED'")
    rows = cursor.fetchall()
    conn.close()
    return [r['telegram_id'] for r in rows]

def get_admin_logs(limit: int = 15) -> List[AdminLogModel]:
    """Retrieves recent administrator action logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, admin_id, action, target_id, details, created_at
        FROM admin_logs
        ORDER BY id DESC
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

def _row_to_student(row: sqlite3.Row) -> StudentModel:
    c_at = row['created_at']
    if isinstance(c_at, str):
        try:
            c_at = datetime.fromisoformat(c_at.replace('Z', '+00:00'))
        except ValueError:
            c_at = datetime.now()
    u_at = row['updated_at']
    if isinstance(u_at, str):
        try:
            u_at = datetime.fromisoformat(u_at.replace('Z', '+00:00'))
        except ValueError:
            u_at = datetime.now()
    return StudentModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        first_name=row['first_name'],
        username=row['username'],
        grade=row['grade'],
        education_level=row['education_level'],
        preferred_language=row['preferred_language'],
        approval_status=row['approval_status'],
        created_at=c_at,
        updated_at=u_at
    )

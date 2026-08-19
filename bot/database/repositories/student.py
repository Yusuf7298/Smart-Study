import sqlite3
import json
from typing import Optional, List, Any
from datetime import datetime
from bot.database.database import get_db_connection
from bot.database.models import StudentModel

def _row_to_student(row: sqlite3.Row) -> StudentModel:
    def parse_dt(val: Any) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace('Z', '+00:00'))
            except Exception:
                return None
        return val

    keys = row.keys()
    return StudentModel(
        id=row['id'],
        telegram_id=row['telegram_id'],
        first_name=row['first_name'],
        username=row['username'],
        grade=row['grade'],
        education_level=row['education_level'],
        preferred_language=row['preferred_language'] or 'English',
        approval_status=row['approval_status'] or 'REGISTRATION_PENDING',
        phone_number=row['phone_number'] if 'phone_number' in keys else None,
        selected_courses_json=row['selected_courses_json'] if 'selected_courses_json' in keys else "[]",
        payment_amount=row['payment_amount'] if 'payment_amount' in keys else 0,
        payment_screenshot_file_id=row['payment_screenshot_file_id'] if 'payment_screenshot_file_id' in keys else None,
        payment_screenshot_path=row['payment_screenshot_path'] if 'payment_screenshot_path' in keys else None,
        payment_submitted_at=parse_dt(row['payment_submitted_at']) if 'payment_submitted_at' in keys else None,
        approved_at=parse_dt(row['approved_at']) if 'approved_at' in keys else None,
        rejected_reason=row['rejected_reason'] if 'rejected_reason' in keys else None,
        has_exam_package=bool(row['has_exam_package']) if 'has_exam_package' in keys and row['has_exam_package'] is not None else False,
        created_at=parse_dt(row['created_at']) if 'created_at' in keys else None,
        updated_at=parse_dt(row['updated_at']) if 'updated_at' in keys else None
    )

def get_student_by_id(telegram_id: int) -> Optional[StudentModel]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM students
        WHERE telegram_id = ?
    """, (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_student(row)

def create_student(telegram_id: int, first_name: Optional[str], username: Optional[str]) -> StudentModel:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO students (telegram_id, first_name, username, approval_status)
        VALUES (?, ?, ?, 'APPROVED')
    """, (telegram_id, first_name, username))
    conn.commit()
    conn.close()
    return get_student_by_id(telegram_id) # type: ignore

def register_full_student(
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
    phone_number: Optional[str],
    grade: str,
    education_level: str,
    preferred_language: str,
    selected_courses: List[str],
    payment_amount: int,
    approval_status: str = 'PAYMENT_PENDING',
    has_exam_package: bool = False
) -> StudentModel:
    conn = get_db_connection()
    cursor = conn.cursor()
    courses_json = json.dumps(selected_courses, ensure_ascii=False)
    has_exam_int = 1 if has_exam_package else 0
    
    cursor.execute("SELECT id FROM students WHERE telegram_id = ?", (telegram_id,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("""
            UPDATE students
            SET first_name = ?, username = ?, phone_number = ?, grade = ?, education_level = ?,
                preferred_language = ?, selected_courses_json = ?, payment_amount = ?,
                approval_status = ?, has_exam_package = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        """, (
            first_name, username, phone_number, str(grade), education_level,
            preferred_language, courses_json, payment_amount, approval_status, has_exam_int, telegram_id
        ))
    else:
        cursor.execute("""
            INSERT INTO students (
                telegram_id, first_name, username, phone_number, grade, education_level,
                preferred_language, selected_courses_json, payment_amount, approval_status, has_exam_package
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telegram_id, first_name, username, phone_number, str(grade), education_level,
            preferred_language, courses_json, payment_amount, approval_status, has_exam_int
        ))
    conn.commit()
    conn.close()
    return get_student_by_id(telegram_id) # type: ignore

def set_exam_package_access(telegram_id: int, has_access: bool = True) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    val = 1 if has_access else 0
    cursor.execute("""
        UPDATE students
        SET has_exam_package = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (val, telegram_id))
    conn.commit()
    conn.close()

def register_pending_student(
    telegram_id: int,
    first_name: Optional[str],
    username: Optional[str],
    grade: Any,
    education_level: str,
    preferred_language: str
) -> StudentModel:
    return register_full_student(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        phone_number=None,
        grade=str(grade),
        education_level=education_level,
        preferred_language=preferred_language,
        selected_courses=[],
        payment_amount=0,
        approval_status='PAYMENT_PENDING'
    )

def update_payment_screenshot(
    telegram_id: int,
    file_id: str,
    file_path: Optional[str] = None
) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET payment_screenshot_file_id = ?,
            payment_screenshot_path = ?,
            approval_status = 'PAYMENT_SUBMITTED',
            payment_submitted_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (file_id, file_path, telegram_id))
    conn.commit()
    conn.close()

def approve_student(telegram_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET approval_status = 'APPROVED',
            approved_at = CURRENT_TIMESTAMP,
            rejected_reason = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (telegram_id,))
    conn.commit()
    conn.close()

def reject_student(telegram_id: int, reason: Optional[str] = None) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET approval_status = 'REJECTED',
            rejected_reason = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (reason, telegram_id))
    conn.commit()
    conn.close()

def update_approval_status(telegram_id: int, status: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET approval_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (status, telegram_id))
    conn.commit()
    conn.close()

def update_student_courses(telegram_id: int, courses: List[str]) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    courses_json = json.dumps(courses, ensure_ascii=False)
    cursor.execute("""
        UPDATE students
        SET selected_courses_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    """, (courses_json, telegram_id))
    conn.commit()
    conn.close()

def update_student_profile(
    telegram_id: int, 
    grade: Optional[Any] = None, 
    education_level: Optional[str] = None, 
    preferred_language: Optional[str] = None
) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if grade is not None:
        updates.append("grade = ?")
        params.append(str(grade))
    if education_level is not None:
        updates.append("education_level = ?")
        params.append(education_level)
    if preferred_language is not None:
        updates.append("preferred_language = ?")
        params.append(preferred_language)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE students SET {', '.join(updates)} WHERE telegram_id = ?"
        params.append(telegram_id)
        cursor.execute(sql, tuple(params))
        conn.commit()
    conn.close()

def get_system_setting(key: str, default: str = "") -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row and row['value']:
        return str(row['value'])
    return default

def set_system_setting(key: str, value: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, (key, str(value)))
    conn.commit()
    conn.close()

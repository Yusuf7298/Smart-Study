import sqlite3
import logging
import config

from typing import Optional

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-64000;")
        conn.execute("PRAGMA temp_store=MEMORY;")
    except Exception:
        pass
    return conn

def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('price_per_course', ?)", (str(config.DEFAULT_PRICE_PER_COURSE_ETB),))
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_prices (
            grade TEXT PRIMARY KEY,
            price_per_course INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            first_name TEXT,
            username TEXT,
            phone_number TEXT,
            grade TEXT,
            education_level TEXT,
            preferred_language TEXT DEFAULT 'English',
            approval_status TEXT DEFAULT 'REGISTRATION_PENDING',
            selected_courses_json TEXT DEFAULT '[]',
            payment_amount INTEGER DEFAULT 0,
            payment_screenshot_file_id TEXT,
            payment_screenshot_path TEXT,
            payment_submitted_at TIMESTAMP,
            approved_at TIMESTAMP,
            rejected_reason TEXT,
            has_exam_package INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_id) REFERENCES students(telegram_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            subtopic TEXT,
            stage TEXT DEFAULT 'INTRODUCTION' CHECK(stage IN ('INTRODUCTION', 'LEARNING', 'PRACTICE', 'QUIZ', 'REVIEW', 'MASTERED')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_id) REFERENCES students(telegram_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            learning_session_id INTEGER,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            total_questions INTEGER DEFAULT 5,
            current_question INTEGER DEFAULT 1,
            correct_answers INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_id) REFERENCES students(telegram_id),
            FOREIGN KEY(learning_session_id) REFERENCES learning_sessions(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_session_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            student_answer TEXT,
            is_correct INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            answered_at TIMESTAMP,
            FOREIGN KEY(quiz_session_id) REFERENCES quiz_sessions(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            learning_session_id INTEGER,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            questions_text TEXT NOT NULL,
            student_answers TEXT NOT NULL,
            score INTEGER,
            max_score INTEGER DEFAULT 10,
            letter_grade TEXT,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(learning_session_id) REFERENCES learning_sessions(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_id TEXT,
            file_size INTEGER,
            mime_type TEXT DEFAULT 'application/pdf',
            title TEXT,
            page_count INTEGER DEFAULT 1,
            extracted_text TEXT,
            summary TEXT,
            topics_json TEXT,
            extraction_status TEXT DEFAULT 'SUCCESS',
            extraction_error TEXT,
            is_active INTEGER DEFAULT 1,
            is_deleted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_id INTEGER,
            details TEXT,
            old_status TEXT,
            new_status TEXT,
            amount INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '📚',
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            chapter_id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            chapter_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            topics_json TEXT DEFAULT '[]',
            is_active INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            telegram_id INTEGER NOT NULL,
            selected_courses_json TEXT NOT NULL,
            unit_price INTEGER DEFAULT 50,
            total_amount INTEGER NOT NULL,
            currency TEXT DEFAULT 'ETB',
            pricing_version INTEGER DEFAULT 1,
            status TEXT DEFAULT 'PENDING',
            receipt_file_id TEXT,
            receipt_storage_path TEXT,
            submitted_at TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing (
            pricing_id TEXT PRIMARY KEY,
            course_price INTEGER NOT NULL DEFAULT 50,
            currency TEXT DEFAULT 'ETB',
            is_active INTEGER DEFAULT 1,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    migrate_db_internal(cursor)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_telegram_id ON students (telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_status ON students (approval_status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_telegram_id ON conversation (telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_sessions_telegram_id ON learning_sessions (telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_learning_sessions_active ON learning_sessions (telegram_id, is_active);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_sessions_telegram_id ON quiz_sessions (telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_sessions_status ON quiz_sessions (status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_questions_session ON quiz_questions (quiz_session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_results_telegram_id ON test_results (telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_materials_telegram_id ON study_materials (telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_materials_active ON study_materials (telegram_id, is_active);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_materials_deleted ON study_materials (telegram_id, is_deleted);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs (admin_id);")
    
    conn.commit()
    conn.close()

def migrate_db_internal(cursor: sqlite3.Cursor) -> None:
    """Internal helper to add missing columns to existing tables before index creation."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('price_per_course', ?)", (str(config.DEFAULT_PRICE_PER_COURSE_ETB),))

    
    cursor.execute("PRAGMA table_info(students)")
    columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if len(columns) > 0:
        if 'approval_status' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN approval_status TEXT DEFAULT 'REGISTRATION_PENDING'")
            except Exception as e:
                logging.error(f"Error adding approval_status: {e}")
        if 'phone_number' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN phone_number TEXT")
            except Exception as e:
                logging.error(f"Error adding phone_number: {e}")
        if 'selected_courses_json' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN selected_courses_json TEXT DEFAULT '[]'")
            except Exception as e:
                logging.error(f"Error adding selected_courses_json: {e}")
        if 'payment_amount' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN payment_amount INTEGER DEFAULT 0")
            except Exception as e:
                logging.error(f"Error adding payment_amount: {e}")
        if 'payment_screenshot_file_id' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN payment_screenshot_file_id TEXT")
            except Exception as e:
                logging.error(f"Error adding payment_screenshot_file_id: {e}")
        if 'payment_screenshot_path' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN payment_screenshot_path TEXT")
            except Exception as e:
                logging.error(f"Error adding payment_screenshot_path: {e}")
        if 'payment_submitted_at' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN payment_submitted_at TIMESTAMP")
            except Exception as e:
                logging.error(f"Error adding payment_submitted_at: {e}")
        if 'approved_at' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN approved_at TIMESTAMP")
            except Exception as e:
                logging.error(f"Error adding approved_at: {e}")
        if 'rejected_reason' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN rejected_reason TEXT")
            except Exception as e:
                logging.error(f"Error adding rejected_reason: {e}")
        if 'has_exam_package' not in columns:
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN has_exam_package INTEGER DEFAULT 0")
            except Exception as e:
                logging.error(f"Error adding has_exam_package: {e}")
            
    cursor.execute("PRAGMA table_info(learning_sessions)")
    learn_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'subtopic' not in learn_columns and len(learn_columns) > 0:
        try:
            cursor.execute("ALTER TABLE learning_sessions ADD COLUMN subtopic TEXT")
        except Exception as e:
            logging.error(f"Error adding subtopic: {e}")

    cursor.execute("PRAGMA table_info(quiz_sessions)")
    quiz_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'updated_at' not in quiz_columns and len(quiz_columns) > 0:
        try:
            cursor.execute("ALTER TABLE quiz_sessions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception as e:
            logging.error(f"Error adding updated_at to quiz_sessions: {e}")

    cursor.execute("PRAGMA table_info(quiz_questions)")
    qq_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'created_at' not in qq_columns and len(qq_columns) > 0:
        try:
            cursor.execute("ALTER TABLE quiz_questions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception as e:
            logging.error(f"Error adding created_at to quiz_questions: {e}")

    cursor.execute("PRAGMA table_info(study_materials)")
    mat_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if len(mat_columns) > 0:
        if 'mime_type' not in mat_columns:
            try:
                cursor.execute("ALTER TABLE study_materials ADD COLUMN mime_type TEXT DEFAULT 'application/pdf'")
            except Exception as e:
                logging.error(f"Error adding mime_type: {e}")
        if 'extraction_status' not in mat_columns:
            try:
                cursor.execute("ALTER TABLE study_materials ADD COLUMN extraction_status TEXT DEFAULT 'SUCCESS'")
            except Exception as e:
                logging.error(f"Error adding extraction_status: {e}")
        if 'extraction_error' not in mat_columns:
            try:
                cursor.execute("ALTER TABLE study_materials ADD COLUMN extraction_error TEXT")
            except Exception as e:
                logging.error(f"Error adding extraction_error: {e}")
        if 'is_deleted' not in mat_columns:
            try:
                cursor.execute("ALTER TABLE study_materials ADD COLUMN is_deleted INTEGER DEFAULT 0")
            except Exception as e:
                logging.error(f"Error adding is_deleted: {e}")

def migrate_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    migrate_db_internal(cursor)
    conn.commit()
    conn.close()

async def init_database() -> None:
    init_db()
    from bot.database.mongo import init_mongo_db
    await init_mongo_db()

def get_grade_price_sync(grade: str) -> Optional[int]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT price_per_course FROM grade_prices WHERE grade = ?", (str(grade),))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
    except sqlite3.OperationalError:
        pass
    except Exception as e:
        logging.error(f"Error fetching grade price: {e}")
    return None

def set_grade_price_sync(grade: str, price: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_prices (
            grade TEXT PRIMARY KEY,
            price_per_course INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO grade_prices (grade, price_per_course, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(grade) DO UPDATE SET price_per_course = EXCLUDED.price_per_course, updated_at = CURRENT_TIMESTAMP
    """, (str(grade), price))
    conn.commit()
    conn.close()

def get_all_grade_prices_sync() -> dict:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT grade, price_per_course FROM grade_prices")
        rows = cursor.fetchall()
        conn.close()
        return {str(r[0]): int(r[1]) for r in rows} if rows else {}
    except sqlite3.OperationalError:
        return {}
    except Exception as e:
        logging.error(f"Error fetching all grade prices: {e}")
        return {}

def has_used_free_trial_sync(telegram_id: int) -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM free_trials WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        return bool(row)
    except sqlite3.OperationalError:
        return False
    except Exception as e:
        logging.error(f"Error checking free trial status: {e}")
        return False

def record_free_trial_usage_sync(telegram_id: int, grade: str, subject: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS free_trials (
                telegram_id INTEGER PRIMARY KEY,
                grade TEXT,
                subject TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO free_trials (telegram_id, grade, subject, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (telegram_id, str(grade), str(subject)))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error recording free trial usage: {e}")

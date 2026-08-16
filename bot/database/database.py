import sqlite3
import logging
import config

def get_db_connection() -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database with Row factory and busy timeout."""
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes all database tables, foreign keys, migrations, and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    
    # 1. Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            first_name TEXT,
            username TEXT,
            grade TEXT,
            education_level TEXT,
            preferred_language TEXT DEFAULT 'English',
            approval_status TEXT DEFAULT 'PENDING' CHECK(approval_status IN ('PENDING', 'APPROVED', 'REJECTED')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Conversation history table
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
    
    # 3. Learning sessions table
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
    
    # 4. Quiz sessions table
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
    
    # 5. Quiz questions table
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
    
    # 6. Test results table
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
    
    # 7. Study materials / PDF memory table
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
    
    # 8. Admin audit logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 9. Run schema migrations BEFORE creating indexes on newly added columns
    migrate_db_internal(cursor)
    
    # 10. Create indexes for optimal query performance
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
    # 1. Check students table columns
    cursor.execute("PRAGMA table_info(students)")
    columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'approval_status' not in columns and len(columns) > 0:
        logging.info("Migrating database: adding approval_status to students table")
        try:
            cursor.execute("""
                ALTER TABLE students 
                ADD COLUMN approval_status TEXT DEFAULT 'APPROVED' CHECK(approval_status IN ('PENDING', 'APPROVED', 'REJECTED'))
            """)
        except Exception as e:
            logging.error(f"Error migrating students table: {e}")
            
    # 2. Check learning_sessions table columns
    cursor.execute("PRAGMA table_info(learning_sessions)")
    learn_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'subtopic' not in learn_columns and len(learn_columns) > 0:
        try:
            cursor.execute("ALTER TABLE learning_sessions ADD COLUMN subtopic TEXT")
        except Exception as e:
            logging.error(f"Error adding subtopic: {e}")

    # 3. Check quiz_sessions table columns
    cursor.execute("PRAGMA table_info(quiz_sessions)")
    quiz_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'updated_at' not in quiz_columns and len(quiz_columns) > 0:
        try:
            cursor.execute("ALTER TABLE quiz_sessions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception as e:
            logging.error(f"Error adding updated_at to quiz_sessions: {e}")

    # 4. Check quiz_questions table columns
    cursor.execute("PRAGMA table_info(quiz_questions)")
    qq_columns = [row['name'] if isinstance(row, sqlite3.Row) else row[1] for row in cursor.fetchall()]
    if 'created_at' not in qq_columns and len(qq_columns) > 0:
        try:
            cursor.execute("ALTER TABLE quiz_questions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception as e:
            logging.error(f"Error adding created_at to quiz_questions: {e}")

    # 5. Check study_materials table columns
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
    """Public wrapper to migrate existing database schemas safely."""
    conn = get_db_connection()
    cursor = conn.cursor()
    migrate_db_internal(cursor)
    conn.commit()
    conn.close()

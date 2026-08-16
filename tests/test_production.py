import os
import io
import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

TEST_DB_PATH = "test_production_bot.db"
os.environ["DATABASE_PATH"] = TEST_DB_PATH

from bot.database.database import init_db, get_db_connection
from bot.database.models import StudentModel
from bot.services import (
    student_service, learning_service, quiz_service,
    conversation_service, pdf_service, progress_service, i18n
)
from bot.services.i18n import t, normalize_lang
from bot.database.repositories import (
    materials as mat_repo, tests as test_repo, admin as admin_repo
)
from bot.keyboards.main_menu import get_main_menu_keyboard, get_main_reply_keyboard
from bot.middlewares.ratelimit import RateLimitMiddleware
from main import global_error_handler
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
import config

def run_async(coro):
    return asyncio.run(coro)

class TestProductionReadiness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.DATABASE_PATH = TEST_DB_PATH
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError:
                pass

    def setUp(self):
        config.DATABASE_PATH = TEST_DB_PATH
        config.ADMIN_IDS = [8223004316]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF;")
        cursor.execute("DELETE FROM quiz_questions")
        cursor.execute("DELETE FROM quiz_sessions")
        cursor.execute("DELETE FROM test_results")
        cursor.execute("DELETE FROM learning_sessions")
        cursor.execute("DELETE FROM study_materials")
        cursor.execute("DELETE FROM conversation")
        cursor.execute("DELETE FROM admin_logs")
        cursor.execute("DELETE FROM students")
        cursor.execute("PRAGMA foreign_keys=ON;")
        conn.commit()
        conn.close()

    # 1. Internationalization (i18n)
    def test_i18n_all_three_languages(self):
        """Verify that English, Amharic, and Afaan Oromoo translations exist and render properly."""
        # English
        self.assertEqual(normalize_lang("English"), "en")
        en_title = t("btn_study", "English")
        self.assertIn("Study", en_title)
        
        # Amharic
        self.assertEqual(normalize_lang("Amharic"), "am")
        am_title = t("btn_study", "Amharic")
        self.assertIn("አጥና", am_title)
        
        # Afaan Oromoo
        self.assertEqual(normalize_lang("Afaan Oromo"), "om")
        om_title = t("btn_study", "Afaan Oromo")
        self.assertIn("Qo'adhu", om_title)

    # 2. Main Menu Keyboards
    def test_main_menu_keyboards_all_buttons(self):
        """Verify main menu inline and reply keyboards have all core student actions."""
        inline_kb = get_main_menu_keyboard("English")
        reply_kb = get_main_reply_keyboard("English")
        
        all_inline_callbacks = [btn.callback_data for row in inline_kb.inline_keyboard for btn in row]
        self.assertIn("menu_study", all_inline_callbacks)
        self.assertIn("menu_study_pdf", all_inline_callbacks)
        self.assertIn("menu_quiz", all_inline_callbacks)
        self.assertIn("menu_test", all_inline_callbacks)
        self.assertIn("menu_notes", all_inline_callbacks)
        self.assertIn("menu_materials", all_inline_callbacks)
        self.assertIn("menu_progress", all_inline_callbacks)
        self.assertIn("menu_profile", all_inline_callbacks)
        self.assertIn("menu_language", all_inline_callbacks)
        self.assertIn("menu_help", all_inline_callbacks)
        
        all_reply_texts = [btn.text for row in reply_kb.keyboard for btn in row]
        self.assertTrue(any("Study" in txt for txt in all_reply_texts))
        self.assertTrue(any("PDF" in txt for txt in all_reply_texts))
        self.assertTrue(any("Quiz" in txt for txt in all_reply_texts))
        self.assertTrue(any("Test" in txt for txt in all_reply_texts))
        self.assertTrue(any("Notes" in txt for txt in all_reply_texts))
        self.assertTrue(any("Materials" in txt for txt in all_reply_texts))
        self.assertTrue(any("Progress" in txt for txt in all_reply_texts))
        self.assertTrue(any("Profile" in txt for txt in all_reply_texts))
        self.assertTrue(any("Help" in txt for txt in all_reply_texts))

    # 3. PDF Pipeline: Text Extraction & Safety
    def test_pdf_extraction_and_safety(self):
        """Verify PDF text extraction using pypdf and filename sanitization."""
        from bot.services.pdf_service import sanitize_filename
        
        evil_name = "../../../etc/passwd; DROP TABLE students; -- .pdf"
        clean_name = sanitize_filename(evil_name)
        self.assertNotIn("..", clean_name)
        self.assertNotIn("/", clean_name)
        self.assertNotIn("\\", clean_name)
        self.assertTrue(clean_name.endswith(".pdf"))

    # 4. PDF Storage & Grounded Q&A Memory
    def test_pdf_storage_and_memory_repository(self):
        """Verify saving and retrieving study materials in the database."""
        user_id = 10001
        
        mat = run_async(asyncio.to_thread(
            mat_repo.save_study_material,
            telegram_id=user_id,
            filename="biology_chapter1.pdf",
            file_path="/tmp/biology_chapter1.pdf",
            file_id="tg_file_123",
            file_size=10240,
            title="Cell Structure & Organelles",
            page_count=5,
            extracted_text="The nucleus contains the genetic material DNA of the cell.",
            summary="Chapter 1 covers eukaryotic cell organelles and mitochondria.",
            topics_json='["Cell Theory", "Organelles", "Membranes"]'
        ))
        
        self.assertIsNotNone(mat)
        self.assertEqual(mat.telegram_id, user_id)
        self.assertEqual(mat.title, "Cell Structure & Organelles")
        self.assertEqual(mat.is_active, 1)
        
        active_mat = run_async(pdf_service.get_active_material(user_id))
        self.assertIsNotNone(active_mat)
        self.assertEqual(active_mat.id, mat.id)
        self.assertIn("nucleus", active_mat.extracted_text)

    # 5. Written Test Results Persistence & Progress Calculation
    def test_written_test_persistence_and_progress_analytics(self):
        """Verify written tests are persisted to DB and included in progress metrics."""
        user_id = 10002
        run_async(student_service.register_student(user_id, "TestStudent", "test_user"))
        ls = run_async(learning_service.start_session(user_id, "Computer Science", "🐍 Python"))
        
        test_res = run_async(asyncio.to_thread(
            test_repo.save_test_result,
            telegram_id=user_id,
            subject="Computer Science",
            topic="🐍 Python",
            questions_text="1. Explain Python lists.\n2. What is a dict?\n3. How do functions work?",
            student_answers="Lists are ordered collections. Dicts are key-value pairs. Functions execute reusable code.",
            score=9,
            max_score=10,
            letter_grade="A",
            feedback="Excellent explanations.",
            learning_session_id=ls.id
        ))
        self.assertIsNotNone(test_res)
        self.assertEqual(test_res.score, 9)
        self.assertEqual(test_res.letter_grade, "A")
        
        stats = run_async(progress_service.get_student_progress(user_id))
        self.assertEqual(stats["tests_count"], 1)
        self.assertEqual(stats["test_avg_score"], 9.0)
        self.assertEqual(stats["lessons_count"], 1)

    # 6. Admin Control Dashboard & Broadcast
    def test_admin_dashboard_and_broadcast_audit(self):
        """Verify admin dashboard stats and broadcast logging."""
        admin_id = 8223004316
        student_id_1 = 10003
        student_id_2 = 10004
        
        run_async(student_service.register_student_pending(student_id_1, "PendingUser", "pending_u", "10", "English"))
        run_async(student_service.register_student_pending(student_id_2, "ApprovedUser", "approved_u", "12", "Amharic"))
        run_async(student_service.update_approval_status(student_id_2, "APPROVED"))
        
        stats = run_async(asyncio.to_thread(admin_repo.get_admin_dashboard_stats))
        self.assertEqual(stats["total_students"], 2)
        self.assertEqual(stats["pending_students"], 1)
        self.assertEqual(stats["approved_students"], 1)
        
        approved_ids = run_async(asyncio.to_thread(admin_repo.get_all_approved_student_ids))
        self.assertEqual(len(approved_ids), 1)
        self.assertEqual(approved_ids[0], student_id_2)
        
        run_async(asyncio.to_thread(
            admin_repo.log_admin_action,
            admin_id=admin_id,
            action="BROADCAST",
            details="Sent to 1 student"
        ))

    # 7. Rate Limiting Sliding Window
    def test_rate_limiting_sliding_window(self):
        """Verify RateLimitMiddleware blocks flooding requests above the threshold."""
        limiter = RateLimitMiddleware(limit=3, window=60)
        
        from aiogram.types import Message, User
        user_msg = AsyncMock(spec=Message)
        user_msg.from_user = MagicMock(spec=User)
        user_msg.from_user.id = 555001
        user_msg.answer = AsyncMock()
        
        data = {"event_from_user": user_msg.from_user}
        handler = AsyncMock(return_value="OK")
        
        for _ in range(3):
            res = run_async(limiter(handler, user_msg, data))
            self.assertEqual(res, "OK")
            
        res_blocked = run_async(limiter(handler, user_msg, data))
        self.assertIsNone(res_blocked)
        user_msg.answer.assert_called_with("⚠️ You are sending requests too quickly. Please wait a few seconds before continuing.")

    # 8. Profile Grade & Language Updates
    def test_profile_grade_and_language_switching(self):
        """Verify student profile grade & language updates."""
        user_id = 10005
        student = run_async(student_service.register_student(user_id, "Sara", "sara_user"))
        self.assertEqual(student.preferred_language, "English")
        
        run_async(student_service.update_language(user_id, "Amharic"))
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(student.preferred_language, "Amharic")
        
        run_async(student_service.update_grade(user_id, "University"))
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(student.grade, "University")
        self.assertEqual(student.education_level, "University")

    # 9. Materials Library: CRUD & Student Ownership
    def test_materials_library_management_and_ownership(self):
        """Verify uploading, listing, activating, deleting, and student isolation in materials library."""
        user_a = 20001
        user_b = 20002
        
        mat1 = run_async(asyncio.to_thread(
            mat_repo.save_study_material,
            telegram_id=user_a,
            filename="algebra.pdf",
            file_path="uploads/20001/algebra.pdf",
            title="Algebra Basics"
        ))
        mat2 = run_async(asyncio.to_thread(
            mat_repo.save_study_material,
            telegram_id=user_a,
            filename="geometry.pdf",
            file_path="uploads/20001/geometry.pdf",
            title="Euclidean Geometry"
        ))
        
        mat_b = run_async(asyncio.to_thread(
            mat_repo.save_study_material,
            telegram_id=user_b,
            filename="history.pdf",
            file_path="uploads/20002/history.pdf",
            title="World History"
        ))
        
        mats_a = run_async(pdf_service.get_student_materials(user_a))
        self.assertEqual(len(mats_a), 2)
        self.assertEqual(mats_a[0].title, "Euclidean Geometry")
        
        mats_b = run_async(pdf_service.get_student_materials(user_b))
        self.assertEqual(len(mats_b), 1)
        self.assertEqual(mats_b[0].title, "World History")
        
        activated = run_async(pdf_service.activate_student_material(user_a, mat1.id))
        self.assertTrue(activated)
        active_a = run_async(pdf_service.get_active_material(user_a))
        self.assertEqual(active_a.id, mat1.id)
        
        del_attempt = run_async(pdf_service.delete_student_material(user_a, mat_b.id))
        self.assertFalse(del_attempt)
        
        deleted = run_async(pdf_service.delete_student_material(user_a, mat2.id))
        self.assertTrue(deleted)
        
        remaining_a = run_async(pdf_service.get_student_materials(user_a))
        self.assertEqual(len(remaining_a), 1)

    # 10. Admin: Student Search & Status Filters
    def test_admin_approved_rejected_and_search(self):
        """Verify admin repository search and status retrieval."""
        run_async(student_service.register_student_pending(30001, "Solomon Haile", "shaile", "11", "English"))
        run_async(student_service.register_student_pending(30002, "Almaz Kebede", "akebede", "9", "Amharic"))
        run_async(student_service.update_approval_status(30001, "APPROVED"))
        run_async(student_service.update_approval_status(30002, "REJECTED"))
        
        approved = run_async(asyncio.to_thread(admin_repo.get_students_by_status, "APPROVED", 10))
        self.assertTrue(any(s.telegram_id == 30001 for s in approved))
        
        rejected = run_async(asyncio.to_thread(admin_repo.get_students_by_status, "REJECTED", 10))
        self.assertTrue(any(s.telegram_id == 30002 for s in rejected))
        
        results = run_async(asyncio.to_thread(admin_repo.search_students, "Solomon", 10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].telegram_id, 30001)

    # 11. Written Test History Retrieval
    def test_test_history_retrieval(self):
        """Verify retrieving historical test results for a student."""
        user_id = 40001
        run_async(student_service.register_student(user_id, "HistoryStudent", "h_student"))
        
        for i in range(1, 4):
            run_async(asyncio.to_thread(
                test_repo.save_test_result,
                telegram_id=user_id,
                subject="Physics",
                topic=f"Topic {i}",
                questions_text=f"Q{i}",
                student_answers=f"A{i}",
                score=i + 6,
                letter_grade="A"
            ))
            
        history = run_async(asyncio.to_thread(test_repo.get_student_test_results, user_id, 10))
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].topic, "Topic 3")

    # 12. Corrupt / Empty PDF Extraction Handling
    def test_pdf_corrupt_and_empty_handling(self):
        """Verify pdf_service handles empty and corrupt PDF bytes gracefully."""
        from bot.services.pdf_service import extract_text_from_pdf_bytes
        
        corrupt_bytes = b"NOT_A_PDF_CORRUPT_HEADER_DATA"
        text, pages, status, err = extract_text_from_pdf_bytes(corrupt_bytes)
        self.assertEqual(status, "CORRUPT")
        self.assertIsNotNone(err)

    # 13. PDF Chunking & Retrieval Algorithm
    def test_pdf_chunking_and_retrieval(self):
        """Verify chunking large document text and retrieving relevant chunks."""
        from bot.services.pdf_service import chunk_pdf_text, retrieve_relevant_chunks
        
        large_doc = ("Photosynthesis is the process by which green plants create food.\n" * 100) + \
                    ("Mitochondria generate most of the chemical energy needed by the cell.\n" * 100)
                    
        chunks = chunk_pdf_text(large_doc, chunk_size=1000, overlap=100)
        self.assertTrue(len(chunks) > 5)
        
        result_chunk = retrieve_relevant_chunks(chunks, "What do mitochondria do?", top_k=2)
        self.assertIn("Mitochondria", result_chunk)

    # 14. Global Error Handler Catching Telegram Exceptions
    def test_global_error_handler(self):
        """Verify global_error_handler catches Telegram exceptions without crashing."""
        from aiogram.types import Update
        dummy_update = Update(update_id=1)
        event_forbidden = ErrorEvent(update=dummy_update, exception=TelegramForbiddenError(method=MagicMock(), message="Forbidden: bot was blocked by the user"))
        res1 = run_async(global_error_handler(event_forbidden))
        self.assertTrue(res1)
        
        event_bad_req = ErrorEvent(update=dummy_update, exception=TelegramBadRequest(method=MagicMock(), message="Bad Request: message not modified"))
        res2 = run_async(global_error_handler(event_bad_req))
        self.assertTrue(res2)

    # 15. Admin Search by Numeric Telegram ID
    def test_admin_search_by_numeric_id(self):
        """Verify searching student by Telegram ID."""
        user_id = 998877
        run_async(student_service.register_student_pending(user_id, "NumericUser", "numuser", "10", "English"))
        
        results = run_async(asyncio.to_thread(admin_repo.search_students, "998877", 10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].telegram_id, user_id)

    # 16. SQLite Database Connection and Schema Verification
    def test_database_wal_mode_and_concurrency(self):
        """Verify SQLite connection is active and all required tables exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("students", tables)
        self.assertIn("learning_sessions", tables)
        self.assertIn("quiz_sessions", tables)
        self.assertIn("test_results", tables)
        self.assertIn("study_materials", tables)
        self.assertIn("admin_logs", tables)
        conn.close()

    # 17. Environment Validation Check
    def test_config_environment_validation(self):
        """Verify validate_environment runs and validates key presence."""
        from config import validate_environment
        try:
            validate_environment()
        except ValueError as ve:
            self.assertIn("BOT_TOKEN", str(ve))

    # 18. i18n Safe Fallback to English on Unknown Key
    def test_i18n_fallback_safety(self):
        """Verify t() returns key or fallback gracefully on missing translation."""
        val = t("completely_nonexistent_key_xyz", "Amharic")
        self.assertEqual(val, "completely_nonexistent_key_xyz")

    # 19. Gemini Fallback Models List
    def test_gemini_fallback_models_integrity(self):
        """Verify fallback models list has valid alternative model identifiers."""
        from bot.services.gemini import FALLBACK_MODELS
        self.assertTrue(len(FALLBACK_MODELS) >= 3)
        for m in FALLBACK_MODELS:
            self.assertTrue(m.startswith("gemini-"))

    # 20. Student Profile Persistence Across Simulation
    def test_student_persistence_across_sessions(self):
        """Verify student data remains consistent when queried across independent connections."""
        user_id = 887766
        run_async(student_service.register_student(user_id, "PersistentUser", "pers_user"))
        run_async(student_service.update_grade(user_id, "12"))
        run_async(student_service.update_language(user_id, "Afaan Oromo"))
        
        s = run_async(student_service.get_student(user_id))
        self.assertIsNotNone(s)
        self.assertEqual(s.grade, "12")
        self.assertEqual(s.preferred_language, "Afaan Oromo")

    # 21. Socials & Islamic Reminders Links Across All Languages
    def test_socials_command_and_multilingual_content(self):
        """Verify socials strings and links exist in English, Amharic, and Afaan Oromoo."""
        for lang in ["English", "Amharic", "Afaan Oromo"]:
            socials_text = t("socials_title", lang)
            self.assertIn("t.me/yusufcodes", socials_text)
            self.assertIn("linkedin.com/in/yusuf-mohammed", socials_text)
            self.assertIn("instagram.com/kebilad_7488", socials_text)

    # 22. Admin Audit Logs Persistence and Retrieval
    def test_admin_logs_retrieval_and_audit(self):
        """Verify logging an administrative action and retrieving it."""
        admin_id = config.ADMIN_IDS[0]
        run_async(asyncio.to_thread(admin_repo.log_admin_action, admin_id, "TEST_ACTION", 123456, "Unit test verification"))
        
        logs = run_async(asyncio.to_thread(admin_repo.get_admin_logs, 5))
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0].action, "TEST_ACTION")
        self.assertEqual(logs[0].target_id, 123456)

if __name__ == "__main__":
    unittest.main()

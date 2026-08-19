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
    def test_i18n_all_three_languages(self):
        self.assertEqual(normalize_lang("English"), "en")
        en_title = t("btn_study", "English")
        self.assertIn("Study", en_title)
        self.assertEqual(normalize_lang("Amharic"), "am")
        am_title = t("btn_study", "Amharic")
        self.assertIn("አጥና", am_title)
        self.assertEqual(normalize_lang("Afaan Oromo"), "om")
        om_title = t("btn_study", "Afaan Oromo")
        self.assertIn("Qo'adhu", om_title)
    def test_main_menu_keyboards_all_buttons(self):
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
        self.assertIn("menu_support", all_inline_callbacks)
        
        all_reply_texts = [btn.text for row in reply_kb.keyboard for btn in row]
        self.assertTrue(any("Menu" in txt for txt in all_reply_texts))
        self.assertTrue(any("Back" in txt for txt in all_reply_texts))
        self.assertTrue(any("Clear" in txt for txt in all_reply_texts))
    def test_pdf_extraction_and_safety(self):
        from bot.services.pdf_service import sanitize_filename
        evil_name = "../../../etc/passwd; DROP TABLE students; -- .pdf"
        clean_name = sanitize_filename(evil_name)
        self.assertNotIn("..", clean_name)
        self.assertNotIn("/", clean_name)
        self.assertNotIn("\\", clean_name)
        self.assertTrue(clean_name.endswith(".pdf"))
    def test_pdf_storage_and_memory_repository(self):
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
    def test_written_test_persistence_and_progress_analytics(self):
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
    def test_admin_dashboard_and_broadcast_audit(self):
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
    def test_rate_limiting_sliding_window(self):
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
    def test_profile_grade_and_language_switching(self):
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
    def test_materials_library_management_and_ownership(self):
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
    def test_admin_approved_rejected_and_search(self):
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
    def test_test_history_retrieval(self):
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
    def test_pdf_corrupt_and_empty_handling(self):
        from bot.services.pdf_service import extract_text_from_pdf_bytes
        corrupt_bytes = b"NOT_A_PDF_CORRUPT_HEADER_DATA"
        text, pages, status, err = extract_text_from_pdf_bytes(corrupt_bytes)
        self.assertEqual(status, "CORRUPT")
        self.assertIsNotNone(err)
    def test_pdf_chunking_and_retrieval(self):
        from bot.services.pdf_service import chunk_pdf_text, retrieve_relevant_chunks
        
        large_doc = ("Photosynthesis is the process by which green plants create food.\n" * 100) + \
                    ("Mitochondria generate most of the chemical energy needed by the cell.\n" * 100)
                    
        chunks = chunk_pdf_text(large_doc, chunk_size=1000, overlap=100)
        self.assertTrue(len(chunks) > 5)
        
        result_chunk = retrieve_relevant_chunks(chunks, "What do mitochondria do?", top_k=2)
        self.assertIn("Mitochondria", result_chunk)
    def test_global_error_handler(self):
        from aiogram.types import Update
        dummy_update = Update(update_id=1)
        event_forbidden = ErrorEvent(update=dummy_update, exception=TelegramForbiddenError(method=MagicMock(), message="Forbidden: bot was blocked by the user"))
        res1 = run_async(global_error_handler(event_forbidden))
        self.assertTrue(res1)
        
        event_bad_req = ErrorEvent(update=dummy_update, exception=TelegramBadRequest(method=MagicMock(), message="Bad Request: message not modified"))
        res2 = run_async(global_error_handler(event_bad_req))
        self.assertTrue(res2)
    def test_admin_search_by_numeric_id(self):
        user_id = 998877
        run_async(student_service.register_student_pending(user_id, "NumericUser", "numuser", "10", "English"))
        
        results = run_async(asyncio.to_thread(admin_repo.search_students, "998877", 10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].telegram_id, user_id)
    def test_database_wal_mode_and_concurrency(self):
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
    def test_config_environment_validation(self):
        from config import validate_environment
        try:
            validate_environment()
        except ValueError as ve:
            self.assertIn("BOT_TOKEN", str(ve))
    def test_i18n_fallback_safety(self):
        val = t("completely_nonexistent_key_xyz", "Amharic")
        self.assertEqual(val, "completely_nonexistent_key_xyz")
    def test_gemini_fallback_models_integrity(self):
        from bot.services.gemini import FALLBACK_MODELS
        self.assertTrue(len(FALLBACK_MODELS) >= 3)
        for m in FALLBACK_MODELS:
            self.assertTrue(m.startswith("gemini-"))
    def test_student_persistence_across_sessions(self):
        user_id = 887766
        run_async(student_service.register_student(user_id, "PersistentUser", "pers_user"))
        run_async(student_service.update_grade(user_id, "12"))
        run_async(student_service.update_language(user_id, "Afaan Oromo"))
        
        s = run_async(student_service.get_student(user_id))
        self.assertIsNotNone(s)
        self.assertEqual(s.grade, "12")
        self.assertEqual(s.preferred_language, "Afaan Oromo")
    def test_socials_command_and_multilingual_content(self):
        for lang in ["English", "Amharic", "Afaan Oromo"]:
            socials_text = t("socials_title", lang)
            self.assertIn("t.me/yusufcodes", socials_text)
            self.assertIn("linkedin.com/in/yusuf-mohammed", socials_text)
            self.assertIn("instagram.com/kebilad_7488", socials_text)
    def test_admin_logs_retrieval_and_audit(self):
        admin_id = config.ADMIN_IDS[0]
        run_async(asyncio.to_thread(admin_repo.log_admin_action, admin_id, "TEST_ACTION", 123456, "Unit test verification"))
        
        logs = run_async(asyncio.to_thread(admin_repo.get_admin_logs, 5))
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0].action, "TEST_ACTION")
        self.assertEqual(logs[0].target_id, 123456)
    def test_support_command_and_multilingual_content(self):
        for lang in ["English", "Amharic", "Afaan Oromo"]:
            support_text = t("support_title", lang)
            self.assertIn("Cs1At07", support_text)
            self.assertIn("0928892344", support_text)
    def test_clean_telegram_text_removes_hashtags_and_latex(self):
        from bot.utils import clean_telegram_text, strip_all_formatting
        sample = (
            "**Telegram ID:** `123456`\n\n"
            "# The Cell: The Fundamental Unit of Life\n\n"
            "1. The Modern Tenets of Cell Theory\n"
            "* **Energy Flow:** All reactions occur in cells.\n"
            "Surface Area-to-Volume Ratio ($SA/V$) with volume ($r^3$) and area ($r^2$).\n"
            "Let's Think About This"
        )
        cleaned = clean_telegram_text(sample)
        self.assertNotIn("#", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("$", cleaned)
        self.assertIn("<b>Telegram ID:</b>", cleaned)
        self.assertIn("<b>The Cell: The Fundamental Unit of Life</b>", cleaned)
        self.assertIn("• <b>Energy Flow:</b>", cleaned)
        self.assertIn("r³", cleaned)
        self.assertIn("r²", cleaned)
        
        # Test fallback
        plain = strip_all_formatting(cleaned)
        self.assertNotIn("<", plain)
        self.assertNotIn(">", plain)
        self.assertNotIn("*", plain)
        self.assertIn("Telegram ID:", plain)
        self.assertIn("Energy Flow:", plain)

    def test_ethiopian_curriculum_subject_selection(self):
        from config import get_curriculum_subjects, STREAMS, GRADE_9_10_SUBJECTS
        from bot.handlers.registration import get_subjects_selection_keyboard

        # Grade 5 & 6 Primary Second Cycle (8 subjects)
        g5_subjects = get_curriculum_subjects(grade="5")
        g6_subjects = get_curriculum_subjects(grade="6")
        self.assertEqual(len(g5_subjects), 8)
        self.assertEqual(len(g6_subjects), 8)
        self.assertIn("Environmental Science", g5_subjects)
        self.assertIn("Social Studies", g5_subjects)
        self.assertIn("Moral and Citizenship Education", g5_subjects)
        self.assertIn("Performing and Visual Arts (PVA)", g5_subjects)
        self.assertIn("Health and Physical Education (HPE)", g5_subjects)

        # Grade 7 & 8 Middle School (10 subjects)
        g7_subjects = get_curriculum_subjects(grade="7")
        g8_subjects = get_curriculum_subjects(grade="8")
        self.assertEqual(len(g7_subjects), 10)
        self.assertEqual(len(g8_subjects), 10)
        self.assertIn("General Science", g7_subjects)
        self.assertIn("Career and Technical Education (CTE)", g7_subjects)
        self.assertIn("Social Studies", g7_subjects)
        self.assertIn("Citizenship Education", g7_subjects)
        self.assertIn("Information Technology (IT)", g7_subjects)

        # Grade 9 & 10 Common Curriculum (12 subjects)
        g9_subjects = get_curriculum_subjects(grade="9")
        g10_subjects = get_curriculum_subjects(grade="10")
        self.assertEqual(len(g9_subjects), 12)
        self.assertEqual(len(g10_subjects), 12)
        self.assertIn("English", g9_subjects)
        self.assertIn("Mathematics", g9_subjects)
        self.assertIn("Physics", g9_subjects)
        self.assertIn("Chemistry", g9_subjects)
        self.assertIn("Biology", g9_subjects)
        self.assertIn("History", g9_subjects)
        self.assertIn("Geography", g9_subjects)
        self.assertIn("Economics", g9_subjects)
        self.assertIn("Citizenship Education", g9_subjects)
        self.assertIn("Information Technology (IT)", g9_subjects)
        self.assertIn("Health and Physical Education (HPE)", g9_subjects)
        self.assertIn("National/Regional Language", g9_subjects)

        # Grade 11 & 12 Natural Science Stream (7 subjects)
        g11_nat = get_curriculum_subjects(grade="11", stream="Natural Science")
        g12_nat = get_curriculum_subjects(grade="12", stream="Natural Science")
        self.assertEqual(len(g11_nat), 7)
        self.assertEqual(len(g12_nat), 7)
        self.assertIn("Mathematics (Natural Science)", g11_nat)
        self.assertIn("Agriculture", g11_nat)
        self.assertNotIn("History", g11_nat)

        # Grade 11 & 12 Social Science Stream (7 subjects)
        g11_soc = get_curriculum_subjects(grade="11", stream="Social Science")
        g12_soc = get_curriculum_subjects(grade="12", stream="Social Science")
        self.assertEqual(len(g11_soc), 7)
        self.assertEqual(len(g12_soc), 7)
        self.assertIn("Mathematics (Social Science)", g11_soc)
        self.assertIn("Citizenship Education", g11_soc)
        self.assertNotIn("Biology", g11_soc)

        # Keyboard generation verification
        kb_g10 = get_subjects_selection_keyboard([], grade="10")
        kb_g11_nat = get_subjects_selection_keyboard([], grade="11", stream="Natural Science")
        self.assertTrue(len(kb_g10.inline_keyboard) > 0)
        self.assertTrue(len(kb_g11_nat.inline_keyboard) > 0)

        # Subject & Stream Translation Verification
        from bot.services.i18n import get_subject_name_in_lang, get_stream_name_in_lang
        self.assertEqual(get_subject_name_in_lang("Mathematics", "Amharic"), "ሒሳብ (Mathematics)")
        self.assertEqual(get_subject_name_in_lang("Mathematics", "Afaan Oromoo"), "Hisaaba (Mathematics)")
        self.assertEqual(get_subject_name_in_lang("Biology", "Amharic"), "ባዮሎጂ (Biology)")
        self.assertEqual(get_subject_name_in_lang("Biology", "Afaan Oromoo"), "Bayooloojii (Biology)")
        self.assertIn("ተፈጥሮ ሳይንስ", get_stream_name_in_lang("Natural Science", "Amharic"))
        self.assertIn("Saayinsii Uamaa", get_stream_name_in_lang("Natural Science", "Afaan Oromoo"))
        
        # Localized keyboard generation
        kb_am = get_subjects_selection_keyboard([], grade="10", lang="Amharic")
        am_texts = [btn.text for row in kb_am.inline_keyboard for btn in row]
        self.assertTrue(any("ሒሳብ" in t for t in am_texts))
        self.assertTrue(any("ባዮሎጂ" in t for t in am_texts))

    def test_national_exam_prep_features(self):
        from config import get_exam_review_grades
        from bot.services import student_service
        from bot.database.models import StudentModel
        from bot.handlers.exam import get_exam_scope_keyboard, get_exam_qcount_keyboard

        # Exam review grade mapping
        self.assertEqual(get_exam_review_grades("6"), ["5", "6"])
        self.assertEqual(get_exam_review_grades("8"), ["7", "8"])
        self.assertEqual(get_exam_review_grades("12"), ["9", "10", "11", "12"])

        # Entitlement check
        s6 = StudentModel(id=1, telegram_id=101, first_name="Abebe", username="abe", grade="6", education_level="Primary", preferred_language="Amharic", approval_status="APPROVED")
        s7 = StudentModel(id=2, telegram_id=102, first_name="Kebede", username="keb", grade="7", education_level="Middle", preferred_language="English", approval_status="APPROVED", has_exam_package=False)
        s7_bought = StudentModel(id=3, telegram_id=103, first_name="Almaz", username="alm", grade="7", education_level="Middle", preferred_language="English", approval_status="APPROVED", has_exam_package=True)

        self.assertTrue(student_service.has_national_exam_access(s6))
        self.assertFalse(student_service.has_national_exam_access(s7))
        self.assertTrue(student_service.has_national_exam_access(s7_bought))

        # Payment bundle calculation
        tot6, det6 = student_service.calculate_student_payment("6", 2, 50)
        tot12, det12 = student_service.calculate_student_payment("12", 2, 50)
        self.assertTrue(det6["is_exam_package"])
        self.assertTrue(det12["is_exam_package"])
        self.assertTrue(tot12 > 100)

        # Keyboard checks
        scope_kb = get_exam_scope_keyboard("Biology", grade="12", lang="English")
        qc_kb = get_exam_qcount_keyboard(lang="English")
        self.assertTrue(len(scope_kb.inline_keyboard) >= 2)
        self.assertTrue(len(qc_kb.inline_keyboard) >= 3)

    def test_student_feedback_feature(self):
        from bot.keyboards.main_menu import get_main_menu_keyboard
        from bot.handlers.feedback import FeedbackStates
        from bot.services.i18n import t

        # Verify button presence
        kb = get_main_menu_keyboard(lang="English")
        callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        self.assertIn("menu_feedback", callbacks)

        kb_am = get_main_menu_keyboard(lang="Amharic")
        am_texts = [btn.text for row in kb_am.inline_keyboard for btn in row]
        self.assertTrue(any("አስተያየት" in txt for txt in am_texts))

        # Verify state exists
        self.assertTrue(hasattr(FeedbackStates, "waiting_for_feedback"))
    def test_full_registration_with_phone_and_courses(self):
        user_id = 998877
        courses = ["Biology", "Mathematics", "Computer Science"]
        price = run_async(student_service.get_course_price())
        total_fee = len(courses) * price
        
        student = run_async(student_service.register_student_full(
            telegram_id=user_id,
            first_name="Abebe Bikila",
            username="abebe_runner",
            phone_number="0911223344",
            grade="12",
            preferred_language="English",
            selected_courses=courses,
            payment_amount=total_fee,
            approval_status="PAYMENT_PENDING"
        ))
        
        self.assertIsNotNone(student)
        self.assertEqual(student.phone_number, "0911223344")
        self.assertEqual(student.grade, "12")
        self.assertEqual(student.education_level, "High School")
        self.assertEqual(student.selected_courses, courses)
        self.assertEqual(student.payment_amount, 150)
        self.assertEqual(student.approval_status, "PAYMENT_PENDING")
    def test_dynamic_pricing_get_and_set(self):
        default_price = run_async(student_service.get_course_price())
        self.assertEqual(default_price, 50)
        run_async(student_service.set_course_price(75))
        new_price = run_async(student_service.get_course_price())
        self.assertEqual(new_price, 75)
        run_async(student_service.set_course_price(50))
        self.assertEqual(run_async(student_service.get_course_price()), 50)
    def test_payment_card_content_and_calculation(self):
        card_en = t(
            "payment_instructions_card",
            "English",
            owner=config.PAYMENT_OWNER_NAME,
            cbe=config.PAYMENT_CBE_ACCOUNT,
            telebirr=config.PAYMENT_TELEBIRR_PHONE,
            count=3,
            price=50,
            total=150
        )
        self.assertIn("Yusuf Mohammed", card_en)
        self.assertIn("1000359254718", card_en)
        self.assertIn("0928892344", card_en)
        self.assertIn("150 ETB", card_en)
        self.assertIn("Commercial Bank of Ethiopia", card_en)
        self.assertIn("Telebirr", card_en)
    def test_submit_payment_receipt_and_admin_verification(self):
        user_id = 998878
        run_async(student_service.register_student_full(
            telegram_id=user_id,
            first_name="Fatima Zahra",
            username="fatima_z",
            phone_number="0922334455",
            grade="University",
            preferred_language="Amharic",
            selected_courses=["Physics", "Chemistry"],
            payment_amount=100
        ))
        
        run_async(student_service.submit_payment_screenshot(user_id, "file_id_receipt_abc123", "/tmp/receipt.jpg"))
        
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(student.approval_status, "PAYMENT_SUBMITTED")
        self.assertEqual(student.payment_screenshot_file_id, "file_id_receipt_abc123")
        self.assertIsNotNone(student.payment_submitted_at)

        run_async(student_service.approve_student(user_id))
        approved_student = run_async(student_service.get_student(user_id))
        self.assertEqual(approved_student.approval_status, "APPROVED")
        self.assertIsNotNone(approved_student.approved_at)

    def test_course_access_authorization_gating(self):
        user_id = 998879
        student = run_async(student_service.register_student_full(
            telegram_id=user_id,
            first_name="Ahmed Ali",
            username="ahmed_ali",
            phone_number="0933445566",
            grade="11",
            preferred_language="English",
            selected_courses=["Biology", "Mathematics"],
            payment_amount=100
        ))
        
        self.assertTrue(student_service.is_course_registered(student, "Biology"))
        self.assertTrue(student_service.is_course_registered(student, "Mathematics"))
        self.assertFalse(student_service.is_course_registered(student, "Computer Science"))
        self.assertFalse(student_service.is_course_registered(student, "Geography"))

    def test_registration_keyboards_generation(self):
        from bot.handlers.registration import get_subjects_selection_keyboard, get_grades_keyboard, get_languages_keyboard
        sub_kb = get_subjects_selection_keyboard(["Biology", "Physics"], "English")
        self.assertIsNotNone(sub_kb)
        grade_kb = get_grades_keyboard()
        self.assertIsNotNone(grade_kb)
        lang_kb = get_languages_keyboard()
        self.assertIsNotNone(lang_kb)

    def test_pydantic_schemas_validation(self):
        from bot.database.schemas import StudentSchema, CourseSchema, PaymentSchema, PricingSchema
        student_data = StudentSchema(
            telegram_id=1234567,
            telegram_username="student1",
            full_name="Fatima Ali",
            phone="0911223344",
            grade="12",
            registered_courses=["Biology", "Chemistry"],
            payment_amount=100
        )
        self.assertEqual(student_data.telegram_id, 1234567)
        self.assertEqual(len(student_data.registered_courses), 2)
        
        course_data = CourseSchema(course_id="bio_101", name="Biology", emoji="🧬")
        self.assertEqual(course_data.course_id, "bio_101")
        
        pricing_data = PricingSchema(pricing_id="p1", course_price=60, currency="ETB")
        self.assertEqual(pricing_data.course_price, 60)

    def test_file_storage_security_and_traversal(self):
        from bot.services.storage import sanitize_filename, LocalFileStorageProvider
        self.assertEqual(sanitize_filename("../../dangerous.pdf"), "dangerous.pdf")
        self.assertEqual(sanitize_filename("valid_notes.pdf"), "valid_notes.pdf")
        
        storage = LocalFileStorageProvider()
        test_bytes = b"%PDF-1.4 Mock content for unit test"
        
        saved_path, safe_name = run_async(storage.save(12345, "my_notes.pdf", test_bytes, category="uploads"))
        self.assertTrue(os.path.exists(saved_path))
        self.assertIn("12345", saved_path)
        
        read_bytes = run_async(storage.get(saved_path))
        self.assertEqual(read_bytes, test_bytes)
        
        deleted = run_async(storage.delete(saved_path))
        self.assertTrue(deleted)
        self.assertFalse(os.path.exists(saved_path))
    def test_file_storage_max_size_enforcement(self):
        from bot.services.storage import LocalFileStorageProvider
        storage = LocalFileStorageProvider()
        oversized = b"0" * (21 * 1024 * 1024)
        with self.assertRaises(ValueError):
            run_async(storage.save(12345, "big.pdf", oversized))
    def test_courses_and_chapters_hierarchy(self):
        from bot.database.repositories.courses import get_all_courses, get_course_chapters
        courses = get_all_courses()
        self.assertTrue(len(courses) > 0)
        chapters = get_course_chapters("Biology")
        self.assertTrue(len(chapters) >= 5)
        self.assertEqual(chapters[0].chapter_number, 1)
        self.assertTrue(len(chapters[0].topics) > 0)
    def test_pricing_repository_versioning(self):
        from bot.database.repositories.pricing import get_active_course_price, set_course_price
        set_course_price(65, admin_id=8223004316)
        self.assertEqual(get_active_course_price(), 65)
        set_course_price(50, admin_id=8223004316)
        self.assertEqual(get_active_course_price(), 50)
    def test_admin_start_command_shows_admin_dashboard(self):
        from bot.handlers.start import start
        admin_id = config.ADMIN_IDS[0]
        mock_msg = AsyncMock()
        mock_msg.from_user.id = admin_id
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        with patch("bot.handlers.admin.admin_command", new_callable=AsyncMock) as mock_admin_cmd:
            run_async(start(mock_msg, mock_state))
            mock_admin_cmd.assert_called_once_with(mock_msg)
            mock_state.clear.assert_called_once()
    def test_admin_approval_forwards_to_payment_channel(self):
        from bot.handlers.admin import approve_student_callback
        admin_id = config.ADMIN_IDS[0]
        student_id = 998891
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="ChannelStudent",
            username="chan_student",
            phone_number="0911556677",
            grade="12",
            preferred_language="English",
            selected_courses=["Physics", "Mathematics"],
            payment_amount=100,
            approval_status="PAYMENT_SUBMITTED"
        ))
        run_async(student_service.submit_payment_screenshot(student_id, "photo_file_id_999", "/tmp/receipt.jpg"))
        
        mock_cb = AsyncMock()
        mock_cb.from_user.id = admin_id
        mock_cb.data = f"admin_approve_{student_id}"
        mock_cb.message.edit_caption = AsyncMock()
        mock_cb.message.edit_text = AsyncMock()
        mock_cb.message.photo = ["mock_photo"]
        mock_cb.answer = AsyncMock()
        mock_cb.bot.send_photo = AsyncMock()
        mock_cb.bot.send_message = AsyncMock()
        
        with patch.object(config, "PAYMENT_CHANNEL_ID", "-1001234567890"):
            run_async(approve_student_callback(mock_cb))
            mock_cb.bot.send_photo.assert_called()
            call_args = mock_cb.bot.send_photo.call_args
            self.assertEqual(call_args.kwargs["chat_id"], "-1001234567890")
            self.assertIn("ChannelStudent", call_args.kwargs["caption"])
            self.assertIn("100 ETB", call_args.kwargs["caption"])

    def test_is_grade_matching_validation(self):
        from bot.services.student_service import is_grade_matching
        from bot.database.models import StudentModel
        student_g10 = StudentModel(
            id=1,
            telegram_id=111,
            first_name="Test",
            username="test",
            grade="10",
            education_level="High School",
            preferred_language="English",
            approval_status="APPROVED"
        )
        self.assertTrue(is_grade_matching(student_g10, "Grade 10"))
        self.assertTrue(is_grade_matching(student_g10, "10"))
        self.assertFalse(is_grade_matching(student_g10, "Grade 12"))
        self.assertFalse(is_grade_matching(student_g10, "Grade 9"))
        student_g12 = StudentModel(
            id=2,
            telegram_id=222,
            first_name="TestG12",
            username="testg12",
            grade="12",
            education_level="High School",
            preferred_language="English",
            approval_status="APPROVED"
        )
        self.assertTrue(is_grade_matching(student_g12, "Grade 12"))
        self.assertTrue(is_grade_matching(student_g12, "Grade 11"))
        self.assertTrue(is_grade_matching(student_g12, "Grade 10"))
        self.assertTrue(is_grade_matching(student_g12, "Grade 9"))
        self.assertFalse(is_grade_matching(student_g12, "Grade 8"))
    def test_pdf_upload_security_blocks_unauthorized_course(self):
        from bot.services import pdf_service
        from bot.database.models import StudentModel
        import json
        student = StudentModel(
            id=2,
            telegram_id=222,
            first_name="Test2",
            username="test2",
            grade="11",
            education_level="High School",
            preferred_language="English",
            approval_status="APPROVED",
            selected_courses_json=json.dumps(["Biology", "Chemistry"])
        )
        
        with patch("bot.services.gemini.extract_pdf_topics_and_summary", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ("Physics Textbook", "Physics", "Grade 11", ["Motion", "Forces"], "Physics summary")
            with patch("bot.services.pdf_service.extract_text_from_pdf_bytes") as mock_text:
                mock_text.return_value = ("Physics Chapter 1 content", 10, "SUCCESS", None)
                with patch("bot.services.storage.default_storage.save_file", new_callable=AsyncMock) as mock_save:
                    mock_save.return_value = ("/tmp/phys.pdf", "phys.pdf")
                    with patch("bot.services.storage.default_storage.delete_file", new_callable=AsyncMock):
                        with self.assertRaises(ValueError) as ctx:
                            run_async(pdf_service.process_and_save_pdf(
                                telegram_id=222,
                                pdf_bytes=b"%PDF-1.4 test",
                                original_filename="physics.pdf",
                                student=student
                            ))
                        self.assertIn("Unauthorized Course", str(ctx.exception))

    def test_pdf_upload_security_blocks_grade_mismatch(self):
        from bot.services import pdf_service
        from bot.database.models import StudentModel
        import json
        
        student = StudentModel(
            id=3,
            telegram_id=333,
            first_name="Test3",
            username="test3",
            grade="9",
            education_level="High School",
            preferred_language="English",
            approval_status="APPROVED",
            selected_courses_json=json.dumps(["Biology"])
        )
        
        with patch("bot.services.gemini.extract_pdf_topics_and_summary", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ("Grade 12 Biology", "Biology", "Grade 12", ["Genetics", "Ecology"], "Bio 12 summary")
            with patch("bot.services.pdf_service.extract_text_from_pdf_bytes") as mock_text:
                mock_text.return_value = ("Grade 12 Biology chapter content", 15, "SUCCESS", None)
                with patch("bot.services.storage.default_storage.save_file", new_callable=AsyncMock) as mock_save:
                    mock_save.return_value = ("/tmp/bio12.pdf", "bio12.pdf")
                    with patch("bot.services.storage.default_storage.delete_file", new_callable=AsyncMock):
                        with self.assertRaises(ValueError) as ctx:
                            run_async(pdf_service.process_and_save_pdf(
                                telegram_id=333,
                                pdf_bytes=b"%PDF-1.4 test",
                                original_filename="bio12.pdf",
                                student=student
                            ))
                        self.assertIn("Grade Level Mismatch", str(ctx.exception))
    def test_process_course_name_input_blocks_unregistered_course(self):
        from bot.handlers.study import process_course_name_input
        student_id = 998894
        
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="SecStudent",
            username="sec_student",
            phone_number="0911223344",
            grade="10",
            preferred_language="English",
            selected_courses=["Mathematics"],
            payment_amount=50,
            approval_status="APPROVED"
        ))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = student_id
        mock_msg.text = "History"
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(process_course_name_input(mock_msg, mock_state))
        mock_msg.answer.assert_called()
        call_text = mock_msg.answer.call_args[0][0]
        self.assertIn("Unauthorized Course", call_text)
        mock_state.set_state.assert_not_called()
    def test_grades_keyboard_school_focus(self):
        from bot.handlers.registration import get_grades_keyboard
        kb = get_grades_keyboard()
        button_texts = [btn.text for row in kb.inline_keyboard for btn in row]
        for g in range(1, 13):
            self.assertIn(f"Grade {g}", button_texts)
    def test_calculate_student_payment_grade_12_and_standard(self):
        from bot.services.student_service import calculate_student_payment
        total_g10, details_g10 = calculate_student_payment("10", 2, 50)
        self.assertEqual(total_g10, 100)
        self.assertFalse(details_g10["is_grade_12_package"])
        self.assertEqual(details_g10["per_course_bundle"], 50)
        total_g12, details_g12 = calculate_student_payment("12", 2, 50)
        self.assertEqual(details_g12["per_course_bundle"], 88)
        self.assertEqual(total_g12, 176)
        self.assertTrue(details_g12["is_grade_12_package"])
        self.assertEqual(details_g12["review_fee_per_course"], 38)

    def test_stream_keyboard_and_curriculum_filtering(self):
        from bot.handlers.registration import get_streams_keyboard, get_subjects_selection_keyboard
        
        stream_kb = get_streams_keyboard()
        stream_texts = [btn.text for row in stream_kb.inline_keyboard for btn in row]
        self.assertTrue(any("Natural Science" in t for t in stream_texts))
        self.assertTrue(any("Social Science" in t for t in stream_texts))
        nat_kb = get_subjects_selection_keyboard([], stream="Natural Science")
        nat_texts = [btn.text for row in nat_kb.inline_keyboard for btn in row]
        self.assertTrue(any("Biology" in t for t in nat_texts))
        self.assertTrue(any("Physics" in t for t in nat_texts))
        self.assertFalse(any("Economics" in t for t in nat_texts))
        
        soc_kb = get_subjects_selection_keyboard([], stream="Social Science")
        soc_texts = [btn.text for row in soc_kb.inline_keyboard for btn in row]
        self.assertTrue(any("History" in t for t in soc_texts))
        self.assertTrue(any("Economics" in t for t in soc_texts))
        self.assertFalse(any("Biology" in t for t in soc_texts))

    def test_profile_change_grade_locked_for_approved_students(self):
        from bot.handlers.profile import change_grade_callback
        student_id = 998895
        
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="LockedStudent",
            username="locked_stud",
            phone_number="0911998877",
            grade="12",
            preferred_language="English",
            selected_courses=["Biology"],
            payment_amount=88,
            approval_status="APPROVED"
        ))
        
        mock_cb = AsyncMock()
        mock_cb.from_user.id = student_id
        mock_cb.message.edit_text = AsyncMock()
        mock_cb.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(change_grade_callback(mock_cb, mock_state))
        mock_cb.message.edit_text.assert_called()
        call_text = mock_cb.message.edit_text.call_args[0][0]
        self.assertIn("Locked", call_text)
        self.assertIn("Grade Level", call_text)
        self.assertIn("@Cs1At07", call_text)

    def test_study_methods_picker_and_file_chapter_prompt(self):
        from bot.handlers.study import (
            study_pick_subject_callback,
            study_method_topic_callback,
            study_method_photo_callback,
            study_method_file_callback,
            process_study_file_input,
            StudyStates
        )
        from bot.handlers.pdf import PDFStates, process_exam_chapter_selection
        
        student_id = 998896
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="FlowStudent",
            username="flow_stud",
            phone_number="0911223344",
            grade="12",
            preferred_language="English",
            selected_courses=["Biology"],
            payment_amount=88,
            approval_status="APPROVED"
        ))
        
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_state.update_data = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={"subject": "Biology"})
        
        mock_cb_subj = AsyncMock()
        mock_cb_subj.from_user.id = student_id
        mock_cb_subj.data = "study_pick_subj_Biology"
        mock_cb_subj.message.edit_text = AsyncMock()
        mock_cb_subj.answer = AsyncMock()
        
        run_async(study_pick_subject_callback(mock_cb_subj, mock_state))
        prompt_text = mock_cb_subj.message.edit_text.call_args[0][0]
        self.assertIn("Biology Study Mode", prompt_text)
        self.assertIn("preferred study method", prompt_text)
        
        mock_cb_topic = AsyncMock()
        mock_cb_topic.from_user.id = student_id
        mock_cb_topic.data = "study_method_topic_Biology"
        mock_cb_topic.message.edit_text = AsyncMock()
        mock_cb_topic.answer = AsyncMock()
        
        run_async(study_method_topic_callback(mock_cb_topic, mock_state))
        mock_state.set_state.assert_called_with(StudyStates.waiting_for_text)
        mock_cb_photo = AsyncMock()
        mock_cb_photo.from_user.id = student_id
        mock_cb_photo.data = "study_method_photo_Biology"
        mock_cb_photo.message.edit_text = AsyncMock()
        mock_cb_photo.answer = AsyncMock()
        
        run_async(study_method_photo_callback(mock_cb_photo, mock_state))
        mock_state.set_state.assert_called_with(StudyStates.waiting_for_file)
        
        mock_cb_file = AsyncMock()
        mock_cb_file.from_user.id = student_id
        mock_cb_file.data = "study_method_file_Biology"
        mock_cb_file.message.edit_text = AsyncMock()
        mock_cb_file.answer = AsyncMock()
        
        run_async(study_method_file_callback(mock_cb_file, mock_state))
        mock_state.set_state.assert_called_with(StudyStates.waiting_for_file)
        file_prompt = mock_cb_file.message.edit_text.call_args[0][0]
        self.assertIn("PDF", file_prompt)
        
        mock_doc_msg = AsyncMock()
        mock_doc_msg.from_user.id = student_id
        mock_doc_msg.document.file_id = "doc123"
        mock_doc_msg.document.file_name = "Grade12_Biology.pdf"
        mock_doc_msg.document.mime_type = "application/pdf"
        mock_doc_msg.document.file_size = 1024
        mock_doc_msg.answer = AsyncMock()
        
        with patch("bot.services.pdf_service.process_and_save_pdf", new_callable=AsyncMock) as mock_pdf_save:
            mock_pdf_save.return_value = AsyncMock(
                id=88,
                title="Grade12_Biology.pdf",
                filename="Grade12_Biology.pdf",
                extracted_text="Chapter 1: Molecular Biology"
            )
            run_async(process_study_file_input(mock_doc_msg, mock_state))
            mock_state.set_state.assert_called_with(PDFStates.waiting_for_chapter)
            chap_ask = mock_doc_msg.answer.call_args_list[-1][0][0]
            
    def test_admin_student_edit_grade_and_courses(self):
        from bot.handlers.admin import (
            admin_manage_callback,
            admin_setgrade_callback,
            admin_togcourse_callback,
            admin_addallcourses_callback,
            admin_edit_command
        )
        
        student_id = 998897
        admin_id = config.ADMIN_IDS[0]
        
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="EditTarget",
            username="edittarget",
            phone_number="0911556677",
            grade="10",
            preferred_language="English",
            selected_courses=["Biology"],
            payment_amount=50,
            approval_status="APPROVED"
        ))
        
        mock_cb_manage = AsyncMock()
        mock_cb_manage.from_user.id = admin_id
        mock_cb_manage.data = f"admin_manage_{student_id}"
        mock_cb_manage.message.edit_text = AsyncMock()
        mock_cb_manage.answer = AsyncMock()
        
        run_async(admin_manage_callback(mock_cb_manage))
        manage_text = mock_cb_manage.message.edit_text.call_args[0][0]
        self.assertIn("Student Profile Management", manage_text)
        self.assertIn("EditTarget", manage_text)
        
        mock_cb_grade = AsyncMock()
        mock_cb_grade.from_user.id = admin_id
        mock_cb_grade.data = f"admin_setgrade_{student_id}_12"
        mock_cb_grade.message.edit_text = AsyncMock()
        mock_cb_grade.answer = AsyncMock()
        mock_cb_grade.bot.send_message = AsyncMock()
        
        run_async(admin_setgrade_callback(mock_cb_grade))
        updated_student = run_async(student_service.get_student(student_id))
        self.assertEqual(str(updated_student.grade), "12")
        
        mock_cb_course = AsyncMock()
        mock_cb_course.from_user.id = admin_id
        mock_cb_course.data = f"admin_togcourse_{student_id}_Chemistry"
        mock_cb_course.message.edit_text = AsyncMock()
        mock_cb_course.answer = AsyncMock()
        
        run_async(admin_togcourse_callback(mock_cb_course))
        updated_student = run_async(student_service.get_student(student_id))
        self.assertIn("Chemistry", updated_student.selected_courses)
        self.assertIn("Biology", updated_student.selected_courses)
        
        mock_cb_all = AsyncMock()
        mock_cb_all.from_user.id = admin_id
        mock_cb_all.data = f"admin_addallcourses_{student_id}"
        mock_cb_all.message.edit_text = AsyncMock()
        mock_cb_all.answer = AsyncMock()
        
        run_async(admin_addallcourses_callback(mock_cb_all))
        updated_student = run_async(student_service.get_student(student_id))
    
    def test_persistent_reply_menu_back_clear_buttons(self):
        from bot.keyboards.main_menu import get_main_reply_keyboard
        from bot.handlers.start import menu_command, back_command
        from bot.handlers.chat import reply_clear_button_handler
        from bot.database.repositories import conversation as conv_repo
        
        reply_kb = get_main_reply_keyboard("English")
        self.assertEqual(len(reply_kb.keyboard), 1)
        self.assertEqual(len(reply_kb.keyboard[0]), 3)
        self.assertEqual(reply_kb.keyboard[0][0].text, "📱 Menu")
        self.assertEqual(reply_kb.keyboard[0][1].text, "🔙 Back")
        self.assertEqual(reply_kb.keyboard[0][2].text, "🧹 Clear")
        
        student_id = 998811
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="ReplyUser",
            username="replyuser",
            phone_number="0911998877",
            grade="11",
            preferred_language="English",
            selected_courses=["Physics"],
            payment_amount=50,
            approval_status="APPROVED"
        ))
        
        mock_msg_menu = AsyncMock()
        mock_msg_menu.from_user.id = student_id
        mock_msg_menu.text = "📱 Menu"
        mock_msg_menu.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(menu_command(mock_msg_menu, mock_state))
        menu_reply = mock_msg_menu.answer.call_args[0][0]
        self.assertIn("Main Dashboard", menu_reply)
        
        mock_msg_back = AsyncMock()
        mock_msg_back.from_user.id = student_id
        mock_msg_back.text = "🔙 Back"
        mock_msg_back.answer = AsyncMock()
        
        run_async(back_command(mock_msg_back, mock_state))
        mock_state.clear.assert_called()
        back_reply = mock_msg_back.answer.call_args[0][0]
        self.assertIn("Returned to Main Menu", back_reply)
        
        run_async(asyncio.to_thread(conv_repo.add_conversation_message, student_id, "user", "Hello tutor"))
        history_before = run_async(asyncio.to_thread(conv_repo.get_conversation_history, student_id))
        self.assertTrue(len(history_before) > 0)
        
        mock_msg_clear = AsyncMock()
        mock_msg_clear.from_user.id = student_id
        mock_msg_clear.text = "🧹 Clear"
        mock_msg_clear.answer = AsyncMock()
        
        run_async(reply_clear_button_handler(mock_msg_clear, mock_state))
        mock_state.clear.assert_called()
        history_after = run_async(asyncio.to_thread(conv_repo.get_conversation_history, student_id))
        self.assertEqual(len(history_after), 0)
        clear_reply = mock_msg_clear.answer.call_args[0][0]
    def test_interactive_pdf_exam_mcqs_and_score_evaluation(self):
        from bot.handlers.pdf import (
            pdf_exam_start_mcqs_callback,
            pdf_mcq_ans_callback,
            pdf_mcq_next_callback,
            pdf_mcq_finish_callback,
            pdf_exam_retest_topic_callback
        )
        
        student_id = 998844
        run_async(student_service.register_student_full(
            telegram_id=student_id,
            first_name="MCQUser",
            username="mcquser",
            phone_number="0911443322",
            grade="12",
            preferred_language="English",
            selected_courses=["Chemistry"],
            payment_amount=50,
            approval_status="APPROVED"
        ))
        
        mock_state = AsyncMock()
        mock_data = {
            "chapter_name": "Unit 1",
            "filename": "Grade12_Chemistry.pdf",
            "extracted_text": "Acid base concepts...",
            "topics_list": ["Acid-Base Concepts", "pH and pOH"],
            "current_topic_index": 0,
            "current_topic_name": "Acid-Base Concepts",
            "current_mcqs": [
                {
                    "number": 1,
                    "question": "What is the conjugate base of HCl?",
                    "option_a": "Cl-",
                    "option_b": "H2O",
                    "option_c": "H3O+",
                    "option_d": "OH-",
                    "correct_answer": "A",
                    "explanation": "Cl- is the conjugate base of HCl."
                },
                {
                    "number": 2,
                    "question": "What is Arrhenius acid?",
                    "option_a": "Produces OH-",
                    "option_b": "Increases H+ in water",
                    "option_c": "Electron donor",
                    "option_d": "None",
                    "correct_answer": "B",
                    "explanation": "Arrhenius acid produces H+ in water."
                }
            ],
            "current_question_idx": 0,
            "student_answers": {}
        }
        mock_state.get_data.return_value = mock_data
        
        mock_cb_start = AsyncMock()
        mock_cb_start.from_user.id = student_id
        mock_cb_start.data = "pdf_exam_start_mcqs"
        mock_cb_start.message.edit_text = AsyncMock()
        mock_cb_start.answer = AsyncMock()
        
        run_async(pdf_exam_start_mcqs_callback(mock_cb_start, mock_state))
        q1_text = mock_cb_start.message.edit_text.call_args[0][0]
        self.assertIn("Question 1 of 2", q1_text)
        self.assertIn("conjugate base of HCl", q1_text)
        
        mock_cb_ans1 = AsyncMock()
        mock_cb_ans1.from_user.id = student_id
        mock_cb_ans1.data = "pdf_mcq_ans_1_A"
        mock_cb_ans1.message.edit_text = AsyncMock()
        mock_cb_ans1.answer = AsyncMock()
        
        run_async(pdf_mcq_ans_callback(mock_cb_ans1, mock_state))
        ans1_feedback = mock_cb_ans1.message.edit_text.call_args[0][0]
        self.assertIn("Correct!", ans1_feedback)
        
        mock_cb_next = AsyncMock()
        mock_cb_next.from_user.id = student_id
        mock_cb_next.data = "pdf_mcq_next_1"
        mock_cb_next.message.edit_text = AsyncMock()
        mock_cb_next.answer = AsyncMock()
        
        run_async(pdf_mcq_next_callback(mock_cb_next, mock_state))
        q2_text = mock_cb_next.message.edit_text.call_args[0][0]
        self.assertIn("Question 2 of 2", q2_text)
        
        mock_cb_ans2 = AsyncMock()
        mock_cb_ans2.from_user.id = student_id
        mock_cb_ans2.data = "pdf_mcq_ans_2_A"
        mock_cb_ans2.message.edit_text = AsyncMock()
        mock_cb_ans2.answer = AsyncMock()
        
        run_async(pdf_mcq_ans_callback(mock_cb_ans2, mock_state))
        ans2_feedback = mock_cb_ans2.message.edit_text.call_args[0][0]
        self.assertIn("Incorrect", ans2_feedback)
        
        mock_cb_finish = AsyncMock()
        mock_cb_finish.from_user.id = student_id
        mock_cb_finish.data = "pdf_mcq_finish"
        mock_cb_finish.message.edit_text = AsyncMock()
        mock_cb_finish.answer = AsyncMock()
        
        run_async(pdf_mcq_finish_callback(mock_cb_finish, mock_state))
        score_text = mock_cb_finish.message.edit_text.call_args[0][0]
        self.assertIn("Exam Checkpoint", score_text)
        self.assertIn("Score:", score_text)

if __name__ == "__main__":
    unittest.main()





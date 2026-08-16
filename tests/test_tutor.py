import os
import sqlite3
import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Override database path for a clean test run
TEST_DB_PATH = "test_tutor_bot.db"
os.environ["DATABASE_PATH"] = TEST_DB_PATH

from config import DATABASE_PATH
from bot.database.database import init_db, get_db_connection
from bot.database.models import StudentModel, ConversationModel
from bot.database.repositories import student as student_repo
from bot.database.repositories import conversation as conv_repo
from bot.services import student_service, conversation_service, learning_service
from bot.services.gemini import ask_gemini_with_profile
from bot.handlers.start import start as start_handler
from bot.handlers.profile import show_profile, ProfileStates
from bot.handlers.chat import chat as chat_handler, clear_chat, new_chat, clear_confirm_callback, cancel_action

def run_async(coro):
    return asyncio.run(coro)

class TestStudentTutor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import config
        config.DATABASE_PATH = TEST_DB_PATH
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Cleanup database
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except PermissionError:
                pass

    def setUp(self):
        # Reset admin IDs and DB path
        import config
        config.DATABASE_PATH = TEST_DB_PATH
        config.ADMIN_IDS = [8223004316]
        
        # Clear tables before each test
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

    def test_database_initialization(self):
        """Verify the database tables and indexes exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify students table
        cursor.execute("PRAGMA table_info(students)")
        student_columns = {row[1]: row[2] for row in cursor.fetchall()}
        self.assertIn("telegram_id", student_columns)
        self.assertIn("grade", student_columns)
        self.assertIn("education_level", student_columns)
        self.assertIn("preferred_language", student_columns)
        
        # Verify conversation table
        cursor.execute("PRAGMA table_info(conversation)")
        conv_columns = {row[1]: row[2] for row in cursor.fetchall()}
        self.assertIn("telegram_id", conv_columns)
        self.assertIn("role", conv_columns)
        self.assertIn("message", conv_columns)
        
        conn.close()

    def test_student_profile_registration_and_update(self):
        """Verify registering a student and updating their grade/language works."""
        user_id = 12345
        
        # Register
        student = run_async(student_service.register_student(user_id, "Alice", "alice_user"))
        self.assertIsNotNone(student)
        self.assertEqual(student.first_name, "Alice")
        self.assertIsNone(student.grade)
        
        # Update grade
        run_async(student_service.update_grade(user_id, "8"))
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(str(student.grade), "8")
        self.assertEqual(student.education_level, "Middle School")
        
        # Update language
        run_async(student_service.update_language(user_id, "Spanish"))
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(student.preferred_language, "Spanish")

    def test_conversation_history_retrieval_and_limit(self):
        """Verify conversation messages are stored and retrieved (capped at last 20 chronologically)."""
        user_id = 55555
        
        # Add 25 messages
        for i in range(1, 26):
            role = "user" if i % 2 != 0 else "assistant"
            run_async(conversation_service.add_message(user_id, role, f"Message {i}"))
            
        history = run_async(conversation_service.get_history(user_id, limit=20))
        
        # Must be exactly 20
        self.assertEqual(len(history), 20)
        
        # Oldest message in slice should be Message 6
        self.assertEqual(history[0].message, "Message 6")
        
        # Newest message should be Message 25
        self.assertEqual(history[-1].message, "Message 25")

    def test_cross_talk_separation(self):
        """Verify different Telegram users have isolated profiles and histories."""
        user_a = 11111
        user_b = 22222
        
        # Register User A
        run_async(student_service.register_student(user_a, "UserA", "user_a"))
        run_async(student_service.update_grade(user_a, "6"))
        run_async(conversation_service.add_message(user_a, "user", "Hello from A"))
        
        # Register User B
        run_async(student_service.register_student(user_b, "UserB", "user_b"))
        run_async(student_service.update_grade(user_b, "11"))
        run_async(conversation_service.add_message(user_b, "user", "Hello from B"))
        
        student_a = run_async(student_service.get_student(user_a))
        student_b = run_async(student_service.get_student(user_b))
        
        self.assertEqual(str(student_a.grade), "6")
        self.assertEqual(str(student_b.grade), "11")
        
        history_a = run_async(conversation_service.get_history(user_a))
        history_b = run_async(conversation_service.get_history(user_b))
        
        self.assertEqual(len(history_a), 1)
        self.assertEqual(history_a[0].message, "Hello from A")
        self.assertEqual(len(history_b), 1)
        self.assertEqual(history_b[0].message, "Hello from B")

    def test_handler_start_new_and_returning(self):
        """Verify `/start` welcomes returning students with dashboard."""
        user_id = 99999
        run_async(student_service.register_student(user_id, "Charlie", "charlie_username"))
        
        # Case 1: Returning student with no grade (APPROVED)
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.from_user.first_name = "Charlie"
        mock_msg.from_user.username = "charlie_username"
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(start_handler(mock_msg, mock_state))
        
        # Verify welcomed
        self.assertIn("Smart Study Bot", mock_msg.answer.call_args[0][0])
        
        # Case 2: Returning student with set grade (APPROVED)
        run_async(student_service.update_grade(user_id, "10"))
        mock_msg_returning = AsyncMock()
        mock_msg_returning.from_user.id = user_id
        mock_msg_returning.answer = AsyncMock()
        
        run_async(start_handler(mock_msg_returning, mock_state))
        self.assertIn("Smart Study Bot", mock_msg_returning.answer.call_args[0][0])
        self.assertIn("10", mock_msg_returning.answer.call_args[0][0])

    def test_handler_profile_display(self):
        """Verify `/profile` displays student information correctly."""
        user_id = 88888
        run_async(student_service.register_student(user_id, "Daisy", "daisy_username"))
        run_async(student_service.update_grade(user_id, "7"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(show_profile(mock_msg))
        
        reply_text = mock_msg.answer.call_args[0][0]
        self.assertIn("Student Profile", reply_text)
        self.assertIn("Daisy", reply_text)
        self.assertIn("7", reply_text)

    def test_newchat_command(self):
        """Verify `/newchat` resets conversation history but preserves student profile."""
        user_id = 77777
        run_async(student_service.register_student(user_id, "Eric", "eric_username"))
        run_async(student_service.update_grade(user_id, "9"))
        run_async(conversation_service.add_message(user_id, "user", "What is geography?"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(new_chat(mock_msg))
        
        # Profile exists, history wiped
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(str(student.grade), "9")
        self.assertEqual(len(run_async(conversation_service.get_history(user_id))), 0)
        mock_msg.answer.assert_called_once()
        call_text = mock_msg.answer.call_args[0][0]
        self.assertIn("New Chat Started", call_text)

    def test_clearchat_confirm(self):
        """Verify callback confirmations for clearing chat history."""
        user_id = 66666
        run_async(conversation_service.add_message(user_id, "user", "Hello"))
        
        mock_callback = AsyncMock()
        mock_callback.from_user.id = user_id
        mock_callback.message.edit_text = AsyncMock()
        mock_callback.answer = AsyncMock()
        
        run_async(clear_confirm_callback(mock_callback))
        
        # Verify history deleted
        self.assertEqual(len(run_async(conversation_service.get_history(user_id))), 0)

    @patch("bot.handlers.chat.ask_gemini_with_profile")
    def test_handler_gemini_failure(self, mock_ask):
        """Verify error handling on Gemini failure uses the updated templates."""
        mock_ask.side_effect = Exception("Service unavailable")
        
        user_id = 44444
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.from_user.first_name = "FailureUser"
        mock_msg.from_user.username = "failure_user"
        mock_msg.text = "Tell me a joke"
        mock_msg.answer = AsyncMock()
        
        run_async(chat_handler(mock_msg))
        
        mock_msg.answer.assert_any_call("🤔 Thinking...")
        mock_msg.answer.assert_any_call(
            "⚠️ *Connection Error*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "I'm having trouble connecting to the AI right now.\n\n"
            "Please try again in a moment.",
            parse_mode="Markdown"
        )

    @patch("bot.handlers.chat.ask_gemini_with_profile")
    def test_gemini_dynamic_grade_extraction(self, mock_ask):
        """Verify dynamic profile grade extraction via Structured JSON outputs works."""
        mock_ask.return_value = ("Gravity is an attractive force between masses.", "10", "English")
        
        user_id = 33333
        run_async(student_service.register_student(user_id, "George", "george_username"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.from_user.first_name = "George"
        mock_msg.from_user.username = "george_username"
        mock_msg.text = "I am in grade 10 now, can you explain gravity?"
        mock_msg.answer = AsyncMock()
        
        run_async(chat_handler(mock_msg))
        
        # Verify the student profile was automatically updated to Grade 10!
        student = run_async(student_service.get_student(user_id))
        self.assertEqual(str(student.grade), "10")
        self.assertEqual(student.education_level, "High School")

    def test_grade_preservation_in_gemini_instruction(self):
        """Verify system instruction contains student grade, education level, and language."""
        student = StudentModel(
            id=1,
            telegram_id=101,
            first_name="Helen",
            username="helen",
            grade="8",
            education_level="Middle School",
            preferred_language="Afaan Oromo",
            approval_status="APPROVED",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        from bot.services.gemini import get_system_instruction
        instruction = get_system_instruction(student)
        
        self.assertIn("Grade: 8", instruction)
        self.assertIn("Education Level: Middle School", instruction)
        self.assertIn("Language: Afaan Oromo", instruction)

    def test_study_mode_selection_and_session_creation(self):
        """Verify that study command displays keyboards and selecting a topic registers a session."""
        from bot.handlers.study import (
            start_study_mode, select_subject_callback, select_topic_callback,
            process_study_text_input, StudyStates
        )
        user_id = 99111
        run_async(student_service.register_student(user_id, "StudyStudent", "studystudent"))
        
        # Case 1: Start study command
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        run_async(start_study_mode(mock_msg))
        mock_msg.answer.assert_called_once()
        self.assertIn("Study Mode", mock_msg.answer.call_args[0][0])
        
        # Case 2: Select subject callback
        mock_cb_sub = AsyncMock()
        mock_cb_sub.from_user.id = user_id
        mock_cb_sub.data = "study_sub_School Subjects"
        mock_cb_sub.message.edit_text = AsyncMock()
        mock_cb_sub.answer = AsyncMock()
        run_async(select_subject_callback(mock_cb_sub))
        
        edit_text = mock_cb_sub.message.edit_text.call_args[0][0]
        self.assertIn("School Subjects", edit_text)
        self.assertIn("Choose a topic", edit_text)
        
        # Case 3: Select topic callback
        mock_cb_topic = AsyncMock()
        mock_cb_topic.from_user.id = user_id
        mock_cb_topic.data = "study_topic_School Subjects|🧬 Biology"
        mock_cb_topic.message.edit_text = AsyncMock()
        mock_cb_topic.answer = AsyncMock()
        
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_state.update_data = AsyncMock()
        
        run_async(select_topic_callback(mock_cb_topic, mock_state))
        mock_state.set_state.assert_called_with(StudyStates.waiting_for_input_choice)
        mock_state.update_data.assert_called_with(subject="School Subjects", topic="🧬 Biology")
        
        # Case 4: Process text description to launch session
        mock_msg_text = AsyncMock()
        mock_msg_text.from_user.id = user_id
        mock_msg_text.from_user.first_name = "StudyStudent"
        mock_msg_text.from_user.username = "studystudent"
        mock_msg_text.text = "Explain photosynthesis and plant cell anatomy"
        mock_msg_text.answer = AsyncMock()
        
        mock_state.get_data = AsyncMock(return_value={"subject": "School Subjects", "topic": "🧬 Biology"})
        mock_state.clear = AsyncMock()
        
        with patch("bot.handlers.study.ask_gemini_with_profile", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = ("Introduction to photosynthesis...", None, None)
            run_async(process_study_text_input(mock_msg_text, mock_state))
            
            # Verify session registered in database
            session = run_async(learning_service.get_active_session(user_id))
            self.assertIsNotNone(session)
            self.assertEqual(session.subject, "School Subjects")
            self.assertEqual(session.topic, "🧬 Biology")
            self.assertEqual(session.stage, "INTRODUCTION")

    def test_current_command(self):
        """Verify /current command shows active study session details."""
        from bot.handlers.study import show_current_session
        user_id = 99112
        run_async(student_service.register_student(user_id, "CurrentStudent", "currentstudent"))
        run_async(student_service.update_grade(user_id, "11"))
        run_async(learning_service.start_session(user_id, "School Subjects", "⚛️ Physics"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(show_current_session(mock_msg))
        
        reply = mock_msg.answer.call_args[0][0]
        self.assertIn("Current Study Session", reply)
        self.assertIn("Physics", reply)
        self.assertIn("11", reply)

    def test_cancel_command_deactivates_session(self):
        """Verify /cancel command deactivates the current study session."""
        user_id = 99113
        run_async(student_service.register_student(user_id, "CancelStudent", "cancelstudent"))
        run_async(learning_service.start_session(user_id, "School Subjects", "🧪 Chemistry"))
        
        # Verify active
        self.assertIsNotNone(run_async(learning_service.get_active_session(user_id)))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(cancel_action(mock_msg, mock_state))
        
        # Verify deactivated
        self.assertIsNone(run_async(learning_service.get_active_session(user_id)))
        self.assertIn("Study Session Stopped", mock_msg.answer.call_args[0][0])

    def test_start_command_starts_registration_fsm(self):
        """Verify /start triggers registration FSM for unregistered users."""
        user_id = 77111
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(start_handler(mock_msg, mock_state))
        
        # Verify FSM was set to waiting_for_name
        from bot.handlers.registration import RegistrationStates
        mock_state.set_state.assert_called_once_with(RegistrationStates.waiting_for_name)
        self.assertIn("Student Registration", mock_msg.answer.call_args[0][0])

    def test_approval_middleware_blocking(self):
        """Verify ApprovalMiddleware blocks unregistered, pending, and rejected users from actions."""
        from bot.middlewares.approval import ApprovalMiddleware
        middleware = ApprovalMiddleware()
        
        # Case 1: Unregistered user tries to send a message
        mock_msg_unreg = AsyncMock()
        mock_msg_unreg.text = "Hello tutor"
        mock_msg_unreg.from_user.id = 77112
        mock_msg_unreg.answer = AsyncMock()
        
        data_unreg = {"event_from_user": mock_msg_unreg.from_user, "state": AsyncMock()}
        next_handler = AsyncMock()
        
        run_async(middleware(next_handler, mock_msg_unreg, data_unreg))
        next_handler.assert_not_called()
        mock_msg_unreg.answer.assert_called_with("Welcome to Smart Study Bot! Please send /start to register and begin learning.")

    def test_admin_approve_callback(self):
        """Verify that admin approval updates DB, notifies student, and edits message."""
        from bot.handlers.admin import approve_student_callback
        import config
        
        config.ADMIN_IDS = [99999]
        
        student_id = 77113
        run_async(student_service.register_student_pending(student_id, "Jane Doe", "janedoe", "12", "English"))
        
        mock_cb = AsyncMock()
        mock_cb.from_user.id = 99999
        mock_cb.data = f"admin_approve_{student_id}"
        mock_cb.message.edit_text = AsyncMock()
        mock_cb.answer = AsyncMock()
        mock_cb.bot.send_message = AsyncMock()
        
        run_async(approve_student_callback(mock_cb))
        
        student = run_async(student_service.get_student(student_id))
        self.assertEqual(student.approval_status, "APPROVED")
        self.assertTrue(mock_cb.bot.send_message.called)
        
        edit_text = mock_cb.message.edit_text.call_args[0][0]
        self.assertIn("Student Approved", edit_text)
        self.assertIn("Jane Doe", edit_text)

    def test_admin_reject_callback(self):
        """Verify that admin rejection updates DB, notifies student, and edits message."""
        from bot.handlers.admin import reject_student_callback
        import config
        
        config.ADMIN_IDS = [99999]
        
        student_id = 77114
        run_async(student_service.register_student_pending(student_id, "Rejected Student", "rejected", "8", "Amharic"))
        
        mock_cb = AsyncMock()
        mock_cb.from_user.id = 99999
        mock_cb.data = f"admin_reject_{student_id}"
        mock_cb.message.edit_text = AsyncMock()
        mock_cb.answer = AsyncMock()
        mock_cb.bot.send_message = AsyncMock()
        
        run_async(reject_student_callback(mock_cb))
        
        student = run_async(student_service.get_student(student_id))
        self.assertEqual(student.approval_status, "REJECTED")
        self.assertTrue(mock_cb.bot.send_message.called)

    def test_quiz_no_active_session(self):
        """Verify /quiz with no active study session instructs to use /study."""
        from bot.handlers.quiz import quiz_start
        user_id = 88111
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(quiz_start(mock_msg))
        
        reply_text = mock_msg.answer.call_args[0][0]
        self.assertIn("active study", reply_text)
        self.assertIn("/study", reply_text)

    def test_quiz_active_session_and_cancellation(self):
        """Verify /quiz starts a session, handles cancel, and does double answers check."""
        from bot.handlers.quiz import quiz_start, quiz_answer_callback
        from bot.services import quiz_service
        from bot.database.repositories import quiz as quiz_repo
        
        user_id = 88112
        run_async(student_service.register_student(user_id, "Jane", "jane"))
        ls = run_async(learning_service.start_session(user_id, "School Subjects", "🧬 Biology"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        with patch("bot.services.gemini.client.aio.models.generate_content", new_callable=AsyncMock) as mock_gemini:
            mock_resp = AsyncMock()
            mock_resp.parsed.question = "What is mitosis?"
            mock_resp.parsed.options = {"A": "Cell division", "B": "Energy production", "C": "Digestion", "D": "Respiration"}
            mock_resp.parsed.correct_answer = "A"
            mock_resp.parsed.explanation = "Mitosis is eukaryotic cell division."
            mock_gemini.return_value = mock_resp
            
            run_async(quiz_start(mock_msg))
            
            active_quiz = run_async(quiz_service.get_active_quiz(user_id))
            self.assertIsNotNone(active_quiz)
            self.assertEqual(active_quiz.current_question, 1)
            
            # Simulate student answering correctly
            mock_cb = AsyncMock()
            mock_cb.from_user.id = user_id
            mock_cb.data = f"quiz_ans_{active_quiz.id}_1_A"
            mock_cb.message.edit_text = AsyncMock()
            mock_cb.answer = AsyncMock()
            
            run_async(quiz_answer_callback(mock_cb))
            
            # Double click check
            mock_cb_double = AsyncMock()
            mock_cb_double.from_user.id = user_id
            mock_cb_double.data = f"quiz_ans_{active_quiz.id}_1_B"
            mock_cb_double.answer = AsyncMock()
            
            run_async(quiz_answer_callback(mock_cb_double))
            mock_cb_double.answer.assert_called_with("This question has already been answered. Please continue with the next question.", show_alert=True)

    def test_quiz_completion_flow(self):
        """Verify that 5 quiz questions lead to quiz completion and stage transition."""
        from bot.services import quiz_service
        from bot.database.repositories import quiz as quiz_repo
        
        user_id = 88113
        run_async(student_service.register_student(user_id, "TestStudent", "test_student"))
        ls = run_async(learning_service.start_session(user_id, "School Subjects", "🧬 Biology"))
        quiz = run_async(quiz_service.start_quiz(user_id, ls.id, "School Subjects", "🧬 Biology"))
        
        # Simulate 5 questions answered (4 correct, 1 wrong)
        for i in range(1, 6):
            q = run_async(asyncio.to_thread(
                quiz_repo.save_quiz_question,
                quiz.id, i, f"Question {i}", '{"A":"OptA", "B":"OptB", "C":"OptC", "D":"OptD"}', "A", f"Exp {i}"
            ))
            run_async(asyncio.to_thread(quiz_repo.update_session_progress, quiz.id, i))
            choice = "A" if i != 5 else "B" # Question 5 answered wrong
            is_correct, exp, updated_quiz = run_async(quiz_service.evaluate_answer(user_id, quiz, q, choice))
            
        self.assertEqual(updated_quiz.status, "COMPLETED")
        self.assertEqual(updated_quiz.correct_answers, 4)
        
        updated_ls = run_async(learning_service.get_active_session(user_id))
        self.assertEqual(updated_ls.stage, "REVIEW")

    def test_quiz_cancel_during_quiz(self):
        """Verify that /cancel during quiz deactivates it but keeps learning session."""
        from bot.services import quiz_service
        from bot.database.repositories import quiz as quiz_repo
        user_id = 88114
        run_async(student_service.register_student(user_id, "Joe", "joe"))
        ls = run_async(learning_service.start_session(user_id, "School Subjects", "🧬 Biology"))
        quiz = run_async(quiz_service.start_quiz(user_id, ls.id, "School Subjects", "🧬 Biology"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(cancel_action(mock_msg, mock_state))
        
        quiz_check = run_async(asyncio.to_thread(quiz_repo.get_quiz_session_by_id, quiz.id))
        self.assertEqual(quiz_check.status, "CANCELLED")
        
        ls_check = run_async(learning_service.get_active_session(user_id))
        self.assertIsNotNone(ls_check)

    def test_study_material_file_input_processing(self):
        """Verify that sending a study file (photo) registers session and converts file to Gemini part."""
        from bot.handlers.study import process_study_file_input
        
        user_id = 99120
        run_async(student_service.register_student(user_id, "FileStudent", "file_student"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.from_user.first_name = "FileStudent"
        mock_msg.from_user.username = "file_student"
        mock_msg.caption = "My notes photo description"
        mock_msg.photo = [AsyncMock()]
        mock_msg.answer = AsyncMock()
        
        mock_msg.bot.get_file = AsyncMock()
        mock_msg.bot.download_file = AsyncMock()
        
        mock_state = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={"subject": "Computer Science", "topic": "🐍 Python"})
        mock_state.clear = AsyncMock()
        
        with patch("bot.handlers.study.ask_gemini_with_profile", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = ("Multimodal lesson content", None, None)
            
            run_async(process_study_file_input(mock_msg, mock_state))
            
            active_session = run_async(learning_service.get_active_session(user_id))
            self.assertIsNotNone(active_session)
            self.assertEqual(active_session.subject, "Computer Science")
            self.assertEqual(active_session.topic, "🐍 Python")
            
            mock_ask.assert_called_once()
            called_q = mock_ask.call_args[1]["question"]
            self.assertIsInstance(called_q, list)
            self.assertTrue(len(called_q) > 0)

    def test_action_test_command_and_grading(self):
        """Verify that /test command generates questions, sets state, and grades answer on reply."""
        from bot.handlers.actions import ActionStates, test_start, process_test_answer
        
        user_id = 99121
        run_async(student_service.register_student(user_id, "TestStudent", "test_student"))
        run_async(learning_service.start_session(user_id, "Computer Science", "🐍 Python"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_state.update_data = AsyncMock()
        
        with patch("bot.handlers.actions.gemini_service.ask_gemini_with_profile", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = ("Test Question 1, 2, 3", None, None)
            
            run_async(test_start(mock_msg, mock_state))
            
            mock_state.set_state.assert_called_once_with(ActionStates.waiting_for_test_answer)
            mock_state.update_data.assert_called_once()
            
            thinking = mock_msg.answer.return_value
            reply = thinking.edit_text.call_args[0][0]
            self.assertIn("Written Test Mode", reply)
            self.assertIn("Test Question 1, 2, 3", reply)
            
        # Simulate answering
        mock_msg_ans = AsyncMock()
        mock_msg_ans.from_user.id = user_id
        mock_msg_ans.text = "My answers to the test."
        mock_msg_ans.answer = AsyncMock()
        
        mock_state.get_data = AsyncMock(return_value={"test_questions": "Test Question 1, 2, 3"})
        mock_state.clear = AsyncMock()
        
        with patch("bot.handlers.actions.gemini_service.grade_written_test", new_callable=AsyncMock) as mock_grade:
            mock_grade.return_value = (9, "A", "Good understanding", "None", "None", "Keep it up", "Constructive Grade: A")
            
            run_async(process_test_answer(mock_msg_ans, mock_state))
            
            thinking = mock_msg_ans.answer.return_value
            reply = thinking.edit_text.call_args[0][0]
            self.assertIn("Test Evaluation Results", reply)
            self.assertIn("Constructive Grade: A", reply)

    def test_action_short_note_command(self):
        """Verify that /short_note command generates bulleted notes summary."""
        from bot.handlers.actions import short_note_start
        
        user_id = 99122
        run_async(student_service.register_student(user_id, "NoteStudent", "notestudent"))
        run_async(learning_service.start_session(user_id, "Computer Science", "🐍 Python"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        with patch("bot.handlers.actions.gemini_service.ask_gemini_with_profile", new_callable=AsyncMock) as mock_ask:
            mock_ask.return_value = ("Concise note content", None, None)
            
            run_async(short_note_start(mock_msg))
            
            thinking = mock_msg.answer.return_value
            reply = thinking.edit_text.call_args[0][0]
            self.assertIn("Short Notes Summary", reply)
            self.assertIn("Concise note content", reply)

    def test_action_personalize_command(self):
        """Verify that /personalize command outputs option keypad."""
        from bot.handlers.actions import personalize_start
        
        user_id = 99123
        run_async(student_service.register_student(user_id, "PersStudent", "persstudent"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(personalize_start(mock_msg))
        
        reply = mock_msg.answer.call_args[0][0]
        self.assertIn("Personalization", reply)
        self.assertIn("Grade Level", reply)

    def test_registration_grades_college_university(self):
        """Verify that FSM grade selection handles College and University and maps to correct education level."""
        from bot.handlers.registration import process_grade_callback, RegistrationStates
        
        user_id = 99124
        mock_cb_college = AsyncMock()
        mock_cb_college.from_user.id = user_id
        mock_cb_college.from_user.first_name = "CollStudent"
        mock_cb_college.from_user.username = "coll_student"
        mock_cb_college.data = "reg_grade_College"
        mock_cb_college.message.edit_text = AsyncMock()
        mock_cb_college.answer = AsyncMock()
        
        mock_state = AsyncMock()
        mock_state.set_state = AsyncMock()
        mock_state.update_data = AsyncMock()
        
        run_async(process_grade_callback(mock_cb_college, mock_state))
        
        mock_state.update_data.assert_called_with(grade="College")
        mock_state.set_state.assert_called_with(RegistrationStates.waiting_for_language)

    def test_registration_cancel_callback(self):
        """Verify registration cancellation clears state and responds."""
        from bot.handlers.registration import process_cancel_callback
        
        mock_cb = AsyncMock()
        mock_cb.data = "reg_cancel"
        mock_cb.message.edit_text = AsyncMock()
        mock_cb.answer = AsyncMock()
        mock_state = AsyncMock()
        mock_state.clear = AsyncMock()
        
        run_async(process_cancel_callback(mock_cb, mock_state))
        mock_state.clear.assert_called_once()
        self.assertIn("cancelled", mock_cb.message.edit_text.call_args[0][0])

    def test_profile_cancel_callback(self):
        """Verify profile cancellation clears state and edits text."""
        from bot.handlers.profile import cancel_profile_callback
        
        mock_cb = AsyncMock()
        mock_cb.message.edit_text = AsyncMock()
        mock_state = AsyncMock()
        mock_state.get_state = AsyncMock(return_value="ProfileStates:waiting_for_grade")
        mock_state.clear = AsyncMock()
        
        run_async(cancel_profile_callback(mock_cb, mock_state))
        mock_state.clear.assert_called_once()
        self.assertIn("cancelled", mock_cb.message.edit_text.call_args[0][0])

    def test_admin_broadcast_empty_message(self):
        """Verify /broadcast with no message prompts the administrator."""
        from bot.handlers.admin import broadcast_command
        import config
        config.ADMIN_IDS = [99999]
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = 99999
        mock_msg.text = "/broadcast"
        mock_msg.answer = AsyncMock()
        
        run_async(broadcast_command(mock_msg))
        self.assertIn("Usage", mock_msg.answer.call_args[0][0])

    def test_admin_unauthorized_access(self):
        """Verify non-admin users cannot access /admin command."""
        from bot.handlers.admin import admin_dashboard
        import config
        config.ADMIN_IDS = [8223004316]
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = 123999 # Non-admin
        mock_msg.answer = AsyncMock()
        
        run_async(admin_dashboard(mock_msg))
        self.assertIn("not authorized", mock_msg.answer.call_args[0][0])

    def test_quiz_evaluate_zero_score(self):
        """Verify quiz evaluation when all questions are answered incorrectly."""
        from bot.services import quiz_service
        from bot.database.repositories import quiz as quiz_repo
        
        user_id = 99125
        run_async(student_service.register_student(user_id, "ZeroStudent", "zero"))
        ls = run_async(learning_service.start_session(user_id, "School Subjects", "🧬 Biology"))
        quiz = run_async(quiz_service.start_quiz(user_id, ls.id, "School Subjects", "🧬 Biology"))
        
        for i in range(1, 6):
            q = run_async(asyncio.to_thread(
                quiz_repo.save_quiz_question,
                quiz.id, i, f"Q{i}", '{"A":"OptA","B":"OptB","C":"OptC","D":"OptD"}', "A", f"Exp {i}"
            ))
            run_async(asyncio.to_thread(quiz_repo.update_session_progress, quiz.id, i))
            is_correct, exp, updated_quiz = run_async(quiz_service.evaluate_answer(user_id, quiz, q, "D"))
            self.assertFalse(is_correct)
            
        self.assertEqual(updated_quiz.status, "COMPLETED")
        self.assertEqual(updated_quiz.correct_answers, 0)

    def test_test_history_empty(self):
        """Verify /test_history when student has taken no written tests."""
        from bot.handlers.actions import test_history_command
        user_id = 99126
        run_async(student_service.register_student(user_id, "NoTestsStudent", "no_tests"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(test_history_command(mock_msg))
        self.assertIn("haven't taken any written tests", mock_msg.answer.call_args[0][0])

    def test_materials_command_empty(self):
        """Verify /materials when student has no uploaded documents."""
        from bot.handlers.materials import show_materials_command
        user_id = 99127
        run_async(student_service.register_student(user_id, "NoMatsStudent", "no_mats"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        mock_state = AsyncMock()
        
        run_async(show_materials_command(mock_msg, mock_state))
        self.assertIn("haven't uploaded any study materials", mock_msg.answer.call_args[0][0])

    def test_help_command_display(self):
        """Verify /help outputs full user guide."""
        from bot.handlers.start import help_command
        user_id = 99128
        run_async(student_service.register_student(user_id, "HelpUser", "help_u"))
        
        mock_msg = AsyncMock()
        mock_msg.from_user.id = user_id
        mock_msg.answer = AsyncMock()
        
        run_async(help_command(mock_msg))
        reply = mock_msg.answer.call_args[0][0]
        self.assertIn("User Guide", reply)
        self.assertIn("/study", reply)

if __name__ == "__main__":
    unittest.main()


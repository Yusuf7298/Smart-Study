"""
Centralized Internationalization (i18n) Service for Smart Study Bot.
Supports English (en), Amharic (am), and Afaan Oromoo (om).
"""
from typing import Optional

# Language code normalization map
LANG_MAP = {
    "English": "en",
    "en": "en",
    "Amharic": "am",
    "am": "am",
    "አማርኛ": "am",
    "Afaan Oromo": "om",
    "Afaan Oromoo": "om",
    "om": "om",
    "Oromo": "om",
}

TRANSLATIONS = {
    # ------------------ English ------------------
    "en": {
        # Main Menu & Navigation
        "menu_title": "🎓 *Smart Study Bot — Main Dashboard*\n━━━━━━━━━━━━━━━━━━━━\nWelcome back, *{name}*!\n\n🎓 Grade Level: *{grade}*\n🌐 Language: *English*\n📚 Active Topic: *{topic}*\n\nSelect an option below to start:",
        "btn_study": "📚 Study",
        "btn_study_pdf": "📄 Study PDF",
        "btn_ai_tutor": "🤖 AI Tutor",
        "btn_quiz": "❓ Quiz",
        "btn_written_test": "📝 Written Test",
        "btn_short_notes": "📖 Short Notes",
        "btn_progress": "📊 My Progress",
        "btn_profile": "👤 My Profile",
        "btn_materials": "📎 My Materials",
        "btn_socials": "🌟 Follow Us",
        "btn_language": "🌐 Language",
        "btn_help": "❓ Help",
        "btn_cancel": "❌ Cancel",
        "btn_back": "🔙 Back",
        "btn_continue": "▶️ Continue",
        "btn_delete": "🗑️ Delete",
        "btn_study_mat": "📖 Study Material",
        "btn_upload_pdf": "📤 Upload PDF",
        "socials_title": "🌟 *Follow for More Islamic Reminders & Updates*\n━━━━━━━━━━━━━━━━━━━━\n\nTelegram: [Yusuf Moha](https://t.me/yusufcodes)\nLinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\nInstagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n━━━━━━━━━━━━━━━━━━━━\nMay Allah reward you 🤍",

        # Registration
        "reg_welcome": "📝 *Student Registration*\n━━━━━━━━━━━━━━━━━━━━\nWelcome to Smart Study Bot!\nLet's set up your profile.\n\nPlease enter your full name:",
        "reg_ask_grade": "🎓 *Select your grade level or academic status:*",
        "reg_ask_language": "🌐 *Select your preferred language:*",
        "reg_summary": "📋 *Registration Summary*\n━━━━━━━━━━━━━━━━━━━━\n👤 Name: *{name}*\n🎓 Grade: *{grade}*\n🌐 Language: *{language}*\n\nPlease confirm your registration:",
        "reg_btn_submit": "✅ Confirm & Submit",
        "reg_submitted": "⏳ *Registration Submitted!*\n━━━━━━━━━━━━━━━━━━━━\nYour profile has been submitted and is pending administrator approval.\nYou will receive a notification as soon as you are approved.",
        "reg_cancelled": "❌ Registration cancelled. Send /start to register again.",
        "reg_pending_wait": "⏳ *Registration Pending Approval*\n━━━━━━━━━━━━━━━━━━━━\nYour registration is currently under review by an administrator. You will be notified as soon as you are approved.",
        "reg_rejected": "❌ *Registration Rejected*\n━━━━━━━━━━━━━━━━━━━━\nYour registration was rejected by an administrator.",
        "reg_approved_notify": "🎉 *Congratulations! Your account has been approved!*\n━━━━━━━━━━━━━━━━━━━━\nYou now have full access to Smart Study Bot.\nUse the menu below or /study to begin learning!",

        # Study Mode
        "study_mode_title": "📚 *Study Mode*\n━━━━━━━━━━━━━━━━━━━━\nChoose a subject to start learning:",
        "study_choose_topic": "{emoji} *{subject}*\n━━━━━━━━━━━━━━━━━━━━\nChoose a topic to study:",
        "study_input_choice": "📚 *Study Material Input*\n━━━━━━━━━━━━━━━━━━━━\nYou selected: *{subject} → {topic}*\n\nHow would you like to provide your study context or requirements?",
        "study_btn_upload_file": "📎 Upload File / PDF + Description",
        "study_btn_text_desc": "✍️ Add Text Description / Topic",
        "study_ask_text": "✍️ *Text Description / Topic*\n━━━━━━━━━━━━━━━━━━━━\nPlease enter a description of the topic or specific questions you want to focus on:",
        "study_ask_file": "📎 *Upload File / PDF*\n━━━━━━━━━━━━━━━━━━━━\nPlease upload a PDF document or a photo of your study notes, with an optional description in the caption:",
        "study_intro_thinking": "🤔 Preparing your lesson introduction...",
        "study_stopped": "⏹️ *Study Session Stopped*\n━━━━━━━━━━━━━━━━━━━━\nReturning to general chat mode.\nUse /study to start a new topic.",
        "no_active_session": "📚 You don't have an active study session yet.\n\nUse /study or select 📚 Study from the menu to start learning.",
        "current_session_title": "📚 *Current Study Session*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *Grade:* {grade}\n{emoji} *Subject:* {subject}\n📌 *Topic:* {topic}\n🔄 *Stage:* {stage}\n📅 *Started:* {started}\n━━━━━━━━━━━━━━━━━━━━\n💡 /quiz to practice | /study to change topic | /cancel to stop",
        "current_session_quiz_active": "📚 *Current Study Session (Quiz Active)*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *Grade:* {grade}\n{emoji} *Subject:* {subject}\n📌 *Topic:* {topic}\n🔄 *Stage:* {stage}\n❓ *Quiz Progress:* Question {q_num}/{q_total} ({correct} correct)\n━━━━━━━━━━━━━━━━━━━━\n💡 Use /quiz to continue your quiz!",

        # PDF Study
        "pdf_welcome": "📄 *Study from PDF / Documents*\n━━━━━━━━━━━━━━━━━━━━\nPlease upload a PDF document (lecture notes, textbook chapter, assignment, or past paper).\n\nMax file size: 20 MB.",
        "pdf_processing": "⏳ Processing your PDF document and extracting key topics...",
        "pdf_ready": "📄 *PDF Study Material Ready!*\n━━━━━━━━━━━━━━━━━━━━\n📌 Title: *{title}*\n📑 Pages: *{pages}*\n\n📋 *Topics Detected:*\n{topics}\n\n📝 *Summary:*\n{summary}\n\nSelect an action below to learn from this document:",
        "pdf_btn_learn": "📖 Learn from PDF",
        "pdf_btn_ask": "💬 Ask Questions",
        "pdf_btn_quiz": "❓ Quiz from PDF",
        "pdf_btn_test": "📝 Practice Test",
        "pdf_btn_summary": "📑 Key Summary",
        "pdf_ask_prompt": "💬 *Ask PDF*\n━━━━━━━━━━━━━━━━━━━━\nSend any question about *{title}*, and I'll explain it directly from your uploaded material:",

        # Materials Library
        "materials_title": "📎 *My Study Materials Library*\n━━━━━━━━━━━━━━━━━━━━\nHere are your uploaded study documents:",
        "materials_empty": "📎 You haven't uploaded any study materials yet.\nUse /pdf or the button below to upload your first document.",
        "materials_deleted": "✅ Material deleted successfully.",
        "materials_activated": "✅ Set as active study material!",

        # Quiz
        "quiz_no_session": "📚 You don't have an active study session yet.\n\nUse /study or select 📚 Study from the menu to start learning.",
        "quiz_generating": "🤔 Generating your personalized quiz question...",
        "quiz_mode_title": "❓ *Quiz Mode Started*\n━━━━━━━━━━━━━━━━━━━━\n📚 Subject: *{subject} → {topic}*\n\nGet ready for 5 adaptive questions!",
        "quiz_active_prompt": "❓ *You have an active quiz session in progress!*\nQuestion {current} of {total}.",
        "quiz_question_header": "━━━━━━━━━━━━━━━━━━━━\n{emoji} *{topic} — Quiz*\n━━━━━━━━━━━━━━━━━━━━\n📝 Question *{num}* of *{total}*\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🇦  {opt_a}\n🇧  {opt_b}\n🇨  {opt_c}\n🇩  {opt_d}",
        "quiz_correct": "✅ *Correct!*",
        "quiz_incorrect": "❌ *Incorrect.*",
        "quiz_correct_reveal": "\n❗ *Correct Answer:* {correct_key}. {correct_text}\n",
        "quiz_complete_title": "━━━━━━━━━━━━━━━━━━━━\n🎉 *Quiz Completed!*\n━━━━━━━━━━━━━━━━━━━━\n{emoji} *{subject} → {topic}*\n\n📊 *Final Results:*\n   ✅ Correct: *{score}*\n   ❌ Incorrect: *{incorrect}*\n   💯 Score: *{score}/{total} — {pct}%*\n\n{medal} {verdict}\n━━━━━━━━━━━━━━━━━━━━\n💡 Continue with /study | Retake with /quiz",

        # Written Test
        "test_title": "━━━━━━━━━━━━━━━━━━━━\n📝 *Written Test Mode*\n━━━━━━━━━━━━━━━━━━━━\n📚 Subject: *{subject} → {topic}*\n\nAnswer the following 3 conceptual questions in ONE message:\n\n━━━━━━━━━━━━━━━━━━━━\n{questions}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 _Type all your answers in a single reply message and send._",
        "test_grading_title": "━━━━━━━━━━━━━━━━━━━━\n💯 *Test Evaluation Results*\n━━━━━━━━━━━━━━━━━━━━\n{result}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 Retake with /test or practice with /quiz",
        "test_evaluating": "💯 Evaluating your answers with AI, please wait a moment...",
        "test_history_title": "📝 *Previous Written Test Results*\n━━━━━━━━━━━━━━━━━━━━",

        # Short Notes
        "notes_title": "━━━━━━━━━━━━━━━━━━━━\n📖 *Short Notes Summary*\n━━━━━━━━━━━━━━━━━━━━\n📚 *{subject} → {topic}*\n\n{content}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 Use /quiz to test your knowledge or /test for written practice",
        "notes_generating": "📖 Preparing your short notes summary...",

        # Progress
        "progress_title": "📊 *My Learning Progress*\n━━━━━━━━━━━━━━━━━━━━\n👤 Student: *{name}*\n🎓 Grade: *{grade}*\n🌐 Language: *{language}*\n\n📚 *Academic Statistics:*\n• 📖 Lessons Started: *{lessons_count}*\n• ❓ Quizzes Taken: *{quizzes_count}*\n• 🎯 Quiz Success Rate: *{quiz_avg_pct}%* ({total_correct}/{total_questions} correct)\n• 📝 Written Tests: *{tests_count}* (Avg Score: *{test_avg_score}/10*)\n• 📄 PDFs Uploaded: *{pdf_count}*\n\n📌 *Active Session:* {active_topic}\n━━━━━━━━━━━━━━━━━━━━\nKeep up the great work! 💪",

        # Profile
        "profile_title": "👤 *Student Profile*\n━━━━━━━━━━━━━━━━━━━━\n👤 Name: *{name}*\n🆔 Telegram ID: `{telegram_id}`\n🎓 Grade Level: *{grade}*\n🌐 Preferred Language: *{language}*\n📅 Registered: *{registered_date}*\n📌 Current Topic: *{topic}*\n━━━━━━━━━━━━━━━━━━━━\nSelect an option below to update:",
        "profile_btn_change_grade": "🎓 Change Grade",
        "profile_btn_change_lang": "🌐 Change Language",

        # AI Tutor / Chat
        "tutor_thinking": "🤔 Thinking...",
        "ai_error": "⚠️ *Connection Error*\n━━━━━━━━━━━━━━━━━━━━\nI'm having trouble connecting to the AI right now.\nPlease try again in a moment.",

        # Help
        "help_title": "❓ *Smart Study Bot — User Guide*\n━━━━━━━━━━━━━━━━━━━━\nWelcome to your AI Personal Tutor! Here is how to use the bot:\n\n📚 *Study Mode (`/study`)*\nSelect any subject and topic. Provide your requirements via text or document to start learning step-by-step.\n\n📄 *PDF Study (`/pdf`)*\nUpload your lecture notes, textbook chapters, or PDFs. Ask questions directly grounded in the text, get summaries, or take quizzes!\n\n📎 *Materials Library (`/materials`)*\nManage your uploaded study documents.\n\n❓ *Quiz (`/quiz`)*\nTest your knowledge with 5 adaptive multiple-choice questions with instant explanations.\n\n📝 *Written Test (`/test`)*\nTake a 3-question conceptual exam and get letter grades with constructive feedback.\n\n📖 *Short Notes (`/short_note`)*\nGenerate high-yield summary notes and key formulas tailored to your grade.\n\n📊 *Progress (`/progress`)*\nView your comprehensive study analytics and quiz scores.\n\n⚙️ *Profile & Language (`/profile`)*\nSwitch your grade (Grade 5 to University) or language (English, Amharic, Afaan Oromoo) anytime.\n\n💡 *Helpful Commands:*\n`/menu` - Main Dashboard\n`/study` - Start studying\n`/pdf` - PDF study tool\n`/materials` - Uploaded documents\n`/quiz` - Start quiz\n`/test` - Take written test\n`/short_note` - Study notes\n`/current` - View active topic\n`/progress` - View stats\n`/profile` - Account settings\n`/cancel` - Cancel current action\n`/newchat` - Clear conversation history",

        # Admin
        "admin_only_error": "❌ You are not authorized to perform this action.",
        "admin_dashboard_title": "🛡️ *Admin Control Dashboard*\n━━━━━━━━━━━━━━━━━━━━\n👥 *Students Overview:*\n• Total Registered: *{total}*\n• ✅ Approved: *{approved}*\n• ⏳ Pending: *{pending}*\n• ❌ Rejected: *{rejected}*\n\n📊 *Activity Statistics:*\n• 📚 Study Sessions: *{sessions}*\n• ❓ Quizzes Taken: *{quizzes}*\n• 📝 Tests Evaluated: *{tests}*\n• 📄 PDFs Uploaded: *{pdfs}*\n━━━━━━━━━━━━━━━━━━━━\nUse buttons below to manage students or broadcast an announcement:",
        "admin_btn_pending": "⏳ Pending ({count})",
        "admin_btn_approved_list": "👥 Approved List",
        "admin_btn_rejected_list": "❌ Rejected List",
        "admin_btn_search": "🔍 Search Student",
        "admin_btn_broadcast": "📢 Broadcast Message",
        "admin_btn_refresh": "🔄 Refresh Dashboard",
        "admin_no_pending": "✅ No pending registrations at this time.",
    },

    # ------------------ Amharic (አማርኛ) ------------------
    "am": {
        # Main Menu & Navigation
        "menu_title": "🎓 *ስማርት የጥናት ቦት — ዋና ዳሽቦርድ*\n━━━━━━━━━━━━━━━━━━━━\nእንኳን ደህና መጡ፣ *{name}*!\n\n🎓 የክፍል ደረጃ: *{grade}*\n🌐 ቋንቋ: *አማርኛ*\n📚 ንቁ ርዕስ: *{topic}*\n\nለመጀመር ከታች ካሉት አማራጮች አንዱን ይምረጡ:",
        "btn_study": "📚 አጥና",
        "btn_study_pdf": "📄 የፒዲኤፍ ጥናት",
        "btn_ai_tutor": "🤖 AI አስተማሪ",
        "btn_quiz": "❓ ጥያቄና መልስ (Quiz)",
        "btn_written_test": "📝 የጽሁፍ ፈተና",
        "btn_short_notes": "📖 አጫጭር ማስታወሻዎች",
        "btn_progress": "📊 የኔ ውጤት/እድገት",
        "btn_profile": "👤 የኔ መገለጫ",
        "btn_materials": "📎 የእኔ ማቴሪያሎች",
        "btn_socials": "🌟 ተከተሉን (Socials)",
        "btn_language": "🌐 ቋንቋ ቀይር",
        "btn_help": "❓ እገዛ",
        "btn_cancel": "❌ ሰርዝ",
        "btn_back": "🔙 ተመለስ",
        "btn_continue": "▶️ ቀጥል",
        "btn_delete": "🗑️ ሰርዝ",
        "btn_study_mat": "📖 ይህን አጥና",
        "btn_upload_pdf": "📤 ፒዲኤፍ ጫን",
        "socials_title": "🌟 *ተጨማሪ ኢስላማዊ ማስታወሻዎችን ለማግኘት ይከተሉን*\n━━━━━━━━━━━━━━━━━━━━\n\nTelegram: [Yusuf Moha](https://t.me/yusufcodes)\nLinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\nInstagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n━━━━━━━━━━━━━━━━━━━━\nአላህ መልካም ምንዳ ይክፈላችሁ 🤍",

        # Registration
        "reg_welcome": "📝 *የተማሪ ምዝገባ*\n━━━━━━━━━━━━━━━━━━━━\nወደ ስማርት የጥናት ቦት እንኳን በደህና መጡ!\nመገለጫዎን እናዘጋጅ።\n\nእባክዎ ሙሉ ስምዎን ያስገቡ:",
        "reg_ask_grade": "🎓 *የትምህርት ደረጃዎን ወይም ክፍልዎን ይምረጡ:*",
        "reg_ask_language": "🌐 *የሚመርጡትን ቋንቋ ይምረጡ:*",
        "reg_summary": "📋 *የምዝገባ ማጠቃለያ*\n━━━━━━━━━━━━━━━━━━━━\n👤 ስም: *{name}*\n🎓 ክፍል: *{grade}*\n🌐 ቋንቋ: *{language}*\n\nእባክዎን ምዝገባዎን ያረጋግጡ:",
        "reg_btn_submit": "✅ አረጋግጥና አስገባ",
        "reg_submitted": "⏳ *ምዝገባዎ ገብቷል!*\n━━━━━━━━━━━━━━━━━━━━\nመረጃዎ ለአስተዳዳሪ ቀርቧል። ልክ እንደተፈቀደልዎ ማሳወቂያ ይደርስዎታል።",
        "reg_cancelled": "❌ ምዝገባው ተሰርዟል። እንደገና ለመመዝገብ /start ይላኩ።",
        "reg_pending_wait": "⏳ *ምዝገባዎ በመጠባበቅ ላይ ነው*\n━━━━━━━━━━━━━━━━━━━━\nምዝገባዎ በአስተዳዳሪ እየታየ ነው። ልክ እንደተፈቀደልዎ ማሳወቂያ ይደርስዎታል።",
        "reg_rejected": "❌ *ምዝገባዎ ውድቅ ተደርጓል*\n━━━━━━━━━━━━━━━━━━━━\nምዝገባዎ በአስተዳዳሪ ተቀባይነት አላገኘም።",
        "reg_approved_notify": "🎉 *እንኳን ደስ አለዎት! ምዝገባዎ ተፈቅዷል!*\n━━━━━━━━━━━━━━━━━━━━\nአሁን የቦቱን አገልግሎት ሙሉ በሙሉ መጠቀም ይችላሉ።\nለመማር /study ይጠቀሙ ወይም ሜኑውን ይምረጡ!",

        # Study Mode
        "study_mode_title": "📚 *የጥናት ሁነታ*\n━━━━━━━━━━━━━━━━━━━━\nለመማር የሚፈልጉትን የትምህርት ዓይነት ይምረጡ:",
        "study_choose_topic": "{emoji} *{subject}*\n━━━━━━━━━━━━━━━━━━━━\nየጥናት ርዕስ ይምረጡ:",
        "study_input_choice": "📚 *የጥናት ማቴሪያል ማስገቢያ*\n━━━━━━━━━━━━━━━━━━━━\nየመረጡት: *{subject} → {topic}*\n\nየጥናት ፍላጎትዎን ወይም ይዘትዎን እንዴት ማቅረብ ይፈልጋሉ?",
        "study_btn_upload_file": "📎 ፋይል / ፒዲኤፍ ጫን + ማብራሪያ",
        "study_btn_text_desc": "✍️ በጽሁፍ ማብራሪያ / ጥያቄ አስገባ",
        "study_ask_text": "✍️ *የጽሁፍ ማብራሪያ*\n━━━━━━━━━━━━━━━━━━━━\nማተኮር የሚፈልጉትን የርዕስ ማብራሪያ ወይም የተወሰኑ ጥያቄዎችን ይጻፉ:",
        "study_ask_file": "📎 *ፋይል / ፒዲኤፍ መጫኛ*\n━━━━━━━━━━━━━━━━━━━━\nእባክዎን የጥናት ፒዲኤፍ ወይም የማስታወሻ ፎቶ ይላኩ:",
        "study_intro_thinking": "🤔 የትምህርት መግቢያ በማዘጋጀት ላይ...",
        "study_stopped": "⏹️ *የጥናት ክፍለ ጊዜ ቆሟል*\n━━━━━━━━━━━━━━━━━━━━\nወደ መደበኛ ውይይት ተመልሰዋል።\nአዲስ ለማጥናት /study ይጠቀሙ።",
        "no_active_session": "📚 በአሁኑ ጊዜ ምንም ንቁ የጥናት ክፍለ ጊዜ የለዎትም።\n\nለመማር /study ይጠቀሙ ወይም ከሜኑ ውስጥ 📚 አጥና የሚለውን ይምረጡ።",
        "current_session_title": "📚 *የአሁኑ የጥናት ክፍለ ጊዜ*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *ክፍል:* {grade}\n{emoji} *ትምህርት:* {subject}\n📌 *ርዕስ:* {topic}\n🔄 *ደረጃ:* {stage}\n📅 *የተጀመረበት:* {started}\n━━━━━━━━━━━━━━━━━━━━\n💡 /quiz ለመለማመድ | /study ርዕስ ለመቀየር | /cancel ለማቆም",
        "current_session_quiz_active": "📚 *የአሁኑ የጥናት ክፍለ ጊዜ (ፈተና ንቁ ነው)*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *ክፍል:* {grade}\n{emoji} *ትምህርት:* {subject}\n📌 *ርዕስ:* {topic}\n🔄 *ደረጃ:* {stage}\n❓ *የፈተና ሂደት:* ጥያቄ {q_num}/{q_total}\n━━━━━━━━━━━━━━━━━━━━\n💡 ፈተናውን ለመቀጠል /quiz ይጠቀሙ!",

        # PDF Study
        "pdf_welcome": "📄 *ከፒዲኤፍ / ሰነድ ማጥናት*\n━━━━━━━━━━━━━━━━━━━━\nእባክዎ የፒዲኤፍ ሰነድዎን ይጫኑ (የማስታወሻ ደብተር፣ መጽሐፍ ወይም ፈተናዎች)።\n\nከፍተኛው የፋይል መጠን: 20 MB።",
        "pdf_processing": "⏳ ፒዲኤፉን በማንበብ እና ዋና ዋና ርዕሶችን በመለየት ላይ...",
        "pdf_ready": "📄 *የፒዲኤፍ ማቴሪያል ዝግጁ ነው!*\n━━━━━━━━━━━━━━━━━━━━\n📌 ርዕስ: *{title}*\n📑 ገጾች: *{pages}*\n\n📋 *የተገኙ ዋና ዋና ርዕሶች:*\n{topics}\n\n📝 *ማጠቃለያ:*\n{summary}\n\nከዚህ ሰነድ ለመማር ከታች አንዱን ይምረጡ:",
        "pdf_btn_learn": "📖 ከፒዲኤፉ ተማር",
        "pdf_btn_ask": "💬 ከፒዲኤፉ ጠይቅ",
        "pdf_btn_quiz": "❓ ከፒዲኤፉ ፈተና ውሰድ",
        "pdf_btn_test": "📝 የጽሁፍ ፈተና ውሰድ",
        "pdf_btn_summary": "📑 ዋና ማጠቃለያ",
        "pdf_ask_prompt": "💬 *ከፒዲኤፍ ጠይቅ*\n━━━━━━━━━━━━━━━━━━━━\nስለ *{title}* ማንኛውንም ጥያቄ ይላኩ፤ ከሰነዱ ላይ በቀጥታ አስረዳዎታለሁ:",

        # Materials Library
        "materials_title": "📎 *የእኔ የጥናት ማቴሪያሎች ቤተ-መጽሐፍት*\n━━━━━━━━━━━━━━━━━━━━\nየጫኗቸው ሰነዶች ዝርዝር:",
        "materials_empty": "📎 እስካሁን ምንም የጥናት ማቴሪያል አልጫኑም።\nለመጀመሪያ ጊዜ ሰነድ ለመጫን /pdf ወይም ከታች ያለውን ቁልፍ ይጠቀሙ።",
        "materials_deleted": "✅ ማቴሪያሉ በተሳካ ሁኔታ ተሰርዟል።",
        "materials_activated": "✅ እንደ ንቁ የጥናት ማቴሪያል ተመርጧል!",

        # Quiz
        "quiz_no_session": "📚 በአሁኑ ጊዜ ምንም ንቁ የጥናት ክፍለ ጊዜ የለዎትም።\n\nለመማር /study ይጠቀሙ ወይም ከሜኑ ውስጥ 📚 አጥና የሚለውን ይምረጡ።",
        "quiz_generating": "🤔 ለርስዎ የተዘጋጀ የፈተና ጥያቄ በማዘጋጀት ላይ...",
        "quiz_mode_title": "❓ *የፈተና ሁነታ ተጀምሯል*\n━━━━━━━━━━━━━━━━━━━━\n📚 ትምህርት: *{subject} → {topic}*\n\nለ 5 ጥያቄዎች ይዘጋጁ!",
        "quiz_active_prompt": "❓ *በሂደት ላይ ያለ ንቁ ፈተና አለዎት!*\nጥያቄ {current} ከ {total}።",
        "quiz_question_header": "━━━━━━━━━━━━━━━━━━━━\n{emoji} *{topic} — ጥያቄ*\n━━━━━━━━━━━━━━━━━━━━\n📝 ጥያቄ *{num}* ከ *{total}*\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🇦  {opt_a}\n🇧  {opt_b}\n🇨  {opt_c}\n🇩  {opt_d}",
        "quiz_correct": "✅ *ትክክል ነው!*",
        "quiz_incorrect": "❌ *ትክክል አይደለም።*",
        "quiz_correct_reveal": "\n❗ *ትክክለኛው መልስ:* {correct_key}. {correct_text}\n",
        "quiz_complete_title": "━━━━━━━━━━━━━━━━━━━━\n🎉 *ፈተናው ተጠናቋል!*\n━━━━━━━━━━━━━━━━━━━━\n{emoji} *{subject} → {topic}*\n\n📊 *ውጤት:*\n   ✅ ትክክል: *{score}*\n   ❌ ስህተት: *{incorrect}*\n   💯 ውጤት: *{score}/{total} — {pct}%*\n\n{medal} {verdict}\n━━━━━━━━━━━━━━━━━━━━\n💡 በ /study ይቀጥሉ | በ /quiz እንደገና ይሞክሩ",

        # Written Test
        "test_title": "━━━━━━━━━━━━━━━━━━━━\n📝 *የጽሁፍ ፈተና ሁነታ*\n━━━━━━━━━━━━━━━━━━━━\n📚 ትምህርት: *{subject} → {topic}*\n\nየሚከተሉትን 3 የፅንሰ-ሀሳብ ጥያቄዎች በአንድ መልእክት ይመልሱ:\n\n━━━━━━━━━━━━━━━━━━━━\n{questions}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 _ሁሉንም መልሶች በአንድ መልእክት ጽፈው ይላኩ_",
        "test_grading_title": "━━━━━━━━━━━━━━━━━━━━\n💯 *የፈተና ውጤት እና ግምገማ*\n━━━━━━━━━━━━━━━━━━━━\n{result}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 በ /test እንደገና ይሞክሩ ወይም በ /quiz ይለማመዱ",
        "test_evaluating": "💯 መልስዎን በ AI እየገመገምን ነው፣ እባክዎ ጥቂት ይጠብቁ...",
        "test_history_title": "📝 *ያለፉት የጽሁፍ ፈተና ውጤቶች*\n━━━━━━━━━━━━━━━━━━━━",

        # Short Notes
        "notes_title": "━━━━━━━━━━━━━━━━━━━━\n📖 *አጫጭር ማስታወሻዎች*\n━━━━━━━━━━━━━━━━━━━━\n📚 *{subject} → {topic}*\n\n{content}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 እውቀትዎን በ /quiz ይፈትሹ",
        "notes_generating": "📖 አጫጭር ማስታወሻዎችን በማዘጋጀት ላይ...",

        # Progress
        "progress_title": "📊 *የትምህርት እድገቴ*\n━━━━━━━━━━━━━━━━━━━━\n👤 ተማሪ: *{name}*\n🎓 ክፍል: *{grade}*\n🌐 ቋንቋ: *አማርኛ*\n\n📚 *የትምህርት ስታቲስቲክስ:*\n• 📖 የተጀመሩ ትምህርቶች: *{lessons_count}*\n• ❓ የተወሰዱ ፈተናዎች (Quizzes): *{quizzes_count}*\n• 🎯 የፈተና አማካይ: *{quiz_avg_pct}%* ({total_correct}/{total_questions} ትክክል)\n• 📝 የጽሁፍ ፈተናዎች: *{tests_count}* (አማካይ: *{test_avg_score}/10*)\n• 📄 የተጫኑ ፒዲኤፎች: *{pdf_count}*\n\n📌 *የአሁኑ ንቁ ርዕስ:* {active_topic}\n━━━━━━━━━━━━━━━━━━━━\nበርቱ፣ ጥሩ ውጤት እያስመዘገቡ ነው! 💪",

        # Profile
        "profile_title": "👤 *የተማሪ መገለጫ*\n━━━━━━━━━━━━━━━━━━━━\n👤 ስም: *{name}*\n🆔 Telegram ID: `{telegram_id}`\n🎓 የክፍል ደረጃ: *{grade}*\n🌐 የተመረጠ ቋንቋ: *{language}*\n📅 የተመዘገቡበት ቀን: *{registered_date}*\n📌 የአሁኑ ርዕስ: *{topic}*\n━━━━━━━━━━━━━━━━━━━━\nለመቀየር ከታች ካሉት አንዱን ይምረጡ:",
        "profile_btn_change_grade": "🎓 ክፍል ቀይር",
        "profile_btn_change_lang": "🌐 ቋንቋ ቀይር",

        # AI Tutor / Chat
        "tutor_thinking": "🤔 በማሰብ ላይ...",
        "ai_error": "⚠️ *የግንኙነት ስህተት*\n━━━━━━━━━━━━━━━━━━━━\nበአሁኑ ጊዜ ከ AI ጋር መገናኘት አልተቻለም። እባክዎን ከጥቂት ደቂቃዎች በኋላ እንደገና ይሞክሩ።",

        # Help
        "help_title": "❓ *ስማርት የጥናት ቦት — መመሪያ*\n━━━━━━━━━━━━━━━━━━━━\nእንኳን ወደ ግል የ AI አስተማሪዎ በደህና መጡ!\n\n📚 *የጥናት ሁነታ (`/study`)*\nትምህርት እና ርዕስ መርጠው ደረጃ በደረጃ ይማሩ።\n\n📄 *የፒዲኤፍ ጥናት (`/pdf`)*\nማስታወሻዎን ወይም ፒዲኤፍ ልከው ከሰነዱ ላይ በቀጥታ ይጠይቁ እና ይማሩ።\n\n📎 *ማቴሪያሎች (`/materials`)*\nየጫኗቸውን ሰነዶች ይመልከቱ።\n\n❓ *ጥያቄና መልስ (`/quiz`)*\nበ 5 ባለብዙ ምርጫ ጥያቄዎች እውቀትዎን ይፈትሹ።\n\n📝 *የጽሁፍ ፈተና (`/test`)*\nየፅንሰ-ሀሳብ ጥያቄዎችን ይመልሱና ውጤት ያግኙ።\n\n📖 *አጫጭር ማስታወሻዎች (`/short_note`)*\nለፈተና የሚረዱ አጫጭር ማጠቃለያዎችን ያግኙ።\n\n📊 *የኔ ውጤት (`/progress`)*\nየትምህርት እድገትዎን ይመልከቱ።",

        # Admin
        "admin_only_error": "❌ ይህን እርምጃ ለማከናወን ፈቃድ የለዎትም።",
        "admin_dashboard_title": "🛡️ *የአስተዳዳሪ ዳሽቦርድ*\n━━━━━━━━━━━━━━━━━━━━\n👥 *የተማሪዎች አጠቃላይ ሁኔታ:*\n• ጠቅላላ የተመዘገቡ: *{total}*\n• ✅ የተፈቀደላቸው: *{approved}*\n• ⏳ በመጠባበቅ ላይ: *{pending}*\n• ❌ ውድቅ የተደረጉ: *{rejected}*\n\n📊 *የትምህርት እንቅስቃሴ:*\n• 📚 የጥናት ክፍለ ጊዜዎች: *{sessions}*\n• ❓ የተወሰዱ ፈተናዎች: *{quizzes}*\n• 📝 የጽሁፍ ፈተናዎች: *{tests}*\n• 📄 የተላኩ ፒዲኤፎች: *{pdfs}*\n━━━━━━━━━━━━━━━━━━━━",
        "admin_btn_pending": "⏳ በመጠባበቅ ላይ ያሉ ({count})",
        "admin_btn_approved_list": "👥 የተፈቀደላቸው ዝርዝር",
        "admin_btn_rejected_list": "❌ ውድቅ የተደረጉ ዝርዝር",
        "admin_btn_search": "🔍 ተማሪ ፈልግ",
        "admin_btn_broadcast": "📢 መልእክት ለሁሉም አስተላልፍ",
        "admin_btn_refresh": "🔄 አድስ",
        "admin_no_pending": "✅ በአሁኑ ጊዜ በመጠባበቅ ላይ ያለ ምዝገባ የለም።",
    },

    # ------------------ Afaan Oromoo ------------------
    "om": {
        # Main Menu & Navigation
        "menu_title": "🎓 *Smart Study Bot — Fuula Guddaa*\n━━━━━━━━━━━━━━━━━━━━\nBaga nagaan dhufte, *{name}*!\n\n🎓 Sadarkaa Kutaa: *{grade}*\n🌐 Afaan: *Afaan Oromoo*\n📚 Mata Duree Ammaa: *{topic}*\n\nJalqabuuf filannoowwan armaan gadii keessaa tokko filadhu:",
        "btn_study": "📚 Qo'adhu",
        "btn_study_pdf": "📄 Qo'annoo PDF",
        "btn_ai_tutor": "🤖 Barsiisaa AI",
        "btn_quiz": "❓ Gaaffilee (Quiz)",
        "btn_written_test": "📝 Qormaata Barreeffamaa",
        "btn_short_notes": "📖 Yaadannoo Gabaabaa",
        "btn_progress": "📊 Guddina Koo",
        "btn_profile": "👤 Piroofayilii Koo",
        "btn_materials": "📎 Meeshaalee Koo",
        "btn_socials": "🌟 Nu Hordofaa (Socials)",
        "btn_language": "🌐 Afaan Jijjiiri",
        "btn_help": "❓ Gargaarsa",
        "btn_cancel": "❌ Dhiisi",
        "btn_back": "🔙 Deebi'i",
        "btn_continue": "▶️ Itti Fufi",
        "btn_delete": "🗑️ Haqi",
        "btn_study_mat": "📖 Sanada Kana Qo'adhu",
        "btn_upload_pdf": "📤 PDF Fe'i",
        "socials_title": "🌟 *Yaadachiisa Islaamaa Dabalataaf Nu Hordofaa*\n━━━━━━━━━━━━━━━━━━━━\n\nTelegram: [Yusuf Moha](https://t.me/yusufcodes)\nLinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\nInstagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n━━━━━━━━━━━━━━━━━━━━\nRabbiin jazaaykeessan isiniif haa kaffalu 🤍",

        # Registration
        "reg_welcome": "📝 *Galmee Barataa*\n━━━━━━━━━━━━━━━━━━━━\nBaga nagaan gara Smart Study Bot dhuftan!\nPiroofayilii keessan haa qopheessinu.\n\nMaqaa keessan guutuu galchaa:",
        "reg_ask_grade": "🎓 *Sadarkaa kutaa ykn barnoota keessanii filadhaa:*",
        "reg_ask_language": "🌐 *Afaan ittiin barachuu barbaaddan filadhaa:*",
        "reg_summary": "📋 *Cuunfaa Galmee*\n━━━━━━━━━━━━━━━━━━━━\n👤 Maqaa: *{name}*\n🎓 Kutaa: *{grade}*\n🌐 Afaan: *{language}*\n\nGalmee keessan mirkaneessaa:",
        "reg_btn_submit": "✅ Mirkaneessi & Ergi",
        "reg_submitted": "⏳ *Galmeen Ergameera!*\n━━━━━━━━━━━━━━━━━━━━\nOdeeffannoon keessan bulchaaf ergamee eegaa jira. Yeroo eeyyamamu beeksisni isiniif dhufa.",
        "reg_cancelled": "❌ Galmeen haqameera. Irra deebiin galmaa'uuf /start ergaa.",
        "reg_pending_wait": "⏳ *Galmeen Keessan Eegaa Jira*\n━━━━━━━━━━━━━━━━━━━━\nGalmeen keessan bulchaan ilaalamaa jira. Yeroo eeyyamamu beeksisni isiniif dhufa.",
        "reg_rejected": "❌ *Galmeen Keessan Kufaa Ta'eera*\n━━━━━━━━━━━━━━━━━━━━\nGalmeen keessan bulchaan fudhatama hin arganne.",
        "reg_approved_notify": "🎉 *Baga Gammaddan! Galmeen keessan eeyyamameera!*\n━━━━━━━━━━━━━━━━━━━━\nAmma tajaajila botii guutummaatti fayyadamuu dandeessu.\nQo'annoo jalqabuuf /study fayyadamaa ykn meenuu filadhaa!",

        # Study Mode
        "study_mode_title": "📚 *Haala Qo'annoo*\n━━━━━━━━━━━━━━━━━━━━\nGosa barnootaa barachuu barbaaddan filadhaa:",
        "study_choose_topic": "{emoji} *{subject}*\n━━━━━━━━━━━━━━━━━━━━\nMata duree qo'annoo filadhaa:",
        "study_input_choice": "📚 *Galtee Meeshaa Qo'annoo*\n━━━━━━━━━━━━━━━━━━━━\nKan filattan: *{subject} → {topic}*\n\nFedhii ykn qabiyyee keessan akkamitti dhiyeessuu barbaaddu?",
        "study_btn_upload_file": "📎 Faayilii / PDF Fe'i + Ibsa",
        "study_btn_text_desc": "✍️ Ibsa Barreeffamaa / Gaaffii Galchi",
        "study_ask_text": "✍️ *Ibsa Barreeffamaa*\n━━━━━━━━━━━━━━━━━━━━\nMata duree ykn gaaffilee irratti xiyyeeffachuu barbaaddan barreessaa:",
        "study_ask_file": "📎 *Faayilii / PDF Fe'i*\n━━━━━━━━━━━━━━━━━━━━\nSanada PDF ykn suuraa yaadannoo keessanii ergaa:",
        "study_intro_thinking": "🤔 Seensa barnootaa qopheessaa jira...",
        "study_stopped": "⏹️ *Qo'annoon Dhaabbateera*\n━━━━━━━━━━━━━━━━━━━━\nGara marii waliigalaatti deebitanitu.\nMata duree haaraa qo'achuuf /study fayyadamaa.",
        "no_active_session": "📚 Hanga ammaatti qo'annoo qophaa'e hin qabdan.\n\nBarnoota jalqabuuf /study fayyadamaa ykn meenuu irraa 📚 Qo'adhu filadhaa.",
        "current_session_title": "📚 *Qo'annoo Ammaa*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *Kutaa:* {grade}\n{emoji} *Gosa Barnootaa:* {subject}\n📌 *Mata Duree:* {topic}\n🔄 *Sadarkaa:* {stage}\n📅 *Jalqabame:* {started}\n━━━━━━━━━━━━━━━━━━━━\n💡 /quiz yaaluuf | /study jijjiiruuf | /cancel dhaabuuf",
        "current_session_quiz_active": "📚 *Qo'annoo Ammaa (Qormaanni Hojjechaa Jira)*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *Kutaa:* {grade}\n{emoji} *Gosa Barnootaa:* {subject}\n📌 *Mata Duree:* {topic}\n🔄 *Sadarkaa:* {stage}\n❓ *Adeemsa Qormaataa:* Gaaffii {q_num}/{q_total}\n━━━━━━━━━━━━━━━━━━━━\n💡 Qormaata itti fufuuf /quiz fayyadamaa!",

        # PDF Study
        "pdf_welcome": "📄 *PDF / Sanada Irraa Barachuu*\n━━━━━━━━━━━━━━━━━━━━\nSanada PDF (yaadannoo, boqonnaa kitaabaa, ykn qormaata) fe'aa.\n\nHangamtaan faayilii guddaan: 20 MB.",
        "pdf_processing": "⏳ PDF dubbisuu fi mata dureewwan ijoo adda baasaa jira...",
        "pdf_ready": "📄 *Sanadni PDF Qophaa'eera!*\n━━━━━━━━━━━━━━━━━━━━\n📌 Mata Duree: *{title}*\n📑 Fuulota: *{pages}*\n\n📋 *Mata Dureewwan Ijoo:*\n{topics}\n\n📝 *Cuunfaa:*\n{summary}\n\nSanada kana irraa barachuuf armaan gadii filadhaa:",
        "pdf_btn_learn": "📖 PDF Irraa Baraadhu",
        "pdf_btn_ask": "💬 PDF Irraa Gaafadhu",
        "pdf_btn_quiz": "❓ PDF Irraa Qormaata Fudhadhu",
        "pdf_btn_test": "📝 Qormaata Barreeffamaa",
        "pdf_btn_summary": "📑 Cuunfaa Ijoo",
        "pdf_ask_prompt": "💬 *PDF Irraa Gaafadhu*\n━━━━━━━━━━━━━━━━━━━━\nWaa'ee *{title}* gaaffii qabdan kamiyyuu ergaa; sanada keessan irraa kallattiin isiniif ibsa:",

        # Materials Library
        "materials_title": "📎 *Kuusaa Meeshaalee Barnootaa Koo*\n━━━━━━━━━━━━━━━━━━━━\nSanadoota barnootaa featan:",
        "materials_empty": "📎 Hanga ammaatti sanada barnootaa hin feene.\nSanada keessan jalqabaa fe'uuf /pdf ykn qabduu armaan gadii fayyadamaa.",
        "materials_deleted": "✅ Sanadni milkaa'inaan haqameera.",
        "materials_activated": "✅ Sanada qo'annoo ammaa ta'ee filatameera!",

        # Quiz
        "quiz_no_session": "📚 Hanga ammaatti qo'annoo qophaa'e hin qabdan.\n\nBarnoota jalqabuuf /study fayyadamaa ykn meenuu irraa 📚 Qo'adhu filadhaa.",
        "quiz_generating": "🤔 Gaaffii qormaataa isiniif qopheessaa jira...",
        "quiz_mode_title": "❓ *Haalli Qormaataa Jalqabeera*\n━━━━━━━━━━━━━━━━━━━━\n📚 Gosa Barnootaa: *{subject} → {topic}*\n\nGaaffilee 5f qophaa'aa!",
        "quiz_active_prompt": "❓ *Qormaanni hojjechaa jiru jira!*\nGaaffii {current} / {total}።",
        "quiz_question_header": "━━━━━━━━━━━━━━━━━━━━\n{emoji} *{topic} — Gaaffii*\n━━━━━━━━━━━━━━━━━━━━\n📝 Gaaffii *{num}* / *{total}*\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🇦  {opt_a}\n🇧  {opt_b}\n🇨  {opt_c}\n🇩  {opt_d}",
        "quiz_correct": "✅ *Sirrii dha!*",
        "quiz_incorrect": "❌ *Sirrii miti.*",
        "quiz_correct_reveal": "\n❗ *Deebii Sirrii:* {correct_key}. {correct_text}\n",
        "quiz_complete_title": "━━━━━━━━━━━━━━━━━━━━\n🎉 *Qormaanni Xumurameera!*\n━━━━━━━━━━━━━━━━━━━━\n{emoji} *{subject} → {topic}*\n\n📊 *Bu'aa:*\n   ✅ Sirrii: *{score}*\n   ❌ Dogoggora: *{incorrect}*\n   💯 Qabxii: *{score}/{total} — {pct}%*\n\n{medal} {verdict}\n━━━━━━━━━━━━━━━━━━━━\n💡 /study'n itti fufaa | /quiz'n irra deebiin yaalaa",

        # Written Test
        "test_title": "━━━━━━━━━━━━━━━━━━━━\n📝 *Qormaata Barreeffamaa*\n━━━━━━━━━━━━━━━━━━━━\n📚 Gosa Barnootaa: *{subject} → {topic}*\n\nGaaffilee 3 armaan gadii ergaa tokkoon deebisaa:\n\n━━━━━━━━━━━━━━━━━━━━\n{questions}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 _Deebii keessan hunda ergaa tokkoon barreessaa ergaa_",
        "test_grading_title": "━━━━━━━━━━━━━━━━━━━━\n💯 *Bu'aa fi Qorannoo Qormaataa*\n━━━━━━━━━━━━━━━━━━━━\n{result}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 /test'n irra deebiin yaalaa ykn /quiz fayyadamaa",
        "test_evaluating": "💯 Deebii keessan gamaaggamaa jira, mee xiqqoo eegaa...",
        "test_history_title": "📝 *Bu'aawwan Qormaata Barreeffamaa Darban*\n━━━━━━━━━━━━━━━━━━━━",

        # Short Notes
        "notes_title": "━━━━━━━━━━━━━━━━━━━━\n📖 *Cuunfaa Yaadannoo Gabaabaa*\n━━━━━━━━━━━━━━━━━━━━\n📚 *{subject} → {topic}*\n\n{content}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 /quiz'n beekumsa keessan mirkaneessaa",
        "notes_generating": "📖 Cuunfaa yaadannoo qopheessaa jira...",

        # Progress
        "progress_title": "📊 *Guddina Barnoota Koo*\n━━━━━━━━━━━━━━━━━━━━\n👤 Barataa: *{name}*\n🎓 Kutaa: *{grade}*\n🌐 Afaan: *Afaan Oromoo*\n\n📚 *Istaatistiksii Barnootaa:*\n• 📖 Barnoota Jalqabame: *{lessons_count}*\n• ❓ Qormaata Fudhatame: *{quizzes_count}*\n• 🎯 Giddu-galeessa Qabxii: *{quiz_avg_pct}%* ({total_correct}/{total_questions} sirrii)\n• 📝 Qormaata Barreeffamaa: *{tests_count}* (Giddu-galeessa: *{test_avg_score}/10*)\n• 📄 PDF Ergame: *{pdf_count}*\n\n📌 *Mata Duree Ammaa:* {active_topic}\n━━━━━━━━━━━━━━━━━━━━\nHojii gaariidha, itti fufaa! 💪",

        # Profile
        "profile_title": "👤 *Piroofayilii Barataa*\n━━━━━━━━━━━━━━━━━━━━\n👤 Maqaa: *{name}*\n🆔 Telegram ID: `{telegram_id}`\n🎓 Sadarkaa Kutaa: *{grade}*\n🌐 Afaan Filatame: *{language}*\n📅 Guyyaa Galmee: *{registered_date}*\n📌 Mata Duree Ammaa: *{topic}*\n━━━━━━━━━━━━━━━━━━━━\nJijjiiruuf armaan gadii filadhaa:",
        "profile_btn_change_grade": "🎓 Kutaa Jijjiiri",
        "profile_btn_change_lang": "🌐 Afaan Jijjiiri",

        # AI Tutor / Chat
        "tutor_thinking": "🤔 Yaadaa jira...",
        "ai_error": "⚠️ *Dogoggora Wal-qunnamtii*\n━━━━━━━━━━━━━━━━━━━━\nAmma AI wajjin wal-qunnamuu hin dandeenye. Mee daqiiqaa muraasa booda irra deebiin yaalaa.",

        # Help
        "help_title": "❓ *Smart Study Bot — Qajeelfama Fayyadamaa*\n━━━━━━━━━━━━━━━━━━━━\nBaga nagaan gara Barsiisaa AI dhuftan!\n\n📚 *Qo'annoo (`/study`)*\nGosa barnootaa fi mata duree filachuun sadarkaa sadarkaan baraadhaa.\n\n📄 *Qo'annoo PDF (`/pdf`)*\nSanada PDF ykn yaadannoo erguun kallattiin dokumantii keessan irraa gaafadhaa fi baraadhaa.\n\n📎 *Kuusaa Meeshaalee (`/materials`)*\nSanadoota keessan ilaalaa fi to'adhaa.\n\n❓ *Gaaffilee (`/quiz`)*\nGaaffilee 5 filannoo qabaniin beekumsa keessan qoraa.\n\n📝 *Qormaata Barreeffamaa (`/test`)*\nGaaffilee yaadaa deebisuun qabxii fi yaada gamaaggamaa argadhaa.\n\n📖 *Yaadannoo Gabaabaa (`/short_note`)*\nCuunfaa qabxiiwwan ijoo argadhaa.\n\n📊 *Guddina Koo (`/progress`)*\nIstaatistiksii barnoota keessanii hordofaa.",

        # Admin
        "admin_only_error": "❌ Gocha kana raawwachuuf heeyyama hin qabdan.",
        "admin_dashboard_title": "🛡️ *Gabatee To'annoo Bulchaa*\n━━━━━━━━━━━━━━━━━━━━\n👥 *Waliigala Barattootaa:*\n• Waliigala Galmaa'an: *{total}*\n• ✅ Eeyyamameef: *{approved}*\n• ⏳ Eegaa Jiran: *{pending}*\n• ❌ Kufaa Ta'an: *{rejected}*\n\n📊 *Sochii Barnootaa:*\n• 📚 Qo'annoo: *{sessions}*\n• ❓ Gaaffilee (Quizzes): *{quizzes}*\n• 📝 Qormaata: *{tests}*\n• 📄 PDF'wwan: *{pdfs}*\n━━━━━━━━━━━━━━━━━━━━",
        "admin_btn_pending": "⏳ Kan Eegaa Jiran ({count})",
        "admin_btn_approved_list": "👥 Barattoota Eeyyamameef",
        "admin_btn_rejected_list": "❌ Kufaa Kan Ta'an",
        "admin_btn_search": "🔍 Barataa Barbaadi",
        "admin_btn_broadcast": "📢 Ergaa Waliigalaa",
        "admin_btn_refresh": "🔄 Haaromsi",
        "admin_no_pending": "✅ Ammaaf galmeen eegaa jiru hin jiru.",
    }
}

def normalize_lang(language_str: Optional[str]) -> str:
    """Normalizes any language string to 'en', 'am', or 'om'."""
    if not language_str:
        return "en"
    return LANG_MAP.get(language_str.strip(), "en")

def t(key: str, lang: Optional[str] = "English", **kwargs) -> str:
    """
    Returns localized string for the given key and language.
    Falls back to English if key is missing in the target language.
    """
    lang_code = normalize_lang(lang)
    lang_dict = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
    
    template = lang_dict.get(key) or TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template

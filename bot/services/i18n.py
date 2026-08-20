"""
Centralized Internationalization (i18n) Service for Ethio Smart Study Bot.
Provides clean templates in English, Amharic (አማርኛ), and Afaan Oromoo.
"""

from typing import Dict, Any, Optional

# Supported language map
LANGUAGE_MAP = {
    "English": "en",
    "en": "en",
    "Amharic": "am",
    "አማርኛ": "am",
    "am": "am",
    "Afaan Oromoo": "om",
    "Afaan Oromo": "om",
    "om": "om",
    "Oromo": "om",
}

def normalize_lang(lang: Optional[str]) -> str:
    """Normalizes language name or code to standard 'en', 'am', or 'om'."""
    if not lang:
        return "en"
    if lang in LANGUAGE_MAP:
        return LANGUAGE_MAP[lang]
    clean = str(lang).strip().lower()
    if "amharic" in clean or "አማርኛ" in clean or clean == "am":
        return "am"
    if "oromo" in clean or "afaan" in clean or clean == "om":
        return "om"
    return "en"

SUBJECT_TRANSLATIONS = {
    "English": {
        "en": "English",
        "am": "እንግሊዝኛ (English)",
        "om": "Afaan Ingilizi (English)",
    },
    "Mathematics": {
        "en": "Mathematics",
        "am": "ሒሳብ (Mathematics)",
        "om": "Hisaaba (Mathematics)",
    },
    "Mathematics (Natural Science)": {
        "en": "Mathematics (Nat Sci)",
        "am": "ሒሳብ - ተፈጥሮ ሳይንስ",
        "om": "Hisaaba - Saayinsii Uamaa",
    },
    "Mathematics (Social Science)": {
        "en": "Mathematics (Soc Sci)",
        "am": "ሒሳብ - ማህበራዊ ሳይንስ",
        "om": "Hisaaba - Saayinsii Hawaasaa",
    },
    "Physics": {
        "en": "Physics",
        "am": "ፊዚክስ (Physics)",
        "om": "Fiiziksii (Physics)",
    },
    "Chemistry": {
        "en": "Chemistry",
        "am": "ኬሚስትሪ (Chemistry)",
        "om": "Keemistrii (Chemistry)",
    },
    "Biology": {
        "en": "Biology",
        "am": "ባዮሎጂ (Biology)",
        "om": "Bayooloojii (Biology)",
    },
    "History": {
        "en": "History",
        "am": "ታሪክ (History)",
        "om": "Seenaa (History)",
    },
    "Geography": {
        "en": "Geography",
        "am": "ጂኦግራፊ (Geography)",
        "om": "Joograafii (Geography)",
    },
    "Economics": {
        "en": "Economics",
        "am": "ኢኮኖሚክስ (Economics)",
        "om": "Ikoonoomiksii (Economics)",
    },
    "Citizenship Education": {
        "en": "Citizenship Education",
        "am": "ዜግነት ትምህርት",
        "om": "Barnoota Lammiyyummaa",
    },
    "Civics": {
        "en": "Citizenship Education",
        "am": "ዜግነት ትምህርት",
        "om": "Barnoota Lammiyyummaa",
    },
    "Information Technology (IT)": {
        "en": "Information Technology (IT)",
        "am": "ኢንፎርሜሽን ቴክኖሎጂ (IT)",
        "om": "Teeknoloojii Odeeffannoo (IT)",
    },
    "Computer Science": {
        "en": "Information Technology (IT)",
        "am": "ኢንፎርሜሽን ቴክኖሎጂ (IT)",
        "om": "Teeknoloojii Odeeffannoo (IT)",
    },
    "Health and Physical Education (HPE)": {
        "en": "Health & Physical Ed (HPE)",
        "am": "የሰውነት ማጠናከሪያ (HPE)",
        "om": "Fayyaa fi Leenjii Qaamaa",
    },
    "National/Regional Language": {
        "en": "National/Regional Language",
        "am": "ብሔራዊ/ክልላዊ ቋንቋ",
        "om": "Afaan Naannoo/Biyyooleessa",
    },
    "Agriculture": {
        "en": "Agriculture",
        "am": "ግብርና (Agriculture)",
        "om": "Qonnaa (Agriculture)",
    },
    "Environmental Science": {
        "en": "Environmental Science",
        "am": "አካባቢ ሳይንስ (Env Science)",
        "om": "Saayinsii Naannoo (Env Science)",
    },
    "Social Studies": {
        "en": "Social Studies",
        "am": "ኅብረተሰብ ጥናት (Social Studies)",
        "om": "Qorannoo Hawaasaa (Social Studies)",
    },
    "Moral and Citizenship Education": {
        "en": "Moral & Citizenship Ed",
        "am": "ስነ-ምግባር እና ዜግነት (Moral & Civics)",
        "om": "Safuu fi Barnoota Lammiyyummaa",
    },
    "Performing and Visual Arts (PVA)": {
        "en": "Performing & Visual Arts (PVA)",
        "am": "ሥነ-ጥበባት (PVA)",
        "om": "Aartii fi Aadaa (PVA)",
    },
    "General Science": {
        "en": "General Science",
        "am": "አጠቃላይ ሳይንስ (Gen Science)",
        "om": "Saayinsii Waliigalaa (Gen Science)",
    },
    "Career and Technical Education (CTE)": {
        "en": "Career & Technical Ed (CTE)",
        "am": "የሙያ እና ቴክኒክ ትምህርት (CTE)",
        "om": "Barnoota Ogummaa fi Teeknikaa (CTE)",
    }
}

STREAM_TRANSLATIONS = {
    "Natural Science": {
        "en": "🔬 Natural Science",
        "am": "🔬 ተፈጥሮ ሳይንስ (Natural Science)",
        "om": "🔬 Saayinsii Uamaa (Natural Science)",
    },
    "Social Science": {
        "en": "📜 Social Science",
        "am": "📜 ማህበራዊ ሳይንስ (Social Science)",
        "om": "📜 Saayinsii Hawaasaa (Social Science)",
    }
}

def get_subject_name_in_lang(subject: str, lang: Optional[str] = "English") -> str:
    n_lang = normalize_lang(lang)
    if subject in SUBJECT_TRANSLATIONS:
        return SUBJECT_TRANSLATIONS[subject].get(n_lang, subject)
    return subject

def get_stream_name_in_lang(stream: str, lang: Optional[str] = "English") -> str:
    n_lang = normalize_lang(lang)
    if stream in STREAM_TRANSLATIONS:
        return STREAM_TRANSLATIONS[stream].get(n_lang, stream)
    return stream

TRANSLATIONS = {
    # ------------------ English ------------------
    "en": {
        # Main Menu & Navigation
        "menu_title": "🎓 *Ethio Smart Study — Main Dashboard*\n━━━━━━━━━━━━━━━━━━━━\nWelcome back, *{name}*!\n\n🎓 Grade Level: *{grade}*\n🌐 Language: *English*\n📚 Active Topic: *{topic}*\n\nSelect an option below to start:",
        "btn_study": "📚 Study",
        "btn_study_pdf": "📄 Study PDF",
        "btn_ai_tutor": "🤖 AI Tutor",
        "btn_quiz": "❓ Quiz",
        "btn_written_test": "📝 Written Test",
        "btn_short_notes": "📖 Short Notes",
        "btn_national_exam": "🎓 National Exam Prep",
        "btn_progress": "📊 My Progress",
        "btn_profile": "👤 My Profile",
        "btn_materials": "📎 My Materials",
        "btn_study_tips": "💡 Study Tips & Advice",
        "btn_socials": "🌟 Follow Us",
        "btn_language": "🌐 Language",
        "btn_help": "ℹ️ Help",
        "btn_support": "📞 Support",
        "btn_feedback": "💬 Send Feedback",
        "btn_cancel": "❌ Cancel",
        "btn_back": "🔙 Back",
        "btn_continue": "▶️ Continue",
        "btn_delete": "🗑️ Delete",
        "btn_free_trial": "🎁 Try 1-Time Free AI Trial",
        "btn_study_mat": "📖 Study Material",
        "btn_upload_pdf": "📤 Upload PDF",
        "study_tips_menu_title": "💡 *Effective Study & Exam Success Coach*\n━━━━━━━━━━━━━━━━━━━━\nMaster how to study smarter, retain memory, manage time, and overcome exam stress with proven psychological techniques!\n\nSelect a topic or describe your specific study difficulty below:",
        "tips_btn_time": "⏰ Time Management & Pomodoro",
        "tips_btn_reading": "🧠 Active Recall & Feynman Method",
        "tips_btn_memory": "📝 Memory Tricks & Exam Strategy",
        "tips_btn_digital": "📱 Phone & Online Distractions",
        "tips_btn_focus": "⚡ Overcoming Procrastination & Focus",
        "tips_btn_custom": "💬 Describe My Study Problem",
        "tips_ask_problem": "💬 *Tell me about your study problem*\n━━━━━━━━━━━━━━━━━━━━\nWhat difficulty are you facing right now?\n_(e.g., 'I forget everything before exams', 'I get distracted easily', 'I don't know how to divide time for 5 subjects')_\n\nType your problem below and our AI Study Coach will give you tailored psychological advice and reading techniques:",
        "socials_title": "🌟 *Follow for More Islamic Reminders & Updates*\n━━━━━━━━━━━━━━━━━━━━\n\nTelegram: [Yusuf Moha](https://t.me/yusufcodes)\nLinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\nInstagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n━━━━━━━━━━━━━━━━━━━━\nMay Allah reward you 🤍",
        "support_title": "📞 *Support & Contact Information*\n━━━━━━━━━━━━━━━━━━━━\n\nFor inquiries, help, or technical support:\n\n• 💬 Telegram: [@Cs1At07](https://t.me/Cs1At07)\n• 📱 Phone: `0928892344`\n\nWe are here to assist you anytime! 🎓",

        # Registration & Payment
        "reg_welcome": "📝 *Student Registration*\n━━━━━━━━━━━━━━━━━━━━\nWelcome to Ethio Smart Study Bot!\nLet's set up your profile.\n\nPlease enter your full name:",
        "reg_ask_phone": "📱 *Phone Number*\n━━━━━━━━━━━━━━━━━━━━\nPlease enter your phone number (e.g. `0912345678`) or tap the button below to share your contact:",
        "btn_share_phone": "📱 Share Phone Number",
        "reg_ask_grade": "🎓 *Select your grade level or academic status:*",
        "reg_ask_stream": "🔬 *High School Academic Stream (Grade {grade})*\n━━━━━━━━━━━━━━━━━━━━\nPlease choose your academic stream to filter the correct curriculum:",
        "reg_ask_language": "🌐 *Select your preferred language:*",
        "reg_ask_subjects": "📚 *Select Courses / Subjects*\n━━━━━━━━━━━━━━━━━━━━\nChoose the subjects you want to study.\nPrice is *{price} ETB* per course.\n\nTap each button to select/unselect, then tap *Continue*:",
        "reg_btn_done_subjects": "➡️ Continue ({count} selected)",
        "reg_no_subjects_error": "⚠️ Please select at least one subject to proceed.",
        "reg_payment_summary": "📋 *Registration & Payment Summary*\n━━━━━━━━━━━━━━━━━━━━\n👤 *Full Name:* {name}\n📱 *Phone:* {phone}\n🏷️ *Username:* @{username}\n🎓 *Grade:* {grade}\n🌐 *Language:* {language}\n\n📚 *Selected Courses ({count}):*\n{courses}\n\n💰 *Price per Course:* {price} ETB\n💵 *Total Amount:* {total} ETB\n━━━━━━━━━━━━━━━━━━━━\nClick below to view payment instructions:",
        "btn_proceed_payment": "💳 Proceed to Payment",
        "btn_edit_subjects": "✏️ Edit Courses",
        "payment_instructions_card": "💳 *Payment Information*\n━━━━━━━━━━━━━━━━━━━━\n👤 *Owner Name:* {owner}\n\n🏦 *Commercial Bank of Ethiopia (CBE)*\nAccount Name: *{owner}*\nAccount Number: `{cbe}`\n\n📱 *Telebirr*\nOwner Name: *{owner}*\nPhone: `{telebirr}`\n━━━━━━━━━━━━━━━━━━━━\nSelected Courses: *{count}*\n💰 *Total Amount to Pay: {total} ETB*\n━━━━━━━━━━━━━━━━━━━━\n📸 *Next Step:* Please transfer the exact amount and upload a screenshot of your payment receipt below.",
        "payment_ask_screenshot": "📸 *Upload Payment Screenshot*\n━━━━━━━━━━━━━━━━━━━━\nPlease upload a clear screenshot or photo of your payment receipt:",
        "payment_submitted_student_notify": "⏳ *Payment Screenshot Submitted!*\n━━━━━━━━━━━━━━━━━━━━\nYour payment of *{total} ETB* for *{count} course(s)* is now submitted for verification.\n\nOur administrator will verify your receipt and approve your account shortly.\nYou will receive an instant notification once approved! 🎓",
        "reg_submitted": "⏳ *Registration Submitted!*\n━━━━━━━━━━━━━━━━━━━━\nYour profile has been submitted and is pending administrator approval.",
        "reg_cancelled": "❌ Registration cancelled. Send /start to register again.",
        "reg_pending_wait": "⏳ *Your registration is still waiting for admin approval.*\n━━━━━━━━━━━━━━━━━━━━\nPlease wait until your registration and payment have been verified by an administrator.",
        "reg_rejected": "❌ *Registration Rejected*\n━━━━━━━━━━━━━━━━━━━━\nYour registration was not approved by an administrator.",
        "reg_rejected_with_retry": "❌ *Registration Rejected*\n━━━━━━━━━━━━━━━━━━━━\nYour registration or payment was not approved by an administrator.\n\nReason: {reason}\n\nSend /start to re-submit your registration and payment receipt.",
        "reg_approved_notify": "🎉 *Congratulations! Your account has been approved!*\n━━━━━━━━━━━━━━━━━━━━\nYou now have full access to Ethio Smart Study Bot.\nUse the menu below or /study to begin learning!",
        "unregistered_course_error": "⛔ *Course Access Restricted*\n━━━━━━━━━━━━━━━━━━━━\nYou are not enrolled in *{course}*.\n\nYour active enrolled courses are:\n{courses}\n\nTo enroll in additional courses, please contact support (@Cs1At07).",

        # National Exam Prep
        "exam_locked_card": "🔒 *National Exam Preparation Package*\n━━━━━━━━━━━━━━━━━━━━\nNational Exam Prep is a premium package designed for Grade 6, 8, and 12 Ministry Leaving Examinations.\n\n✨ *Included Features:*\n• Authentic Ministry Exam Questions & Model Papers\n• Multi-Grade Review Access (Grades 5-6 for G6, 7-8 for G8, 9-12 for G12)\n• Custom Chapter & Question Count Tests\n• Score Analysis & Medal Grading\n\nTo unlock access, please contact support:\n• 💬 Telegram: [@Cs1At07](https://t.me/Cs1At07)\n• 📱 Phone: `0928892344`",
        "exam_ask_subject": "🎓 *National Exam Practice*\n━━━━━━━━━━━━━━━━━━━━\nSelect the subject you want to practice for your Ministry / National Examination:",
        "exam_ask_scope": "📚 *Provide Exam Scope or Material*\n━━━━━━━━━━━━━━━━━━━━\nSubject: *{subject}*\n\nPlease provide your exam material or scope:\n• 📄 *Upload a PDF / Document file*\n• 📸 *Upload a Photo / Image* of your textbook page or notes\n• ✍️ *Type a short description* of your topic/chapter below\n\n_Or choose Full Multi-Grade Exam Practice below:_",
        "exam_ask_qcount": "🔢 *Select Number of Questions*\n━━━━━━━━━━━━━━━━━━━━\nSubject: *{subject}*\nScope: *{scope}*\n\nSelect how many questions you want to practice:",

        # Feedback
        "feedback_ask": "💬 *Student Feedback & Suggestions*\n━━━━━━━━━━━━━━━━━━━━\nWe value your feedback to make Ethio Smart Study Bot better for all students!\n\nPlease type your feedback, experience, or feature suggestion below (or send a photo/document):",
        "feedback_thanks": "✅ *Thank You for Your Feedback!*\n━━━━━━━━━━━━━━━━━━━━\nYour feedback has been submitted successfully to our private feedback channel.\nWe appreciate your support in making Ethio Smart Study Bot better! 🤍",

        # Free Trial
        "trial_ask_grade": "🎁 *1-Time Free AI Trial Session*\n━━━━━━━━━━━━━━━━━━━━\nSelect your Grade Level to test 3 sample AI-generated practice questions without registering:",
        "trial_ask_subject": "🎁 *Select Free Trial Subject*\n━━━━━━━━━━━━━━━━━━━━\nGrade: *Grade {grade}*\n\nSelect a subject to try out 3 sample AI questions:",
        "trial_already_used": "⚠️ *Free Trial Limit Reached*\n━━━━━━━━━━━━━━━━━━━━\nYou have already completed your 1-Time Free Trial session.\n\nTo unlock unlimited AI practice, study sessions, written tests, and National Exam Prep, please click /start to register and enroll!",
        "trial_complete_card": "🎉 *Free Trial Completed!*\n━━━━━━━━━━━━━━━━━━━━\nScore: *{score}/{total} ({pct}%)*\n\n✨ *Unlock Unlimited Access:*\n• Unlimited AI Tutoring & Study Sessions\n• Summary Short Notes & PDF Processing\n• Ministry National Exam Practice\n\nClick /start to register & activate your full account!",

        # Admin Dynamic Pricing
        "admin_pricing_title": "💰 *Dynamic Course Pricing Management*\n━━━━━━━━━━━━━━━━━━━━\nCurrent price per course: *{price} ETB*\n\nTo update the price, enter the new amount in ETB (e.g. `60`):",
        "admin_pricing_updated": "✅ Course price updated successfully to *{price} ETB* per course!",

        # Study Mode
        "study_mode_title": "📚 *Study Mode*\n━━━━━━━━━━━━━━━━━━━━\nPlease choose one of your registered subjects to study:",
        "study_ask_course": "📚 *Start Studying*\n━━━━━━━━━━━━━━━━━━━━\nChoose a subject from your registered courses:",
        "study_choose_chapter": "📖 *{subject}*\n━━━━━━━━━━━━━━━━━━━━\nChoose a chapter to study:",
        "study_choose_topic": "📌 *{subject} — {chapter}*\n━━━━━━━━━━━━━━━━━━━━\nChoose a topic to study:",
        "study_input_choice": "📚 *Study Material Input*\n━━━━━━━━━━━━━━━━━━━━\nYou selected: *{subject}*\n\nHow would you like to provide your study context or requirements?",
        "study_btn_upload_file": "📎 Upload File / PDF + Description",
        "study_btn_text_desc": "✍️ Add Text Description / Topic",
        "study_ask_text": "✍️ *Text Description / Topic*\n━━━━━━━━━━━━━━━━━━━━\nPlease enter a description of the topic or specific questions you want to focus on:",
        "study_ask_file": "📎 *Upload File / PDF*\n━━━━━━━━━━━━━━━━━━━━\nPlease upload a PDF document or a photo of your study notes, with an optional description in the caption:",
        "study_intro_thinking": "⏳ Working, please wait...",
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
        "pdf_ask_upload": "📄 *PDF Study Mode*\n━━━━━━━━━━━━━━━━━━━━\nPlease send a PDF document to start studying.",
        "pdf_invalid_type": "❌ Please send a valid PDF document (.pdf file).",
        "pdf_size_error": "❌ File is too large. Maximum supported size is {max_size} MB.",
        "pdf_analyzed_title": "📄 *PDF Document Ready: {title}*\n━━━━━━━━━━━━━━━━━━━━\n📑 Pages: {pages} | 📝 Extracted Characters: {chars}\n\n📋 *Key Chapters / Topics:*\n{topics}\n\n📖 *Summary:*\n{summary}",
        "pdf_ask_question_prompt": "💬 *Ask Question on Document: {title}*\n━━━━━━━━━━━━━━━━━━━━\nType your question about this document below:",
        "pdf_answer_header": "📖 *Answer from Document:*\n━━━━━━━━━━━━━━━━━━━━\n{answer}",
        "pdf_empty_error": "❌ Could not find text in this document to answer your question.",

        # Materials Library
        "materials_title": "📎 *My Study Materials Library*\n━━━━━━━━━━━━━━━━━━━━\nHere are your uploaded study documents:",
        "materials_empty": "📎 You haven't uploaded any study materials yet.\nUse /pdf or the button below to upload your first document.",
        "materials_deleted": "✅ Material deleted successfully.",
        "materials_activated": "✅ Set as active study material!",

        # Quiz
        "quiz_no_session": "📚 You don't have an active study session yet.\n\nUse /study or select 📚 Study from the menu to start learning.",
        "quiz_generating": "⏳ Working, please wait...",
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
        "test_evaluating": "⏳ Working, please wait...",
        "test_history_title": "📝 *Previous Written Test Results*\n━━━━━━━━━━━━━━━━━━━━",

        # Short Notes
        "notes_title": "━━━━━━━━━━━━━━━━━━━━\n📖 *Short Notes Summary*\n━━━━━━━━━━━━━━━━━━━━\n📚 *{subject} → {topic}*\n\n{content}\n\n━━━━━━━━━━━━━━━━━━━━\n💡 Use /quiz to test your knowledge or /test for written practice",
        "notes_generating": "⏳ Working, please wait...",

        # Progress
        "progress_title": "📊 *My Learning Progress*\n━━━━━━━━━━━━━━━━━━━━\n👤 Student: *{name}*\n🎓 Grade: *{grade}*\n🌐 Language: *{language}*\n\n📚 *Academic Statistics:*\n• 📖 Lessons Started: *{lessons_count}*\n• ❓ Quizzes Taken: *{quizzes_count}*\n• 🎯 Quiz Success Rate: *{quiz_avg_pct}%* ({total_correct}/{total_questions} correct)\n• 📝 Written Tests: *{tests_count}* (Avg Score: *{test_avg_score}/10*)\n• 📄 PDFs Uploaded: *{pdf_count}*\n\n📌 *Active Session:* {active_topic}\n━━━━━━━━━━━━━━━━━━━━\nKeep up the great work! 💪",

        # Profile
        "profile_title": "👤 *Student Profile*\n━━━━━━━━━━━━━━━━━━━━\n👤 Name: *{name}*\n📱 Phone: `{phone}`\n🆔 Telegram ID: `{telegram_id}`\n🎓 Grade Level: *{grade}*\n🌐 Preferred Language: *{language}*\n📚 Registered Courses:\n{courses}\n📅 Registered: *{registered_date}*\n━━━━━━━━━━━━━━━━━━━━\nSelect an option below to update:",
        "profile_btn_change_grade": "🎓 Change Grade",
        "profile_btn_change_lang": "🌐 Change Language",

        # AI Tutor / Chat
        "tutor_thinking": "⏳ Working, please wait...",
        "ai_error": "⚠️ *Connection Error*\n━━━━━━━━━━━━━━━━━━━━\nI'm having trouble connecting to the AI right now.\nPlease try again in a moment.",

        # Help
        "help_title": "❓ *Ethio Smart Study — User Guide*\n━━━━━━━━━━━━━━━━━━━━\nWelcome to your AI Personal Tutor! Here is how to use the bot:\n\n📚 *Study Mode (`/study`)*\nSelect from your paid subjects and topics to start learning step-by-step.\n\n📄 *PDF Study (`/pdf`)*\nUpload your lecture notes, textbook chapters, or PDFs. Ask questions directly grounded in the text, get summaries, or take quizzes!\n\n📎 *Materials Library (`/materials`)*\nManage your uploaded study documents.\n\n❓ *Quiz (`/quiz`)*\nTest your knowledge with 5 adaptive multiple-choice questions with instant explanations.\n\n📝 *Written Test (`/test`)*\nTake a 3-question conceptual exam and get letter grades with constructive feedback.\n\n📖 *Short Notes (`/short_note`)*\nGenerate high-yield summary notes and key formulas tailored to your grade.\n\n📊 *Progress (`/progress`)*\nView your comprehensive study analytics and quiz scores.\n\n⚙️ *Profile & Language (`/profile`)*\nSwitch your grade (Grade 5 to University) or language (English, Amharic, Afaan Oromoo) anytime.\n\n💡 *Helpful Commands:*\n`/menu` - Main Dashboard\n`/study` - Start studying\n`/pdf` - PDF study tool\n`/materials` - Uploaded documents\n`/quiz` - Start quiz\n`/test` - Take written test\n`/short_note` - Study notes\n`/current` - View active topic\n`/progress` - View stats\n`/profile` - Account settings\n`/cancel` - Cancel current action\n`/newchat` - Clear conversation history",

        # Admin
        "admin_only_error": "❌ You are not authorized to perform this action.",
        "admin_dashboard_title": "🛡️ *Admin Control Dashboard*\n━━━━━━━━━━━━━━━━━━━━\n💰 *Course Price:* {price} ETB\n\n👥 *Students Overview:*\n• Total Registered: *{total}*\n• ✅ Approved: *{approved}*\n• ⏳ Pending: *{pending}*\n• ❌ Rejected: *{rejected}*\n\n📊 *Activity Statistics:*\n• 📚 Study Sessions: *{sessions}*\n• ❓ Quizzes Taken: *{quizzes}*\n• 📝 Tests Evaluated: *{tests}*\n• 📄 PDFs Uploaded: *{pdfs}*\n━━━━━━━━━━━━━━━━━━━━\nUse buttons below to manage students or broadcast an announcement:",
        "admin_btn_pricing": "💰 Set Price per Course",
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
        "menu_title": "🎓 *ኢትዮ ስማርት የጥናት ቦት — ዋና ዳሽቦርድ*\n━━━━━━━━━━━━━━━━━━━━\nእንኳን ደህና መጡ፣ *{name}*!\n\n🎓 የክፍል ደረጃ: *{grade}*\n🌐 ቋንቋ: *አማርኛ*\n📚 ንቁ ርዕስ: *{topic}*\n\nለመጀመር ከታች ካሉት አማራጮች አንዱን ይምረጡ:",
        "btn_study": "📚 አጥና",
        "btn_study_pdf": "📄 የፒዲኤፍ ጥናት",
        "btn_ai_tutor": "🤖 AI አስተማሪ",
        "btn_quiz": "❓ ጥያቄና መልስ (Quiz)",
        "btn_written_test": "📝 የጽሁፍ ፈተና",
        "btn_short_notes": "📖 አጫጭር ማስታወሻዎች",
        "btn_national_exam": "🎓 የብሔራዊ ፈተና ዝግጅት",
        "btn_progress": "📊 የኔ ውጤት/እድገት",
        "btn_profile": "👤 የኔ መገለጫ",
        "btn_materials": "📎 የእኔ ማቴሪያሎች",
        "btn_study_tips": "💡 የጥናት ምክሮች",
        "btn_socials": "🌟 ተከተሉን (Socials)",
        "btn_language": "🌐 ቋንቋ ቀይር",
        "btn_help": "ℹ️ እገዛ",
        "btn_support": "📞 ድጋፍ",
        "btn_feedback": "💬 አስተያየት ይላኩ",
        "btn_cancel": "❌ ሰርዝ",
        "btn_back": "🔙 ተመለስ",
        "btn_continue": "▶️ ቀጥል",
        "btn_delete": "🗑️ ሰርዝ",
        "btn_free_trial": "🎁 ነፃ 1 ጊዜ የሙከራ ትምህርት",
        "btn_study_mat": "📖 የጥናት ማቴሪያል",
        "btn_upload_pdf": "📤 ፒዲኤፍ ጫን",
        "study_tips_menu_title": "💡 *ውጤታማ የጥናት እና የፈተና ስኬት መመሪያ*\n━━━━━━━━━━━━━━━━━━━━\nሳይንሳዊ እና ስነ-ልቦናዊ የጥናት መንገዶችን በመጠቀም በጥራት ማጠናትን፣ ጊዜን በአግባቡ መጠቀምን፣ የማስታወስ ችሎታን እና ትኩረት ማድረግን ይማሩ!\n\nከታች ካሉት አማራጮች ይምረጡ ወይም የእርስዎን የጥናት ችግር ይንገሩን:",
        "tips_btn_time": "⏰ የጊዜ አጠቃቀም እና Pomodoro",
        "tips_btn_reading": "🧠 ንቁ ንባብ (Active Recall) እና Feynman ዘዴ",
        "tips_btn_memory": "📝 የማስታወስ ዘዴዎች እና የፈተና ጥበብ",
        "tips_btn_digital": "📱 የስልክ እና የኦንላይን ትኩረት መበተን",
        "tips_btn_focus": "⚡ ትኩረት መሰብሰብ እና ስንፍናን ማሸነፍ",
        "tips_btn_custom": "💬 የእኔን የጥናት ችግር ለመናገር",
        "tips_ask_problem": "💬 *የጥናት ችግርዎን ይንገሩን*\n━━━━━━━━━━━━━━━━━━━━\nበጥናትዎ ላይ ምን አይነት ፈተና ወይም ችግር አጋጥሞዎታል?\n_(ለምሳሌ፦ 'በፍጥነት እረሳለሁ'፣ 'ትኩረቴ በፍጥነት ይበተናል'፣ 'ጊዜ እንዴት እንደምመድብ ግራ ገብቶኛል')_\n\nችግርዎን ከታች ይጻፉ፤ AI የጥናት መካሪያችን ሳይንሳዊ እና ስነ-ልቦናዊ መፍትሔ ይሰጥዎታል:",
        "socials_title": "🌟 *ተጨማሪ ኢስላማዊ ማስታወሻዎችን ለማግኘት ይከተሉን*\n━━━━━━━━━━━━━━━━━━━━\n\nTelegram: [Yusuf Moha](https://t.me/yusufcodes)\nLinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\nInstagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n━━━━━━━━━━━━━━━━━━━━\nአላህ መልካም ምንዳ ይክፈላችሁ 🤍",
        "support_title": "📞 *የእርዳታ እና የድጋፍ መስመር*\n━━━━━━━━━━━━━━━━━━━━\n\nለማንኛውም ጥያቄ ወይም የቴክኒክ ድጋፍ:\n\n• 💬 ቴሌግራም: [@Cs1At07](https://t.me/Cs1At07)\n• 📱 ስልክ: `0928892344`\n\nበትምህርትዎ እንዲሳካልዎት ሁልጊዜ ከጎንዎ ነን! 🎓",

        # Registration & Payment
        "reg_welcome": "📝 *የተማሪ ምዝገባ*\n━━━━━━━━━━━━━━━━━━━━\nወደ ኢትዮ ስማርት የጥናት ቦት እንኳን በደህና መጡ!\nመገለጫዎን እናዘጋጅ።\n\nእባክዎ ሙሉ ስምዎን ያስገቡ:",
        "reg_ask_phone": "📱 *የስልክ ቁጥር*\n━━━━━━━━━━━━━━━━━━━━\nእባክዎ የስልክ ቁጥርዎን ያስገቡ (ለምሳሌ፦ `0912345678`) ወይም ከታች ያለውን ቁልፍ በመጫን ያጋሩ:",
        "btn_share_phone": "📱 ስልክ ቁጥር አጋራ",
        "reg_ask_grade": "🎓 *የትምህርት ደረጃዎን ወይም ክፍልዎን ይምረጡ:*",
        "reg_ask_stream": "🔬 *የሁለተኛ ደረጃ ትምህርት ዘርፍ (ክፍል {grade})*\n━━━━━━━━━━━━━━━━━━━━\nእባክዎ ትክክለኛውን የትምህርት ዘርፍ ይምረጡ:",
        "reg_ask_language": "🌐 *የሚመርጡትን ቋንቋ ይምረጡ:*",
        "reg_ask_subjects": "📚 *የሚፈልጓቸውን የትምህርት አይነቶች ይምረጡ*\n━━━━━━━━━━━━━━━━━━━━\nየአንድ ትምህርት ክፍያ: *{price} ብር* ነው።\n\nመምረጥ የሚፈልጉትን ይጫኑ፣ ሲጨርሱ *ቀጥል* የሚለውን ይጫኑ:",
        "reg_btn_done_subjects": "➡️ ቀጥል ({count} ተመርጧል)",
        "reg_no_subjects_error": "⚠️ እባክዎ ለመቀጠል ቢያንስ አንድ የትምህርት አይነት ይምረጡ።",
        "reg_payment_summary": "📋 *የምዝገባ እና የክፍያ ማጠቃለያ*\n━━━━━━━━━━━━━━━━━━━━\n👤 *ስም:* {name}\n📱 *ስልክ:* {phone}\n🏷️ *ዩዘርኔም:* @{username}\n🎓 *ክፍል:* {grade}\n🌐 *ቋንቋ:* {language}\n\n📚 *የተመረጡ ትምህርቶች ({count}):*\n{courses}\n\n💰 *ዋጋ በኮርስ:* {price} ብር\n💵 *ጠቅላላ የሚከፈል:* {total} ብር\n━━━━━━━━━━━━━━━━━━━━\nየክፍያ መረጃዎችን ለማየት ከታች ይጫኑ:",
        "btn_proceed_payment": "💳 ወደ ክፍያ ቀጥል",
        "btn_edit_subjects": "✏️ ትምህርቶችን ቀይር",
        "payment_instructions_card": "💳 *የክፍያ መረጃዎች*\n━━━━━━━━━━━━━━━━━━━━\n👤 *የሂሳብ ባለቤት:* {owner}\n\n🏦 *የኢትዮጵያ ንግድ ባንክ (CBE)*\nየሂሳብ ስም: *{owner}*\nየሂሳብ ቁጥር: `{cbe}`\n\n📱 *ቴሌብር (Telebirr)*\nየስም ባለቤት: *{owner}*\nስልክ: `{telebirr}`\n━━━━━━━━━━━━━━━━━━━━\nየተመረጡ ትምህርቶች: *{count}*\n💰 *ጠቅላላ የሚከፈል: {total} ብር*\n━━━━━━━━━━━━━━━━━━━━\n📸 *ቀጣይ እርምጃ:* እባክዎ የተጠቀሰውን ክፍያ ከፈጸሙ በኋላ የደረሰኝ ስክሪንሽት (ፎቶ) ከታች ይላኩ።",
        "payment_ask_screenshot": "📸 *የክፍያ ደረሰኝ ፎቶ (Screenshot) ይላኩ*\n━━━━━━━━━━━━━━━━━━━━\nእባክዎ የከፈሉበትን ደረሰኝ ስክሪንሽት ወይም ፎቶ ይላኩ:",
        "payment_submitted_student_notify": "⏳ *የክፍያ ደረሰኝዎ ደርሶናል!*\n━━━━━━━━━━━━━━━━━━━━\nየከፈሉት *{total} ብር* ለ *{count} ትምህርት(ቶች)* ለአስተዳዳሪ ቀርቧል።\n\nአስተዳዳሪው ደረሰኝዎን አረጋግጦ አካውንትዎን በቅርቡ ያጸድቃል።\nልክ እንደተፈቀደልዎ ወዲያውኑ መልዕክት ይደርስዎታል! 🎓",
        "reg_submitted": "⏳ *ምዝገባዎ ገብቷል!*\n━━━━━━━━━━━━━━━━━━━━\nመረጃዎ ለአስተዳዳሪ ቀርቧል። ልክ እንደተፈቀደልዎ ማሳወቂያ ይደርስዎታል።",
        "reg_cancelled": "❌ ምዝገባው ተሰርዟል። እንደገና ለመመዝገብ /start ይላኩ።",
        "reg_pending_wait": "⏳ *ምዝገባዎ እና ክፍያዎ በመጠባበቅ ላይ ነው*\n━━━━━━━━━━━━━━━━━━━━\nምዝገባዎ በአስተዳዳሪ እየታየ ነው። ልክ እንደተፈቀደልዎ ማሳወቂያ ይደርስዎታል።",
        "reg_rejected": "❌ *ምዝገባዎ ውድቅ ተደርጓል*\n━━━━━━━━━━━━━━━━━━━━\nምዝገባዎ በአስተዳዳሪ ተቀባይነት አላገኘም።",
        "reg_rejected_with_retry": "❌ *ምዝገባዎ ተቀባይነት አላገኘም*\n━━━━━━━━━━━━━━━━━━━━\nምክንያት: {reason}\n\nእንደገና ለመመዝገብ እና ደረሰኝ ለመላክ /start ይጫኑ።",
        "reg_approved_notify": "🎉 *እንኳን ደስ አለዎት! ምዝገባዎ ተፈቅዷል!*\n━━━━━━━━━━━━━━━━━━━━\nአሁን የኢትዮ ስማርት የጥናት ቦት አገልግሎትን ሙሉ በሙሉ መጠቀም ይችላሉ።\nለመማር /study ይጠቀሙ ወይም ሜኑውን ይምረጡ!",
        "unregistered_course_error": "⛔ *ይህ ትምህርት አልተመዘገበም*\n━━━━━━━━━━━━━━━━━━━━\nየተመዘገቡባቸው ትምህርቶች:\n{courses}\n\nተጨማሪ ትምህርት ለመመዝገብ እባክዎ ድጋፍን ያነጋግሩ (@Cs1At07)።",

        # Admin Dynamic Pricing
        "admin_pricing_title": "💰 *የትምህርት ዋጋ ማስተካከያ*\n━━━━━━━━━━━━━━━━━━━━\nየአሁኑ ዋጋ በኮርስ: *{price} ብር*\n\nአዲሱን ዋጋ በብር ያስገቡ (ለምሳሌ፦ `60`):",
        "admin_pricing_updated": "✅ የኮርስ ዋጋ በተሳካ ሁኔታ ወደ *{price} ብር* ተቀይሯል!",

        # Study Mode
        "study_mode_title": "📚 *የጥናት ሁነታ*\n━━━━━━━━━━━━━━━━━━━━\nከተመዘገቡባቸው ትምህርቶች መካከል አንዱን ይምረጡ:",
        "study_ask_course": "📚 *ጥናት ጀምር*\n━━━━━━━━━━━━━━━━━━━━\nማጥናት የሚፈልጉትን የትምህርት አይነት ይምረጡ:",
        "study_choose_chapter": "📖 *{subject}*\n━━━━━━━━━━━━━━━━━━━━\nየጥናት ምዕራፍ ይምረጡ:",
        "study_choose_topic": "📌 *{subject} — {chapter}*\n━━━━━━━━━━━━━━━━━━━━\nየጥናት ርዕስ ይምረጡ:",
        "study_input_choice": "📚 *የጥናት ማቴሪያል ማስገቢያ*\n━━━━━━━━━━━━━━━━━━━━\nየመረጡት: *{subject}*\n\nየጥናት ፍላጎትዎን ወይም ይዘትዎን እንዴት ማቅረብ ይፈልጋሉ?",
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
        "pdf_ask_prompt": "💬 *ከፒዲኤፉ ጠይቅ*\n━━━━━━━━━━━━━━━━━━━━\nስለ *{title}* ማንኛውንም ጥያቄ ይጠይቁ:",
        "pdf_ask_upload": "📄 *የፒዲኤፍ ጥናት ሁነታ*\n━━━━━━━━━━━━━━━━━━━━\nለማጥናት እባክዎን የፒዲኤፍ ሰነድ ይላኩ።",
        "pdf_invalid_type": "❌ እባክዎ ትክክለኛ የፒዲኤፍ ፋይል (.pdf) ይላኩ።",
        "pdf_size_error": "❌ ፋይሉ በጣም ትልቅ ነው። የሚፈቀደው ከፍተኛ መጠን {max_size} MB ነው።",
        "pdf_analyzed_title": "📄 *የተዘጋጀ የፒዲኤፍ ሰነድ: {title}*\n━━━━━━━━━━━━━━━━━━━━\n📑 ገጾች: {pages}\n\n📋 *ምዕራፎች / ርዕሶች:*\n{topics}\n\n📖 *ማጠቃለያ:*\n{summary}",
        "pdf_ask_question_prompt": "💬 *ስለ ሰነዱ ጥያቄ ይጠይቁ: {title}*\n━━━━━━━━━━━━━━━━━━━━\nጥያቄዎን ከታች ይጻፉ:",
        "pdf_answer_header": "📖 *ከሰነዱ የተገኘ መልስ:*\n━━━━━━━━━━━━━━━━━━━━\n{answer}",
        "pdf_empty_error": "❌ ለጥያቄዎ በሰነዱ ውስጥ መልስ ማግኘት አልተቻለም።",

        # Materials Library
        "materials_title": "📎 *የእኔ ማቴሪያሎች ቤተ-መጽሐፍት*\n━━━━━━━━━━━━━━━━━━━━\nየጫኗቸው የጥናት ሰነዶች ዝርዝር:",
        "materials_empty": "📎 እስካሁን ምንም የጥናት ማቴሪያል አልጫኑም።",
        "materials_deleted": "✅ ማቴሪያሉ በተሳካ ሁኔታ ተሰርዟል።",
        "materials_activated": "✅ ንቁ የጥናት ሰነድ ሆኖ ተመርጧል!",

        # Quiz
        "quiz_no_session": "📚 ምንም ንቁ የጥናት ክፍለ ጊዜ የለዎትም።\n\nለመማር /study ይጠቀሙ።",
        "quiz_generating": "🤔 የፈተና ጥያቄዎችን በማዘጋጀት ላይ...",
        "quiz_mode_title": "❓ *የጥያቄና መልስ ፈተና ተጀመረ*\n━━━━━━━━━━━━━━━━━━━━\n📚 ትምህርት: *{subject} → {topic}*",
        "quiz_active_prompt": "❓ *ንቁ የጥያቄና መልስ ፈተና አለዎት!*\nጥያቄ {current} ከ {total}።",
        "quiz_question_header": "━━━━━━━━━━━━━━━━━━━━\n{emoji} *{topic} — ፈተና*\n━━━━━━━━━━━━━━━━━━━━\n📝 ጥያቄ *{num}* ከ *{total}*\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🇦  {opt_a}\n🇧  {opt_b}\n🇨  {opt_c}\n🇩  {opt_d}",
        "quiz_correct": "✅ *ትክክል ነው!*",
        "quiz_incorrect": "❌ *ስህተት ነው።*",
        "quiz_correct_reveal": "\n❗ *ትክክለኛው መልስ:* {correct_key}. {correct_text}\n",
        "quiz_complete_title": "━━━━━━━━━━━━━━━━━━━━\n🎉 *ፈተናው ተጠናቋል!*\n━━━━━━━━━━━━━━━━━━━━\n{emoji} *{subject} → {topic}*\n\n📊 *ውጤት:*\n   ✅ ትክክል: *{score}*\n   ❌ የተሳሳተ: *{incorrect}*\n   💯 ውጤት: *{score}/{total} — {pct}%*",

        # Written Test
        "test_title": "━━━━━━━━━━━━━━━━━━━━\n📝 *የጽሁፍ ፈተና ሁነታ*\n━━━━━━━━━━━━━━━━━━━━\n📚 ትምህርት: *{subject} → {topic}*\n\nየሚከተሉትን 3 የጽሁፍ ጥያቄዎች በአንድ መልእክት ይመልሱ:\n\n━━━━━━━━━━━━━━━━━━━━\n{questions}",
        "test_grading_title": "━━━━━━━━━━━━━━━━━━━━\n💯 *የፈተና ውጤት እና ግምገማ*\n━━━━━━━━━━━━━━━━━━━━\n{result}",
        "test_evaluating": "⏳ ይሰራል፣ እባክዎ ትንሽ ይጠብቁ...",
        "test_history_title": "📝 *ያለፉ የጽሁፍ ፈተና ውጤቶች*\n━━━━━━━━━━━━━━━━━━━━",

        # Short Notes
        "notes_title": "━━━━━━━━━━━━━━━━━━━━\n📖 *አጭር የጥናት ማጠቃለያ*\n━━━━━━━━━━━━━━━━━━━━\n📚 *{subject} → {topic}*\n\n{content}",
        "notes_generating": "⏳ ይሰራል፣ እባክዎ ትንሽ ይጠብቁ...",

        # Progress
        "progress_title": "📊 *የትምህርት እድገት እና ውጤቴ*\n━━━━━━━━━━━━━━━━━━━━\n👤 ተማሪ: *{name}*\n🎓 ክፍል: *{grade}*\n🌐 ቋንቋ: *{language}*\n\n📚 *ስታትስቲክስ:*\n• 📖 የተጀመሩ ትምህርቶች: *{lessons_count}*\n• ❓ የተወሰዱ ፈተናዎች: *{quizzes_count}*\n• 🎯 አማካይ ውጤት: *{quiz_avg_pct}%*\n• 📝 የጽሁፍ ፈተናዎች: *{tests_count}*\n• 📄 የተጫኑ ፒዲኤፎች: *{pdf_count}*",

        # Profile
        "profile_title": "👤 *የተማሪ መገለጫ*\n━━━━━━━━━━━━━━━━━━━━\n👤 ስም: *{name}*\n📱 ስልክ: `{phone}`\n🆔 ቴሌግራም ID: `{telegram_id}`\n🎓 ክፍል: *{grade}*\n🌐 ቋንቋ: *{language}*\n📚 የተመዘገቡ ትምህርቶች:\n{courses}\n📅 የተመዘገበበት ቀን: *{registered_date}*",
        "profile_btn_change_grade": "🎓 ክፍል ቀይር",
        "profile_btn_change_lang": "🌐 ቋንቋ ቀይር",

        # AI Tutor / Chat
        "tutor_thinking": "⏳ ይሰራል፣ እባክዎ ትንሽ ይጠብቁ...",
        "ai_error": "⚠️ *የግንኙነት ስህተት*\n━━━━━━━━━━━━━━━━━━━━\nእባክዎ ከጥቂት ደቂቃዎች በኋላ እንደገና ይሞክሩ።",

        # Help
        "help_title": "❓ *ኢትዮ ስማርት የጥናት ቦት — የተጠቃሚ መመሪያ*\n━━━━━━━━━━━━━━━━━━━━\nእንኳን ወደ AI የግል አስተማሪዎ በደህና መጡ!",

        # Feedback
        "feedback_ask": "💬 *የተማሪዎች አስተያየት እና ጥቆማ*\n━━━━━━━━━━━━━━━━━━━━\nቦቱን የበለጠ ለማሻሻል የእርሶ አስተያየት ለእኛ በጣም ጠቃሚ ነው!\n\nእባክዎ አስተያየትዎን፣ ጥቆማዎን ወይም ያጋጠመዎትን ሁኔታ ከታች ይጻፉ (ወይም ፎቶ/ፋይል ይላኩ):",
        "feedback_thanks": "✅ *ስለ አስተያየትዎ እናመሰግናለን!*\n━━━━━━━━━━━━━━━━━━━━\nአስተያየትዎ በተሳካ ሁኔታ ወደ አስተያየት ቻናላችን ተልኳል።\nቦታችንን የበለጠ ለማሻሻል ስላደረጉት አስተዋጽኦ እናመሰግናለን! 🤍",

        # Free Trial
        "trial_ask_grade": "🎁 *ነፃ 1 ጊዜ የ AI የሙከራ ትምህርት*\n━━━━━━━━━━━━━━━━━━━━\nሳይመዘገቡ 3 የ AI ጥያቄዎችን ለመሞከር ክፍሎትን ይምረጡ:",
        "trial_ask_subject": "🎁 *የሙከራ ትምህርቱን ይምረጡ*\n━━━━━━━━━━━━━━━━━━━━\nክፍል: *ክፍል {grade}*\n\n3 የ AI ጥያቄዎችን ለመሞከር ትምህርት ይምረጡ:",
        "trial_already_used": "⚠️ *የነፃ ሙከራ ገደብ ተደርሷል*\n━━━━━━━━━━━━━━━━━━━━\nየ 1 ጊዜ ነፃ የሙከራ ትምህርቶን ጨርሰዋል።\n\nሁሉንም የ AI ጥናቶች፣ ማስታወሻዎች እና የብሔራዊ ፈተና ልምምዶችን ለማግኘት እባክዎ /start በመጫን ይመዝገቡ!",
        "trial_complete_card": "🎉 *የሙከራ ትምህርቱ ተጠናቋል!*\n━━━━━━━━━━━━━━━━━━━━\nውጤት: *{score}/{total} ({pct}%)*\n\n✨ *ሙሉ አገልግሎቱን ይክፈቱ:*\n• ያልተገደበ የ AI አስተማሪ እና የጥናት ሁነታ\n• አጭር ማጠቃለያዎች እና ፒዲኤፍ ማነበብ\n• የብሔራዊ እና ሚኒስቴር ፈተናዎች ልምምድ\n\nአካውንቶን ለማግበር እባክዎ /start ን ይጫኑ!",

        # Admin
        "admin_only_error": "❌ ይህን እርምጃ ለማከናወን ፈቃድ የለዎትም።",
        "admin_dashboard_title": "🛡️ *የአስተዳዳሪ ዳሽቦርድ*\n━━━━━━━━━━━━━━━━━━━━\n💰 *የኮርስ ዋጋ:* {price} ብር\n\n👥 *የተማሪዎች አጠቃላይ ሁኔታ:*\n• የተመዘገቡ: *{total}*\n• ✅ የጸደቁ: *{approved}*\n• ⏳ በመጠባበቅ ላይ: *{pending}*\n• ❌ ውድቅ የተደረጉ: *{rejected}*",
        "admin_btn_pricing": "💰 የኮርስ ዋጋ ማስተካከያ",
        "admin_btn_pending": "⏳ በመጠባበቅ ላይ ({count})",
        "admin_btn_approved_list": "👥 የጸደቁ ተማሪዎች",
        "admin_btn_rejected_list": "❌ ውድቅ የተደረጉ",
        "admin_btn_search": "🔍 ተማሪ ፈልግ",
        "admin_btn_broadcast": "📢 መልእክት አስተላልፍ",
        "admin_btn_refresh": "🔄 ዳሽቦርድ አድስ",
        "admin_no_pending": "✅ በአሁኑ ጊዜ በመጠባበቅ ላይ ያሉ ማመልከቻዎች የሉም።",
    },

    # ------------------ Afaan Oromoo ------------------
    "om": {
        # Main Menu & Navigation
        "menu_title": "🎓 *Ethio Smart Study — Fuula Guddaa*\n━━━━━━━━━━━━━━━━━━━━\nBaga nagaan dhufte, *{name}*!\n\n🎓 Sadarkaa Kutaa: *{grade}*\n🌐 Afaan: *Afaan Oromoo*\n📚 Mata Duree Ammaa: *{topic}*\n\nJalqabuuf filannoowwan armaan gadii keessaa tokko filadhu:",
        "btn_study": "📚 Qo'adhu",
        "btn_study_pdf": "📄 Qo'annoo PDF",
        "btn_ai_tutor": "🤖 Barsiisaa AI",
        "btn_quiz": "❓ Gaaffilee (Quiz)",
        "btn_written_test": "📝 Qormaata Barreeffamaa",
        "btn_short_notes": "📖 Yaadannoo Gabaabaa",
        "btn_national_exam": "🎓 Qormaata Biyyooleessaa",
        "btn_progress": "📊 Guddina Koo",
        "btn_profile": "👤 Piroofayilii Koo",
        "btn_materials": "📎 Meeshaalee Koo",
        "btn_study_tips": "💡 Tarsa'aa Qo'annoo",
        "btn_socials": "🌟 Nu Hordofaa",
        "btn_language": "🌐 Afaan Jijjiiri",
        "btn_help": "ℹ️ Gargaarsa",
        "btn_support": "📞 Deeggarsa",
        "btn_feedback": "💬 Yaada Ergaa",
        "btn_cancel": "❌ Dhiisi",
        "btn_back": "🔙 Duubatti",
        "btn_continue": "▶️ Itti Fufi",
        "btn_delete": "🗑️ Dhiisi",
        "btn_free_trial": "🎁 Yaalii Bilisaa 1-Yeroo",
        "btn_study_mat": "📖 Meeshaa Qo'annoo",
        "btn_upload_pdf": "📤 PDF Ol-kaasi",
        "study_tips_menu_title": "💡 *Gorsa Qo'annoo fi Milkaa'ina Qormaataa*\n━━━━━━━━━━━━━━━━━━━━\nMalleen qorannoofi saayinsawaa fayyadamuun akkamitti bu'a qabeessummaan akka qo'attan, yeroo akka bulchattaniifi qormaataf akkamitti qophaa'an baradhaa!\n\nFilannoowwan armaan gadii keessaa filadhaa ykn rakkoo qo'annoo keessan nuuf barreessaa:",
        "tips_btn_time": "⏰ Bulchiinsa Yeroo fi Pomodoro",
        "tips_btn_reading": "🧠 Dubbisa Dammaqaa (Active Recall) fi Feynman",
        "tips_btn_memory": "📝 Malleen Yaadannoo fi Toftaa Qormaataa",
        "tips_btn_digital": "📱 Jeequmsa Bilbilaa fi Interneetaa",
        "tips_btn_focus": "⚡ Xiyyeeffannoo fi Dhibaa'ummaa Mo'achuu",
        "tips_btn_custom": "💬 Rakkoo Qo'annoo Koo Barreessuuf",
        "tips_ask_problem": "💬 *Rakkoo Qo'annoo Keessan Nuuf Barreessaa*\n━━━━━━━━━━━━━━━━━━━━\nYeroo qo'attan rakkoon isin mudate maali?\n_(fakkeenyaaf: 'Dafeen irraanfadhadha', 'Xiyyeeffannoon koo dafee badha', 'Yeroo qoodachuu hin danda'u')_\n\nBarreessaa; Barsiisaan AI keenya gorsa teeknikaa fi saayinsawaa isiniif kennama:",
        "socials_title": "🌟 *Gorsaalee Islaamaa fi Odeeffannoo Dabalataaf Nu Hordofaa*\n━━━━━━━━━━━━━━━━━━━━\n\nTelegram: [Yusuf Moha](https://t.me/yusufcodes)\nLinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\nInstagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n━━━━━━━━━━━━━━━━━━━━\nRabbiin jazaa keessan isiniif haa kennu 🤍",
        "support_title": "📞 *Teessoo Deeggarsaa fi Qunnamtii*\n━━━━━━━━━━━━━━━━━━━━\n\nGaaffii ykn deeggarsa teeknikaa kamiyyuuf:\n\n• 💬 Telegram: [@Cs1At07](https://t.me/Cs1At07)\n• 📱 Bilbila: `0928892344`\n\nBarnoota keessaniin akka milkooftan isin gargaaruuf qophiidha! 🎓",

        # Registration & Payment
        "reg_welcome": "📝 *Galmee Barataa*\n━━━━━━━━━━━━━━━━━━━━\nBaga nagaan gara Ethio Smart Study Bot dhuftan!\nPiroofayilii keessan haa qopheessinu.\n\nMaqaa keessan guutuu galchaa:",
        "reg_ask_phone": "📱 *Lakkoofsa Bilbilaa*\n━━━━━━━━━━━━━━━━━━━━\nMee lakkoofsa bilbila keessanii galchaa (fakkeenyaaf: `0912345678`) ykn qabduu armaan gadii tuquun nuuf qoodaa:",
        "btn_share_phone": "📱 Bilbila Qoodaa",
        "reg_ask_grade": "🎓 *Sadarkaa kutaa ykn barnoota keessanii filadhaa:*",
        "reg_ask_stream": "🔬 *Kutaa Qo'annoo Mana Barumsaa Sadarkaa 2ffaa (Kutaa {grade})*\n━━━━━━━━━━━━━━━━━━━━\nMaaloo killee qo'annoo kee sirrii ta'e filadhu:",
        "reg_ask_language": "🌐 *Afaan ittiin barachuu barbaaddan filadhaa:*",
        "reg_ask_subjects": "📚 *Gosoota Barnootaa Filadhaa*\n━━━━━━━━━━━━━━━━━━━━\nGatiin gosa barnootaa tokkoo: *{price} ETB* dha.\n\nFilachuuf tuqaa, yeroo xumurtan *Itti Fufi* tuqaa:",
        "reg_btn_done_subjects": "➡️ Itti Fufi ({count} filatameera)",
        "reg_no_subjects_error": "⚠️ Mee itti fufuuf yoo xiqqaate gosa barnootaa tokko filadhaa.",
        "reg_payment_summary": "📋 *Cuunfaa Galmee fi Kaffaltii*\n━━━━━━━━━━━━━━━━━━━━\n👤 *Maqaa:* {name}\n📱 *Bilbila:* {phone}\n🏷️ *Username:* @{username}\n🎓 *Kutaa:* {grade}\n🌐 *Afaan:* {language}\n\n📚 *Barnoota Filataman ({count}):*\n{courses}\n\n💰 *Gatii Koorsootiin:* {price} ETB\n💵 *Dimshaasha Kaffalamu:* {total} ETB\n━━━━━━━━━━━━━━━━━━━━\nOdeeffannoo kaffaltii argachuuf armaan gadi tuqaa:",
        "btn_proceed_payment": "💳 Gara Kaffaltiitti Dabbari",
        "btn_edit_subjects": "✏️ Barnoota Jijjiiri",
        "payment_instructions_card": "💳 *Odeeffannoo Kaffaltii*\n━━━━━━━━━━━━━━━━━━━━\n👤 *Abbaa Herregaa:* {owner}\n\n🏦 *Baankii Daldala Itoophiyaa (CBE)*\nMaqaa Herregaa: *{owner}*\nLakkoofsa Herregaa: `{cbe}`\n\n📱 *Telebirr*\nMaqaa Abbaa Bilbilaa: *{owner}*\nBilbila: `{telebirr}`\n━━━━━━━━━━━━━━━━━━━━\nBarnoota Filataman: *{count}*\n💰 *Kaffaltii Dimshaashaa: {total} ETB*\n━━━━━━━━━━━━━━━━━━━━\n📸 *Tarkaanfii Itti Aanu:* Kaffaltii erga raawwattanii booda nagahee isaa (screenshot) asitti ergaa.",
        "payment_ask_screenshot": "📸 *Nagahee Kaffaltii (Screenshot) Ergaa*\n━━━━━━━━━━━━━━━━━━━━\nMee suuraa ykn screenshot nagahee kaffaltii keessanii ergaa:",
        "payment_submitted_student_notify": "⏳ *Nagaheen Kaffaltii Keessan Nu Qaqqabeera!*\n━━━━━━━━━━━━━━━━━━━━\nKaffaltiin *{total} ETB* koorsii *{count}* qorannoof dhiyaateera.\n\nBulchaan keenya nagahee keessan mirkaneessee yeroo gabaabaatti eeyyamsiisa.\nEeyyama argachuu keessan yeroo sana beeksifamtu! 🎓",
        "reg_submitted": "⏳ *Galmeen Dhiyaateera!*\n━━━━━━━━━━━━━━━━━━━━\nOdeeffannoon keessan bulchaatti dhiyaateera.",
        "reg_cancelled": "❌ Galmeen haqameera. Irra deebiin galmaa'uuf /start ergaa.",
        "reg_pending_wait": "⏳ *Galmeen keessan eeyyama bulchaa eegaa jira.*\n━━━━━━━━━━━━━━━━━━━━\nMee hanga nagaheen kaffaltii keessanii mirkanaa'utti obsaan eegaa.",
        "reg_rejected": "❌ *Galmeen keessan kufaa ta'eera.*",
        "reg_rejected_with_retry": "❌ *Galmeen Keessan Kufaa Ta'eera*\n━━━━━━━━━━━━━━━━━━━━\nSababa: {reason}\n\nIrra deebiin galmaa'uuf fi nagahee erguuf /start tuqaa.",
        "reg_approved_notify": "🎉 *Baga Gammaddan! Galmeen Keessan Eeyyamameera!*\n━━━━━━━━━━━━━━━━━━━━\nAmma tajaajila Ethio Smart Study Bot guututti fayyadamuu dandeessu.\nJalqabuuf /study fayyadamaa!",
        "unregistered_course_error": "⛔ *Koorsii Kanaaf Hin Galmoofne*\n━━━━━━━━━━━━━━━━━━━━\nKoorsoonni keessan galmaa'an:\n{courses}\n\nKoorsii dabalataa dabalachuuf deeggarsa qunnamaa (@Cs1At07).",

        # Admin Dynamic Pricing
        "admin_pricing_title": "💰 *Gatii Koorsootaa Sirreessuu*\n━━━━━━━━━━━━━━━━━━━━\nGatiin ammaa: *{price} ETB*\n\nGatii haaraa ETB galchaa (fakkeenyaaf: `60`):",
        "admin_pricing_updated": "✅ Gatiin koorsii gara *{price} ETB* tti sirreeffameera!",

        # Study Mode
        "study_mode_title": "📚 *Qo'annoo*\n━━━━━━━━━━━━━━━━━━━━\nKoorsoota galmooftan keessaa tokko filadhaa:",
        "study_ask_course": "📚 *Barnoota Jalqabaa*\n━━━━━━━━━━━━━━━━━━━━\nGosa barnootaa qo'achuu barbaaddan filadhaa:",
        "study_choose_chapter": "📖 *{subject}*\n━━━━━━━━━━━━━━━━━━━━\nBoqonnaa filadhaa:",
        "study_choose_topic": "📌 *{subject} — {chapter}*\n━━━━━━━━━━━━━━━━━━━━\nMata duree filadhaa:",
        "study_input_choice": "📚 *Galmee Meeshaa Qo'annoo*\n━━━━━━━━━━━━━━━━━━━━\nFilannoo: *{subject}*\n\nHaala kamiin dhiheessuu barbaaddu?",
        "study_btn_upload_file": "📎 Faayilii / PDF Ol-kaasi",
        "study_btn_text_desc": "✍️ Ibsa Barreeffamaa Galchi",
        "study_ask_text": "✍️ *Ibsa Barreeffamaa*\n━━━━━━━━━━━━━━━━━━━━\nIbsa mata duree ykn gaaffii keessan galchaa:",
        "study_ask_file": "📎 *Faayilii / PDF Ol-kaasuu*\n━━━━━━━━━━━━━━━━━━━━\nSanada PDF ykn suuraa yaadannoo keessanii ergaa:",
        "study_intro_thinking": "🤔 Seensa barnootaa qopheessaa jira...",
        "study_stopped": "⏹️ *Qo'annoon Dhaabbateera*\n━━━━━━━━━━━━━━━━━━━━\nHaasawa idileetti deebi'aniiru.",
        "no_active_session": "📚 Yeroo ammaa qo'annoon eegalame hin jiru.\n\nJalqabuuf /study fayyadamaa.",
        "current_session_title": "📚 *Qo'annoo Ammaa*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *Kutaa:* {grade}\n{emoji} *Gosa:* {subject}\n📌 *Mata Duree:* {topic}\n🔄 *Sadarkaa:* {stage}",
        "current_session_quiz_active": "📚 *Qo'annoo Ammaa (Qormaanni Hojjataa Jira)*\n━━━━━━━━━━━━━━━━━━━━\n🎓 *Kutaa:* {grade}\n{emoji} *Gosa:* {subject}\n📌 *Mata Duree:* {topic}",

        # PDF Study
        "pdf_welcome": "📄 *PDF irraa Qo'achuu*\n━━━━━━━━━━━━━━━━━━━━\nSanada PDF keessan ol-kaasaa (Hanga 20 MB).",
        "pdf_processing": "⏳ PDF dubbisuu fi qabxiiwwan baasaa jira...",
        "pdf_ready": "📄 *Sanadni PDF Qophaa'eera!*\n━━━━━━━━━━━━━━━━━━━━\n📌 Mata Duree: *{title}*\n📑 Fuula: *{pages}*",
        "pdf_btn_learn": "📖 PDF irraa Bari",
        "pdf_btn_ask": "💬 Gaaffii Gaafadhu",
        "pdf_btn_quiz": "❓ Gaaffilee Qori",
        "pdf_btn_test": "📝 Qormaata Yaali",
        "pdf_btn_summary": "📑 Cuunfaa Argadhu",
        "pdf_ask_prompt": "💬 *PDF Gaafadhu*\n━━━━━━━━━━━━━━━━━━━━\nGaaffii waa'ee *{title}* qabdan kamiyyuu gaafadhaa:",
        "pdf_ask_upload": "📄 *Qo'annoo PDF*\n━━━━━━━━━━━━━━━━━━━━\nQo'achuuf mee sanada PDF ergaa.",
        "pdf_invalid_type": "❌ Mee faayilii PDF (.pdf) sirrii ergaa.",
        "pdf_size_error": "❌ Faayiliin baay'ee guddaadha. Hangi heyyamame {max_size} MB qofa.",
        "pdf_analyzed_title": "📄 *Sanada Qophaa'e: {title}*\n━━━━━━━━━━━━━━━━━━━━\n📑 Fuula: {pages}\n\n📋 *Boqonnaalee:*\n{topics}\n\n📖 *Cuunfaa:*\n{summary}",
        "pdf_ask_question_prompt": "💬 *Sanada Irraa Gaafadhaa: {title}*\n━━━━━━━━━━━━━━━━━━━━\nGaaffii keessan barreessaa:",
        "pdf_answer_header": "📖 *Deebii Sanada Irraa:*\n━━━━━━━━━━━━━━━━━━━━\n{answer}",
        "pdf_empty_error": "❌ Gaaffii keessaniif sanada keessaa deebii argachuun hin danda'amne.",

        # Materials Library
        "materials_title": "📎 *Kuusaa Sanadoota Koo*\n━━━━━━━━━━━━━━━━━━━━\nSanadoota keessan:",
        "materials_empty": "📎 Hamma yoonaatti sanada hin ol-kaasne.",
        "materials_deleted": "✅ Sanadni haqameera.",
        "materials_activated": "✅ Sanadni kun qo'annoof filatameera!",

        # Quiz
        "quiz_no_session": "📚 Qo'annoon jalqabame hin jiru.",
        "quiz_generating": "⏳ Hojjechaa jira, mee xiqqoo eegaa...",
        "quiz_mode_title": "❓ *Qormaanni Eegalame*\n━━━━━━━━━━━━━━━━━━━━\n📚 Gosa: *{subject} → {topic}*",
        "quiz_active_prompt": "❓ *Qormaanni hojjachaa jirtan jira!*\nGaaffii {current} keessaa {total}።",
        "quiz_question_header": "━━━━━━━━━━━━━━━━━━━━\n{emoji} *{topic} — Qormaata*\n━━━━━━━━━━━━━━━━━━━━\n📝 Gaaffii *{num}* / *{total}*\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━\n🇦  {opt_a}\n🇧  {opt_b}\n🇨  {opt_c}\n🇩  {opt_d}",
        "quiz_correct": "✅ *Sirrii dha!*",
        "quiz_incorrect": "❌ *Dogoggora.*",
        "quiz_correct_reveal": "\n❗ *Deebii Sirrii:* {correct_key}. {correct_text}\n",
        "quiz_complete_title": "━━━━━━━━━━━━━━━━━━━━\n🎉 *Qormaanni Xumurameera!*\n━━━━━━━━━━━━━━━━━━━━\n{emoji} *{subject} → {topic}*\n\n📊 *Bu'aa:*\n   ✅ Sirrii: *{score}*\n   ❌ Dogoggora: *{incorrect}*\n   💯 Qabxii: *{score}/{total} — {pct}%*",

        # Written Test
        "test_title": "━━━━━━━━━━━━━━━━━━━━\n📝 *Qormaata Barreeffamaa*\n━━━━━━━━━━━━━━━━━━━━\n📚 Gosa: *{subject} → {topic}*\n\nGaaffilee 3 armaan gadii ergaa tokkoon deebisaa:\n\n━━━━━━━━━━━━━━━━━━━━\n{questions}",
        "test_grading_title": "━━━━━━━━━━━━━━━━━━━━\n💯 *Bu'aa Qormaataa fi Gamaaggama*\n━━━━━━━━━━━━━━━━━━━━\n{result}",
        "test_evaluating": "⏳ Hojjechaa jira, mee xiqqoo eegaa...",
        "test_history_title": "📝 *Qormaatawwan Kanaan Duraa*\n━━━━━━━━━━━━━━━━━━━━",

        # Short Notes
        "notes_title": "━━━━━━━━━━━━━━━━━━━━\n📖 *Yaadannoo Gabaabaa*\n━━━━━━━━━━━━━━━━━━━━\n📚 *{subject} → {topic}*\n\n{content}",
        "notes_generating": "⏳ Hojjechaa jira, mee xiqqoo eegaa...",

        # Progress
        "progress_title": "📊 *Guddina Barnoota Koo*\n━━━━━━━━━━━━━━━━━━━━\n👤 Barataa: *{name}*\n🎓 Kutaa: *{grade}*\n🌐 Afaan: *{language}*\n\n📚 *Istaatistiksii:*\n• 📖 Barnoota Jalqabaman: *{lessons_count}*\n• ❓ Gaaffilee Qoraman: *{quizzes_count}*\n• 🎯 Qabxii Giddu-galeessaa: *{quiz_avg_pct}%*\n• 📝 Qormaata Barreeffamaa: *{tests_count}*\n• 📄 Sanadoota PDF: *{pdf_count}*",

        # Profile
        "profile_title": "👤 *Piroofayilii Barataa*\n━━━━━━━━━━━━━━━━━━━━\n👤 Maqaa: *{name}*\n📱 Bilbila: `{phone}`\n🆔 Telegram ID: `{telegram_id}`\n🎓 Kutaa: *{grade}*\n🌐 Afaan: *{language}*\n📚 Koorsoota Galmaa'an:\n{courses}\n📅 Guyyaa Galmee: *{registered_date}*",
        "profile_btn_change_grade": "🎓 Kutaa Jijjiiri",
        "profile_btn_change_lang": "🌐 Afaan Jijjiiri",

        # AI Tutor / Chat
        "tutor_thinking": "⏳ Hojjechaa jira, mee xiqqoo eegaa...",
        "ai_error": "⚠️ *Dogoggora Wal-qunnamtii*\n━━━━━━━━━━━━━━━━━━━━\nAmma AI wajjin wal-qunnamuu hin dandeenye. Mee daqiiqaa muraasa booda irra deebiin yaalaa.",

        # Help
        "help_title": "❓ *Ethio Smart Study — Qajeelfama Fayyadamaa*\n━━━━━━━━━━━━━━━━━━━━\nBaga nagaan gara Barsiisaa AI dhuftan!",

        # National Exam Prep
        "exam_locked_card": "🔒 *Paakeejii Qophii Qormaata Biyyooleessaa*\n━━━━━━━━━━━━━━━━━━━━\nQophiin Qormaata Biyyooleessaa qormaata Ministeeraa Kutaa 6ffaa, 8ffaa fi 12ffaatif kan qophaa'edha.\n\n✨ *Faayidaalee Inni Qabu:*\n• Gaaffilee Qormaata Biyyooleessaa dhugaati fi Modeela\n• Irra Deebii Kutaa 5-6, 7-8, fi 9-12 Guutuu\n• Qormaata Boqonnaa fi Baayyina Gaaffiin Filatamu\n• Xiinxala Qabxii fi Sammoo Qormaataa\n\nOddeeffannoo dabalataaf ykn Paakeejii kana banachuuf deeggarsa qunnamaa:\n• 💬 Telegram: [@Cs1At07](https://t.me/Cs1At07)\n• 📱 Bilbila: `0928892344`",
        "exam_ask_subject": "🎓 *Shaakala Qormaata Biyyooleessaa*\n━━━━━━━━━━━━━━━━━━━━\nGosa barnootaa shaakaluu barbaaddan filadhaa:",
        "exam_ask_scope": "📚 *Daangaa Qormaataa Filadhaa*\n━━━━━━━━━━━━━━━━━━━━\nBarnoota: *{subject}*\n\nBoqonnaa muraasa ykn Qormaata Biyyooleessaa Guutuu filadhaa:",
        "exam_ask_qcount": "🔢 *Baayyina Gaaffii Filadhaa*\n━━━━━━━━━━━━━━━━━━━━\nBarnoota: *{subject}*\nDaangaa: *{scope}*\n\nGaaffii meeqa shaakaluu barbaaddu?",

        # Feedback
        "feedback_ask": "💬 *Yaada fi Yaada Barattootaa*\n━━━━━━━━━━━━━━━━━━━━\nBota keenya caalaatti fooyyessuuf yaadni keessan nuuf baay'ee murteessaadha!\n\nMee yaada ykn yaada keessan armaan gadiitti barreessaa (ykn suuraa/sanada ergaa):",
        "feedback_thanks": "✅ *Yaada Keessaniif Galatoomaa!*\n━━━━━━━━━━━━━━━━━━━━\nYaadni keessan karaa milkaa'inaan chaanaalii yaada keenyaatti ergameera.\nBota keenya fooyyessuuf gumaacha gootaniif galatoomaa! 🤍",

        # Free Trial
        "trial_ask_grade": "🎁 *Shaakala AI Yaalii Bilisaa 1-Yeroo*\n━━━━━━━━━━━━━━━━━━━━\nOsoo hin galmaa'in gaaffilee AI 3 yaaluuf kutaa keessan filadhaa:",
        "trial_ask_subject": "🎁 *Barnoota Yaalii Filadhaa*\n━━━━━━━━━━━━━━━━━━━━\nKutaa: *Kutaa {grade}*\n\nGaaffilee 3 shaakaluuf barnoota filadhaa:",
        "trial_already_used": "⚠️ *Daangaan Yaalii Bilisaa Xumurameera*\n━━━━━━━━━━━━━━━━━━━━\nYaalii bilisaa yeroo 1 xumurtaniiltu.\n\nTajaajila AI guutuu argachuuf mee /start cuqaasuun galmaa'aa!",
        "trial_complete_card": "🎉 *Shaakalli Yaalii Xumurameera!*\n━━━━━━━━━━━━━━━━━━━━\nQabxii: *{score}/{total} ({pct}%)*\n\n✨ *Tajaajila Guutuu Banadhaa:*\n• Barsiisaa AI fi Qo'annoo Daangaa Malee\n• Yaadannoo Gababaa fi PDF dubbisuu\n• Qormaata Biyyooleessaa Shaakaluu\n\nAkkaawuntii keessan banachuuf /start cuqaasaa!",

        # Admin
        "admin_only_error": "❌ Gocha kana raawwachuuf heeyyama hin qabdan.",
        "admin_dashboard_title": "🛡️ *Fuula To'annoo Bulchaa*\n━━━━━━━━━━━━━━━━━━━━\n💰 *Gatii Koorsootiin:* {price} ETB\n\n👥 *Haala Barattootaa:*\n• Barattoota Hunda: *{total}*\n• ✅ Eeyyamaman: *{approved}*\n• ⏳ Eegaa Jiran: *{pending}*\n• ❌ Kufaa Ta'an: *{rejected}*",
        "admin_btn_pricing": "💰 Gatii Koorsootaa",
        "admin_btn_pending": "⏳ Eegaa Jiran ({count})",
        "admin_btn_approved_list": "👥 Eeyyamaman",
        "admin_btn_rejected_list": "❌ Kufaa Ta'an",
        "admin_btn_search": "🔍 Barataa Barbaadi",
        "admin_btn_broadcast": "📢 Beeksisa Dabarsoo",
        "admin_btn_refresh": "🔄 Haaromsi",
        "admin_no_pending": "✅ Yeroo ammaa iyyannoon eegaa jiru hin jiru.",
    }
}

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Returns translated string formatted with kwargs.
    Falls back to English if key is missing in target language, or returns key if not found.
    """
    code = normalize_lang(lang)
    lang_dict = TRANSLATIONS.get(code, TRANSLATIONS["en"])
    template = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template

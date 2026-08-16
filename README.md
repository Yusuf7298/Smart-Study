# 🎓 Smart Study Bot — Production-Ready AI Telegram Tutor

Smart Study Bot is an intelligent, multilingual Telegram AI tutoring platform built with **Python**, **aiogram 3**, **Google Gemini GenAI SDK**, and **SQLite**. It offers structured tutoring, grounded PDF study, adaptive multiple-choice quizzes, written conceptual tests with AI grading, study materials management, and a comprehensive administrative dashboard.

---

## 🌟 Key Features

### 1. 🌐 Centralized Multilingual System (i18n)
- Native language support for:
  - 🇬🇧 **English** (`en`)
  - 🇪🇹 **አማርኛ / Amharic** (`am`)
  - 🟢 **Afaan Oromoo** (`om`)
- Controls menus, buttons, registration, approval alerts, study prompts, quiz cards, test grading, notes, progress, and PDF Q&A.

### 2. 🔐 Student Registration & Admin Approval Lifecycle
- `/start` triggers an interactive registration FSM:
  - Full Name → Grade (Grade 5 to University) → Preferred Language → Confirmation Summary → `PENDING`
- Administrators receive an instant approval card with one-tap `Approve` or `Reject` buttons.
- `ApprovalMiddleware` blocks unapproved/pending students from learning features while maintaining friendly guidance.

### 3. 🛡️ Administrator Control Center (`/admin`)
- Real-time dashboard showing total registered, approved, pending, and rejected students, alongside counters for lessons, quizzes, tests, and PDFs.
- **One-Tap Actions**:
  - `⏳ Pending`: Review and approve/reject applications.
  - `👥 Approved List`: View recent approved students.
  - `❌ Rejected List`: View rejected records with re-approval option.
  - `🔍 Student Search`: `/admin_search <name or ID>`
  - `📢 Broadcast`: `/broadcast <message>` to send paced announcements to all approved students.

### 4. 📚 Structured Study Mode (`/study`)
- Covers **Computer Science** (Python, JavaScript, HTML, CSS, C++, Java, Next.js), **Mathematics**, **Physics**, **Biology**, **Chemistry**, **Geography**, **English**, and **School Subjects**.
- Socratic teaching method: explains concepts, gives real-world examples, checks student understanding, and adapts dynamically to grade level.
- Multi-modal support: Provide study requirements via text or upload photos/documents.

### 5. 📄 PDF Study & Document Library (`/pdf`, `/materials`)
- **Document Processing**: Pure-Python `pypdf` extraction, size limits (<=20MB), path-traversal sanitization, and isolated user upload storage.
- **AI Document Analysis**: Extracts key topics and creates high-yield summaries on upload.
- **Grounded Q&A**: Answers questions grounded strictly in document text with intelligent chunking for large documents.
- **Study Materials Library (`/materials`)**: View, activate, and delete uploaded study materials.

### 6. 🧠 Interactive MCQ Quiz & 📝 Written Test
- **Quiz (`/quiz`)**: 5 adaptive questions with instant answer explanations, double-answer lockout, and progress tracking.
- **Written Test (`/test`)**: 3 conceptual questions evaluated by AI for score (0–10), letter grade (A+ to F), strengths, weaknesses, and corrections. Past results accessible via `/test_history`.

### 7. 📊 Learning Progress Dashboard (`/progress`)
- Live academic metrics aggregated from SQLite: lessons started, quiz counts, quiz average %, written test average score, PDFs uploaded, and active topic.

### 8. 🚦 Abuse Protection & Security
- `RateLimitMiddleware` enforces a per-user sliding window limit (20 requests / 60 seconds) with admin bypass.
- Path traversal prevention, safe parameter binding for all SQL queries, and zero hardcoded secrets.

---

## 🛠️ Project Structure

```text
├── bot/
│   ├── database/
│   │   ├── database.py           # SQLite initialization, schema, migrations
│   │   ├── models.py             # Dataclass models
│   │   └── repositories/         # Modular DB repositories (student, admin, materials, tests, quiz, learning, conv)
│   ├── handlers/
│   │   ├── start.py              # /start, /menu, /help, main dashboard
│   │   ├── registration.py       # Registration FSM & Admin alerts
│   │   ├── admin.py              # /admin, approval/rejection, search, broadcast
│   │   ├── profile.py            # /profile, grade & language switcher
│   │   ├── study.py              # /study, /current, topic selection
│   │   ├── pdf.py                # /pdf, grounded Q&A, PDF quiz/test
│   │   ├── materials.py          # /materials, material library & management
│   │   ├── quiz.py               # /quiz, adaptive MCQ flow
│   │   ├── actions.py            # /test, /test_history, /short_note, /personalize
│   │   ├── progress.py           # /progress academic dashboard
│   │   └── chat.py               # AI Tutor chat, /newchat, /clearchat, /cancel
│   ├── keyboards/                # Localized inline & reply keyboards
│   ├── middlewares/
│   │   ├── approval.py           # Registration & access control gatekeeper
│   │   └── ratelimit.py          # Sliding window rate limiter
│   └── services/
│       ├── gemini.py             # Google GenAI integration, fallback models, structured responses
│       ├── i18n.py               # Centralized 3-language translation dictionary
│       ├── pdf_service.py        # PDF extraction, chunking, retrieval
│       ├── storage.py            # StorageProvider abstraction (LocalStorageProvider)
│       └── progress_service.py   # Live analytics aggregator
├── data/
│   └── uploads/                  # User-isolated document storage
├── tests/
│   ├── test_tutor.py             # Core tutor and handler unit tests
│   └── test_production.py        # Comprehensive production integration tests
├── config.py                     # Environment variables, constants, subjects config
├── main.py                       # Application entrypoint & router dispatcher
├── requirements.txt              # Production dependencies
├── PRODUCTION_CHECKLIST.md       # Audit checklist & verification matrix
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Gemini API Key (from [Google AI Studio](https://aistudio.google.com/))

### 2. Installation
```bash
# Clone the repository
git clone <repository_url>
cd "Ai Bot"

# Create virtual environment
python -m venv .venv
# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration (`.env`)
Create a `.env` file in the root directory:
```env
BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
DATABASE_PATH=tutor_bot.db
ADMIN_IDS=8223004316
MAX_FILE_SIZE_MB=20
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
```

### 4. Running the Bot
```bash
python main.py
```

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
# Run all unit and integration tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run syntax compilation across all files
python -m compileall .
```

---

## 🛡️ Production Deployment & Maintenance

### Systemd Service (Linux Deployment)
Create `/etc/systemd/system/smartstudybot.service`:
```ini
[Unit]
Description=Smart Study Bot Telegram Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/smartstudybot
ExecStart=/opt/smartstudybot/.venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/smartstudybot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable smartstudybot
sudo systemctl start smartstudybot
```

### Database Backup
The SQLite database file `tutor_bot.db` contains all tables. Backup using:
```bash
sqlite3 tutor_bot.db ".backup 'backup_$(date +%Y%m%d_%H%M%S).db'"
```

---

## 📋 Available Commands

| Command | Description |
|---|---|
| `/start` | Launch registration or open main dashboard |
| `/menu` | Open interactive main menu |
| `/study` | Select subject, topic, and enter study mode |
| `/pdf` | Upload and study from PDF documents |
| `/materials` | Manage uploaded study documents |
| `/quiz` | Start 5-question adaptive multiple-choice quiz |
| `/test` | Take 3-question conceptual written test |
| `/test_history` | View previous written test evaluations |
| `/short_note` | Generate high-yield study summary notes |
| `/progress` | View comprehensive academic progress |
| `/profile` | Change grade or preferred language |
| `/current` | View currently active study session |
| `/cancel` | Cancel current quiz, session, or action |
| `/newchat` | Reset conversation history |
| `/admin` | Administrator control dashboard (Admin only) |
| `/broadcast <msg>` | Broadcast announcement to approved students (Admin only) |
| `/admin_search <q>` | Search students by name or ID (Admin only) |
| `/help` | View user guide in preferred language |

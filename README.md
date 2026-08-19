# 🎓 Ethio Smart Study Bot — Production Learning Platform

**Ethio Smart Study** is an AI-powered personalized educational and exam preparation platform on Telegram built with **Python 3.10+**, **aiogram 3**, **MongoDB Atlas**, and **Google Gemini API**. It provides step-by-step curriculum teaching, grounded PDF exam preparation, adaptive quizzes, written tests, and student progress tracking for Ethiopian students from Grade 1 to University in **English**, **Amharic (አማርኛ)**, and **Afaan Oromoo**.

---

## 🌟 System Architecture

```
🎓 ETHIO SMART STUDY BOT
        │
   Telegram Bot (aiogram 3)
        │
 ┌──────┼───────────────┐
 │      │               │
 ▼      ▼               ▼
MongoDB Atlas       Gemini API       File Storage Provider
────────────        ──────────       ─────────────────────
Students            Study content    PDFs (user-isolated)
Courses             Lesson gen       Payment receipts
Chapters            10 MCQs          Path traversal guard
Payments            Test grading     Size limits (20MB)
Pricing             Translations
Progress            Explanations
```

---

## 🚀 Key Platform Features

### 1. Student Registration & Onboarding (`/start`)
- **Profile Capture**: Full Name, Phone Number (via Telegram Contact button or text input), Grade Level (1–12, College, University), and Preferred Language (**English**, **አማርኛ**, **Afaan Oromoo**).
- **Interactive Multi-Subject Picker**: Select multiple courses with dynamic inline checkbox buttons (`[✅ Biology]`, `[⬜ Physics]`, `[➡️ Continue (1 selected)]`).
- **Automated Fee Calculation**: Automatically calculates `Total = Enrolled Courses × Price ETB`.

### 2. Dynamic Pricing & Course Payments
- **Dynamic Pricing**: Configurable by administrators anytime in MongoDB Atlas via `/admin_pricing` (Default: `50 ETB` per course).
- **Payment Credentials**:
  - **Account Owner**: `Yusuf Mohammed`
  - **Commercial Bank of Ethiopia (CBE)**: `1000359254718`
  - **Telebirr**: `0928892344`
- **Receipt Screenshot Verification**: Students upload payment receipt photos. The bot securely saves receipts and forwards them to all `ADMIN_IDS` with instant `[✅ Approve]` and `[❌ Reject]` buttons.

### 3. Server-Side Access Control & Gating
- Strict middleware restricts paid learning features until the administrator verifies payment and sets status to `APPROVED`.
- `/study` and `/menu` present **only enrolled and paid courses**.

### 4. 📄 PDF Final Exam Study Mode (`/pdf`)
- Upload lecture slides or textbook chapters.
- **Source-Only Grounding**: The internal tutoring instruction ensures learning is grounded *strictly* in the uploaded material without outside hallucinations:
  > *"Let's study together, starting from Chapter {chapter_number} in {file_name}. I am studying for my final exam. We will study step by step... Follow ONLY the attached study material..."*
- **6-Step Study Cycle**:
  1. **Short Notes**: High-yield definitions, concepts, and formulas.
  2. **10 Grounded MCQs**: Generated strictly from the text with A, B, C, D options.
  3. **Student Answers**: Submit formatted answers (e.g. `1-A, 2-C, 3-B...`).
  4. **AI Checks Answers**: Instant scoring and explanation of mistakes.
  5. **Score Summary**: Performance evaluation.
  6. **Next Topic**: Progression to the next logical topic in the document.

### 5. Adaptive Quizzes (`/quiz`), Written Tests (`/test`), & Short Notes (`/short_note`)
- 5-MCQ interactive quizzes per topic.
- 3-Question written conceptual tests graded by AI with letter grades and step-by-step feedback.
- High-yield summary notes tailored to student grade level.

---

## 🗄️ MongoDB Atlas Collections

The platform utilizes 16 collections:
1. `students` — User profiles, registration, phone, enrolled courses, and approval status.
2. `courses` — Curriculum course catalog.
3. `subjects` — Subject classifications.
4. `chapters` — Structured chapter listings.
5. `study_materials` — Uploaded PDF text, summaries, and detected topics.
6. `payments` — Student fee calculations, course lists, and status.
7. `payment_receipts` — Uploaded receipt images and audit links.
8. `learning_sessions` — Active study sessions and learning stages.
9. `quiz_sessions` — 5-MCQ active sessions and scores.
10. `quiz_questions` — Individual quiz questions and options.
11. `quiz_results` — Historical quiz performance records.
12. `test_results` — Written test evaluations and feedback.
13. `progress` — Student mastery, accuracy metrics, weak/strong topics.
14. `conversations` — Chat history memory.
15. `admin_logs` — Action audit logs for approvals, rejections, and pricing changes.
16. `pricing` — Historical and active course pricing versions.

---

## ⚙️ Installation & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Yusuf7298/Smart-Study.git
cd Smart-Study

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
Key configuration parameters:
- `BOT_TOKEN`: From Telegram [@BotFather](https://t.me/BotFather)
- `GEMINI_API_KEY`: From [Google AI Studio](https://aistudio.google.com/)
- `MONGO_URI`: MongoDB Atlas connection URI (`mongodb+srv://...`)
- `ADMIN_IDS`: Numeric Telegram IDs of administrators

---

## 🧪 Testing & Verification

Run the comprehensive unit and integration test suite:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Audit callbacks and commands:
```bash
python tests/audit_callbacks.py
```

Validate compilation:
```bash
python -m compileall bot main.py config.py tests
```

---

## 🚀 Deployment Options

### Option A: Docker Compose (Recommended)
Deploying with Docker provides isolated environments, automatic restart policies, and persistent storage:

```bash
# 1. Clone repository & configure environment
git clone https://github.com/Yusuf7298/Smart-Study.git
cd Smart-Study
cp .env.example .env
nano .env  # Add your BOT_TOKEN, GEMINI_API_KEY, MONGO_URI, ADMIN_IDS

# 2. Build and start the container in detached mode
docker compose up -d --build

# 3. View live logs
docker compose logs -f

# 4. Stop or restart
docker compose restart
docker compose down
```

---

### Option B: Linux VPS with Systemd (Ubuntu / Debian)
For dedicated or virtual servers (DigitalOcean, Hetzner, AWS EC2, Linode):

```bash
# 1. Setup system dependencies and Python 3.11+
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. Clone repo and setup virtualenv
git clone https://github.com/Yusuf7298/Smart-Study.git /home/ubuntu/Ethio-Smart-Study
cd /home/ubuntu/Ethio-Smart-Study
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
nano .env

# 4. Install & Enable Systemd Service
sudo cp ethio-smart-study.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ethio-smart-study
sudo systemctl start ethio-smart-study

# 5. Monitor service
sudo systemctl status ethio-smart-study
sudo journalctl -u ethio-smart-study -f
```

---

### Option C: Cloud PaaS (Render / Railway / Fly.io)
1. Fork or push the repo to GitHub.
2. Create a new **Background Worker** or **Web Service** in Render / Railway.
3. Select **Docker** deployment or **Python 3.11** runtime.
4. Set the Start Command: `python main.py`.
5. Add all Environment Variables from `.env` in the dashboard secrets tab.

---

## 👥 Support & Contact
- **Owner**: Yusuf Mohammed
- **Telegram Support**: [@Cs1At07](https://t.me/Cs1At07)
- **Phone**: `0928892344`


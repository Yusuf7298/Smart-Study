import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "tutor_bot.db")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

raw_admins = os.getenv("ADMIN_IDS", "8223004316")
ADMIN_IDS = []
for x in raw_admins.split(","):
    x_clean = x.strip()
    if x_clean.isdigit():
        ADMIN_IDS.append(int(x_clean))
if not ADMIN_IDS:
    ADMIN_IDS = [8223004316]

# File and Rate Limit Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "data", "uploads"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Socials & Islamic Reminders Configuration
SOCIALS_INFO = (
    "🌟 Follow for more Islamic reminders:\n\n"
    "Telegram: [Yusuf Moh](https://t.me/yusufcodes)\n"
    "LinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\n"
    "Instagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n"
    "May Allah reward you 🤍"
)

# Support & Contact Configuration
SUPPORT_INFO = (
    "📞 *Support & Contact Information*\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "For inquiries, help, or technical support:\n\n"
    "• 💬 Telegram: [Cs1At07](https://t.me/Cs1At07)\n"
    "• 📱 Phone: `0928892344`\n\n"
    "We are here to assist you anytime! 🎓"
)

# Centralized Subjects & Topics Configuration
SUBJECTS = {
    "Computer Science": {
        "emoji": "💻",
        "topics": [
            "🐍 Python",
            "🎨 CSS",
            "💛 JavaScript",
            "🌐 HTML",
            "➕ C++",
            "☕ Java",
            "🚀 Next.js",
            "📝 Other"
        ]
    },
    "Mathematics": {
        "emoji": "🧮",
        "topics": [
            "🔢 Algebra",
            "📐 Geometry",
            "📈 Trigonometry",
            "∫ Calculus",
            "📊 Statistics & Probability",
            "📝 General Math"
        ]
    },
    "Physics": {
        "emoji": "⚛️",
        "topics": [
            "🚗 Classical Mechanics",
            "🔥 Thermodynamics",
            "⚡ Electricity & Magnetism",
            "💡 Optics & Waves",
            "🌌 Modern Physics"
        ]
    },
    "Biology": {
        "emoji": "🧬",
        "topics": [
            "🔬 Cell Biology",
            "🧬 Genetics & DNA",
            "🫀 Human Physiology",
            "🌿 Ecology & Plants",
            "🦕 Evolution & Diversity"
        ]
    },
    "Chemistry": {
        "emoji": "🧪",
        "topics": [
            "⚛️ Atomic Structure",
            "🔗 Chemical Bonding",
            "⚗️ Organic Chemistry",
            "⚖️ Stoichiometry",
            "🧪 Acids, Bases & Salts"
        ]
    },
    "Geography": {
        "emoji": "🌍",
        "topics": [
            "🏔️ Physical Geography",
            "🌦️ Climate & Weather",
            "🗺️ Cartography & Maps",
            "🏙️ Human & Economic Geography",
            "🌱 Environmental Studies"
        ]
    },
    "English": {
        "emoji": "📖",
        "topics": [
            "📝 English Grammar",
            "📚 Vocabulary & Idioms",
            "📖 Reading Comprehension",
            "✍️ Essay & Creative Writing",
            "🎭 World Literature"
        ]
    },
    "School Subjects": {
        "emoji": "🏫",
        "topics": [
            "⚛️ Physics",
            "🧬 Biology",
            "🧪 Chemistry",
            "🌍 Others"
        ]
    }
}

def validate_environment() -> None:
    """Validates that all required environment variables and secrets are populated before startup."""
    errors = []
    if not BOT_TOKEN or BOT_TOKEN.startswith("your_"):
        errors.append("BOT_TOKEN is missing or set to placeholder. Please configure BOT_TOKEN in .env.")
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
        errors.append("GEMINI_API_KEY is missing or set to placeholder. Please configure GEMINI_API_KEY in .env.")
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is not configured. Please specify at least one numeric admin ID in .env.")
        
    if errors:
        for err in errors:
            logging.error(f"[CONFIG ERROR] {err}")
        raise ValueError("\n".join(errors))
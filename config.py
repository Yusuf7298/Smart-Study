import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = os.getenv("BOT_NAME", "Ethio Smart Study")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MONGO_URI = os.getenv("MONGO_URI", "") or os.getenv("MONGODB_URI", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ethio_smart_study")
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
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "data", "uploads"))
PAYMENT_RECEIPTS_DIR = os.getenv("PAYMENT_RECEIPTS_DIR", os.path.join(os.getcwd(), "data", "receipts"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

DEFAULT_PRICE_PER_COURSE_ETB = int(os.getenv("PRICE_PER_COURSE_ETB", "50"))
PAYMENT_OWNER_NAME = os.getenv("PAYMENT_OWNER_NAME", "Yusuf Mohammed")
PAYMENT_CBE_ACCOUNT = os.getenv("PAYMENT_CBE_ACCOUNT", "1000359254718")
PAYMENT_TELEBIRR_PHONE = os.getenv("PAYMENT_TELEBIRR_PHONE", "0928892344")
PAYMENT_CHANNEL_ID = os.getenv("PAYMENT_CHANNEL_ID", "")
FEEDBACK_CHANNEL_ID = os.getenv("FEEDBACK_CHANNEL_ID", os.getenv("PAYMENT_CHANNEL_ID", ""))

SOCIALS_INFO = (
    "🌟 Follow for more Islamic reminders:\n\n"
    "Telegram: [Yusuf Moh](https://t.me/yusufcodes)\n"
    "LinkedIn: [Yusuf Mohammed](https://www.linkedin.com/in/yusuf-mohammed-5272572b6)\n"
    "Instagram: [Yusuf Mohammed](https://instagram.com/kebilad_7488)\n\n"
    "May Allah reward you 🤍"
)

SUPPORT_INFO = (
    "📞 Support & Contact Information\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "For inquiries, help, or technical support:\n\n"
    "• 💬 Telegram: [Cs1At07](https://t.me/Cs1At07)\n"
    "• 📱 Phone: `0928892344`\n\n"
    "We are here to assist you anytime! 🎓"
)

from typing import Optional, List, Dict, Any

SUBJECTS = {
    "English": {
        "emoji": "📖",
        "topics": [
            "📝 English Grammar",
            "📚 Vocabulary & Idioms",
            "📖 Reading Comprehension",
            "✍️ Essay & Creative Writing",
            "🎭 World Literature & Communication"
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
    "Mathematics (Natural Science)": {
        "emoji": "🧮",
        "topics": [
            "🔢 Advanced Algebra & Functions",
            "📈 Trigonometry & Vector Analysis",
            "∫ Differential & Integral Calculus",
            "📊 Probability & Statistics",
            "📐 Analytical Geometry"
        ]
    },
    "Mathematics (Social Science)": {
        "emoji": "🧮",
        "topics": [
            "🔢 Commercial Arithmetic & Algebra",
            "📈 Financial Mathematics & Interest",
            "📊 Applied Statistics & Data Analysis",
            "📐 Coordinate Geometry",
            "✍️ Matrices & Linear Programming"
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
    "History": {
        "emoji": "📜",
        "topics": [
            "🇪🇹 Ethiopian & Horn of Africa History",
            "🌍 African & World Civilizations",
            "⚔️ World Wars & Modern Era",
            "🏛️ Ancient Civilizations & Heritage"
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
    "Economics": {
        "emoji": "📊",
        "topics": [
            "📈 Microeconomics & Market Dynamics",
            "🏦 Macroeconomics & Fiscal Policy",
            "🌍 Ethiopian Economy & Development",
            "💵 Money, Banking & International Trade"
        ]
    },
    "Citizenship Education": {
        "emoji": "⚖️",
        "topics": [
            "🏛️ Constitutional Democracy & Governance",
            "⚖️ Rule of Law & Human Rights",
            "🤝 Ethics, Patriotism & Civic Duty",
            "🌍 Global Citizenship & International Relations"
        ]
    },
    "Civics": {
        "emoji": "⚖️",
        "topics": [
            "🏛️ Constitutional Democracy & Governance",
            "⚖️ Rule of Law & Human Rights",
            "🤝 Ethics, Patriotism & Civic Duty",
            "🌍 Global Citizenship & International Relations"
        ]
    },
    "Information Technology (IT)": {
        "emoji": "💻",
        "topics": [
            "💻 Fundamentals of IT & Hardware",
            "🌐 Networking & Web Technologies",
            "🐍 Programming Basics & Algorithms",
            "🗄️ Database Management Systems",
            "🛡️ Cybersecurity & Ethics"
        ]
    },
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
    "Health and Physical Education (HPE)": {
        "emoji": "🏃",
        "topics": [
            "🏃 Physical Fitness & Athletics",
            "🥗 Nutrition & Personal Health",
            "🫀 Human Anatomy & Exercise Science",
            "⚽ Sports Skills & Teamwork",
            "🧘 Mental Health & Wellness"
        ]
    },
    "National/Regional Language": {
        "emoji": "🗣️",
        "topics": [
            "📝 Grammar & Language Structure",
            "📚 Reading Comprehension & Literature",
            "✍️ Creative & Expository Writing",
            "🗣️ Oral Communication & Culture"
        ]
    },
    "Agriculture": {
        "emoji": "🌾",
        "topics": [
            "🌾 Crop Science & Soil Fertility",
            "🐄 Animal Husbandry & Production",
            "🚜 Farm Tools & Mechanization",
            "🌲 Forestry & Natural Resource Management",
            "📈 Agribusiness & Agricultural Economics"
        ]
    },
    "Environmental Science": {
        "emoji": "🌱",
        "topics": [
            "🌱 Living Things & Ecosystems",
            "💧 Water & Natural Resources",
            "🌦️ Weather & Climate Change",
            "🧹 Environmental Hygiene & Conservation"
        ]
    },
    "Social Studies": {
        "emoji": "🗺️",
        "topics": [
            "🏔️ Local & Regional Geography",
            "📜 History of Our Community",
            "🏛️ Culture & Society",
            "🏙️ Community Services & Livelihood"
        ]
    },
    "Moral and Citizenship Education": {
        "emoji": "⚖️",
        "topics": [
            "🤝 Ethics, Moral Values & Respect",
            "⚖️ Rights & Responsibilities",
            "🕊️ Peace & National Unity",
            "🏛️ Civic Participation & Governance"
        ]
    },
    "Performing and Visual Arts (PVA)": {
        "emoji": "🎨",
        "topics": [
            "🎨 Drawing, Painting & Visual Arts",
            "🎵 Music & Cultural Songs",
            "🎭 Theatre, Drama & Dance",
            "🏺 Traditional Crafts & Design"
        ]
    },
    "General Science": {
        "emoji": "🔬",
        "topics": [
            "🔬 Foundational Biology & Cells",
            "⚗️ Basic Chemistry & Matter",
            "⚛️ Introductory Physics & Energy",
            "🌿 Ecosystems & Natural Systems"
        ]
    },
    "Career and Technical Education (CTE)": {
        "emoji": "🛠️",
        "topics": [
            "🛠️ Introduction to Technical Skills",
            "💼 Business & Entrepreneurship Basics",
            "🌾 Agricultural & Vocational Arts",
            "🖥️ Digital & Practical Work Skills"
        ]
    }
}

STREAMS = {
    "Natural Science": {
        "emoji": "🔬",
        "name": "Natural Science",
        "subjects": [
            "English",
            "Mathematics (Natural Science)",
            "Physics",
            "Chemistry",
            "Biology",
            "Information Technology (IT)",
            "Agriculture"
        ]
    },
    "Social Science": {
        "emoji": "📜",
        "name": "Social Science",
        "subjects": [
            "English",
            "Mathematics (Social Science)",
            "History",
            "Geography",
            "Economics",
            "Citizenship Education",
            "Information Technology (IT)"
        ]
    }
}

GRADE_5_6_SUBJECTS = [
    "English",
    "Mathematics",
    "Environmental Science",
    "Social Studies",
    "Moral and Citizenship Education",
    "Performing and Visual Arts (PVA)",
    "Health and Physical Education (HPE)",
    "National/Regional Language"
]

GRADE_7_8_SUBJECTS = [
    "English",
    "Mathematics",
    "General Science",
    "Social Studies",
    "Citizenship Education",
    "Career and Technical Education (CTE)",
    "Performing and Visual Arts (PVA)",
    "Health and Physical Education (HPE)",
    "Information Technology (IT)",
    "National/Regional Language"
]

GRADE_9_10_SUBJECTS = [
    "English",
    "Mathematics",
    "Physics",
    "Chemistry",
    "Biology",
    "History",
    "Geography",
    "Economics",
    "Citizenship Education",
    "Information Technology (IT)",
    "Health and Physical Education (HPE)",
    "National/Regional Language"
]

EXAM_BUNDLE_GRADES = {
    "6": ["5", "6"],
    "8": ["7", "8"],
    "12": ["9", "10", "11", "12"]
}

def get_exam_review_grades(grade: Optional[str]) -> List[str]:
    grade_str = str(grade).strip() if grade else ""
    return EXAM_BUNDLE_GRADES.get(grade_str, [grade_str] if grade_str else ["10"])

def get_curriculum_subjects(grade: Optional[str] = None, stream: Optional[str] = None) -> List[str]:
    if stream and stream in STREAMS:
        return STREAMS[stream]["subjects"]
    grade_str = str(grade).strip() if grade else ""
    if grade_str in ["11", "12"]:
        return STREAMS["Natural Science"]["subjects"]
    elif grade_str in ["9", "10"]:
        return GRADE_9_10_SUBJECTS
    elif grade_str in ["7", "8"]:
        return GRADE_7_8_SUBJECTS
    elif grade_str in ["5", "6"]:
        return GRADE_5_6_SUBJECTS
    elif grade_str in ["1", "2", "3", "4"]:
        return GRADE_5_6_SUBJECTS
    else:
        return GRADE_9_10_SUBJECTS

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
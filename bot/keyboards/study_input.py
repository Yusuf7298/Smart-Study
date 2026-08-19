from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_study_methods_keyboard(subject: str, lang: str = "English") -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✍️ 1. Topic / Short Description", callback_data=f"study_method_topic_{subject}")
        ],
        [
            InlineKeyboardButton(text="📸 2. Photo / Screenshot Upload", callback_data=f"study_method_photo_{subject}")
        ],
        [
            InlineKeyboardButton(text="📄 3. File / PDF Upload", callback_data=f"study_method_file_{subject}")
        ],
        [
            InlineKeyboardButton(text="🔙 Back to Subjects", callback_data="study_back_subjects"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="study_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_study_input_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="📎 Upload File + Description", callback_data="study_input_file")
        ],
        [
            InlineKeyboardButton(text="✍️ Add Text Description / Topic", callback_data="study_input_text")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_study_actions_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="❓ Quiz", callback_data="action_quiz"),
            InlineKeyboardButton(text="📝 Test", callback_data="action_test")
        ],
        [
            InlineKeyboardButton(text="📖 Short Note", callback_data="action_note"),
            InlineKeyboardButton(text="⚙️ Personalize", callback_data="action_personalize")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

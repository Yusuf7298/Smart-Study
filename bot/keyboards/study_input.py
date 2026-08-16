from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_study_input_keyboard() -> InlineKeyboardMarkup:
    """Returns an inline keyboard to choose how the student wants to provide study materials."""
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
    """Returns the persistent learning actions panel attached to lessons and chat responses."""
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

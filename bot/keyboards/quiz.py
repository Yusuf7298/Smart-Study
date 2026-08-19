from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_quiz_options_keyboard(session_id: int, question_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="🇦 A", callback_data=f"quiz_ans_{session_id}_{question_id}_A"),
            InlineKeyboardButton(text="🇧 B", callback_data=f"quiz_ans_{session_id}_{question_id}_B")
        ],
        [
            InlineKeyboardButton(text="🇨 C", callback_data=f"quiz_ans_{session_id}_{question_id}_C"),
            InlineKeyboardButton(text="🇩 D", callback_data=f"quiz_ans_{session_id}_{question_id}_D")
        ],
        [
            InlineKeyboardButton(text="🛑 End Test", callback_data=f"quiz_end_{session_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_quiz_active_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="▶️ Continue", callback_data="quiz_active_continue"),
            InlineKeyboardButton(text="❌ Cancel Quiz", callback_data="quiz_active_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

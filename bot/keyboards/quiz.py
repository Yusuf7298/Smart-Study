from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_quiz_options_keyboard(session_id: int, question_id: int) -> InlineKeyboardMarkup:
    """Returns 2x2 grid of option buttons for answering MCQs."""
    keyboard = [
        [
            InlineKeyboardButton(text="A", callback_data=f"quiz_ans_{session_id}_{question_id}_A"),
            InlineKeyboardButton(text="B", callback_data=f"quiz_ans_{session_id}_{question_id}_B")
        ],
        [
            InlineKeyboardButton(text="C", callback_data=f"quiz_ans_{session_id}_{question_id}_C"),
            InlineKeyboardButton(text="D", callback_data=f"quiz_ans_{session_id}_{question_id}_D")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_quiz_active_keyboard() -> InlineKeyboardMarkup:
    """Returns options to continue or cancel the active quiz."""
    keyboard = [
        [
            InlineKeyboardButton(text="▶️ Continue", callback_data="quiz_active_continue"),
            InlineKeyboardButton(text="❌ Cancel Quiz", callback_data="quiz_active_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

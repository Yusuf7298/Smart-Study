import re
import logging
from typing import Optional, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

# Map common math superscripts and subscripts to unicode
SUPERSCRIPTS = {
    "^0": "⁰", "^1": "¹", "^2": "²", "^3": "³", "^4": "⁴",
    "^5": "⁵", "^6": "⁶", "^7": "⁷", "^8": "⁸", "^9": "⁹",
    "^n": "ⁿ", "^x": "ˣ", "^y": "ʸ", "^+": "⁺", "^-": "⁻"
}
SUBSCRIPTS = {
    "_0": "₀", "_1": "₁", "_2": "₂", "_3": "₃", "_4": "₄",
    "_5": "₅", "_6": "₆", "_7": "₇", "_8": "₈", "_9": "₉",
    "_n": "ₙ", "_x": "ₓ", "_y": "ᵧ", "_i": "ᵢ", "_j": "ⱼ"
}

def clean_telegram_text(text: str) -> str:
    """
    Cleans raw AI markdown output into completely clean, natural text:
    - Completely removes all markdown hashtag headers (#, ##, ###, ####, #####).
    - Completely removes all asterisks (*, **, ***).
    - Converts list bullet markers (* item, - item) into clean unicode bullets (• item).
    - Converts raw LaTeX math ($r^3$, $x^2$) into clean unicode math (r³, x²).
    - Converts markdown rules (---, ___, ***) into clean dividers (━━━━━━━━━━━━━━━━━━━━).
    """
    if not text:
        return ""
        
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Convert markdown horizontal rules (---, ___, ***) to clean dividers
        if stripped in ["---", "___", "***", "----", "____", "*****"]:
            cleaned_lines.append("━━━━━━━━━━━━━━━━━━━━")
            continue
            
        # 2. Convert markdown headers (### Heading, #### Heading, etc.) to clean text without #
        if re.match(r"^#{1,6}\s+", stripped):
            header_text = re.sub(r"^#{1,6}\s+", "", stripped).strip()
            cleaned_lines.append(header_text)
            continue
            
        # 3. Convert markdown list bullets (* **Term:** or * Term or - Term) to clean unicode bullets (• Term:)
        if re.match(r"^\s*[\*\-]\s+\*\*(.*?)\*\*", line):
            line = re.sub(r"^\s*[\*\-]\s+\*\*(.*?)\*\*", r"• \1", line)
        elif re.match(r"^\s*[\*\-]\s+\*(.*?)\*", line):
            line = re.sub(r"^\s*[\*\-]\s+\*(.*?)\*", r"• \1", line)
        elif re.match(r"^\s*[\*\-]\s+", line):
            line = re.sub(r"^\s*[\*\-]\s+", r"• ", line)
            
        cleaned_lines.append(line)
        
    result = "\n".join(cleaned_lines)
    
    # 4. Convert superscripts & subscripts in math formulas
    for k, v in SUPERSCRIPTS.items():
        result = result.replace(k, v)
    for k, v in SUBSCRIPTS.items():
        result = result.replace(k, v)
        
    # 5. Clean LaTeX math delimiters ($formula$ -> formula)
    result = re.sub(r"\$\$([^\$\n]+)\$\$", r"\1", result)
    result = re.sub(r"\$([^\$\n]+)\$", r"\1", result)
    
    # 6. Completely strip any remaining asterisks (*) and hashtags (#)
    result = result.replace("*", "").replace("#", "")
    
    # 7. Collapse excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    
    return result.strip()

async def safe_reply(
    event: Union[Message, CallbackQuery],
    text: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    parse_mode: Optional[str] = "Markdown"
) -> Optional[Message]:
    """
    Safely sends a reply message with cleaned natural Telegram formatting.
    Falls back to plain text if Telegram fails to parse entities.
    """
    target = event.message if isinstance(event, CallbackQuery) else event
    if not target:
        return None

    clean_text = clean_telegram_text(text)

    # When all * and # are removed, we can send safely
    try:
        return await target.answer(clean_text, parse_mode=None, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in safe_reply: {e}")
        return None

async def safe_edit(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "Markdown"
) -> Optional[Message]:
    """
    Safely edits an existing message with cleaned natural Telegram formatting.
    """
    clean_text = clean_telegram_text(text)

    try:
        return await message.edit_text(clean_text, parse_mode=None, reply_markup=reply_markup) # type: ignore
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return message
        else:
            logging.error(f"TelegramBadRequest in safe_edit: {e}")
            return None
    except Exception as e:
        logging.error(f"Error in safe_edit: {e}")
        return None

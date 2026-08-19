import re
import html
import logging
from typing import Optional, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
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

def strip_all_formatting(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", "", text)
    t = t.replace("*", "").replace("#", "")
    return t.strip()

def markdown_to_telegram_html(text: str) -> str:
    if not text:
        return ""

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped in ["---", "___", "***", "----", "____", "*****"]:
            cleaned_lines.append("━━━━━━━━━━━━━━━━━━━━")
            continue

        if re.match(r"^#{1,6}\s+", stripped):
            header_text = re.sub(r"^#{1,6}\s+", "", stripped).strip()
            header_text = header_text.replace("**", "").replace("*", "")
            cleaned_lines.append(f"<b>{html.escape(header_text)}</b>")
            continue

        if re.match(r"^\s*[\*\-]\s+\*\*(.*?)\*\*", line):
            line = re.sub(r"^\s*[\*\-]\s+\*\*(.*?)\*\*", lambda m: f"• <b>{html.escape(m.group(1))}</b>", line)
        elif re.match(r"^\s*[\*\-]\s+\*(.*?)\*", line):
            line = re.sub(r"^\s*[\*\-]\s+\*(.*?)\*", lambda m: f"• <b>{html.escape(m.group(1))}</b>", line)
        elif re.match(r"^\s*[\*\-]\s+", line):
            line = re.sub(r"^\s*[\*\-]\s+", "• ", line)

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines)

    for k, v in SUPERSCRIPTS.items():
        result = result.replace(k, v)
    for k, v in SUBSCRIPTS.items():
        result = result.replace(k, v)
    result = re.sub(r"\$\$([^\$\n]+)\$\$", r"\1", result)
    result = re.sub(r"\$([^\$\n]+)\$", r"\1", result)
    result = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s\)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>',
        result
    )
    result = re.sub(r"`([^`\n]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", result)
    result = re.sub(r"\*\*\*([^\*\n]+)\*\*\*", lambda m: f"<b>{html.escape(m.group(1))}</b>", result)
    result = re.sub(r"\*\*([^\*\n]+)\*\*", lambda m: f"<b>{html.escape(m.group(1))}</b>", result)
    result = re.sub(r"\*([^\*\n]+)\*", lambda m: f"<b>{html.escape(m.group(1))}</b>", result)
    result = re.sub(r"_([^_	\n]+)_", lambda m: f"<i>{html.escape(m.group(1))}</i>", result)

    result = result.replace("*", "").replace("#", "")
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()

def clean_telegram_text(text: str) -> str:
    return markdown_to_telegram_html(text)

async def safe_reply(
    event: Union[Message, CallbackQuery],
    text: str,
    reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    parse_mode: Optional[str] = "HTML"
) -> Optional[Message]:
    target = event.message if isinstance(event, CallbackQuery) else event
    if not target:
        return None

    html_text = markdown_to_telegram_html(text)

    try:
        return await target.answer(html_text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest as e:
        logging.warning(f"HTML parse error in safe_reply, falling back to plain text: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await target.answer(plain, parse_mode=None, reply_markup=reply_markup)
        except Exception:
            return None
    except Exception as e:
        logging.error(f"Error in safe_reply: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await target.answer(plain, parse_mode=None, reply_markup=reply_markup)
        except Exception:
            return None

async def safe_edit(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "HTML"
) -> Optional[Message]:
    html_text = markdown_to_telegram_html(text)

    try:
        return await message.edit_text(html_text, parse_mode="HTML", reply_markup=reply_markup) # type: ignore
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return message
        logging.warning(f"HTML parse error in safe_edit, falling back to plain text: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await message.edit_text(plain, parse_mode=None, reply_markup=reply_markup) # type: ignore
        except Exception:
            return None
    except Exception as e:
        logging.error(f"Error in safe_edit: {e}")
        plain = strip_all_formatting(html_text)
        try:
            return await message.edit_text(plain, parse_mode=None, reply_markup=reply_markup) # type: ignore
        except Exception:
            return None

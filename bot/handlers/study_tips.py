import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services import student_service, learning_service
from bot.services.gemini import ask_gemini_with_profile
from bot.services.i18n import t
from bot.keyboards.study_tips import get_study_tips_keyboard
from bot.utils import safe_reply, safe_edit

router = Router()

class StudyTipsStates(StatesGroup):
    waiting_for_problem = State()

@router.message(Command("tips"))
@router.message(Command("study_tips"))
@router.message(Command("advice"))
@router.message(F.text.in_(["💡 Study Tips & Advice", "💡 Study Tips", "💡 የጥናት ምክሮች", "💡 Tarsa'aa Qo'annoo"]))
async def study_tips_command(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id if message.from_user else None
    student = await student_service.get_student(telegram_id) if telegram_id else None
    lang = student.preferred_language if student else "English"
    
    await safe_reply(
        message,
        t("study_tips_menu_title", lang),
        reply_markup=get_study_tips_keyboard(lang)
    )

@router.callback_query(F.data == "menu_study_tips", StateFilter(None))
async def menu_study_tips_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    await state.clear()
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await safe_edit(
        callback.message, # type: ignore
        t("study_tips_menu_title", lang),
        reply_markup=get_study_tips_keyboard(lang)
    )

@router.callback_query(F.data == "tips_cat_time")
async def tips_cat_time_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    if lang == "am":
        content = (
            "⏰ ውጤታማ የጊዜ አጠቃቀም እና የ Pomodoro ዘዴ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. ⏱️ የ Pomodoro ዘዴ (25/5 ህግ):\n"
            "• ለ25 ደቂቃ ያህል ስልክዎን ከጎንዎ በማራቅ ሙሉ በሙሉ በጥናትዎ ላይ ብቻ ያተኩሩ።\n"
            "• የ25 ደቂቃው ሲያልቅ የግዴታ የ5 ደቂቃ እረፍት ይውሰዱ (ተነስተው ውሃ ይጡ፣ ይዘረጋጉ)።\n"
            "• ይህን ዑደት 4 ጊዜ ከደገሙ በኋላ የ20–30 ደቂቃ ረጅም እረፍት ይውሰዱ። አእምሮዎ እንዳይደክም ይረዳል!\n\n"
            "2. 🗓️ የጊዜ ክፍፍል (Time-Blocking):\n"
            "• ከባድ ትምህርቶችን (ለምሳሌ፦ ሂሳብ ወይም ፊዚክስ) አእምሮዎ ትኩስ በሚሆንበት ጊዜ (ጠዋት ላይ) ያጠናሉ።\n"
            "• ቀላል የሆኑ የንባብ ትምህርቶችን ከሰዓት በኋላ ወይም ማታ ላይ ይመድቡ።\n\n"
            "3. 🎯 የ 80/20 ህግ (Pareto Principle):\n"
            "• 80% የሚሆነው የፈተና ውጤት የሚመጣው ከ 20% ዋና ዋና እና ተደጋጋሚ ርዕሶች ነው።\n"
            "• ሁልጊዜ ዋና ዋና ነጥቦችን እና ዋና መፈተኛ ርዕሶችን አስቀድመው ያጠናቅቁ።"
        )
    elif lang == "om":
        content = (
            "⏰ Bulchiinsa Yeroo fi Pomodoro\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. ⏱️ Malleen Pomodoro (Seera 25/5):\n"
            "• Daqiiqaa 25f bilbila keessan fageessuun xiyyeeffannoo guutuun qo'adhaa.\n"
            "• Daqiiqaa 25 erga xumurtanii booda boqonnaa daqiiqaa 5 fudhadhaa.\n"
            "• Adeemsa kana si'a 4 erga irra deddeebitanii booda boqonnaa dheeraa daqiiqaa 20–30 fudhadhaa!\n\n"
            "2. 🗓️ Qoodinsa Yeroo (Time-Blocking):\n"
            "• Barnoota cimaa (fakkeenyaaf Hiisaaba ykn Fiziksii) ganama yeroo sammuun keessan qulqulluu ta'etti qo'adhaa.\n\n"
            "3. 🎯 Seera 80/20:* Barnoota keessaa mata dureewwan ijoo qormaata irratti irra deddeebiin dhufan irratti dursa dhiyeessaa."
        )
    else:
        content = (
            "⏰ Mastering Time Management & The Pomodoro Technique\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. ⏱️ The 25/5 Pomodoro Cycle:\n"
            "• Study with 100% laser focus for 25 minutes (put phone away!).\n"
            "• Take a mandatory 5-minute break (stretch, drink water).\n"
            "• After 4 cycles, reward yourself with a 20-30 minute long break. This eliminates brain fatigue!\n\n"
            "2. 🗓️ Time-Blocking Strategy:\n"
            "• Schedule challenging subjects (Math, Physics, Chemistry) during peak energy hours (mornings).\n"
            "• Save lighter reading or review tasks for afternoon or evening blocks.\n\n"
            "3. 🎯 The 80/20 Pareto Rule:\n"
            "• 80% of exam score value comes from 20% of core high-yield concepts. Master fundamental definitions and formulas first!"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_study_tips")]
    ])
    await safe_reply(callback, content, reply_markup=kb)

@router.callback_query(F.data == "tips_cat_reading")
async def tips_cat_reading_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    if lang == "am":
        content = (
            "🧠 ንቁ ንባብ (Active Recall) እና Feynman ዘዴ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 🚫 መጽሐፍን ደጋግሞ የማንበብን ስህተት ያስወግዱ:\n"
            "• ገጽን 5 ጊዜ ማንበብ አእምሮን 'አውቀዋለሁ' የሚል ሀሰተኛ ስሜት ያሳስታል። በምትኩ እራስዎን መጠየቅ እና መፈተን 3 እጥፍ ያበልጻል!\n\n"
            "2. 💡 የ Feynman ዘዴ (Feynman Technique):\n"
            "• ያነበቡትን ከባድ ርዕስ ለ10 ዓመት ልጅ እንደሚያስረዱ አድርገው በቃላትዎ በከፍተኛ ድምጽ ያስረዱ።\n"
            "• የተሳሳቱበትን ወይም ያጠረዎትን ነጥብ መልሰው ከመጽሐፉ በማየት ይሙሉ።\n\n"
            "3. ✍️ የ Blurting ዘዴ:"
            "• ለ10 ደቂቃ ያህል አንድ ርዕስ ካነበቡ በኋላ መጽሐፉን ይዝጉት።\n"
            "• ያመጣችሁትን መረጃ በሙሉ በባዶ ወረቀት ላይ ፈጥነው ይፃፉ። ከዚያ ከመጽሐፉ ጋር በማነጻጸር የቀረዎትን በሌላ ቀለም ይፃፉ!"
        )
    elif lang == "om":
        content = (
            "🧠 Dubbisa Dammaqaa (Active Recall) fi Feynman\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 🚫 Irra Deddeebi'anii Dubbisuu Dhiisaa:\n"
            "• Kitaaba si'a 5 dubbisuun 'haalaan beeka' jechuuf sammuu dagarsa. Of gaafachuun immoo dachaa 3n sammuu keessatti tooraa.\n\n"
            "2. 💡 Malleen Feynman:\n"
            "• Mata duree dubbistan sana akka nama daa'ima waggaa 10f barsiisutti sagalee ol kaastanii ibsaa.\n\n"
            "3. ✍️ Toftaa Blurting:\n"
            "• Erga dubbistanii booda kitaaba cufaatii waan yaadattan waraqaa qullaa irratti barreessaa. Booda kitaaba wajjin madaalaa!"
        )
    else:
        content = (
            "🧠 Active Recall & The Feynman Technique\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 🚫 Stop Passive Re-reading:\n"
            "• Re-reading a textbook chapter 5 times creates a false 'illusion of competence'. Active testing builds 3x stronger neural connections!\n\n"
            "2. 💡 The Feynman Technique:\n"
            "• Explain the complex concept out loud in plain, simple words as if teaching a 10-year-old child.\n"
            "• Whenever you stumble or rely on complex jargon, re-read that exact paragraph to bridge your gap.\n\n"
            "3. ✍️ The Blurting Method:\n"
            "• Read a topic for 10-15 minutes, then close your material.\n"
            "• Write down every single detail, formula, and step you remember on a blank paper. Compare with the original notes in red ink to see what you missed!"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_study_tips")]
    ])
    await safe_reply(callback, content, reply_markup=kb)

@router.callback_query(F.data == "tips_cat_memory")
async def tips_cat_memory_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    if lang == "am":
        content = (
            "📝 የማስታወስ ዘዴዎች እና የፈተና ጥበብ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 🧠 ምህፃረ ቃላት እና ተረቶች (Mnemonics):\n"
            "• ረጅም የትምህርት ዝርዝሮችን ወይም ቀመሮችን የመጀመሪያ ፊደሎቻቸውን በመውሰድ አጫጭር ቃላትን ወይም አስቂኝ አረፍተ ነገሮችን ይፍጠሩ።\n\n"
            "2. 📈 የጊዜ ክፍተት ድግግሞሽ (Spaced Repetition):\n"
            "• ያጠኑትን አዲስ ትምህርት በ24 ሰዓት ውስጥ፣ ከዚያ በ3ኛው ቀን፣ በ7ኛው ቀን እና በ30ኛው ቀን መልሰው ይከልሱት። ለረጅም ጊዜ አእምሮ ውስጥ ይቀመጣል!\n\n"
            "3. 🎯 በፈተና ወቅት ምርጫዎችን የማስወገድ ዘዴ:\n"
            "• ባለብዙ ምርጫ (MCQ) ጥያቄዎችን ሲሰሩ ምርጫዎቹን ከማየትዎ በፊት የጥያቄውን ዋና ፍሬ ነገር ያንብቡ። ከእውነታው የራቁ 2 ምርጫዎችን ወዲያውኑ ይሰርዙ!\n\n"
            "4. 🫁 የፈተና ጭንቀትን ማስታገስ (Box Breathing):\n"
            "• በፈተና ወቅት ጭንቀት ከተሰማዎት፦ ለ4 ሰከንድ አየር ወደ ውስጥ ያስገቡ፣ ለ4 ሰከንድ ይያዙ፣ ለ4 ሰከንድ ያስወጡ። አእምሮን ወዲያውኑ ያረጋጋል!"
        )
    elif lang == "om":
        content = (
            "📝 Malleen Yaadannoo fi Toftaa Qormaataa\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 🧠 Qubee Jalqabaa Fayyadamuu (Mnemonics):\n"
            "• Tarree barnootaa dheeraa yaadachuuf qubeewwan jalqabaa walitti fiduun jecha ykn dubbii salphaa uumaa.\n\n"
            "2. 📈 Guyyoota Garaagaraatti Irra Deebi'uu (Spaced Repetition):\n"
            "• Waan har'a qo'attan saa'a 24 keessatti, guyyaa 3ffaa, guyyaa 7ffaa fi guyyaa 30ffaatti irra deebi'aa.\n\n"
            "3. 🫁 Sodaa Qormaataa Hir'isuu: Yeroo sodaan isin qabe qilleensa daqiiqaa saniif hafuura keessatti fudhadhaa, qabadhaa, gad lakkisaa."
        )
    else:
        content = (
            "📝 Memory Tricks & Exam Room Masterclass\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 🧠 Mnemonics & Visual Association:\n"
            "• Turn long lists or formulas into memorable acronyms or funny mental stories to lock them in memory.\n\n"
            "2. 📈 Spaced Repetition (Beating the Forgetting Curve):\n"
            "• Review new material within 24 hours, then again on Day 3, Day 7, and Day 30. This shifts knowledge from short-term memory to long-term memory permanently!\n\n"
            "3. 🎯 MCQ Distractor Elimination:\n"
            "• Read the question stem thoroughly BEFORE looking at options. Immediately cross out 2 obviously false options to increase accuracy to 50%+ instantly.\n\n"
            "4. 🫁 Exam Panic Control (Box Breathing):\n"
            "• If your mind goes blank during an exam: Inhale for 4 seconds, Hold for 4 seconds, Exhale for 4 seconds, Hold for 4 seconds. This instantly lowers cortisol (stress hormone)!"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_study_tips")]
    ])
    await safe_reply(callback, content, reply_markup=kb)

@router.callback_query(F.data == "tips_cat_digital")
async def tips_cat_digital_callback(callback: CallbackQuery):
    """Displays evidence-based guide on overcoming phone, online, and technology distractions."""
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    if lang == "am":
        content = (
            "📱 *የስልክ፣ የኦንላይን እና የቴክኖሎጂ ትኩረት መበተንን ማሸነፍ*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 📵 *የራቀ ቦታ ማስቀመጥ (Out of Sight, Out of Mind):*\n"
            "• በሚያጠኑበት ጊዜ ስልክዎን በሌላ ክፍል ወይም በሳጥን ውስጥ ይቆልፉ። ስልክዎን ጠረጴዛ ላይ ማስቀመጥ (ምንም እንኳን ቢደፉት) አእምሮዎን በየሰከንዱ እንዲጨነቅ እና ትኩረቱ እንዲበተን ያደርገዋል!\n\n"
            "2. 🎨 *የስልክ ቀለም ወደ ጥቁርና ነጭ መቀየር (Grayscale Mode):*\n"
            "• የስልክዎን ማሳያ ወደ ጥቁርና ነጭ (Grayscale) ይለውጡ። ቀለማት የሌለው ስልክ የአእምሮን የዶፓሚን ፍላጎት ይቀንሳል፤ የሶሻል ሚዲያ ሱስን ያጠፋል።\n\n"
            "3. 🛡️ *መተግበሪያዎችን እና ዌብሳይቶችን መቆለፍ (App Blockers):* \n"
            "• በጥናት ወቅት የማህበራዊ ሚዲያ መተግበሪያዎችን ለመቆለፍ App Blockers (Forest, StayFocusd, Freedom) ይጠቀሙ።\n"
            "• በሚያነቡበት ጊዜ ስልክዎን Airplane Mode ወይም Do Not Disturb ያድርጉ።\n\n"
            "4. 🌐 *የጥናት ብራውዘር እና ማህበራዊ ሚዲያን መዝጋት:*\n"
            "• ጥናት ከመጀመርዎ በፊት የቴሌግራም፣ ቲክቶክ፣ ኢንስታግራም እና ዩቲዩብ ገጾችን ሙሉ በሙሉ ይዝጉ።\n"
            "• በጥናት ወቅት ለትምህርት የሚያስፈልጉ ገጾችን ብቻ ክፍት ያድርጉ።\n\n"
            "5. ⏰ *የተወሰነ የስልክ ማየቻ ጊዜ መመደብ:*\n"
            "• መልእክቶችን እና ሶሻል ሚዲያን የሚያዩት በረጅም እረፍት ጊዜ ብቻ ይሁን። በየ5 ደቂቃው ስልክ ማየት ትኩረት የማድረግ አቅምን በከፍተኛ ደረጃ ያበላሻል!"
        )
    elif lang == "om":
        content = (
            "📱 *Jeequmsa Bilbilaa fi Interneetaa Mo'achuu*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 📵 *Bilbila Fageessuu (Out of Sight, Out of Mind):*\n"
            "• Yeroo qo'attan bilbila keessan kellaa biraatti kaasaa ykn meeshaa keessatti hidhaa. Bilbila fuula keessan dura kaa'uun xiyyeeffannoo sammuu keessanii fitteneesa!\n\n"
            "2. 🎨 *Halluu Bilbilaa Jijjiiruu (Grayscale Mode):*\n"
            "• Saffisaan halluu bilbila keessanii gara gurraacha fi adiitti (Grayscale) jijjiiraa. Halluu dhabuun hawwata miidiyaa hawaasaa sammuu irraa hir'isa.\n\n"
            "3. 🛡️ *Apps fi Interneeta Cufuu (App Blockers):*\n"
            "• Yeroo qo'annoo App Blockers (Forest, StayFocusd) fayyadamuu ykn bilbila keessan Airplane Mode irratti godhaa.\n\n"
            "4. 🌐 *Tabs Miidiyaa Hawaasaa Cufuu:*\n"
            "• Qo'annoo jalqabuu keessan dura fuulota Telegram, TikTok, Instagram fi YouTube cufaa. Fuula barnootaa qofa banattanii qo'adhaa.\n\n"
            "5. ⏰ *Yeroo Bilbilaa Murteessuu:*\n"
            "• Ergaawwan fi miidiyaa hawaasaa yeroo boqonnaa qofa irratti ilaalaa. Daqiiqaa 5n 5niin bilbila ilaaluun dandeettii xiyyeeffannoo balleessa!"
        )
    else:
        content = (
            "📱 *Overcoming Phone, Online & Technology Distractions*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 📵 *Physical Distance (Out of Sight, Out of Mind):*\n"
            "• During study blocks, place your phone in another room or inside a closed drawer. Keeping your phone on your desk — even face down — drains mental energy as your brain constantly resists checking notifications!\n\n"
            "2. 🎨 *Grayscale / Monochrome Display:* \n"
            "• Turn on Grayscale Mode in your phone settings. Colorless screens neutralize the visual triggers and dopamine rewards engineered into social media apps.\n\n"
            "3. 🛡️ *Website & App Blockers:* \n"
            "• Use app blockers (Forest, StayFocusd, Freedom, Cold Turkey) during your 25-minute Pomodoro focus blocks.\n"
            "• Turn on Airplane Mode or Do Not Disturb (DND) mode while reading.\n\n"
            "4. 🌐 *Clean Study Browser & Tab Isolation:*\n"
            "• Close all social media browser tabs (Telegram, TikTok, Instagram, YouTube) before starting.\n"
            "• Use a dedicated 'Study Profile' or Incognito mode without logged-in personal accounts.\n\n"
            "5. ⏰ *Scheduled Digital Checkpoints:*\n"
            "• Check messages and social media ONLY during designated 15-minute break windows, not every 5 minutes. Protect your attention span!"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_study_tips")]
    ])
    await safe_reply(callback, content, reply_markup=kb)

@router.callback_query(F.data == "tips_cat_focus")
async def tips_cat_focus_callback(callback: CallbackQuery):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    if lang == "am":
        content = (
            "⚡ ትኩረት መሰብሰብ እና ስንፍናን (Procrastination) ማሸነፍ\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. ⏱️ የ 5-ደቂቃ ህግ (5-Minute Rule):\n"
            "• ማናት የመሰነፍ ስሜት ሲሰማዎት 'ለ5 ደቂቃ ብቻ ነው የማነበው' ብለው ይጀምሩ። አስቸጋሪው ክፍል መጀመሩ ብቻ ነው፤ አንዴ ከጀመሩ 80% ጊዜ መቀጠል ይቻላል!\n\n"
            "2. 📵 ስልክን ማራቅ እና ዶፓሚን ማስተካከል:\n"
            "• የሶሻል ሚዲያ ማሳወቂያዎች የአእምሮን ትኩረት ይበትናሉ። በሚያጠኑበት ጊዜ ስልክዎን በሌላ ክፍል ያድርጉት።\n\n"
            "3. 🛏️ የጥናት ቦታን መለየት:\n"
            "• አልጋ ላይ ሆነው አያጥኑ! አልጋ ለአእምሮ የእንቅልፍ ቦታ በመሆኑ ወዲያውኑ ድካም ያመጣል። ንፁህ ጠረጴዛ እና ወንበር ይጠቀሙ።"
        )
    elif lang == "om":
        content = (
            "⚡ Xiyyeeffannoo fi Dhibaa'ummaa Mo'achuu\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. ⏱️ Seera Daqiiqaa 5:\n"
            "• Yeroo mormiin isinitti dhufu 'Daqiiqaa 5 qofaafan dubbisa' jedhaatii jalqabaa. Jalqabuun isa cimaadha!\n\n"
            "2. 📵 Bilbila Fageessuu:\n"
            "• Yeroo qo'attan bilbila keessan kellaa biraatti kaasaa ykn Silent godhaa."
        )
    else:
        content = (
            "⚡ Overcoming Procrastination & Building Unshakable Focus\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. ⏱️ The 5-Minute Rule:\n"
            "• Tell yourself: 'I will only study for 5 minutes.' Procrastination is a psychological friction to starting. Once you start, momentum carries you forward 80%+ of the time!\n\n"
            "2. 📵 Dopamine Detox & Phone Shield:\n"
            "• Put your smartphone in another room or on Airplane Mode. Social media notifications shatter deep focus.\n\n"
            "3. 🛏️ Environment Anchoring:\n"
            "• NEVER study in bed! Your brain associates bed with sleep, releasing melatonin and causing drowsiness. Use a desk and chair dedicated solely to learning."
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_study_tips")]
    ])
    await safe_reply(callback, content, reply_markup=kb)

@router.callback_query(F.data == "tips_cat_custom")
async def tips_cat_custom_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
    except Exception:
        pass
    telegram_id = callback.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    
    await state.set_state(StudyTipsStates.waiting_for_problem)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="menu_study_tips")]
    ])
    await safe_reply(callback, t("tips_ask_problem", lang), reply_markup=kb)

@router.message(StudyTipsStates.waiting_for_problem)
async def process_custom_study_problem(message: Message, state: FSMContext):
    if not message.text:
        return

    telegram_id = message.from_user.id
    student = await student_service.get_student(telegram_id)
    lang = student.preferred_language if student else "English"
    user_problem = message.text.strip()
    
    thinking_msg = await message.answer("🤔 Analyzing your study problem and preparing personalized psychological advice...*", parse_mode="Markdown")
    
    try:
        prompt = (
            f"You are the master psychological and academic study coach for Ethio Smart Study.\n"
            f"Student Grade Level: Grade {student.grade if student else '10'}\n"
            f"Preferred Language: {lang}\n\n"
            f"STUDENT STUDY PROBLEM:\n"
            f"\"{user_problem}\"\n\n"
            f"REQUIREMENTS:\n"
            f"1. Give an empathetic, warm, highly encouraging response in {lang}.\n"
            f"2. Provide a 4-step actionable solution combining cognitive psychology, effective reading techniques (e.g. Active Recall, Feynman, Pomodoro), time management, and exam anxiety management.\n"
            f"3. Keep the formatting telegram-friendly using bold headings and bullet points.\n"
            f"4. End with an empowering motivational takeaway."
        )
        
        advice_text, _, _ = await ask_gemini_with_profile(
            question=prompt,
            history=[],
            student=student
        )
        
        await state.clear()
        
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💡 More Study Tips", callback_data="menu_study_tips")],
            [InlineKeyboardButton(text=t("btn_back", lang), callback_data="menu_back")]
        ])
        await safe_reply(message, advice_text, reply_markup=kb)

    except Exception as e:
        logging.error(f"Error processing custom study problem: {e}", exc_info=True)
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await safe_reply(message, "⚠️ Error generating personalized advice. Please try again or select one of the study tip categories.")

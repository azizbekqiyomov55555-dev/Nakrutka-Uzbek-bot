# main.py — bitta faylda to‘liq ishlaydigan (aiogram v2) kod
# ✅ telefon (contact + text) ✅ instagram link regex ✅ like +/- ✅ tasdiqlash ✅ chek ✅ admin approve

import logging
import os
import re
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

API_TOKEN = ("8581826002:AAERcJJEZm1RIyp5U3SzdMgrzzfMq0NmkbI")  # Railway Variables -> BOT_TOKEN
ADMIN_ID =  8537782289             # admin telegram ID

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== GLOBAL STORAGE ==================
user_likes = {}   # {user_id: int}
user_urls = {}    # {user_id: str}

# ================== STATES ==================
class Form(StatesGroup):
    phone = State()
    instagram_menu = State()
    like_url = State()
    waiting_for_check = State()

# ================== KEYBOARDS ==================
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Telefon yuborish 📱", request_contact=True)]],
    resize_keyboard=True,
)

instagram_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Likes ❤️")]],
    resize_keyboard=True,
)

def like_keyboard(count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("-1000 ❤️", callback_data="minus"),
            InlineKeyboardButton(str(count), callback_data="count"),
            InlineKeyboardButton("+1000 ❤️", callback_data="plus"),
        ],
        [InlineKeyboardButton("Tasdiqlash ✅", callback_data="confirm")]
    ])

def admin_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}")]
    ])

# ================== INSTAGRAM VALIDATION ==================
INSTAGRAM_REGEX = r"(https?:\/\/)?(www\.)?instagram\.com\/(reel|p|tv)\/[A-Za-z0-9_\-]+"

async def check_instagram_post(url: str) -> bool:
    """
    Instagram ko‘p hollarda botlarni bloklashi mumkin.
    Shunga qaramay, 200 bo‘lsa True, bo‘lmasa False qaytaramiz.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, allow_redirects=True, timeout=15) as resp:
                return resp.status == 200
    except Exception:
        return False

# ================== START ==================
@dp.message_handler(commands=["start", "help"])
async def start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "<b>Instagram botiga xush kelibsiz!</b>\n\n"
        "Telefon raqamingizni yuboring yoki +998XXXXXXXXX yozing.",
        reply_markup=phone_keyboard
    )
    await Form.phone.set()

# ================== PHONE (CONTACT) ==================
@dp.message_handler(content_types=types.ContentType.CONTACT, state=Form.phone)
async def get_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    # admin ga yuborish (xohlasangiz o‘chirib qo‘ying)
    try:
        await bot.send_message(ADMIN_ID, f"📞 Yangi raqam: {phone}\nUserID: {user_id}")
    except Exception:
        pass

    user_likes[user_id] = 0
    await message.answer("✅ Raqam qabul qilindi. Xizmatni tanlang ⬇️", reply_markup=instagram_menu_keyboard)
    await Form.instagram_menu.set()

# ================== PHONE (TEXT) ==================
@dp.message_handler(content_types=types.ContentType.TEXT, state=Form.phone)
async def get_phone_text(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    user_id = message.from_user.id

    if text.startswith("+998") and len(text) == 13 and text[1:].isdigit():
        try:
            await bot.send_message(ADMIN_ID, f"📞 Yangi raqam: {text}\nUserID: {user_id}")
        except Exception:
            pass

        user_likes[user_id] = 0
        await message.answer("✅ Raqam qabul qilindi. Xizmatni tanlang ⬇️", reply_markup=instagram_menu_keyboard)
        await Form.instagram_menu.set()
    else:
        await message.answer("Telefon noto‘g‘ri formatda ❌\nMasalan: +998901234567")

# ================== MENU ==================
@dp.message_handler(state=Form.instagram_menu, text="Likes ❤️")
async def ask_url(message: Message, state: FSMContext):
    await message.answer("Instagram link yuboring (reel/p/tv):")
    await Form.like_url.set()

# ================== URL QABUL ==================
@dp.message_handler(state=Form.like_url, content_types=types.ContentType.TEXT)
async def get_url(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    match = re.search(INSTAGRAM_REGEX, text)
    if not match:
        await message.answer("❌ Noto‘g‘ri Instagram link.\nMisol: https://www.instagram.com/reel/XXXX")
        return

    clean_url = match.group(0)

    await message.answer("🔎 Link tekshirilmoqda...")

    # Post mavjudligini tekshirish (ba'zan instagram bloklasa False chiqishi mumkin)
    ok = await check_instagram_post(clean_url)
    if not ok:
        await message.answer("❌ Post topilmadi yoki private.\nPublic post yuboring.")
        return

    user_urls[user_id] = clean_url
    user_likes[user_id] = 0

    await message.answer("Like sonini tanlang:", reply_markup=like_keyboard(0))

    # MUHIM: endi link state’da qolib ketmasin
    await Form.instagram_menu.set()

# ================== CALLBACKS: COUNT (0 tugma) ==================
@dp.callback_query_handler(text="count")
async def count_btn(call: types.CallbackQuery):
    await call.answer()  # faqat loadingni o‘chiradi

# ================== CALLBACKS: PLUS/MINUS ==================
@dp.callback_query_handler(text="plus")
async def plus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_likes[user_id] = user_likes.get(user_id, 0) + 1000
    await safe_update_like_keyboard(call, user_likes[user_id])
    await call.answer()  # MUHIM

@dp.callback_query_handler(text="minus")
async def minus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_likes[user_id] = max(0, user_likes.get(user_id, 0) - 1000)
    await safe_update_like_keyboard(call, user_likes[user_id])
    await call.answer()  # MUHIM

async def safe_update_like_keyboard(call: types.CallbackQuery, count: int):
    try:
        await call.message.edit_reply_markup(reply_markup=like_keyboard(count))
    except Exception:
        # ba'zan "message is not modified" yoki boshqa xato bo‘lishi mumkin
        pass

# ================== CONFIRM (TO'LOV) ==================
@dp.callback_query_handler(text="confirm")
async def confirm(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username or "username_yoq"

    url = user_urls.get(user_id)
    likes = user_likes.get(user_id, 0)
    price = likes * 5

    if not url:
        await call.answer("Avval link yuboring!", show_alert=True)
        return

    # admin ga buyurtma
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 <b>Buyurtma</b>\n"
            f"User: @{username} (ID: {user_id})\n"
            f"URL: {url}\n"
            f"Likelar: {likes}\n"
            f"Narxi: {price} so'm\n"
            f"Chek kutilmoqda..."
        )
    except Exception:
        pass

    await call.message.answer(
        f"💳 To‘lov qiling:\n"
        f"<code>5614681909981023</code>\n\n"
        f"Summa: <b>{price} so'm</b>\n\n"
        f"To‘lovdan so‘ng chek (rasm) yuboring 📷"
    )

    await Form.waiting_for_check.set()
    await call.answer()

# ================== CHEK QABUL ==================
@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.waiting_for_check)
async def get_check(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "username_yoq"

    url = user_urls.get(user_id)
    likes = user_likes.get(user_id, 0)
    price = likes * 5

    caption = (
        f"📷 <b>Chek</b>\n"
        f"User: @{username} (ID: {user_id})\n"
        f"URL: {url}\n"
        f"Likelar: {likes}\n"
        f"Narxi: {price} so'm"
    )

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=admin_keyboard(user_id)
    )

    await message.answer("✅ Chek adminga yuborildi. Tekshirilmoqda.")
    await state.finish()

# ================== ADMIN APPROVE ==================
@dp.callback_query_handler(lambda c: c.data and c.data.startswith("approve_"))
async def approve(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Siz admin emassiz!", show_alert=True)
        return

    user_id = int(call.data.split("_")[1])

    await bot.send_message(user_id, "🎉 To‘lov tasdiqlandi! Buyurtmangiz bajarilmoqda.")
    try:
        await call.message.edit_caption((call.message.caption or "") + "\n\n✅ <b>Tasdiqlandi</b>")
    except Exception:
        pass

    await call.answer("Tasdiqlandi ✅")

# ================== RUN ==================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

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
    InlineKeyboardButton
)
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

API_TOKEN = ("8581826002:AAERcJJEZm1RIyp5U3SzdMgrzzfMq0NmkbI")
ADMIN_ID = 8537782289  # o'zingizni ID

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

user_likes = {}
user_urls = {}

# ================= STATES =================
class Form(StatesGroup):
    phone = State()
    instagram_menu = State()
    like_url = State()
    waiting_for_check = State()

# ================= KEYBOARDS =================
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Telefon yuborish 📱", request_contact=True)]],
    resize_keyboard=True
)

instagram_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Likes ❤️")]],
    resize_keyboard=True
)

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "<b>Instagram Nakrutka Bot</b>\n\nTelefon raqamingizni yuboring:",
        reply_markup=phone_keyboard
    )
    await Form.phone.set()

# ================= PHONE CONTACT =================
@dp.message_handler(content_types=types.ContentType.CONTACT, state=Form.phone)
async def get_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_likes[user_id] = 0

    await message.answer(
        "Raqam qabul qilindi ✅",
        reply_markup=instagram_menu_keyboard
    )
    await Form.instagram_menu.set()

# ================= PHONE TEXT =================
@dp.message_handler(content_types=types.ContentType.TEXT, state=Form.phone)
async def get_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()

    if text.startswith("+998") and len(text) == 13 and text[1:].isdigit():
        user_id = message.from_user.id
        user_likes[user_id] = 0

        await message.answer(
            "Raqam qabul qilindi ✅",
            reply_markup=instagram_menu_keyboard
        )
        await Form.instagram_menu.set()
    else:
        await message.answer("Telefon noto‘g‘ri formatda ❌")

# ================= URL VALIDATION =================
INSTAGRAM_REGEX = r"(https?:\/\/)?(www\.)?instagram\.com\/(reel|p|tv)\/[A-Za-z0-9_\-]+"

async def check_instagram_post(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return resp.status == 200
    except:
        return False

# ================= MENU =================
@dp.message_handler(state=Form.instagram_menu, text="Likes ❤️")
async def ask_url(message: Message):
    await message.answer("Instagram post linkini yuboring:")
    await Form.like_url.set()

# ================= GET URL =================
@dp.message_handler(state=Form.like_url)
async def get_url(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    match = re.search(INSTAGRAM_REGEX, text)

    if not match:
        await message.answer("❌ Noto‘g‘ri Instagram link.")
        return

    clean_url = match.group(0)

    await message.answer("🔎 Link tekshirilmoqda...")

    is_valid = await check_instagram_post(clean_url)

    if not is_valid:
        await message.answer("❌ Post mavjud emas yoki private.")
        return

    user_urls[user_id] = clean_url
    user_likes[user_id] = 0

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("-1000 ❤️", callback_data="minus"),
            InlineKeyboardButton("0", callback_data="count"),
            InlineKeyboardButton("+1000 ❤️", callback_data="plus"),
        ],
        [
            InlineKeyboardButton("Tasdiqlash ✅", callback_data="confirm")
        ]
    ])

    await message.answer("Like sonini tanlang:", reply_markup=keyboard)

# ================= LIKE +/- =================
@dp.callback_query_handler(text="plus")
async def plus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_likes[user_id] += 1000
    await update_keyboard(call)

@dp.callback_query_handler(text="minus")
async def minus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_likes[user_id] >= 1000:
        user_likes[user_id] -= 1000
    await update_keyboard(call)

async def update_keyboard(call):
    user_id = call.from_user.id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("-1000 ❤️", callback_data="minus"),
            InlineKeyboardButton(str(user_likes[user_id]), callback_data="count"),
            InlineKeyboardButton("+1000 ❤️", callback_data="plus"),
        ],
        [
            InlineKeyboardButton("Tasdiqlash ✅", callback_data="confirm")
        ]
    ])

    await call.message.edit_reply_markup(reply_markup=keyboard)

# ================= CONFIRM =================
@dp.callback_query_handler(text="confirm")
async def confirm(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username or "username_yoq"

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Buyurtma\nUser: @{username}\nURL: {user_urls[user_id]}\nLikelar: {user_likes[user_id]}"
    )

    await call.message.answer(
        f"💳 To‘lov qiling:\n<code>5614681909981023</code>\n\nChekni yuboring 📷"
    )

    await Form.waiting_for_check.set()

# ================= CHECK =================
def admin_keyboard(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}")]
    ])

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.waiting_for_check)
async def get_check(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "username_yoq"

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"📷 Chek\nUser: @{username}",
        reply_markup=admin_keyboard(user_id)
    )

    await message.answer("Chek yuborildi. Tekshirilmoqda.")
    await state.finish()

# ================= APPROVE =================
@dp.callback_query_handler(lambda c: c.data.startswith("approve_"))
async def approve(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])

    await bot.send_message(user_id, "🎉 To‘lov tasdiqlandi. Buyurtma bajarilmoqda.")
    await call.message.edit_caption(call.message.caption + "\n\n✅ Tasdiqlandi")

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

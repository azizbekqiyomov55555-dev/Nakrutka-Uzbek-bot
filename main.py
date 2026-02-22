import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from keyboards.defaults.instagram import instagram_paket, orqaqa, phone
from keyboards.inlines.accses import like_button

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

son = {}
user_urls = {}

# ================= STATES =================
class Shogirdchalar(StatesGroup):
    Instagram_state = State()
    url_like_state = State()
    get_phone = State()

# ================= DATABASE =================
conn = sqlite3.connect('stats.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE
)
""")
conn.commit()

def record_stat(user_id):
    cursor.execute(
        "INSERT INTO stats (user_id, date) VALUES (?, DATE('now'))",
        (user_id,)
    )
    conn.commit()

# ================= START =================
@dp.message_handler(commands=['start', 'help'])
async def start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer("<b>I N S T A G R A M</b> botiga xush kelibsiz!")
    await message.answer(
        "Telefon raqamingizni yuboring yoki +998XXXXXXXXX yozing.",
        reply_markup=phone
    )
    await Shogirdchalar.get_phone.set()
    record_stat(message.from_user.id)

# ================= CONTACT HANDLER =================
@dp.message_handler(
    content_types=types.ContentType.CONTACT,
    state=Shogirdchalar.get_phone
)
async def get_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number

    await bot.send_message(6457971132, f"Mijoz telefon: {phone_number}")

    son[user_id] = 0
    await message.answer(
        "Xizmat turini tanlang ⬇️",
        reply_markup=instagram_paket
    )
    await Shogirdchalar.Instagram_state.set()

# ================= TEXT PHONE HANDLER =================
@dp.message_handler(
    content_types=types.ContentType.TEXT,
    state=Shogirdchalar.get_phone
)
async def get_phone_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()

    if text.startswith("+998") and len(text) == 13 and text[1:].isdigit():
        await bot.send_message(6457971132, f"Mijoz telefon: {text}")

        son[user_id] = 0
        await message.answer(
            "Raqam qabul qilindi ✅\nXizmat turini tanlang ⬇️",
            reply_markup=instagram_paket
        )
        await Shogirdchalar.Instagram_state.set()
    else:
        await message.answer("Telefon noto‘g‘ri formatda ❌")

# ================= LIKES MENU =================
@dp.message_handler(
    state=Shogirdchalar.Instagram_state,
    text="Likes ❤️"
)
async def likes_menu(message: Message):
    await message.answer(
        "Instagram post linkini yuboring:",
        reply_markup=orqaqa
    )
    await Shogirdchalar.url_like_state.set()

# ================= URL QABUL =================
@dp.message_handler(state=Shogirdchalar.url_like_state)
async def get_url(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text.startswith("https://www.instagram.com"):
        user_urls[user_id] = text
        son[user_id] = 0
        await message.answer(
            "Like sonini tanlang:",
            reply_markup=like_button
        )
    else:
        await message.answer("URL noto‘g‘ri ❌")

# ================= LIKE +/- =================
@dp.callback_query_handler(text="like+")
async def plus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    son[user_id] += 1000
    await update_like_keyboard(call)

@dp.callback_query_handler(text="like-")
async def minus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    if son[user_id] >= 1000:
        son[user_id] -= 1000
    await update_like_keyboard(call)

async def update_like_keyboard(call):
    user_id = call.from_user.id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("-1000 ❤️", callback_data="like-"),
            InlineKeyboardButton(str(son[user_id]), callback_data="none"),
            InlineKeyboardButton("+1000 ❤️", callback_data="like+"),
        ],
        [
            InlineKeyboardButton(
                "Tasdiqlash ✅",
                callback_data="like_tasdiqlash"
            )
        ]
    ])

    await call.message.edit_reply_markup(reply_markup=keyboard)

# ================= TASDIQLASH =================
@dp.callback_query_handler(text="like_tasdiqlash")
async def confirm(call: types.CallbackQuery):
    user_id = call.from_user.id
    username = call.from_user.username or "username_yoq"

    await bot.send_message(
        6457971132,
        f"<b>Yangi buyurtma</b>\n"
        f"URL: {user_urls.get(user_id)}\n"
        f"Soni: {son[user_id]}\n"
        f"Narxi: {son[user_id] * 5} so'm\n"
        f"Telegram: @{username}"
    )

    await call.message.answer(
        f"Likelar: <b>{son[user_id]}</b>\n"
        f"Narxi: <b>{son[user_id] * 5} so'm</b>\n"
        f"Karta: <code>5614681909981023</code>"
    )

# ================= ASOSIY MENU =================
@dp.message_handler(text="Asosiy menu🔙")
async def menu(message: Message):
    await message.answer(
        "Tanlang:",
        reply_markup=instagram_paket
    )
    await Shogirdchalar.Instagram_state.set()

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

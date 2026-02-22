import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from keyboards.defaults.instagram import instagram_paket, orqaqa, phone
from keyboards.inlines.accses import true_false, follow_button, like_button, view_button, comment_button

logging.basicConfig(level=logging.INFO)

# TOKEN Railway Variables dan olinadi
API_TOKEN = ("8581826002:AAERcJJEZm1RIyp5U3SzdMgrzzfMq0NmkbI")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# USER LIKE SONI SAQLASH
son = {}

# GLOBAL URL
user_urls = {}

# ================= STATES =================
class Shogirdchalar(StatesGroup):
    Socials_button_state = State()
    Instagram_state = State()
    YouTube_state = State()
    TikTok_state = State()
    Telegram_state = State()
    username_insta_state = State()
    url_like_state = State()
    views_state = State()
    comment_state = State()
    get_phone = State()

# ================= DATABASE =================
conn = sqlite3.connect('stats.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE
)
''')
conn.commit()

def record_stat(user_id):
    cursor.execute("INSERT INTO stats (user_id, date) VALUES (?, DATE('now'))", (user_id,))
    conn.commit()

# ================= STATISTIKA =================
@dp.message_handler(commands=['stats'])
async def show_stats(message: Message):
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM stats WHERE date = DATE('now')")
    today_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM stats")
    total_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM stats WHERE date = DATE('now')")
    today_requests = cursor.fetchone()[0]

    text = (
        f"📊 Bot statistikasi:\n"
        f"Jami foydalanuvchi: {total_users}\n"
        f"Bugungi foydalanuvchi: {today_users}\n"
        f"Jami so'rov: {total_requests}\n"
        f"Bugungi so'rov: {today_requests}"
    )
    await message.answer(text)

# ================= START =================
@dp.message_handler(commands=['start','help'])
async def start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer("<b>I N S T A G R A M</b> botiga xush kelibsiz!")
    await message.answer(
        "Telefon raqamingizni yuboring yoki +998XXXXXXXXX ko'rinishida yozing.",
        reply_markup=phone
    )
    await Shogirdchalar.get_phone.set()
    record_stat(message.from_user.id)

# ================= CONTACT =================
@dp.message_handler(content_types=types.ContentType.CONTACT, state=Shogirdchalar.get_phone)
async def get_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await bot.send_message(6457971132, f"Mijoz telefon: {message.contact.phone_number}")
    son[user_id] = 0
    await message.answer("Xizmat turini tanlang ⬇️", reply_markup=instagram_paket)
    await Shogirdchalar.Instagram_state.set()

# ================= TEXT PHONE =================
@dp.message_handler(state=Shogirdchalar.get_phone)
async def get_phone_text(message: Message, state: FSMContext):
    if message.text.startswith("+998"):
        user_id = message.from_user.id
        await bot.send_message(6457971132, f"Mijoz telefon: {message.text}")
        son[user_id] = 0
        await message.answer("Raqam qabul qilindi ✅", reply_markup=instagram_paket)
        await Shogirdchalar.Instagram_state.set()
    else:
        await message.answer("Telefon noto‘g‘ri formatda ❌")

# ================= LIKES =================
@dp.message_handler(state=Shogirdchalar.Instagram_state, text="Likes ❤️")
async def likes(message: Message):
    await message.answer("Instagram link yuboring:", reply_markup=orqaqa)
    await Shogirdchalar.url_like_state.set()

@dp.message_handler(state=Shogirdchalar.url_like_state)
async def get_url(message: Message):
    user_id = message.from_user.id
    if message.text.startswith("https://www.instagram.com"):
        user_urls[user_id] = message.text
        await message.answer("Like sonini tanlang:", reply_markup=like_button)
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
        [InlineKeyboardButton("Tasdiqlash ✅", callback_data="like_tasdiqlash")]
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
        f"Narxi: {son[user_id]*5} so'm\n"
        f"Telegram: @{username}"
    )

    await call.message.answer(
        f"Likelar: <b>{son[user_id]}</b>\n"
        f"Narxi: <b>{son[user_id]*5} so'm</b>\n"
        f"Karta: <code>5614681909981023</code>"
    )

# ================= ASOSIY MENU =================
@dp.message_handler(text="Asosiy menu🔙")
async def menu(message: Message):
    await message.answer("Tanlang:", reply_markup=instagram_paket)
    await Shogirdchalar.Instagram_state.set()

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

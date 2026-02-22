import logging
import os
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

API_TOKEN = ("8581826002:AAERcJJEZm1RIyp5U3SzdMgrzzfMq0NmkbI")  # Railway Variables ga qo‘ying

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= GLOBAL =================
user_likes = {}
user_urls = {}

# ================= STATES =================
class Form(StatesGroup):
    phone = State()
    instagram_menu = State()
    like_url = State()

# ================= PHONE KEYBOARD =================
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Telefon raqamni yuborish 📱", request_contact=True)]
    ],
    resize_keyboard=True
)

# ================= INSTAGRAM MENU =================
instagram_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Likes ❤️")]
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "<b>INSTAGRAM botiga xush kelibsiz!</b>\n\n"
        "Telefon raqamingizni yuboring yoki +998XXXXXXXXX yozing.",
        reply_markup=phone_keyboard
    )
    await Form.phone.set()

# ================= CONTACT =================
@dp.message_handler(content_types=types.ContentType.CONTACT, state=Form.phone)
async def get_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    await message.answer(
        f"Raqam qabul qilindi ✅\n\n{phone}",
        reply_markup=instagram_menu_keyboard
    )

    user_likes[user_id] = 0
    await Form.instagram_menu.set()

# ================= TEXT PHONE =================
@dp.message_handler(content_types=types.ContentType.TEXT, state=Form.phone)
async def get_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()

    if text.startswith("+998") and len(text) == 13 and text[1:].isdigit():
        user_id = message.from_user.id

        await message.answer(
            f"Raqam qabul qilindi ✅\n\n{text}",
            reply_markup=instagram_menu_keyboard
        )

        user_likes[user_id] = 0
        await Form.instagram_menu.set()
    else:
        await message.answer("Telefon noto‘g‘ri formatda ❌")

# ================= LIKES MENU =================
@dp.message_handler(state=Form.instagram_menu, text="Likes ❤️")
async def ask_url(message: Message):
    await message.answer("Instagram post linkini yuboring:")
    await Form.like_url.set()

# ================= URL =================
@dp.message_handler(state=Form.like_url)
async def get_url(message: Message):
    user_id = message.from_user.id
    url = message.text.strip()

    if url.startswith("https://"):
        user_urls[user_id] = url
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
    else:
        await message.answer("URL noto‘g‘ri ❌")

# ================= PLUS =================
@dp.callback_query_handler(text="plus")
async def plus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_likes[user_id] += 1000
    await update_keyboard(call)

# ================= MINUS =================
@dp.callback_query_handler(text="minus")
async def minus_like(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_likes[user_id] >= 1000:
        user_likes[user_id] -= 1000
    await update_keyboard(call)

# ================= UPDATE KEYBOARD =================
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
async def confirm(call: types.CallbackQuery):
    user_id = call.from_user.id
    username = call.from_user.username or "username_yoq"

    await call.message.answer(
        f"<b>Buyurtma qabul qilindi</b>\n\n"
        f"URL: {user_urls.get(user_id)}\n"
        f"Likelar: {user_likes[user_id]}\n"
        f"Narxi: {user_likes[user_id]*5} so'm\n"
        f"User: @{username}"
    )

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

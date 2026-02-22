import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

API_TOKEN = ("8581826002:AAERcJJEZm1RIyp5U3SzdMgrzzfMq0NmkbI")  # Railway Variables dan qo‘ying

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================= STATES =================
class Form(StatesGroup):
    phone = State()

# ================= PHONE KEYBOARD =================
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("Telefon raqamni yuborish 📱", request_contact=True)]
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Telefon raqamingizni yuboring yoki +998XXXXXXXXX yozing.",
        reply_markup=phone_keyboard
    )
    await Form.phone.set()

# ================= CONTACT HANDLER =================
@dp.message_handler(
    content_types=types.ContentType.CONTACT,
    state=Form.phone
)
async def get_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await message.answer(f"CONTACT qabul qilindi ✅\nRaqam: {phone}")
    await state.finish()

# ================= TEXT PHONE HANDLER =================
@dp.message_handler(
    content_types=types.ContentType.TEXT,
    state=Form.phone
)
async def get_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()

    if text.startswith("+998") and len(text) == 13 and text[1:].isdigit():
        await message.answer(f"TEXT qabul qilindi ✅\nRaqam: {text}")
        await state.finish()
    else:
        await message.answer("Telefon noto‘g‘ri formatda ❌")

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

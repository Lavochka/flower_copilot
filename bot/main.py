import logging
import asyncio
import uuid
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from dotenv import load_dotenv
from models import db, Card
from utils.qr_generator import generate_custom_qr
from flask import Flask

load_dotenv()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Инициализация минимального Flask приложения для работы с БД внутри бота
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db.init_app(app)

class CardCreation(StatesGroup):
    choosing_background = State()
    uploading_media = State()
    entering_title = State()
    entering_text = State()
    entering_sender_name = State()
    confirming = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [KeyboardButton(text="Создать открытку 🌸")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Добро пожаловать в {os.getenv('SHOP_NAME')}! Я помогу вам создать уникальную онлайн-открытку.", reply_markup=keyboard)

@dp.message(F.text == "Создать открытку 🌸")
async def start_creation(message: types.Message, state: FSMContext):
    kb = [
        [InlineKeyboardButton(text="Шаблон 1", callback_data="tpl_1"), 
         InlineKeyboardButton(text="Шаблон 2", callback_data="tpl_2")],
        [InlineKeyboardButton(text="Шаблон 3", callback_data="tpl_3")],
        [InlineKeyboardButton(text="Загрузить свое фото/видео", callback_data="custom_media")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("Выберите фон для вашей открытки:", reply_markup=keyboard)
    await state.set_state(CardCreation.choosing_background)

@dp.callback_query(F.data.startswith("tpl_"))
async def choose_template(callback: types.CallbackQuery, state: FSMContext):
    template_id = callback.data.split("_")[1]
    await state.update_data(template_id=template_id, media_type=None, media_path=None)
    await callback.message.answer("Введите заголовок для открытки (например, 'С днем рождения!'):")
    await state.set_state(CardCreation.entering_title)

@dp.callback_query(F.data == "custom_media")
async def ask_custom_media(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Пожалуйста, отправьте фото или видео, которое будет фоном открытки:")
    await state.set_state(CardCreation.uploading_media)

@dp.message(CardCreation.uploading_media, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    file = await bot.get_file(file_id)
    file_path = f"static/uploads/{uuid.uuid4()}.jpg"
    await bot.download_file(file.file_path, file_path)
    await state.update_data(media_path=file_path, media_type='photo', template_id=None)
    await message.answer("Отлично! Теперь введите заголовок для открытки:")
    await state.set_state(CardCreation.entering_title)

@dp.message(CardCreation.uploading_media, F.video)
async def handle_video(message: types.Message, state: FSMContext):
    video = message.video
    file_id = video.file_id
    file = await bot.get_file(file_id)
    file_path = f"static/uploads/{uuid.uuid4()}.mp4"
    await bot.download_file(file.file_path, file_path)
    await state.update_data(media_path=file_path, media_type='video', template_id=None)
    await message.answer("Видео загружено! Теперь введите заголовок для открытки:")
    await state.set_state(CardCreation.entering_title)

@dp.message(CardCreation.entering_title)
async def handle_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Теперь введите текст пожелания:")
    await state.set_state(CardCreation.entering_text)

@dp.message(CardCreation.entering_text)
async def handle_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("И последнее: как вас подписать? (От кого открытка):")
    await state.set_state(CardCreation.entering_sender_name)

@dp.message(CardCreation.entering_sender_name)
async def handle_sender_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    card_id = str(uuid.uuid4())
    # Здесь в будущем будет сохранение в БД и генерация QR
    await state.update_data(sender_name=message.text, card_id=card_id, sender_id=message.from_user.id)
    
    # Предварительный просмотр
    await message.answer(f"Проверьте данные:\nЗаголовок: {data.get('title')}\nОт кого: {message.text}\nВсе верно?", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="Да, создать QR-код", callback_data="finalize")],
                             [InlineKeyboardButton(text="Начать заново", callback_data="cancel")]
                         ]))

@dp.callback_query(F.data == "finalize")
async def finalize_card(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_id = data.get('card_id')
    
    with app.app_context():
        new_card = Card(
            id=card_id,
            sender_id=data.get('sender_id'),
            template_id=data.get('template_id'),
            media_path=data.get('media_path'),
            media_type=data.get('media_type'),
            title=data.get('title'),
            text=data.get('text'),
            sender_name=data.get('sender_name')
        )
        db.session.add(new_card)
        db.session.commit()

    # Генерация ссылки и QR
    card_url = f"{os.getenv('BASE_URL')}/card/{card_id}"
    qr_path = generate_custom_qr(card_url, card_id)
    
    qr_file = FSInputFile(qr_path)
    await callback.message.answer_photo(
        qr_file, 
        caption=f"🎉 Ваша открытка готова!\n\nРаспечатайте этот QR-код. Когда его отсканируют, вы получите уведомление.\n\nСсылка на открытку: {card_url}"
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Создание отменено. Нажмите 'Создать открытку 🌸', чтобы начать заново.")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

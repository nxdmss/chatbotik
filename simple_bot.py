#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРОСТЕЙШИЙ БОТ С НУЛЯ
Максимально простая версия
"""

import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Админ ID
ADMIN_ID = 1593426947

# Простое хранилище товаров (в памяти)
products = [
    {"id": 1, "title": "Футболка", "price": 1500, "description": "Крутая футболка"},
    {"id": 2, "title": "Джинсы", "price": 3000, "description": "Стильные джинсы"},
    {"id": 3, "title": "Кроссовки", "price": 5000, "description": "Удобные кроссовки"}
]

# Клавиатуры
def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [KeyboardButton(text="🛍️ Магазин", web_app=WebAppInfo(url="http://localhost:8000"))],
        [KeyboardButton(text="📞 Связаться с администратором")],
        [KeyboardButton(text="⭐ Отзывы")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_keyboard():
    """Админ клавиатура"""
    keyboard = [
        [KeyboardButton(text="🛍️ Магазин", web_app=WebAppInfo(url="http://localhost:8000"))],
        [KeyboardButton(text="⚙️ Админ панель", web_app=WebAppInfo(url="http://localhost:8000/admin"))],
        [KeyboardButton(text="📞 Связаться с администратором")],
        [KeyboardButton(text="⭐ Отзывы")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    logger.info(f"Пользователь {user_id} запустил бота")
    
    if user_id == ADMIN_ID:
        # Админ
        await message.answer(
            "👋 Добро пожаловать, администратор!\n\n"
            "У вас есть доступ к админ панели.",
            reply_markup=get_admin_keyboard()
        )
    else:
        # Обычный пользователь
        await message.answer(
            "👋 Добро пожаловать в наш магазин!\n\n"
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )

@dp.message()
async def message_handler(message: types.Message):
    """Обработчик всех сообщений"""
    text = message.text
    user_id = message.from_user.id
    
    if text == "📞 Связаться с администратором":
        await message.answer(
            "📞 Для связи с администратором напишите @admin_username\n"
            "или оставьте сообщение, и мы с вами свяжемся!"
        )
    
    elif text == "⭐ Отзывы":
        await message.answer(
            "⭐ Отзывы:\n\n"
            "💬 Чтобы написать отзыв, просто отправьте сообщение с вашим отзывом.\n"
            "👀 Чтобы посмотреть отзывы, напишите 'отзывы'"
        )
    
    elif text.lower() == "отзывы":
        await message.answer(
            "⭐ Отзывы клиентов:\n\n"
            "👤 Анна: 'Отличный магазин, быстрая доставка!'\n"
            "👤 Максим: 'Качественные товары, рекомендую!'\n"
            "👤 Елена: 'Прекрасное обслуживание!'"
        )
    
    elif text.lower().startswith("отзыв") or "отзыв" in text.lower():
        await message.answer(
            "✅ Спасибо за ваш отзыв! Мы обязательно его учтем."
        )
    
    elif user_id == ADMIN_ID and text == "⚙️ Админ панель":
        await message.answer(
            "⚙️ Админ панель доступна через веб-приложение.\n"
            "Нажмите кнопку '⚙️ Админ панель' для входа."
        )
    
    else:
        # Обычное сообщение
        await message.answer(
            "Спасибо за сообщение! Мы его получили и обязательно ответим."
        )

async def main():
    """Главная функция"""
    logger.info("🚀 Запускаем простейшего бота...")
    
    if BOT_TOKEN == 'your_bot_token_here':
        logger.error("❌ Токен бота не настроен!")
        logger.info("📝 Создайте файл .env с BOT_TOKEN=ваш_токен")
        return
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

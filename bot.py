#!/usr/bin/env python3
# coding: utf-8

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
    WebAppInfo,
)

from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime

# Импортируем наши модули
from models import Product, CartItem, OrderCreate, Order, Review
from logger_config import setup_logging, bot_logger
from error_handlers import handle_errors, safe_send_message, validate_user_input, ValidationError
from database import db

# ======================
# 🔹 Настройки и переменные
# ======================

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-replit-url.replit.dev")

# Единственный администратор
ADMINS = ["1593426947"]

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

# Настраиваем логирование
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
bot_logger.logger.info("Bot starting up", admins_count=len(ADMINS))

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ======================
# 🔹 Состояния FSM
# ======================

class AdminStates(StatesGroup):
    waiting_for_note = State()

class ReviewStates(StatesGroup):
    waiting_for_review = State()

# ======================
# 🔹 Вспомогательные функции
# ======================

def is_admin(user_id: str) -> bool:
    """Проверка, является ли пользователь администратором"""
    return str(user_id) == "1593426947"

def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{price:.2f} ₽"

def get_user_name(user_id: int) -> str:
    """Получение имени пользователя"""
    try:
        return f"Пользователь {user_id}"
    except:
        return str(user_id)

# ======================
# 🔹 Клавиатуры
# ======================

def main_kb() -> ReplyKeyboardMarkup:
    """Основная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text="📞 Связаться с администратором"), KeyboardButton(text="⭐ Отзывы")],
            [KeyboardButton(text="❓ FAQ")]
        ],
        resize_keyboard=True
    )

def admin_kb() -> ReplyKeyboardMarkup:
    """Клавиатура администратора"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Клиенты")],
            [KeyboardButton(text="📞 Связаться с нами"), KeyboardButton(text="⭐ Отзывы")],
            [KeyboardButton(text="❓ FAQ")]
        ],
        resize_keyboard=True
    )

def reviews_kb() -> ReplyKeyboardMarkup:
    """Клавиатура отзывов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Написать отзыв")],
            [KeyboardButton(text="👀 Посмотреть отзывы")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_user_kb(user_id: str) -> ReplyKeyboardMarkup:
    """Клавиатура пользователя"""
    if is_admin(user_id):
        return admin_kb()
    return main_kb()

# ======================
# 🔹 Обработчики команд
# ======================

@dp.message(Command("start"))
@handle_errors
async def start(msg: Message):
    """Обработчик команды /start"""
    user_id = str(msg.chat.id)
    
    # Регистрируем пользователя в базе данных
    await db.register_user(user_id, msg.from_user.username or "Без имени")
    
    bot_logger.logger.info("User started bot", user_id=user_id, username=msg.from_user.username)
    
    if is_admin(user_id):
        await msg.answer(
            f"👋 Привет, админ!\n\n"
            f"Добро пожаловать в панель управления магазином! 🛍️\n\n"
            f"Используйте кнопки ниже для управления:",
            reply_markup=admin_kb()
        )
    else:
        await msg.answer(
            f"👋 Привет, {msg.from_user.first_name}!\n\n"
            f"Добро пожаловать в наш магазин! 🛍️\n\n"
            f"Используйте кнопку ниже, чтобы открыть каталог:",
            reply_markup=main_kb()
        )

@dp.message(Command("myid"))
@handle_errors
async def cmd_myid(msg: Message):
    """Показать ID пользователя"""
    user_id = str(msg.chat.id)
    username = msg.from_user.username or "Без имени"
    
    await msg.answer(
        f"🆔 **Ваш Telegram ID:** `{user_id}`\n\n"
        f"👤 **Имя пользователя:** @{username}\n\n"
        f"📝 **Имя:** {msg.from_user.first_name or 'Не указано'}\n"
        f"📝 **Фамилия:** {msg.from_user.last_name or 'Не указано'}\n\n"
        f"💡 Чтобы стать администратором, отправьте этот ID разработчику.",
        parse_mode="Markdown"
    )

# ======================
# 🔹 Обработчики кнопок
# ======================

@dp.message(F.text == "📞 Связаться с нами")
@handle_errors
async def contact_us(msg: Message):
    """Обработчик кнопки 'Связаться с нами'"""
    user_id = str(msg.chat.id)
    
    await msg.answer(
        "📞 **Связаться с нами**\n\n"
        "Вы можете связаться с нами следующими способами:\n\n"
        "• Написать в этот чат\n"
        "• Использовать WebApp для заказа\n"
        "• Оставить отзыв через бота\n\n"
        "Мы ответим в течение 24 часов! ⏰",
        reply_markup=get_user_kb(user_id)
    )

@dp.message(F.text == "❓ FAQ")
@handle_errors
async def faq(msg: Message):
    """Обработчик кнопки FAQ"""
    user_id = str(msg.chat.id)
    
    await msg.answer(
        "❓ **Часто задаваемые вопросы**\n\n"
        "**Q: Как сделать заказ?**\n"
        "A: Нажмите кнопку '🛒 Каталог' и выберите товары в WebApp\n\n"
        "**Q: Как оплатить заказ?**\n"
        "A: Оплата происходит через Telegram Payments\n\n"
        "**Q: Сколько времени доставка?**\n"
        "A: Обычно 1-3 рабочих дня\n\n"
        "**Q: Можно ли отменить заказ?**\n"
        "A: Да, в течение 1 часа после оформления",
        reply_markup=get_user_kb(user_id)
    )

@dp.message(F.text == "📞 Связаться с администратором")
@handle_errors
async def contact_admin(msg: Message):
    """Обработчик кнопки 'Связаться с администратором'"""
    user_id = str(msg.chat.id)
    
    await msg.answer(
        "📞 **Связь с администратором**\n\n"
        "Напишите ваше сообщение, и администратор свяжется с вами в ближайшее время.\n\n"
        "💬 Просто отправьте текстовое сообщение в этот чат.\n"
        "⏰ Время ответа: до 24 часов",
        reply_markup=get_user_kb(user_id)
    )

@dp.message(F.text == "⭐ Отзывы")
@handle_errors
async def reviews_menu(msg: Message):
    """Обработчик кнопки 'Отзывы'"""
    user_id = str(msg.chat.id)
    
    await msg.answer(
        "⭐ **Отзывы**\n\n"
        "Здесь вы можете:\n"
        "• ✍️ Написать свой отзыв о нашем магазине\n"
        "• 👀 Посмотреть отзывы других покупателей\n\n"
        "Выберите действие:",
        reply_markup=reviews_kb()
    )

@dp.message(F.text == "✍️ Написать отзыв")
@handle_errors
async def write_review(msg: Message, state: FSMContext):
    """Обработчик кнопки 'Написать отзыв'"""
    user_id = str(msg.chat.id)
    
    # Проверяем, есть ли уже отзыв от этого пользователя
    reviews = await db.get_all_reviews()
    user_review = next((r for r in reviews if r['user_id'] == user_id), None)
    
    if user_review:
        await msg.answer(
            "⚠️ **Вы уже оставляли отзыв!**\n\n"
            f"Ваш отзыв:\n"
            f"⭐ Рейтинг: {user_review['rating']}/5\n"
            f"📝 Текст: {user_review['text']}\n"
            f"📅 Дата: {user_review['created_at']}\n"
            f"✅ Статус: {'Одобрен' if user_review['is_approved'] else 'На модерации'}",
            reply_markup=reviews_kb()
        )
        return
    
    await msg.answer(
        "✍️ **Написать отзыв**\n\n"
        "Пожалуйста, отправьте ваш отзыв в следующем формате:\n\n"
        "**Рейтинг (1-5):** [оценка]\n"
        "**Отзыв:** [текст отзыва]\n\n"
        "**Пример:**\n"
        "Рейтинг: 5\n"
        "Отзыв: Отличный магазин! Быстрая доставка, качественные товары. Рекомендую!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Назад")]],
            resize_keyboard=True
        )
    )
    
    await state.set_state(ReviewStates.waiting_for_review)

@dp.message(F.text == "👀 Посмотреть отзывы")
@handle_errors
async def view_reviews(msg: Message):
    """Обработчик кнопки 'Посмотреть отзывы'"""
    user_id = str(msg.chat.id)
    
    reviews = await db.get_approved_reviews(limit=10)
    
    if not reviews:
        await msg.answer(
            "👀 **Отзывы**\n\n"
            "😔 Пока нет одобренных отзывов.\n"
            "Станьте первым, кто оставит отзыв!",
            reply_markup=reviews_kb()
        )
        return
    
    response = "👀 **Отзывы наших покупателей**\n\n"
    
    for i, review in enumerate(reviews, 1):
        stars = "⭐" * review['rating']
        username = review['username']
        text = review['text']
        date = review['created_at'][:10]  # Только дата
        
        response += f"**{i}. {username}** {stars}\n"
        response += f"📝 {text}\n"
        response += f"📅 {date}\n\n"
    
    if len(response) > 4000:
        response = response[:4000] + "\n\n... (показаны последние отзывы)"
    
    await msg.answer(response, reply_markup=reviews_kb())

@dp.message(F.text == "🔙 Назад")
@handle_errors
async def back_to_main(msg: Message, state: FSMContext):
    """Обработчик кнопки 'Назад'"""
    user_id = str(msg.chat.id)
    await state.clear()
    
    await msg.answer(
        "🔙 Возвращаемся в главное меню",
        reply_markup=get_user_kb(user_id)
    )

@dp.message(F.text == "📊 Статистика")
@handle_errors
async def admin_stats(msg: Message):
    """Обработчик кнопки статистики (только для админов)"""
    user_id = str(msg.chat.id)
    
    if not is_admin(user_id):
        await msg.answer("❌ У вас нет прав для просмотра статистики.")
        return
    
    try:
        # Получаем статистику из базы данных
        products_count = len(db.get_products())
        orders = db.get_all_orders()
        orders_count = len(orders)
        total_revenue = sum(order['total_amount'] for order in orders)
        
        await msg.answer(
            f"📊 **Статистика магазина**\n\n"
            f"🛍️ **Товаров в каталоге:** {products_count}\n"
            f"📦 **Всего заказов:** {orders_count}\n"
            f"💰 **Общая выручка:** {format_price(total_revenue)}\n\n"
            f"📈 **За последние 7 дней:**\n"
            f"• Новых заказов: {len([o for o in orders if o.get('created_at', '') > '2024-01-01'])}\n"
            f"• Выручка: {format_price(sum(o['total_amount'] for o in orders if o.get('created_at', '') > '2024-01-01'))}",
            reply_markup=admin_kb()
        )
    except Exception as e:
        bot_logger.logger.error("Error getting stats", error=str(e))
        await msg.answer("❌ Ошибка при получении статистики.")

@dp.message(F.text == "👥 Клиенты")
@handle_errors
async def admin_clients(msg: Message):
    """Обработчик кнопки клиентов (только для админов)"""
    user_id = str(msg.chat.id)
    
    if not is_admin(user_id):
        await msg.answer("❌ У вас нет прав для просмотра клиентов.")
        return
    
    try:
        orders = db.get_all_orders()
        unique_clients = len(set(order['user_id'] for order in orders))
        
        await msg.answer(
            f"👥 **Клиенты**\n\n"
            f"👤 **Уникальных клиентов:** {unique_clients}\n"
            f"📦 **Всего заказов:** {len(orders)}\n\n"
            f"💡 Для детального просмотра используйте WebApp",
            reply_markup=admin_kb()
        )
    except Exception as e:
        bot_logger.logger.error("Error getting clients", error=str(e))
        await msg.answer("❌ Ошибка при получении данных о клиентах.")

# ======================
# 🔹 Обработчики WebApp
# ======================

@dp.message(F.web_app_data)
@handle_errors
async def handle_web_app_data(msg: Message):
    """Обработчик данных из WebApp"""
    user_id = str(msg.chat.id)
    
    try:
        # Парсим данные из WebApp
        data = json.loads(msg.web_app_data.data)
        action = data.get('action')
        
        if action == 'order':
            # Обработка заказа
            await process_order(msg, data)
        elif action == 'add_product' and is_admin(user_id):
            # Добавление товара (только для админов)
            await process_add_product(msg, data)
        else:
            await msg.answer("⚠️ Неподдерживаемое действие из WebApp.")
            
    except Exception as e:
        bot_logger.logger.error("Error processing webapp data", error=str(e))
        await msg.answer("❌ Ошибка при обработке данных из WebApp.")

async def process_order(msg: Message, data: dict):
    """Обработка заказа из WebApp"""
    user_id = str(msg.chat.id)
    
    try:
        # Валидируем данные заказа
        order_data = OrderCreate(
            text=f"Заказ из WebApp, {len(data.get('items', []))} позиций",
            items=[CartItem(**item) for item in data.get('items', [])],
            total=data.get('total', 0)
        )
        
        # Создаем заказ в базе данных
        order_id = await db.create_order(user_id, order_data)
        
        # Уведомляем админа
        try:
            await safe_send_message(
                bot, int(ADMINS[0]),
                f"🆕 **Новый заказ #{order_id}**\n\n"
                f"👤 **Клиент:** {msg.from_user.first_name}\n"
                f"💰 **Сумма:** {format_price(order_data.total)}\n"
                f"📦 **Позиций:** {len(order_data.items)}"
            )
        except Exception as e:
            bot_logger.logger.error("Error notifying admin", error=str(e))
        
        await msg.answer(
            f"✅ **Заказ #{order_id} создан!**\n\n"
            f"💰 **Сумма:** {format_price(order_data.total)}\n"
            f"📦 **Позиций:** {len(order_data.items)}\n\n"
            f"Администратор скоро свяжется для подтверждения.",
            reply_markup=get_user_kb(user_id)
        )
        
    except Exception as e:
        bot_logger.logger.error("Error processing order", error=str(e))
        await msg.answer("❌ Ошибка при создании заказа.")

async def process_add_product(msg: Message, data: dict):
    """Обработка добавления товара (только для админов)"""
    user_id = str(msg.chat.id)
    
    try:
        # Валидируем данные товара
        product_data = Product(**data.get('product', {}))
        
        # Добавляем товар в базу данных
        product_id = await db.create_product(product_data)
        
        await msg.answer(
            f"✅ **Товар добавлен!**\n\n"
            f"🆔 **ID:** {product_id}\n"
            f"📦 **Название:** {product_data.title}\n"
            f"💰 **Цена:** {format_price(product_data.price)}",
            reply_markup=admin_kb()
        )
        
    except Exception as e:
        bot_logger.logger.error("Error adding product", error=str(e))
        await msg.answer("❌ Ошибка при добавлении товара.")

# ======================
# 🔹 Обработчики состояний
# ======================

@dp.message(ReviewStates.waiting_for_review)
@handle_errors
async def process_review(msg: Message, state: FSMContext):
    """Обработчик получения отзыва"""
    user_id = str(msg.chat.id)
    text = msg.text
    
    try:
        # Парсим отзыв
        lines = text.strip().split('\n')
        rating = None
        review_text = ""
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('рейтинг'):
                try:
                    rating = int(line.split(':')[1].strip())
                    if rating < 1 or rating > 5:
                        rating = None
                except (ValueError, IndexError):
                    rating = None
            elif line.lower().startswith('отзыв'):
                review_text = ':'.join(line.split(':')[1:]).strip()
        
        # Валидация
        if not rating:
            await msg.answer(
                "❌ **Ошибка в рейтинге**\n\n"
                "Пожалуйста, укажите рейтинг от 1 до 5.\n"
                "**Пример:** Рейтинг: 5",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔙 Назад")]],
                    resize_keyboard=True
                )
            )
            return
        
        if not review_text or len(review_text) < 10:
            await msg.answer(
                "❌ **Ошибка в тексте отзыва**\n\n"
                "Пожалуйста, напишите отзыв минимум 10 символов.\n"
                "**Пример:** Отзыв: Отличный магазин! Рекомендую!",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="🔙 Назад")]],
                    resize_keyboard=True
                )
            )
            return
        
        # Получаем имя пользователя
        username = msg.from_user.username or msg.from_user.first_name or "Пользователь"
        
        # Добавляем отзыв в базу данных
        success = await db.add_review(user_id, username, review_text, rating)
        
        if success:
            await msg.answer(
                "✅ **Отзыв отправлен на модерацию!**\n\n"
                f"⭐ **Рейтинг:** {rating}/5\n"
                f"📝 **Отзыв:** {review_text}\n\n"
                "Спасибо за ваш отзыв! После модерации он появится в списке отзывов.",
                reply_markup=get_user_kb(user_id)
            )
            
            # Уведомляем админа
            for admin_id in ADMINS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"📝 **Новый отзыв на модерацию**\n\n"
                        f"👤 **Пользователь:** {username} (ID: {user_id})\n"
                        f"⭐ **Рейтинг:** {rating}/5\n"
                        f"📝 **Отзыв:** {review_text}\n\n"
                        f"Используйте команду /admin для управления отзывами"
                    )
                except Exception as e:
                    bot_logger.logger.error(f"Failed to notify admin {admin_id}: {e}")
        else:
            await msg.answer(
                "⚠️ **Ошибка отправки отзыва**\n\n"
                "Возможно, вы уже оставляли отзыв ранее. Попробуйте позже.",
                reply_markup=get_user_kb(user_id)
            )
    
    except Exception as e:
        bot_logger.logger.error(f"Error processing review: {e}")
        await msg.answer(
            "❌ **Ошибка обработки отзыва**\n\n"
            "Пожалуйста, проверьте формат и попробуйте снова.",
            reply_markup=get_user_kb(user_id)
        )
    
    finally:
        await state.clear()

# ======================
# 🔹 Обработчики платежей
# ======================

@dp.pre_checkout_query()
@handle_errors
async def handle_pre_checkout(pre: PreCheckoutQuery):
    """Обработчик pre-checkout запроса"""
    try:
        await bot.answer_pre_checkout_query(pre.id, ok=True)
        bot_logger.logger.info("Pre-checkout approved", query_id=pre.id)
    except Exception as e:
        bot_logger.logger.error("Pre-checkout error", error=str(e))
        try:
            await bot.answer_pre_checkout_query(pre.id, ok=False, error_message="Ошибка обработки платежа")
        except Exception:
            pass

@dp.message(F.successful_payment)
@handle_errors
async def handle_successful_payment(msg: Message):
    """Обработчик успешного платежа"""
    user_id = str(msg.chat.id)
    
    try:
        payment = msg.successful_payment
        order_id = payment.invoice_payload.split('_')[-1] if '_' in payment.invoice_payload else "unknown"
        
        # Обновляем статус заказа
        await db.update_order_status(order_id, 'paid')

        # Уведомляем админа
        try:
            await safe_send_message(
                bot, int(ADMINS[0]),
                f"💰 **Оплачен заказ #{order_id}**\n\n"
                f"👤 **Клиент:** {msg.from_user.first_name}\n"
                f"💳 **Сумма:** {format_price(payment.total_amount / 100)}"
            )
        except Exception as e:
            bot_logger.logger.error("Error notifying admin about payment", error=str(e))
        
        await msg.answer(
            "✅ **Оплата получена!**\n\n"
            "Спасибо за покупку! Ваш заказ в обработке.",
            reply_markup=get_user_kb(user_id)
        )
        
    except Exception as e:
        bot_logger.logger.error("Error processing payment", error=str(e))
        await msg.answer("❌ Ошибка при обработке платежа.")

# ======================
# 🔹 Обработчик всех остальных сообщений
# ======================

@dp.message()
@handle_errors
async def handle_message(msg: Message):
    """Обработчик всех остальных сообщений"""
    user_id = str(msg.chat.id)
    
    # Если это текстовое сообщение, обрабатываем как обращение к поддержке
    if msg.text and not msg.text.startswith('/'):
        try:
            # Валидируем сообщение
            validated_text = validate_user_input(msg.text, max_length=2000)
            
            # Отправляем админу
            try:
                await safe_send_message(
                    bot, int(ADMINS[0]),
                    f"💬 **Сообщение от клиента**\n\n"
                    f"👤 **Имя:** {msg.from_user.first_name}\n"
                    f"🆔 **ID:** {user_id}\n\n"
                    f"📝 **Сообщение:**\n{validated_text}"
                )
            except Exception as e:
                bot_logger.logger.error("Error sending message to admin", error=str(e))
            
            await msg.answer(
                "✅ **Сообщение отправлено!**\n\n"
                "Мы получили ваше сообщение и ответим в ближайшее время.",
                reply_markup=get_user_kb(user_id)
            )
            
        except ValidationError as e:
            await msg.answer(f"❌ {e.message}")
        except Exception as e:
            bot_logger.logger.error("Error processing message", error=str(e))
            await msg.answer("❌ Ошибка при отправке сообщения.")

# ======================
# 🔹 Основная функция
# ======================

async def main():
    """Основная функция запуска бота"""
    try:
        bot_logger.logger.info("Bot starting up", version="2.0", features=["validation", "logging", "error_handling"])
        print("🤖 Улучшенный бот запущен на aiogram 3.x с валидацией, логированием и обработкой ошибок!")
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        bot_logger.logger.error("Fatal error", error=str(e))
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

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
from models import Product, CartItem, OrderCreate, Order
from logger_config import setup_logging, bot_logger
from error_handlers import handle_errors, safe_send_message, validate_user_input, ValidationError
from database import db

# ======================
# 🔹 Настройки и переменные
# ======================

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-replit-url.replit.dev")

# Основные администраторы (всегда активны)
ADMINS = ["1593426947", "8226153553"]

# Добавляем админов из переменной окружения
env_admins = [x.strip() for x in os.getenv("ADMINS", "").split(",") if x.strip()]
for admin_id in env_admins:
    if admin_id not in ADMINS:
        ADMINS.append(admin_id)

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

# Добавляем дополнительных админов из файла admins.json
try:
    with open('webapp/admins.json', 'r', encoding='utf-8') as f:
        admins_data = json.load(f)
        for admin_id in admins_data.get('admins', []):
            if str(admin_id) not in ADMINS:
                ADMINS.append(str(admin_id))
except Exception as e:
    print(f"Ошибка загрузки админов: {e}")

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

# ======================
# 🔹 Вспомогательные функции
# ======================

def is_admin(user_id: str) -> bool:
    """Проверка, является ли пользователь администратором"""
    user_id_str = str(user_id)
    
    # Главный администратор всегда имеет права
    if user_id_str == "1593426947":
        return True
    
    return user_id_str in ADMINS

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
            [KeyboardButton(text="📞 Связаться с нами"), KeyboardButton(text="❓ FAQ")]
        ],
        resize_keyboard=True
    )

def admin_kb() -> ReplyKeyboardMarkup:
    """Клавиатура администратора"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Клиенты")],
            [KeyboardButton(text="📞 Связаться с нами"), KeyboardButton(text="❓ FAQ")]
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
        
        # Уведомляем админов
        for admin_id in ADMINS:
            try:
                await safe_send_message(
                    bot, int(admin_id),
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

        # Уведомляем админов
        for admin_id in ADMINS:
            try:
                await safe_send_message(
                    bot, int(admin_id),
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
            
            # Отправляем всем админам
            for admin_id in ADMINS:
                try:
                    await safe_send_message(
                        bot, int(admin_id),
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

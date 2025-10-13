#!/usr/bin/env python3
"""
🤖 БОТ ПОДДЕРЖКИ ДЛЯ СТАРЫХ ВЕРСИЙ
===================================
Совместим с python-telegram-bot 12.x и ниже
"""

import os
import sqlite3
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_IDS = [1593426947]  # Ваш ID как админа
SUPPORT_DATABASE_PATH = 'customer_support.db'

# База данных поддержки
def init_support_database():
    """Инициализация базы данных поддержки"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    # Таблица клиентов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица сообщений поддержки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_from_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Таблица отзывов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_number TEXT UNIQUE NOT NULL,
            order_data TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных поддержки инициализирована")

# Утилиты поддержки
def get_or_create_customer(user_id, username=None, first_name=None, last_name=None):
    """Получить или создать клиента"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    # Пытаемся найти существующего клиента
    cursor.execute('SELECT id FROM customers WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result:
        customer_id = result[0]
    else:
        # Создаем нового клиента
        cursor.execute('''
            INSERT INTO customers (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        customer_id = cursor.lastrowid
    
    # Обновляем последнюю активность
    cursor.execute('''
        UPDATE customers 
        SET last_activity = CURRENT_TIMESTAMP,
            username = COALESCE(?, username),
            first_name = COALESCE(?, first_name),
            last_name = COALESCE(?, last_name)
        WHERE id = ?
    ''', (username, first_name, last_name, customer_id))
    
    conn.commit()
    conn.close()
    return customer_id

def is_admin(user_id):
    """Проверить, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def start_command(bot, update):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    # Регистрируем или обновляем клиента
    get_or_create_customer(
        user_id, 
        user.username, 
        user.first_name, 
        user.last_name
    )
    
    if is_admin(user_id):
        # Меню для администратора
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        keyboard = [
            [KeyboardButton("📋 Список клиентов")],
            [KeyboardButton("💬 Сообщения поддержки"), KeyboardButton("⭐ Отзывы")],
            [KeyboardButton("📦 Заказы"), KeyboardButton("📊 Статистика")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            "👑 *Добро пожаловать в панель администратора!*\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Меню для клиента
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        keyboard = [
            [KeyboardButton("📞 Связь с администратором")],
            [KeyboardButton("⭐ Отзывы")],
            [KeyboardButton("📦 Мои заказы")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            "👋 *Добро пожаловать!*\n\n"
            "Я помогу вам связаться с администратором или оставить отзыв.\n\n"
            "Выберите нужное действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def handle_support_text(bot, update):
    """Обработчик текстовых сообщений поддержки"""
    user = update.effective_user
    user_id = user.id
    message_text = update.message.text
    
    if is_admin(user_id):
        handle_admin_message(bot, update)
    else:
        handle_customer_message(bot, update)

def handle_customer_message(bot, update):
    """Обработка сообщений от клиентов"""
    user = update.effective_user
    user_id = user.id
    message_text = update.message.text
    
    if message_text == "📞 Связь с администратором":
        update.message.reply_text(
            "💬 *Связь с администратором*\n\n"
            "Напишите ваш вопрос или сообщение, и администратор ответит вам в ближайшее время.\n\n"
            "Просто отправьте сообщение, и оно будет передано администратору.",
            parse_mode='Markdown'
        )
        
    elif message_text == "⭐ Отзывы":
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("📝 Оставить отзыв", callback_data="leave_review")],
            [InlineKeyboardButton("👀 Посмотреть отзывы", callback_data="view_reviews")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "⭐ *Отзывы*\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    elif message_text == "📦 Мои заказы":
        show_customer_orders(bot, update)
        
    else:
        # Сообщение для администратора
        forward_to_admin(bot, update)

def handle_admin_message(bot, update):
    """Обработка сообщений от администратора"""
    message_text = update.message.text
    
    if message_text == "📋 Список клиентов":
        show_customers_list(bot, update)
    elif message_text == "💬 Сообщения поддержки":
        show_support_messages(bot, update)
    elif message_text == "⭐ Отзывы":
        show_admin_reviews(bot, update)
    elif message_text == "📦 Заказы":
        show_admin_orders(bot, update)
    elif message_text == "📊 Статистика":
        show_statistics(bot, update)
    else:
        # Проверяем, не является ли это ответом на сообщение клиента
        handle_admin_reply(bot, update)

def forward_to_admin(bot, update):
    """Пересылка сообщения клиента администратору"""
    user = update.effective_user
    user_id = user.id
    message_text = update.message.text
    
    # Сохраняем сообщение в базу данных
    customer_id = get_or_create_customer(user_id, user.username, user.first_name, user.last_name)
    
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO support_messages (customer_id, message, is_from_admin)
        VALUES (?, ?, FALSE)
    ''', (customer_id, message_text))
    conn.commit()
    conn.close()
    
    # Отправляем сообщение всем администраторам
    admin_message = (
        f"📞 *Новое сообщение от клиента*\n\n"
        f"👤 Клиент: {user.first_name or 'Неизвестно'}"
        f"{' (@' + user.username + ')' if user.username else ''}\n"
        f"🆔 ID: {user_id}\n\n"
        f"💬 Сообщение:\n{message_text}\n\n"
        f"Для ответа используйте команду /reply {user_id} <ваш ответ>"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения админу {admin_id}: {e}")
    
    update.message.reply_text(
        "✅ *Ваше сообщение отправлено администратору*\n\n"
        "Мы получили ваше сообщение и ответим в ближайшее время!",
        parse_mode='Markdown'
    )

def show_customers_list(bot, update):
    """Показать список клиентов"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, last_activity,
               COUNT(sm.id) as messages_count
        FROM customers c
        LEFT JOIN support_messages sm ON c.id = sm.customer_id
        GROUP BY c.id
        ORDER BY last_activity DESC
        LIMIT 20
    ''')
    
    customers = cursor.fetchall()
    conn.close()
    
    if not customers:
        update.message.reply_text("📋 *Список клиентов*\n\nКлиентов пока нет.")
        return
    
    message = "📋 *Список клиентов*\n\n"
    
    for customer in customers:
        user_id, username, first_name, last_name, last_activity, messages_count = customer
        
        name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
        message += (
            f"👤 *{name}*\n"
            f"🆔 ID: `{user_id}`\n"
            f"💬 Сообщений: {messages_count}\n"
            f"⏰ Активность: {last_activity[:16]}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def show_support_messages(bot, update):
    """Показать сообщения поддержки"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sm.id, c.user_id, c.first_name, c.username, sm.message, 
               sm.is_from_admin, sm.created_at
        FROM support_messages sm
        JOIN customers c ON sm.customer_id = c.id
        ORDER BY sm.created_at DESC
        LIMIT 10
    ''')
    
    messages = cursor.fetchall()
    conn.close()
    
    if not messages:
        update.message.reply_text("💬 *Сообщения поддержки*\n\nСообщений пока нет.")
        return
    
    message = "💬 *Последние сообщения поддержки*\n\n"
    
    for msg in messages:
        msg_id, user_id, first_name, username, msg_text, is_from_admin, created_at = msg
        
        sender = "👑 Админ" if is_from_admin else f"👤 {first_name or username or 'Клиент'}"
        
        message += (
            f"{sender}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💬 {msg_text[:100]}{'...' if len(msg_text) > 100 else ''}\n"
            f"⏰ {created_at[:16]}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def show_admin_reviews(bot, update):
    """Показать отзывы для администратора"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.rating, r.review_text, c.first_name, c.username, r.created_at
        FROM reviews r
        JOIN customers c ON r.customer_id = c.id
        ORDER BY r.created_at DESC
        LIMIT 10
    ''')
    
    reviews = cursor.fetchall()
    conn.close()
    
    if not reviews:
        update.message.reply_text("⭐ *Отзывы*\n\nОтзывов пока нет.")
        return
    
    message = "⭐ *Последние отзывы*\n\n"
    
    for review in reviews:
        rating, review_text, first_name, username, created_at = review
        
        stars = "⭐" * rating
        name = first_name or username or "Аноним"
        
        message += (
            f"{stars} *{name}*\n"
            f"💬 {review_text or 'Без текста'}\n"
            f"⏰ {created_at[:16]}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def show_customer_orders(bot, update):
    """Показать заказы клиента"""
    user = update.effective_user
    user_id = user.id
    
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT order_number, order_data, status, created_at
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE c.user_id = ?
        ORDER BY o.created_at DESC
        LIMIT 10
    ''', (user_id,))
    
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        update.message.reply_text(
            "📦 *Мои заказы*\n\n"
            "У вас пока нет заказов.\n\n"
            "Для создания заказа обратитесь к администратору."
        )
        return
    
    message = "📦 *Мои заказы*\n\n"
    
    for order in orders:
        order_number, order_data, status, created_at = order
        
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'shipped': '🚚',
            'delivered': '🎉',
            'cancelled': '❌'
        }.get(status, '❓')
        
        message += (
            f"{status_emoji} *Заказ #{order_number}*\n"
            f"📦 Статус: {status}\n"
            f"📅 Дата: {created_at[:16]}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def show_admin_orders(bot, update):
    """Показать заказы для администратора"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT o.order_number, c.first_name, c.username, o.status, o.created_at
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        ORDER BY o.created_at DESC
        LIMIT 15
    ''')
    
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        update.message.reply_text("📦 *Заказы*\n\nЗаказов пока нет.")
        return
    
    message = "📦 *Последние заказы*\n\n"
    
    for order in orders:
        order_number, first_name, username, status, created_at = order
        
        name = first_name or username or "Неизвестно"
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'shipped': '🚚',
            'delivered': '🎉',
            'cancelled': '❌'
        }.get(status, '❓')
        
        message += (
            f"{status_emoji} *#{order_number}* - {name}\n"
            f"📊 Статус: {status}\n"
            f"📅 {created_at[:16]}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='Markdown')

def show_statistics(bot, update):
    """Показать статистику"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute('SELECT COUNT(*) FROM customers')
    total_customers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM support_messages WHERE is_from_admin = FALSE')
    total_messages = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM reviews')
    total_reviews = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM orders')
    total_orders = cursor.fetchone()[0]
    
    # Средний рейтинг
    cursor.execute('SELECT AVG(rating) FROM reviews')
    avg_rating = cursor.fetchone()[0] or 0
    
    conn.close()
    
    message = (
        "📊 *Статистика*\n\n"
        f"👥 Всего клиентов: {total_customers}\n"
        f"💬 Сообщений поддержки: {total_messages}\n"
        f"⭐ Отзывов: {total_reviews}\n"
        f"📦 Заказов: {total_orders}\n"
        f"⭐ Средний рейтинг: {avg_rating:.1f}/5"
    )
    
    update.message.reply_text(message, parse_mode='Markdown')

def callback_query_handler(bot, update):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    user = update.effective_user
    user_id = user.id
    
    if data == "leave_review":
        leave_review(bot, update)
    elif data == "view_reviews":
        view_reviews(bot, update)
    elif data.startswith("rating_"):
        rating = int(data.split("_")[1])
        process_review_rating(bot, update, rating)

def leave_review(bot, update):
    """Начать процесс оставления отзыва"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("⭐", callback_data="rating_1"),
         InlineKeyboardButton("⭐⭐", callback_data="rating_2"),
         InlineKeyboardButton("⭐⭐⭐", callback_data="rating_3"),
         InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_4"),
         InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.callback_query.edit_message_text(
        "⭐ *Оставить отзыв*\n\n"
        "Выберите оценку от 1 до 5 звезд:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def process_review_rating(bot, update, rating):
    """Обработка выбора рейтинга"""
    user = update.effective_user
    user_id = user.id
    
    # Сохраняем рейтинг в глобальном хранилище (упрощенно)
    global pending_ratings
    if 'pending_ratings' not in globals():
        pending_ratings = {}
    pending_ratings[user_id] = rating
    
    update.callback_query.edit_message_text(
        f"⭐ *Оценка: {'⭐' * rating}*\n\n"
        "Теперь напишите ваш отзыв (или отправьте 'пропустить' чтобы оставить только оценку):",
        parse_mode='Markdown'
    )

def view_reviews(bot, update):
    """Показать отзывы клиенту"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.rating, r.review_text, c.first_name, r.created_at
        FROM reviews r
        JOIN customers c ON r.customer_id = c.id
        ORDER BY r.created_at DESC
        LIMIT 10
    ''')
    
    reviews = cursor.fetchall()
    conn.close()
    
    if not reviews:
        update.callback_query.edit_message_text(
            "👀 *Отзывы*\n\n"
            "Пока нет отзывов. Станьте первым!"
        )
        return
    
    message = "👀 *Отзывы наших клиентов*\n\n"
    
    for review in reviews:
        rating, review_text, first_name, created_at = review
        
        stars = "⭐" * rating
        name = first_name or "Аноним"
        
        message += (
            f"{stars} *{name}*\n"
            f"💬 {review_text or 'Без текста'}\n"
            f"📅 {created_at[:16]}\n\n"
        )
    
    update.callback_query.edit_message_text(message, parse_mode='Markdown')

def handle_admin_reply(bot, update):
    """Обработка ответов администратора"""
    update.message.reply_text(
        "💬 *Сообщение получено*\n\n"
        "Для ответа клиенту используйте команду /reply <user_id> <сообщение>",
        parse_mode='Markdown'
    )

def reply_command(bot, update):
    """Команда для ответа клиенту"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    args = update.message.text.split()[1:]  # Убираем /reply
    if len(args) < 2:
        update.message.reply_text(
            "❌ Неверный формат команды.\n"
            "Используйте: /reply <user_id> <сообщение>"
        )
        return
    
    try:
        user_id = int(args[0])
        message_text = " ".join(args[1:])
        
        # Отправляем сообщение клиенту
        bot.send_message(
            chat_id=user_id,
            text=f"💬 *Ответ от администратора*\n\n{message_text}",
            parse_mode='Markdown'
        )
        
        # Сохраняем в базу данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM customers WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            customer_id = result[0]
            cursor.execute('''
                INSERT INTO support_messages (customer_id, message, is_from_admin)
                VALUES (?, ?, TRUE)
            ''', (customer_id, message_text))
        
        conn.commit()
        conn.close()
        
        update.message.reply_text(f"✅ Ответ отправлен пользователю {user_id}")
        
    except ValueError:
        update.message.reply_text("❌ Неверный ID пользователя.")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка отправки: {e}")

def create_order_command(bot, update):
    """Команда для создания заказа"""
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
        return
    
    args = update.message.text.split()[1:]  # Убираем /order
    if len(args) < 2:
        update.message.reply_text(
            "❌ Неверный формат команды.\n"
            "Используйте: /order <user_id> <описание_заказа>"
        )
        return
    
    try:
        user_id = int(args[0])
        order_description = " ".join(args[1:])
        
        # Генерируем номер заказа
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Сохраняем заказ в базу данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM customers WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            update.message.reply_text("❌ Пользователь не найден в базе данных.")
            conn.close()
            return
        
        customer_id = result[0]
        
        cursor.execute('''
            INSERT INTO orders (customer_id, order_number, order_data, status)
            VALUES (?, ?, ?, 'pending')
        ''', (customer_id, order_number, order_description))
        
        conn.commit()
        conn.close()
        
        # Уведомляем клиента о создании заказа
        bot.send_message(
            chat_id=user_id,
            text=f"📦 *Новый заказ создан!*\n\n"
                 f"🆔 Номер заказа: #{order_number}\n"
                 f"📝 Описание: {order_description}\n"
                 f"📊 Статус: В обработке\n\n"
                 f"Следите за статусом в разделе 'Мои заказы'",
            parse_mode='Markdown'
        )
        
        update.message.reply_text(
            f"✅ Заказ #{order_number} создан для пользователя {user_id}"
        )
        
    except ValueError:
        update.message.reply_text("❌ Неверный ID пользователя.")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка создания заказа: {e}")

def error_handler(bot, update, error):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {error}")

def main():
    """Главная функция"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        print("💡 Установите переменную окружения BOT_TOKEN")
        return
    
    print("🤖 ЗАПУСК БОТА ПОДДЕРЖКИ КЛИЕНТОВ (LEGACY)")
    print("=" * 50)
    
    # Инициализация базы данных
    init_support_database()
    
    # Импорт telegram для старой версии
    try:
        from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
        from telegram.error import TelegramError
    except ImportError as e:
        print(f"❌ Ошибка импорта telegram: {e}")
        print("💡 Попробуйте установить: pip install python-telegram-bot==12.8")
        return
    
    # Создание приложения
    updater = Updater(token=BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    # Добавление обработчиков
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("reply", reply_command))
    dispatcher.add_handler(CommandHandler("order", create_order_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_support_text))
    dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))
    dispatcher.add_error_handler(error_handler)
    
    print("✅ Бот поддержки запущен и готов к работе!")
    print("📞 Клиенты могут писать сообщения администраторам")
    print("⭐ Система отзывов активна")
    print("📊 Статистика и заказы доступны админам")
    print("=" * 50)
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

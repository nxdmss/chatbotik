#!/usr/bin/env python3
"""
🤖 МИНИМАЛЬНЫЙ БОТ ПОДДЕРЖКИ
============================
Работает с самыми старыми версиями python-telegram-bot
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
    try:
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
            message = (
                "👑 Добро пожаловать в панель администратора!\n\n"
                "Доступные команды:\n"
                "📋 /customers - Список клиентов\n"
                "💬 /messages - Сообщения поддержки\n"
                "⭐ /reviews - Отзывы клиентов\n"
                "📦 /orders - Заказы\n"
                "📊 /stats - Статистика\n\n"
                "Для ответа клиенту: /reply <user_id> <сообщение>\n"
                "Для создания заказа: /order <user_id> <описание>"
            )
        else:
            # Меню для клиента
            message = (
                "👋 Добро пожаловать!\n\n"
                "Я помогу вам связаться с администратором или оставить отзыв.\n\n"
                "Доступные команды:\n"
                "📞 /support - Связь с администратором\n"
                "⭐ /reviews - Отзывы\n"
                "📦 /myorders - Мои заказы\n\n"
                "Просто напишите сообщение, и оно будет передано администратору."
            )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}")
        update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

def handle_text(bot, update):
    """Обработчик текстовых сообщений"""
    try:
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        if is_admin(user_id):
            handle_admin_message(bot, update)
        else:
            handle_customer_message(bot, update)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_text: {e}")
        update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

def handle_customer_message(bot, update):
    """Обработка сообщений от клиентов"""
    try:
        # Сообщение для администратора
        forward_to_admin(bot, update)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_message: {e}")

def handle_admin_message(bot, update):
    """Обработка сообщений от администратора"""
    try:
        update.message.reply_text(
            "💬 Сообщение получено\n\n"
            "Для ответа клиенту используйте команду /reply <user_id> <сообщение>"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_admin_message: {e}")

def forward_to_admin(bot, update):
    """Пересылка сообщения клиента администратору"""
    try:
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
            f"📞 Новое сообщение от клиента\n\n"
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
                    text=admin_message
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения админу {admin_id}: {e}")
        
        update.message.reply_text(
            "✅ Ваше сообщение отправлено администратору\n\n"
            "Мы получили ваше сообщение и ответим в ближайшее время!"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в forward_to_admin: {e}")

def support_command(bot, update):
    """Команда связи с администратором"""
    try:
        update.message.reply_text(
            "💬 Связь с администратором\n\n"
            "Напишите ваш вопрос или сообщение, и администратор ответит вам в ближайшее время.\n\n"
            "Просто отправьте сообщение, и оно будет передано администратору."
        )
    except Exception as e:
        logger.error(f"Ошибка в support_command: {e}")

def reviews_command(bot, update):
    """Команда отзывов"""
    try:
        user = update.effective_user
        user_id = user.id
        
        if is_admin(user_id):
            show_admin_reviews(bot, update)
        else:
            show_customer_reviews(bot, update)
            
    except Exception as e:
        logger.error(f"Ошибка в reviews_command: {e}")

def show_customer_reviews(bot, update):
    """Показать отзывы клиенту"""
    try:
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
            update.message.reply_text(
                "👀 Отзывы\n\n"
                "Пока нет отзывов. Станьте первым!\n\n"
                "Для оставления отзыва используйте /rate <оценка> <отзыв>\n"
                "Например: /rate 5 Отличный сервис!"
            )
            return
        
        message = "👀 Отзывы наших клиентов\n\n"
        
        for review in reviews:
            rating, review_text, first_name, created_at = review
            
            stars = "⭐" * rating
            name = first_name or "Аноним"
            
            message += (
                f"{stars} {name}\n"
                f"💬 {review_text or 'Без текста'}\n"
                f"📅 {created_at[:16]}\n\n"
            )
        
        message += "Для оставления отзыва используйте /rate <оценка> <отзыв>"
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в show_customer_reviews: {e}")

def rate_command(bot, update):
    """Команда для оставления отзыва"""
    try:
        user = update.effective_user
        user_id = user.id
        
        # Парсим команду /rate <оценка> <отзыв>
        args = update.message.text.split()[1:]  # Убираем /rate
        
        if len(args) < 1:
            update.message.reply_text(
                "❌ Неверный формат команды.\n"
                "Используйте: /rate <оценка> <отзыв>\n"
                "Например: /rate 5 Отличный сервис!"
            )
            return
        
        try:
            rating = int(args[0])
            if rating < 1 or rating > 5:
                update.message.reply_text("❌ Оценка должна быть от 1 до 5.")
                return
            
            review_text = " ".join(args[1:]) if len(args) > 1 else "Только оценка"
            
            # Сохраняем отзыв
            customer_id = get_or_create_customer(user_id, user.username, user.first_name, user.last_name)
            
            conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
            cursor = conn.cursor()
            
            # Проверяем, не оставлял ли уже отзыв этот пользователь
            cursor.execute('SELECT id FROM reviews WHERE customer_id = ?', (customer_id,))
            existing_review = cursor.fetchone()
            
            if existing_review:
                # Обновляем существующий отзыв
                cursor.execute('''
                    UPDATE reviews 
                    SET rating = ?, review_text = ?, created_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                ''', (rating, review_text, customer_id))
                message = "✅ Отзыв обновлен!"
            else:
                # Создаем новый отзыв
                cursor.execute('''
                    INSERT INTO reviews (customer_id, rating, review_text)
                    VALUES (?, ?, ?)
                ''', (customer_id, rating, review_text))
                message = "✅ Отзыв сохранен!"
            
            conn.commit()
            conn.close()
            
            stars = "⭐" * rating
            update.message.reply_text(
                f"{message}\n\n"
                f"⭐ Оценка: {stars}\n"
                f"💬 Отзыв: {review_text}\n\n"
                f"Спасибо за ваш отзыв!"
            )
            
        except ValueError:
            update.message.reply_text("❌ Оценка должна быть числом от 1 до 5.")
            
    except Exception as e:
        logger.error(f"Ошибка в rate_command: {e}")

def myorders_command(bot, update):
    """Команда моих заказов"""
    try:
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
                "📦 Мои заказы\n\n"
                "У вас пока нет заказов.\n\n"
                "Для создания заказа обратитесь к администратору."
            )
            return
        
        message = "📦 Мои заказы\n\n"
        
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
                f"{status_emoji} Заказ #{order_number}\n"
                f"📦 Статус: {status}\n"
                f"📅 Дата: {created_at[:16]}\n\n"
            )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в myorders_command: {e}")

def customers_command(bot, update):
    """Команда списка клиентов (только для админов)"""
    try:
        if not is_admin(update.effective_user.id):
            update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
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
            update.message.reply_text("📋 Список клиентов\n\nКлиентов пока нет.")
            return
        
        message = "📋 Список клиентов\n\n"
        
        for customer in customers:
            user_id, username, first_name, last_name, last_activity, messages_count = customer
            
            name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
            message += (
                f"👤 {name}\n"
                f"🆔 ID: {user_id}\n"
                f"💬 Сообщений: {messages_count}\n"
                f"⏰ Активность: {last_activity[:16]}\n\n"
            )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в customers_command: {e}")

def messages_command(bot, update):
    """Команда сообщений поддержки (только для админов)"""
    try:
        if not is_admin(update.effective_user.id):
            update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
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
            update.message.reply_text("💬 Сообщения поддержки\n\nСообщений пока нет.")
            return
        
        message = "💬 Последние сообщения поддержки\n\n"
        
        for msg in messages:
            msg_id, user_id, first_name, username, msg_text, is_from_admin, created_at = msg
            
            sender = "👑 Админ" if is_from_admin else f"👤 {first_name or username or 'Клиент'}"
            
            message += (
                f"{sender}\n"
                f"🆔 ID: {user_id}\n"
                f"💬 {msg_text[:100]}{'...' if len(msg_text) > 100 else ''}\n"
                f"⏰ {created_at[:16]}\n\n"
            )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в messages_command: {e}")

def show_admin_reviews(bot, update):
    """Показать отзывы для администратора"""
    try:
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
            update.message.reply_text("⭐ Отзывы\n\nОтзывов пока нет.")
            return
        
        message = "⭐ Последние отзывы\n\n"
        
        for review in reviews:
            rating, review_text, first_name, username, created_at = review
            
            stars = "⭐" * rating
            name = first_name or username or "Аноним"
            
            message += (
                f"{stars} {name}\n"
                f"💬 {review_text or 'Без текста'}\n"
                f"⏰ {created_at[:16]}\n\n"
            )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в show_admin_reviews: {e}")

def orders_command(bot, update):
    """Команда заказов (только для админов)"""
    try:
        if not is_admin(update.effective_user.id):
            update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
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
            update.message.reply_text("📦 Заказы\n\nЗаказов пока нет.")
            return
        
        message = "📦 Последние заказы\n\n"
        
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
                f"{status_emoji} #{order_number} - {name}\n"
                f"📊 Статус: {status}\n"
                f"📅 {created_at[:16]}\n\n"
            )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в orders_command: {e}")

def stats_command(bot, update):
    """Команда статистики (только для админов)"""
    try:
        if not is_admin(update.effective_user.id):
            update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
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
            "📊 Статистика\n\n"
            f"👥 Всего клиентов: {total_customers}\n"
            f"💬 Сообщений поддержки: {total_messages}\n"
            f"⭐ Отзывов: {total_reviews}\n"
            f"📦 Заказов: {total_orders}\n"
            f"⭐ Средний рейтинг: {avg_rating:.1f}/5"
        )
        
        update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка в stats_command: {e}")

def reply_command(bot, update):
    """Команда для ответа клиенту"""
    try:
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
        
        user_id = int(args[0])
        message_text = " ".join(args[1:])
        
        # Отправляем сообщение клиенту
        bot.send_message(
            chat_id=user_id,
            text=f"💬 Ответ от администратора\n\n{message_text}"
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
        logger.error(f"Ошибка в reply_command: {e}")
        update.message.reply_text(f"❌ Ошибка отправки: {e}")

def order_command(bot, update):
    """Команда для создания заказа"""
    try:
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
            text=f"📦 Новый заказ создан!\n\n"
                 f"🆔 Номер заказа: #{order_number}\n"
                 f"📝 Описание: {order_description}\n"
                 f"📊 Статус: В обработке\n\n"
                 f"Следите за статусом командой /myorders"
        )
        
        update.message.reply_text(
            f"✅ Заказ #{order_number} создан для пользователя {user_id}"
        )
        
    except ValueError:
        update.message.reply_text("❌ Неверный ID пользователя.")
    except Exception as e:
        logger.error(f"Ошибка в order_command: {e}")
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
    
    print("🤖 ЗАПУСК МИНИМАЛЬНОГО БОТА ПОДДЕРЖКИ")
    print("=" * 50)
    
    # Инициализация базы данных
    init_support_database()
    
    # Пробуем импортировать telegram с минимальными требованиями
    try:
        # Пробуем разные варианты импорта
        try:
            from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
            print("✅ Импорт telegram успешен (современная версия)")
        except ImportError:
            try:
                from telegram.ext import Updater, CommandHandler, MessageHandler
                from telegram import Filters
                print("✅ Импорт telegram успешен (средняя версия)")
            except ImportError:
                # Последняя попытка - очень старая версия
                import telegram
                from telegram.ext import Updater, CommandHandler, MessageHandler
                print("✅ Импорт telegram успешен (старая версия)")
                
    except ImportError as e:
        print(f"❌ Ошибка импорта telegram: {e}")
        print("💡 Попробуйте установить: pip install python-telegram-bot")
        return
    
    try:
        # Создание приложения
        updater = Updater(token=BOT_TOKEN)
        dispatcher = updater.dispatcher
        
        # Добавление обработчиков
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("support", support_command))
        dispatcher.add_handler(CommandHandler("reviews", reviews_command))
        dispatcher.add_handler(CommandHandler("rate", rate_command))
        dispatcher.add_handler(CommandHandler("myorders", myorders_command))
        dispatcher.add_handler(CommandHandler("customers", customers_command))
        dispatcher.add_handler(CommandHandler("messages", messages_command))
        dispatcher.add_handler(CommandHandler("orders", orders_command))
        dispatcher.add_handler(CommandHandler("stats", stats_command))
        dispatcher.add_handler(CommandHandler("reply", reply_command))
        dispatcher.add_handler(CommandHandler("order", order_command))
        
        # Пробуем добавить обработчик текста
        try:
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        except:
            try:
                dispatcher.add_handler(MessageHandler(Filters.text, handle_text))
            except:
                # Если ничего не работает, добавляем без фильтров
                dispatcher.add_handler(MessageHandler(None, handle_text))
        
        dispatcher.add_error_handler(error_handler)
        
        print("✅ Бот поддержки запущен и готов к работе!")
        print("📞 Клиенты могут писать сообщения администраторам")
        print("⭐ Система отзывов активна")
        print("📊 Статистика и заказы доступны админам")
        print("=" * 50)
        
        # Запуск бота
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

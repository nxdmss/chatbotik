#!/usr/bin/env python3
"""
🤖 БОТ БЕЗ TELEGRAM БИБЛИОТЕКИ
==============================
Работает вообще без python-telegram-bot
Использует только HTTP API Telegram
"""

import os
import sqlite3
import logging
import json
import requests
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
TELEGRAM_API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

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

# Функции для создания клавиатур
def create_reply_keyboard(keyboard_layout, resize_keyboard=True, one_time_keyboard=False):
    """Создать reply клавиатуру"""
    return {
        'keyboard': keyboard_layout,
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyboard
    }

def create_inline_keyboard(inline_layout):
    """Создать inline клавиатуру"""
    return {
        'inline_keyboard': inline_layout
    }

def get_admin_keyboard():
    """Получить главную клавиатуру для администратора"""
    keyboard = [
        ['📋 Клиенты'],
        ['⭐ Отзывы', '📊 Статистика']
    ]
    return create_reply_keyboard(keyboard)

def get_customer_detail_keyboard(customer_id):
    """Получить клавиатуру для детального просмотра клиента"""
    keyboard = [
        ['💬 Чат с клиентом', '📦 Заказы клиента'],
        ['⭐ Отзывы клиента'],
        ['🔙 Назад к списку клиентов']
    ]
    return create_reply_keyboard(keyboard)

def get_chat_history_keyboard(customer_id):
    """Получить клавиатуру для истории чата с клиентом"""
    keyboard = [
        ['💬 Отправить сообщение'],
        ['🔙 Назад к клиенту']
    ]
    return create_reply_keyboard(keyboard)

def get_client_keyboard():
    """Получить главную клавиатуру для клиента"""
    keyboard = [
        ['📞 Поддержка'],
        ['⭐ Отзывы', '📦 Мои заказы']
    ]
    return create_reply_keyboard(keyboard)

def get_back_keyboard():
    """Получить клавиатуру с кнопкой Назад"""
    keyboard = [
        ['🔙 Назад']
    ]
    return create_reply_keyboard(keyboard)

def get_support_keyboard():
    """Получить клавиатуру поддержки"""
    keyboard = [
        ['📝 Написать сообщение'],
        ['🔙 Назад']
    ]
    return create_reply_keyboard(keyboard)

def get_reviews_keyboard():
    """Получить клавиатуру отзывов"""
    keyboard = [
        ['⭐ Оставить отзыв'],
        ['👀 Посмотреть отзывы'],
        ['🔙 Назад']
    ]
    return create_reply_keyboard(keyboard)

def get_rating_keyboard():
    """Получить клавиатуру для выбора рейтинга"""
    keyboard = [
        ['⭐ 1', '⭐⭐ 2', '⭐⭐⭐ 3'],
        ['⭐⭐⭐⭐ 4', '⭐⭐⭐⭐⭐ 5'],
        ['🔙 Назад']
    ]
    return create_reply_keyboard(keyboard)

# Telegram API функции
def send_message(chat_id, text, reply_markup=None):
    """Отправить сообщение через Telegram API"""
    try:
        url = f'{TELEGRAM_API_URL}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = reply_markup
            print(f"🔍 DEBUG: Отправляем сообщение с reply_markup: {reply_markup}")
        
        response = requests.post(url, json=data, timeout=10)
        print(f"🔍 DEBUG: Ответ Telegram API: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return False

def get_updates(offset=None):
    """Получить обновления от Telegram"""
    try:
        url = f'{TELEGRAM_API_URL}/getUpdates'
        params = {'timeout': 30}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Ошибка получения обновлений: {e}")
        return None

def answer_callback_query(callback_query_id, text=None, show_alert=False):
    """Ответить на callback query"""
    try:
        url = f'{TELEGRAM_API_URL}/answerCallbackQuery'
        data = {
            'callback_query_id': callback_query_id,
            'show_alert': show_alert
        }
        if text:
            data['text'] = text
        
        response = requests.post(url, json=data, timeout=10)
        print(f"🔍 DEBUG: Ответ на callback query: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ошибка ответа на callback query: {e}")
        return False

# Обработчики команд
def handle_start_command(user_id, username, first_name, last_name):
    """Обработчик команды /start"""
    try:
        # Регистрируем или обновляем клиента
        get_or_create_customer(user_id, username, first_name, last_name)
        
        if is_admin(user_id):
            # Меню для администратора
            message = (
                "👑 <b>Панель администратора</b>\n\n"
                "Выберите действие с помощью кнопок ниже:\n\n"
                "📋 <b>Клиенты</b> - список всех клиентов с полной информацией\n"
                "⭐ <b>Отзывы</b> - все отзывы клиентов\n"
                "📊 <b>Статистика</b> - общая статистика\n\n"
                "<i>Все сообщения и заказы доступны через раздел 'Клиенты'</i>\n\n"
                "<i>Или используйте команды: /reply, /order</i>"
            )
            keyboard = get_admin_keyboard()
        else:
            # Меню для клиента
            message = (
                "👋 <b>Добро пожаловать!</b>\n\n"
                "Выберите нужное действие с помощью кнопок:\n\n"
                "📞 <b>Поддержка</b> - связь с администратором\n"
                "⭐ <b>Отзывы</b> - оставить или посмотреть отзывы\n"
                "📦 <b>Мои заказы</b> - история ваших заказов\n\n"
                "💬 <i>Или просто напишите сообщение для связи с администратором</i>"
            )
            keyboard = get_client_keyboard()
        
        send_message(user_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_start_command: {e}")
        send_message(user_id, "❌ Произошла ошибка. Попробуйте позже.")

def handle_support_command(user_id):
    """Команда связи с администратором"""
    try:
        message = (
            "💬 Связь с администратором\n\n"
            "Напишите ваш вопрос или сообщение, и администратор ответит вам в ближайшее время.\n\n"
            "Просто отправьте сообщение, и оно будет передано администратору."
        )
        send_message(user_id, message, get_back_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_support_command: {e}")

def handle_support_button(user_id):
    """Обработка кнопки поддержки"""
    try:
        message = (
            "📞 <b>Поддержка</b>\n\n"
            "Выберите действие:"
        )
        send_message(user_id, message, get_support_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_support_button: {e}")

def handle_write_message_button(user_id):
    """Обработка кнопки написать сообщение"""
    try:
        message = (
            "📝 <b>Написать сообщение</b>\n\n"
            "Просто напишите ваш вопрос или сообщение, и оно будет передано администратору.\n\n"
            "Администратор ответит вам в ближайшее время!"
        )
        send_message(user_id, message, get_back_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_write_message_button: {e}")

def handle_reviews_button(user_id):
    """Обработка кнопки отзывов"""
    try:
        message = (
            "⭐ <b>Отзывы</b>\n\n"
            "Выберите действие:"
        )
        send_message(user_id, message, get_reviews_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_reviews_button: {e}")

def handle_leave_review_button(user_id):
    """Обработка кнопки оставить отзыв"""
    try:
        message = (
            "⭐ <b>Оставить отзыв</b>\n\n"
            "Выберите оценку от 1 до 5 звезд:"
        )
        send_message(user_id, message, get_rating_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_leave_review_button: {e}")

def handle_rating_selection(user_id, rating_text):
    """Обработка выбора рейтинга"""
    try:
        # Извлекаем количество звезд из текста
        rating = rating_text.count('⭐')
        
        message = (
            f"⭐ <b>Вы выбрали {rating} звезд</b>\n\n"
            f"Теперь напишите ваш отзыв (или отправьте любое сообщение для подтверждения только оценки):"
        )
        send_message(user_id, message, get_back_keyboard())
        
        # Сохраняем выбранный рейтинг для пользователя (можно в памяти или базе)
        # Здесь мы будем ждать следующее сообщение от пользователя
        
    except Exception as e:
        logger.error(f"Ошибка в handle_rating_selection: {e}")

def handle_reviews_command(user_id):
    """Команда отзывов"""
    try:
        if is_admin(user_id):
            show_admin_reviews(user_id)
        else:
            show_customer_reviews(user_id)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_reviews_command: {e}")

def show_customer_reviews(user_id):
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
            message = (
                "👀 Отзывы\n\n"
                "Пока нет отзывов. Станьте первым!\n\n"
                "Для оставления отзыва используйте /rate <оценка> <отзыв>\n"
                "Например: /rate 5 Отличный сервис!"
            )
        else:
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
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в show_customer_reviews: {e}")

def handle_rate_command(user_id, username, first_name, last_name, text):
    """Команда для оставления отзыва"""
    try:
        # Парсим команду /rate <оценка> <отзыв>
        args = text.split()[1:]  # Убираем /rate
        
        if len(args) < 1:
            send_message(user_id, (
                "❌ Неверный формат команды.\n"
                "Используйте: /rate <оценка> <отзыв>\n"
                "Например: /rate 5 Отличный сервис!"
            ))
            return
        
        try:
            rating = int(args[0])
            if rating < 1 or rating > 5:
                send_message(user_id, "❌ Оценка должна быть от 1 до 5.")
                return
            
            review_text = " ".join(args[1:]) if len(args) > 1 else "Только оценка"
            
            # Сохраняем отзыв
            customer_id = get_or_create_customer(user_id, username, first_name, last_name)
            
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
            send_message(user_id, (
                f"{message}\n\n"
                f"⭐ Оценка: {stars}\n"
                f"💬 Отзыв: {review_text}\n\n"
                f"Спасибо за ваш отзыв!"
            ))
            
        except ValueError:
            send_message(user_id, "❌ Оценка должна быть числом от 1 до 5.")
            
    except Exception as e:
        logger.error(f"Ошибка в handle_rate_command: {e}")

def handle_myorders_command(user_id):
    """Команда моих заказов"""
    try:
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
            message = (
                "📦 Мои заказы\n\n"
                "У вас пока нет заказов.\n\n"
                "Для создания заказа обратитесь к администратору."
            )
        else:
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
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_myorders_command: {e}")

def handle_customers_command(user_id):
    """Команда списка клиентов (только для админов)"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
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
            send_message(user_id, "📋 Список клиентов\n\nКлиентов пока нет.")
            return
        
        message = "📋 Список клиентов\n\n"
        
        for customer in customers:
            user_id_val, username, first_name, last_name, last_activity, messages_count = customer
            
            name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
            message += (
                f"👤 {name}\n"
                f"🆔 ID: {user_id_val}\n"
                f"💬 Сообщений: {messages_count}\n"
                f"⏰ Активность: {last_activity[:16]}\n\n"
            )
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customers_command: {e}")

def handle_messages_command(user_id):
    """Команда сообщений поддержки (только для админов)"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
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
            send_message(user_id, "💬 Сообщения поддержки\n\nСообщений пока нет.")
            return
        
        message = "💬 Последние сообщения поддержки\n\n"
        
        for msg in messages:
            msg_id, user_id_val, first_name, username, msg_text, is_from_admin, created_at = msg
            
            sender = "👑 Админ" if is_from_admin else f"👤 {first_name or username or 'Клиент'}"
            
            message += (
                f"{sender}\n"
                f"🆔 ID: {user_id_val}\n"
                f"💬 {msg_text[:100]}{'...' if len(msg_text) > 100 else ''}\n"
                f"⏰ {created_at[:16]}\n\n"
            )
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_messages_command: {e}")

def show_admin_reviews(user_id):
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
            send_message(user_id, "⭐ Отзывы\n\nОтзывов пока нет.")
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
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в show_admin_reviews: {e}")

def handle_orders_command(user_id):
    """Команда заказов (только для админов)"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
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
            send_message(user_id, "📦 Заказы\n\nЗаказов пока нет.")
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
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_orders_command: {e}")

def handle_stats_command(user_id):
    """Команда статистики (только для админов)"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
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
        
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_stats_command: {e}")

def handle_reply_command(user_id, text):
    """Команда для ответа клиенту"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        args = text.split()[1:]  # Убираем /reply
        if len(args) < 2:
            send_message(user_id, (
                "❌ Неверный формат команды.\n"
                "Используйте: /reply <user_id> <сообщение>"
            ))
            return
        
        target_user_id = int(args[0])
        message_text = " ".join(args[1:])
        
        # Отправляем сообщение клиенту
        if send_message(target_user_id, f"💬 Ответ от администратора\n\n{message_text}"):
            # Сохраняем в базу данных
            conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM customers WHERE user_id = ?', (target_user_id,))
            result = cursor.fetchone()
            
            if result:
                customer_id = result[0]
                cursor.execute('''
                    INSERT INTO support_messages (customer_id, message, is_from_admin)
                    VALUES (?, ?, TRUE)
                ''', (customer_id, message_text))
            
            conn.commit()
            conn.close()
            
            send_message(user_id, f"✅ Ответ отправлен пользователю {target_user_id}")
        else:
            send_message(user_id, f"❌ Ошибка отправки сообщения пользователю {target_user_id}")
        
    except ValueError:
        send_message(user_id, "❌ Неверный ID пользователя.")
    except Exception as e:
        logger.error(f"Ошибка в handle_reply_command: {e}")
        send_message(user_id, f"❌ Ошибка отправки: {e}")

def handle_order_command(user_id, text):
    """Команда для создания заказа"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        args = text.split()[1:]  # Убираем /order
        if len(args) < 2:
            send_message(user_id, (
                "❌ Неверный формат команды.\n"
                "Используйте: /order <user_id> <описание_заказа>"
            ))
            return
        
        target_user_id = int(args[0])
        order_description = " ".join(args[1:])
        
        # Генерируем номер заказа
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Сохраняем заказ в базу данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM customers WHERE user_id = ?', (target_user_id,))
        result = cursor.fetchone()
        
        if not result:
            send_message(user_id, "❌ Пользователь не найден в базе данных.")
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
        send_message(target_user_id, (
            f"📦 Новый заказ создан!\n\n"
            f"🆔 Номер заказа: #{order_number}\n"
            f"📝 Описание: {order_description}\n"
            f"📊 Статус: В обработке\n\n"
            f"Следите за статусом командой /myorders"
        ))
        
        send_message(user_id, f"✅ Заказ #{order_number} создан для пользователя {target_user_id}")
        
    except ValueError:
        send_message(user_id, "❌ Неверный ID пользователя.")
    except Exception as e:
        logger.error(f"Ошибка в handle_order_command: {e}")
        send_message(user_id, f"❌ Ошибка создания заказа: {e}")

def forward_to_admin(sender_user_id, sender_username, sender_first_name, sender_last_name, message_text):
    """Пересылка сообщения клиента администратору"""
    try:
        # Сохраняем сообщение в базу данных
        customer_id = get_or_create_customer(sender_user_id, sender_username, sender_first_name, sender_last_name)
        
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
            f"👤 Клиент: {sender_first_name or 'Неизвестно'}"
            f"{' (@' + sender_username + ')' if sender_username else ''}\n"
            f"🆔 ID: {sender_user_id}\n\n"
            f"💬 Сообщение:\n{message_text}\n\n"
            f"Для ответа используйте команду /reply {sender_user_id} <ваш ответ>"
        )
        
        for admin_id in ADMIN_IDS:
            send_message(admin_id, admin_message)
        
        send_message(sender_user_id, (
            "✅ Ваше сообщение отправлено администратору\n\n"
            "Мы получили ваше сообщение и ответим в ближайшее время!"
        ))
        
    except Exception as e:
        logger.error(f"Ошибка в forward_to_admin: {e}")

def process_update(update):
    """Обработка одного обновления"""
    try:
        if 'message' in update:
            message = update['message']
            user_id = message['from']['id']
            username = message['from'].get('username')
            first_name = message['from'].get('first_name')
            last_name = message['from'].get('last_name')
            
            if 'text' in message:
                text = message['text']
                
                # Обработка кнопок
                if text == '🏠 Главное меню' or text == '🔙 Назад':
                    handle_start_command(user_id, username, first_name, last_name)
                elif text == '📞 Поддержка':
                    handle_support_button(user_id)
                elif text == '📝 Написать сообщение':
                    handle_write_message_button(user_id)
                elif text == '⭐ Отзывы':
                    handle_reviews_button(user_id)
                elif text == '👀 Посмотреть отзывы':
                    show_customer_reviews(user_id)
                elif text == '⭐ Оставить отзыв':
                    handle_leave_review_button(user_id)
                elif text in ['⭐ 1', '⭐⭐ 2', '⭐⭐⭐ 3', '⭐⭐⭐⭐ 4', '⭐⭐⭐⭐⭐ 5']:
                    handle_rating_selection(user_id, text)
                elif text == '📦 Мои заказы':
                    handle_myorders_command(user_id)
                elif text == '📋 Клиенты':
                    handle_customers_list_button(user_id)
                elif text == '📊 Статистика':
                    handle_stats_command(user_id)
                elif text == '💬 Чат с клиентом':
                    handle_customer_chat_button(user_id)
                elif text == '📦 Заказы клиента':
                    handle_customer_orders_button(user_id)
                elif text == '🔙 Назад к списку клиентов':
                    handle_customers_list_button(user_id)
                elif text == '💬 Отправить сообщение':
                    handle_send_message_to_customer_button(user_id)
                elif text == '⭐ Отзывы клиента':
                    handle_customer_reviews_button(user_id)
                elif text == '🔙 Назад к клиенту':
                    handle_back_to_customer_button(user_id)
                # Обработка команд
                elif text.startswith('/start'):
                    handle_start_command(user_id, username, first_name, last_name)
                elif text.startswith('/support'):
                    handle_support_command(user_id)
                elif text.startswith('/reviews'):
                    handle_reviews_command(user_id)
                elif text.startswith('/rate'):
                    handle_rate_command(user_id, username, first_name, last_name, text)
                elif text.startswith('/myorders'):
                    handle_myorders_command(user_id)
                elif text.startswith('/customers'):
                    handle_customers_command(user_id)
                elif text.startswith('/messages'):
                    handle_messages_command(user_id)
                elif text.startswith('/orders'):
                    handle_orders_command(user_id)
                elif text.startswith('/stats'):
                    handle_stats_command(user_id)
                elif text.startswith('/reply'):
                    handle_reply_command(user_id, text)
                elif text.startswith('/order'):
                    handle_order_command(user_id, text)
                elif text.startswith('/customer_reviews'):
                    handle_customer_reviews_command(user_id, text)
                else:
                    # Обычное сообщение - пересылаем админу
                    forward_to_admin(user_id, username, first_name, last_name, text)
        
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            user_id = callback_query['from']['id']
            callback_data = callback_query['data']
            callback_query_id = callback_query['id']
            
            print(f"🔍 DEBUG: Получен callback_query: user_id={user_id}, data='{callback_data}', query_id={callback_query_id}")
            
            # Обрабатываем callback query
            if callback_data.startswith('customer_'):
                customer_user_id = int(callback_data.split('_')[1])
                print(f"🔍 DEBUG: Обрабатываем клиента {customer_user_id} для админа {user_id}")
                answer_callback_query(callback_query_id, "Загрузка информации о клиенте...")
                show_customer_detail(user_id, customer_user_id)
            elif callback_data == 'back_to_admin':
                answer_callback_query(callback_query_id, "Возврат в главное меню")
                handle_start_command(user_id, callback_query['from'].get('username'), 
                                   callback_query['from'].get('first_name'), 
                                   callback_query['from'].get('last_name'))
            elif callback_data == 'customers_list':
                answer_callback_query(callback_query_id, "Загрузка списка клиентов...")
                handle_customers_list_button(user_id)
            elif callback_data.startswith('chat_'):
                customer_user_id = int(callback_data.split('_')[1])
                answer_callback_query(callback_query_id, "Открытие чата...")
                handle_customer_chat_callback(user_id, customer_user_id)
            elif callback_data.startswith('orders_'):
                customer_user_id = int(callback_data.split('_')[1])
                answer_callback_query(callback_query_id, "Загрузка заказов...")
                handle_customer_orders_callback(user_id, customer_user_id)
            elif callback_data.startswith('reviews_'):
                customer_user_id = int(callback_data.split('_')[1])
                answer_callback_query(callback_query_id, "Загрузка отзывов...")
                handle_customer_reviews_callback(user_id, customer_user_id)
            else:
                answer_callback_query(callback_query_id, "Неизвестная команда")
            
            return
        
    except Exception as e:
        logger.error(f"Ошибка в process_update: {e}")

def handle_customers_list_button(user_id):
    """Показать список клиентов с inline кнопками"""
    try:
        print(f"🔍 DEBUG: handle_customers_list_button вызвана для пользователя {user_id}")
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.user_id, c.username, c.first_name, c.last_name, c.last_activity,
                   COUNT(DISTINCT sm.id) as messages_count,
                   COUNT(DISTINCT o.id) as orders_count
            FROM customers c
            LEFT JOIN support_messages sm ON c.id = sm.customer_id
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id
            ORDER BY c.last_activity DESC
            LIMIT 10
        ''')
        
        customers = cursor.fetchall()
        conn.close()
        
        if not customers:
            send_message(user_id, "📋 <b>Список клиентов</b>\n\nКлиентов пока нет.", get_back_keyboard())
            return
        
        # Создаем inline клавиатуру с клиентами
        inline_keyboard = []
        message = "📋 <b>Выберите клиента:</b>"
        
        for i, customer in enumerate(customers):
            customer_id, user_id_val, username, first_name, last_name, last_activity, messages_count, orders_count = customer
            
            name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
            
            # Добавляем inline кнопку для каждого клиента с краткой информацией
            button_text = f"👤 {name}"
            if orders_count > 0:
                button_text += f" (#{orders_count})"
            if messages_count > 0:
                button_text += f" 💬{messages_count}"
            
            callback_data = f"customer_{user_id_val}"
            print(f"🔍 DEBUG: Создаем кнопку для клиента {name} с callback_data: {callback_data}")
            inline_keyboard.append([{
                "text": button_text,
                "callback_data": callback_data
            }])
        
        # Добавляем кнопку "Назад"
        inline_keyboard.append([{
            "text": "🔙 Назад",
            "callback_data": "back_to_admin"
        }])
        
        reply_markup = create_inline_keyboard(inline_keyboard)
        print(f"🔍 DEBUG: Отправляем сообщение с клавиатурой: {len(inline_keyboard)} кнопок")
        send_message(user_id, message, reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customers_list_button: {e}")


def show_customer_detail(admin_user_id, customer_user_id):
    """Показать детальную информацию о клиенте"""
    try:
        print(f"🔍 DEBUG: show_customer_detail вызвана для админа {admin_user_id}, клиента {customer_user_id}")
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем информацию о клиенте
        cursor.execute('''
            SELECT c.id, c.username, c.first_name, c.last_name, c.created_at, c.last_activity,
                   COUNT(DISTINCT sm.id) as messages_count,
                   COUNT(DISTINCT o.id) as orders_count,
                   COUNT(DISTINCT r.id) as reviews_count
            FROM customers c
            LEFT JOIN support_messages sm ON c.id = sm.customer_id
            LEFT JOIN orders o ON c.id = o.customer_id
            LEFT JOIN reviews r ON c.id = r.customer_id
            WHERE c.user_id = ?
            GROUP BY c.id
        ''', (customer_user_id,))
        
        customer = cursor.fetchone()
        
        if not customer:
            send_message(admin_user_id, "❌ Клиент не найден.", get_back_keyboard())
            return
        
        customer_id, username, first_name, last_name, created_at, last_activity, messages_count, orders_count, reviews_count = customer
        
        name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
        username_text = f"@{username}" if username else "Не указан"
        
        # Получаем последнее сообщение
        cursor.execute('''
            SELECT message, created_at, is_from_admin
            FROM support_messages sm
            WHERE sm.customer_id = ?
            ORDER BY sm.created_at DESC
            LIMIT 1
        ''', (customer_id,))
        
        last_message = cursor.fetchone()
        last_message_text = ""
        if last_message:
            message_text, msg_date, is_from_admin = last_message
            sender = "Админ" if is_from_admin else "Клиент"
            last_message_text = f"\n💬 <b>Последнее сообщение:</b>\n{sender}: {message_text[:100]}{'...' if len(message_text) > 100 else ''}\n📅 {msg_date[:16]}"
        
        # Получаем последний заказ
        cursor.execute('''
            SELECT order_number, status, created_at
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (customer_id,))
        
        last_order = cursor.fetchone()
        last_order_text = ""
        if last_order:
            order_number, status, order_date = last_order
            last_order_text = f"\n📦 <b>Последний заказ:</b>\n#{order_number} - {status}\n📅 {order_date[:16]}"
        
        conn.close()
        
        message = (
            f"👤 <b>Информация о клиенте</b>\n\n"
            f"<b>Имя:</b> {name}\n"
            f"<b>Username:</b> {username_text}\n"
            f"<b>ID:</b> {customer_user_id}\n"
            f"<b>Регистрация:</b> {created_at[:16]}\n"
            f"<b>Активность:</b> {last_activity[:16]}\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"💬 Сообщений: {messages_count}\n"
            f"📦 Заказов: {orders_count}\n"
            f"⭐ Отзывов: {reviews_count}"
            f"{last_message_text}"
            f"{last_order_text}"
        )
        
        # Создаем inline клавиатуру для детального просмотра клиента
        inline_keyboard = [
            [{"text": "💬 Чат с клиентом", "callback_data": f"chat_{customer_user_id}"}],
            [{"text": "📦 Заказы клиента", "callback_data": f"orders_{customer_user_id}"}],
            [{"text": "⭐ Отзывы клиента", "callback_data": f"reviews_{customer_user_id}"}],
            [{"text": "🔙 Назад к списку", "callback_data": "customers_list"}]
        ]
        
        reply_markup = create_inline_keyboard(inline_keyboard)
        send_message(admin_user_id, message, reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_customer_detail: {e}")

def handle_customer_chat_button(user_id):
    """Показать историю чата с клиентом"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        message = (
            "💬 <b>История чата с клиентом</b>\n\n"
            "Используйте команду:\n"
            "<code>/reply &lt;ID_клиента&gt; &lt;ваше сообщение&gt;</code>\n\n"
            "Для просмотра всех сообщений используйте кнопку '💬 Все сообщения'"
        )
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_chat_button: {e}")

def handle_customer_orders_button(user_id):
    """Показать заказы клиента"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        message = (
            "📦 <b>Заказы клиента</b>\n\n"
            "Для просмотра всех заказов используйте кнопку '📦 Все заказы'\n\n"
            "Для создания заказа используйте команду:\n"
            "<code>/order &lt;ID_клиента&gt; &lt;описание_заказа&gt;</code>"
        )
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_orders_button: {e}")

def handle_send_message_to_customer_button(user_id):
    """Показать форму для отправки сообщения клиенту"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        message = (
            "💬 <b>Отправить сообщение клиенту</b>\n\n"
            "Используйте команду:\n"
            "<code>/reply &lt;ID_клиента&gt; &lt;ваше сообщение&gt;</code>\n\n"
            "Например:\n"
            "<code>/reply 123456789 Привет! Как дела?</code>"
        )
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_send_message_to_customer_button: {e}")

def handle_back_to_customer_button(user_id):
    """Вернуться к детальной информации о клиенте"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Возвращаемся к списку клиентов
        handle_customers_list_button(user_id)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_back_to_customer_button: {e}")

def handle_customer_reviews_button(user_id):
    """Показать отзывы конкретного клиента"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        message = (
            "⭐ <b>Отзывы клиента</b>\n\n"
            "Для просмотра отзывов конкретного клиента используйте команду:\n"
            "<code>/customer_reviews &lt;ID_клиента&gt;</code>\n\n"
            "Например:\n"
            "<code>/customer_reviews 123456789</code>\n\n"
            "Для просмотра всех отзывов используйте кнопку '⭐ Отзывы' в главном меню."
        )
        send_message(user_id, message, get_back_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_reviews_button: {e}")

def handle_customer_reviews_command(user_id, text):
    """Команда для просмотра отзывов конкретного клиента"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        args = text.split()[1:]  # Убираем /customer_reviews
        if len(args) < 1:
            send_message(user_id, (
                "❌ Неверный формат команды.\n"
                "Используйте: /customer_reviews <ID_клиента>"
            ))
            return
        
        customer_user_id = int(args[0])
        handle_customer_reviews_callback(user_id, customer_user_id)
        
    except ValueError:
        send_message(user_id, "❌ Неверный ID клиента.")
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_reviews_command: {e}")
        send_message(user_id, f"❌ Ошибка получения отзывов: {e}")

def handle_customer_chat_callback(user_id, customer_user_id):
    """Callback для чата с клиентом"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Находим клиента в базе данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, first_name, last_name, username FROM customers WHERE user_id = ?', (customer_user_id,))
        result = cursor.fetchone()
        
        if not result:
            send_message(user_id, "❌ Клиент не найден в базе данных.")
            conn.close()
            return
        
        customer_id, first_name, last_name, username = result
        customer_name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
        
        # Получаем последние сообщения
        cursor.execute('''
            SELECT message, created_at, is_from_admin
            FROM support_messages
            WHERE customer_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (customer_id,))
        
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            message = f"💬 <b>Чат с клиентом {customer_name}</b>\n\nСообщений пока нет."
        else:
            message = f"💬 <b>Чат с клиентом {customer_name}</b>\n\n"
            for msg in reversed(messages):
                message_text, created_at, is_from_admin = msg
                sender = "👑 Админ" if is_from_admin else "👤 Клиент"
                message += f"{sender}: {message_text}\n📅 {created_at[:16]}\n\n"
        
        message += "\nДля отправки сообщения используйте:\n<code>/reply " + str(customer_user_id) + " ваше сообщение</code>"
        
        # Кнопка назад к клиенту
        inline_keyboard = [[{"text": "🔙 Назад к клиенту", "callback_data": f"customer_{customer_user_id}"}]]
        reply_markup = create_inline_keyboard(inline_keyboard)
        send_message(user_id, message, reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_chat_callback: {e}")

def handle_customer_orders_callback(user_id, customer_user_id):
    """Callback для заказов клиента"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Находим клиента в базе данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, first_name, last_name, username FROM customers WHERE user_id = ?', (customer_user_id,))
        result = cursor.fetchone()
        
        if not result:
            send_message(user_id, "❌ Клиент не найден в базе данных.")
            conn.close()
            return
        
        customer_id, first_name, last_name, username = result
        customer_name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
        
        # Получаем заказы клиента
        cursor.execute('''
            SELECT order_number, order_data, status, created_at
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
        ''', (customer_id,))
        
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            message = f"📦 <b>Заказы клиента {customer_name}</b>\n\nЗаказов пока нет."
        else:
            message = f"📦 <b>Заказы клиента {customer_name}</b>\n\n"
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
                    f"{status_emoji} <b>#{order_number}</b>\n"
                    f"📝 {order_data or 'Без описания'}\n"
                    f"📊 Статус: {status}\n"
                    f"📅 {created_at[:16]}\n\n"
                )
        
        message += "\nДля создания заказа используйте:\n<code>/order " + str(customer_user_id) + " описание заказа</code>"
        
        # Кнопка назад к клиенту
        inline_keyboard = [[{"text": "🔙 Назад к клиенту", "callback_data": f"customer_{customer_user_id}"}]]
        reply_markup = create_inline_keyboard(inline_keyboard)
        send_message(user_id, message, reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_orders_callback: {e}")

def handle_customer_reviews_callback(user_id, customer_user_id):
    """Callback для отзывов клиента"""
    try:
        if not is_admin(user_id):
            send_message(user_id, "❌ У вас нет прав для выполнения этой команды.")
            return
        
        # Находим клиента в базе данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, first_name, last_name, username FROM customers WHERE user_id = ?', (customer_user_id,))
        result = cursor.fetchone()
        
        if not result:
            send_message(user_id, "❌ Клиент не найден в базе данных.")
            conn.close()
            return
        
        customer_id, first_name, last_name, username = result
        customer_name = f"{first_name or ''} {last_name or ''}".strip() or username or "Неизвестно"
        
        # Получаем отзывы клиента
        cursor.execute('''
            SELECT rating, review_text, created_at
            FROM reviews
            WHERE customer_id = ?
            ORDER BY created_at DESC
        ''', (customer_id,))
        
        reviews = cursor.fetchall()
        conn.close()
        
        if not reviews:
            message = f"⭐ <b>Отзывы клиента {customer_name}</b>\n\nУ клиента пока нет отзывов."
        else:
            message = f"⭐ <b>Отзывы клиента {customer_name}</b>\n\n"
            for review in reviews:
                rating, review_text, created_at = review
                stars = "⭐" * rating
                
                message += (
                    f"{stars} <b>{rating}/5</b>\n"
                    f"💬 {review_text or 'Без текста'}\n"
                    f"📅 {created_at[:16]}\n\n"
                )
        
        # Кнопка назад к клиенту
        inline_keyboard = [[{"text": "🔙 Назад к клиенту", "callback_data": f"customer_{customer_user_id}"}]]
        reply_markup = create_inline_keyboard(inline_keyboard)
        send_message(user_id, message, reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_customer_reviews_callback: {e}")


def main():
    """Главная функция"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        print("💡 Установите переменную окружения BOT_TOKEN")
        return
    
    print("🤖 ЗАПУСК БОТА БЕЗ TELEGRAM БИБЛИОТЕКИ")
    print("=" * 50)
    
    # Инициализация базы данных
    init_support_database()
    
    print("✅ Бот поддержки запущен и готов к работе!")
    print("📞 Клиенты могут писать сообщения администраторам")
    print("⭐ Система отзывов активна")
    print("📊 Статистика и заказы доступны админам")
    print("=" * 50)
    
    # Основной цикл
    last_update_id = None
    
    while True:
        try:
            # Получаем обновления
            updates = get_updates(last_update_id)
            
            if updates and updates.get('ok'):
                for update in updates['result']:
                    process_update(update)
                    last_update_id = update['update_id'] + 1
            else:
                # Если нет обновлений, ждем немного
                import time
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Остановка бота...")
            break
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            import time
            time.sleep(5)  # Ждем перед повтором

if __name__ == "__main__":
    main()

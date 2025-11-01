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
import time
from datetime import datetime

# Устанавливаем requests если не установлен
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("📦 Устанавливаем requests...")
    import subprocess
    subprocess.check_call(['pip', 'install', '--quiet', 'requests'])
    import requests
    REQUESTS_AVAILABLE = True

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

# Глобальная переменная для хранения текущего выбранного клиента
current_customer_user_id = None

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
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица отзывов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            rating INTEGER NOT NULL,
            comment TEXT,
            is_approved INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            order_number TEXT,
            description TEXT,
            total_price REAL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Таблица сообщений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            message TEXT,
            is_from_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_or_create_customer(user_id, username=None, first_name=None, last_name=None):
    """Получить или создать клиента"""
    conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
    cursor = conn.cursor()
    
    # Проверяем, существует ли клиент
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
        SET last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()
    
    return customer_id

def is_admin(user_id):
    """Проверить, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def create_reply_keyboard(keyboard_layout, resize_keyboard=True, one_time_keyboard=False):
    """Создать reply клавиатуру"""
    return {
        'keyboard': keyboard_layout,
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyboard
    }

def create_inline_keyboard(inline_layout):
    """Создать inline клавиатуру"""
    return {'inline_keyboard': inline_layout}

def get_admin_keyboard():
    """Получить главную клавиатуру для администратора"""
    keyboard = [
        ['📋 Клиенты', '📊 Статистика'],
        ['📦 Заказы', '💬 Сообщения'],
        ['⭐ Отзывы', '📊 Статистика']
    ]
    return create_reply_keyboard(keyboard)

def get_customer_keyboard():
    """Получить главную клавиатуру для клиента"""
    keyboard = [
        ['🛍️ Каталог товаров'],
        ['📞 Поддержка'],
        ['⭐ Отзывы', '📦 Мои заказы']
    ]
    return create_reply_keyboard(keyboard)

def get_back_keyboard():
    """Получить клавиатуру с кнопкой Назад"""
    keyboard = [['🔙 Назад']]
    return create_reply_keyboard(keyboard)

def send_message(user_id, text, parse_mode='HTML'):
    """Отправить сообщение пользователю"""
    try:
        url = f'{TELEGRAM_API_URL}/sendMessage'
        data = {
            'chat_id': user_id,
            'text': text,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None

def send_message_with_keyboard(user_id, text, keyboard, parse_mode='HTML'):
    """Отправить сообщение с клавиатурой"""
    try:
        url = f'{TELEGRAM_API_URL}/sendMessage'
        data = {
            'chat_id': user_id,
            'text': text,
            'parse_mode': parse_mode,
            'reply_markup': keyboard
        }
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения с клавиатурой: {e}")
        return None

def get_updates(offset=None):
    """Получить обновления от Telegram"""
    try:
        url = f'{TELEGRAM_API_URL}/getUpdates'
        params = {'timeout': 30}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok') and result.get('result'):
                print(f"🔍 DEBUG: get_updates получил {len(result['result'])} обновлений")
            return result
        return None
    except Exception as e:
        logger.error(f"Ошибка получения обновлений: {e}")
        return None

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
                # Обработка команд
                elif text.startswith('/start'):
                    handle_start_command(user_id, username, first_name, last_name)
                elif text.startswith('/support'):
                    handle_support_button(user_id)
                elif text.startswith('/reviews'):
                    handle_reviews_button(user_id)
                elif text.startswith('/myorders'):
                    handle_myorders_command(user_id)
                elif text.startswith('/customers'):
                    if is_admin(user_id):
                        handle_customers_list_button(user_id)
                    else:
                        send_message(user_id, "❌ У вас нет прав доступа.")
                elif text.startswith('/stats'):
                    if is_admin(user_id):
                        handle_stats_command(user_id)
                    else:
                        send_message(user_id, "❌ У вас нет прав доступа.")
                else:
                    # Обычное сообщение - пересылаем админу
                    forward_to_admin(user_id, username, first_name, last_name, text)
            
            elif 'web_app_data' in message:
                # Обработка данных из WebApp
                web_app_data = message['web_app_data']['data']
                handle_webapp_order(user_id, web_app_data)
        
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            user_id = callback_query['from']['id']
            callback_data = callback_query['data']
            callback_query_id = callback_query['id']
            
            print(f"🔍 DEBUG: Получен callback_query: user_id={user_id}, data='{callback_data}', query_id={callback_query_id}")
            
            # Отвечаем на callback query
            answer_callback_query(callback_query_id, "✅ Обработано")
                
    except Exception as e:
        logger.error(f"Ошибка обработки обновления: {e}")
        print(f"❌ Ошибка обработки обновления: {e}")

def handle_start_command(user_id, username, first_name, last_name):
    """Обработчик команды /start"""
    try:
        # Регистрируем или обновляем клиента
        get_or_create_customer(user_id, username, first_name, last_name)
        
        if is_admin(user_id):
            # Клавиатура для админа
            keyboard = get_admin_keyboard()
            message = (
                "👋 <b>Добро пожаловать, администратор!</b>\n\n"
                "Вы можете управлять:\n"
                "• 👥 Клиентами\n"
                "• 📦 Заказами\n"
                "• 💬 Сообщениями\n"
                "• ⭐ Отзывами\n"
                "• 📊 Статистикой"
            )
        else:
            # Клавиатура для клиента
            keyboard = get_customer_keyboard()
            message = (
                "🛍️ <b>Добро пожаловать в наш магазин!</b>\n\n"
                "Здесь вы можете:\n"
                "• 🛍️ Просматривать каталог товаров\n"
                "• 📞 Связаться с поддержкой\n"
                "• ⭐ Оставить отзыв\n"
                "• 📦 Посмотреть свои заказы\n\n"
                "Для начала работы нажмите 'Каталог товаров'"
            )
        
        send_message_with_keyboard(user_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_start_command: {e}")
        send_message(user_id, "❌ Произошла ошибка. Попробуйте позже.")

def handle_webapp_order(user_id, web_app_data):
    """Обработка заказа из WebApp"""
    try:
        import json
        
        # Парсим данные из WebApp
        order_data = json.loads(web_app_data)
        
        logger.info(f"📦 Получены данные WebApp от пользователя {user_id}: {order_data}")
        
        # Проверяем разные варианты структуры данных
        if order_data.get('action') == 'order':
            # Новый формат: {action: 'order', data: {...}}
            order = order_data.get('data', order_data)
        elif order_data.get('type') == 'order':
            # Альтернативный формат: {type: 'order', order: {...}}
            order = order_data.get('order', order_data)
        elif 'items' in order_data or 'total' in order_data:
            # Прямой формат заказа
            order = order_data
        else:
            logger.error(f"❌ Неизвестный формат данных WebApp: {order_data}")
            return
        
        # Получаем customer_id
        customer_id = get_or_create_customer(user_id, None, None, None)
        
        # Создаем простой номер заказа: 1, 2, 3...
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0]
        order_number = str(orders_count + 1)
        conn.close()
        
        # Формируем описание заказа
        items = order.get('items', [])
        order_description = "🛒 Заказ из WebApp:\n\n"
        
        # Если есть 'total' в данных, используем его
        total_price = order.get('total', 0)
        
        # Если total не указан, вычисляем по товарам
        if total_price == 0:
            # Загружаем товары из JSON
            try:
                products_json_path = os.path.join(os.path.dirname(__file__), 'webapp', 'products.json')
                with open(products_json_path, 'r', encoding='utf-8') as f:
                    products_data = json.load(f)
                    products = {p['id']: p for p in products_data}
            except Exception as e:
                logger.error(f"Ошибка загрузки products.json: {e}")
                products = {}
            
            for i, item in enumerate(items, 1):
                product_id = item.get('productId')
                quantity = item.get('quantity', 1)
                size = item.get('size', '')
                
                # Получаем информацию о товаре
                product = products.get(product_id, {})
                product_name = product.get('title', f'Товар #{product_id}')
                price = product.get('price', 0)
                
                item_total = price * quantity
                total_price += item_total
                
                size_text = f" (размер: {size})" if size else ""
                order_description += f"{i}. {product_name}{size_text}\n"
                order_description += f"   Количество: {quantity}\n"
                order_description += f"   Цена: {price}₽ × {quantity} = {item_total}₽\n\n"
        else:
            # Если total уже указан, просто перечисляем товары
            for i, item in enumerate(items, 1):
                product_id = item.get('productId')
                quantity = item.get('quantity', 1)
                size = item.get('size', '')
                
                size_text = f" (размер: {size})" if size else ""
                order_description += f"{i}. Товар #{product_id}{size_text} × {quantity}\n"
        
        # Сохраняем заказ в базу данных
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Вставляем заказ
        cursor.execute('''
            INSERT INTO orders (customer_id, order_number, description, total_price, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, order_number, order_description, total_price, 'new'))
        
        conn.commit()
        conn.close()
        
        # Уведомляем всех админов о новом заказе
        for admin_id in ADMIN_IDS:
            try:
                # СООБЩЕНИЕ 1: Информация о заказе
                admin_message = (
                    f"🔔 <b>НОВЫЙ ЗАКАЗ {order_number}</b>\n\n"
                    f"💰 <b>{total_price:,} ₽</b>\n"
                    f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"👤 <b>КЛИЕНТ:</b>\n"
                    f"   Имя: Пользователь\n"
                    f"   ID: <code>{user_id}</code>\n\n"
                    f"{order_description}\n\n"
                    f"<b>ЧТО ДЕЛАТЬ:</b>\n\n"
                    f"1️⃣ Связаться с клиентом\n"
                    f"2️⃣ Уточнить адрес доставки\n"
                    f"3️⃣ Получить подтверждение оплаты\n\n"
                    f"⏱ <b>Обработать в течение 15 минут</b>"
                )
                
                send_message(admin_id, admin_message)
                time.sleep(0.5)  # Небольшая задержка между сообщениями
                
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
        
        # Отправляем подтверждение клиенту
        confirmation_message = (
            f"✅ <b>Заказ #{order_number} принят!</b>\n\n"
            f"💰 Сумма: <b>{total_price:,} ₽</b>\n"
            f"📦 Товаров: {len(items)}\n\n"
            f"⏱ Менеджер свяжется с вами в течение 15 минут\n"
            f"📞 Для срочных вопросов: /support"
        )
        
        send_message(user_id, confirmation_message)
        
    except Exception as e:
        logger.error(f"Ошибка обработки WebApp заказа: {e}")
        send_message(user_id, "❌ Ошибка обработки заказа. Попробуйте еще раз.")

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ОТЗЫВАМИ =====

def handle_reviews_button(user_id):
    """Обработка кнопки отзывов"""
    keyboard = create_reply_keyboard([
        ['👀 Посмотреть отзывы', '⭐ Оставить отзыв'],
        ['🔙 Назад']
    ])
    
    message = (
        "⭐ <b>Система отзывов</b>\n\n"
        "Здесь вы можете:\n"
        "• Посмотреть отзывы других клиентов\n"
        "• Оставить свой отзыв о покупке\n"
        "• Оценить качество обслуживания\n\n"
        "Ваше мнение очень важно для нас!"
    )
    
    send_message_with_keyboard(user_id, message, keyboard)

def show_customer_reviews(user_id):
    """Показать отзывы клиентов"""
    try:
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем последние 5 отзывов
        cursor.execute('''
            SELECT r.rating, r.comment, r.created_at, c.first_name, c.last_name
            FROM reviews r
            JOIN customers c ON r.customer_id = c.id
            WHERE r.is_approved = 1
            ORDER BY r.created_at DESC
            LIMIT 5
        ''')
        
        reviews = cursor.fetchall()
        conn.close()
        
        if not reviews:
            message = "📝 Пока нет отзывов. Станьте первым, кто оставит отзыв!"
        else:
            message = "⭐ <b>Отзывы наших клиентов:</b>\n\n"
            
            for rating, comment, created_at, first_name, last_name in reviews:
                stars = "⭐" * rating
                name = f"{first_name} {last_name}".strip() or "Аноним"
                date = created_at.split()[0] if created_at else "Недавно"
                
                message += f"{stars} <b>{name}</b> ({date})\n"
                if comment:
                    message += f"💬 {comment}\n"
                message += "\n"
        
        keyboard = create_reply_keyboard([
            ['⭐ Оставить отзыв'],
            ['🔙 Назад']
        ])
        
        send_message_with_keyboard(user_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения отзывов: {e}")
        send_message(user_id, "❌ Ошибка загрузки отзывов. Попробуйте позже.")

def handle_leave_review_button(user_id):
    """Обработка кнопки оставить отзыв"""
    keyboard = create_reply_keyboard([
        ['⭐ 1', '⭐⭐ 2', '⭐⭐⭐ 3', '⭐⭐⭐⭐ 4', '⭐⭐⭐⭐⭐ 5'],
        ['🔙 Назад']
    ])
    
    message = (
        "⭐ <b>Оставьте отзыв</b>\n\n"
        "Пожалуйста, оцените нашу работу от 1 до 5 звезд.\n"
        "После оценки вы сможете написать комментарий."
    )
    
    send_message_with_keyboard(user_id, message, keyboard)

def handle_rating_selection(user_id, rating_text):
    """Обработка выбора рейтинга"""
    rating = len(rating_text.split())
    
    # Сохраняем рейтинг во временное хранилище
    global temp_ratings
    if 'temp_ratings' not in globals():
        temp_ratings = {}
    temp_ratings[user_id] = rating
    
    keyboard = create_reply_keyboard([
        ['💬 Написать комментарий', '✅ Отправить без комментария'],
        ['🔙 Назад']
    ])
    
    message = (
        f"⭐ <b>Спасибо за оценку: {rating_text}</b>\n\n"
        "Хотите добавить комментарий к отзыву?\n"
        "Или можете отправить отзыв только с оценкой."
    )
    
    send_message_with_keyboard(user_id, message, keyboard)

def save_review(user_id, rating, comment=None):
    """Сохранить отзыв в базу данных"""
    try:
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем customer_id
        customer_id = get_or_create_customer(user_id, None, None, None)
        
        # Сохраняем отзыв
        cursor.execute('''
            INSERT INTO reviews (customer_id, rating, comment, is_approved, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, rating, comment or '', 1, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка сохранения отзыва: {e}")
        return False

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАКАЗАМИ =====

def handle_myorders_command(user_id):
    """Показать заказы клиента"""
    try:
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем customer_id
        customer_id = get_or_create_customer(user_id, None, None, None)
        
        # Получаем заказы клиента
        cursor.execute('''
            SELECT order_number, description, total_price, status, created_at
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (customer_id,))
        
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            message = "📦 <b>У вас пока нет заказов</b>\n\nПерейдите в каталог и сделайте свой первый заказ!"
        else:
            message = "📦 <b>Ваши заказы:</b>\n\n"
            
            for order_number, description, total_price, status, created_at in orders:
                status_emoji = {
                    'new': '🆕',
                    'processing': '⏳',
                    'shipped': '🚚',
                    'delivered': '✅',
                    'cancelled': '❌'
                }.get(status, '❓')
                
                date = created_at.split()[0] if created_at else "Недавно"
                message += f"{status_emoji} <b>Заказ #{order_number}</b>\n"
                message += f"💰 {total_price:,.0f} ₽\n"
                message += f"📅 {date}\n"
                message += f"📋 Статус: {status}\n\n"
        
        keyboard = create_reply_keyboard([
            ['🛍️ Каталог товаров'],
            ['🔙 Назад']
        ])
        
        send_message_with_keyboard(user_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения заказов: {e}")
        send_message(user_id, "❌ Ошибка загрузки заказов. Попробуйте позже.")

# ===== ФУНКЦИИ ДЛЯ АДМИНОВ =====

def handle_customers_list_button(user_id):
    """Показать список клиентов для админа"""
    try:
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Получаем список клиентов
        cursor.execute('''
            SELECT user_id, first_name, last_name, created_at, last_activity
            FROM customers
            WHERE is_admin = 0
            ORDER BY last_activity DESC
            LIMIT 20
        ''')
        
        customers = cursor.fetchall()
        conn.close()
        
        if not customers:
            message = "👥 <b>Клиенты не найдены</b>\n\nПока никто не зарегистрировался."
        else:
            message = f"👥 <b>Список клиентов ({len(customers)}):</b>\n\n"
            
            for user_id_customer, first_name, last_name, created_at, last_activity in customers:
                name = f"{first_name} {last_name}".strip() or "Без имени"
                date = created_at.split()[0] if created_at else "Недавно"
                
                message += f"👤 <b>{name}</b>\n"
                message += f"🆔 ID: <code>{user_id_customer}</code>\n"
                message += f"📅 Регистрация: {date}\n\n"
        
        keyboard = create_reply_keyboard([
            ['📊 Статистика'],
            ['🔙 Назад']
        ])
        
        send_message_with_keyboard(user_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения списка клиентов: {e}")
        send_message(user_id, "❌ Ошибка загрузки клиентов. Попробуйте позже.")

def handle_stats_command(user_id):
    """Показать статистику для админа"""
    try:
        conn = sqlite3.connect(SUPPORT_DATABASE_PATH)
        cursor = conn.cursor()
        
        # Статистика клиентов
        cursor.execute("SELECT COUNT(*) FROM customers WHERE is_admin = 0")
        customers_count = cursor.fetchone()[0]
        
        # Статистика заказов
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_price) FROM orders WHERE status != 'cancelled'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Статистика отзывов
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = 1")
        reviews_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(rating) FROM reviews WHERE is_approved = 1")
        avg_rating = cursor.fetchone()[0] or 0
        
        conn.close()
        
        message = (
            "📊 <b>Статистика магазина</b>\n\n"
            f"👥 Клиентов: <b>{customers_count}</b>\n"
            f"📦 Заказов: <b>{orders_count}</b>\n"
            f"💰 Выручка: <b>{total_revenue:,.0f} ₽</b>\n"
            f"⭐ Отзывов: <b>{reviews_count}</b>\n"
            f"⭐ Средняя оценка: <b>{avg_rating:.1f}/5</b>\n\n"
            f"📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        keyboard = create_reply_keyboard([
            ['👥 Клиенты', '📦 Заказы'],
            ['⭐ Отзывы', '💬 Сообщения'],
            ['🔙 Назад']
        ])
        
        send_message_with_keyboard(user_id, message, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        send_message(user_id, "❌ Ошибка загрузки статистики. Попробуйте позже.")

# ===== НЕДОСТАЮЩИЕ ФУНКЦИИ =====

def handle_support_button(user_id):
    """Обработка кнопки поддержки"""
    message = (
        "📞 <b>Поддержка клиентов</b>\n\n"
        "Если у вас есть вопросы или проблемы, "
        "напишите нам сообщение, и мы ответим в течение 15 минут.\n\n"
        "⏰ Время работы: 9:00 - 21:00 (МСК)\n"
        "📱 Для срочных вопросов: /support"
    )
    send_message(user_id, message)

def forward_to_admin(user_id, username, first_name, last_name, text):
    """Переслать сообщение админу"""
    try:
        # Получаем список админов
        admins = ADMIN_IDS
        
        message = (
            f"📨 <b>Сообщение от клиента</b>\n\n"
            f"👤 Имя: {first_name} {last_name}".strip() or "Без имени"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📝 Сообщение: {text}"
        )
        
        for admin_id in admins:
            try:
                send_message(admin_id, message)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения админу {admin_id}: {e}")
        
        # Отправляем подтверждение клиенту
        send_message(user_id, "✅ Ваше сообщение отправлено администратору. Мы ответим в течение 15 минут.")
        
    except Exception as e:
        logger.error(f"Ошибка пересылки сообщения: {e}")
        send_message(user_id, "❌ Ошибка отправки сообщения. Попробуйте позже.")

def answer_callback_query(callback_query_id, text):
    """Ответить на callback query"""
    try:
        url = f'{TELEGRAM_API_URL}/answerCallbackQuery'
        data = {
            'callback_query_id': callback_query_id,
            'text': text
        }
        requests.post(url, json=data)
    except Exception as e:
        logger.error(f"Ошибка ответа на callback query: {e}")

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
                print(f"🔍 DEBUG: Получено {len(updates['result'])} обновлений")
                for update in updates['result']:
                    print(f"🔍 DEBUG: Обрабатываем обновление ID {update['update_id']}")
                    if 'message' in update:
                        print(f"🔍 DEBUG: Это сообщение от {update['message']['from']['id']}")
                    elif 'callback_query' in update:
                        print(f"🔍 DEBUG: Это callback_query от {update['callback_query']['from']['id']}")
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

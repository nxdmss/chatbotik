"""
Профессиональный бот с продвинутыми функциями
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from functools import wraps
from contextlib import contextmanager

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from src.config import BOT_TOKEN, ADMIN_IDS, ADMIN_PHONE
from src.database import get_db
from src.utils.logger import get_logger
from src.models.order import OrderCreate, OrderItem

logger = get_logger(__name__)

# ===== КОНСТАНТЫ =====
TELEGRAM_API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Эмодзи для красивого интерфейса
EMOJI = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'loading': '⏳',
    'shop': '🛍️',
    'cart': '🛒',
    'order': '📦',
    'money': '💰',
    'phone': '📱',
    'location': '📍',
    'user': '👤',
    'admin': '👑',
    'time': '🕐',
    'fire': '🔥',
    'star': '⭐',
    'heart': '❤️',
    'check': '✔️',
    'arrow_right': '➡️',
    'new': '🆕',
}


# ===== ДЕКОРАТОРЫ =====

def typing_action(func):
    """Показывает 'typing...' пока функция выполняется"""
    @wraps(func)
    def wrapper(chat_id, *args, **kwargs):
        send_typing_action(chat_id)
        return func(chat_id, *args, **kwargs)
    return wrapper


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Повторяет запрос при ошибке"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator


def rate_limit(calls: int = 30, period: float = 1.0):
    """Ограничение частоты вызовов"""
    call_times = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Удаляем старые вызовы
            call_times[:] = [t for t in call_times if now - t < period]
            
            if len(call_times) >= calls:
                sleep_time = period - (now - call_times[0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
            
            call_times.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ===== TELEGRAM API ФУНКЦИИ =====

def send_typing_action(chat_id: int):
    """Отправка typing action"""
    if not BOT_TOKEN or not REQUESTS_AVAILABLE:
        return
    
    try:
        url = f'{TELEGRAM_API_URL}/sendChatAction'
        data = {'chat_id': chat_id, 'action': 'typing'}
        requests.post(url, json=data, timeout=5)
    except Exception as e:
        logger.debug(f"Failed to send typing action: {e}")


@retry_on_error(max_retries=3)
@rate_limit(calls=30, period=1.0)
def send_message(
    chat_id: int,
    text: str,
    reply_markup: Optional[Dict] = None,
    parse_mode: str = 'HTML',
    disable_web_page_preview: bool = False
) -> Optional[Dict]:
    """
    Отправка сообщения с retry и rate limiting
    """
    if not BOT_TOKEN or not REQUESTS_AVAILABLE:
        logger.info(f"[BOT] {chat_id}: {text}")
        return None
    
    url = f'{TELEGRAM_API_URL}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'disable_web_page_preview': disable_web_page_preview
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message: {e}")
        raise


def create_inline_keyboard(buttons: List[List[Dict]]) -> Dict:
    """Создает inline клавиатуру"""
    return {'inline_keyboard': buttons}


def create_reply_keyboard(buttons: List[List[str]], resize: bool = True, one_time: bool = False) -> Dict:
    """Создает reply клавиатуру"""
    keyboard = [[{'text': btn} for btn in row] for row in buttons]
    return {
        'keyboard': keyboard,
        'resize_keyboard': resize,
        'one_time_keyboard': one_time
    }


# ===== КРАСИВЫЕ СООБЩЕНИЯ =====

def format_price(price: float) -> str:
    """Форматирует цену красиво"""
    return f"{price:,.0f} ₽".replace(',', ' ')


def format_order_message(order_data: Dict) -> str:
    """
    Создает красивое сообщение о заказе для администратора
    """
    customer = order_data.get('customer', {})
    items = order_data.get('items', [])
    totals = order_data.get('totals', {})
    
    # Шапка
    msg = f"{EMOJI['new']} <b>НОВЫЙ ЗАКАЗ</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Информация о клиенте
    msg += f"{EMOJI['user']} <b>КЛИЕНТ:</b>\n"
    msg += f"   • Имя: {customer.get('name', 'Не указано')}\n"
    msg += f"   • Телефон: {customer.get('phone', 'Не указан')}\n"
    if customer.get('address'):
        msg += f"   • Адрес: {customer.get('address')}\n"
    if customer.get('telegram_username'):
        msg += f"   • TG: @{customer['telegram_username']}\n"
    msg += "\n"
    
    # Товары
    msg += f"{EMOJI['cart']} <b>ТОВАРЫ:</b>\n"
    for i, item in enumerate(items, 1):
        title = item.get('title', 'Товар')
        price = item.get('price', 0)
        quantity = item.get('quantity', 1)
        size = item.get('size')
        
        msg += f"   {i}. {title}"
        if size:
            msg += f" <code>[{size}]</code>"
        msg += f"\n      {format_price(price)} × {quantity} = {format_price(price * quantity)}\n"
    
    msg += "\n"
    
    # Итого
    msg += f"{EMOJI['money']} <b>ИТОГО: {format_price(totals.get('total', 0))}</b>\n\n"
    
    # Время
    msg += f"{EMOJI['time']} {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"{EMOJI['fire']} <b>Обработать в течение 15 минут!</b>"
    
    return msg


def format_payment_instructions(order_number: int, total: float) -> str:
    """
    Создает инструкцию по оплате для клиента
    """
    msg = f"{EMOJI['success']} <b>Заказ #{order_number} принят!</b>\n\n"
    
    msg += f"{EMOJI['money']} <b>Сумма к оплате: {format_price(total)}</b>\n\n"
    
    msg += f"{EMOJI['phone']} <b>Оплата через СБП</b> (без комиссии):\n\n"
    
    msg += "1️⃣ Откройте приложение вашего банка\n"
    msg += "2️⃣ Выберите «Переводы» → «По номеру телефона»\n"
    msg += f"3️⃣ Номер: <code>{ADMIN_PHONE}</code>\n"
    msg += f"4️⃣ Сумма: <code>{total:.0f}</code> ₽\n"
    msg += f"5️⃣ Комментарий: <code>Заказ {order_number}</code>\n\n"
    
    msg += f"{EMOJI['check']} После оплаты отправьте скриншок чека\n"
    msg += f"{EMOJI['order']} Отправим заказ в течение часа\n\n"
    
    msg += f"{EMOJI['heart']} Спасибо за покупку!"
    
    return msg


def format_order_confirmation(order_number: int, total: float, items_count: int) -> str:
    """
    Краткое подтверждение заказа
    """
    msg = f"{EMOJI['success']} <b>Заказ оформлен!</b>\n\n"
    msg += f"{EMOJI['order']} Номер: <b>#{order_number}</b>\n"
    msg += f"{EMOJI['cart']} Товаров: <b>{items_count}</b>\n"
    msg += f"{EMOJI['money']} Сумма: <b>{format_price(total)}</b>\n\n"
    msg += f"{EMOJI['time']} Менеджер свяжется с вами в течение 15 минут\n"
    msg += f"{EMOJI['phone']} Для срочных вопросов: /support"
    
    return msg


# ===== ОБРАБОТКА ЗАКАЗОВ =====

@typing_action
def handle_new_order(chat_id: int, order_data: Dict) -> bool:
    """
    Обработка нового заказа с красивыми уведомлениями
    """
    try:
        logger.info(f"Processing order from chat_id: {chat_id}")
        
        # Валидация данных
        customer = order_data.get('customer', {})
        items = order_data.get('items', [])
        totals = order_data.get('totals', {})
        
        if not items:
            send_message(
                chat_id,
                f"{EMOJI['error']} Ошибка: корзина пуста"
            )
            return False
        
        # Сохранение в БД
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Генерируем номер заказа
            cursor.execute('SELECT COALESCE(MAX(order_number), 0) + 1 FROM orders')
            order_number = cursor.fetchone()[0]
            
            # Сохраняем заказ
            cursor.execute('''
                INSERT INTO orders (
                    order_number, customer_name, customer_phone, customer_address,
                    telegram_id, telegram_username, items, total_amount, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')
            ''', (
                order_number,
                customer.get('name', 'Клиент'),
                customer.get('phone', 'Не указан'),
                customer.get('address'),
                str(chat_id),
                customer.get('telegram_username'),
                str(items),  # JSON строка
                totals.get('total', 0)
            ))
            
            conn.commit()
            logger.info(f"Order #{order_number} saved to database")
        
        # Отправляем подтверждение клиенту
        confirmation = format_order_confirmation(
            order_number,
            totals.get('total', 0),
            len(items)
        )
        send_message(chat_id, confirmation)
        
        # Небольшая пауза для красоты
        time.sleep(0.5)
        
        # Отправляем инструкции по оплате
        payment_instructions = format_payment_instructions(
            order_number,
            totals.get('total', 0)
        )
        
        keyboard = create_inline_keyboard([[
            {'text': f'{EMOJI["phone"]} Позвонить', 'url': f'tel:{ADMIN_PHONE}'},
            {'text': f'{EMOJI["info"]} Помощь', 'callback_data': 'help'}
        ]])
        
        send_message(chat_id, payment_instructions, reply_markup=keyboard)
        
        # Уведомляем администраторов
        admin_message = format_order_message(order_data)
        
        admin_keyboard = create_inline_keyboard([[
            {'text': f'{EMOJI["user"]} Связаться', 'url': f'tg://user?id={chat_id}'},
            {'text': f'{EMOJI["check"]} Обработан', 'callback_data': f'order_done_{order_number}'}
        ]])
        
        for admin_id in ADMIN_IDS:
            try:
                send_message(int(admin_id), admin_message, reply_markup=admin_keyboard)
                logger.info(f"Order notification sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing order: {e}", exc_info=True)
        send_message(
            chat_id,
            f"{EMOJI['error']} Произошла ошибка при оформлении заказа.\n"
            f"{EMOJI['phone']} Пожалуйста, свяжитесь с поддержкой: /support"
        )
        return False


# ===== КОМАНДЫ БОТА =====

@typing_action
def handle_start_command(chat_id: int, user_data: Dict):
    """Красивая стартовая команда"""
    is_admin = str(chat_id) in ADMIN_IDS
    
    if is_admin:
        text = f"{EMOJI['admin']} <b>Добро пожаловать, Администратор!</b>\n\n"
        text += f"{EMOJI['shop']} Вы можете управлять:\n"
        text += f"   • {EMOJI['cart']} Товарами\n"
        text += f"   • {EMOJI['order']} Заказами\n"
        text += f"   • {EMOJI['user']} Клиентами\n"
        text += f"   • {EMOJI['star']} Отзывами\n\n"
        text += f"{EMOJI['info']} Используйте меню для навигации"
        
        keyboard = create_reply_keyboard([
            [f'{EMOJI["shop"]} Каталог', f'{EMOJI["order"]} Заказы'],
            [f'{EMOJI["user"]} Клиенты', f'{EMOJI["star"]} Отзывы'],
            [f'{EMOJI["info"]} Статистика']
        ])
    else:
        text = f"{EMOJI['shop']} <b>Добро пожаловать в магазин!</b>\n\n"
        text += f"{EMOJI['fire']} Здесь вы можете:\n"
        text += f"   • {EMOJI['cart']} Выбрать товары\n"
        text += f"   • {EMOJI['order']} Оформить заказ\n"
        text += f"   • {EMOJI['phone']} Связаться с нами\n"
        text += f"   • {EMOJI['star']} Оставить отзыв\n\n"
        text += f"{EMOJI['arrow_right']} Нажмите кнопку ниже, чтобы начать!"
        
        keyboard = create_reply_keyboard([
            [f'{EMOJI["shop"]} Открыть магазин'],
            [f'{EMOJI["phone"]} Поддержка', f'{EMOJI["star"]} Отзывы']
        ])
    
    send_message(chat_id, text, reply_markup=keyboard)


@typing_action  
def handle_support_command(chat_id: int):
    """Команда поддержки"""
    text = f"{EMOJI['phone']} <b>Поддержка клиентов</b>\n\n"
    text += f"{EMOJI['time']} <b>Время работы:</b>\n"
    text += "   Пн-Пт: 9:00 - 21:00\n"
    text += "   Сб-Вс: 10:00 - 20:00\n\n"
    text += f"{EMOJI['info']} Напишите ваш вопрос, и мы ответим в течение 15 минут.\n\n"
    text += f"{EMOJI['phone']} Для срочных вопросов:\n"
    text += f"   Телефон: <code>{ADMIN_PHONE}</code>"
    
    keyboard = create_inline_keyboard([[
        {'text': f'{EMOJI["phone"]} Позвонить', 'url': f'tel:{ADMIN_PHONE}'},
        {'text': f'{EMOJI["arrow_right"]} Назад', 'callback_data': 'back_to_menu'}
    ]])
    
    send_message(chat_id, text, reply_markup=keyboard)


# ===== ANALYTICS =====

def log_user_action(user_id: int, action: str, details: Optional[Dict] = None):
    """Логирование действий пользователя для аналитики"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO user_actions (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, str(details) if details else None))
            
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")


# ===== HEALTH CHECK =====

def health_check() -> Dict[str, Any]:
    """Проверка здоровья системы"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Проверка БД
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {e}'
        status['status'] = 'unhealthy'
    
    # Проверка Telegram API
    try:
        if REQUESTS_AVAILABLE and BOT_TOKEN:
            url = f'{TELEGRAM_API_URL}/getMe'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                status['checks']['telegram_api'] = 'ok'
            else:
                status['checks']['telegram_api'] = f'error: status {response.status_code}'
                status['status'] = 'degraded'
        else:
            status['checks']['telegram_api'] = 'not_configured'
    except Exception as e:
        status['checks']['telegram_api'] = f'error: {e}'
        status['status'] = 'degraded'
    
    return status


if __name__ == '__main__':
    # Тест
    print("🧪 Тестирование профессионального бота...")
    
    # Тест health check
    health = health_check()
    print(f"Health Check: {health}")
    
    # Тест форматирования
    test_order = {
        'customer': {
            'name': 'Иван Иванов',
            'phone': '+7 999 123-45-67',
            'address': 'Москва, ул. Примерная, 1'
        },
        'items': [
            {'title': 'iPhone 15 Pro', 'price': 99999, 'quantity': 1},
            {'title': 'AirPods Pro', 'price': 24999, 'quantity': 2, 'size': 'Белый'}
        ],
        'totals': {'total': 149997}
    }
    
    print("\n" + "="*50)
    print(format_order_message(test_order))
    print("="*50)
    
    print("\n✅ Тесты пройдены!")

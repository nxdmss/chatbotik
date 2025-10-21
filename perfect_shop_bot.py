#!/usr/bin/env python3
"""
🛍️ ИДЕАЛЬНЫЙ МАГАЗИН-БОТ С WEBAPP
==================================
Все в одном файле - бот, веб-сервер, обработка заказов
Просто запустите и все заработает!

Запуск: python3 perfect_shop_bot.py
"""

import os
import json
import sqlite3
import logging
import asyncio
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/shop_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === КОНФИГУРАЦИЯ ===
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_IDS = [1593426947]  # Ваш ID
PORT = int(os.getenv('PORT', 8080))
WEBAPP_URL = os.getenv('WEBAPP_URL', f'http://localhost:{PORT}')
DATABASE_PATH = 'shop.db'

# Создаем необходимые директории
Path('logs').mkdir(exist_ok=True)
Path('webapp').mkdir(exist_ok=True)
Path('webapp/uploads').mkdir(exist_ok=True)

# === БАЗА ДАННЫХ ===
def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL,
            photo TEXT DEFAULT '',
            sizes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")

init_database()

# === TELEGRAM BOT API ===
import requests

def send_telegram_message(chat_id, text, parse_mode='HTML'):
    """Отправка сообщения в Telegram"""
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ Сообщение отправлено пользователю {chat_id}")
            return True
        else:
            logger.error(f"❌ Ошибка отправки сообщения: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")
        return False

def get_telegram_updates(offset=0):
    """Получение обновлений от Telegram"""
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
        params = {
            'offset': offset,
            'timeout': 30,
            'allowed_updates': ['message', 'callback_query']
        }
        response = requests.get(url, params=params, timeout=35)
        
        if response.status_code == 200:
            return response.json().get('result', [])
        else:
            logger.error(f"❌ Ошибка получения обновлений: {response.text}")
            return []
    except Exception as e:
        logger.error(f"❌ Ошибка получения обновлений: {e}")
        return []

def send_order_to_admins(order_data, user_info):
    """Отправка заказа администраторам"""
    try:
        # Получаем информацию о товарах
        products_file = Path('webapp/products.json')
        if products_file.exists():
            with open(products_file, 'r', encoding='utf-8') as f:
                products = {p['id']: p for p in json.load(f)}
        else:
            products = {}
        
        # Формируем сообщение
        message = "🛒 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
        message += f"👤 <b>Клиент:</b> {user_info.get('first_name', 'Неизвестно')}"
        if user_info.get('username'):
            message += f" (@{user_info['username']})"
        message += f"\n🆔 <b>ID:</b> {user_info.get('id', 'Неизвестно')}\n\n"
        
        message += "📦 <b>Товары:</b>\n"
        
        items = order_data.get('items', [])
        total = 0
        
        for i, item in enumerate(items, 1):
            product_id = item.get('productId')
            quantity = item.get('quantity', 1)
            size = item.get('size')
            
            product = products.get(product_id, {})
            title = product.get('title', f'Товар #{product_id}')
            price = product.get('price', 0)
            
            item_total = price * quantity
            total += item_total
            
            message += f"\n{i}. <b>{title}</b>\n"
            message += f"   • Количество: {quantity}\n"
            if size:
                message += f"   • Размер: {size}\n"
            message += f"   • Цена: {price}₽ × {quantity} = {item_total}₽\n"
        
        message += f"\n💰 <b>ИТОГО: {total}₽</b>\n"
        message += f"\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        message += f"\n💬 Для связи с клиентом напишите ему напрямую"
        
        # Отправляем всем администраторам
        success_count = 0
        for admin_id in ADMIN_IDS:
            if send_telegram_message(admin_id, message):
                success_count += 1
        
        logger.info(f"✅ Заказ отправлен {success_count} администраторам из {len(ADMIN_IDS)}")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки заказа админам: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_telegram_update(update):
    """Обработка обновления от Telegram"""
    try:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user = message['from']
            
            # Обработка команд
            if 'text' in message:
                text = message['text']
                
                if text == '/start':
                    # Приветственное сообщение с кнопкой WebApp
                    response = (
                        f"👋 Привет, {user.get('first_name', 'друг')}!\n\n"
                        f"🛍️ Добро пожаловать в наш магазин!\n\n"
                        f"Открой WebApp чтобы посмотреть каталог и сделать заказ 👇"
                    )
                    
                    # Отправляем с inline кнопкой WebApp
                    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
                    data = {
                        'chat_id': chat_id,
                        'text': response,
                        'reply_markup': {
                            'inline_keyboard': [[
                                {
                                    'text': '🛍️ Открыть магазин',
                                    'web_app': {'url': f'{WEBAPP_URL}/webapp/'}
                                }
                            ]]
                        }
                    }
                    requests.post(url, json=data)
                    logger.info(f"✅ Отправлено приветствие пользователю {chat_id}")
                
                elif text == '/help':
                    help_text = (
                        "🆘 <b>Справка</b>\n\n"
                        "/start - Главное меню\n"
                        "/help - Эта справка\n\n"
                        "Нажмите 'Открыть магазин' чтобы начать покупки!"
                    )
                    send_telegram_message(chat_id, help_text)
            
            # Обработка данных из WebApp
            elif 'web_app_data' in message:
                web_app_data = message['web_app_data']['data']
                logger.info(f"📦 Получены данные WebApp от {chat_id}: {web_app_data}")
                
                try:
                    data = json.loads(web_app_data)
                    
                    if data.get('action') == 'order':
                        # Сохраняем заказ в базу
                        conn = sqlite3.connect(DATABASE_PATH)
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            INSERT INTO orders (user_id, user_name, items, total, status)
                            VALUES (?, ?, ?, ?, 'new')
                        ''', (
                            chat_id,
                            user.get('first_name', '') + ' ' + user.get('last_name', ''),
                            json.dumps(data.get('items', [])),
                            data.get('total', 0)
                        ))
                        
                        order_id = cursor.lastrowid
                        conn.commit()
                        conn.close()
                        
                        logger.info(f"✅ Заказ #{order_id} сохранен в БД")
                        
                        # Отправляем администраторам
                        if send_order_to_admins(data, user):
                            # Подтверждение клиенту
                            confirmation = (
                                f"✅ <b>Заказ #{order_id} принят!</b>\n\n"
                                f"Ваш заказ получен и передан администратору.\n"
                                f"Скоро мы с вами свяжемся!\n\n"
                                f"💰 Сумма: {data.get('total', 0)}₽\n\n"
                                f"Спасибо за покупку! 🛍️"
                            )
                            send_telegram_message(chat_id, confirmation)
                        else:
                            error_msg = (
                                "⚠️ Заказ получен, но возникла проблема с уведомлением администратора.\n"
                                "Мы исправим это в ближайшее время!"
                            )
                            send_telegram_message(chat_id, error_msg)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка парсинга JSON: {e}")
                    send_telegram_message(chat_id, "❌ Ошибка обработки данных. Попробуйте еще раз.")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки обновления: {e}")
        import traceback
        logger.error(traceback.format_exc())

# === WEB SERVER ===
class WebAppHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для WebApp"""
    
    def log_message(self, format, *args):
        """Переопределяем логирование"""
        logger.info(f"{self.address_string()} - {format%args}")
    
    def do_GET(self):
        """Обработка GET запросов"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Главная страница WebApp
            if path == '/webapp/' or path == '/webapp/index.html' or path == '/webapp':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html = self.get_webapp_html()
                self.wfile.write(html.encode('utf-8'))
            
            # API: список товаров
            elif path == '/api/products' or path == '/webapp/products.json':
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                products_file = Path('webapp/products.json')
                if products_file.exists():
                    with open(products_file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                else:
                    products = []
                
                self.wfile.write(json.dumps(products, ensure_ascii=False).encode('utf-8'))
            
            # Обработка загруженных файлов
            elif path.startswith('/webapp/uploads/') or path.startswith('/webapp/static/uploads/'):
                file_path = path.replace('/webapp/', '')
                file_path = Path('webapp') / file_path.lstrip('/')
                
                if file_path.exists():
                    self.send_response(200)
                    if path.endswith('.jpg') or path.endswith('.jpeg'):
                        self.send_header('Content-type', 'image/jpeg')
                    elif path.endswith('.png'):
                        self.send_header('Content-type', 'image/png')
                    else:
                        self.send_header('Content-type', 'application/octet-stream')
                    self.end_headers()
                    
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'File not found')
            
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not found')
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки GET: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal server error')
    
    def get_webapp_html(self):
        """HTML для WebApp"""
        return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Магазин</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
            padding: 16px;
            padding-bottom: 80px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 24px;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }
        
        .product-card {
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            border-radius: 12px;
            padding: 12px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .product-card:active {
            transform: scale(0.95);
        }
        
        .product-image {
            width: 100%;
            height: 150px;
            background: #ddd;
            border-radius: 8px;
            margin-bottom: 8px;
            object-fit: cover;
        }
        
        .product-title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }
        
        .product-price {
            color: var(--tg-theme-link-color, #0088cc);
            font-weight: 700;
            font-size: 16px;
        }
        
        .cart-button {
            background: var(--tg-theme-button-color, #0088cc);
            color: var(--tg-theme-button-text-color, #ffffff);
            padding: 8px;
            border-radius: 8px;
            border: none;
            font-size: 12px;
            margin-top: 8px;
            width: 100%;
            cursor: pointer;
        }
        
        .cart-panel {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            padding: 16px;
            border-top: 1px solid #ddd;
            display: none;
        }
        
        .cart-panel.active {
            display: block;
        }
        
        .cart-total {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        
        .checkout-button {
            background: #4CAF50;
            color: white;
            padding: 14px;
            border-radius: 8px;
            border: none;
            font-size: 16px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛍️ Наш магазин</h1>
        <p>Выберите товары и добавьте в корзину</p>
    </div>
    
    <div id="products" class="products-grid"></div>
    
    <div id="cart" class="cart-panel">
        <div class="cart-total">
            Итого: <span id="total">0</span>₽
        </div>
        <button class="checkout-button" onclick="checkout()">
            Оформить заказ
        </button>
    </div>
    
    <script>
        // Инициализация Telegram WebApp
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        // Корзина
        let cart = [];
        
        // Загрузка товаров
        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                const products = await response.json();
                
                const container = document.getElementById('products');
                
                if (products.length === 0) {
                    container.innerHTML = '<div class="empty-state">Товары скоро появятся!</div>';
                    return;
                }
                
                container.innerHTML = products.map(product => `
                    <div class="product-card">
                        <img src="${product.photo || '/webapp/uploads/default.jpg'}" 
                             class="product-image" 
                             alt="${product.title}"
                             onerror="this.src='/webapp/uploads/default.jpg'">
                        <div class="product-title">${product.title}</div>
                        <div class="product-price">${product.price}₽</div>
                        <button class="cart-button" onclick="addToCart(${product.id}, '${product.title}', ${product.price})">
                            В корзину
                        </button>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Ошибка загрузки товаров:', error);
                document.getElementById('products').innerHTML = 
                    '<div class="empty-state">Ошибка загрузки товаров</div>';
            }
        }
        
        // Добавление в корзину
        function addToCart(id, title, price) {
            const existing = cart.find(item => item.productId === id);
            
            if (existing) {
                existing.quantity++;
            } else {
                cart.push({
                    productId: id,
                    title: title,
                    price: price,
                    quantity: 1
                });
            }
            
            updateCart();
            
            // Вибрация при добавлении
            if (tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }
        }
        
        // Обновление корзины
        function updateCart() {
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            document.getElementById('total').textContent = total;
            
            const cartPanel = document.getElementById('cart');
            if (cart.length > 0) {
                cartPanel.classList.add('active');
            } else {
                cartPanel.classList.remove('active');
            }
        }
        
        // Оформление заказа
        function checkout() {
            if (cart.length === 0) {
                tg.showAlert('Корзина пуста!');
                return;
            }
            
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            
            const orderData = {
                action: 'order',
                items: cart,
                total: total
            };
            
            console.log('Отправка заказа:', orderData);
            
            // Отправляем данные боту
            tg.sendData(JSON.stringify(orderData));
            
            // Закрываем WebApp
            setTimeout(() => {
                tg.close();
            }, 100);
        }
        
        // Загружаем товары при старте
        loadProducts();
    </script>
</body>
</html>'''

# === MAIN ===
def run_web_server():
    """Запуск веб-сервера"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), WebAppHandler)
        logger.info(f"🌐 Веб-сервер запущен на порту {PORT}")
        logger.info(f"📱 WebApp URL: {WEBAPP_URL}/webapp/")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Ошибка веб-сервера: {e}")

def run_telegram_bot():
    """Запуск Telegram бота"""
    logger.info("🤖 Telegram бот запущен")
    
    offset = 0
    while True:
        try:
            updates = get_telegram_updates(offset)
            
            for update in updates:
                offset = update['update_id'] + 1
                process_telegram_update(update)
            
        except KeyboardInterrupt:
            logger.info("👋 Остановка бота")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка в боте: {e}")
            import traceback
            logger.error(traceback.format_exc())
            import time
            time.sleep(5)

def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("🛍️ ИДЕАЛЬНЫЙ МАГАЗИН-БОТ")
    print("=" * 60)
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        print("💡 Установите переменную окружения:")
        print("   export BOT_TOKEN='ваш_токен_бота'")
        return
    
    print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
    print(f"✅ Admin IDs: {ADMIN_IDS}")
    print(f"🌐 WebApp URL: {WEBAPP_URL}/webapp/")
    print(f"🔌 Port: {PORT}")
    print("=" * 60 + "\n")
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Даем серверу время на запуск
    import time
    time.sleep(2)
    
    print("✅ Все компоненты запущены!")
    print("💡 Напишите боту /start чтобы открыть магазин\n")
    
    # Запускаем бота в основном потоке
    run_telegram_bot()

if __name__ == '__main__':
    main()


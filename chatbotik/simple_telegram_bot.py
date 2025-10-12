#!/usr/bin/env python3
"""
🤖 SIMPLE TELEGRAM BOT WITH WEBAPP
==================================
Простой Telegram бот с веб-приложением для Replit
"""

import os
import json
import sqlite3
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
PORT = int(os.getenv('PORT', 8000))
WEBAPP_URL = f'http://localhost:{PORT}'

# База данных
DATABASE_PATH = 'shop.db'

class SimpleTelegramBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.webapp_url = WEBAPP_URL
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Создаем таблицы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                total_amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем тестовые данные
        cursor.execute('SELECT COUNT(*) FROM products')
        if cursor.fetchone()[0] == 0:
            test_products = [
                ('iPhone 15 Pro', 99999, 'Новейший смартфон Apple', 'electronics'),
                ('MacBook Air M3', 129999, 'Мощный ноутбук для работы', 'electronics'),
                ('Nike Air Max', 8999, 'Спортивные кроссовки', 'clothing'),
                ('Кофе Starbucks', 299, 'Премиальный кофе', 'food'),
                ('Книга Python', 1999, 'Программирование на Python', 'books')
            ]
            
            for title, price, description, category in test_products:
                cursor.execute('''
                    INSERT INTO products (title, price, description, category)
                    VALUES (?, ?, ?, ?)
                ''', (title, price, description, category))
        
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Отправка сообщения в Telegram"""
        if not self.token or not REQUESTS_AVAILABLE:
            print(f"📱 [BOT] {chat_id}: {text}")
            return
        
        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
    
    def handle_start(self, chat_id):
        """Обработка команды /start"""
        text = '''🛍️ **Добро пожаловать в наш магазин!**

Здесь вы можете:
• 🛒 Просматривать товары
• 📦 Добавлять в корзину
• 💳 Оформлять заказы
• 📞 Связываться с нами

Нажмите кнопку ниже, чтобы открыть магазин!'''
        
        keyboard = {
            'inline_keyboard': [
                [{'text': '🛍️ Открыть магазин', 'web_app': {'url': self.webapp_url}}],
                [{'text': '📦 Каталог', 'callback_data': 'catalog'}],
                [{'text': '📞 Контакты', 'callback_data': 'contact'}]
            ]
        }
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_catalog(self, chat_id):
        """Обработка команды /catalog"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products LIMIT 5')
            products = cursor.fetchall()
            conn.close()
            
            if not products:
                self.send_message(chat_id, '📦 Каталог пока пуст. Зайдите позже!')
                return
            
            text = '🛍️ **Каталог товаров:**\n\n'
            
            for i, product in enumerate(products, 1):
                text += f'{i}. **{product[1]}**\n'
                text += f'   💰 {product[2]:,} ₽\n'.replace(',', ' ')
                if product[3]:
                    text += f'   📝 {product[3][:50]}...\n'
                text += '\n'
            
            text += 'Нажмите кнопку ниже, чтобы открыть полный каталог!'
            
            keyboard = {
                'inline_keyboard': [
                    [{'text': '🛍️ Открыть полный каталог', 'web_app': {'url': self.webapp_url}}]
                ]
            }
            
            self.send_message(chat_id, text, keyboard)
        except Exception as e:
            print(f"❌ Ошибка в каталоге: {e}")
            self.send_message(chat_id, '❌ Ошибка загрузки каталога')
    
    def handle_contact(self, chat_id):
        """Обработка команды /contact"""
        text = '''📞 **Связаться с нами:**

🕐 **Время работы:** 9:00 - 21:00 (МСК)

📱 **Телефон:** +7 (999) 123-45-67
📧 **Email:** support@eshoppro.ru
💬 **Telegram:** @eshoppro_support

🏢 **Адрес:**
г. Москва, ул. Примерная, д. 123

❓ **Частые вопросы:**
• Доставка по всей России
• Оплата картой или наличными
• Возврат в течение 14 дней
• Гарантия на все товары

Напишите нам, и мы обязательно поможем!'''
        
        keyboard = {
            'inline_keyboard': [
                [{'text': '💬 Написать в поддержку', 'url': 'https://t.me/eshoppro_support'}],
                [{'text': '🛍️ Вернуться в магазин', 'web_app': {'url': self.webapp_url}}]
            ]
        }
        
        self.send_message(chat_id, text, keyboard)
    
    def handle_webapp_data(self, chat_id, data):
        """Обработка данных от WebApp"""
        try:
            if data.get('type') == 'order':
                # Сохраняем заказ в базу данных
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                order_data = data.get('order', {})
                total_amount = 0
                
                # Простой расчет суммы (в реальном проекте нужно получать цены из БД)
                for item in order_data.get('items', []):
                    cursor.execute('SELECT price FROM products WHERE id = ?', (item.get('product_id'),))
                    product = cursor.fetchone()
                    if product:
                        total_amount += product[0] * item.get('quantity', 1)
                
                cursor.execute('''
                    INSERT INTO orders (customer_name, customer_phone, total_amount)
                    VALUES (?, ?, ?)
                ''', (order_data.get('customer_name', ''), 
                      order_data.get('customer_phone', ''), 
                      total_amount))
                
                order_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                response_text = f'''✅ **Заказ оформлен успешно!**

🆔 Номер заказа: #{order_id}
💰 Сумма: {total_amount:,} ₽
📞 Мы свяжемся с вами в ближайшее время!'''
                
                self.send_message(chat_id, response_text)
                
            elif data.get('type') == 'feedback':
                response_text = f'''✅ **Спасибо за обратную связь!**

📝 Ваше сообщение: "{data.get('feedback', '')}"

Мы обязательно рассмотрим ваше сообщение и ответим!'''
                
                self.send_message(chat_id, response_text)
                
        except Exception as e:
            print(f"❌ Ошибка обработки данных WebApp: {e}")
            self.send_message(chat_id, '❌ Произошла ошибка при обработке данных')

class WebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.get_main_page()
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path == '/api/products':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
                products = cursor.fetchall()
                conn.close()
                
                products_data = []
                for product in products:
                    products_data.append({
                        'id': product[0],
                        'title': product[1],
                        'price': product[2],
                        'description': product[3],
                        'category': product[4],
                        'image_url': product[5] if product[5] else '',
                        'created_at': product[6]
                    })
                
                self.wfile.write(json.dumps(products_data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"❌ Ошибка получения товаров: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/api/orders':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Простая обработка заказа
                response = {'success': True, 'order_id': 12345}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Ошибка обработки заказа: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'Internal Server Error')
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def get_main_page(self):
        """Главная страница WebApp"""
        return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛍️ E-Shop Pro - Telegram Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
            padding: 16px;
        }
        .header {
            text-align: center;
            margin-bottom: 24px;
            padding: 20px;
            background: var(--tg-theme-secondary-bg-color, #f1f1f1);
            border-radius: 12px;
        }
        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .product-card {
            background: var(--tg-theme-bg-color, #ffffff);
            border: 1px solid var(--tg-theme-hint-color, #e0e0e0);
            border-radius: 12px;
            padding: 16px;
            transition: transform 0.2s;
        }
        .product-card:hover {
            transform: translateY(-2px);
        }
        .product-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .product-price {
            font-size: 18px;
            font-weight: 700;
            color: var(--tg-theme-button-color, #2481cc);
        }
        .add-to-cart-btn {
            background: var(--tg-theme-button-color, #2481cc);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 12px;
            width: 100%;
        }
        .cart-section {
            background: var(--tg-theme-secondary-bg-color, #f1f1f1);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .checkout-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 16px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 16px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: var(--tg-theme-hint-color, #999);
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛍️ E-Shop Pro</h1>
        <p>Добро пожаловать в наш магазин!</p>
    </div>
    
    <div id="productsContainer" class="loading">
        <div>Загрузка товаров...</div>
    </div>
    
    <div class="cart-section">
        <h2>🛒 Корзина</h2>
        <div id="cartItems">Корзина пуста</div>
        <div id="cartTotal">Итого: 0 ₽</div>
        <button id="checkoutBtn" class="checkout-btn hidden">Оформить заказ</button>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        let products = [];
        let cart = [];
        
        // Загрузка товаров
        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                products = await response.json();
                renderProducts();
            } catch (error) {
                document.getElementById('productsContainer').innerHTML = 
                    '<div class="loading">Ошибка загрузки товаров</div>';
            }
        }
        
        // Отображение товаров
        function renderProducts() {
            const container = document.getElementById('productsContainer');
            container.className = 'products-grid';
            
            container.innerHTML = products.map(product => `
                <div class="product-card">
                    <div class="product-title">${product.title}</div>
                    ${product.description ? `<div style="margin-bottom: 8px; color: #666;">${product.description}</div>` : ''}
                    <div class="product-price">${product.price.toLocaleString()} ₽</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        В корзину
                    </button>
                </div>
            `).join('');
        }
        
        // Добавление в корзину
        function addToCart(productId) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            const existingItem = cart.find(item => item.product_id === productId);
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cart.push({
                    product_id: productId,
                    quantity: 1,
                    product: product
                });
            }
            
            updateCartUI();
            tg.showAlert(`${product.title} добавлен в корзину!`);
        }
        
        // Обновление интерфейса корзины
        function updateCartUI() {
            const cartItems = document.getElementById('cartItems');
            const cartTotal = document.getElementById('cartTotal');
            const checkoutBtn = document.getElementById('checkoutBtn');
            
            if (cart.length === 0) {
                cartItems.innerHTML = 'Корзина пуста';
                cartTotal.innerHTML = 'Итого: 0 ₽';
                checkoutBtn.classList.add('hidden');
                return;
            }
            
            cartItems.innerHTML = cart.map(item => `
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span>${item.product.title} x${item.quantity}</span>
                    <span>${(item.product.price * item.quantity).toLocaleString()} ₽</span>
                </div>
            `).join('');
            
            const total = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
            cartTotal.innerHTML = `Итого: ${total.toLocaleString()} ₽`;
            checkoutBtn.classList.remove('hidden');
        }
        
        // Оформление заказа
        function checkout() {
            if (cart.length === 0) return;
            
            const orderData = {
                type: 'order',
                order: {
                    customer_name: 'Покупатель',
                    customer_phone: '+7 (999) 123-45-67',
                    items: cart
                }
            };
            
            tg.sendData(JSON.stringify(orderData));
            tg.showAlert('Заказ отправлен! Спасибо за покупку!');
            
            cart = [];
            updateCartUI();
        }
        
        // Обработчики событий
        document.getElementById('checkoutBtn').addEventListener('click', checkout);
        
        // Запуск
        loadProducts();
    </script>
</body>
</html>'''

def start_web_server():
    """Запуск веб-сервера"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), WebAppHandler)
        print(f"🌐 Веб-сервер запущен на http://0.0.0.0:{PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК SIMPLE TELEGRAM BOT")
    print("=" * 40)
    
    bot = SimpleTelegramBot()
    
    if not bot.token:
        print("⚠️ BOT_TOKEN не найден - бот отключен")
        print("💡 Установите переменную окружения BOT_TOKEN")
    else:
        print(f"🤖 Бот готов к работе")
        print(f"📱 Токен: {bot.token[:10]}...")
        print(f"🌐 WebApp URL: {bot.webapp_url}")
    
    print("=" * 40)
    print("🛑 Для остановки нажмите Ctrl+C")
    
    # Запускаем веб-сервер
    start_web_server()

if __name__ == "__main__":
    main()

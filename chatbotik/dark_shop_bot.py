#!/usr/bin/env python3
"""
🌙 DARK TELEGRAM SHOP BOT WITH WORKING ADD FUNCTION
===================================================
Исправленная версия с темной темой и рабочими функциями
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

class DarkShopBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.webapp_url = WEBAPP_URL
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Создаем таблицы с правильной структурой
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'general',
                image_url TEXT DEFAULT '',
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
                ('iPhone 15 Pro', 99999, 'Новейший смартфон Apple с титановым корпусом', 'electronics', ''),
                ('MacBook Air M3', 129999, 'Мощный ноутбук для работы и творчества', 'electronics', ''),
                ('Nike Air Max 270', 8999, 'Спортивные кроссовки для активного образа жизни', 'clothing', ''),
                ('Кофе Starbucks Premium', 299, 'Премиальный кофе в зернах для истинных ценителей', 'food', ''),
                ('Книга "Python для начинающих"', 1999, 'Полное руководство по изучению Python', 'books', ''),
                ('Samsung Galaxy S24', 89999, 'Флагманский смартфон с ИИ-функциями', 'electronics', ''),
                ('Adidas Ultraboost 22', 12999, 'Беговые кроссовки с технологией Boost', 'clothing', ''),
                ('Чай Earl Grey Premium', 599, 'Элитный чай с бергамотом', 'food', '')
            ]
            
            for title, price, description, category, image_url in test_products:
                cursor.execute('''
                    INSERT INTO products (title, price, description, category, image_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, price, description, category, image_url))
        
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

class DarkWebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.get_dark_page()
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
                        'description': product[3] or '',
                        'category': product[4] or 'general',
                        'image_url': product[5] or '',
                        'created_at': product[6]
                    })
                
                self.wfile.write(json.dumps(products_data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"❌ Ошибка получения товаров: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
        
        elif self.path == '/api/add-product':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                # Получаем данные из URL параметров
                import urllib.parse
                params = urllib.parse.parse_qs(self.path.split('?')[1] if '?' in self.path else '')
                
                title = params.get('title', [''])[0]
                price = int(params.get('price', ['0'])[0])
                description = params.get('description', [''])[0]
                category = params.get('category', ['general'])[0]
                
                if title and price > 0:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO products (title, price, description, category)
                        VALUES (?, ?, ?, ?)
                    ''', (title, price, description, category))
                    conn.commit()
                    conn.close()
                    
                    response = {'success': True, 'message': 'Товар добавлен успешно!'}
                else:
                    response = {'success': False, 'message': 'Неверные данные товара'}
                
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"❌ Ошибка добавления товара: {e}")
                response = {'success': False, 'message': 'Ошибка добавления товара'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
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
        
        elif self.path == '/api/add-product':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                title = data.get('title', '')
                price = int(data.get('price', 0))
                description = data.get('description', '')
                category = data.get('category', 'general')
                
                if title and price > 0:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO products (title, price, description, category)
                        VALUES (?, ?, ?, ?)
                    ''', (title, price, description, category))
                    conn.commit()
                    conn.close()
                    
                    response = {'success': True, 'message': 'Товар добавлен успешно!'}
                else:
                    response = {'success': False, 'message': 'Неверные данные товара'}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Ошибка добавления товара: {e}")
                response = {'success': False, 'message': 'Ошибка добавления товара'}
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def get_dark_page(self):
        """Главная страница WebApp с темной темой"""
        return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌙 Dark Shop - Telegram Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            padding: 16px;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 24px;
            padding: 20px;
            background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
            border-radius: 16px;
            border: 1px solid #333;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .header h1 {
            font-size: 28px;
            margin-bottom: 8px;
            background: linear-gradient(45deg, #00d4ff, #ff00ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            color: #cccccc;
            font-size: 16px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .product-card {
            background: linear-gradient(135deg, #2d2d2d, #1f1f1f);
            border: 1px solid #333;
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .product-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0, 212, 255, 0.2);
            border-color: #00d4ff;
        }
        
        .product-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #00d4ff, #ff00ff);
        }
        
        .product-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #ffffff;
        }
        
        .product-description {
            color: #aaaaaa;
            font-size: 14px;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        
        .product-price {
            font-size: 20px;
            font-weight: 700;
            color: #00d4ff;
            margin-bottom: 16px;
        }
        
        .add-to-cart-btn {
            background: linear-gradient(45deg, #00d4ff, #ff00ff);
            color: #ffffff;
            border: none;
            padding: 12px 20px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .add-to-cart-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
        }
        
        .cart-section {
            background: linear-gradient(135deg, #2d2d2d, #1f1f1f);
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        
        .cart-section h2 {
            color: #00d4ff;
            margin-bottom: 16px;
            font-size: 20px;
        }
        
        .checkout-btn {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            border: none;
            padding: 16px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 16px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .checkout-btn:hover:not(.hidden) {
            transform: scale(1.02);
            box-shadow: 0 4px 20px rgba(40, 167, 69, 0.4);
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #aaaaaa;
            font-size: 16px;
        }
        
        .hidden { 
            display: none; 
        }
        
        .admin-section {
            background: linear-gradient(135deg, #2d2d2d, #1f1f1f);
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        
        .admin-form {
            display: grid;
            gap: 16px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .form-group label {
            color: #00d4ff;
            font-weight: 600;
            font-size: 14px;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            color: #ffffff;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }
        
        .add-product-btn {
            background: linear-gradient(45deg, #ff6b6b, #ffa500);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .add-product-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(255, 107, 107, 0.4);
        }
        
        .success-message {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            text-align: center;
            font-weight: 600;
        }
        
        .error-message {
            background: linear-gradient(45deg, #dc3545, #fd7e14);
            color: white;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            text-align: center;
            font-weight: 600;
        }
        
        .cart-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: #1a1a1a;
            border-radius: 8px;
            margin-bottom: 8px;
            border: 1px solid #333;
        }
        
        .cart-item-info {
            flex: 1;
        }
        
        .cart-item-title {
            color: #ffffff;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .cart-item-price {
            color: #00d4ff;
            font-weight: 600;
        }
        
        .quantity-controls {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .quantity-btn {
            background: #333;
            color: #ffffff;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .quantity-btn:hover {
            background: #00d4ff;
        }
        
        .quantity-input {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 6px;
            color: #ffffff;
            width: 50px;
            text-align: center;
        }
        
        .remove-btn {
            background: linear-gradient(45deg, #dc3545, #fd7e14);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 8px;
            transition: all 0.3s ease;
        }
        
        .remove-btn:hover {
            transform: scale(1.05);
        }
        
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            background: #2d2d2d;
            padding: 8px;
            border-radius: 12px;
        }
        
        .tab-btn {
            flex: 1;
            background: transparent;
            color: #aaaaaa;
            border: none;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .tab-btn.active {
            background: linear-gradient(45deg, #00d4ff, #ff00ff);
            color: #ffffff;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .search-box {
            position: relative;
            margin-bottom: 16px;
        }
        
        .search-box input {
            width: 100%;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 12px 16px 12px 40px;
            color: #ffffff;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #00d4ff;
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }
        
        .search-box::before {
            content: '🔍';
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 16px;
        }
        
        @media (max-width: 768px) {
            .products-grid {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-direction: column;
            }
            
            .tab-btn {
                margin-bottom: 4px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌙 Dark Shop</h1>
        <p>Добро пожаловать в наш темный магазин!</p>
    </div>
    
    <div class="tabs">
        <button class="tab-btn active" onclick="showTab('catalog')">🛍️ Каталог</button>
        <button class="tab-btn" onclick="showTab('cart')">🛒 Корзина</button>
        <button class="tab-btn" onclick="showTab('admin')">⚙️ Админ</button>
    </div>
    
    <div id="catalog" class="tab-content active">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Поиск товаров..." onkeyup="filterProducts()">
        </div>
        
        <div id="productsContainer" class="loading">
            <div>Загрузка товаров...</div>
        </div>
    </div>
    
    <div id="cart" class="tab-content">
        <div class="cart-section">
            <h2>🛒 Корзина покупок</h2>
            <div id="cartItems">Корзина пуста</div>
            <div id="cartTotal" style="font-size: 18px; font-weight: 600; color: #00d4ff; margin-top: 16px;">Итого: 0 ₽</div>
            <button id="checkoutBtn" class="checkout-btn hidden">💳 Оформить заказ</button>
        </div>
    </div>
    
    <div id="admin" class="tab-content">
        <div class="admin-section">
            <h2>⚙️ Панель администратора</h2>
            <div id="adminMessage"></div>
            <form class="admin-form" id="adminForm">
                <div class="form-group">
                    <label for="productTitle">Название товара</label>
                    <input type="text" id="productTitle" required>
                </div>
                <div class="form-group">
                    <label for="productPrice">Цена (₽)</label>
                    <input type="number" id="productPrice" min="1" required>
                </div>
                <div class="form-group">
                    <label for="productCategory">Категория</label>
                    <select id="productCategory" required>
                        <option value="electronics">Электроника</option>
                        <option value="clothing">Одежда</option>
                        <option value="food">Еда</option>
                        <option value="books">Книги</option>
                        <option value="general">Общее</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="productDescription">Описание</label>
                    <textarea id="productDescription" rows="3"></textarea>
                </div>
                <button type="submit" class="add-product-btn">➕ Добавить товар</button>
            </form>
        </div>
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
                console.error('Error loading products:', error);
            }
        }
        
        // Отображение товаров
        function renderProducts() {
            const container = document.getElementById('productsContainer');
            container.className = 'products-grid';
            
            if (products.length === 0) {
                container.innerHTML = '<div class="loading">Товары не найдены</div>';
                return;
            }
            
            container.innerHTML = products.map(product => `
                <div class="product-card">
                    <div class="product-title">${product.title}</div>
                    ${product.description ? `<div class="product-description">${product.description}</div>` : ''}
                    <div class="product-price">${product.price.toLocaleString()} ₽</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        🛒 В корзину
                    </button>
                </div>
            `).join('');
        }
        
        // Фильтрация товаров
        function filterProducts() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const filteredProducts = products.filter(product => 
                product.title.toLowerCase().includes(searchTerm) ||
                (product.description && product.description.toLowerCase().includes(searchTerm))
            );
            
            const container = document.getElementById('productsContainer');
            if (filteredProducts.length === 0) {
                container.innerHTML = '<div class="loading">Товары не найдены</div>';
                return;
            }
            
            container.innerHTML = filteredProducts.map(product => `
                <div class="product-card">
                    <div class="product-title">${product.title}</div>
                    ${product.description ? `<div class="product-description">${product.description}</div>` : ''}
                    <div class="product-price">${product.price.toLocaleString()} ₽</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        🛒 В корзину
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
        
        // Удаление из корзины
        function removeFromCart(productId) {
            cart = cart.filter(item => item.product_id !== productId);
            updateCartUI();
        }
        
        // Обновление количества
        function updateQuantity(productId, quantity) {
            if (quantity <= 0) {
                removeFromCart(productId);
                return;
            }
            
            const item = cart.find(item => item.product_id === productId);
            if (item) {
                item.quantity = quantity;
                updateCartUI();
            }
        }
        
        // Обновление интерфейса корзины
        function updateCartUI() {
            const cartItems = document.getElementById('cartItems');
            const cartTotal = document.getElementById('cartTotal');
            const checkoutBtn = document.getElementById('checkoutBtn');
            
            if (cart.length === 0) {
                cartItems.innerHTML = '<div style="text-align: center; color: #aaaaaa; padding: 20px;">Корзина пуста</div>';
                cartTotal.innerHTML = 'Итого: 0 ₽';
                checkoutBtn.classList.add('hidden');
                return;
            }
            
            cartItems.innerHTML = cart.map(item => `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <div class="cart-item-title">${item.product.title}</div>
                        <div class="cart-item-price">${item.product.price.toLocaleString()} ₽</div>
                    </div>
                    <div class="quantity-controls">
                        <button class="quantity-btn" onclick="updateQuantity(${item.product_id}, ${item.quantity - 1})">-</button>
                        <input type="number" class="quantity-input" value="${item.quantity}" min="1" 
                               onchange="updateQuantity(${item.product_id}, parseInt(this.value))">
                        <button class="quantity-btn" onclick="updateQuantity(${item.product_id}, ${item.quantity + 1})">+</button>
                        <button class="remove-btn" onclick="removeFromCart(${item.product_id})">🗑️</button>
                    </div>
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
        
        // Добавление товара
        async function addProduct(event) {
            event.preventDefault();
            
            const title = document.getElementById('productTitle').value;
            const price = parseInt(document.getElementById('productPrice').value);
            const description = document.getElementById('productDescription').value;
            const category = document.getElementById('productCategory').value;
            
            if (!title || !price || price <= 0) {
                showAdminMessage('Пожалуйста, заполните все обязательные поля!', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/add-product', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: title,
                        price: price,
                        description: description,
                        category: category
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAdminMessage('Товар добавлен успешно!', 'success');
                    document.getElementById('adminForm').reset();
                    await loadProducts();
                } else {
                    showAdminMessage(result.message || 'Ошибка добавления товара', 'error');
                }
            } catch (error) {
                console.error('Error adding product:', error);
                showAdminMessage('Ошибка добавления товара', 'error');
            }
        }
        
        // Показать сообщение админу
        function showAdminMessage(message, type) {
            const messageDiv = document.getElementById('adminMessage');
            messageDiv.innerHTML = `<div class="${type}-message">${message}</div>`;
            
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 3000);
        }
        
        // Переключение табов
        function showTab(tabName) {
            // Скрыть все табы
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Показать выбранный таб
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Обновить данные для определенных табов
            if (tabName === 'cart') {
                updateCartUI();
            }
        }
        
        // Обработчики событий
        document.getElementById('checkoutBtn').addEventListener('click', checkout);
        document.getElementById('adminForm').addEventListener('submit', addProduct);
        
        // Запуск
        loadProducts();
    </script>
</body>
</html>'''

def start_web_server():
    """Запуск веб-сервера"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), DarkWebAppHandler)
        print(f"🌐 Веб-сервер запущен на http://0.0.0.0:{PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

def main():
    """Главная функция"""
    print("🌙 ЗАПУСК DARK TELEGRAM SHOP BOT")
    print("=" * 40)
    
    bot = DarkShopBot()
    
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

#!/usr/bin/env python3
"""
🌙 DARK SHOP BOT V2 - ИСПРАВЛЕННЫЙ ДИЗАЙН
==========================================
Версия с темно-синими кнопками, нижней навигацией и компактными товарами
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
                ('iPhone 15 Pro', 99999, 'Новейший смартфон Apple', 'electronics', ''),
                ('MacBook Air M3', 129999, 'Мощный ноутбук', 'electronics', ''),
                ('Nike Air Max', 8999, 'Спортивные кроссовки', 'clothing', ''),
                ('Кофе Starbucks', 299, 'Премиальный кофе', 'food', ''),
                ('Книга Python', 1999, 'Программирование', 'books', ''),
                ('Samsung Galaxy', 89999, 'Флагманский смартфон', 'electronics', ''),
                ('Adidas Boost', 12999, 'Беговые кроссовки', 'clothing', ''),
                ('Чай Earl Grey', 599, 'Элитный чай', 'food', ''),
                ('iPad Pro', 79999, 'Планшет Apple', 'electronics', ''),
                ('Nike Dunk', 7999, 'Классические кроссовки', 'clothing', ''),
                ('Кофе Lavazza', 399, 'Итальянский кофе', 'food', ''),
                ('Книга JavaScript', 2499, 'Веб-разработка', 'books', '')
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
            
            html_content = self.get_dark_page_v2()
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
    
    def get_dark_page_v2(self):
        """Главная страница WebApp с исправленным дизайном"""
        return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛍️ Dark Shop - Telegram Mini App</title>
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
            padding-bottom: 100px; /* Место для нижней навигации */
        }
        
        .header {
            text-align: center;
            margin-bottom: 24px;
            padding: 20px;
            background: #2d2d2d;
            border-radius: 12px;
            border: 1px solid #333;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
            color: #ffffff;
        }
        
        .header p {
            color: #cccccc;
            font-size: 14px;
        }
        
        .search-box {
            position: relative;
            margin-bottom: 16px;
        }
        
        .search-box input {
            width: 100%;
            background: #2d2d2d;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px 16px 12px 40px;
            color: #ffffff;
            font-size: 16px;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #1e40af;
        }
        
        .search-box::before {
            content: '🔍';
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 16px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: 1fr 1fr; /* 2 колонки */
            gap: 12px;
            margin-bottom: 24px;
        }
        
        .product-card {
            background: #2d2d2d;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .product-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
            border-color: #1e40af;
        }
        
        .product-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
            color: #ffffff;
            line-height: 1.3;
        }
        
        .product-description {
            color: #aaaaaa;
            font-size: 11px;
            margin-bottom: 8px;
            line-height: 1.2;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .product-price {
            font-size: 16px;
            font-weight: 700;
            color: #3b82f6;
            margin-bottom: 8px;
        }
        
        .add-to-cart-btn {
            background: #1e40af;
            color: #ffffff;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .add-to-cart-btn:hover {
            background: #1d4ed8;
            transform: scale(1.02);
        }
        
        .cart-section {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        
        .cart-section h2 {
            color: #3b82f6;
            margin-bottom: 16px;
            font-size: 18px;
        }
        
        .checkout-btn {
            background: #1e40af;
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 16px;
            transition: all 0.3s ease;
        }
        
        .checkout-btn:hover:not(.hidden) {
            background: #1d4ed8;
            transform: scale(1.02);
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
            background: #2d2d2d;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        
        .admin-section h2 {
            color: #3b82f6;
            margin-bottom: 16px;
            font-size: 18px;
        }
        
        .admin-form {
            display: grid;
            gap: 12px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .form-group label {
            color: #3b82f6;
            font-weight: 600;
            font-size: 14px;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 10px;
            color: #ffffff;
            font-size: 14px;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #1e40af;
        }
        
        .add-product-btn {
            background: #1e40af;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .add-product-btn:hover {
            background: #1d4ed8;
            transform: scale(1.02);
        }
        
        .success-message {
            background: #1e40af;
            color: white;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 16px;
            text-align: center;
            font-weight: 600;
        }
        
        .error-message {
            background: #dc2626;
            color: white;
            padding: 12px;
            border-radius: 6px;
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
            border-radius: 6px;
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
            font-size: 14px;
        }
        
        .cart-item-price {
            color: #3b82f6;
            font-weight: 600;
            font-size: 14px;
        }
        
        .quantity-controls {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .quantity-btn {
            background: #333;
            color: #ffffff;
            border: none;
            width: 28px;
            height: 28px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 12px;
        }
        
        .quantity-btn:hover {
            background: #1e40af;
        }
        
        .quantity-input {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 4px;
            color: #ffffff;
            width: 40px;
            text-align: center;
            font-size: 12px;
        }
        
        .remove-btn {
            background: #dc2626;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 10px;
            margin-left: 6px;
            transition: all 0.3s ease;
        }
        
        .remove-btn:hover {
            background: #b91c1c;
        }
        
        /* Нижняя навигация */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #2d2d2d;
            border-top: 1px solid #333;
            padding: 8px 16px;
            display: flex;
            justify-content: space-around;
            z-index: 1000;
        }
        
        .nav-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            background: transparent;
            border: none;
            color: #aaaaaa;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.3s ease;
            min-width: 60px;
        }
        
        .nav-btn.active {
            color: #3b82f6;
            background: rgba(30, 64, 175, 0.1);
        }
        
        .nav-btn i {
            font-size: 18px;
        }
        
        .nav-btn span {
            font-size: 10px;
            font-weight: 600;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .cart-count {
            position: absolute;
            top: -2px;
            right: -2px;
            background: #dc2626;
            color: white;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 10px;
            min-width: 18px;
            text-align: center;
            font-weight: 600;
        }
        
        @media (max-width: 768px) {
            .products-grid {
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .product-card {
                padding: 8px;
            }
            
            .product-title {
                font-size: 12px;
            }
            
            .product-description {
                font-size: 10px;
            }
            
            .product-price {
                font-size: 14px;
            }
            
            .add-to-cart-btn {
                padding: 6px 8px;
                font-size: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛍️ Dark Shop</h1>
        <p>Добро пожаловать в наш магазин!</p>
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
            <div id="cartTotal" style="font-size: 16px; font-weight: 600; color: #3b82f6; margin-top: 16px;">Итого: 0 ₽</div>
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

    <!-- Нижняя навигация -->
    <div class="bottom-nav">
        <button class="nav-btn active" onclick="showTab('catalog')">
            <span>📦</span>
            <span>Каталог</span>
        </button>
        <button class="nav-btn" onclick="showTab('cart')">
            <span>🛒</span>
            <span>Корзина</span>
            <span class="cart-count" id="cartCount">0</span>
        </button>
        <button class="nav-btn" onclick="showTab('admin')">
            <span>⚙️</span>
            <span>Админ</span>
        </button>
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
                        В корзину
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
            const cartCount = document.getElementById('cartCount');
            
            // Обновляем счетчик в навигации
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.textContent = totalItems;
            cartCount.style.display = totalItems > 0 ? 'block' : 'none';
            
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
            
            document.querySelectorAll('.nav-btn').forEach(btn => {
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
    print("🌙 ЗАПУСК DARK SHOP BOT V2")
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

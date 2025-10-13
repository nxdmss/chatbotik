#!/usr/bin/env python3
"""
🌙 DARK SHOP BOT V3 - С ФОТОГРАФИЯМИ И РЕДАКТИРОВАНИЕМ
========================================================
Версия с загрузкой фотографий и редактированием товаров
"""

import os
import json
import sqlite3
import base64
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
try:
    from PIL import Image
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL не установлен, изображения будут сохраняться без сжатия")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
PORT = int(os.getenv('PORT', 8000))
WEBAPP_URL = f'http://localhost:{PORT}'
UPLOADS_DIR = 'uploads'

# Создаем папку для загрузок
os.makedirs(UPLOADS_DIR, exist_ok=True)

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
                ('iPhone 15 Pro', 99999, ''),
                ('MacBook Air M3', 129999, ''),
                ('Nike Air Max', 8999, ''),
                ('Кофе Starbucks', 299, ''),
                ('Книга Python', 1999, ''),
                ('Samsung Galaxy', 89999, ''),
                ('Adidas Boost', 12999, ''),
                ('Чай Earl Grey', 599, ''),
                ('iPad Pro', 79999, ''),
                ('Nike Dunk', 7999, ''),
                ('Кофе Lavazza', 399, ''),
                ('Книга JavaScript', 2499, '')
            ]
            
            for title, price, image_url in test_products:
                cursor.execute('''
                    INSERT INTO products (title, price, image_url)
                    VALUES (?, ?, ?)
                ''', (title, price, image_url))
            
            print("✅ Добавлены тестовые товары без изображений")
        
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
    
    def save_image(self, base64_data):
        """Простое сохранение изображения из base64"""
        try:
            print(f"🔍 save_image вызвана с данными длиной: {len(base64_data) if base64_data else 0}")
            
            if not base64_data or base64_data.strip() == '':
                print("⚠️ Пустые данные изображения - возвращаем пустую строку")
                return ''
            
            # Проверяем что это действительно base64
            if len(base64_data) < 100:
                print(f"⚠️ Слишком короткие данные: {base64_data[:50]}...")
                return ''
            
            print(f"📸 Получены данные изображения, длина: {len(base64_data)}")
            
            # Простая обработка - убираем заголовок если есть
            if base64_data.startswith('data:'):
                # Находим запятую и берем только base64 данные
                if ',' in base64_data:
                    base64_data = base64_data.split(',', 1)[1]
                    print("📸 Убран заголовок data:")
            
            # Декодируем base64
            try:
                image_data = base64.b64decode(base64_data)
                print(f"✅ Base64 декодирован, размер: {len(image_data)} байт")
            except Exception as decode_error:
                print(f"❌ Ошибка декодирования base64: {decode_error}")
                return ''
            
            # Генерируем простое имя файла
            filename = f"img_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(UPLOADS_DIR, filename)
            
            # Проверяем что папка существует
            if not os.path.exists(UPLOADS_DIR):
                os.makedirs(UPLOADS_DIR)
                print(f"📁 Создана папка: {UPLOADS_DIR}")
            
            # Сохраняем файл
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Проверяем что файл создался
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                result_url = f"/uploads/{filename}"
                print(f"✅ Изображение сохранено: {filename} ({file_size} байт)")
                print(f"📁 Полный путь: {filepath}")
                print(f"🌐 URL для базы: {result_url}")
                return result_url
            else:
                print(f"❌ Файл не создался: {filepath}")
                return ''
            
        except Exception as e:
            print(f"❌ Ошибка сохранения изображения: {e}")
            import traceback
            traceback.print_exc()
            return ''
    
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
            
            html_content = self.get_dark_page_v3()
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
                        'image_url': product[3] or '',
                        'created_at': product[4]
                    })
                
                print(f"📦 Отправляем {len(products_data)} товаров")
                for p in products_data:
                    print(f"  - {p['title']}: изображение = {p['image_url'] or 'НЕТ'}")
                
                self.wfile.write(json.dumps(products_data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"❌ Ошибка получения товаров: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
        
        elif self.path == '/test-image':
            # Тестовый эндпоинт для проверки изображений
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            test_html = '''
            <!DOCTYPE html>
            <html>
            <head><title>Тест изображений</title></head>
            <body>
                <h1>Тест изображений</h1>
                <p>Папка uploads:</p>
                <ul>
            '''
            
            if os.path.exists(UPLOADS_DIR):
                files = os.listdir(UPLOADS_DIR)
                for file in files:
                    test_html += f'<li><a href="/uploads/{file}">{file}</a></li>'
                    test_html += f'<li><img src="/uploads/{file}" style="width:100px; height:100px; object-fit:cover; border:1px solid #ccc; margin:5px;"></li>'
            else:
                test_html += '<li>Папка uploads не существует</li>'
            
            test_html += '''
                </ul>
                <p><a href="/">Вернуться к магазину</a></p>
            </body>
            </html>
            '''
            
            self.wfile.write(test_html.encode('utf-8'))
        
        elif self.path.startswith('/uploads/'):
            # Простая обработка изображений
            filename = self.path[9:]  # Убираем '/uploads/'
            filepath = os.path.join(UPLOADS_DIR, filename)
            
            print(f"🖼️ Запрос изображения: {self.path}")
            print(f"📁 Ищем файл: {filepath}")
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ Файл найден, размер: {file_size} байт")
                
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'public, max-age=3600')
                self.end_headers()
                
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                        self.wfile.write(content)
                    print(f"✅ Изображение отправлено: {filename} ({len(content)} байт)")
                except Exception as e:
                    print(f"❌ Ошибка чтения файла: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'Server Error')
            else:
                print(f"❌ Файл не найден: {filepath}")
                # Показываем содержимое папки для отладки
                if os.path.exists(UPLOADS_DIR):
                    files = os.listdir(UPLOADS_DIR)
                    print(f"📁 Файлы в папке uploads: {files}")
                else:
                    print(f"📁 Папка uploads не существует!")
                
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Image not found')
        
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
                image_data = data.get('image', '')
                
                print(f"📝 Получены данные: title='{title}', price={price}, image_data_len={len(image_data)}")
                
                if title and price > 0:
                    # Сохраняем изображение
                    bot = DarkShopBot()
                    image_url = bot.save_image(image_data)
                    print(f"🖼️ URL изображения: {image_url}")
                    
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO products (title, price, image_url)
                        VALUES (?, ?, ?)
                    ''', (title, price, image_url))
                    conn.commit()
                    conn.close()
                    
                    print(f"✅ Товар добавлен: {title} - {price} ₽, изображение: {image_url}")
                    response = {'success': True, 'message': 'Товар добавлен успешно!'}
                else:
                    print(f"❌ Неверные данные: title='{title}', price={price}")
                    response = {'success': False, 'message': 'Неверные данные товара'}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Ошибка добавления товара: {e}")
                response = {'success': False, 'message': f'Ошибка добавления товара: {str(e)}'}
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        elif self.path.startswith('/api/update-product/'):
            product_id = self.path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                title = data.get('title', '')
                price = int(data.get('price', 0))
                image_data = data.get('image', '')
                
                print(f"🔄 Обновление товара ID {product_id}: title='{title}', price={price}, image_len={len(image_data) if image_data else 0}")
                
                if title and price > 0:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    
                    # Если есть новое изображение, сохраняем его
                    if image_data and image_data.strip():
                        bot = DarkShopBot()
                        image_url = bot.save_image(image_data)
                        print(f"🖼️ Новое изображение сохранено: {image_url}")
                        cursor.execute('''
                            UPDATE products 
                            SET title = ?, price = ?, image_url = ?
                            WHERE id = ?
                        ''', (title, price, image_url, product_id))
                        print(f"✅ Товар обновлен с новым изображением: {title} -> {image_url}")
                    else:
                        print("📝 Обновление без изменения изображения")
                        cursor.execute('''
                            UPDATE products 
                            SET title = ?, price = ?
                            WHERE id = ?
                        ''', (title, price, product_id))
                        print(f"✅ Товар обновлен без изображения: {title}")
                    
                    rows_affected = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    print(f"📊 Обновлено строк: {rows_affected}")
                    
                    response = {'success': True, 'message': 'Товар обновлен успешно!'}
                else:
                    print(f"❌ Неверные данные: title='{title}', price={price}")
                    response = {'success': False, 'message': 'Неверные данные товара'}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Ошибка обновления товара: {e}")
                import traceback
                traceback.print_exc()
                response = {'success': False, 'message': 'Ошибка обновления товара'}
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        elif self.path.startswith('/api/delete-product/'):
            product_id = self.path.split('/')[-1]
            
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
                conn.commit()
                conn.close()
                
                response = {'success': True, 'message': 'Товар удален успешно!'}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                print(f"❌ Ошибка удаления товара: {e}")
                response = {'success': False, 'message': 'Ошибка удаления товара'}
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def get_dark_page_v3(self):
        """Главная страница WebApp с фотографиями и редактированием"""
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
            padding-bottom: 100px;
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
            grid-template-columns: 1fr 1fr;
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
        
        .product-image {
            width: 100%;
            height: 80px;
            background: #1a1a1a;
            border-radius: 6px;
            margin-bottom: 8px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 24px;
            position: relative;
        }
        
        .product-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            transition: transform 0.3s ease;
        }
        
        .product-image img:hover {
            transform: scale(1.05);
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
        
        .file-input-wrapper {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        
        .file-input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .file-input-button {
            background: #1e40af;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .file-input-button:hover {
            background: #1d4ed8;
        }
        
        .image-preview {
            width: 100%;
            height: 120px;
            background: #1a1a1a;
            border-radius: 6px;
            margin-top: 8px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 18px;
        }
        
        .image-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
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
        
        /* Админ панель - список товаров */
        .admin-products-list {
            margin-bottom: 20px;
        }
        
        .admin-product-item {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .admin-product-image {
            width: 60px;
            height: 60px;
            background: #2d2d2d;
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 18px;
        }
        
        .admin-product-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .admin-product-info {
            flex: 1;
        }
        
        .admin-product-title {
            color: #ffffff;
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 14px;
        }
        
        .admin-product-price {
            color: #3b82f6;
            font-weight: 600;
            font-size: 14px;
        }
        
        .admin-product-actions {
            display: flex;
            gap: 8px;
        }
        
        .edit-btn {
            background: #1e40af;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }
        
        .edit-btn:hover {
            background: #1d4ed8;
        }
        
        .delete-btn {
            background: #dc2626;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
        }
        
        .delete-btn:hover {
            background: #b91c1c;
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
            
            <!-- Список товаров -->
            <div class="admin-products-list" id="adminProductsList">
                <div class="loading">Загрузка товаров...</div>
            </div>
            
            <!-- Форма добавления/редактирования -->
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
                    <label for="productImage">Фотография</label>
                    <div class="file-input-wrapper">
                        <input type="file" id="productImage" class="file-input" accept="image/*" onchange="handleImageUpload(this)">
                        <button type="button" class="file-input-button">📷 Выбрать фото</button>
                    </div>
                    <div class="image-preview" id="imagePreview">Выберите изображение</div>
                </div>
                <button type="submit" class="add-product-btn" id="submitBtn">➕ Добавить товар</button>
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
        
        // Проверяем что мы в Telegram WebApp
        const isTelegramWebApp = typeof window.Telegram !== 'undefined' && window.Telegram.WebApp;
        console.log('📱 Telegram WebApp:', isTelegramWebApp ? 'ДА' : 'НЕТ');
        
        if (isTelegramWebApp) {
            console.log('🤖 Telegram WebApp данные:', {
                platform: tg.platform,
                version: tg.version,
                colorScheme: tg.colorScheme,
                isExpanded: tg.isExpanded
            });
        }
        
        let products = [];
        let cart = [];
        let currentEditingProduct = null;
        let selectedImageData = '';
        
        // Загрузка товаров
        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                products = await response.json();
                renderProducts();
                if (document.getElementById('adminProductsList')) {
                    renderAdminProducts();
                }
            } catch (error) {
                document.getElementById('productsContainer').innerHTML = 
                    '<div class="loading">Ошибка загрузки товаров</div>';
                console.error('Error loading products:', error);
            }
        }
        
        // Отображение товаров в каталоге
        function renderProducts() {
            const container = document.getElementById('productsContainer');
            container.className = 'products-grid';
            
            if (products.length === 0) {
                container.innerHTML = '<div class="loading">Товары не найдены</div>';
                return;
            }
            
            console.log('🛍️ Отображение товаров:', products.length);
            products.forEach(product => {
                console.log(`📦 Товар: ${product.title}, изображение: ${product.image_url || 'нет'}`);
                if (product.image_url && product.image_url.startsWith('/uploads/')) {
                    console.log(`🖼️ Полный URL изображения: ${window.location.origin}${product.image_url}`);
                }
            });
            
            container.innerHTML = products.map(product => `
                <div class="product-card">
                    <div class="product-image">
                        ${product.image_url ? 
                            `<img src="${window.location.origin}${product.image_url}" alt="${product.title}" 
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onload="console.log('✅ Изображение загружено в Telegram WebApp:', this.src)"
                                 onerror="console.error('❌ Ошибка загрузки в Telegram WebApp:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div style="display:none; color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>` : 
                            '<div style="color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>'
                        }
                    </div>
                    <div class="product-title">${product.title}</div>
                    <div class="product-price">${product.price.toLocaleString()} ₽</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        В корзину
                    </button>
                </div>
            `).join('');
        }
        
        // Отображение товаров в админ панели
        function renderAdminProducts() {
            const container = document.getElementById('adminProductsList');
            
            if (products.length === 0) {
                container.innerHTML = '<div class="loading">Товары не найдены</div>';
                return;
            }
            
            container.innerHTML = products.map(product => `
                <div class="admin-product-item">
                    <div class="admin-product-image">
                        ${product.image_url ? 
                            `<img src="${product.image_url}" alt="${product.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div style="display:none;">📷</div>` : 
                            '📷'
                        }
                    </div>
                    <div class="admin-product-info">
                        <div class="admin-product-title">${product.title}</div>
                        <div class="admin-product-price">${product.price.toLocaleString()} ₽</div>
                    </div>
                    <div class="admin-product-actions">
                        <button class="edit-btn" onclick="editProduct(${product.id})">✏️</button>
                        <button class="delete-btn" onclick="deleteProduct(${product.id})">🗑️</button>
                    </div>
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
                    <div class="product-image">
                        ${product.image_url ? 
                            `<img src="${window.location.origin}${product.image_url}" alt="${product.title}" 
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onload="console.log('✅ Изображение загружено в Telegram WebApp:', this.src)"
                                 onerror="console.error('❌ Ошибка загрузки в Telegram WebApp:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div style="display:none; color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>` : 
                            '<div style="color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>'
                        }
                    </div>
                    <div class="product-title">${product.title}</div>
                    <div class="product-price">${product.price.toLocaleString()} ₽</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        В корзину
                    </button>
                </div>
            `).join('');
        }
        
        // Простая обработка загрузки изображения
        function handleImageUpload(input) {
            console.log('📸 handleImageUpload вызвана');
            
            const file = input.files[0];
            if (file) {
                console.log('📸 Выбран файл:', {
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    lastModified: file.lastModified
                });
                
                // Проверяем размер файла (максимум 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    console.log('❌ Файл слишком большой:', file.size, 'байт');
                    alert('Файл слишком большой! Максимум 5MB.');
                    input.value = '';
                    return;
                }
                
                console.log('📸 Начинаем чтение файла...');
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    selectedImageData = e.target.result;
                    console.log('📸 Base64 готов:', {
                        length: selectedImageData.length,
                        startsWith: selectedImageData.substring(0, 50) + '...',
                        type: selectedImageData.split(',')[0]
                    });
                    
                    // Показываем превью
                    const preview = document.getElementById('imagePreview');
                    preview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 100%; max-height: 120px; object-fit: cover; border-radius: 4px;">`;
                    console.log('📸 Превью обновлено');
                };
                
                reader.onerror = function(error) {
                    console.error('❌ Ошибка чтения файла:', error);
                    alert('Ошибка чтения файла!');
                };
                
                reader.onprogress = function(e) {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        console.log('📸 Прогресс чтения:', percentComplete.toFixed(2) + '%');
                    }
                };
                
                reader.readAsDataURL(file);
            } else {
                console.log('📸 Файл не выбран, очищаем данные');
                selectedImageData = '';
                document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
            }
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
        
        // Добавление/обновление товара
        async function addProduct(event) {
            event.preventDefault();
            
            console.log('🚀 Функция addProduct вызвана');
            
            const title = document.getElementById('productTitle').value;
            const price = parseInt(document.getElementById('productPrice').value);
            
            console.log('📝 Данные формы:', { 
                title: title, 
                price: price, 
                imageData: selectedImageData ? `есть (${selectedImageData.length} символов)` : 'нет',
                currentEditingProduct: currentEditingProduct
            });
            
            if (!title || !price || price <= 0) {
                console.log('❌ Неверные данные формы');
                showAdminMessage('Пожалуйста, заполните все обязательные поля!', 'error');
                return;
            }
            
            try {
                const url = currentEditingProduct ? 
                    `/api/update-product/${currentEditingProduct}` : 
                    '/api/add-product';
                
                console.log('🌐 URL запроса:', url);
                
                const requestData = {
                    title: title,
                    price: price,
                    image: selectedImageData
                };
                
                console.log('📤 Отправляем данные:', {
                    title: title,
                    price: price,
                    imageLength: selectedImageData ? selectedImageData.length : 0,
                    fullRequestData: requestData
                });
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                console.log('📡 Ответ сервера получен, статус:', response.status);
                
                const result = await response.json();
                
                console.log('📥 Ответ сервера:', result);
                
                if (result.success) {
                    console.log('✅ Успешно сохранено');
                    showAdminMessage(
                        currentEditingProduct ? 'Товар обновлен успешно!' : 'Товар добавлен успешно!', 
                        'success'
                    );
                    resetForm();
                    await loadProducts();
                } else {
                    console.log('❌ Ошибка сервера:', result.message);
                    showAdminMessage(result.message || 'Ошибка сохранения товара', 'error');
                }
            } catch (error) {
                console.error('❌ Ошибка fetch:', error);
                showAdminMessage('Ошибка соединения с сервером: ' + error.message, 'error');
            }
        }
        
        // Редактирование товара
        function editProduct(productId) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            currentEditingProduct = productId;
            
            document.getElementById('productTitle').value = product.title;
            document.getElementById('productPrice').value = product.price;
            
            if (product.image_url) {
                selectedImageData = '';
                document.getElementById('imagePreview').innerHTML = `<img src="${product.image_url}" alt="${product.title}">`;
            } else {
                selectedImageData = '';
                document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
            }
            
            document.getElementById('submitBtn').textContent = '💾 Сохранить изменения';
            
            // Прокручиваем к форме
            document.getElementById('adminForm').scrollIntoView({ behavior: 'smooth' });
        }
        
        // Удаление товара
        async function deleteProduct(productId) {
            if (!confirm('Вы уверены, что хотите удалить этот товар?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/delete-product/${productId}`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAdminMessage('Товар удален успешно!', 'success');
                    await loadProducts();
                } else {
                    showAdminMessage('Ошибка удаления товара', 'error');
                }
            } catch (error) {
                console.error('Error deleting product:', error);
                showAdminMessage('Ошибка удаления товара', 'error');
            }
        }
        
        // Сброс формы
        function resetForm() {
            currentEditingProduct = null;
            selectedImageData = '';
            document.getElementById('adminForm').reset();
            document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
            document.getElementById('submitBtn').textContent = '➕ Добавить товар';
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
            } else if (tabName === 'admin') {
                renderAdminProducts();
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
    print("🌙 ЗАПУСК DARK SHOP BOT V3")
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

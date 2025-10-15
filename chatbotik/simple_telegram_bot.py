#!/usr/bin/env python3
"""
🛍️ ОСНОВНОЙ TELEGRAM BOT - ИНТЕРНЕТ-МАГАЗИН
============================================
Полнофункциональный интернет-магазин с Telegram интеграцией
- Каталог товаров с фотографиями
- Корзина покупок
- Админ панель для управления товарами
- Темная тема и современный интерфейс
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
                description TEXT DEFAULT '',
                price INTEGER NOT NULL,
                image_url TEXT DEFAULT '',
                gallery_images TEXT DEFAULT '',
                sizes TEXT DEFAULT '',
                category TEXT DEFAULT '',
                brand TEXT DEFAULT '',
                color TEXT DEFAULT '',
                material TEXT DEFAULT '',
                weight TEXT DEFAULT '',
                dimensions TEXT DEFAULT '',
                in_stock INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Добавляем новые поля если их нет (миграция)
        new_fields = [
            ('description', 'TEXT DEFAULT ""'),
            ('gallery_images', 'TEXT DEFAULT ""'),
            ('sizes', 'TEXT DEFAULT ""'),
            ('category', 'TEXT DEFAULT ""'),
            ('brand', 'TEXT DEFAULT ""'),
            ('color', 'TEXT DEFAULT ""'),
            ('material', 'TEXT DEFAULT ""'),
            ('weight', 'TEXT DEFAULT ""'),
            ('dimensions', 'TEXT DEFAULT ""'),
            ('in_stock', 'INTEGER DEFAULT 1')
        ]
        
        for field_name, field_type in new_fields:
            try:
                cursor.execute(f'ALTER TABLE products ADD COLUMN {field_name} {field_type}')
                print(f"✅ Добавлено поле {field_name} в таблицу products")
            except sqlite3.OperationalError:
                # Поле уже существует
                pass
        
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
            
        elif self.path.startswith('/product/'):
            # Страница товара
            product_id = self.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.get_product_page(product_id)
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
                        'image_url': (product[3] if len(product) > 3 else '') or '',
                        'description': product[5] if len(product) > 5 else '',
                        'sizes': (product[7] if len(product) > 7 else '') or '',
                        'category': (product[8] if len(product) > 8 else '') or '',
                        'brand': (product[9] if len(product) > 9 else '') or '',
                        'color': (product[10] if len(product) > 10 else '') or '',
                        'material': (product[11] if len(product) > 11 else '') or '',
                        'weight': (product[12] if len(product) > 12 else '') or '',
                        'dimensions': (product[13] if len(product) > 13 else '') or '',
                        'in_stock': (product[14] if len(product) > 14 else 1),
                        'created_at': product[4] if len(product) > 4 else ''
                    })
                
                print(f"📦 Отправляем {len(products_data)} товаров")
                for p in products_data:
                    print(f"  - {p['title']}: {p['price']} ₽")
                
                self.wfile.write(json.dumps(products_data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"❌ Ошибка получения товаров: {e}")
                self.wfile.write(json.dumps([]).encode('utf-8'))
        
        elif self.path.startswith('/api/product/'):
            # API для получения детальной информации о товаре
            product_id = self.path.split('/')[-1]
            
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
                product = cursor.fetchone()
                conn.close()
                
                if product:
                    # Парсим галерею изображений (JSON строка)
                    gallery_images = []
                    if len(product) > 6 and product[6]:  # gallery_images
                        try:
                            gallery_images = json.loads(product[6]) if product[6] else []
                        except:
                            gallery_images = []
                    
                    product_data = {
                        'id': product[0],
                        'title': product[1],
                        'description': product[5] if len(product) > 5 else '',
                        'price': product[2],
                        'image_url': (product[3] if len(product) > 3 else '') or '',
                        'gallery_images': gallery_images,
                        'sizes': (product[7] if len(product) > 7 else '') or '',
                        'category': (product[8] if len(product) > 8 else '') or '',
                        'brand': (product[9] if len(product) > 9 else '') or '',
                        'color': (product[10] if len(product) > 10 else '') or '',
                        'material': (product[11] if len(product) > 11 else '') or '',
                        'weight': (product[12] if len(product) > 12 else '') or '',
                        'dimensions': (product[13] if len(product) > 13 else '') or '',
                        'in_stock': (product[14] if len(product) > 14 else 1),
                        'created_at': product[4] if len(product) > 4 else ''
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(product_data, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Product not found'}).encode('utf-8'))
                    
            except Exception as e:
                print(f"❌ Ошибка получения товара {product_id}: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Internal server error'}).encode('utf-8'))
        
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
                description = data.get('description', '')
                price = int(data.get('price', 0))
                category = data.get('category', '')
                brand = data.get('brand', '')
                color = data.get('color', '')
                material = data.get('material', '')
                weight = data.get('weight', '')
                dimensions = data.get('dimensions', '')
                sizes = data.get('sizes', '')
                image_data = data.get('image', '')
                gallery_images_data = data.get('gallery_images', [])
                
                print(f"📝 Получены данные: title='{title}', price={price}, sizes='{sizes}', image_data_len={len(image_data)}, gallery_len={len(gallery_images_data)}")
                
                if title and price > 0:
                    # Сохраняем основное изображение
                    bot = DarkShopBot()
                    image_url = bot.save_image(image_data)
                    print(f"🖼️ URL основного изображения: {image_url}")
                    
                    # Сохраняем галерею изображений
                    gallery_urls = []
                    for gallery_image_data in gallery_images_data:
                        if gallery_image_data:
                            gallery_url = bot.save_image(gallery_image_data)
                            if gallery_url:
                                gallery_urls.append(gallery_url)
                    
                    gallery_images_json = json.dumps(gallery_urls)
                    print(f"🖼️ Галерея изображений: {len(gallery_urls)} фото")
                    
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO products (title, description, price, image_url, gallery_images, 
                                            category, brand, color, material, weight, dimensions, sizes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (title, description, price, image_url, gallery_images_json,
                          category, brand, color, material, weight, dimensions, sizes))
                    conn.commit()
                    conn.close()
                    
                    print(f"✅ Товар добавлен: {title} - {price} ₽, изображение: {image_url}, галерея: {len(gallery_urls)} фото")
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
                description = data.get('description', '')
                price = int(data.get('price', 0))
                category = data.get('category', '')
                brand = data.get('brand', '')
                color = data.get('color', '')
                material = data.get('material', '')
                weight = data.get('weight', '')
                dimensions = data.get('dimensions', '')
                sizes = data.get('sizes', '')
                image_data = data.get('image', '')
                gallery_images_data = data.get('gallery_images', [])
                
                print(f"🔄 Обновление товара ID {product_id}: title='{title}', price={price}, sizes='{sizes}', image_len={len(image_data) if image_data else 0}, gallery_len={len(gallery_images_data)}")
                
                if title and price > 0:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    
                    # Получаем текущие данные товара
                    cursor.execute('SELECT image_url, gallery_images FROM products WHERE id = ?', (product_id,))
                    current_product = cursor.fetchone()
                    current_image_url = current_product[0] if current_product else ''
                    current_gallery_images = current_product[1] if current_product else '[]'
                    
                    # Если есть новое основное изображение, сохраняем его
                    if image_data and image_data.strip():
                        bot = DarkShopBot()
                        image_url = bot.save_image(image_data)
                        print(f"🖼️ Новое основное изображение сохранено: {image_url}")
                    else:
                        image_url = current_image_url
                        print("📝 Основное изображение не изменено")
                    
                    # Если есть новая галерея, сохраняем её
                    if gallery_images_data:
                        bot = DarkShopBot()
                        gallery_urls = []
                        for gallery_image_data in gallery_images_data:
                            if gallery_image_data:
                                gallery_url = bot.save_image(gallery_image_data)
                                if gallery_url:
                                    gallery_urls.append(gallery_url)
                        gallery_images_json = json.dumps(gallery_urls)
                        print(f"🖼️ Новая галерея сохранена: {len(gallery_urls)} фото")
                    else:
                        gallery_images_json = current_gallery_images
                        print("📝 Галерея не изменена")
                    
                    # Обновляем товар
                    cursor.execute('''
                        UPDATE products 
                        SET title = ?, description = ?, price = ?, image_url = ?, gallery_images = ?,
                            category = ?, brand = ?, color = ?, material = ?, weight = ?, dimensions = ?, sizes = ?
                        WHERE id = ?
                    ''', (title, description, price, image_url, gallery_images_json,
                          category, brand, color, material, weight, dimensions, sizes, product_id))
                    
                    rows_affected = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    print(f"📊 Обновлено строк: {rows_affected}")
                    print(f"✅ Товар обновлен: {title}")
                    
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
    <title>LOOK & GO - Telegram Mini App</title>
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
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 24px;
            padding: 0 16px;
            justify-items: center;
        }
        
        .product-card {
            background: transparent;
            border: none;
            border-radius: 12px;
            transition: all 0.3s ease;
            position: relative;
            aspect-ratio: 0.85;
            min-height: 220px;
            overflow: hidden;
            margin: 8px;
            padding: 4px;
            box-sizing: border-box;
        }
        
        .product-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .product-image-full {
            width: 100%;
            height: 100%;
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .product-image-full img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            display: block;
            transition: transform 0.3s ease;
        }
        
        .product-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
            padding: 16px 12px 12px;
            color: white;
            border-radius: 0 0 12px 12px;
        }
        
        .product-info {
            margin-bottom: 8px;
        }
        
        .product-overlay .product-title {
            font-size: 12px;
            font-weight: 600;
            margin: 0 0 4px 0;
            color: #ffffff;
            line-height: 1.2;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
        }
        
        .product-overlay .product-price {
            font-size: 14px;
            font-weight: 700;
            margin: 0;
            color: #ffffff;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
        }
        
        .product-image-full img:hover {
            transform: scale(1.05);
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
        
        .product-overlay .product-buttons {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 8px;
        }
        
        .size-btn-thin, .add-to-cart-btn-thin {
            background: rgba(0, 0, 0, 0.7);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 10px;
            font-weight: 500;
            transition: all 0.3s ease;
            width: 100%;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
        }
        
        .size-btn-thin {
            background: rgba(45, 45, 45, 0.8);
            border-color: rgba(255, 255, 255, 0.4);
        }
        
        .size-btn-thin:hover {
            background: rgba(61, 61, 61, 0.9);
            border-color: #007bff;
            transform: translateY(-1px);
        }
        
        .size-btn-thin.required {
            background: rgba(0, 86, 179, 0.9);
            border-color: #0056b3;
            color: #ffffff;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .add-to-cart-btn-thin {
            background: rgba(0, 123, 255, 0.9);
            border-color: #007bff;
        }
        
        .add-to-cart-btn-thin:hover {
            background: rgba(0, 86, 179, 0.95);
            transform: translateY(-1px);
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
        
        .admin-products-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
            padding: 0 12px;
            justify-items: center;
        }
        
        /* Специальные стили для карточек в админ панели */
        .admin-products-grid .product-card {
            margin: 0;
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
        }
        
        .admin-products-grid .product-image-full {
            box-sizing: border-box;
        }
        
        /* Мобильная оптимизация для админ панели */
        @media (max-width: 480px) {
            .admin-products-grid {
                gap: 16px;
                padding: 0 16px;
                margin-bottom: 20px;
            }
            
            .admin-products-grid .product-card {
                padding: 8px;
                margin: 6px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }
            
            .admin-products-grid .product-image-full {
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 4px;
            }
            
            .admin-products-grid .product-image-full img {
                border-radius: 8px;
            }
            
            .product-overlay {
                padding: 12px 8px 8px;
                border-radius: 8px;
            }
            
            .product-overlay .product-title {
                font-size: 10px;
                margin-bottom: 2px;
                line-height: 1.1;
            }
            
            .product-overlay .product-price {
                font-size: 11px;
                margin-bottom: 3px;
            }
            
            .product-buttons {
                gap: 4px;
                margin-bottom: 2px;
            }
            
            .product-buttons button {
                padding: 6px 8px !important;
                font-size: 9px !important;
                margin-bottom: 3px !important;
                min-height: 30px !important;
                border-radius: 6px;
            }
        }
        
        .admin-search-box {
            margin-bottom: 20px;
        }
        
        .admin-search-box input {
            width: 100%;
            background: #1a1a1a;
            border: 1px solid #333;
            color: #fff;
            padding: 12px;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .admin-search-box input:focus {
            outline: none;
            border-color: #1e40af;
        }
        
        .admin-products-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
            padding: 0 8px;
            justify-items: center;
        }
        
        .admin-product-item {
            background: transparent;
            border: none;
            border-radius: 12px;
            padding: 0;
            transition: all 0.3s ease;
            position: relative;
            aspect-ratio: 1;
            overflow: hidden;
        }
        
        .admin-product-image {
            width: 100%;
            height: 100%;
            background: #2d2d2d;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 24px;
            position: relative;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .admin-product-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 12px;
            display: block;
            position: absolute;
            top: 0;
            left: 0;
        }
        
        .admin-product-info {
            padding: 8px 0;
            text-align: center;
        }
        
        .admin-product-title {
            color: #ffffff;
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 14px;
            line-height: 1.3;
        }
        
        .admin-product-price {
            color: #10b981;
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 8px;
        }
        
        .admin-product-actions {
            display: flex;
            gap: 8px;
            justify-content: center;
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
                gap: 12px;
                padding: 0 12px;
            }
            
            .product-card {
                padding: 6px;
                margin: 4px;
                min-height: 200px;
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
        
        /* Модальное окно для выбора размера */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(4px);
        }
        
        .modal-content {
            background: #2d2d2d;
            margin: 10% auto;
            padding: 0;
            border: 1px solid #333;
            border-radius: 12px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #333;
            background: #1a1a1a;
            border-radius: 12px 12px 0 0;
        }
        
        .modal-header h3 {
            margin: 0;
            color: #ffffff;
            font-size: 18px;
        }
        
        .close {
            color: #aaaaaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
        }
        
        .close:hover {
            color: #ffffff;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .modal-body p {
            margin-bottom: 16px;
            color: #cccccc;
        }
        
        .modal-body strong {
            color: #ffffff;
        }
        
        .size-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
            gap: 8px;
            margin-top: 16px;
        }
        
        .size-btn {
            background: #1a1a1a;
            border: 2px solid #333;
            border-radius: 8px;
            color: #ffffff;
            padding: 12px 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .size-btn:hover {
            background: #3d3d3d;
            border-color: #007bff;
            transform: translateY(-2px);
        }
        
        .size-btn:active {
            transform: translateY(0);
            background: #007bff;
            border-color: #007bff;
        }
        
        @media (max-width: 480px) {
            .modal-content {
                width: 95%;
                margin: 5% auto;
            }
            
            .size-grid {
                grid-template-columns: repeat(auto-fill, minmax(45px, 1fr));
                gap: 6px;
            }
            
            .size-btn {
                padding: 10px 6px;
                font-size: 12px;
                min-height: 40px;
            }
        }
        
        /* Шторка для выбора размера */
        .size-drawer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #2d2d2d;
            border-top: 1px solid #333;
            border-radius: 16px 16px 0 0;
            transform: translateY(100%);
            transition: transform 0.3s ease;
            z-index: 1000;
            max-height: 70vh;
            overflow-y: auto;
        }
        
        .size-drawer.open {
            transform: translateY(0);
        }
        
        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #333;
            background: #1a1a1a;
            border-radius: 16px 16px 0 0;
        }
        
        .drawer-header h3 {
            margin: 0;
            color: #ffffff;
            font-size: 18px;
        }
        
        .drawer-close {
            color: #aaaaaa;
            font-size: 24px;
            font-weight: bold;
            cursor: pointer;
            line-height: 1;
            padding: 4px;
        }
        
        .drawer-close:hover {
            color: #ffffff;
        }
        
        .drawer-content {
            padding: 20px;
        }
        
        .drawer-product-info {
            margin-bottom: 20px;
            text-align: center;
        }
        
        .drawer-product-info h4 {
            color: #ffffff;
            margin: 0 0 8px 0;
            font-size: 16px;
        }
        
        .drawer-product-info p {
            color: #cccccc;
            margin: 0;
            font-size: 14px;
        }
        
        .drawer-size-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .drawer-size-btn {
            background: #1a1a1a;
            border: 2px solid #333;
            border-radius: 8px;
            color: #ffffff;
            padding: 12px 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .drawer-size-btn:hover {
            background: #3d3d3d;
            border-color: #007bff;
        }
        
        .drawer-size-btn.selected {
            background: #007bff;
            border-color: #007bff;
        }
        
        .drawer-size-btn.out-of-stock {
            background: #333;
            border-color: #555;
            color: #888;
            cursor: not-allowed;
        }
        
        .drawer-actions {
            display: flex;
            gap: 12px;
            padding-top: 16px;
            border-top: 1px solid #333;
        }
        
        .drawer-btn {
            flex: 1;
            padding: 12px;
            border-radius: 8px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .drawer-btn-cancel {
            background: #333;
            color: #ffffff;
            border: 1px solid #555;
        }
        
        .drawer-btn-cancel:hover {
            background: #444;
        }
        
        .drawer-btn-add {
            background: #007bff;
            color: #ffffff;
            border: 1px solid #007bff;
        }
        
        .drawer-btn-add:hover {
            background: #0056b3;
        }
        
        .drawer-btn-add:disabled {
            background: #333;
            border-color: #555;
            color: #888;
            cursor: not-allowed;
        }
        
        @media (max-width: 480px) {
            .drawer-size-grid {
                grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
                gap: 8px;
            }
            
            .drawer-size-btn {
                min-height: 44px;
                font-size: 12px;
            }
        }
    </style>
</head>
<body>
        <div class="header">
            <h1>LOOK & GO</h1>
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
            
            <!-- Поиск товаров -->
            <div class="admin-search-box">
                <input type="text" id="adminSearchInput" placeholder="Поиск товаров..." onkeyup="filterAdminProducts()">
            </div>
            
            <!-- Список товаров -->
            <div class="admin-products-grid" id="adminProductsList">
                <div class="loading">Загрузка товаров...</div>
            </div>
            
            <!-- Форма добавления/редактирования -->
            <form class="admin-form" id="adminForm">
                <div class="form-group">
                    <label for="productTitle">Название товара</label>
                    <input type="text" id="productTitle" required>
                </div>
                <div class="form-group">
                    <label for="productDescription">Описание товара</label>
                    <textarea id="productDescription" rows="3" placeholder="Подробное описание товара..."></textarea>
                </div>
                <div class="form-group">
                    <label for="productPrice">Цена (₽)</label>
                    <input type="number" id="productPrice" min="1" required>
                </div>
                <div class="form-group">
                    <label for="productCategory">Категория</label>
                    <input type="text" id="productCategory" placeholder="Одежда, Обувь, Аксессуары...">
                </div>
                <div class="form-group">
                    <label for="productBrand">Бренд</label>
                    <input type="text" id="productBrand" placeholder="Nike, Adidas, Apple...">
                </div>
                <div class="form-group">
                    <label for="productColor">Цвет</label>
                    <input type="text" id="productColor" placeholder="Черный, Белый, Красный...">
                </div>
                <div class="form-group">
                    <label for="productMaterial">Материал</label>
                    <input type="text" id="productMaterial" placeholder="Хлопок, Кожа, Полиэстер...">
                </div>
                <div class="form-group">
                    <label for="productWeight">Вес</label>
                    <input type="text" id="productWeight" placeholder="500г, 1кг...">
                </div>
                <div class="form-group">
                    <label for="productDimensions">Размеры</label>
                    <input type="text" id="productDimensions" placeholder="30x20x10 см...">
                </div>
                <div class="form-group">
                    <label for="productSizes">Размерная сетка (через запятую)</label>
                    <input type="text" id="productSizes" placeholder="36,37,38,39,40,41,42,43,44,45,46">
                    <small style="color: #666; font-size: 12px;">Оставьте пустым для товаров без размера</small>
                </div>
                <div class="form-group">
                    <label for="productImage">Основное фото</label>
                    <div class="file-input-wrapper">
                        <input type="file" id="productImage" class="file-input" accept="image/*" onchange="handleImageUpload(this)">
                        <button type="button" class="file-input-button">📷 Выбрать фото</button>
                    </div>
                    <div class="image-preview" id="imagePreview">Выберите изображение</div>
                </div>
                <div class="form-group">
                    <label for="productGallery">Дополнительные фото (галерея)</label>
                    <div class="file-input-wrapper">
                        <input type="file" id="productGallery" class="file-input" accept="image/*" multiple onchange="handleGalleryUpload(this)">
                        <button type="button" class="file-input-button">📷 Выбрать фото для галереи</button>
                    </div>
                    <div class="gallery-preview" id="galleryPreview" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; margin-top: 8px;"></div>
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
        let selectedGalleryImages = [];
        
        // Загрузка товаров
        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                products = await response.json();
                renderProducts();
                if (document.getElementById('adminProductsList')) {
                    console.log('🛠️ Рендерим админ товары, количество:', products.length);
                    renderAdminProducts();
                    console.log('✅ Админ товары отрендерены');
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
                <div class="product-card" onclick="openProductPage(${product.id})">
                    <div class="product-image-full">
                        ${product.image_url ? 
                            `<img src="${window.location.origin}${product.image_url}" alt="${product.title}" 
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onload="console.log('✅ Изображение загружено в Telegram WebApp:', this.src)"
                                 onerror="console.error('❌ Ошибка загрузки в Telegram WebApp:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div style="display:none; color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>` : 
                            '<div style="color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>'
                        }
                        <div class="product-overlay">
                            <div class="product-info">
                                <div class="product-title">${product.title}</div>
                                <div class="product-price">${product.price.toLocaleString()} ₽</div>
                                ${product.description ? `<div class="product-description">${product.description.substring(0, 60)}${product.description.length > 60 ? '...' : ''}</div>` : ''}
                            </div>
                            <div class="product-buttons">
                                <div style="display: flex; gap: 6px; margin-top: 4px;">
                                    <button class="view-product-btn" onclick="event.stopPropagation(); openProductPage(${product.id})" style="background: rgba(0, 0, 0, 0.7); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.3); padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 10px; font-weight: 500; transition: all 0.3s ease; height: 28px; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8); flex: 1;">
                                        👁 Подробнее
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Отображение товаров в админ панели - ПРОСТАЯ ВЕРСИЯ
        function renderAdminProducts(productsToRender = products) {
            const container = document.getElementById('adminProductsList');
            
            if (productsToRender.length === 0) {
                container.innerHTML = '<div class="loading">Товары не найдены</div>';
                return;
            }
            
            container.innerHTML = productsToRender.map(product => `
                <div class="product-card">
                    <div class="product-image-full">
                        ${product.image_url ? 
                            `<img src="${window.location.origin}${product.image_url}" alt="${product.title}" 
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onload="console.log('✅ Админ изображение загружено:', this.src)"
                                 onerror="console.error('❌ Ошибка загрузки админ изображения:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div style="display:none; color: #666; font-size: 32px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>` : 
                            '<div style="color: #666; font-size: 32px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>'
                        }
                        <div class="product-overlay">
                            <div class="product-info">
                                <div class="product-title">${product.title}</div>
                                <div class="product-price">${product.price.toLocaleString()} ₽</div>
                                ${product.sizes ? `<div style="color: #ccc; font-size: 10px; margin-top: 2px;">Размеры: ${product.sizes}</div>` : ''}
                            </div>
                            <div class="product-buttons">
                                <button onclick="simpleEditProduct(${product.id})" style="background: #2196F3; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold; width: 100%; margin-bottom: 6px; min-height: 36px;">✏ Изменить</button>
                                <button onclick="simpleDeleteProduct(${product.id})" style="background: #f44336; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold; width: 100%; min-height: 36px;">🗑 Удалить</button>
                            </div>
                        </div>
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
                <div class="product-card" onclick="openProductPage(${product.id})">
                    <div class="product-image-full">
                        ${product.image_url ? 
                            `<img src="${window.location.origin}${product.image_url}" alt="${product.title}" 
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onload="console.log('✅ Изображение загружено в Telegram WebApp:', this.src)"
                                 onerror="console.error('❌ Ошибка загрузки в Telegram WebApp:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div style="display:none; color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>` : 
                            '<div style="color: #666; font-size: 24px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>'
                        }
                        <div class="product-overlay">
                            <div class="product-info">
                                <div class="product-title">${product.title}</div>
                                <div class="product-price">${product.price.toLocaleString()} ₽</div>
                                ${product.description ? `<div class="product-description">${product.description.substring(0, 60)}${product.description.length > 60 ? '...' : ''}</div>` : ''}
                            </div>
                            <div class="product-buttons">
                                <div style="display: flex; gap: 6px; margin-top: 4px;">
                                    <button class="view-product-btn" onclick="event.stopPropagation(); openProductPage(${product.id})" style="background: rgba(0, 0, 0, 0.7); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.3); padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 10px; font-weight: 500; transition: all 0.3s ease; height: 28px; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px); text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8); flex: 1;">
                                        👁 Подробнее
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Фильтрация товаров в админ панели
        function filterAdminProducts() {
            const searchTerm = document.getElementById('adminSearchInput').value.toLowerCase();
            const filteredProducts = products.filter(product => 
                product.title.toLowerCase().includes(searchTerm)
            );
            renderAdminProducts(filteredProducts);
        }
        
        // Обработка загрузки галереи изображений
        function handleGalleryUpload(input) {
            console.log('📸 handleGalleryUpload вызвана');
            
            const files = Array.from(input.files);
            if (files.length === 0) {
                selectedGalleryImages = [];
                document.getElementById('galleryPreview').innerHTML = '';
                return;
            }
            
            selectedGalleryImages = [];
            const preview = document.getElementById('galleryPreview');
            preview.innerHTML = '';
            
            files.forEach((file, index) => {
                if (file.size > 5 * 1024 * 1024) {
                    console.log('❌ Файл слишком большой:', file.size, 'байт');
                    alert(`Файл ${file.name} слишком большой! Максимум 5MB.`);
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    selectedGalleryImages.push(e.target.result);
                    
                    // Добавляем превью
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.cssText = 'width: 80px; height: 80px; object-fit: cover; border-radius: 4px; border: 1px solid #333;';
                    preview.appendChild(img);
                };
                
                reader.readAsDataURL(file);
            });
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
        function addToCart(productId, size = null) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            const existingItem = cart.find(item => item.product_id === productId && item.size === size);
            if (existingItem) {
                existingItem.quantity += 1;
            } else {
                cart.push({
                    product_id: productId,
                    quantity: 1,
                    size: size,
                    product: product
                });
            }
            
            // Сбрасываем состояние кнопок
            resetProductButtons(productId);
            
            updateCartUI();
            const sizeText = size ? ` (размер ${size})` : '';
            tg.showAlert(`${product.title}${sizeText} добавлен в корзину!`);
        }
        
        function selectSize(productId) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            // Определяем размеры в зависимости от типа товара
            let sizes = [];
            const title = product.title.toLowerCase();
            
            if (title.includes('кроссовки') || title.includes('кроссовки') || title.includes('sneakers') || 
                title.includes('nike') || title.includes('adidas') || title.includes('puma') || 
                title.includes('jordan') || title.includes('dunk') || title.includes('boost') || 
                title.includes('balance') || title.includes('обувь') || title.includes('туфли')) {
                sizes = ['36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46'];
            } else if (title.includes('футболка') || title.includes('майка') || title.includes('рубашка') || 
                      title.includes('топ') || title.includes('блузка')) {
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            } else if (title.includes('джинсы') || title.includes('брюки') || title.includes('штаны') || 
                      title.includes('шорты') || title.includes('юбка')) {
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            } else if (title.includes('куртка') || title.includes('пальто') || title.includes('пиджак') || 
                      title.includes('костюм') || title.includes('платье')) {
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            } else {
                // Для товаров без размера просто добавляем в корзину
                addToCart(productId);
                return;
            }
            
            showSizeModal(productId, sizes);
        }
        
        function showSizeModal(productId, sizes) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            const sizeButtons = sizes.map(size => 
                `<button class="size-btn" onclick="addToCartWithSize(${productId}, '${size}')">${size}</button>`
            ).join('');
            
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Выберите размер</h3>
                        <span class="close" onclick="closeModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <p><strong>${product.title}</strong></p>
                        <p>Цена: ${product.price.toLocaleString()} ₽</p>
                        <div class="size-grid">
                            ${sizeButtons}
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            modal.style.display = 'block';
        }
        
        function addToCartWithSize(productId, size) {
            closeModal();
            addToCart(productId, size);
        }
        
        function closeModal() {
            const modal = document.querySelector('.modal');
            if (modal) {
                modal.remove();
            }
        }
        
        // Переменные для шторки
        let currentProductId = null;
        let selectedSize = null;
        let currentProductSizes = [];
        
        function showSizeDrawer(productId) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            currentProductId = productId;
            
            // Определяем размеры в зависимости от типа товара
            let sizes = [];
            const title = product.title.toLowerCase();
            
            if (title.includes('кроссовки') || title.includes('sneakers') || 
                title.includes('nike') || title.includes('adidas') || title.includes('puma') || 
                title.includes('jordan') || title.includes('dunk') || title.includes('boost') || 
                title.includes('balance') || title.includes('обувь') || title.includes('туфли')) {
                sizes = ['36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46'];
            } else if (title.includes('футболка') || title.includes('майка') || title.includes('рубашка') || 
                      title.includes('топ') || title.includes('блузка')) {
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            } else if (title.includes('джинсы') || title.includes('брюки') || title.includes('штаны') || 
                      title.includes('шорты') || title.includes('юбка')) {
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            } else if (title.includes('куртка') || title.includes('пальто') || title.includes('пиджак') || 
                      title.includes('костюм') || title.includes('платье')) {
                sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
            }
            
            if (sizes.length === 0) {
                // Для товаров без размера используем стандартные размеры
                sizes = ['Без размера'];
            }
            
            currentProductSizes = sizes;
            selectedSize = null;
            
            // Заполняем информацию о товаре
            document.getElementById('drawerProductTitle').textContent = product.title;
            document.getElementById('drawerProductPrice').textContent = `${product.price.toLocaleString()} ₽`;
            
            // Создаем кнопки размеров
            const sizeGrid = document.getElementById('drawerSizeGrid');
            sizeGrid.innerHTML = sizes.map(size => `
                <button class="drawer-size-btn" onclick="selectSizeInDrawer('${size}')" data-size="${size}">
                    ${size}
                </button>
            `).join('');
            
            // Сбрасываем состояние кнопки
            document.getElementById('addToCartDrawerBtn').disabled = true;
            document.getElementById('addToCartDrawerBtn').textContent = 'Выберите размер';
            
            // Показываем шторку
            document.getElementById('sizeDrawer').classList.add('open');
        }
        
        function selectSizeInDrawer(size) {
            selectedSize = size;
            
            // Обновляем визуальное состояние кнопок в шторке
            document.querySelectorAll('.drawer-size-btn').forEach(btn => {
                btn.classList.remove('selected');
                if (btn.dataset.size === size) {
                    btn.classList.add('selected');
                }
            });
            
            // Активируем кнопку добавления в шторке
            const addBtn = document.getElementById('addToCartDrawerBtn');
            addBtn.disabled = false;
            addBtn.textContent = `Добавить размер ${size}`;
            
            // Обновляем кнопки на карточке товара
            const sizeBtn = document.getElementById(`sizeBtn_${currentProductId}`);
            const cartBtn = document.getElementById(`cartBtn_${currentProductId}`);
            
            if (sizeBtn && cartBtn) {
                sizeBtn.style.display = 'none';
                cartBtn.style.display = 'flex';
                cartBtn.textContent = `В корзину (${size})`;
                sizeBtn.classList.remove('required');
            }
        }
        
        function addToCartFromDrawer() {
            if (!currentProductId || !selectedSize) return;
            
            addToCart(currentProductId, selectedSize);
            closeSizeDrawer();
            
            // Сбрасываем глобальные переменные
            currentProductId = null;
            selectedSize = null;
            currentProductSizes = [];
        }
        
        function resetProductButtons(productId) {
            const sizeBtn = document.getElementById(`sizeBtn_${productId}`);
            const cartBtn = document.getElementById(`cartBtn_${productId}`);
            
            if (sizeBtn && cartBtn) {
                sizeBtn.style.display = 'flex';
                cartBtn.style.display = 'none';
                sizeBtn.textContent = 'Добавить в корзину';
                cartBtn.textContent = 'В корзину';
                sizeBtn.classList.add('required');
            }
        }
        
        function closeSizeDrawer() {
            document.getElementById('sizeDrawer').classList.remove('open');
            // Не сбрасываем состояние, если размер уже выбран
            if (!selectedSize) {
                currentProductId = null;
                currentProductSizes = [];
            }
        }
        
        // Удаление из корзины
        function removeFromCart(productId, size = null) {
            cart = cart.filter(item => !(item.product_id === productId && item.size === size));
            updateCartUI();
        }
        
        // Обновление количества
        function updateQuantity(productId, quantity, size = null) {
            if (quantity <= 0) {
                removeFromCart(productId, size);
                return;
            }
            
            const item = cart.find(item => item.product_id === productId && item.size === size);
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
                        <div class="cart-item-title">${item.product.title}${item.size ? ` (размер ${item.size})` : ''}</div>
                        <div class="cart-item-price">${item.product.price.toLocaleString()} ₽</div>
                    </div>
                    <div class="quantity-controls">
                        <button class="quantity-btn" onclick="updateQuantity(${item.product_id}, ${item.quantity - 1}, '${item.size || ''}')">-</button>
                        <input type="number" class="quantity-input" value="${item.quantity}" min="1" 
                               onchange="updateQuantity(${item.product_id}, parseInt(this.value), '${item.size || ''}')">
                        <button class="quantity-btn" onclick="updateQuantity(${item.product_id}, ${item.quantity + 1}, '${item.size || ''}')">+</button>
                        <button class="remove-btn" onclick="removeFromCart(${item.product_id}, '${item.size || ''}')">🗑️</button>
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
            const description = document.getElementById('productDescription').value;
            const price = parseInt(document.getElementById('productPrice').value);
            const category = document.getElementById('productCategory').value.trim();
            const brand = document.getElementById('productBrand').value.trim();
            const color = document.getElementById('productColor').value.trim();
            const material = document.getElementById('productMaterial').value.trim();
            const weight = document.getElementById('productWeight').value.trim();
            const dimensions = document.getElementById('productDimensions').value.trim();
            const sizes = document.getElementById('productSizes').value.trim();
            
            console.log('📝 Данные формы:', { 
                title: title, 
                description: description,
                price: price, 
                category: category,
                brand: brand,
                color: color,
                material: material,
                weight: weight,
                dimensions: dimensions,
                sizes: sizes,
                imageData: selectedImageData ? `есть (${selectedImageData.length} символов)` : 'нет',
                galleryImages: selectedGalleryImages.length,
                currentEditingProduct: currentEditingProduct,
                isEditMode: !!currentEditingProduct
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
                    description: description,
                    price: price,
                    category: category,
                    brand: brand,
                    color: color,
                    material: material,
                    weight: weight,
                    dimensions: dimensions,
                    sizes: sizes,
                    image: selectedImageData,
                    gallery_images: selectedGalleryImages
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
        
        // Редактирование товара (используем существующую форму)
        function editProduct(productId) {
            alert('Начинаем редактирование товара ID: ' + productId);
            console.log('🔧 Функция editProduct вызвана для ID:', productId);
            
            const product = products.find(p => p.id === productId);
            if (!product) {
                alert('Товар не найден!');
                console.error('Товар не найден:', productId);
                return;
            }
            
            console.log('Редактирование товара:', product);
            
            // Устанавливаем режим редактирования
            currentEditingProduct = productId;
            
            // Заполняем форму добавления товара
            document.getElementById('productTitle').value = product.title;
            document.getElementById('productDescription').value = product.description || '';
            document.getElementById('productPrice').value = product.price;
            document.getElementById('productCategory').value = product.category || '';
            document.getElementById('productBrand').value = product.brand || '';
            document.getElementById('productColor').value = product.color || '';
            document.getElementById('productMaterial').value = product.material || '';
            document.getElementById('productWeight').value = product.weight || '';
            document.getElementById('productDimensions').value = product.dimensions || '';
            document.getElementById('productSizes').value = product.sizes || '';
            
            // Очищаем выбранное изображение
            selectedImageData = '';
            
            // Показываем текущее изображение
            if (product.image_url) {
                const imageUrl = product.image_url.startsWith('http') ? product.image_url : `${window.location.origin}${product.image_url}`;
                document.getElementById('imagePreview').innerHTML = `<img src="${imageUrl}" alt="${product.title}" style="max-width: 100%; max-height: 120px; object-fit: cover; border-radius: 4px;">`;
            } else {
                document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
            }
            
            // Меняем текст кнопки на "Сохранить изменения"
            document.getElementById('submitBtn').textContent = '💾 Сохранить изменения';
            
            // Переключаемся на вкладку админа
            showTab('admin');
            
            // Прокручиваем к форме
            setTimeout(() => {
                document.getElementById('adminForm').scrollIntoView({ behavior: 'smooth' });
            }, 100);
        }
        
        // ПРОСТЫЕ ФУНКЦИИ ДЛЯ АДМИН ПАНЕЛИ
        function simpleEditProduct(productId) {
            // Используем существующую функцию редактирования
            editProduct(productId);
        }
        
        async function simpleDeleteProduct(productId) {
            if (!confirm('Удалить товар ID: ' + productId + '?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/delete-product/' + productId, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Товар удален успешно!');
                    loadProducts(); // Перезагружаем список
                } else {
                    alert('Ошибка удаления: ' + result.message);
                }
            } catch (error) {
                alert('Ошибка: ' + error.message);
                console.error('Error:', error);
            }
        }
        
        // Удаление товара
        async function deleteProduct(productId) {
            alert('Попытка удаления товара ID: ' + productId);
            console.log('🗑️ Функция deleteProduct вызвана для ID:', productId);
            
            if (!confirm('Вы уверены, что хотите удалить этот товар?')) {
                console.log('❌ Удаление отменено пользователем');
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
            selectedGalleryImages = [];
            document.getElementById('adminForm').reset();
            document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
            document.getElementById('galleryPreview').innerHTML = '';
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
        
        // Открытие страницы товара
        function openProductPage(productId) {
            window.location.href = `/product/${productId}`;
        }
        
        // Запуск
        loadProducts();
    </script>
    
    <!-- Шторка для выбора размера -->
    <div id="sizeDrawer" class="size-drawer">
        <div class="drawer-header">
            <h3>Выберите размер</h3>
            <span class="drawer-close" onclick="closeSizeDrawer()">&times;</span>
        </div>
        <div class="drawer-content">
            <div class="drawer-product-info">
                <h4 id="drawerProductTitle"></h4>
                <p id="drawerProductPrice"></p>
            </div>
            <div id="drawerSizeGrid" class="drawer-size-grid">
                <!-- Размеры будут добавлены динамически -->
            </div>
            <div class="drawer-actions">
                <button class="drawer-btn drawer-btn-cancel" onclick="closeSizeDrawer()">Отмена</button>
                <button class="drawer-btn drawer-btn-add" id="addToCartDrawerBtn" onclick="addToCartFromDrawer()" disabled>Добавить в корзину</button>
            </div>
        </div>
    </div>
    </body>
</html>'''

    def get_product_page(self, product_id):
        """Страница товара с подробной информацией и галереей"""
        return f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Товар - LOOK & GO</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {{ 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            padding: 16px;
            min-height: 100vh;
            padding-bottom: 100px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 24px;
            padding: 20px;
            background: #2d2d2d;
            border-radius: 12px;
            border: 1px solid #333;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .back-btn {{
            background: #1e40af;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        
        .back-btn:hover {{
            background: #1d4ed8;
        }}
        
        .header h1 {{
            font-size: 20px;
            margin: 0;
            color: #ffffff;
        }}
        
        .product-container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .product-gallery {{
            margin-bottom: 24px;
        }}
        
        .main-image {{
            width: 100%;
            height: 300px;
            background: #2d2d2d;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 16px;
            position: relative;
        }}
        
        .main-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .thumbnail-gallery {{
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 8px 0;
        }}
        
        .thumbnail {{
            min-width: 80px;
            height: 80px;
            background: #2d2d2d;
            border-radius: 8px;
            overflow: hidden;
            cursor: pointer;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .thumbnail.active {{
            border-color: #1e40af;
        }}
        
        .thumbnail img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .product-info {{
            background: #2d2d2d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            border: 1px solid #333;
        }}
        
        .product-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #ffffff;
        }}
        
        .product-price {{
            font-size: 28px;
            font-weight: 700;
            color: #10b981;
            margin-bottom: 16px;
        }}
        
        .product-description {{
            color: #cccccc;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        
        .product-details {{
            display: grid;
            gap: 12px;
        }}
        
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }}
        
        .detail-row:last-child {{
            border-bottom: none;
        }}
        
        .detail-label {{
            color: #aaaaaa;
            font-weight: 500;
        }}
        
        .detail-value {{
            color: #ffffff;
            font-weight: 600;
        }}
        
        .size-section {{
            background: #2d2d2d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            border: 1px solid #333;
        }}
        
        .size-section h3 {{
            color: #3b82f6;
            margin-bottom: 16px;
            font-size: 18px;
        }}
        
        .size-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
            gap: 8px;
        }}
        
        .size-btn {{
            background: #1a1a1a;
            border: 2px solid #333;
            border-radius: 8px;
            color: #ffffff;
            padding: 12px 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .size-btn:hover {{
            background: #3d3d3d;
            border-color: #007bff;
        }}
        
        .size-btn.selected {{
            background: #007bff;
            border-color: #007bff;
        }}
        
        .size-btn.out-of-stock {{
            background: #333;
            border-color: #555;
            color: #888;
            cursor: not-allowed;
        }}
        
        .add-to-cart-section {{
            background: #2d2d2d;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #333;
            position: sticky;
            bottom: 16px;
        }}
        
        .add-to-cart-btn {{
            background: #1e40af;
            color: white;
            border: none;
            padding: 16px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }}
        
        .add-to-cart-btn:hover:not(:disabled) {{
            background: #1d4ed8;
            transform: scale(1.02);
        }}
        
        .add-to-cart-btn:disabled {{
            background: #333;
            color: #888;
            cursor: not-allowed;
        }}
        
        .loading {{
            text-align: center;
            padding: 40px;
            color: #aaaaaa;
            font-size: 16px;
        }}
        
        .error {{
            text-align: center;
            padding: 40px;
            color: #dc2626;
            font-size: 16px;
        }}
        
        @media (max-width: 480px) {{
            .main-image {{
                height: 250px;
            }}
            
            .thumbnail {{
                min-width: 60px;
                height: 60px;
            }}
            
            .product-title {{
                font-size: 20px;
            }}
            
            .product-price {{
                font-size: 24px;
            }}
            
            .size-grid {{
                grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <button class="back-btn" onclick="goBack()">← Назад</button>
        <h1>Товар</h1>
        <div></div>
    </div>
    
    <div class="product-container">
        <div id="productContent" class="loading">
            Загрузка товара...
        </div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        let currentProduct = null;
        let selectedSize = null;
        
        // Загрузка данных товара
        async function loadProduct() {{
            const productId = window.location.pathname.split('/').pop();
            
            try {{
                const response = await fetch(`/api/product/${{productId}}`);
                
                if (!response.ok) {{
                    throw new Error('Товар не найден');
                }}
                
                currentProduct = await response.json();
                renderProduct();
            }} catch (error) {{
                document.getElementById('productContent').innerHTML = `
                    <div class="error">
                        Ошибка загрузки товара: ${{error.message}}
                    </div>
                `;
            }}
        }}
        
        // Отображение товара
        function renderProduct() {{
            if (!currentProduct) return;
            
            const galleryImages = currentProduct.gallery_images || [];
            const mainImage = currentProduct.image_url || (galleryImages.length > 0 ? galleryImages[0] : '');
            
            document.getElementById('productContent').innerHTML = `
                <div class="product-gallery">
                    <div class="main-image" id="mainImage">
                        ${{mainImage ? 
                            `<img src="${{window.location.origin}}${{mainImage}}" alt="${{currentProduct.title}}" id="mainImageImg">` : 
                            '<div style="color: #666; font-size: 48px; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">📷</div>'
                        }}
                    </div>
                    ${{galleryImages.length > 1 ? `
                        <div class="thumbnail-gallery">
                            ${{galleryImages.map((img, index) => `
                                <div class="thumbnail ${{index === 0 ? 'active' : ''}}" onclick="changeMainImage('${{img}}', this)">
                                    <img src="${{window.location.origin}}${{img}}" alt="Фото ${{index + 1}}">
                                </div>
                            `).join('')}}
                        </div>
                    ` : ''}}
                </div>
                
                <div class="product-info">
                    <h1 class="product-title">${{currentProduct.title}}</h1>
                    <div class="product-price">${{currentProduct.price.toLocaleString()}} ₽</div>
                    
                    ${{currentProduct.description ? `
                        <div class="product-description">
                            ${{currentProduct.description}}
                        </div>
                    ` : ''}}
                    
                    <div class="product-details">
                        ${{currentProduct.brand ? `
                            <div class="detail-row">
                                <span class="detail-label">Бренд:</span>
                                <span class="detail-value">${{currentProduct.brand}}</span>
                            </div>
                        ` : ''}}
                        
                        ${{currentProduct.category ? `
                            <div class="detail-row">
                                <span class="detail-label">Категория:</span>
                                <span class="detail-value">${{currentProduct.category}}</span>
                            </div>
                        ` : ''}}
                        
                        ${{currentProduct.color ? `
                            <div class="detail-row">
                                <span class="detail-label">Цвет:</span>
                                <span class="detail-value">${{currentProduct.color}}</span>
                            </div>
                        ` : ''}}
                        
                        ${{currentProduct.material ? `
                            <div class="detail-row">
                                <span class="detail-label">Материал:</span>
                                <span class="detail-value">${{currentProduct.material}}</span>
                            </div>
                        ` : ''}}
                        
                        ${{currentProduct.weight ? `
                            <div class="detail-row">
                                <span class="detail-label">Вес:</span>
                                <span class="detail-value">${{currentProduct.weight}}</span>
                            </div>
                        ` : ''}}
                        
                        
                        <div class="detail-row">
                            <span class="detail-label">Наличие:</span>
                            <span class="detail-value" style="color: ${{currentProduct.in_stock ? '#10b981' : '#dc2626'}}">
                                ${{currentProduct.in_stock ? 'В наличии' : 'Нет в наличии'}}
                            </span>
                        </div>
                    </div>
                </div>
                
                ${{currentProduct.sizes ? `
                    <div class="size-section">
                        <h3>Размеры</h3>
                        <div class="size-grid" id="sizeGrid">
                            ${{currentProduct.sizes.split(',').map(size => `
                                <button class="size-btn" onclick="selectSize('${{size.trim()}}', this)">
                                    ${{size.trim()}}
                                </button>
                            `).join('')}}
                        </div>
                    </div>
                ` : ''}}
                
                <div class="add-to-cart-section">
                    <button class="add-to-cart-btn" id="addToCartBtn" onclick="addToCart()" ${{!currentProduct.in_stock ? 'disabled' : ''}}>
                        ${{!currentProduct.in_stock ? 'Нет в наличии' : 'Добавить в корзину'}}
                    </button>
                </div>
            `;
        }}
        
        // Смена главного изображения
        function changeMainImage(imageUrl, thumbnail) {{
            const mainImageImg = document.getElementById('mainImageImg');
            if (mainImageImg) {{
                mainImageImg.src = window.location.origin + imageUrl;
            }}
            
            // Обновляем активный thumbnail
            document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
            thumbnail.classList.add('active');
        }}
        
        // Выбор размера
        function selectSize(size, button) {{
            selectedSize = size;
            
            // Обновляем визуальное состояние
            document.querySelectorAll('.size-btn').forEach(btn => {{
                btn.classList.remove('selected');
            }});
            button.classList.add('selected');
            
            // Обновляем кнопку добавления в корзину
            updateAddToCartButton();
        }}
        
        // Обновление кнопки добавления в корзину
        function updateAddToCartButton() {{
            const btn = document.getElementById('addToCartBtn');
            if (!btn) return;
            
            if (currentProduct.sizes && !selectedSize) {{
                btn.textContent = 'Выберите размер';
                btn.disabled = true;
            }} else {{
                btn.textContent = selectedSize ? `Добавить в корзину (размер ${{selectedSize}})` : 'Добавить в корзину';
                btn.disabled = false;
            }}
        }}
        
        // Добавление в корзину
        function addToCart() {{
            if (!currentProduct || !currentProduct.in_stock) return;
            
            if (currentProduct.sizes && !selectedSize) {{
                tg.showAlert('Пожалуйста, выберите размер');
                return;
            }}
            
            // Здесь можно добавить логику добавления в корзину
            // Пока просто показываем уведомление
            const sizeText = selectedSize ? ` (размер ${{selectedSize}})` : '';
            tg.showAlert(`${{currentProduct.title}}${{sizeText}} добавлен в корзину!`);
        }}
        
        // Возврат назад
        function goBack() {{
            if (window.history.length > 1) {{
                window.history.back();
            }} else {{
                window.location.href = '/';
            }}
        }}
        
        // Запуск
        loadProduct();
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
    print("🛍️ ЗАПУСК ОСНОВНОГО TELEGRAM BOT")
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

#!/usr/bin/env python3
"""
🚀 СОВРЕМЕННЫЙ TELEGRAM BOT С ПРОФЕССИОНАЛЬНОЙ СИСТЕМОЙ ИЗОБРАЖЕНИЙ
==================================================================
Полностью переписанный сервер с современными подходами
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
from pathlib import Path
import mimetypes

# Импортируем нашу современную систему изображений
from modern_image_system import ModernImageProcessor

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
PORT = int(os.getenv('PORT', 8000))
WEBAPP_URL = f'http://localhost:{PORT}'

# Инициализируем процессор изображений
image_processor = ModernImageProcessor()

# База данных
DATABASE_PATH = 'shop.db'

class ModernShopBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.webapp_url = WEBAPP_URL
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных с современной схемой"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Современная схема таблицы продуктов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price INTEGER NOT NULL,
                image_filename TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Проверяем, есть ли данные
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Добавляем тестовые данные без изображений
            test_products = [
                ('iPhone 15 Pro', 99999),
                ('MacBook Air M3', 129999),
                ('Nike Air Max', 8999),
                ('Кофе Starbucks', 299),
                ('Книга Python', 1999)
            ]
            
            cursor.executemany(
                'INSERT INTO products (title, price) VALUES (?, ?)',
                test_products
            )
            print("✅ Добавлены тестовые товары")
        
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")

class ModernHTTPHandler(BaseHTTPRequestHandler):
    """Современный HTTP обработчик с улучшенной архитектурой"""
    
    def __init__(self, *args, **kwargs):
        self.bot = ModernShopBot()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Обработка GET запросов"""
        try:
            # Логируем запрос
            print(f"📥 GET {self.path}")
            
            if self.path == '/':
                self.serve_main_page()
            elif self.path == '/api/products':
                self.serve_products_api()
            elif self.path.startswith('/uploads/'):
                self.serve_uploaded_file()
            elif self.path == '/api/images':
                self.serve_images_list()
            else:
                self.send_404()
                
        except Exception as e:
            print(f"❌ Ошибка GET {self.path}: {e}")
            self.send_500()
    
    def do_POST(self):
        """Обработка POST запросов"""
        try:
            print(f"📤 POST {self.path}")
            
            if self.path == '/api/add-product':
                self.handle_add_product()
            elif self.path.startswith('/api/update-product/'):
                product_id = self.path.split('/')[-1]
                self.handle_update_product(product_id)
            elif self.path == '/api/upload-image':
                self.handle_upload_image()
            else:
                self.send_404()
                
        except Exception as e:
            print(f"❌ Ошибка POST {self.path}: {e}")
            self.send_500()
    
    def do_DELETE(self):
        """Обработка DELETE запросов"""
        try:
            print(f"🗑️ DELETE {self.path}")
            
            if self.path.startswith('/api/delete-product/'):
                product_id = self.path.split('/')[-1]
                self.handle_delete_product(product_id)
            else:
                self.send_404()
                
        except Exception as e:
            print(f"❌ Ошибка DELETE {self.path}: {e}")
            self.send_500()
    
    def serve_main_page(self):
        """Отдача главной страницы"""
        html_content = self.get_modern_html()
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_products_api(self):
        """API для получения списка товаров"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
            products = cursor.fetchall()
            conn.close()
            
            products_data = []
            for product in products:
                product_data = {
                    'id': product[0],
                    'title': product[1],
                    'price': product[2],
                    'image_url': self.get_image_url(product[3]) if product[3] else '',
                    'created_at': product[4]
                }
                products_data.append(product_data)
            
            print(f"📦 Отправляем {len(products_data)} товаров")
            
            self.send_json_response(products_data)
            
        except Exception as e:
            print(f"❌ Ошибка получения товаров: {e}")
            self.send_json_response({'error': str(e)}, status=500)
    
    def serve_uploaded_file(self):
        """Отдача загруженных файлов"""
        try:
            # Парсим путь
            path_parts = self.path.split('/')
            if len(path_parts) < 3:
                self.send_404()
                return
            
            folder = path_parts[2]  # thumbnails или originals
            filename = '/'.join(path_parts[3:])  # остальная часть пути
            
            if folder not in ['thumbnails', 'originals']:
                self.send_404()
                return
            
            file_path = image_processor.uploads_dir / folder / filename
            
            if not file_path.exists():
                print(f"❌ Файл не найден: {file_path}")
                self.send_404()
                return
            
            # Определяем MIME тип
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'image/jpeg'
            
            # Читаем файл
            with open(file_path, 'rb') as f:
                content = f.read()
            
            print(f"🖼️ Отдаем файл: {filename} ({len(content)} байт)")
            
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            print(f"❌ Ошибка отдачи файла {self.path}: {e}")
            self.send_404()
    
    def handle_add_product(self):
        """Добавление нового товара"""
        try:
            # Получаем данные
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            title = data.get('title', '').strip()
            price = int(data.get('price', 0))
            image_base64 = data.get('image', '')
            
            print(f"📝 Добавление товара: '{title}', цена: {price}")
            
            if not title or price <= 0:
                self.send_json_response({'error': 'Неверные данные'}, status=400)
                return
            
            # Обрабатываем изображение
            image_filename = ''
            if image_base64:
                result = image_processor.save_image(image_base64, title)
                if result['success']:
                    image_filename = result['filename']
                    print(f"✅ Изображение сохранено: {image_filename}")
                else:
                    print(f"⚠️ Ошибка сохранения изображения: {result['error']}")
            
            # Сохраняем в базу
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO products (title, price, image_filename) VALUES (?, ?, ?)',
                (title, price, image_filename)
            )
            conn.commit()
            conn.close()
            
            print(f"✅ Товар добавлен: {title}")
            self.send_json_response({'success': True, 'message': 'Товар добавлен успешно!'})
            
        except Exception as e:
            print(f"❌ Ошибка добавления товара: {e}")
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_update_product(self, product_id):
        """Обновление товара"""
        try:
            # Получаем данные
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            title = data.get('title', '').strip()
            price = int(data.get('price', 0))
            image_base64 = data.get('image', '')
            
            print(f"🔄 Обновление товара ID {product_id}: '{title}', цена: {price}")
            
            if not title or price <= 0:
                self.send_json_response({'error': 'Неверные данные'}, status=400)
                return
            
            # Получаем текущий товар
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT image_filename FROM products WHERE id = ?', (product_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                self.send_json_response({'error': 'Товар не найден'}, status=404)
                return
            
            old_image_filename = result[0]
            
            # Обрабатываем новое изображение
            image_filename = old_image_filename
            if image_base64:
                # Удаляем старое изображение
                if old_image_filename:
                    image_processor.delete_image(old_image_filename)
                
                # Сохраняем новое
                result = image_processor.save_image(image_base64, title)
                if result['success']:
                    image_filename = result['filename']
                    print(f"✅ Новое изображение сохранено: {image_filename}")
            
            # Обновляем в базе
            cursor.execute(
                'UPDATE products SET title = ?, price = ?, image_filename = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (title, price, image_filename, product_id)
            )
            conn.commit()
            conn.close()
            
            print(f"✅ Товар обновлен: {title}")
            self.send_json_response({'success': True, 'message': 'Товар обновлен успешно!'})
            
        except Exception as e:
            print(f"❌ Ошибка обновления товара: {e}")
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_delete_product(self, product_id):
        """Удаление товара"""
        try:
            print(f"🗑️ Удаление товара ID {product_id}")
            
            # Получаем информацию о товаре
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT title, image_filename FROM products WHERE id = ?', (product_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                self.send_json_response({'error': 'Товар не найден'}, status=404)
                return
            
            title, image_filename = result
            
            # Удаляем изображение
            if image_filename:
                image_processor.delete_image(image_filename)
                print(f"🗑️ Удалено изображение: {image_filename}")
            
            # Удаляем товар из базы
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
            conn.close()
            
            print(f"✅ Товар удален: {title}")
            self.send_json_response({'success': True, 'message': 'Товар удален успешно!'})
            
        except Exception as e:
            print(f"❌ Ошибка удаления товара: {e}")
            self.send_json_response({'error': str(e)}, status=500)
    
    def get_image_url(self, filename):
        """Получение URL изображения"""
        if not filename:
            return ''
        return f'/uploads/thumbnails/{filename}'
    
    def send_json_response(self, data, status=200):
        """Отправка JSON ответа"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_404(self):
        """Отправка 404 ошибки"""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')
    
    def send_500(self):
        """Отправка 500 ошибки"""
        self.send_response(500)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Internal Server Error')
    
    def get_modern_html(self):
        """Современный HTML с улучшенной архитектурой"""
        return '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛍️ Modern Shop</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
            padding-bottom: 80px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
            border-bottom: 1px solid #333;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 10px;
        }
        
        .tab-button {
            background: #1a1a1a;
            border: 1px solid #333;
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .tab-button.active {
            background: #2563eb;
            border-color: #2563eb;
        }
        
        .tab-button:hover {
            background: #1e40af;
            border-color: #1e40af;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .product-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .product-card:hover {
            transform: translateY(-5px);
            border-color: #2563eb;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.2);
        }
        
        .product-image {
            width: 100%;
            height: 200px;
            background: #2a2a2a;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        .product-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        
        .product-image:hover img {
            transform: scale(1.05);
        }
        
        .product-image .placeholder {
            font-size: 3rem;
            color: #666;
        }
        
        .product-info {
            padding: 20px;
        }
        
        .product-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: #fff;
        }
        
        .product-price {
            font-size: 1.5rem;
            font-weight: 700;
            color: #10b981;
            margin-bottom: 15px;
        }
        
        .add-to-cart-btn {
            width: 100%;
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .add-to-cart-btn:hover {
            background: #1d4ed8;
            transform: translateY(-1px);
        }
        
        .admin-form {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            margin: 0 auto;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #fff;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            background: #2a2a2a;
            border: 1px solid #444;
            color: #fff;
            padding: 12px;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
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
            width: 100%;
            background: #374151;
            color: white;
            border: 1px solid #4b5563;
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .file-input-button:hover {
            background: #4b5563;
        }
        
        .image-preview {
            margin-top: 10px;
            min-height: 100px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }
        
        .image-preview img {
            max-width: 100%;
            max-height: 200px;
            border-radius: 8px;
        }
        
        .submit-btn {
            width: 100%;
            background: #10b981;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .submit-btn:hover {
            background: #059669;
            transform: translateY(-1px);
        }
        
        .cart {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 20px;
        }
        
        .cart-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #333;
        }
        
        .cart-item:last-child {
            border-bottom: none;
        }
        
        .cart-total {
            font-size: 1.5rem;
            font-weight: 700;
            color: #10b981;
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #333;
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: 600;
        }
        
        .message.success {
            background: #065f46;
            color: #10b981;
            border: 1px solid #10b981;
        }
        
        .message.error {
            background: #7f1d1d;
            color: #f87171;
            border: 1px solid #f87171;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .products-grid {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛍️ Modern Shop</h1>
            <p>Современный интернет-магазин с профессиональной системой изображений</p>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('catalog')">📦 Каталог</button>
            <button class="tab-button" onclick="switchTab('cart')">🛒 Корзина</button>
            <button class="tab-button" onclick="switchTab('admin')">⚙️ Админ</button>
        </div>
        
        <div id="catalog" class="tab-content active">
            <div class="products-grid" id="productsGrid">
                <div class="loading">Загрузка товаров...</div>
            </div>
        </div>
        
        <div id="cart" class="tab-content">
            <div class="cart" id="cartContent">
                <h3>🛒 Корзина</h3>
                <div class="loading">Корзина пуста</div>
            </div>
        </div>
        
        <div id="admin" class="tab-content">
            <div class="admin-form">
                <h3>⚙️ Управление товарами</h3>
                <div id="adminMessage"></div>
                
                <form id="productForm" onsubmit="addProduct(event)">
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
                    
                    <button type="submit" class="submit-btn" id="submitBtn">➕ Добавить товар</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        // Глобальные переменные
        let products = [];
        let cart = JSON.parse(localStorage.getItem('cart')) || {};
        let selectedImageData = '';
        let currentEditingProduct = null;
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            loadProducts();
            updateCartDisplay();
            console.log('🚀 Modern Shop инициализирован');
        });
        
        // Переключение вкладок
        function switchTab(tabName) {
            // Убираем активный класс со всех вкладок
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Активируем выбранную вкладку
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            console.log(`📱 Переключено на вкладку: ${tabName}`);
        }
        
        // Загрузка товаров
        async function loadProducts() {
            try {
                console.log('📦 Загрузка товаров...');
                const response = await fetch('/api/products');
                products = await response.json();
                
                console.log(`✅ Загружено ${products.length} товаров:`, products);
                renderProducts();
                
            } catch (error) {
                console.error('❌ Ошибка загрузки товаров:', error);
                showMessage('Ошибка загрузки товаров', 'error');
            }
        }
        
        // Отрисовка товаров
        function renderProducts() {
            const grid = document.getElementById('productsGrid');
            
            if (products.length === 0) {
                grid.innerHTML = '<div class="loading">Товары не найдены</div>';
                return;
            }
            
            grid.innerHTML = products.map(product => `
                <div class="product-card">
                    <div class="product-image">
                        ${product.image_url ? 
                            `<img src="${window.location.origin}${product.image_url}" 
                                 alt="${product.title}"
                                 onload="console.log('✅ Изображение загружено:', this.src)"
                                 onerror="console.error('❌ Ошибка загрузки:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                            <div class="placeholder" style="display:none;">📷</div>` : 
                            '<div class="placeholder">📷</div>'
                        }
                    </div>
                    <div class="product-info">
                        <div class="product-title">${product.title}</div>
                        <div class="product-price">${product.price.toLocaleString()} ₽</div>
                        <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                            В корзину
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        // Добавление в корзину
        function addToCart(productId) {
            const product = products.find(p => p.id === productId);
            if (!product) return;
            
            if (cart[productId]) {
                cart[productId].quantity += 1;
            } else {
                cart[productId] = {
                    ...product,
                    quantity: 1
                };
            }
            
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartDisplay();
            
            console.log(`🛒 Добавлен в корзину: ${product.title}`);
            showMessage(`${product.title} добавлен в корзину`, 'success');
        }
        
        // Обновление отображения корзины
        function updateCartDisplay() {
            const cartContent = document.getElementById('cartContent');
            const items = Object.values(cart);
            
            if (items.length === 0) {
                cartContent.innerHTML = '<div class="loading">Корзина пуста</div>';
                return;
            }
            
            const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            
            cartContent.innerHTML = `
                <h3>🛒 Корзина</h3>
                ${items.map(item => `
                    <div class="cart-item">
                        <div>
                            <strong>${item.title}</strong><br>
                            <small>${item.price.toLocaleString()} ₽ × ${item.quantity}</small>
                        </div>
                        <div>
                            <button onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                            <span style="margin: 0 10px;">${item.quantity}</span>
                            <button onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                            <button onclick="removeFromCart(${item.id})" style="margin-left: 10px; color: #f87171;">🗑️</button>
                        </div>
                    </div>
                `).join('')}
                <div class="cart-total">
                    Итого: ${total.toLocaleString()} ₽
                </div>
            `;
        }
        
        // Обновление количества
        function updateQuantity(productId, newQuantity) {
            if (newQuantity <= 0) {
                removeFromCart(productId);
                return;
            }
            
            if (cart[productId]) {
                cart[productId].quantity = newQuantity;
                localStorage.setItem('cart', JSON.stringify(cart));
                updateCartDisplay();
            }
        }
        
        // Удаление из корзины
        function removeFromCart(productId) {
            delete cart[productId];
            localStorage.setItem('cart', JSON.stringify(cart));
            updateCartDisplay();
        }
        
        // Обработка загрузки изображения
        function handleImageUpload(input) {
            console.log('📸 handleImageUpload вызвана');
            
            const file = input.files[0];
            if (!file) {
                console.log('📸 Файл не выбран');
                selectedImageData = '';
                document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
                return;
            }
            
            console.log('📸 Выбран файл:', {
                name: file.name,
                size: file.size,
                type: file.type
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
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                console.log('📸 Превью обновлено');
            };
            
            reader.onerror = function(error) {
                console.error('❌ Ошибка чтения файла:', error);
                alert('Ошибка чтения файла!');
            };
            
            reader.readAsDataURL(file);
        }
        
        // Добавление товара
        async function addProduct(event) {
            event.preventDefault();
            
            console.log('🚀 Функция addProduct вызвана');
            
            const title = document.getElementById('productTitle').value;
            const price = parseInt(document.getElementById('productPrice').value);
            
            console.log('📝 Данные формы:', { 
                title: title, 
                price: price, 
                imageData: selectedImageData ? `есть (${selectedImageData.length} символов)` : 'нет'
            });
            
            if (!title || !price || price <= 0) {
                console.log('❌ Неверные данные формы');
                showMessage('Пожалуйста, заполните все обязательные поля!', 'error');
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
                    imageLength: selectedImageData ? selectedImageData.length : 0
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
                    showMessage(
                        currentEditingProduct ? 'Товар обновлен успешно!' : 'Товар добавлен успешно!', 
                        'success'
                    );
                    resetForm();
                    await loadProducts();
                } else {
                    console.log('❌ Ошибка сервера:', result.message);
                    showMessage(result.message || 'Ошибка сохранения товара', 'error');
                }
            } catch (error) {
                console.error('❌ Ошибка fetch:', error);
                showMessage('Ошибка соединения с сервером: ' + error.message, 'error');
            }
        }
        
        // Сброс формы
        function resetForm() {
            document.getElementById('productForm').reset();
            selectedImageData = '';
            currentEditingProduct = null;
            document.getElementById('imagePreview').innerHTML = 'Выберите изображение';
            document.getElementById('submitBtn').textContent = '➕ Добавить товар';
        }
        
        // Показ сообщений
        function showMessage(text, type) {
            const messageDiv = document.getElementById('adminMessage');
            messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
            
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 3000);
        }
    </script>
</body>
</html>
        '''

def run_server():
    """Запуск сервера"""
    print("🚀 СОВРЕМЕННЫЙ TELEGRAM BOT")
    print("=" * 50)
    
    # Проверяем токен бота
    if BOT_TOKEN:
        print("🤖 Бот готов к работе")
        print(f"📱 Токен: {BOT_TOKEN[:10]}...")
    else:
        print("⚠️ BOT_TOKEN не найден - бот отключен")
        print("💡 Установите переменную окружения BOT_TOKEN")
    
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print("=" * 50)
    
    # Запускаем HTTP сервер
    server = HTTPServer(('0.0.0.0', PORT), ModernHTTPHandler)
    
    try:
        print(f"🛑 Для остановки нажмите Ctrl+C")
        print(f"🌐 Веб-сервер запущен на http://0.0.0.0:{PORT}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        server.shutdown()

if __name__ == "__main__":
    run_server()

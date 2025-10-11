#!/usr/bin/env python3
"""
ИДЕАЛЬНЫЙ СЕРВЕР - Полностью переделанная логика с нуля
Гарантированно работающие добавление и удаление товаров
"""

import http.server
import socketserver
import json
import os
import sqlite3
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = 8000
DB_PATH = "shop.db"

class ProductManager:
    """Менеджер товаров - работа с базой данных"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    sizes TEXT,
                    photo TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT
                )
            """)
            conn.commit()
            print("✅ База данных инициализирована")
    
    def get_all_products(self, active_only=True):
        """Получить все товары"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY id DESC")
            else:
                cursor.execute("SELECT * FROM products ORDER BY id DESC")
            
            rows = cursor.fetchall()
            products = []
            
            for row in rows:
                product = {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "price": row["price"],
                    "sizes": json.loads(row["sizes"]) if row["sizes"] else [],
                    "photo": row["photo"],
                    "is_active": bool(row["is_active"])
                }
                products.append(product)
            
            print(f"📦 Загружено товаров: {len(products)}")
            return products
    
    def get_product_by_id(self, product_id):
        """Получить товар по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "price": row["price"],
                "sizes": json.loads(row["sizes"]) if row["sizes"] else [],
                "photo": row["photo"],
                "is_active": bool(row["is_active"])
            }
    
    def add_product(self, title, description, price, sizes, photo="/webapp/static/uploads/default.jpg"):
        """Добавить новый товар"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (title, description, price, sizes, photo, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                title,
                description,
                price,
                json.dumps(sizes),
                photo,
                datetime.now().isoformat()
            ))
            conn.commit()
            product_id = cursor.lastrowid
            print(f"✅ Товар добавлен: ID={product_id}, {title}")
            return product_id
    
    def update_product(self, product_id, title=None, description=None, price=None, sizes=None, photo=None):
        """Обновить товар"""
        product = self.get_product_by_id(product_id)
        if not product:
            print(f"❌ Товар ID={product_id} не найден")
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if price is not None:
                updates.append("price = ?")
                params.append(price)
            if sizes is not None:
                updates.append("sizes = ?")
                params.append(json.dumps(sizes))
            if photo is not None:
                updates.append("photo = ?")
                params.append(photo)
            
            if not updates:
                return True
            
            params.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, params)
            conn.commit()
            print(f"✅ Товар обновлен: ID={product_id}")
            return True
    
    def delete_product(self, product_id):
        """Удалить товар (мягкое удаление)"""
        product = self.get_product_by_id(product_id)
        if not product:
            print(f"❌ Товар ID={product_id} не найден")
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
            conn.commit()
            
            # Проверяем результат
            cursor.execute("SELECT is_active FROM products WHERE id = ?", (product_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 0:
                print(f"✅ Товар удален: ID={product_id}, {product['title']}")
                return True
            else:
                print(f"❌ Ошибка удаления товара ID={product_id}")
                return False

# Глобальный менеджер товаров
product_manager = ProductManager(DB_PATH)

class PerfectHandler(http.server.SimpleHTTPRequestHandler):
    """Идеальный обработчик запросов"""
    
    def end_headers(self):
        # CORS заголовки для всех запросов
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Обработка preflight запросов"""
        self.send_response(200)
        self.end_headers()
    
    def send_json(self, status_code, data):
        """Отправить JSON ответ"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_GET(self):
        """Обработка GET запросов"""
        print(f"📥 GET {self.path}")
        
        # Главная страница
        if self.path == '/' or self.path == '/webapp/index_clean.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            try:
                with open('webapp/index_clean.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except:
                self.wfile.write('<h1>Сервер работает!</h1>'.encode('utf-8'))
            return
        
        # API: Получить список товаров
        elif self.path == '/webapp/products.json' or self.path == '/api/products':
            products = product_manager.get_all_products(active_only=True)
            self.send_json(200, products)
            return
        
        # API: Получить все товары (для админа)
        elif self.path.startswith('/webapp/admin/products'):
            products = product_manager.get_all_products(active_only=False)
            self.send_json(200, {"products": products})
            return
        
        # Статические файлы
        else:
            super().do_GET()
    
    def do_POST(self):
        """Обработка POST запросов - добавление товара"""
        print(f"📥 POST {self.path}")
        
        if self.path == '/webapp/admin/products' or self.path == '/api/admin/products':
            try:
                # Читаем данные
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Парсим JSON
                data = json.loads(post_data.decode('utf-8'))
                
                # Извлекаем данные
                title = data.get('title', 'Новый товар')
                description = data.get('description', '')
                price = float(data.get('price', 1000))
                sizes = data.get('sizes', ['M', 'L'])
                photo = data.get('photo', '/webapp/static/uploads/default.jpg')
                
                # Добавляем товар
                product_id = product_manager.add_product(title, description, price, sizes, photo)
                
                self.send_json(200, {
                    "success": True,
                    "product_id": product_id,
                    "message": "Товар создан успешно"
                })
                
            except Exception as e:
                print(f"❌ Ошибка добавления товара: {e}")
                self.send_json(500, {"success": False, "error": str(e)})
        else:
            self.send_json(404, {"success": False, "error": "Not found"})
    
    def do_PUT(self):
        """Обработка PUT запросов - редактирование товара"""
        print(f"📥 PUT {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            try:
                # Извлекаем ID товара
                path_parts = self.path.split('/')
                product_id = int(path_parts[-1].split('?')[0])
                
                # Читаем данные
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Парсим JSON
                data = json.loads(post_data.decode('utf-8'))
                
                # Обновляем товар
                success = product_manager.update_product(
                    product_id,
                    title=data.get('title'),
                    description=data.get('description'),
                    price=data.get('price'),
                    sizes=data.get('sizes'),
                    photo=data.get('photo')
                )
                
                if success:
                    self.send_json(200, {"success": True, "message": "Товар обновлен успешно"})
                else:
                    self.send_json(404, {"success": False, "error": "Товар не найден"})
                
            except Exception as e:
                print(f"❌ Ошибка обновления товара: {e}")
                self.send_json(500, {"success": False, "error": str(e)})
        else:
            self.send_json(404, {"success": False, "error": "Not found"})
    
    def do_DELETE(self):
        """Обработка DELETE запросов - удаление товара"""
        print(f"📥 DELETE {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            try:
                # Извлекаем ID товара
                path_parts = self.path.split('/')
                product_id_str = path_parts[-1].split('?')[0]
                product_id = int(product_id_str)
                
                print(f"🗑️ Удаляем товар ID={product_id}")
                
                # Удаляем товар
                success = product_manager.delete_product(product_id)
                
                if success:
                    self.send_json(200, {"success": True, "message": "Товар удален успешно"})
                else:
                    self.send_json(404, {"success": False, "error": "Товар не найден"})
                
            except Exception as e:
                print(f"❌ Ошибка удаления товара: {e}")
                import traceback
                traceback.print_exc()
                self.send_json(500, {"success": False, "error": str(e)})
        else:
            self.send_json(404, {"success": False, "error": "Not found"})

def start_server():
    """Запуск сервера"""
    print("=" * 60)
    print("🚀 ИДЕАЛЬНЫЙ СЕРВЕР")
    print("=" * 60)
    print(f"📱 Адрес: http://localhost:{PORT}")
    print(f"💾 База данных: {DB_PATH}")
    
    # Инициализируем тестовые данные
    products = product_manager.get_all_products(active_only=False)
    print(f"🛍️ Товаров в системе: {len(products)}")
    print("=" * 60)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), PerfectHandler) as httpd:
        try:
            print("✅ Сервер запущен успешно!")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен")

if __name__ == "__main__":
    start_server()


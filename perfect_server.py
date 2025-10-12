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
import time
import shutil
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import traceback

PORT = 8000
DB_PATH = "shop.db"

class ProductManager:
    """Менеджер товаров - работа с базой данных"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.backup_dir = "db_backups"
        self.json_backup = "products_backup.json"
        self.init_database()
        self.restore_from_backup()  # Восстанавливаем данные при запуске
        self.auto_backup()  # Автобэкап при запуске
    
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
    
    def auto_backup(self):
        """Автоматическое резервное копирование"""
        try:
            if not os.path.exists(self.db_path):
                return
            
            # Создаем директорию для бэкапов
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Бэкап файла БД
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"shop_backup_{timestamp}.db")
            shutil.copy2(self.db_path, backup_path)
            
            # Экспорт в JSON
            self.export_to_json()
            
            # Удаляем старые бэкапы (оставляем 10 последних)
            self.cleanup_old_backups()
            
            print(f"💾 Автобэкап создан: {backup_path}")
        except Exception as e:
            print(f"⚠️ Ошибка автобэкапа: {e}")
    
    def export_to_json(self):
        """Экспортировать товары в JSON"""
        try:
            products = self.get_all_products(active_only=False)
            with open(self.json_backup, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            print(f"📄 JSON бэкап: {self.json_backup} ({len(products)} товаров)")
        except Exception as e:
            print(f"⚠️ Ошибка экспорта JSON: {e}")
    
    def cleanup_old_backups(self, keep_count=10):
        """Удалить старые бэкапы"""
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.endswith('.db')]
            backups.sort(reverse=True)
            for backup in backups[keep_count:]:
                os.remove(os.path.join(self.backup_dir, backup))
        except Exception as e:
            print(f"⚠️ Ошибка очистки бэкапов: {e}")
    
    def restore_from_backup(self):
        """Восстановить данные из бэкапа при запуске"""
        try:
            # Проверяем, есть ли активные товары в БД
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
                active_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM products")
                total_count = cursor.fetchone()[0]
            
            print(f"📊 Статус БД: {total_count} товаров всего, {active_count} активных")
            
            if active_count > 0:
                print(f"✅ База данных содержит {active_count} активных товаров")
                return
            elif total_count > 0:
                print(f"⚠️ В БД есть {total_count} товаров, но все неактивные")
            else:
                print("❌ База данных пустая")
            
            # Если БД пустая, пытаемся восстановить из JSON
            if os.path.exists(self.json_backup):
                print("🔄 Восстанавливаем данные из JSON бэкапа...")
                self.restore_from_json()
                return
            
            # Если JSON нет, ищем последний DB бэкап
            if os.path.exists(self.backup_dir):
                backups = [f for f in os.listdir(self.backup_dir) if f.endswith('.db')]
                if backups:
                    backups.sort(reverse=True)
                    latest_backup = os.path.join(self.backup_dir, backups[0])
                    print(f"🔄 Восстанавливаем из DB бэкапа: {latest_backup}")
                    shutil.copy2(latest_backup, self.db_path)
                    return
            
            print("ℹ️ Бэкапы не найдены, создаем новую БД")
            
        except Exception as e:
            print(f"⚠️ Ошибка восстановления из бэкапа: {e}")
    
    def restore_from_json(self):
        """Восстановить данные из JSON файла"""
        try:
            with open(self.json_backup, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for product in products:
                    created_at = product.get("created_at", datetime.now().isoformat())
                    cursor.execute("""
                        INSERT OR REPLACE INTO products (id, title, description, price, sizes, photo, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product.get("id"),
                        product.get("title", ""),
                        product.get("description", ""),
                        product.get("price", 0),
                        json.dumps(product.get("sizes", [])),
                        product.get("photo", ""),
                        1 if product.get("is_active", True) else 0,
                        created_at
                    ))
                
                conn.commit()
            
            print(f"✅ Восстановлено {len(products)} товаров из JSON")
            
        except Exception as e:
            print(f"❌ Ошибка восстановления из JSON: {e}")
    
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
        try:
            print(f"🔧 Добавляем товар в БД: title={title}, price={price}, sizes={sizes}")
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
                print(f"✅ Товар добавлен в БД: ID={product_id}, {title}")
                
                # Автосохранение после добавления
                self.auto_backup()
                
                return product_id
        except Exception as e:
            print(f"❌ Ошибка добавления в БД: {e}")
            traceback.print_exc()
            raise
    
    def update_product(self, product_id, title=None, description=None, price=None, sizes=None, photo=None, is_active=None):
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
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            
            if not updates:
                return True
            
            params.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, params)
            conn.commit()
            print(f"✅ Товар обновлен: ID={product_id}")
            
            # Автосохранение после обновления
            self.auto_backup()
            
            return True
    
    def delete_product(self, product_id):
        """Удалить товар (мягкое удаление)"""
        product = self.get_product_by_id(product_id)
        if not product:
            print(f"❌ Товар ID={product_id} не найден")
            return False
        
        # Проверяем, не удален ли уже товар
        if not product.get('is_active', True):
            print(f"⚠️ Товар ID={product_id} уже был удален ранее")
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
                
                # Автосохранение после удаления
                self.auto_backup()
                
                return True
            else:
                print(f"❌ Ошибка удаления товара ID={product_id}")
                return False

# Глобальный менеджер товаров
product_manager = ProductManager(DB_PATH)

class PerfectHandler(http.server.SimpleHTTPRequestHandler):
    """Идеальный обработчик запросов"""
    
    def is_admin(self, query_params):
        """Проверка админских прав"""
        # Проверяем user_id в параметрах запроса
        user_id = query_params.get('user_id', [''])[0]
        
        # Единственный администратор - ваш Telegram ID
        ADMIN_USER_ID = '1593426947'
        
        is_admin = (user_id == ADMIN_USER_ID)
        
        if is_admin:
            print(f"👑 Админский доступ разрешен для user_id: {user_id}")
        else:
            print(f"🔒 Доступ запрещен для user_id: {user_id}")
        
        return is_admin
    
    def _parse_multipart(self, post_data, content_type):
        """Парсинг multipart/form-data"""
        try:
            # Извлекаем boundary
            boundary = content_type.split('boundary=')[1]
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]
            
            print(f"🔍 Boundary из заголовка: {boundary}")
            
            # Boundary в данных может иметь префикс "--", а может и нет
            # Ищем его в данных
            boundary_bytes = boundary.encode()
            if b'--' + boundary_bytes in post_data:
                separator = b'--' + boundary_bytes
                print(f"✅ Найден разделитель с --")
            elif boundary_bytes in post_data:
                separator = boundary_bytes
                print(f"✅ Найден разделитель без --")
            else:
                print(f"❌ Разделитель не найден в данных!")
                return {}
            
            # Разбиваем на части
            parts = post_data.split(separator)
            
            result = {}
            for i, part in enumerate(parts):
                if b'Content-Disposition' in part:
                    try:
                        # Ищем name
                        name_start = part.find(b'name="') + 6
                        name_end = part.find(b'"', name_start)
                        name = part[name_start:name_end].decode('utf-8')
                        
                        # Проверяем, это файл или текст
                        if b'filename=' in part:
                            # Это файл - сохраняем его!
                            filename_start = part.find(b'filename="') + 10
                            filename_end = part.find(b'"', filename_start)
                            filename = part[filename_start:filename_end].decode('utf-8')
                            
                            if filename:  # Если файл выбран
                                # Извлекаем данные файла
                                file_data_start = part.find(b'\r\n\r\n') + 4
                                file_data_end = part.rfind(b'\r\n')
                                
                                if file_data_start > 3 and file_data_end > file_data_start:
                                    file_data = part[file_data_start:file_data_end]
                                    
                                    # Генерируем уникальное имя файла
                                    timestamp = int(time.time())
                                    ext = os.path.splitext(filename)[1]
                                    new_filename = f"photo_{timestamp}{ext}"
                                    
                                    # Создаем директории если нужно
                                    os.makedirs('webapp/uploads', exist_ok=True)
                                    os.makedirs('webapp/static/uploads', exist_ok=True)
                                    
                                    # Сохраняем файл в оба места
                                    file_path_1 = os.path.join('webapp/uploads', new_filename)
                                    file_path_2 = os.path.join('webapp/static/uploads', new_filename)
                                    
                                    with open(file_path_1, 'wb') as f:
                                        f.write(file_data)
                                    with open(file_path_2, 'wb') as f:
                                        f.write(file_data)
                                    
                                    # Сохраняем путь к файлу
                                    result['photo'] = f'/webapp/static/uploads/{new_filename}'
                                    print(f"   📸 Часть {i}: {name} - файл сохранен: {new_filename} ({len(file_data)} байт)")
                            else:
                                print(f"   📎 Часть {i}: {name} - файл не выбран")
                            continue
                        
                        # Ищем значение (после двойного переноса строки)
                        value_start = part.find(b'\r\n\r\n') + 4
                        value_end = part.rfind(b'\r\n')
                        
                        if value_start > 3 and value_end > value_start:
                            value = part[value_start:value_end].decode('utf-8', errors='ignore').strip()
                            if value:  # Только непустые значения
                                result[name] = value
                                print(f"   ✅ Часть {i}: {name} = {value[:50]}...")
                    except Exception as e:
                        print(f"   ❌ Ошибка обработки части {i}: {e}")
                        traceback.print_exc()
                        continue
            
            print(f"🔧 Распарсен multipart: {result}")
            return result
        except Exception as e:
            print(f"❌ Ошибка парсинга multipart: {e}")
            traceback.print_exc()
            return {}
    
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
            # Проверяем админские права
            query_params = parse_qs(urlparse(self.path).query)
            if not self.is_admin(query_params):
                self.send_json(403, {"error": "Доступ запрещен"})
                return
            
            products = product_manager.get_all_products(active_only=False)
            self.send_json(200, {"products": products})
            return
        
        # Фото товаров - перенаправляем с /webapp/static/uploads/ на /webapp/uploads/
        elif '/webapp/static/uploads/' in self.path or '/webapp/uploads/' in self.path:
            # Убираем query параметры если есть
            clean_path = self.path.split('?')[0]
            
            # Заменяем путь на реальный
            if '/webapp/static/uploads/' in clean_path:
                real_path = clean_path.replace('/webapp/static/uploads/', 'webapp/uploads/')
            else:
                real_path = clean_path.replace('/webapp/uploads/', 'webapp/uploads/')
            
            print(f"🖼️ Запрос фото: {self.path} -> {real_path}")
            
            try:
                with open(real_path, 'rb') as f:
                    self.send_response(200)
                    # Определяем MIME тип
                    if real_path.lower().endswith(('.jpg', '.jpeg')):
                        self.send_header('Content-type', 'image/jpeg')
                    elif real_path.lower().endswith('.png'):
                        self.send_header('Content-type', 'image/png')
                    elif real_path.lower().endswith('.gif'):
                        self.send_header('Content-type', 'image/gif')
                    elif real_path.lower().endswith('.webp'):
                        self.send_header('Content-type', 'image/webp')
                    else:
                        self.send_header('Content-type', 'application/octet-stream')
                    
                    # Добавляем заголовки кеширования
                    self.send_header('Cache-Control', 'public, max-age=86400')
                    self.end_headers()
                    self.wfile.write(f.read())
                print(f"✅ Фото отправлено: {real_path}")
                return
            except FileNotFoundError:
                print(f"❌ Фото не найдено: {real_path}")
                # Пытаемся найти в альтернативных местах
                alt_paths = [
                    real_path.replace('webapp/uploads/', 'webapp/static/uploads/'),
                    'webapp/static/uploads/default.jpg'
                ]
                for alt_path in alt_paths:
                    try:
                        with open(alt_path, 'rb') as f:
                            self.send_response(200)
                            self.send_header('Content-type', 'image/jpeg')
                            self.end_headers()
                            self.wfile.write(f.read())
                        print(f"✅ Фото найдено в альтернативном месте: {alt_path}")
                        return
                    except FileNotFoundError:
                        continue
                
                self.send_error(404, f"File not found: {real_path}")
                return
            except Exception as e:
                print(f"❌ Ошибка чтения фото: {e}")
                self.send_error(500, f"Error reading file: {str(e)}")
                return
        
        # Статические файлы
        else:
            super().do_GET()
    
    def do_POST(self):
        """Обработка POST запросов - добавление товара"""
        print(f"📥 POST {self.path}")
        
        if self.path.startswith('/webapp/admin/products') or self.path.startswith('/api/admin/products'):
            # Проверяем админские права
            query_params = parse_qs(urlparse(self.path).query)
            if not self.is_admin(query_params):
                self.send_json(403, {"error": "Доступ запрещен"})
                return
            
            try:
                # Читаем данные
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                print(f"📦 Получены данные: {post_data[:200]}")  # Первые 200 байт
                
                # Проверяем Content-Type
                content_type = self.headers.get('Content-Type', '')
                print(f"📋 Content-Type: {content_type}")
                
                # Парсим в зависимости от типа
                if 'multipart/form-data' in content_type:
                    print("📝 Обнаружен multipart/form-data, парсим форму...")
                    # Парсим multipart form data
                    data = self._parse_multipart(post_data, content_type)
                else:
                    # Парсим JSON
                    data = json.loads(post_data.decode('utf-8'))
                
                print(f"✅ Распарсены данные: {data}")
                
                # Извлекаем данные
                title = data.get('title', 'Новый товар')
                description = data.get('description', '')
                
                # Обработка цены
                try:
                    price = float(data.get('price', 1000))
                except (ValueError, TypeError):
                    price = 1000
                    print(f"⚠️ Неверная цена, используем 1000")
                
                # Обработка sizes - может быть массив или строка
                sizes_raw = data.get('sizes', ['M', 'L'])
                if isinstance(sizes_raw, str):
                    sizes = [s.strip() for s in sizes_raw.split(',') if s.strip()]
                elif isinstance(sizes_raw, list):
                    sizes = sizes_raw
                else:
                    sizes = ['M', 'L']
                
                photo = data.get('photo', '/webapp/static/uploads/default.jpg')
                
                print(f"📝 Создаем товар:")
                print(f"   - Название: {title}")
                print(f"   - Описание: {description}")
                print(f"   - Цена: {price}")
                print(f"   - Размеры: {sizes}")
                print(f"   - Фото: {photo}")
                
                # Добавляем товар
                product_id = product_manager.add_product(title, description, price, sizes, photo)
                
                print(f"✅ Товар создан с ID: {product_id}")
                
                self.send_json(200, {
                    "success": True,
                    "product_id": product_id,
                    "message": "Товар создан успешно"
                })
                
            except Exception as e:
                print(f"❌ Ошибка добавления товара: {e}")
                import traceback
                traceback.print_exc()
                self.send_json(500, {"success": False, "error": str(e)})
        else:
            self.send_json(404, {"success": False, "error": "Not found"})
    
    def do_PUT(self):
        """Обработка PUT запросов - редактирование товара"""
        print(f"📥 PUT {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            # Проверяем админские права
            query_params = parse_qs(urlparse(self.path).query)
            if not self.is_admin(query_params):
                self.send_json(403, {"error": "Доступ запрещен"})
                return
            
            try:
                # Извлекаем ID товара
                path_parts = self.path.split('/')
                product_id = int(path_parts[-1].split('?')[0])
                
                print(f"✏️ Редактируем товар ID={product_id}")
                
                # Читаем данные
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                print(f"📦 Получены данные для обновления: {post_data[:200]}")
                
                # Проверяем Content-Type
                content_type = self.headers.get('Content-Type', '')
                print(f"📋 Content-Type: {content_type}")
                
                # Парсим в зависимости от типа
                if 'multipart/form-data' in content_type:
                    print("📝 Обнаружен multipart/form-data, парсим форму...")
                    data = self._parse_multipart(post_data, content_type)
                else:
                    data = json.loads(post_data.decode('utf-8'))
                
                print(f"✅ Распарсены данные для обновления: {data}")
                
                # Обработка цены
                price = None
                if 'price' in data:
                    try:
                        price = float(data['price'])
                    except (ValueError, TypeError):
                        print(f"⚠️ Неверная цена: {data['price']}")
                        price = None
                
                # Обработка размеров
                sizes = None
                if 'sizes' in data:
                    sizes_raw = data['sizes']
                    if isinstance(sizes_raw, str):
                        sizes = [s.strip() for s in sizes_raw.split(',') if s.strip()]
                    elif isinstance(sizes_raw, list):
                        sizes = sizes_raw
                
                # Обработка is_active
                is_active = None
                if 'is_active' in data:
                    is_active = bool(data['is_active'])
                
                print(f"📝 Обновляем товар:")
                print(f"   - Название: {data.get('title', 'не изменяется')}")
                print(f"   - Описание: {data.get('description', 'не изменяется')}")
                print(f"   - Цена: {price if price else 'не изменяется'}")
                print(f"   - Размеры: {sizes if sizes else 'не изменяются'}")
                print(f"   - Фото: {data.get('photo', 'не изменяется')}")
                print(f"   - Активен: {is_active if is_active is not None else 'не изменяется'}")
                
                # Обновляем товар
                success = product_manager.update_product(
                    product_id,
                    title=data.get('title'),
                    description=data.get('description'),
                    price=price,
                    sizes=sizes,
                    photo=data.get('photo'),
                    is_active=is_active
                )
                
                if success:
                    print(f"✅ Товар ID={product_id} успешно обновлен")
                    self.send_json(200, {"success": True, "message": "Товар обновлен успешно"})
                else:
                    print(f"❌ Товар ID={product_id} не найден")
                    self.send_json(404, {"success": False, "error": "Товар не найден"})
                
            except Exception as e:
                print(f"❌ Ошибка обновления товара: {e}")
                traceback.print_exc()
                self.send_json(500, {"success": False, "error": str(e)})
        else:
            self.send_json(404, {"success": False, "error": "Not found"})
    
    def do_DELETE(self):
        """Обработка DELETE запросов - удаление товара"""
        print(f"📥 DELETE {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            # Проверяем админские права
            query_params = parse_qs(urlparse(self.path).query)
            if not self.is_admin(query_params):
                self.send_json(403, {"error": "Доступ запрещен"})
                return
            
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


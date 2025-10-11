"""
База данных SQLite для Telegram бота магазина
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "shop.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Создает таблицы в базе данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Таблица товаров
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    sizes TEXT,  -- JSON массив размеров
                    photo TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица заказов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    products TEXT NOT NULL,  -- JSON массив товаров
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',  -- pending, paid, shipped, delivered, cancelled
                    payment_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            """)
            
            # Таблица сообщений админов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    from_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            """)
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    def add_user(self, telegram_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None, 
                 phone: str = None, is_admin: bool = False):
        """Добавляет пользователя в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (telegram_id, username, first_name, last_name, phone, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (telegram_id, username, first_name, last_name, phone, is_admin))
                conn.commit()
                logger.info(f"Пользователь {telegram_id} добавлен в базу")
                return True
            except Exception as e:
                logger.error(f"Ошибка добавления пользователя: {e}")
                return False
    
    async def register_user(self, telegram_id: str, username: str = None):
        """Регистрирует пользователя (асинхронная версия add_user)"""
        try:
            return self.add_user(int(telegram_id), username)
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Получает пользователя по Telegram ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id, username, first_name, last_name, phone, is_admin, created_at
                FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'telegram_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'phone': row[4],
                    'is_admin': bool(row[5]),
                    'created_at': row[6]
                }
            return None
    
    def add_product(self, title: str, description: str, price: float, 
                   sizes: List[str], photo: str = None) -> int:
        """Добавляет товар в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO products (title, description, price, sizes, photo)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, description, price, json.dumps(sizes), photo))
                conn.commit()
                product_id = cursor.lastrowid
                logger.info(f"Товар '{title}' добавлен с ID {product_id}")
                return product_id
            except Exception as e:
                logger.error(f"Ошибка добавления товара: {e}")
                return None
    
    def update_product(self, product_id: int, title: str, description: str, 
                      price: float, sizes: List[str], photo: str = None) -> bool:
        """Обновляет товар в базе данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE products 
                    SET title = ?, description = ?, price = ?, sizes = ?, photo = ?
                    WHERE id = ?
                """, (title, description, price, json.dumps(sizes), photo, product_id))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Товар {product_id} обновлен")
                    return True
                else:
                    logger.warning(f"Товар {product_id} не найден для обновления")
                    return False
            except Exception as e:
                logger.error(f"Ошибка обновления товара {product_id}: {e}")
                return False

    def get_products(self, active_only: bool = True) -> List[Dict]:
        """Получает список товаров"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT id, title, description, price, sizes, photo, is_active FROM products"
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            products = []
            for row in rows:
                products.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'price': row[3],
                    'sizes': json.loads(row[4]) if row[4] else [],
                    'photo': row[5],
                    'is_active': bool(row[6]) if len(row) > 6 else True
                })
            return products
    
    def add_order(self, user_id: int, products: List[Dict], total_amount: float) -> int:
        """Добавляет заказ в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO orders (user_id, products, total_amount)
                    VALUES (?, ?, ?)
                """, (user_id, json.dumps(products), total_amount))
                conn.commit()
                order_id = cursor.lastrowid
                logger.info(f"Заказ {order_id} создан для пользователя {user_id}")
                return order_id
            except Exception as e:
                logger.error(f"Ошибка создания заказа: {e}")
                return None
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Получает заказы пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, products, total_amount, status, created_at
                FROM orders WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                orders.append({
                    'id': row[0],
                    'products': json.loads(row[1]),
                    'total_amount': row[2],
                    'status': row[3],
                    'created_at': row[4]
                })
            return orders
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновляет статус заказа"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE orders SET status = ? WHERE id = ?
                """, (status, order_id))
                conn.commit()
                logger.info(f"Статус заказа {order_id} изменен на {status}")
                return True
            except Exception as e:
                logger.error(f"Ошибка обновления статуса заказа: {e}")
                return False
    
    def add_admin_message(self, user_id: int, message: str, from_admin: bool = False):
        """Добавляет сообщение в чат с админом"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO admin_messages (user_id, message, from_admin)
                    VALUES (?, ?, ?)
                """, (user_id, message, from_admin))
                conn.commit()
                logger.info(f"Сообщение добавлено для пользователя {user_id}")
                return True
            except Exception as e:
                logger.error(f"Ошибка добавления сообщения: {e}")
                return False
    
    def get_admin_messages(self, user_id: int) -> List[Dict]:
        """Получает сообщения чата с админом"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message, from_admin, created_at
                FROM admin_messages WHERE user_id = ? ORDER BY created_at ASC
            """, (user_id,))
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                messages.append({
                    'message': row[0],
                    'from_admin': bool(row[1]),
                    'created_at': row[2]
                })
            return messages
    
    def get_all_orders(self) -> List[Dict]:
        """Получает все заказы (для админов)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id, o.user_id, u.first_name, u.username, o.products, 
                       o.total_amount, o.status, o.created_at
                FROM orders o
                JOIN users u ON o.user_id = u.telegram_id
                ORDER BY o.created_at DESC
            """)
            rows = cursor.fetchall()
            orders = []
            for row in rows:
                orders.append({
                    'id': row[0],
                    'user_id': row[1],
                    'user_name': row[2],
                    'username': row[3],
                    'products': json.loads(row[4]),
                    'total_amount': row[5],
                    'status': row[6],
                    'created_at': row[7]
                })
            return orders
    
    def update_product_status(self, product_id: int, is_active: bool) -> bool:
        """Обновляет статус товара (активен/неактивен)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE products SET is_active = ? WHERE id = ?
                """, (is_active, product_id))
                conn.commit()
                logger.info(f"Product {product_id} status updated to {is_active}")
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Error updating product status: {e}")
                return False
    
    def migrate_from_json(self):
        """Мигрирует данные из JSON файлов в базу данных"""
        logger.info("Начинаем миграцию данных из JSON в базу данных...")
        
        # Мигрируем товары
        if os.path.exists("webapp/products.json"):
            with open("webapp/products.json", "r", encoding="utf-8") as f:
                products = json.load(f)
                for product in products:
                    self.add_product(
                        title=product.get("title", ""),
                        description=product.get("description", ""),
                        price=product.get("price", 0),
                        sizes=product.get("sizes", []),
                        photo=product.get("photo")
                    )
            logger.info(f"Мигрировано {len(products)} товаров")
        
        # Мигрируем админов
        if os.path.exists("webapp/admins.json"):
            with open("webapp/admins.json", "r", encoding="utf-8") as f:
                admins = json.load(f)
                for admin_id in admins:
                    self.add_user(telegram_id=admin_id, is_admin=True)
            logger.info(f"Мигрировано {len(admins)} админов")
        
        logger.info("Миграция завершена!")
    
    async def create_order(self, user_id: str, order_data) -> int:
        """Создает новый заказ"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                # Конвертируем товары в JSON
                products_json = json.dumps([item.dict() for item in order_data.items])
                
                cursor.execute("""
                    INSERT INTO orders (user_id, products, total_amount, status, text)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, products_json, order_data.total, 'pending', order_data.text))
                
                order_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Создан заказ {order_id} для пользователя {user_id}")
                return order_id
            except Exception as e:
                logger.error(f"Ошибка создания заказа: {e}")
                return None
    
    async def create_product(self, product_data) -> int:
        """Создает новый товар"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                # Конвертируем размеры в JSON
                sizes_json = json.dumps(product_data.sizes) if product_data.sizes else None
                
                cursor.execute("""
                    INSERT INTO products (title, description, price, sizes, photo, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (product_data.title, product_data.description, product_data.price, 
                      sizes_json, product_data.photo, True))
                
                product_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Создан товар {product_id}: {product_data.title}")
                return product_id
            except Exception as e:
                logger.error(f"Ошибка создания товара: {e}")
                return None

# Создаем глобальный экземпляр базы данных
db = Database()

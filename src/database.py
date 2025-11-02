"""
Работа с базой данных
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from src.config import DATABASE_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def get_db():
    """Контекстный менеджер для работы с БД"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_database():
    """Инициализация базы данных"""
    logger.info("Инициализация базы данных...")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                price REAL NOT NULL,
                image_url TEXT DEFAULT '',
                gallery_images TEXT DEFAULT '[]',
                sizes TEXT DEFAULT '[]',
                category TEXT DEFAULT '',
                brand TEXT DEFAULT '',
                color TEXT DEFAULT '',
                material TEXT DEFAULT '',
                weight TEXT DEFAULT '',
                dimensions TEXT DEFAULT '',
                in_stock INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для товаров
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_in_stock ON products(in_stock)')
        
        # Таблица клиентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для клиентов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_telegram_id ON customers(telegram_id)')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number INTEGER UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_address TEXT,
                telegram_id TEXT,
                telegram_username TEXT,
                items TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Индексы для заказов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)')
        
        # Таблица отзывов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                rating INTEGER NOT NULL,
                comment TEXT,
                is_approved INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Индексы для отзывов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_approved ON reviews(is_approved)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating)')
        
        # Таблица сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                message TEXT,
                is_from_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        logger.info("База данных инициализирована успешно")


def migrate_old_databases():
    """
    Миграция данных из старых баз данных
    """
    logger.info("Проверка миграции данных...")
    
    # Миграция из shop.db
    try:
        old_shop_db = 'shop.db'
        if sqlite3.connect(old_shop_db).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            logger.info(f"Обнаружена старая БД: {old_shop_db}")
            
            with sqlite3.connect(old_shop_db) as old_conn:
                with get_db() as new_conn:
                    # Копируем товары если их нет
                    cursor = new_conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM products')
                    if cursor.fetchone()[0] == 0:
                        old_cursor = old_conn.cursor()
                        old_cursor.execute('SELECT * FROM products')
                        products = old_cursor.fetchall()
                        
                        for product in products:
                            cursor.execute('''
                                INSERT INTO products 
                                (title, description, price, image_url, gallery_images, 
                                 sizes, category, brand, color, material, weight, dimensions, 
                                 in_stock, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', product[1:])
                        
                        logger.info(f"Мигрировано {len(products)} товаров из {old_shop_db}")
    except Exception as e:
        logger.warning(f"Ошибка миграции shop.db: {e}")
    
    # Миграция из customer_support.db
    try:
        old_support_db = 'customer_support.db'
        if sqlite3.connect(old_support_db).execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
            logger.info(f"Обнаружена старая БД: {old_support_db}")
            
            with sqlite3.connect(old_support_db) as old_conn:
                with get_db() as new_conn:
                    cursor = new_conn.cursor()
                    
                    # Копируем клиентов
                    cursor.execute('SELECT COUNT(*) FROM customers')
                    if cursor.fetchone()[0] == 0:
                        old_cursor = old_conn.cursor()
                        try:
                            old_cursor.execute('SELECT * FROM customers')
                            customers = old_cursor.fetchall()
                            
                            for customer in customers:
                                cursor.execute('''
                                    INSERT INTO customers 
                                    (telegram_id, username, first_name, last_name, 
                                     is_admin, created_at, last_activity)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', customer[1:])
                            
                            logger.info(f"Мигрировано {len(customers)} клиентов")
                        except Exception as e:
                            logger.warning(f"Ошибка миграции клиентов: {e}")
    except Exception as e:
        logger.warning(f"Ошибка миграции customer_support.db: {e}")


if __name__ == '__main__':
    init_database()
    migrate_old_databases()
    logger.info("Миграция завершена")

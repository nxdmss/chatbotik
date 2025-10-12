#!/usr/bin/env python3
"""
🏢 PROFESSIONAL E-COMMERCE PLATFORM
===================================
Современная платформа электронной коммерции
с интеграцией Telegram бота и веб-интерфейсом

Архитектура:
- FastAPI для API
- SQLite для данных  
- Асинхронная обработка
- Безопасность и валидация
"""

import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import base64
from PIL import Image
import io

# Конфигурация
DATABASE_PATH = "shop.db"
UPLOADS_DIR = "uploads"
STATIC_DIR = "static"
PORT = 8000

# Создаем необходимые директории
Path(UPLOADS_DIR).mkdir(exist_ok=True)
Path(STATIC_DIR).mkdir(exist_ok=True)

# FastAPI приложение
app = FastAPI(
    title="Professional E-Commerce Platform",
    description="Современная платформа электронной коммерции",
    version="1.0.0"
)

# CORS middleware
app.middleware("cors")(CORSMiddleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
))

# Модели данных
class ProductCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field(default="general", max_length=50)

class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)

class Product(BaseModel):
    id: int
    title: str
    price: int
    description: Optional[str]
    category: str
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime

class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[CartItem]
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_phone: str = Field(..., min_length=1, max_length=20)

# База данных
def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Таблица продуктов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'general',
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица заказов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            total_amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица элементов заказа
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    # Добавляем тестовые данные
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        test_products = [
            ("iPhone 15 Pro", 99999, "Новейший смартфон Apple", "electronics"),
            ("MacBook Air M3", 129999, "Мощный ноутбук для работы", "electronics"),
            ("Nike Air Max", 8999, "Спортивные кроссовки", "clothing"),
            ("Кофе Starbucks", 299, "Премиальный кофе", "food"),
            ("Книга Python", 1999, "Программирование на Python", "books")
        ]
        
        for title, price, description, category in test_products:
            cursor.execute("""
                INSERT INTO products (title, price, description, category)
                VALUES (?, ?, ?, ?)
            """, (title, price, description, category))
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# Инициализируем базу данных
init_database()

# Вспомогательные функции
def get_db():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_image(image_data: str, filename: str) -> str:
    """Сохранение изображения"""
    try:
        # Декодируем base64
        if ',' in image_data:
            header, data = image_data.split(',', 1)
        else:
            data = image_data
        
        image_bytes = base64.b64decode(data)
        
        # Создаем изображение и оптимизируем
        image = Image.open(io.BytesIO(image_bytes))
        
        # Конвертируем в RGB если нужно
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        # Изменяем размер для оптимизации
        image.thumbnail((800, 600), Image.Resampling.LANCZOS)
        
        # Сохраняем
        filepath = Path(UPLOADS_DIR) / filename
        image.save(filepath, 'JPEG', quality=85, optimize=True)
        
        return f"/uploads/{filename}"
    except Exception as e:
        print(f"❌ Ошибка сохранения изображения: {e}")
        return ""

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Главная страница"""
    return FileResponse("static/index.html")

@app.get("/api/products", response_model=List[Product])
async def get_products(category: Optional[str] = None):
    """Получение списка продуктов"""
    conn = get_db()
    cursor = conn.cursor()
    
    if category:
        cursor.execute("""
            SELECT * FROM products 
            WHERE category = ? 
            ORDER BY created_at DESC
        """, (category,))
    else:
        cursor.execute("""
            SELECT * FROM products 
            ORDER BY created_at DESC
        """)
    
    products = cursor.fetchall()
    conn.close()
    
    return [Product(**dict(product)) for product in products]

@app.post("/api/products", response_model=Product)
async def create_product(product: ProductCreate, image_data: Optional[str] = Form(None)):
    """Создание нового продукта"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Обработка изображения
    image_url = ""
    if image_data:
        filename = f"product_{uuid.uuid4().hex[:8]}.jpg"
        image_url = save_image(image_data, filename)
    
    # Создаем продукт
    cursor.execute("""
        INSERT INTO products (title, price, description, category, image_url)
        VALUES (?, ?, ?, ?, ?)
    """, (product.title, product.price, product.description, product.category, image_url))
    
    product_id = cursor.lastrowid
    conn.commit()
    
    # Получаем созданный продукт
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    new_product = cursor.fetchone()
    conn.close()
    
    return Product(**dict(new_product))

@app.put("/api/products/{product_id}", response_model=Product)
async def update_product(product_id: int, product_update: ProductUpdate):
    """Обновление продукта"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем существование продукта
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Обновляем поля
    update_fields = []
    values = []
    
    if product_update.title is not None:
        update_fields.append("title = ?")
        values.append(product_update.title)
    
    if product_update.price is not None:
        update_fields.append("price = ?")
        values.append(product_update.price)
    
    if product_update.description is not None:
        update_fields.append("description = ?")
        values.append(product_update.description)
    
    if product_update.category is not None:
        update_fields.append("category = ?")
        values.append(product_update.category)
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(product_id)
        
        query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    # Получаем обновленный продукт
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    updated_product = cursor.fetchone()
    conn.close()
    
    return Product(**dict(updated_product))

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    """Удаление продукта"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем существование продукта
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Удаляем изображение если есть
    if product['image_url']:
        image_path = Path(UPLOADS_DIR) / product['image_url'].split('/')[-1]
        if image_path.exists():
            image_path.unlink()
    
    # Удаляем продукт
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Продукт удален"}

@app.get("/api/categories")
async def get_categories():
    """Получение списка категорий"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

@app.post("/api/orders")
async def create_order(order: OrderCreate):
    """Создание заказа"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Вычисляем общую сумму
    total_amount = 0
    for item in order.items:
        cursor.execute("SELECT price FROM products WHERE id = ?", (item.product_id,))
        product = cursor.fetchone()
        if not product:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Продукт с ID {item.product_id} не найден")
        total_amount += product['price'] * item.quantity
    
    # Создаем заказ
    cursor.execute("""
        INSERT INTO orders (customer_name, customer_phone, total_amount)
        VALUES (?, ?, ?)
    """, (order.customer_name, order.customer_phone, total_amount))
    
    order_id = cursor.lastrowid
    
    # Создаем элементы заказа
    for item in order.items:
        cursor.execute("SELECT price FROM products WHERE id = ?", (item.product_id,))
        price = cursor.fetchone()['price']
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, item.product_id, item.quantity, price))
    
    conn.commit()
    conn.close()
    
    return {"order_id": order_id, "total_amount": total_amount}

# Статические файлы
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    print("🚀 ЗАПУСК PROFESSIONAL E-COMMERCE PLATFORM")
    print("=" * 50)
    print(f"🌐 Сервер: http://localhost:{PORT}")
    print(f"📊 API документация: http://localhost:{PORT}/docs")
    print(f"💾 База данных: {DATABASE_PATH}")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)

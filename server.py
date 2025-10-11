"""
Чистый FastAPI сервер для Telegram WebApp магазина
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel, ValidationError

# Импортируем наши модули
from models import Product, OrderCreate, Order
from logger_config import setup_logging, bot_logger
from database import db

# Настраиваем логирование
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = bot_logger.logger

app = FastAPI(
    title="Telegram Shop WebApp API",
    description="API для Telegram WebApp магазина",
    version="2.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEBAPP_DIR = os.path.join(os.path.dirname(__file__), 'webapp')
UPLOADS_DIR = os.path.join(WEBAPP_DIR, 'uploads')
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

# Монтируем статические файлы
app.mount('/webapp/static', StaticFiles(directory=WEBAPP_DIR), name='webapp_static')

# ======================
# 🔹 Вспомогательные функции
# ======================

def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{price:.2f} ₽"

def is_admin(user_id: str) -> bool:
    """Проверка, является ли пользователь администратором"""
    user_id_str = str(user_id)
    
    # Главный администратор всегда имеет права
    if user_id_str == "1593426947":
        return True
    
    try:
        with open('webapp/admins.json', 'r', encoding='utf-8') as f:
            admins_data = json.load(f)
            return user_id_str in admins_data.get('admins', [])
    except:
        return False

# ======================
# 🔹 Основные маршруты
# ======================

@app.get("/")
async def root():
    """Главная страница"""
    return FileResponse(os.path.join(WEBAPP_DIR, 'index.html'))

@app.get("/webapp/")
async def webapp():
    """WebApp главная страница"""
    return FileResponse(os.path.join(WEBAPP_DIR, 'index.html'))

# ======================
# 🔹 API для товаров
# ======================

@app.get("/webapp/products.json")
async def get_products():
    """Получить список товаров"""
    try:
        products = db.get_products()
        
        # Если товаров нет, добавляем примеры
        if not products:
            sample_products = [
                {
                    "id": 1,
                    "title": "Кроссовки Nike Air Max",
                    "description": "Удобные кроссовки для спорта и повседневной носки",
                    "price": 8999.0,
                    "sizes": ["40", "41", "42", "43", "44"],
                    "photo": "/webapp/static/uploads/sample1.jpg",
                    "is_active": True
                },
                {
                    "id": 2,
                    "title": "Джинсы Levis 501",
                    "description": "Классические джинсы прямого кроя",
                    "price": 5999.0,
                    "sizes": ["28", "30", "32", "34", "36"],
                    "photo": "/webapp/static/uploads/sample2.jpg",
                    "is_active": True
                },
                {
                    "id": 3,
                    "title": "Футболка Basic",
                    "description": "Мягкая хлопковая футболка",
                    "price": 1999.0,
                    "sizes": ["S", "M", "L", "XL"],
                    "photo": "/webapp/static/uploads/sample3.jpg",
                    "is_active": True
                }
            ]
            
            # Добавляем примеры в базу данных
            for product_data in sample_products:
                product = Product(**product_data)
                await db.create_product(product)
            
            products = db.get_products()
        
        return {"products": products}
        
    except Exception as e:
        logger.error("Error getting products", error=str(e))
        return {"products": []}

@app.get("/webapp/admins.json")
async def get_admins():
    """Получить список администраторов"""
    try:
        with open('webapp/admins.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"admins": []}

# ======================
# 🔹 API для заказов
# ======================

@app.post("/webapp/orders")
async def create_order(order_data: OrderCreate):
    """Создать новый заказ"""
    try:
        # Валидируем данные заказа
        order_id = await db.create_order("webapp_user", order_data)
        
        return {
            "success": True,
            "order_id": order_id,
            "message": "Заказ создан успешно"
        }
        
    except Exception as e:
        logger.error("Error creating order", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка при создании заказа")

# ======================
# 🔹 Админ API
# ======================

@app.get("/webapp/admin/products")
async def get_admin_products(user_id: str = None):
    """Получить все товары для админа"""
    try:
        if not is_admin(user_id):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        products = db.get_products(include_inactive=True)
        return {"products": products}
        
    except Exception as e:
        logger.error("Error getting admin products", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка при получении товаров")

@app.post("/webapp/admin/products")
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    sizes: str = Form(""),
    photo: UploadFile = File(None),
    user_id: str = Form(None)
):
    """Создать новый товар"""
    try:
        if not is_admin(user_id):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Обрабатываем размеры
        sizes_list = [s.strip() for s in sizes.split(',') if s.strip()] if sizes else []
        
        # Сохраняем фото
        photo_url = None
        if photo:
            filename = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
            file_path = os.path.join(UPLOADS_DIR, filename)
            
            with open(file_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
            
            photo_url = f"/webapp/static/uploads/{filename}"
        
        # Создаем товар
        product_data = Product(
            title=title,
            description=description,
            price=price,
            sizes=sizes_list,
            photo=photo_url or "/webapp/static/uploads/default.jpg",
            is_active=True
        )
        
        product_id = await db.create_product(product_data)
        
        return {
            "success": True,
            "product_id": product_id,
            "message": "Товар создан успешно"
        }
        
    except Exception as e:
        logger.error("Error creating product", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка при создании товара")

@app.put("/webapp/admin/products/{product_id}")
async def update_product(
    product_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    sizes: str = Form(""),
    photo: UploadFile = File(None),
    user_id: str = Form(None)
):
    """Обновить товар"""
    try:
        if not is_admin(user_id):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Обрабатываем размеры
        sizes_list = [s.strip() for s in sizes.split(',') if s.strip()] if sizes else []
        
        # Сохраняем фото если загружено
        photo_url = None
        if photo:
            filename = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
            file_path = os.path.join(UPLOADS_DIR, filename)
            
            with open(file_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
            
            photo_url = f"/webapp/static/uploads/{filename}"
        
        # Обновляем товар
        success = await db.update_product(
            product_id,
            title=title,
            description=description,
            price=price,
            sizes=sizes_list,
            photo=photo_url
        )
        
        if success:
            return {"success": True, "message": "Товар обновлен успешно"}
        else:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
    except Exception as e:
        logger.error("Error updating product", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка при обновлении товара")

@app.delete("/webapp/admin/products/{product_id}")
async def delete_product(product_id: int, user_id: str = None):
    """Удалить товар (деактивировать)"""
    try:
        if not is_admin(user_id):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        success = await db.update_product_status(product_id, False)
        
        if success:
            return {"success": True, "message": "Товар удален успешно"}
        else:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
    except Exception as e:
        logger.error("Error deleting product", error=str(e))
        raise HTTPException(status_code=500, detail="Ошибка при удалении товара")

# ======================
# 🔹 Статус и метрики
# ======================

@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    try:
        products_count = len(db.get_products())
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "products_count": products_count
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Получить метрики сервера"""
    try:
        products = db.get_products()
        orders = db.get_all_orders()
        
        return {
            "products_count": len(products),
            "orders_count": len(orders),
            "total_revenue": sum(order.get('total_amount', 0) for order in orders),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Error getting metrics", error=str(e))
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

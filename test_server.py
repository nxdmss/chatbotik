#!/usr/bin/env python3
"""
Простой тестовый сервер для отладки веб-приложения
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pathlib import Path
from datetime import datetime
import uvicorn

app = FastAPI(title="Test Shop API")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка путей
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), 'webapp')
UPLOADS_DIR = os.path.join(WEBAPP_DIR, 'uploads')
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

# Монтируем статические файлы
app.mount('/webapp/static', StaticFiles(directory=WEBAPP_DIR), name='webapp_static')

# Простые товары для тестирования
test_products = [
    {
        "id": 1,
        "title": "Тестовые кроссовки",
        "description": "Кроссовки для тестирования",
        "price": 5000,
        "sizes": ["40", "41", "42"],
        "photo": "/webapp/static/uploads/default.jpg",
        "is_active": True
    },
    {
        "id": 2,
        "title": "Тестовые кеды",
        "description": "Кеды для тестирования",
        "price": 3000,
        "sizes": ["38", "39", "40"],
        "photo": "/webapp/static/uploads/default.jpg",
        "is_active": True
    }
]

@app.get("/")
async def root():
    return {"message": "Test Shop API is running!"}

@app.get("/webapp/products.json")
async def get_products():
    """Получить список товаров"""
    print("📦 Запрос товаров")
    return test_products

@app.get("/webapp/admin/products")
async def get_admin_products(user_id: str = None):
    """Получить товары для админа"""
    print(f"👑 Запрос админ-товаров для user_id: {user_id}")
    return {"products": test_products}

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
    print(f"➕ Создание товара: {title}")
    
    # Обрабатываем размеры
    sizes_list = [s.strip() for s in sizes.split(',') if s.strip()] if sizes else []
    
    # Создаем новый товар
    new_product = {
        "id": len(test_products) + 1,
        "title": title,
        "description": description,
        "price": price,
        "sizes": sizes_list,
        "photo": "/webapp/static/uploads/default.jpg",
        "is_active": True
    }
    
    test_products.append(new_product)
    
    print(f"✅ Товар создан: {new_product}")
    return {
        "success": True,
        "product_id": new_product["id"],
        "message": "Товар создан успешно"
    }

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
    print(f"✏️ Обновление товара {product_id}: {title}")
    
    # Находим товар
    product = next((p for p in test_products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Обрабатываем размеры
    sizes_list = [s.strip() for s in sizes.split(',') if s.strip()] if sizes else []
    
    # Обновляем товар
    product.update({
        "title": title,
        "description": description,
        "price": price,
        "sizes": sizes_list
    })
    
    print(f"✅ Товар обновлен: {product}")
    return {"success": True, "message": "Товар обновлен успешно"}

@app.delete("/webapp/admin/products/{product_id}")
async def delete_product(product_id: int, user_id: str = None):
    """Удалить товар"""
    print(f"🗑️ Удаление товара {product_id}")
    
    # Находим товар
    product = next((p for p in test_products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Деактивируем товар
    product["is_active"] = False
    
    print(f"✅ Товар деактивирован: {product}")
    return {"success": True, "message": "Товар удален успешно"}

@app.get("/webapp/static/uploads/default.jpg")
async def get_default_image():
    """Возвращаем заглушку для изображения"""
    return FileResponse("webapp/static/uploads/default.jpg", media_type="image/jpeg")

if __name__ == "__main__":
    print("🚀 Запуск тестового сервера...")
    print("📱 Откройте http://localhost:8000/test_webapp.html для тестирования")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

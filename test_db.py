#!/usr/bin/env python3
"""
Тест базы данных
"""

from database import db

print("🔍 Тестируем базу данных...")

# Получаем все товары
products = db.get_products(active_only=False)
print(f"📊 Найдено товаров: {len(products)}")

for product in products:
    print(f"  - ID: {product['id']}, Название: {product['title']}, Активен: {product['is_active']}")

# Получаем только активные товары
active_products = db.get_products(active_only=True)
print(f"📊 Активных товаров: {len(active_products)}")

for product in active_products:
    print(f"  - ID: {product['id']}, Название: {product['title']}, Активен: {product['is_active']}")

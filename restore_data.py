#!/usr/bin/env python3
"""
Скрипт для принудительного восстановления данных
Используется когда данные сбрасываются после перезапуска
"""

import os
import json
import sqlite3
import shutil
from datetime import datetime

DB_PATH = "shop.db"
BACKUP_DIR = "db_backups"
JSON_BACKUP = "products_backup.json"

def restore_from_json():
    """Восстановить данные из JSON файла"""
    try:
        if not os.path.exists(JSON_BACKUP):
            print(f"❌ JSON бэкап не найден: {JSON_BACKUP}")
            return False
        
        print(f"🔄 Восстанавливаем данные из {JSON_BACKUP}...")
        
        with open(JSON_BACKUP, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Создаем БД если её нет
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу если её нет
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
            
            # Очищаем таблицу
            cursor.execute("DELETE FROM products")
            
            # Восстанавливаем данные
            for product in products:
                created_at = product.get("created_at", datetime.now().isoformat())
                cursor.execute("""
                    INSERT INTO products (id, title, description, price, sizes, photo, is_active, created_at)
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
        return True
        
    except Exception as e:
        print(f"❌ Ошибка восстановления из JSON: {e}")
        return False

def restore_from_db_backup():
    """Восстановить данные из DB бэкапа"""
    try:
        if not os.path.exists(BACKUP_DIR):
            print(f"❌ Директория бэкапов не найдена: {BACKUP_DIR}")
            return False
        
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        if not backups:
            print("❌ DB бэкапы не найдены")
            return False
        
        # Выбираем последний бэкап
        backups.sort(reverse=True)
        latest_backup = os.path.join(BACKUP_DIR, backups[0])
        
        print(f"🔄 Восстанавливаем из DB бэкапа: {latest_backup}")
        
        # Копируем бэкап
        shutil.copy2(latest_backup, DB_PATH)
        
        print(f"✅ Восстановлено из DB бэкапа")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка восстановления из DB бэкапа: {e}")
        return False

def main():
    """Основная функция восстановления"""
    print("🚀 Запуск восстановления данных...")
    
    # Проверяем, есть ли данные в БД
    if os.path.exists(DB_PATH):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products")
                count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"📦 База данных уже содержит {count} товаров")
                return
        except:
            pass
    
    # Пытаемся восстановить из JSON
    if restore_from_json():
        return
    
    # Если JSON не сработал, пытаемся из DB бэкапа
    if restore_from_db_backup():
        return
    
    print("❌ Не удалось восстановить данные")
    print("💡 Создайте товары заново или проверьте наличие бэкапов")

if __name__ == "__main__":
    main()

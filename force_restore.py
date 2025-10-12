#!/usr/bin/env python3
"""
Принудительное восстановление данных
Используется когда обычное восстановление не работает
"""

import os
import json
import sqlite3
import shutil
from datetime import datetime

DB_PATH = "shop.db"
BACKUP_DIR = "db_backups"
JSON_BACKUP = "products_backup.json"

def force_restore():
    """Принудительное восстановление данных"""
    print("🚀 ПРИНУДИТЕЛЬНОЕ ВОССТАНОВЛЕНИЕ ДАННЫХ")
    print("=" * 50)
    
    # 1. Проверяем текущее состояние
    print("\n📊 Проверяем текущее состояние:")
    
    if os.path.exists(DB_PATH):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
                active_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM products")
                total_count = cursor.fetchone()[0]
            print(f"   📦 БД: {total_count} товаров всего, {active_count} активных")
        except:
            print("   ❌ Ошибка чтения БД")
    else:
        print("   ❌ БД не существует")
    
    # 2. Проверяем JSON бэкап
    if os.path.exists(JSON_BACKUP):
        try:
            with open(JSON_BACKUP, 'r', encoding='utf-8') as f:
                products = json.load(f)
            print(f"   📄 JSON бэкап: {len(products)} товаров")
        except:
            print("   ❌ Ошибка чтения JSON бэкапа")
    else:
        print("   ❌ JSON бэкап не найден")
    
    # 3. Проверяем DB бэкапы
    if os.path.exists(BACKUP_DIR):
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        print(f"   💾 DB бэкапы: {len(backups)} файлов")
        if backups:
            backups.sort(reverse=True)
            print(f"   📅 Последний: {backups[0]}")
    else:
        print("   ❌ Папка DB бэкапов не найдена")
    
    # 4. Восстанавливаем данные
    print("\n🔄 Восстанавливаем данные:")
    
    restored = False
    
    # Сначала пытаемся из JSON
    if os.path.exists(JSON_BACKUP) and not restored:
        try:
            print("   📄 Восстанавливаем из JSON...")
            with open(JSON_BACKUP, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            # Создаем БД если её нет
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Создаем таблицу
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
            
            print(f"   ✅ Восстановлено {len(products)} товаров из JSON")
            restored = True
            
        except Exception as e:
            print(f"   ❌ Ошибка восстановления из JSON: {e}")
    
    # Если JSON не сработал, пытаемся из DB бэкапа
    if not restored and os.path.exists(BACKUP_DIR):
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        if backups:
            try:
                backups.sort(reverse=True)
                latest_backup = os.path.join(BACKUP_DIR, backups[0])
                print(f"   💾 Восстанавливаем из DB бэкапа: {latest_backup}")
                
                # Удаляем текущую БД
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                
                # Копируем бэкап
                shutil.copy2(latest_backup, DB_PATH)
                print("   ✅ Восстановлено из DB бэкапа")
                restored = True
                
            except Exception as e:
                print(f"   ❌ Ошибка восстановления из DB бэкапа: {e}")
    
    # 5. Проверяем результат
    print("\n📊 Проверяем результат:")
    
    if os.path.exists(DB_PATH):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
                active_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM products")
                total_count = cursor.fetchone()[0]
            print(f"   📦 БД: {total_count} товаров всего, {active_count} активных")
            
            if active_count > 0:
                print("   ✅ ВОССТАНОВЛЕНИЕ УСПЕШНО!")
            else:
                print("   ⚠️ Восстановление выполнено, но активных товаров нет")
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки результата: {e}")
    else:
        print("   ❌ БД не создана")
    
    print("\n" + "=" * 50)
    
    if restored:
        print("🎉 Восстановление завершено!")
    else:
        print("❌ Восстановление не удалось")
        print("💡 Создайте товары заново")

if __name__ == "__main__":
    force_restore()

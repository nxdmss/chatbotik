#!/usr/bin/env python3
"""
Скрипт для резервного копирования базы данных
Автоматически создает backup перед любыми операциями
"""

import os
import shutil
import sqlite3
from datetime import datetime
import json

DB_PATH = "shop.db"
BACKUP_DIR = "db_backups"
JSON_BACKUP = "products_backup.json"

def ensure_backup_dir():
    """Создать директорию для бэкапов"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"✅ Создана директория для бэкапов: {BACKUP_DIR}")

def backup_database():
    """Создать резервную копию базы данных"""
    try:
        if not os.path.exists(DB_PATH):
            print("⚠️ База данных не найдена")
            return None
        
        ensure_backup_dir()
        
        # Создаем timestamp для имени файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"shop_backup_{timestamp}.db")
        
        # Копируем файл базы данных
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Создан бэкап БД: {backup_path}")
        
        # Также экспортируем в JSON для удобства
        export_to_json()
        
        # Удаляем старые бэкапы (оставляем только последние 10)
        cleanup_old_backups()
        
        return backup_path
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return None

def export_to_json():
    """Экспортировать товары в JSON"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY id")
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
                    "is_active": bool(row["is_active"]),
                    "created_at": row["created_at"]
                }
                products.append(product)
            
            # Сохраняем в JSON
            with open(JSON_BACKUP, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Экспорт в JSON: {JSON_BACKUP} ({len(products)} товаров)")
            return products
    except Exception as e:
        print(f"❌ Ошибка экспорта в JSON: {e}")
        return []

def restore_from_json():
    """Восстановить товары из JSON"""
    try:
        if not os.path.exists(JSON_BACKUP):
            print(f"⚠️ Файл {JSON_BACKUP} не найден")
            return False
        
        with open(JSON_BACKUP, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Очищаем таблицу
            cursor.execute("DELETE FROM products")
            
            # Восстанавливаем товары
            for product in products:
                # Получаем created_at или используем текущее время
                created_at = product.get("created_at", datetime.now().isoformat())
                
                cursor.execute("""
                    INSERT INTO products (id, title, description, price, sizes, photo, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product["id"],
                    product["title"],
                    product["description"],
                    product["price"],
                    json.dumps(product["sizes"]),
                    product["photo"],
                    1 if product.get("is_active", True) else 0,
                    created_at
                ))
            
            conn.commit()
            print(f"✅ Восстановлено {len(products)} товаров из JSON")
            return True
    except Exception as e:
        print(f"❌ Ошибка восстановления из JSON: {e}")
        return False

def cleanup_old_backups(keep_count=10):
    """Удалить старые бэкапы, оставить только последние"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        backups.sort(reverse=True)  # Новые первыми
        
        # Удаляем старые
        for backup in backups[keep_count:]:
            backup_path = os.path.join(BACKUP_DIR, backup)
            os.remove(backup_path)
            print(f"🗑️ Удален старый бэкап: {backup}")
    except Exception as e:
        print(f"❌ Ошибка очистки старых бэкапов: {e}")

def restore_latest_backup():
    """Восстановить последний бэкап"""
    try:
        if not os.path.exists(BACKUP_DIR):
            print("⚠️ Нет бэкапов")
            return False
        
        backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
        if not backups:
            print("⚠️ Нет бэкапов")
            return False
        
        backups.sort(reverse=True)
        latest_backup = os.path.join(BACKUP_DIR, backups[0])
        
        shutil.copy2(latest_backup, DB_PATH)
        print(f"✅ Восстановлена БД из: {latest_backup}")
        return True
    except Exception as e:
        print(f"❌ Ошибка восстановления бэкапа: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backup":
            backup_database()
        elif command == "export":
            export_to_json()
        elif command == "restore":
            restore_latest_backup()
        elif command == "restore-json":
            restore_from_json()
        else:
            print("Использование:")
            print("  python backup_db.py backup        - создать бэкап")
            print("  python backup_db.py export        - экспорт в JSON")
            print("  python backup_db.py restore       - восстановить из последнего бэкапа")
            print("  python backup_db.py restore-json  - восстановить из JSON")
    else:
        # По умолчанию создаем бэкап и экспорт
        backup_database()


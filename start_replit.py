#!/usr/bin/env python3
"""
Скрипт запуска для Replit Preview Run
"""

import os
import sys
import subprocess
import threading
import time

def start_server():
    """Запуск веб-сервера"""
    print("🌐 Запускаем веб-сервер...")
    try:
        # Устанавливаем переменную окружения для Replit
        os.environ['REPLIT_DB_URL'] = ''
        
        # Запускаем сервер
        subprocess.run([
            sys.executable, "simple_shop.py"
        ], check=True)
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")

def start_bot():
    """Запуск бота"""
    print("🤖 Запускаем бота...")
    try:
        subprocess.run([
            sys.executable, "bot.py"
        ], check=True)
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

if __name__ == "__main__":
    print("🚀 ЗАПУСК В REPLIT")
    print("=" * 30)
    
    # Создаем папки
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("db_backups", exist_ok=True)
    
    # Запускаем сервер в фоне
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Ждем запуска сервера
    time.sleep(3)
    
    print("✅ Сервер запущен на http://localhost:8000")
    print("🤖 Запускаем бота...")
    
    # Запускаем бота
    start_bot()

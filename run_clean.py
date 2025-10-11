#!/usr/bin/env python3
"""
Скрипт для запуска бота и сервера
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Проверка зависимостей"""
    try:
        import aiogram
        import fastapi
        import uvicorn
        import pydantic
        import structlog
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def check_env():
    """Проверка переменных окружения"""
    required_vars = ["BOT_TOKEN", "WEBAPP_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Создайте файл .env с необходимыми переменными")
        return False
    
    print("✅ Переменные окружения настроены")
    return True

def check_files():
    """Проверка необходимых файлов"""
    required_files = [
        "bot_clean.py",
        "server_clean.py", 
        "models.py",
        "database.py",
        "logger_config.py",
        "error_handlers.py",
        "webapp/index.html",
        "webapp/app.js",
        "webapp/styles.css"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("✅ Все необходимые файлы найдены")
    return True

async def run_bot():
    """Запуск бота"""
    try:
        print("🤖 Запуск бота...")
        from bot_clean import main as bot_main
        await bot_main()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

def run_server():
    """Запуск сервера"""
    try:
        print("🌐 Запуск сервера...")
        import uvicorn
        from server_clean import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

async def main():
    """Основная функция"""
    print("🚀 Запуск приложения...")
    
    # Проверки
    if not check_requirements():
        sys.exit(1)
    
    if not check_env():
        sys.exit(1)
    
    if not check_files():
        sys.exit(1)
    
    print("✅ Все проверки пройдены")
    
    # Запускаем бота и сервер параллельно
    try:
        await asyncio.gather(
            run_bot(),
            asyncio.to_thread(run_server)
        )
    except KeyboardInterrupt:
        print("\n🛑 Остановка приложения...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        print("👋 Приложение остановлено")

if __name__ == "__main__":
    asyncio.run(main())

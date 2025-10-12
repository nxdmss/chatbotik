#!/usr/bin/env python3
"""
🚀 PROFESSIONAL E-COMMERCE PLATFORM - SIMPLE VERSION
====================================================
Простая версия без Telegram бота для быстрого запуска
"""

import os
import sys
from pathlib import Path

import uvicorn
from app import app

def main():
    """Запуск только веб-сервера"""
    print("🚀 ЗАПУСК PROFESSIONAL E-COMMERCE PLATFORM")
    print("=" * 50)
    
    # Конфигурация
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Создаем необходимые директории
    directories = ['uploads', 'static', 'db_backups']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Директории созданы")
    
    # Показываем статус
    print(f"🌐 Веб-сервер: http://{host}:{port}")
    print(f"📚 API документация: http://{host}:{port}/docs")
    print(f"💾 База данных: shop.db")
    print(f"📁 Загрузки: uploads/")
    print("=" * 50)
    print("🎉 Платформа запущена!")
    print("💡 Для запуска бота установите BOT_TOKEN")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    # Запускаем сервер
    try:
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level="info",
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

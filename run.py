#!/usr/bin/env python3
"""
Скрипт для запуска улучшенной версии Telegram бота и WebApp сервера
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
import signal
import time

def check_requirements():
    """Проверка установленных зависимостей"""
    try:
        import aiogram
        import fastapi
        import pydantic
        import structlog
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def check_env_file():
    """Проверка наличия файла конфигурации"""
    if not os.path.exists('.env'):
        if os.path.exists('config_example.env'):
            print("⚠️  Файл .env не найден. Скопируйте config_example.env в .env и настройте его")
            return False
        else:
            print("❌ Файл .env не найден и нет примера конфигурации")
            return False
    
    # Проверяем обязательные переменные
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['BOT_TOKEN', 'ADMINS']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        return False
    
    print("✅ Конфигурация корректна")
    return True

def create_directories():
    """Создание необходимых директорий"""
    directories = ['logs', 'webapp/uploads']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Директории созданы")

def run_bot():
    """Запуск бота"""
    print("🤖 Запуск улучшенного Telegram бота...")
    try:
        from bot_improved import main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return False
    return True

def run_server():
    """Запуск WebApp сервера"""
    print("🌐 Запуск WebApp сервера...")
    try:
        import uvicorn
        from server_improved import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return False
    return True

def run_both():
    """Запуск бота и сервера одновременно"""
    print("🚀 Запуск бота и сервера одновременно...")
    
    # Создаем процессы
    bot_process = None
    server_process = None
    
    try:
        # Запускаем сервер в отдельном процессе
        server_process = subprocess.Popen([
            sys.executable, '-c', 
            'import uvicorn; from server_improved import app; uvicorn.run(app, host="0.0.0.0", port=8000)'
        ])
        
        # Небольшая задержка для запуска сервера
        time.sleep(2)
        
        # Запускаем бота
        from bot_improved import main
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка всех процессов...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        # Останавливаем процессы
        if server_process:
            server_process.terminate()
            server_process.wait()
        print("✅ Все процессы остановлены")

def main():
    """Главная функция"""
    print("=" * 50)
    print("🛍️  Улучшенный Telegram Shop Bot")
    print("=" * 50)
    
    # Проверки
    if not check_requirements():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)
    
    create_directories()
    
    # Меню выбора
    print("\nВыберите режим запуска:")
    print("1. Только бот")
    print("2. Только WebApp сервер")
    print("3. Бот + WebApp сервер")
    print("4. Выход")
    
    while True:
        try:
            choice = input("\nВведите номер (1-4): ").strip()
            
            if choice == "1":
                run_bot()
                break
            elif choice == "2":
                run_server()
                break
            elif choice == "3":
                run_both()
                break
            elif choice == "4":
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор. Введите число от 1 до 4.")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            break

if __name__ == "__main__":
    main()

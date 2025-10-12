#!/usr/bin/env python3
"""
Главный файл для запуска магазина и бота в Replit
"""

import subprocess
import threading
import time
import os
import signal
import sys

def run_server():
    """Запуск веб-сервера магазина"""
    print("🌐 Запускаем веб-сервер магазина...")
    try:
        subprocess.run([sys.executable, "simple_shop.py"], check=True)
    except KeyboardInterrupt:
        print("🛑 Веб-сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

def run_bot():
    """Запуск Telegram бота"""
    print("🤖 Запускаем Telegram бота...")
    try:
        subprocess.run([sys.executable, "bot.py"], check=True)
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка бота: {e}")

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения...")
    sys.exit(0)

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК МАГАЗИНА И БОТА")
    print("=" * 50)
    
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создаем необходимые папки
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("db_backups", exist_ok=True)
    
    # Запускаем веб-сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Небольшая пауза для запуска сервера
    time.sleep(3)
    
    # Запускаем бота в основном потоке
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🎉 Работа завершена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
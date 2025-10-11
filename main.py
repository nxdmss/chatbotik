#!/usr/bin/env python3
"""
Главный файл для запуска в Replit
Автоматически запускает веб-сервер и телеграм бота
"""

import os
import sys
import threading
import time
import subprocess
from pathlib import Path

def print_banner():
    """Красивый баннер при запуске"""
    print("=" * 60)
    print("🚀 ЗАПУСК CHATBOTIK В REPLIT")
    print("=" * 60)
    print("📱 Веб-приложение: http://localhost:8000")
    print("🤖 Телеграм бот: Запускается...")
    print("🛍️ Система товаров: Готова к работе")
    print("=" * 60)

def start_web_server():
    """Запуск веб-сервера"""
    try:
        print("🌐 Запуск веб-сервера...")
        # Импортируем и запускаем идеальный сервер
        from perfect_server import start_server
        start_server()
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")
        print("🔄 Попытка запуска альтернативного сервера...")
        # Запускаем простой HTTP сервер как fallback
        try:
            os.chdir("webapp")
            subprocess.run([sys.executable, "-m", "http.server", "8000"])
        except Exception as e2:
            print(f"❌ Ошибка альтернативного сервера: {e2}")

def start_telegram_bot():
    """Запуск телеграм бота"""
    try:
        print("🤖 Запуск телеграм бота...")
        # Проверяем наличие токена
        if not os.path.exists('.env'):
            print("⚠️ Файл .env не найден, создаем пример...")
            with open('.env.example', 'w') as f:
                f.write("BOT_TOKEN=your_bot_token_here\n")
            print("📝 Создан файл .env.example с примером токена")
            return
        
        # Запускаем бота
        from bot import main as bot_main
        bot_main()
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать бота: {e}")
        print("📱 Веб-приложение работает независимо")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        print("📱 Веб-приложение работает независимо")

def main():
    """Главная функция"""
    print_banner()
    
    # Проверяем наличие файлов
    if not os.path.exists('perfect_server.py'):
        print("❌ Файл perfect_server.py не найден!")
        return
    
    if not os.path.exists('webapp'):
        print("❌ Папка webapp не найдена!")
        return
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Ждем немного, чтобы сервер запустился
    time.sleep(2)
    
    # Запускаем телеграм бота в отдельном потоке
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    
    print("✅ Все сервисы запущены!")
    print("🌐 Веб-приложение: http://localhost:8000")
    print("🛑 Для остановки нажмите Ctrl+C")
    
    try:
        # Держим основную программу запущенной
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервисов...")
        print("👋 До свидания!")

if __name__ == "__main__":
    main()

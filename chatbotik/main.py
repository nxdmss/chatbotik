#!/usr/bin/env python3
"""
🚀 ГЛАВНЫЙ ФАЙЛ ДЛЯ ЗАПУСКА ПРИЛОЖЕНИЯ
=====================================
Запускает и бота, и веб-сервер одновременно
"""

import os
import sys
import subprocess
import threading
import time
import signal

def run_web_server():
    """Запуск веб-сервера"""
    print("🌐 Запуск веб-сервера...")
    try:
        # Импортируем и запускаем веб-сервер из simple_telegram_bot.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from simple_telegram_bot import main as web_main
        web_main()
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")

def run_telegram_bot():
    """Запуск Telegram бота"""
    print("🤖 Запуск Telegram бота...")
    try:
        # Здесь можно добавить логику для запуска отдельного бота
        # Пока что веб-сервер уже включает в себя бота
        print("✅ Telegram бот интегрирован в веб-сервер")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения...")
    print("👋 Завершение работы приложения")
    sys.exit(0)

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ LOOK & GO")
    print("=" * 50)
    
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Проверяем наличие BOT_TOKEN
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            print("⚠️ BOT_TOKEN не найден в переменных окружения")
            print("💡 Установите переменную окружения BOT_TOKEN")
            print("📝 Пример: export BOT_TOKEN='your_bot_token_here'")
        else:
            print(f"✅ BOT_TOKEN найден: {bot_token[:10]}...")
        
        print("\n🎯 Запуск компонентов:")
        print("   🌐 Веб-сервер с интерфейсом")
        print("   🤖 Telegram бот (интегрированный)")
        print("   📱 WebApp для Telegram")
        print("\n" + "=" * 50)
        
        # Запускаем веб-сервер (который включает бота)
        run_web_server()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка по запросу пользователя")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        print("👋 Приложение завершено")

if __name__ == "__main__":
    main()

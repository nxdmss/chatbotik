#!/usr/bin/env python3
"""
🚀 ГЛАВНЫЙ ФАЙЛ ДЛЯ ЗАПУСКА ПРИЛОЖЕНИЯ
=====================================
Запускает и бота, и веб-сервер одновременно
Включает функции поддержки клиентов и отзывов
Совместим с python-telegram-bot 13.15 для Replit
🛒 ОБНОВЛЕНО: Улучшенная система корзины с валидацией
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
    """Запуск Telegram бота поддержки"""
    print("🤖 Запуск Telegram бота поддержки...")
    try:
        if not os.getenv('BOT_TOKEN'):
            print("⚠️ BOT_TOKEN не найден - бот поддержки отключен")
            print("💡 Установите переменную окружения BOT_TOKEN")
            return
        
        # Импортируем и запускаем бот без telegram библиотеки
        from no_telegram_bot import main as support_main
        support_main()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота поддержки: {e}")
        import traceback
        traceback.print_exc()

def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n🛑 Получен сигнал завершения...")
    print("👋 Завершение работы приложения")
    sys.exit(0)

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ LOOK & GO")
    print("🛒 С УЛУЧШЕННОЙ СИСТЕМОЙ КОРЗИНЫ")
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
        print("   🌐 Веб-сервер с интерфейсом магазина")
        print("   🤖 Telegram бот поддержки клиентов")
        print("   📱 WebApp для Telegram")
        print("   📞 Система поддержки и отзывов")
        print("   🛒 Улучшенная система корзины")
        print("      ✅ Валидация данных")
        print("      ✅ Обработка ошибок")
        print("      ✅ Синхронизация с localStorage")
        print("      ✅ Fallback механизмы")
        print("\n" + "=" * 50)
        
        # Запускаем веб-сервер в отдельном потоке
        web_server_thread = threading.Thread(target=run_web_server)
        web_server_thread.daemon = True
        web_server_thread.start()
        
        # Даем серверу немного времени на запуск
        time.sleep(2)
        
        # Запускаем бота поддержки в основном потоке
        run_telegram_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка по запросу пользователя")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Приложение завершено")

if __name__ == "__main__":
    main()
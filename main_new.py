#!/usr/bin/env python3
"""
🛍️ ИНТЕРНЕТ-МАГАЗИН С TELEGRAM MINI APP
=======================================
Главная точка входа приложения

Запуск:
    python main.py

Или через модуль:
    python -m src.main
"""

import sys
import signal
import threading
import time
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.config import BOT_TOKEN, PORT, validate_config
from src.utils.logger import setup_logger
from src.database import init_database, migrate_old_databases

logger = setup_logger(__name__)


def signal_handler(sig, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info("Получен сигнал завершения...")
    logger.info("Завершение работы приложения")
    sys.exit(0)


def run_web_server():
    """Запуск веб-сервера"""
    logger.info("🌐 Запуск веб-сервера...")
    try:
        # Импортируем после настройки логирования
        from simple_telegram_bot import main as web_main
        web_main()
    except Exception as e:
        logger.error(f"Ошибка запуска веб-сервера: {e}", exc_info=True)


def run_telegram_bot():
    """Запуск Telegram бота поддержки"""
    logger.info("🤖 Запуск Telegram бота поддержки...")
    
    if not BOT_TOKEN:
        logger.warning("⚠️ BOT_TOKEN не найден - бот поддержки отключен")
        logger.info("💡 Установите BOT_TOKEN в файле .env")
        return
    
    try:
        from no_telegram_bot import main as support_main
        support_main()
    except Exception as e:
        logger.error(f"Ошибка запуска бота поддержки: {e}", exc_info=True)


def main():
    """Главная функция"""
    print("=" * 60)
    print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ LOOK & GO")
    print("=" * 60)
    
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Валидируем конфигурацию
        try:
            validate_config()
            logger.info("✅ Конфигурация валидна")
        except ValueError as e:
            logger.error(f"❌ Ошибка конфигурации: {e}")
            logger.info("💡 Создайте файл .env на основе .env.example")
            return
        
        # Инициализируем базу данных
        logger.info("📊 Инициализация базы данных...")
        init_database()
        migrate_old_databases()
        logger.info("✅ База данных готова")
        
        # Выводим информацию о запуске
        logger.info("\n" + "=" * 60)
        logger.info("🎯 Запуск компонентов:")
        logger.info("   🌐 Веб-сервер с интерфейсом магазина")
        logger.info("   🤖 Telegram бот поддержки клиентов")
        logger.info("   📱 WebApp для Telegram")
        logger.info("   📞 Система поддержки и отзывов")
        logger.info(f"   🔗 URL: http://localhost:{PORT}")
        logger.info("=" * 60 + "\n")
        
        # Запускаем веб-сервер в отдельном потоке
        web_server_thread = threading.Thread(target=run_web_server, daemon=True)
        web_server_thread.start()
        
        # Даем серверу немного времени на запуск
        time.sleep(2)
        
        # Запускаем бота поддержки в основном потоке
        run_telegram_bot()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        logger.info("👋 Приложение завершено")


if __name__ == "__main__":
    main()

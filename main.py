#!/usr/bin/env python3
"""
🚀 PROFESSIONAL E-COMMERCE PLATFORM - MAIN ENTRY POINT
=======================================================
Главный файл для запуска всей платформы
"""

import asyncio
import os
import signal
import sys
import threading
import time
from pathlib import Path

import uvicorn
import requests

# Импорты для наших модулей
from app import app
from telegram_bot import main as run_bot

class ECommercePlatform:
    def __init__(self):
        self.web_server_process = None
        self.bot_task = None
        self.running = True
        
        # Конфигурация
        self.web_port = int(os.getenv('PORT', 8000))
        self.web_host = os.getenv('HOST', '0.0.0.0')
        self.bot_token = os.getenv('BOT_TOKEN', '')
        self.webapp_url = os.getenv('WEBAPP_URL', f'http://localhost:{self.web_port}')
        
        # Устанавливаем переменную окружения для бота
        os.environ['WEBAPP_URL'] = self.webapp_url
        
    def print_banner(self):
        """Красивый баннер"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  🏢 PROFESSIONAL E-COMMERCE PLATFORM                        ║
║                                                              ║
║  ✨ Современная платформа электронной коммерции              ║
║  🤖 Интеграция с Telegram ботом                             ║
║  🌐 Веб-приложение на FastAPI                               ║
║  💾 SQLite база данных                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def print_status(self):
        """Статус системы"""
        print("\n📊 СТАТУС СИСТЕМЫ:")
        print("=" * 50)
        print(f"🌐 Веб-сервер: http://{self.web_host}:{self.web_port}")
        print(f"📚 API документация: http://{self.web_host}:{self.web_port}/docs")
        print(f"🤖 Telegram бот: {'✅ Запущен' if self.bot_token else '❌ Не настроен'}")
        print(f"💾 База данных: shop.db")
        print(f"📁 Загрузки: uploads/")
        print("=" * 50)
        
    def setup_directories(self):
        """Создание необходимых директорий"""
        directories = ['uploads', 'static', 'db_backups']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        print("✅ Директории созданы")
        
    def check_web_server(self, timeout=30):
        """Проверка доступности веб-сервера"""
        print("🔍 Проверяем веб-сервер...")
        
        for i in range(timeout):
            try:
                response = requests.get(f"http://localhost:{self.web_port}/api/products", timeout=1)
                if response.status_code == 200:
                    print("✅ Веб-сервер запущен и отвечает")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            if i % 5 == 0 and i > 0:
                print(f"⏳ Ожидание запуска сервера... ({i}/{timeout})")
        
        print("❌ Веб-сервер не отвечает")
        return False
        
    def run_web_server(self):
        """Запуск веб-сервера"""
        print("🌐 Запускаем веб-сервер...")
        try:
            uvicorn.run(
                app, 
                host=self.web_host, 
                port=self.web_port,
                log_level="info",
                access_log=False
            )
        except Exception as e:
            print(f"❌ Ошибка веб-сервера: {e}")
            
    async def run_telegram_bot(self):
        """Запуск Telegram бота"""
        if not self.bot_token:
            print("⚠️ BOT_TOKEN не найден - бот не будет запущен")
            print("💡 Для запуска бота установите переменную окружения BOT_TOKEN")
            return
            
        print("🤖 Запускаем Telegram бота...")
        try:
            await run_bot()
        except Exception as e:
            print(f"❌ Ошибка Telegram бота: {e}")
            
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print(f"\n🛑 Получен сигнал {signum}. Завершаем работу...")
        self.running = False
        
        # Завершаем задачи
        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()
            
        print("✅ Платформа остановлена")
        sys.exit(0)
        
    async def start(self):
        """Запуск всей платформы"""
        self.print_banner()
        
        # Создаем директории
        self.setup_directories()
        
        # Настраиваем обработчики сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Запускаем веб-сервер в отдельном потоке
        web_thread = threading.Thread(target=self.run_web_server, daemon=True)
        web_thread.start()
        
        # Ждем запуска веб-сервера
        if not self.check_web_server():
            print("❌ Не удалось запустить веб-сервер")
            return
            
        # Показываем статус
        self.print_status()
        
        # Запускаем Telegram бота
        if self.bot_token:
            self.bot_task = asyncio.create_task(self.run_telegram_bot())
            
            try:
                await self.bot_task
            except asyncio.CancelledError:
                print("🤖 Telegram бот остановлен")
        else:
            print("\n🎉 Платформа запущена!")
            print("💡 Для запуска бота установите BOT_TOKEN")
            print("🛑 Для остановки нажмите Ctrl+C")
            
            # Ожидаем завершения
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass

async def main():
    """Главная функция"""
    platform = ECommercePlatform()
    await platform.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Безопасный запуск бота с обработкой конфликтов портов
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def kill_processes_on_port(port):
    """Убивает все процессы на указанном порту"""
    try:
        # Пытаемся найти и убить процессы на порту
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=False)
                    print(f"🔪 Убит процесс {pid} на порту {port}")
                except:
                    pass
        
        # Дополнительно убиваем все Python процессы
        subprocess.run(['pkill', '-9', 'python'], check=False)
        subprocess.run(['pkill', '-9', 'python3'], check=False)
        subprocess.run(['killall', '-9', 'python'], check=False)
        subprocess.run(['killall', '-9', 'python3'], check=False)
        
        time.sleep(2)
        print(f"✅ Порт {port} освобожден")
        
    except Exception as e:
        print(f"⚠️ Ошибка освобождения порта {port}: {e}")

def check_env_file():
    """Проверяет и создает .env файл если нужно"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("⚠️ Файл .env не найден, создаем...")
        with open('.env', 'w') as f:
            f.write("BOT_TOKEN=your_real_bot_token_here\n")
            f.write("WEBAPP_URL=http://localhost:8000\n")
            f.write("ADMINS=1593426947\n")
            f.write("LOG_LEVEL=INFO\n")
        print("✅ Файл .env создан")
        return False
    
    # Проверяем содержимое
    with open('.env', 'r') as f:
        content = f.read()
    
    if 'your_bot_token_here' in content or 'your_real_bot_token_here' in content:
        print("⚠️ В .env файле стоит заглушка токена!")
        print("📝 Пожалуйста, замените 'your_real_bot_token_here' на реальный токен бота")
        return False
    
    print("✅ Файл .env в порядке")
    return True

def start_server():
    """Запускает веб-сервер"""
    print("🚀 Запускаем веб-сервер...")
    
    # Убиваем процессы на порту 8000
    kill_processes_on_port(8000)
    
    try:
        # Запускаем сервер в фоне
        server_process = subprocess.Popen([
            sys.executable, 'perfect_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем немного и проверяем
        time.sleep(3)
        
        if server_process.poll() is None:
            print("✅ Веб-сервер запущен на порту 8000")
            return server_process
        else:
            stdout, stderr = server_process.communicate()
            print(f"❌ Ошибка запуска сервера:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return None

def start_bot():
    """Запускает бота"""
    print("🤖 Запускаем бота...")
    
    try:
        # Запускаем бота
        bot_process = subprocess.Popen([
            sys.executable, 'bot.py'
        ])
        
        print("✅ Бот запущен")
        return bot_process
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return None

def main():
    """Основная функция"""
    print("=" * 60)
    print("🚀 БЕЗОПАСНЫЙ ЗАПУСК БОТА И СЕРВЕРА")
    print("=" * 60)
    
    # Проверяем .env файл
    if not check_env_file():
        print("\n❌ Нужно настроить токен бота в .env файле!")
        print("1. Получите токен у @BotFather")
        print("2. Замените 'your_real_bot_token_here' на реальный токен")
        print("3. Запустите скрипт снова")
        return
    
    # Запускаем сервер
    server_process = start_server()
    if not server_process:
        print("❌ Не удалось запустить сервер")
        return
    
    # Запускаем бота
    bot_process = start_bot()
    if not bot_process:
        print("❌ Не удалось запустить бота")
        server_process.terminate()
        return
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ СЕРВИСЫ ЗАПУЩЕНЫ!")
    print("🌐 Веб-приложение: http://localhost:8000")
    print("🤖 Бот запущен и готов к работе")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("=" * 60)
    
    try:
        # Ждем завершения процессов
        while True:
            time.sleep(1)
            
            # Проверяем, что процессы еще работают
            if server_process.poll() is not None:
                print("❌ Сервер остановлен")
                break
                
            if bot_process.poll() is not None:
                print("❌ Бот остановлен")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Останавливаем сервисы...")
        
        # Останавливаем процессы
        if server_process:
            server_process.terminate()
        if bot_process:
            bot_process.terminate()
        
        print("✅ Все сервисы остановлены")

if __name__ == "__main__":
    main()

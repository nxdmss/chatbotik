#!/usr/bin/env python3
"""
🚀 КОРНЕВОЙ MAIN.PY ДЛЯ REPLIT
=============================
Запускает приложение из папки chatbotik
"""

import os
import sys
import subprocess

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ LOOK & GO")
    print("=" * 50)
    
    # Переходим в папку chatbotik
    chatbotik_dir = os.path.join(os.path.dirname(__file__), 'chatbotik')
    
    if not os.path.exists(chatbotik_dir):
        print("❌ Папка chatbotik не найдена!")
        return
    
    print(f"📁 Переходим в папку: {chatbotik_dir}")
    os.chdir(chatbotik_dir)
    
    # Запускаем main.py из папки chatbotik
    main_py_path = os.path.join(chatbotik_dir, 'main.py')
    
    if not os.path.exists(main_py_path):
        print("❌ Файл chatbotik/main.py не найден!")
        return
    
    print("🚀 Запуск main.py из папки chatbotik...")
    
    try:
        # Запускаем Python файл
        subprocess.run([sys.executable, 'main.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Остановка по запросу пользователя")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
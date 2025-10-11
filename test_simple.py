#!/usr/bin/env python3
"""
Простой тест для проверки основных компонентов
"""

print("🧪 Тестирование компонентов приложения...")

# Тест 1: Проверка импортов
try:
    print("1. Проверка импортов...")
    import os
    import json
    from datetime import datetime
    print("   ✅ Базовые модули импортированы")
except Exception as e:
    print(f"   ❌ Ошибка импорта базовых модулей: {e}")

# Тест 2: Проверка файлов
try:
    print("2. Проверка файлов...")
    required_files = [
        "bot.py",
        "server.py", 
        "run.py",
        "models.py",
        "database.py",
        "logger_config.py",
        "error_handlers.py",
        "webapp/index.html",
        "webapp/app.js",
        "webapp/styles.css",
        "webapp/admins.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ❌ Отсутствуют файлы: {missing_files}")
    else:
        print("   ✅ Все необходимые файлы найдены")
        
except Exception as e:
    print(f"   ❌ Ошибка проверки файлов: {e}")

# Тест 3: Проверка .env
try:
    print("3. Проверка .env...")
    if os.path.exists('.env'):
        print("   ✅ Файл .env найден")
        with open('.env', 'r') as f:
            content = f.read()
            if 'BOT_TOKEN' in content and 'WEBAPP_URL' in content:
                print("   ✅ Переменные BOT_TOKEN и WEBAPP_URL найдены")
            else:
                print("   ⚠️  Не все переменные найдены в .env")
    else:
        print("   ❌ Файл .env не найден")
except Exception as e:
    print(f"   ❌ Ошибка проверки .env: {e}")

# Тест 4: Проверка webapp/admins.json
try:
    print("4. Проверка admins.json...")
    with open('webapp/admins.json', 'r') as f:
        admins_data = json.load(f)
        if 'admins' in admins_data and len(admins_data['admins']) > 0:
            print(f"   ✅ Найдено {len(admins_data['admins'])} администраторов")
        else:
            print("   ⚠️  Список администраторов пуст")
except Exception as e:
    print(f"   ❌ Ошибка проверки admins.json: {e}")

# Тест 5: Проверка синтаксиса Python файлов
try:
    print("5. Проверка синтаксиса...")
    import py_compile
    
    python_files = ["bot.py", "server.py", "run.py", "models.py", "database.py", "logger_config.py", "error_handlers.py"]
    
    for file_path in python_files:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"   ✅ {file_path} - синтаксис корректен")
        except py_compile.PyCompileError as e:
            print(f"   ❌ {file_path} - ошибка синтаксиса: {e}")
            
except Exception as e:
    print(f"   ❌ Ошибка проверки синтаксиса: {e}")

print("\n🎯 РЕЗУЛЬТАТ:")
print("Если все тесты прошли успешно, приложение готово к запуску в Replit!")
print("Локальные проблемы с архитектурой Python не влияют на работу в Replit.")

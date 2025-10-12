#!/bin/bash

echo "⚡ БЫСТРОЕ ОБНОВЛЕНИЕ"
echo "===================="

# Остановка процессов
pkill -9 python

# Обновление
git pull origin main

# Создание папок
mkdir -p uploads

# Запуск сервера
python3 working_server.py &
echo "✅ Сервер запущен на http://localhost:8000"
echo "🔑 Пароль админа: admin123"

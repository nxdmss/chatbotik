#!/bin/bash
# Скрипт для быстрого обновления Replit

echo "🔄 Обновление проекта из GitHub..."

# Сохраняем локальные изменения
echo "💾 Сохраняем локальные изменения..."
git stash

# Получаем изменения с GitHub
echo "📥 Скачиваем изменения..."
git pull origin main

# Убиваем процессы на порту 8000
echo "🛑 Останавливаем старый сервер..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
sleep 2

# Если база данных пустая или нет товаров - восстанавливаем из JSON
echo "🔍 Проверяем базу данных..."
if [ ! -f "shop.db" ] || [ $(sqlite3 shop.db "SELECT COUNT(*) FROM products;" 2>/dev/null || echo "0") -eq 0 ]; then
    echo "📦 Восстанавливаем базу данных из JSON..."
    python3 backup_db.py restore-json
fi

# Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 perfect_server.py


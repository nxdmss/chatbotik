#!/bin/bash

echo "🚀 ЗАПУСК МАГАЗИНА И БОТА В REPLIT"
echo "=================================="

# Создаем папки
mkdir -p uploads
mkdir -p db_backups

# Очищаем конфликтующие файлы
rm -f shop_data.json

echo "🌐 Запускаем веб-сервер..."
python3 simple_shop.py &
SERVER_PID=$!

# Ждем запуска сервера
sleep 3

echo "✅ Сервер запущен на http://localhost:8000"
echo "🤖 Запускаем бота..."

# Запускаем бота
python3 bot.py

# Ожидание завершения
wait $SERVER_PID

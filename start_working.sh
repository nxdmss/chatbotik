#!/bin/bash

echo "🛑 Останавливаем все Python процессы..."
pkill -9 python

echo "📁 Создаем папку для загрузок..."
mkdir -p uploads

echo "🚀 Запускаем РАБОЧИЙ сервер..."
python3 working_server.py &
SERVER_PID=$!

echo "✅ РАБОЧИЙ сервер запущен!"
echo "🌐 Магазин: http://localhost:8000"
echo "🔑 АДМИН ПАРОЛЬ: admin123"
echo "📷 Фотографии: папка uploads/"
echo "💾 Данные: products_data.json"
echo ""
echo "🛑 Для остановки: Ctrl+C"

wait $SERVER_PID

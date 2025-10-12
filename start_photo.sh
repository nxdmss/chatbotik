#!/bin/bash
# Скрипт запуска сервера с фотографиями

echo "🛑 Останавливаем все процессы..."
pkill -9 python

echo "📷 Создаем папку для фотографий..."
mkdir -p uploads

echo "🚀 Запускаем сервер с фотографиями..."
python3 photo_server.py &
SERVER_PID=$!

echo "✅ Сервер запущен!"
echo "🌐 Магазин: http://localhost:8000"
echo "📷 Фотографии: папка uploads/"
echo "💾 Данные: products_data.json"
echo ""
echo "🛑 Для остановки: Ctrl+C"
echo "📱 Откройте приложение через бота в Telegram!"
echo ""

# Ждем завершения
wait $SERVER_PID

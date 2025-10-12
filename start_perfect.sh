#!/bin/bash
# Скрипт запуска ИДЕАЛЬНОГО сервера

echo "🛑 Останавливаем все процессы..."
pkill -9 python

echo "📷 Создаем папку для фотографий..."
mkdir -p uploads

echo "🚀 Запускаем ИДЕАЛЬНЫЙ сервер..."
python3 perfect_server.py &
SERVER_PID=$!

echo "✅ ИДЕАЛЬНЫЙ сервер запущен!"
echo "🌐 Магазин: http://localhost:8000"
echo "🔑 АДМИН ПАРОЛЬ: admin123"
echo "📷 Фотографии: папка uploads/"
echo "💾 Данные: products_data.json"
echo ""
echo "🛑 Для остановки: Ctrl+C"
echo "📱 Откройте приложение через бота в Telegram!"
echo "🔐 Для доступа к админке нажмите кнопку 'Админ' и введите пароль!"
echo ""

# Ждем завершения
wait $SERVER_PID

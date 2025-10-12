#!/bin/bash
# Скрипт запуска БЕЗОПАСНОГО сервера с админкой по паролю

echo "🛑 Останавливаем все процессы..."
pkill -9 python

echo "📷 Создаем папку для фотографий..."
mkdir -p uploads

echo "🔐 Запускаем БЕЗОПАСНЫЙ сервер с админкой по паролю..."
python3 secure_admin_server.py &
SERVER_PID=$!

echo "✅ БЕЗОПАСНЫЙ сервер запущен!"
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

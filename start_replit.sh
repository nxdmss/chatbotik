#!/bin/bash

echo "🚀 ЗАПУСК В REPLIT"
echo "=================="

# Остановить все процессы
pkill -9 python

# Создать папку для фото
mkdir -p uploads

# Запустить рабочий сервер
echo "🌐 Запускаем сервер..."
python3 working_server.py &

# Пауза для запуска
sleep 2

echo "✅ Сервер запущен!"
echo "🌐 Магазин: http://localhost:8000"
echo "🔑 Админ пароль: admin123"
echo "📱 Откройте приложение через бота в Telegram!"
echo ""
echo "🛑 Для остановки: Ctrl+C"

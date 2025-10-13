#!/bin/bash

echo "🚀 ОБНОВЛЕНИЕ ПРОЕКТА"
echo "===================="

# 1. Останавливаем все процессы Python
echo "🛑 Останавливаем процессы..."
pkill -f python || true
sleep 2

# 2. Обновляем из GitHub
echo "📥 Обновляем из GitHub..."
git pull origin main

# 3. Очищаем базу данных от неправильных записей
echo "🧹 Очищаем базу данных..."
sqlite3 shop.db "UPDATE products SET image_url = '' WHERE image_url NOT LIKE '/uploads/%';" 2>/dev/null || true

# 4. Проверяем папку uploads
echo "📁 Проверяем папку uploads..."
if [ ! -d "uploads" ]; then
    mkdir -p uploads
    echo "📁 Создана папка uploads"
fi

# 5. Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 simple_telegram_bot.py &

echo "✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "========================"
echo "🌐 Веб-приложение: http://localhost:8000"
echo "🛑 Для остановки: Ctrl+C"
echo "📱 Откройте в Telegram WebApp для тестирования"

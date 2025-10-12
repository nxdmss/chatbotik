#!/bin/bash

echo "🔄 ОБНОВЛЕНИЕ REPLIT ЧЕРЕЗ GITHUB"
echo "================================="

# Останавливаем все процессы
echo "🛑 Останавливаем процессы..."
pkill -f python 2>/dev/null || true

# Удаляем конфликтующие файлы
echo "🧹 Очищаем конфликтующие файлы..."
rm -f requirements.txt
rm -f shop.db
rm -f *.pyc

# Обновляем проект
echo "📥 Обновляем проект из GitHub..."
git fetch origin
git reset --hard origin/main

# Перезапускаем сервер
echo "🚀 Запускаем новый сервер..."
python3 simple_telegram_bot.py &

# Ждем запуска
sleep 3

# Проверяем работу
echo "🔍 Проверяем работу сервера..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Сервер работает отлично!"
    echo "🌐 WebApp: http://localhost:8000"
    echo "📱 Готов к настройке Telegram бота!"
else
    echo "❌ Ошибка сервера"
fi

echo "================================="
echo "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "================================="

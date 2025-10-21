#!/bin/bash

echo "🚀 Запуск магазин-бота..."
echo ""

# Проверка токена
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не найден!"
    echo "💡 Запустите:"
    echo "   export BOT_TOKEN='ваш_токен'"
    echo "   ./RUN.sh"
    exit 1
fi

echo "✅ BOT_TOKEN найден"
echo ""

# Создаем директории
mkdir -p logs
mkdir -p webapp/uploads

# Запуск
echo "▶️  Запуск приложения..."
python3 main.py


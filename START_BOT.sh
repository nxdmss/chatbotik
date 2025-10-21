#!/bin/bash
# 🚀 ПРОСТОЙ ЗАПУСК БОТА

echo "🛍️ Запуск идеального магазин-бота..."
echo ""

# Проверка BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не найден!"
    echo "💡 Установите переменную окружения:"
    echo "   export BOT_TOKEN='ваш_токен_бота'"
    echo ""
    echo "Или создайте файл .env:"
    echo "   echo 'BOT_TOKEN=ваш_токен' > .env"
    echo "   source .env"
    exit 1
fi

# Создаем необходимые директории
mkdir -p logs
mkdir -p webapp/uploads

# Запуск бота
python3 perfect_shop_bot.py


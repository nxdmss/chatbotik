#!/bin/bash

# ===============================================
# 🚀 ПРОСТОЙ ЗАПУСК ПРОЕКТА
# ===============================================

echo "🚀 ЗАПУСК ПРОСТОГО ПРОЕКТА"
echo "=================================="

# 1. Останавливаем все процессы
echo "🛑 Останавливаем процессы..."
pkill -9 python || true
sleep 2

# 2. Проверяем .env файл
echo "📝 Проверяем .env файл..."
if [ ! -f ".env" ]; then
    echo "⚠️ Создаем .env файл..."
    echo "BOT_TOKEN=your_real_bot_token_here" > .env
    echo "📝 ВНИМАНИЕ: Замените 'your_real_bot_token_here' на реальный токен!"
    echo "🤖 Получите токен у @BotFather в Telegram"
fi

# 3. Запускаем сервер
echo "🌐 Запускаем веб-сервер..."
python3 ultra_simple_server.py &
SERVER_PID=$!
echo "✅ Сервер запущен с PID: $SERVER_PID"

# 4. Ждем запуска сервера
echo "⏳ Ждем запуска сервера..."
sleep 3

# 5. Проверяем сервер
echo "🔍 Проверяем сервер..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Сервер работает на http://localhost:8000"
else
    echo "❌ Сервер НЕ запущен!"
    exit 1
fi

# 6. Запускаем бота
echo "🤖 Запускаем бота..."
python3 simple_bot.py &
BOT_PID=$!
echo "✅ Бот запущен с PID: $BOT_PID"

echo ""
echo "🎉 ВСЕ ЗАПУЩЕНО!"
echo "=================================="
echo "🌐 Магазин: http://localhost:8000"
echo "⚙️ Админ: http://localhost:8000/admin"
echo "🤖 Бот: настройте токен в .env"
echo ""
echo "📊 PID процессов:"
echo "   Сервер: $SERVER_PID"
echo "   Бот: $BOT_PID"
echo ""
echo "🛑 Для остановки:"
echo "   kill $SERVER_PID $BOT_PID"
echo "=================================="

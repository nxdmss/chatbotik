#!/bin/bash

# ===============================================
# 🚀 ЗАПУСК УЛУЧШЕННОЙ ВЕРСИИ
# ===============================================

echo "🚀 ЗАПУСК УЛУЧШЕННОЙ ВЕРСИИ"
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

# 3. Создаем папку для изображений
echo "📁 Создаем папку для изображений..."
mkdir -p static/images

# 4. Запускаем улучшенный сервер
echo "🌐 Запускаем улучшенный сервер..."
python3 enhanced_server.py &
SERVER_PID=$!
echo "✅ Сервер запущен с PID: $SERVER_PID"

# 5. Ждем запуска сервера
echo "⏳ Ждем запуска сервера..."
sleep 3

# 6. Проверяем сервер
echo "🔍 Проверяем сервер..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Сервер работает на http://localhost:8000"
else
    echo "❌ Сервер НЕ запущен!"
    exit 1
fi

# 7. Запускаем бота
echo "🤖 Запускаем бота..."
python3 simple_bot.py &
BOT_PID=$!
echo "✅ Бот запущен с PID: $BOT_PID"

echo ""
echo "🎉 УЛУЧШЕННАЯ ВЕРСИЯ ЗАПУЩЕНА!"
echo "=================================="
echo "🌐 Магазин: http://localhost:8000"
echo "🛒 Корзина: встроена в магазин"
echo "⚙️ Админ: http://localhost:8000/admin"
echo "🤖 Бот: настройте токен в .env"
echo ""
echo "✨ НОВЫЕ ФУНКЦИИ:"
echo "   📦 Товары по 2 в строке"
echo "   🖼️ Фотографии товаров"
echo "   🛒 Корзина покупок"
echo "   ⚙️ Улучшенная админ панель"
echo "   ✏️ Редактирование товаров"
echo "   📊 Статистика"
echo ""
echo "📊 PID процессов:"
echo "   Сервер: $SERVER_PID"
echo "   Бот: $BOT_PID"
echo ""
echo "🛑 Для остановки:"
echo "   kill $SERVER_PID $BOT_PID"
echo "=================================="

#!/bin/bash

# ===============================================
# 🚀 ЗАПУСК СЕРВЕРА С СОХРАНЕНИЕМ
# ===============================================

echo "🚀 ЗАПУСК СЕРВЕРА С СОХРАНЕНИЕМ"
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

# 3. Запускаем сервер с сохранением
echo "🌐 Запускаем сервер с сохранением..."
python3 persistent_server.py &
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
echo "🎉 СЕРВЕР С СОХРАНЕНИЕМ ЗАПУЩЕН!"
echo "=================================="
echo "🌐 Магазин: http://localhost:8000"
echo "🛒 Корзина: встроена в магазин"
echo "⚙️ Админ: кнопка '⚙️ Админ' в заголовке"
echo "💾 Данные сохраняются в: products_data.json"
echo "🤖 Бот: настройте токен в .env"
echo ""
echo "✨ ФУНКЦИИ СОХРАНЕНИЯ:"
echo "   💾 ТОВАРЫ СОХРАНЯЮТСЯ НАВСЕГДА"
echo "   📁 Файл products_data.json"
echo "   🔄 Автоматическое сохранение"
echo "   📦 Загрузка при запуске"
echo "   🗑️ Реальное удаление из файла"
echo ""
echo "📊 PID процессов:"
echo "   Сервер: $SERVER_PID"
echo "   Бот: $BOT_PID"
echo ""
echo "🛑 Для остановки:"
echo "   kill $SERVER_PID $BOT_PID"
echo "=================================="

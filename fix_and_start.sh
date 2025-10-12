#!/bin/bash
# Скрипт для исправления проблем и запуска

echo "🔧 ИСПРАВЛЯЕМ ПРОБЛЕМЫ И ЗАПУСКАЕМ"
echo "=================================="

# 1. Убиваем все Python процессы
echo "🛑 Останавливаем все Python процессы..."
pkill -9 python 2>/dev/null
pkill -9 python3 2>/dev/null
killall -9 python 2>/dev/null
killall -9 python3 2>/dev/null
sleep 2

# 2. Освобождаем порт 8000
echo "🔓 Освобождаем порт 8000..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
sleep 1

# 3. Проверяем .env файл
echo "📝 Проверяем .env файл..."
if [ ! -f ".env" ]; then
    echo "⚠️ Создаем .env файл..."
    cat > .env << EOF
BOT_TOKEN=your_real_bot_token_here
WEBAPP_URL=http://localhost:8000
ADMINS=1593426947
LOG_LEVEL=INFO
EOF
    echo "✅ .env файл создан"
else
    echo "✅ .env файл существует"
fi

# 4. Проверяем токен
if grep -q "your_.*_token_here" .env; then
    echo "⚠️ ВНИМАНИЕ: В .env файле стоит заглушка токена!"
    echo "📝 Замените 'your_real_bot_token_here' на реальный токен бота"
    echo "🤖 Получите токен у @BotFather в Telegram"
fi

# 5. Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 perfect_server.py &
SERVER_PID=$!
sleep 3

# 6. Проверяем сервер
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Сервер запущен на http://localhost:8000"
else
    echo "❌ Ошибка запуска сервера"
    exit 1
fi

# 7. Запускаем бота (только если токен настроен)
if ! grep -q "your_.*_token_here" .env; then
    echo "🤖 Запускаем бота..."
    python3 bot.py &
    BOT_PID=$!
    echo "✅ Бот запущен"
else
    echo "⚠️ Бот НЕ запущен - нужно настроить токен в .env"
fi

echo ""
echo "=================================="
echo "✅ ГОТОВО!"
echo "🌐 Веб-приложение: http://localhost:8000"
if ! grep -q "your_.*_token_here" .env; then
    echo "🤖 Бот запущен и готов к работе"
else
    echo "⚠️ Настройте токен в .env для запуска бота"
fi
echo "🛑 Для остановки: Ctrl+C"
echo "=================================="

# Ждем сигнала завершения
trap 'echo "🛑 Останавливаем..."; kill $SERVER_PID 2>/dev/null; kill $BOT_PID 2>/dev/null; exit' INT
wait

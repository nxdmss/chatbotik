#!/bin/bash
# Быстрое исправление и запуск всего проекта

echo "🚀 БЫСТРОЕ ИСПРАВЛЕНИЕ И ЗАПУСК"
echo "================================"

# 1. Обновляем проект из GitHub
echo "📥 Обновляем проект из GitHub..."
git pull origin main

# 2. Останавливаем все процессы
echo "🛑 Останавливаем все процессы..."
pkill -9 python 2>/dev/null
pkill -9 python3 2>/dev/null
killall -9 python 2>/dev/null
killall -9 python3 2>/dev/null
sleep 2

# 3. Освобождаем порт 8000
echo "🔓 Освобождаем порт 8000..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
sleep 1

# 4. Проверяем .env файл
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

# 5. Проверяем токен
if grep -q "your_.*_token_here" .env; then
    echo "⚠️ ВНИМАНИЕ: В .env файле стоит заглушка токена!"
    echo "📝 Замените 'your_real_bot_token_here' на реальный токен бота"
    echo "🤖 Получите токен у @BotFather в Telegram"
fi

# 6. Запускаем сервер
echo "🚀 Запускаем веб-сервер..."
python3 perfect_server.py &
SERVER_PID=$!
sleep 3

# 7. Проверяем работу сервера
echo "✅ Проверяем работу сервера..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Веб-сервер работает на http://localhost:8000"
else
    echo "❌ Ошибка запуска веб-сервера"
    echo "🔄 Пробуем альтернативный порт..."
    python3 perfect_server.py --port 8001 &
    SERVER_PID=$!
    sleep 3
    
    if curl -s http://localhost:8001 > /dev/null; then
        echo "✅ Веб-сервер работает на http://localhost:8001"
    else
        echo "❌ Не удалось запустить сервер"
        exit 1
    fi
fi

# 8. Запускаем бота (только если токен настроен)
if ! grep -q "your_.*_token_here" .env; then
    echo "🤖 Запускаем бота..."
    python3 bot.py &
    BOT_PID=$!
    echo "✅ Бот запущен"
else
    echo "⚠️ Бот НЕ запущен - нужно настроить токен в .env"
    BOT_PID=""
fi

echo ""
echo "================================"
echo "✅ ВСЕ ГОТОВО!"
echo ""
echo "🌐 Веб-приложение:"
if curl -s http://localhost:8000 > /dev/null; then
    echo "   http://localhost:8000"
else
    echo "   http://localhost:8001"
fi
echo ""
if [ -n "$BOT_PID" ]; then
    echo "🤖 Бот запущен и готов к работе"
else
    echo "⚠️ Настройте токен в .env для запуска бота"
fi
echo ""
echo "🔧 ИНСТРУКЦИЯ ПО АДМИН ПАНЕЛИ:"
echo "1. Откройте приложение в НОВОЙ вкладке браузера"
echo "2. Откройте консоль (F12) и проверьте логи:"
echo "   🚀 Загружается приложение версии 3.0"
echo "   🔧 Отладочный режим: Replit/localhost обнаружен"
echo "   👑 Админские права предоставлены"
echo "3. Админ панель появится автоматически"
echo "4. Если не появилась - нажмите красную кнопку в правом верхнем углу"
echo ""
echo "🛑 Для остановки: Ctrl+C"
echo "================================"

# Функция для корректного завершения
cleanup() {
    echo ""
    echo "🛑 Останавливаем сервисы..."
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
    fi
    if [ -n "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null
    fi
    echo "✅ Все сервисы остановлены"
    exit 0
}

# Перехватываем сигнал завершения
trap cleanup INT TERM

# Ждем завершения
wait

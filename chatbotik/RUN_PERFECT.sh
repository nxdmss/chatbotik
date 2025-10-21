#!/bin/bash
# 🎯 ЗАПУСК ИДЕАЛЬНОГО РЕШЕНИЯ

clear
echo "════════════════════════════════════════════════════════"
echo "🎯 ИДЕАЛЬНЫЙ БОТ - ГАРАНТИРОВАННОЕ РЕШЕНИЕ"
echo "════════════════════════════════════════════════════════"
echo ""

# Остановка процессов
echo "🛑 Останавливаем старые процессы..."
pkill -9 -f "python.*PERFECT_BOT.py" 2>/dev/null
pkill -9 -f "python.*simple_telegram_bot.py" 2>/dev/null
sleep 2

# Освобождение портов
echo "🔓 Освобождаем порты..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# Проверка токена
if [ -z "$BOT_TOKEN" ]; then
    echo ""
    echo "❌ BOT_TOKEN не найден!"
    echo "💡 Токен должен быть в Replit Secrets"
    echo ""
    exit 1
fi

echo "✅ BOT_TOKEN найден: ${BOT_TOKEN:0:15}..."
echo ""

# Создание директорий
mkdir -p logs
mkdir -p webapp/uploads

# Запуск веб-сервера в фоне
echo "🌐 Запуск веб-сервера..."
nohup python3 simple_telegram_bot.py > logs/web_server.log 2>&1 &
WEB_PID=$!
echo "✅ Веб-сервер запущен (PID: $WEB_PID)"
sleep 3

# Проверка веб-сервера
if lsof -i:8000 > /dev/null 2>&1; then
    echo "✅ Веб-сервер работает на порту 8000"
else
    echo "⚠️ Веб-сервер может не запуститься - проверьте логи"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "🤖 ЗАПУСК БОТА..."
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 Админ ID: 1593426947"
echo "📝 Логи: logs/perfect_bot.log"
echo ""
echo "💡 Для остановки нажмите Ctrl+C"
echo ""

# Запуск бота
python3 PERFECT_BOT.py

echo ""
echo "👋 Бот остановлен"


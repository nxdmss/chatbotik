#!/bin/bash
# 🚀 ИДЕАЛЬНЫЙ СКРИПТ ЗАПУСКА МАГАЗИНА

clear
echo "════════════════════════════════════════════════════════"
echo "🛍️  МАГАЗИН-БОТ - ИДЕАЛЬНЫЙ ЗАПУСК"
echo "════════════════════════════════════════════════════════"
echo ""

# Остановка всех процессов
echo "🛑 Останавливаем старые процессы..."
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "python.*simple_telegram_bot.py" 2>/dev/null
pkill -9 -f "python.*no_telegram_bot.py" 2>/dev/null
sleep 2

# Освобождение портов
echo "🔓 Освобождаем порты..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
lsof -ti:8080 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# Проверка токена
if [ -z "$BOT_TOKEN" ]; then
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "❌ BOT_TOKEN НЕ НАЙДЕН!"
    echo "════════════════════════════════════════════════════════"
    echo ""
    echo "💡 Сначала установите токен бота:"
    echo ""
    echo "   export BOT_TOKEN='8226153553:ваш_полный_токен'"
    echo ""
    echo "Затем запустите снова:"
    echo ""
    echo "   ./LAUNCH.sh"
    echo ""
    echo "════════════════════════════════════════════════════════"
    exit 1
fi

echo "✅ BOT_TOKEN найден: ${BOT_TOKEN:0:15}..."
echo ""

# Создание директорий
echo "📁 Создаем необходимые директории..."
mkdir -p logs
mkdir -p webapp/uploads
mkdir -p chatbotik/logs
mkdir -p chatbotik/webapp/uploads

# Проверка файлов
echo "📋 Проверяем файлы..."
if [ ! -f "main.py" ]; then
    echo "❌ main.py не найден!"
    exit 1
fi
echo "✅ Все файлы на месте"
echo ""

# Запуск
echo "════════════════════════════════════════════════════════"
echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ..."
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 Директория: $(pwd)"
echo "🤖 Бот: @$(echo $BOT_TOKEN | cut -d':' -f1)"
echo "🌐 Веб-сервер: http://localhost:8000"
echo "👤 Админ ID: 1593426947"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""
echo "💡 Для остановки нажмите Ctrl+C"
echo ""

# Запуск приложения
python3 main.py

echo ""
echo "👋 Приложение остановлено"


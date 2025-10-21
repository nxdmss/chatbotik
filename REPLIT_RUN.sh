#!/bin/bash
# 🚀 ЗАПУСК НА REPLIT (токен уже в Secrets)

clear
echo "════════════════════════════════════════════════════════"
echo "🛍️  ЗАПУСК НА REPLIT"
echo "════════════════════════════════════════════════════════"
echo ""

# Остановка процессов
echo "🛑 Останавливаем старые процессы..."
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "python.*simple_telegram_bot.py" 2>/dev/null
sleep 2

# Освобождение портов
echo "🔓 Освобождаем порты..."
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
lsof -ti:8080 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# Проверка токена из Secrets
if [ -z "$BOT_TOKEN" ]; then
    echo ""
    echo "❌ BOT_TOKEN не найден!"
    echo ""
    echo "💡 Проверьте Secrets в Replit:"
    echo "   1. Откройте Secrets (🔐 в левом меню)"
    echo "   2. Убедитесь что есть BOT_TOKEN"
    echo "   3. Перезапустите Repl"
    echo ""
    exit 1
fi

echo "✅ BOT_TOKEN найден в Secrets: ${BOT_TOKEN:0:15}..."
echo ""

# Обновление из Git
echo "📥 Обновляем код из Git..."
git pull origin main
echo ""

# Создание директорий
echo "📁 Создаем директории..."
mkdir -p logs
mkdir -p webapp/uploads
mkdir -p chatbotik/logs
mkdir -p chatbotik/webapp/uploads

# Переход в нужную директорию
if [ -d "chatbotik" ]; then
    cd chatbotik
    echo "📍 Перешли в директорию: $(pwd)"
fi

# Запуск
echo ""
echo "════════════════════════════════════════════════════════"
echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ..."
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 Веб-сервер: https://$(hostname).repl.co"
echo "👤 Админ ID: 1593426947"
echo ""
echo "💡 Для остановки нажмите Ctrl+C"
echo ""

# Запуск приложения
python3 main.py


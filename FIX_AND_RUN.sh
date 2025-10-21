#!/bin/bash
# 🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ И ЗАПУСК

echo "════════════════════════════════════════════════════════"
echo "🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ И ЗАПУСК"
echo "════════════════════════════════════════════════════════"
echo ""

# 1. ПОЛНАЯ ОСТАНОВКА ВСЕХ ПРОЦЕССОВ
echo "🛑 Шаг 1: Останавливаем ВСЕ процессы..."
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "python.*simple_telegram_bot.py" 2>/dev/null
pkill -9 -f "python.*no_telegram_bot.py" 2>/dev/null
sleep 3

# 2. ОСВОБОЖДЕНИЕ ВСЕХ ПОРТОВ
echo "🔓 Шаг 2: Освобождаем порты 8000-8005..."
for port in 8000 8001 8002 8003 8004 8005; do
    lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null
done
sleep 2

# 3. ПРОВЕРКА ПОРТОВ
echo "🔍 Шаг 3: Проверяем что порты свободны..."
if lsof -i:8000 > /dev/null 2>&1; then
    echo "⚠️ Порт 8000 всё еще занят, используем порт 8080"
    export PORT=8080
else
    echo "✅ Порт 8000 свободен"
    export PORT=8000
fi

# 4. ПРОВЕРКА ТОКЕНА
echo "🔑 Шаг 4: Проверяем токен..."
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не найден!"
    echo "💡 Убедитесь что токен в Replit Secrets"
    exit 1
fi
echo "✅ BOT_TOKEN найден: ${BOT_TOKEN:0:15}..."

# 5. СОЗДАНИЕ ДИРЕКТОРИЙ
echo "📁 Шаг 5: Создаем директории..."
mkdir -p logs
mkdir -p webapp/uploads
mkdir -p chatbotik/logs
mkdir -p chatbotik/webapp/uploads

# 6. ПРОВЕРКА ФАЙЛОВ
echo "📋 Шаг 6: Проверяем файлы..."
if [ ! -f "main.py" ]; then
    echo "❌ main.py не найден!"
    exit 1
fi
echo "✅ Все файлы на месте"

echo ""
echo "════════════════════════════════════════════════════════"
echo "🚀 ЗАПУСК ПРИЛОЖЕНИЯ"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📍 Директория: $(pwd)"
echo "🔌 Порт: $PORT"
echo "👤 Админ ID: 1593426947"
echo ""
echo "💡 Для остановки нажмите Ctrl+C"
echo ""

# 7. ЗАПУСК
python3 main.py

echo ""
echo "👋 Приложение остановлено"


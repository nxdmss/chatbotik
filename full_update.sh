#!/bin/bash
# Полное обновление и перезапуск

echo "🔄 ПОЛНОЕ ОБНОВЛЕНИЕ И ПЕРЕЗАПУСК"
echo "================================="

# 1. Обновляем проект из GitHub
echo "📥 Обновляем проект из GitHub..."
git pull origin main

# 2. Останавливаем ВСЕ процессы
echo "🛑 Останавливаем ВСЕ процессы..."
pkill -9 python 2>/dev/null
pkill -9 python3 2>/dev/null
killall -9 python 2>/dev/null
killall -9 python3 2>/dev/null
sleep 3

# 3. Освобождаем порт 8000
echo "🔓 Освобождаем порт 8000..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || echo "Порт 8000 свободен"
sleep 2

# 4. Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 perfect_server.py &
sleep 5

# 5. Проверяем работу
echo "✅ Проверяем работу сервера..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Сервер работает на http://localhost:8000"
else
    echo "❌ Ошибка запуска сервера"
    exit 1
fi

echo ""
echo "================================="
echo "✅ ПОЛНОЕ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "🌐 Веб-приложение: http://localhost:8000"
echo ""
echo "🔧 Теперь:"
echo "1. Откройте приложение через бота в Telegram Desktop"
echo "2. Должна появиться большая красная кнопка '🔧 ВКЛЮЧИТЬ АДМИН ПАНЕЛЬ'"
echo "3. Нажмите на кнопку"
echo "4. Админ панель появится мгновенно!"
echo ""
echo "🛑 Для остановки: Ctrl+C"
echo "================================="

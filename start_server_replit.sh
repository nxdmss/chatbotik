#!/bin/bash
# Скрипт для запуска сервера в Replit с другим портом

echo "============================================"
echo "🚀 ЗАПУСК СЕРВЕРА В REPLIT"
echo "============================================"

# Убиваем все Python процессы
echo "🛑 Останавливаем все Python процессы..."
pkill -9 -f "python" 2>/dev/null
sleep 2

# Проверяем доступность портов
echo "🔍 Проверяем доступные порты..."

# Пробуем порт 3000
if ! lsof -i :3000 >/dev/null 2>&1; then
    echo "✅ Порт 3000 свободен"
    PORT=3000
elif ! lsof -i :3001 >/dev/null 2>&1; then
    echo "✅ Порт 3001 свободен"
    PORT=3001
elif ! lsof -i :5000 >/dev/null 2>&1; then
    echo "✅ Порт 5000 свободен"
    PORT=5000
else
    echo "⚠️ Все порты заняты, используем 8000"
    PORT=8000
fi

echo "🌐 Используем порт: $PORT"

# Временно меняем порт в perfect_server.py
if [ "$PORT" != "8000" ]; then
    echo "🔧 Временно меняем порт на $PORT..."
    sed -i "s/PORT = 8000/PORT = $PORT/" perfect_server.py
fi

# Запускаем сервер
echo ""
echo "============================================"
echo "🚀 ЗАПУСК СЕРВЕРА НА ПОРТУ $PORT"
echo "============================================"
echo ""

python3 perfect_server.py

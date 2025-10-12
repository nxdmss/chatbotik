#!/bin/bash

echo "🛑 Останавливаем все Python процессы..."
pkill -9 python3 2>/dev/null
pkill -9 python 2>/dev/null
killall -9 python3 2>/dev/null
killall -9 python 2>/dev/null

echo "⏳ Ждем 3 секунды..."
sleep 3

echo "🔍 Проверяем порт 8000..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️ Порт 8000 все еще занят, убиваем процесс..."
    PID=$(lsof -t -i :8000)
    if [ ! -z "$PID" ]; then
        kill -9 $PID
        echo "✅ Процесс $PID убит"
        sleep 2
    fi
fi

echo "🚀 Запускаем сервер..."
python3 perfect_server.py


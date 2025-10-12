#!/bin/bash

# ===============================================
# 🔄 БЫСТРЫЙ ПЕРЕЗАПУСК
# ===============================================

echo "🔄 БЫСТРЫЙ ПЕРЕЗАПУСК"

# Останавливаем все
echo "🛑 Останавливаем..."
pkill -9 python 2>/dev/null || true
pkill -9 python3 2>/dev/null || true
sleep 1

# Освобождаем порт
echo "🔄 Освобождаем порт 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 perfect_server.py &
sleep 3

# Проверяем
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Сервер работает на http://localhost:8000"
    echo "👑 Нажмите зеленую кнопку '👑 Админ' в навигации"
else
    echo "❌ Сервер не запустился"
fi

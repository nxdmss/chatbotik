#!/bin/bash

echo "🚀 ЗАПУСК ПРОСТОГО МАГАЗИНА"
echo "=========================="

# Остановить все процессы
echo "🛑 Останавливаем процессы..."
pkill -9 python

# Запустить сервер
echo "🌐 Запускаем сервер..."
python3 simple_shop.py &

# Пауза для запуска
sleep 2

echo "✅ Готово!"
echo "🌐 Магазин: http://localhost:8000"
echo "🔑 Админ пароль: admin123"
echo ""
echo "🛑 Для остановки: Ctrl+C"

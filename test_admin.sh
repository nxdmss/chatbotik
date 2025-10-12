#!/bin/bash
# Тест админских прав

echo "🧪 ТЕСТ АДМИНСКИХ ПРАВ"
echo "======================"

# Останавливаем сервер
echo "🛑 Останавливаем сервер..."
pkill -9 python 2>/dev/null
sleep 2

# Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 perfect_server.py &
SERVER_PID=$!

sleep 3

# Тестируем API с правильным user_id
echo ""
echo "🔍 Тестируем API с правильным user_id (1593426947)..."
curl -s "http://localhost:8000/webapp/admin/products?user_id=1593426947" | head -c 200
echo ""

# Тестируем API с неправильным user_id
echo ""
echo "🔍 Тестируем API с неправильным user_id (1234567890)..."
curl -s "http://localhost:8000/webapp/admin/products?user_id=1234567890" | head -c 200
echo ""

# Тестируем API без user_id
echo ""
echo "🔍 Тестируем API без user_id..."
curl -s "http://localhost:8000/webapp/admin/products" | head -c 200
echo ""

# Останавливаем сервер
echo ""
echo "🛑 Останавливаем сервер..."
kill $SERVER_PID 2>/dev/null

echo ""
echo "✅ Тест завершен!"
echo "📋 Проверьте результаты выше"

#!/bin/bash
# Скрипт для быстрого обновления Replit

echo "============================================"
echo "🔄 ОБНОВЛЕНИЕ ПРОЕКТА ИЗ GITHUB"
echo "============================================"

# Сохраняем локальные изменения
echo ""
echo "💾 Сохраняем локальные изменения..."
git stash 2>/dev/null

# Получаем изменения с GitHub
echo ""
echo "📥 Скачиваем изменения с GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при получении изменений!"
    echo "Попробуйте вручную:"
    echo "  git stash"
    echo "  git pull origin main"
    exit 1
fi

# Убиваем процессы на порту 8000
echo ""
echo "🛑 Останавливаем старый сервер..."

# Агрессивная остановка всех Python процессов
echo "🔪 Убиваем все Python процессы..."
pkill -9 -f "python" 2>/dev/null
pkill -9 -f "perfect_server" 2>/dev/null
pkill -9 -f "main.py" 2>/dev/null

# Пытаемся использовать lsof (если есть)
if command -v lsof &> /dev/null; then
    echo "🔍 Ищем процессы на порту 8000..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null
fi

# Дополнительные попытки
fuser -k 8000/tcp 2>/dev/null
killall -9 python 2>/dev/null
killall -9 python3 2>/dev/null

sleep 3
echo "✅ Сервер остановлен"

# Проверяем базу данных
echo ""
echo "🔍 Проверяем базу данных..."

# Подсчитываем товары
PRODUCT_COUNT=0
if [ -f "shop.db" ]; then
    PRODUCT_COUNT=$(sqlite3 shop.db "SELECT COUNT(*) FROM products WHERE is_active=1;" 2>/dev/null || echo "0")
    echo "📊 Активных товаров в БД: $PRODUCT_COUNT"
fi

# Восстанавливаем только если БД пустая или нет товаров
if [ ! -f "shop.db" ] || [ "$PRODUCT_COUNT" -eq 0 ]; then
    echo "⚠️ База данных пустая!"
    echo "📦 Восстанавливаем базу данных..."
    
    # Сначала пытаемся восстановить из JSON
    python3 restore_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ База данных восстановлена"
    else
        echo "⚠️ Ошибка восстановления (возможно, БД уже в порядке)"
    fi
else
    echo "✅ База данных в порядке"
fi

# Запускаем сервер
echo ""
echo "============================================"
echo "🚀 ЗАПУСК СЕРВЕРА"
echo "============================================"
echo ""

python3 perfect_server.py


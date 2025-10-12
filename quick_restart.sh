#!/bin/bash

echo "⚡ БЫСТРЫЙ ПЕРЕЗАПУСК"
echo "===================="

# Остановка
pkill -9 python

# Очистка
rm -f shop_data.json

# Обновление
git pull origin main

# Создание папки
mkdir -p uploads

# Запуск
python3 simple_shop.py &
echo "✅ Сервер запущен на http://localhost:8000"
echo "🔑 Пароль админа: admin123"

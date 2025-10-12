#!/bin/bash

echo "🔄 ПОЛНОЕ ПЕРЕЗАПУСК МАГАЗИНА"
echo "=============================="

# Остановка всех процессов
echo "🛑 Останавливаем все Python процессы..."
pkill -9 python
sleep 3

# Удаление конфликтующих файлов
echo "🧹 Очищаем конфликтующие файлы..."
rm -f shop_data.json

# Обновление из GitHub
echo "📥 Обновляем проект из GitHub..."
git pull origin main

# Создание необходимых папок
echo "📁 Создаем необходимые папки..."
mkdir -p uploads

# Запуск сервера
echo "🚀 Запускаем сервер..."
python3 simple_shop.py &
SERVER_PID=$!

# Пауза для запуска
sleep 3

# Проверка работы сервера
echo "🔍 Проверяем работу сервера..."
if curl -s http://localhost:8000/api/products > /dev/null; then
    echo "✅ Сервер работает!"
    echo "🌐 Магазин: http://localhost:8000"
    echo "🔑 Админ пароль: admin123"
    echo "📷 Тест фото: http://localhost:8000/test-photo"
else
    echo "❌ Ошибка запуска сервера!"
    echo "Проверьте логи выше"
fi

echo ""
echo "🎉 ГОТОВО!"
echo "=============================="
echo "🛑 Для остановки: Ctrl+C"
echo "=============================="

# Ожидание завершения
wait $SERVER_PID

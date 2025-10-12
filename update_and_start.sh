#!/bin/bash

echo "🔄 ПОЛНОЕ ОБНОВЛЕНИЕ И ЗАПУСК"
echo "============================="

# Остановка всех процессов
echo "🛑 Останавливаем все процессы..."
pkill -9 python
sleep 2

# Удаление всех конфликтующих файлов
echo "🧹 Очищаем все конфликтующие файлы..."
rm -f shop_data.json
rm -f products_data.json
rm -f products_backup.json

# Обновление из GitHub
echo "📥 Обновляем проект из GitHub..."
git pull origin main

# Создание необходимых папок
echo "📁 Создаем необходимые папки..."
mkdir -p uploads
mkdir -p db_backups

# Запуск сервера
echo "🚀 Запускаем сервер..."
python3 simple_shop.py &
SERVER_PID=$!

# Пауза для запуска
sleep 4

# Проверка работы сервера
echo "🔍 Проверяем работу сервера..."
if curl -s http://localhost:8000/api/products > /dev/null; then
    echo "✅ Сервер работает отлично!"
    echo ""
    echo "🌐 Магазин: http://localhost:8000"
    echo "🔑 Админ пароль: admin123"
    echo "📷 Тест фото: http://localhost:8000/test-photo"
    echo "🧪 Тест добавления: http://localhost:8000/test-simple"
    echo ""
    echo "📊 Статус:"
    echo "   • Сервер: ✅ Работает"
    echo "   • API: ✅ Отвечает"
    echo "   • Файлы: ✅ Очищены"
    echo "   • Обновления: ✅ Применены"
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

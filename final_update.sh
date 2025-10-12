#!/bin/bash

echo "🚀 ФИНАЛЬНОЕ ОБНОВЛЕНИЕ ПРОЕКТА"
echo "================================="

# Остановка всех процессов
echo "🛑 Останавливаем все Python процессы..."
pkill -9 python
sleep 2

# Очистка конфликтующих файлов
echo "🧹 Очищаем конфликтующие файлы..."
rm -f enhanced_server.py final_server.py persistent_server.py photo_server.py secure_admin_server.py ultra_simple_server.py

# Сохранение изменений
echo "💾 Сохраняем локальные изменения..."
git stash

# Обновление из GitHub
echo "📥 Обновляем проект из GitHub..."
git pull origin main

# Создание необходимых папок
echo "📁 Создаем необходимые папки..."
mkdir -p uploads
mkdir -p logs

# Создание .env файла если не существует
if [ ! -f .env ]; then
    echo "📝 Создаем .env файл..."
    cat > .env << 'EOF'
BOT_TOKEN=your_bot_token_here
ADMIN_ID=1593426947
EOF
    echo "⚠️  ВАЖНО: Замените your_bot_token_here на реальный токен бота!"
fi

# Установка зависимостей
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

# Запуск рабочего сервера
echo "🚀 Запускаем рабочий сервер..."
python3 working_server.py &
SERVER_PID=$!

# Небольшая пауза для запуска сервера
sleep 3

# Проверка работы сервера
echo "🔍 Проверяем работу сервера..."
if curl -s http://localhost:8000/api/products > /dev/null; then
    echo "✅ Сервер работает!"
    echo "🌐 Магазин: http://localhost:8000"
    echo "🔑 Админ пароль: admin123"
else
    echo "❌ Ошибка запуска сервера!"
fi

echo ""
echo "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "================================="
echo "🌐 Веб-приложение: http://localhost:8000"
echo "🤖 Для запуска бота настройте токен в .env"
echo "🔒 АДМИН ПАРОЛЬ: admin123"
echo "📱 ОТКРОЙТЕ ПРИЛОЖЕНИЕ ЧЕРЕЗ БОТА В TELEGRAM!"
echo "🛑 Для остановки: Ctrl+C"
echo "================================="

# Ожидание завершения
wait $SERVER_PID

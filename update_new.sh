#!/bin/bash

# ===============================================
# 🚀 НОВЫЙ СКРИПТ ОБНОВЛЕНИЯ - ПРОСТОЙ И НАДЕЖНЫЙ
# ===============================================

# Функция для вывода сообщений
log() {
    echo "✅ $1"
}

error() {
    echo "❌ $1" >&2
}

warning() {
    echo "⚠️ $1"
}

echo "🚀 НОВОЕ ОБНОВЛЕНИЕ ПРОЕКТА"
echo "=================================="

# 1. Останавливаем все процессы Python
echo "🛑 Останавливаем процессы..."
pkill -9 python 2>/dev/null || true
pkill -9 python3 2>/dev/null || true
sleep 2

# 2. Освобождаем порт 8000
echo "🔄 Освобождаем порт 8000..."
if command -v lsof &> /dev/null; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
elif command -v fuser &> /dev/null; then
    fuser -k 8000/tcp 2>/dev/null || true
fi
sleep 1

# 3. Обновляем проект с GitHub
echo "📥 Обновляем с GitHub..."
git pull origin main

# 4. Проверяем .env файл
echo "📝 Проверяем .env файл..."
if [ ! -f ".env" ]; then
    warning "Создаем .env файл..."
    cat > .env << EOF
BOT_TOKEN=your_real_bot_token_here
WEBAPP_URL=http://localhost:8000
ADMINS=1593426947
LOG_LEVEL=INFO
EOF
    log ".env файл создан"
else
    log ".env файл существует"
fi

# 5. Проверяем базу данных
echo "💾 Проверяем базу данных..."
if [ ! -f "shop.db" ]; then
    warning "База данных не найдена, инициализируем..."
    python3 -c "
from database import Database
try:
    db = Database()
    db.init_database()
    print('✅ База данных инициализирована')
except Exception as e:
    print(f'⚠️ Ошибка инициализации БД: {e}')
" 2>/dev/null || warning "Не удалось инициализировать БД"
else
    log "База данных существует"
fi

# 6. Запускаем сервер в фоне
echo "🚀 Запускаем сервер..."
python3 perfect_server.py > server.log 2>&1 &
SERVER_PID=$!
log "Сервер запущен с PID: $SERVER_PID"

# 7. Ждем запуска сервера
echo "⏳ Ждем запуска сервера..."
sleep 5

# 8. Проверяем работу сервера
echo "🔍 Проверяем сервер..."
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    log "Сервер работает на http://localhost:8000"
else
    error "Сервер не отвечает!"
    echo "📋 Логи сервера:"
    tail -10 server.log 2>/dev/null || echo "Логи недоступны"
    exit 1
fi

# 9. Запускаем бота в фоне
echo "🤖 Запускаем бота..."
python3 main.py > bot.log 2>&1 &
BOT_PID=$!
log "Бот запущен с PID: $BOT_PID"

# 10. Финальная проверка
echo "🔍 Финальная проверка..."
sleep 2

if curl -s http://localhost:8000 > /dev/null 2>&1; then
    log "✅ ВСЕ ГОТОВО!"
    echo ""
    echo "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
    echo "=================================="
    echo "🌐 Веб-приложение: http://localhost:8000"
    echo "🤖 Бот запущен"
    echo "💾 База данных: shop.db"
    echo "👑 Админ: нажмите зеленую кнопку '👑 Админ' в навигации"
    echo ""
    echo "📊 Статус:"
    echo "   Сервер PID: $SERVER_PID"
    echo "   Бот PID: $BOT_PID"
    echo ""
    echo "🛑 Для остановки:"
    echo "   kill $SERVER_PID $BOT_PID"
    echo "=================================="
else
    error "Что-то пошло не так!"
    exit 1
fi

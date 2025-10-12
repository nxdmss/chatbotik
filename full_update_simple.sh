#!/bin/bash

echo "🚀 ПОЛНОЕ ОБНОВЛЕНИЕ С ПРОСТОЙ ЛОГИКОЙ"
echo "=============================================="

# 1. Останавливаем все процессы
echo "🛑 Останавливаем все процессы..."
pkill -9 python 2>/dev/null || true
pkill -f "perfect_server" 2>/dev/null || true
pkill -f "bot.py" 2>/dev/null || true
sleep 3

# 2. Обновляем с GitHub
echo "📥 Обновляем с GitHub..."
git pull origin main

# 3. Проверяем .env файл
echo "📝 Проверяем .env файл..."
if [ ! -f ".env" ]; then
    echo "⚠️ Создаем .env файл..."
    cat > .env << EOF
BOT_TOKEN=your_real_bot_token_here
EOF
    echo "✅ .env файл создан"
    echo "⚠️ ВНИМАНИЕ: В .env файле стоит заглушка токена!"
    echo "📝 Замените 'your_real_bot_token_here' на реальный токен бота"
    echo "🤖 Получите токен у @BotFather в Telegram"
else
    echo "✅ .env файл существует"
fi

# 4. Проверяем базу данных
echo "💾 Проверяем базу данных..."
if [ ! -f "shop.db" ]; then
    echo "⚠️ База данных не найдена, создаем..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('shop.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        photo TEXT,
        sizes TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print('✅ База данных создана')
"
else
    echo "✅ База данных существует"
fi

# 5. Запускаем сервер
echo "🚀 Запускаем веб-сервер..."
python3 perfect_server.py &

# 6. Ждем запуска
echo "⏳ Ждем запуска сервера..."
sleep 5

# 7. Проверяем работу
echo "🔍 Проверяем работу сервера..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Сервер работает на http://localhost:8000"
else
    echo "❌ Сервер не отвечает"
    exit 1
fi

echo ""
echo "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "=============================================="
echo "🌐 Веб-приложение: http://localhost:8000"
echo "🤖 Для запуска бота настройте токен в .env"
echo ""
echo "🔒 ЛОГИКА АДМИНСКИХ ПРАВ:"
echo "   👑 Ваш ID (1593426947) → АДМИН в Telegram"
echo "   👤 Все остальные → КЛИЕНТЫ в Telegram"
echo "   🔧 Браузер → отладочный режим"
echo ""
echo "📱 ОТКРОЙТЕ ПРИЛОЖЕНИЕ ЧЕРЕЗ БОТА В TELEGRAM!"
echo "🛑 Для остановки: Ctrl+C"
echo "=============================================="

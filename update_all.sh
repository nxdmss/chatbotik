#!/bin/bash
# Полное обновление проекта

echo "🔄 ПОЛНОЕ ОБНОВЛЕНИЕ ПРОЕКТА"
echo "============================"

# 1. Обновляем проект из GitHub
echo "📥 Обновляем проект из GitHub..."
git pull origin main

# 2. Останавливаем все процессы
echo "🛑 Останавливаем все процессы..."
pkill -9 python 2>/dev/null
pkill -9 python3 2>/dev/null
sleep 2

# 3. Запускаем сервер
echo "🚀 Запускаем сервер..."
python3 perfect_server.py &

# 4. Ждем запуска
sleep 3

echo ""
echo "✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "🌐 Веб-приложение: http://localhost:8000"
echo ""
echo "🔧 Для проверки админ панели:"
echo "1. Откройте приложение через бота в Telegram Desktop"
echo "2. Откройте консоль (Ctrl+Shift+I)"
echo "3. Проверьте логи версии 4.0"
echo "4. Админ панель должна появиться автоматически"
echo ""
echo "🛑 Для остановки: Ctrl+C"

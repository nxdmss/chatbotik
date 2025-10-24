#!/bin/bash

echo "🚀 ЗАПУСК ИСПРАВЛЕННОГО ПРИЛОЖЕНИЯ"
echo "=================================================="

# Устанавливаем BOT_TOKEN (замените на ваш токен)
export BOT_TOKEN="8226153553:AAHjK8QZQZQZQZQZQZQZQZQZQZQZQZQZQZQZQ"

# Устанавливаем ADMIN_PHONE
export ADMIN_PHONE="+7 (999) 123-45-67"

echo "✅ BOT_TOKEN установлен"
echo "✅ ADMIN_PHONE установлен"
echo ""

# Останавливаем предыдущие процессы
echo "🛑 Остановка предыдущих процессов..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*simple_telegram_bot.py" 2>/dev/null || true
pkill -f "python.*no_telegram_bot.py" 2>/dev/null || true

# Освобождаем порт 8000
echo "🔧 Освобождение порта 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

sleep 2

echo "🚀 Запуск исправленного приложения..."
echo "=================================================="

# Запускаем приложение
cd /Users/nxdms/Documents/GitHub/chatbot/chatbotik
python3 main.py

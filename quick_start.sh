#!/bin/bash
# Быстрый запуск для Replit

echo "🚀 Быстрый запуск сервера..."

# Убиваем все Python процессы
pkill -9 python 2>/dev/null
sleep 2

# Запускаем сервер
python3 perfect_server.py

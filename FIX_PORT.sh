#!/bin/bash
# 🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С ПОРТОМ

echo "🔧 ИСПРАВЛЕНИЕ ПОРТА..."
echo ""

# Убиваем ВСЕ процессы Python
echo "🛑 Останавливаем все Python процессы..."
pkill -9 -f python 2>/dev/null
sleep 2

# Освобождаем порты
echo "🔓 Освобождаем порты 8000-8005..."
for port in 8000 8001 8002 8003 8004 8005; do
    lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null
done
sleep 2

echo ""
echo "✅ Все процессы остановлены!"
echo "✅ Порты освобождены!"
echo ""
echo "Теперь запустите снова:"
echo "   ./REPLIT_RUN.sh"
echo ""


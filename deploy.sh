#!/bin/bash

# Скрипт для быстрого деплоя в Replit
echo "🚀 Подготовка к деплою в Replit..."

# Проверяем наличие необходимых файлов
echo "📋 Проверка файлов..."
required_files=(".replit" "replit.nix" "run.py" "bot.py" "server.py" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Отсутствует файл: $file"
        exit 1
    fi
done

echo "✅ Все необходимые файлы найдены"

# Создаем директорию для логов
mkdir -p logs

# Проверяем переменные окружения
echo "🔧 Проверка переменных окружения..."
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создайте его на основе env.replit.example"
    echo "📝 Скопируйте env.replit.example в .env и заполните данные"
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
python3 -m pip install -r requirements.txt

# Проверяем синтаксис Python файлов
echo "🐍 Проверка синтаксиса..."
python3 -m py_compile bot.py server.py run.py models.py error_handlers.py logger_config.py

if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен"
else
    echo "❌ Ошибки в синтаксисе"
    exit 1
fi

echo "🎉 Проект готов к деплою в Replit!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите проект в GitHub"
echo "2. Создайте новый Repl из GitHub"
echo "3. Настройте переменные окружения в Secrets"
echo "4. Запустите приложение"
echo ""
echo "📖 Подробная инструкция в файле REPLIT_SETUP.md"

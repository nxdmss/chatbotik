#!/bin/bash

echo "🚀 Запуск Telegram Shop Bot V2 - Enterprise Edition"
echo "=================================================="

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для проверки статуса
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# Запуск PostgreSQL
echo -e "\n${BLUE}📊 Запуск PostgreSQL...${NC}"
sudo service postgresql start
sleep 2
check_status "PostgreSQL запущен"

# Запуск Redis
echo -e "\n${BLUE}💾 Запуск Redis...${NC}"
sudo service redis-server start
sleep 2
check_status "Redis запущен"

# Проверка PostgreSQL
echo -e "\n${BLUE}🔍 Проверка PostgreSQL...${NC}"
sudo -u postgres psql -c "SELECT 1" > /dev/null 2>&1
check_status "PostgreSQL работает корректно"

# Проверка Redis
echo -e "\n${BLUE}🔍 Проверка Redis...${NC}"
redis-cli ping > /dev/null 2>&1
check_status "Redis работает корректно"

# Создание директорий
echo -e "\n${BLUE}📁 Создание директорий...${NC}"
mkdir -p uploads logs
check_status "Директории созданы"

# Проверка .env файла
echo -e "\n${BLUE}🔐 Проверка конфигурации...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo "Создайте .env файл из .env.example:"
    echo "cp .env.example .env"
    exit 1
fi
check_status "Конфигурация найдена"

# Запуск приложения
echo -e "\n${BLUE}🤖 Запуск приложения...${NC}"
echo "=================================================="
python main.py

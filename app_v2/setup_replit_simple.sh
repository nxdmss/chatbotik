#!/bin/bash

# 🚀 Упрощенная установка App V2 на Replit
# Запустите: ./setup_replit_simple.sh

set -e

echo "🎯 Быстрая настройка App V2 для Replit..."
echo ""

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Проверка .env
echo -e "${BLUE}📋 Шаг 1/6: Проверка конфигурации...${NC}"
if [ ! -f .env ] || grep -q "your_bot_token_here" .env 2>/dev/null; then
    echo -e "${RED}❌ Настройте .env файл!${NC}"
    echo -e "${YELLOW}   1. cp .env.example .env${NC}"
    echo -e "${YELLOW}   2. Заполните BOT_TOKEN и ADMIN_IDS${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Конфигурация OK${NC}"

# 2. PostgreSQL
echo ""
echo -e "${BLUE}🐘 Шаг 2/6: PostgreSQL...${NC}"
PGDATA_DIR="$HOME/.postgresql"
mkdir -p "$PGDATA_DIR"

if [ ! -f "$PGDATA_DIR/PG_VERSION" ]; then
    echo -e "${YELLOW}⚙️  Инициализация...${NC}"
    initdb -D "$PGDATA_DIR" -U postgres --auth=trust --locale=C --encoding=UTF8 >/dev/null 2>&1
fi

if ! pg_ctl -D "$PGDATA_DIR" status >/dev/null 2>&1; then
    echo -e "${YELLOW}🚀 Запуск...${NC}"
    pg_ctl -D "$PGDATA_DIR" -l "$PGDATA_DIR/logfile" -o "-k $PGDATA_DIR" start >/dev/null 2>&1
    sleep 2
fi
echo -e "${GREEN}✅ PostgreSQL работает${NC}"

# 3. База данных
echo ""
echo -e "${BLUE}💾 Шаг 3/6: База данных...${NC}"
if ! psql -h "$PGDATA_DIR" -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw shop_db; then
    echo -e "${YELLOW}⚙️  Создание БД...${NC}"
    psql -h "$PGDATA_DIR" -U postgres >/dev/null 2>&1 <<EOF
CREATE USER shopbot WITH PASSWORD 'shopbot_pass';
CREATE DATABASE shop_db OWNER shopbot;
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shopbot;
EOF
fi
echo -e "${GREEN}✅ База данных готова${NC}"

# 4. Redis
echo ""
echo -e "${BLUE}🚀 Шаг 4/6: Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}🚀 Запуск...${NC}"
    mkdir -p "$HOME/.redis"
    redis-server --daemonize yes --dir "$HOME/.redis" >/dev/null 2>&1
    sleep 1
fi
echo -e "${GREEN}✅ Redis работает${NC}"

# 5. Зависимости
echo ""
echo -e "${BLUE}📦 Шаг 5/6: Зависимости...${NC}"
pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
echo -e "${GREEN}✅ Зависимости установлены${NC}"

# 6. Директории
echo ""
echo -e "${BLUE}📁 Шаг 6/6: Директории...${NC}"
mkdir -p uploads logs
echo -e "${GREEN}✅ Структура создана${NC}"

# Готово!
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Готово! Запустите бота:${NC}"
echo -e "${BLUE}   python main.py${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

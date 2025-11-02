#!/bin/bash

# 🚀 Автоматическая установка App V2 на Replit
# Запустите: ./setup_replit.sh

set -e

echo "🎯 Настройка App V2 для Replit..."
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Проверка .env файла
echo -e "${BLUE}📋 Шаг 1: Проверка конфигурации...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}⚠️  Файл .env не найден. Копирую из .env.example...${NC}"
        cp .env.example .env
        echo -e "${RED}❌ ВАЖНО: Отредактируйте .env файл!${NC}"
        echo -e "${RED}   Добавьте: BOT_TOKEN, ADMIN_IDS, SECRET_KEY${NC}"
        echo -e "${RED}   Затем запустите скрипт снова.${NC}"
        exit 1
    else
        echo -e "${RED}❌ Файл .env.example не найден!${NC}"
        exit 1
    fi
fi

# Проверка обязательных переменных
if ! grep -q "BOT_TOKEN=" .env || grep -q "BOT_TOKEN=your_bot_token_here" .env; then
    echo -e "${RED}❌ BOT_TOKEN не настроен в .env!${NC}"
    echo -e "${YELLOW}   Получите токен у @BotFather и добавьте в .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Конфигурация найдена${NC}"

# 2. Инициализация PostgreSQL
echo ""
echo -e "${BLUE}🐘 Шаг 2: Настройка PostgreSQL...${NC}"

# Создаем директорию для данных PostgreSQL
PGDATA_DIR="$HOME/.postgresql"
mkdir -p "$PGDATA_DIR"

# Находим путь к PostgreSQL бинарникам
if command -v initdb &> /dev/null; then
    PG_BIN=""
elif [ -d "/nix/store" ]; then
    # Ищем PostgreSQL в Nix store
    PG_PATH=$(find /nix/store -name "postgresql-*" -type d 2>/dev/null | grep -v "dev\|doc\|man" | head -n 1)
    if [ -n "$PG_PATH" ]; then
        PG_BIN="$PG_PATH/bin/"
        export PATH="$PG_BIN:$PATH"
        echo -e "${GREEN}✅ Найден PostgreSQL: $PG_PATH${NC}"
    fi
fi

# Проверяем, инициализирована ли база
if [ ! -f "$PGDATA_DIR/PG_VERSION" ]; then
    echo -e "${YELLOW}⚙️  Инициализация PostgreSQL...${NC}"
    if command -v initdb &> /dev/null; then
        ${PG_BIN}initdb -D "$PGDATA_DIR" -U postgres --locale=C --encoding=UTF8
        echo -e "${GREEN}✅ PostgreSQL инициализирован${NC}"
    else
        echo -e "${RED}❌ initdb не найден. Убедитесь, что PostgreSQL установлен через Nix.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ PostgreSQL уже инициализирован${NC}"
fi

# Запускаем PostgreSQL
if ! ${PG_BIN}pg_ctl -D "$PGDATA_DIR" status > /dev/null 2>&1; then
    echo -e "${YELLOW}🚀 Запуск PostgreSQL...${NC}"
    ${PG_BIN}pg_ctl -D "$PGDATA_DIR" -l "$PGDATA_DIR/logfile" -o "-k $PGDATA_DIR" start
    sleep 3
    echo -e "${GREEN}✅ PostgreSQL запущен${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL уже работает${NC}"
fi

# 3. Создание базы данных и пользователя
echo ""
echo -e "${BLUE}💾 Шаг 3: Создание базы данных...${NC}"

# Проверяем, существует ли база
if ${PG_BIN}psql -h "$PGDATA_DIR" -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw shop_db; then
    echo -e "${GREEN}✅ База данных shop_db уже существует${NC}"
else
    echo -e "${YELLOW}⚙️  Создание базы данных и пользователя...${NC}"
    ${PG_BIN}psql -h "$PGDATA_DIR" -U postgres <<EOF
CREATE USER shopbot WITH PASSWORD 'shopbot_pass';
CREATE DATABASE shop_db OWNER shopbot;
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shopbot;
EOF
    echo -e "${GREEN}✅ База данных создана${NC}"
fi

# 4. Запуск Redis
echo ""
echo -e "${BLUE}🚀 Шаг 4: Настройка Redis...${NC}"

# Создаем директорию для Redis
REDIS_DIR="$HOME/.redis"
mkdir -p "$REDIS_DIR"

# Проверяем, запущен ли Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis уже работает${NC}"
else
    echo -e "${YELLOW}🚀 Запуск Redis...${NC}"
    redis-server --daemonize yes --dir "$REDIS_DIR" --dbfilename dump.rdb
    sleep 1
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis запущен${NC}"
    else
        echo -e "${RED}❌ Не удалось запустить Redis${NC}"
        exit 1
    fi
fi

# 5. Обновление .env для Replit
echo ""
echo -e "${BLUE}⚙️  Шаг 5: Настройка переменных окружения...${NC}"

# Обновляем DATABASE_URL если нужно
if grep -q "localhost:5432" .env; then
    echo -e "${YELLOW}⚙️  Обновление DATABASE_URL для Replit...${NC}"
    sed -i "s|postgresql+asyncpg://shopbot:shopbot_pass@localhost:5432/shop_db|postgresql+asyncpg://shopbot:shopbot_pass@$PGDATA_DIR:5432/shop_db?host=$PGDATA_DIR|g" .env
fi

echo -e "${GREEN}✅ Переменные окружения настроены${NC}"

# 6. Установка Python зависимостей
echo ""
echo -e "${BLUE}📦 Шаг 6: Установка зависимостей...${NC}"

if [ -f requirements-replit.txt ]; then
    pip install -q -r requirements-replit.txt
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
else
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
fi

# 7. Создание необходимых директорий
echo ""
echo -e "${BLUE}📁 Шаг 7: Создание директорий...${NC}"
mkdir -p uploads logs
echo -e "${GREEN}✅ Директории созданы${NC}"

# 8. Финальная проверка
echo ""
echo -e "${BLUE}🔍 Шаг 8: Финальная проверка...${NC}"

# Проверка PostgreSQL
if ${PG_BIN}psql -h "$PGDATA_DIR" -U shopbot -d shop_db -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL подключение работает${NC}"
else
    echo -e "${RED}❌ Ошибка подключения к PostgreSQL${NC}"
    exit 1
fi

# Проверка Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis подключение работает${NC}"
else
    echo -e "${RED}❌ Ошибка подключения к Redis${NC}"
    exit 1
fi

# 9. Готово!
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Установка завершена успешно!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📊 Информация о системе:${NC}"
echo -e "  🐘 PostgreSQL: ${GREEN}запущен${NC} (директория: $PGDATA_DIR)"
echo -e "  🚀 Redis: ${GREEN}запущен${NC}"
echo -e "  📁 База данных: ${GREEN}shop_db${NC}"
echo -e "  👤 Пользователь БД: ${GREEN}shopbot${NC}"
echo ""
echo -e "${YELLOW}🚀 Запустите бота:${NC}"
echo -e "   ${BLUE}python main.py${NC}"
echo ""
echo -e "${YELLOW}💡 Полезные команды:${NC}"
echo -e "   Проверить PostgreSQL: ${BLUE}${PG_BIN}psql -h $PGDATA_DIR -U shopbot -d shop_db${NC}"
echo -e "   Проверить Redis: ${BLUE}redis-cli ping${NC}"
echo -e "   Посмотреть логи: ${BLUE}tail -f logs/bot.log${NC}"
echo ""
echo -e "${GREEN}Приятной работы! 🎉${NC}"

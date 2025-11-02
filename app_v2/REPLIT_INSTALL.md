# 🚀 ПОЛНАЯ УСТАНОВКА App V2 на Replit

## Топовая версия БЕЗ КОМПРОМИССОВ
**PostgreSQL + Redis + FastAPI + aiogram 3.x + Clean Architecture**

---

## Шаг 1: Установка PostgreSQL на Replit (2 мин)

```bash
# В Shell на Replit выполните:
cd ~/workspace/chatbotik/app_v2

# Установка PostgreSQL
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14

# Запуск PostgreSQL
sudo service postgresql start

# Создание базы данных
sudo -u postgres psql -c "CREATE USER shopbot WITH PASSWORD 'shopbot_pass';"
sudo -u postgres psql -c "CREATE DATABASE shopbot OWNER shopbot;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shopbot TO shopbot;"
```

---

## Шаг 2: Установка Redis на Replit (1 мин)

```bash
# Установка Redis
sudo apt install -y redis-server

# Запуск Redis
sudo service redis-server start

# Проверка
redis-cli ping  # Должно вернуть: PONG
```

---

## Шаг 3: Установка зависимостей Python (2 мин)

```bash
cd ~/workspace/chatbotik/app_v2

# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости
pip install -r requirements.txt
```

---

## Шаг 4: Настройка .env файла (1 мин)

```bash
# Создаем .env из примера
cp .env.example .env

# Редактируем .env
nano .env
```

**Заполните обязательные переменные:**

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# Database (используйте эти значения для Replit)
DATABASE_URL=postgresql+asyncpg://shopbot:shopbot_pass@localhost:5432/shopbot

# Redis (используйте localhost)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-minimum-32-characters-long-random-string
ADMIN_IDS=your_telegram_user_id

# API
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=production
DEBUG=false
```

**Сохраните:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 5: Создание startup скрипта (1 мин)

```bash
cd ~/workspace/chatbotik/app_v2

# Создаем скрипт автозапуска
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Запуск Telegram Shop Bot V2..."

# Запуск PostgreSQL
echo "📊 Запуск PostgreSQL..."
sudo service postgresql start
sleep 2

# Запуск Redis
echo "💾 Запуск Redis..."
sudo service redis-server start
sleep 2

# Проверка сервисов
echo "✅ Проверка сервисов..."
sudo service postgresql status | grep "online"
redis-cli ping

# Запуск приложения
echo "🤖 Запуск бота..."
cd ~/workspace/chatbotik/app_v2
python main.py
EOF

# Делаем скрипт исполняемым
chmod +x start.sh
```

---

## Шаг 6: Запуск! (10 секунд)

```bash
cd ~/workspace/chatbotik/app_v2
./start.sh
```

**Или запустите напрямую:**

```bash
sudo service postgresql start
sudo service redis-server start
cd ~/workspace/chatbotik/app_v2
python main.py
```

---

## 🎉 Готово!

Теперь у вас работает:

✅ **PostgreSQL** - профессиональная СУБД  
✅ **Redis** - быстрый кэш  
✅ **FastAPI** - REST API с документацией  
✅ **aiogram 3.x** - современный Telegram Bot  
✅ **Clean Architecture** - правильная структура  
✅ **Async/Await** - максимальная производительность  

---

## 📊 Проверка работы

### 1. Проверка PostgreSQL:
```bash
psql -U shopbot -d shopbot -c "SELECT version();"
```

### 2. Проверка Redis:
```bash
redis-cli ping  # Должно вернуть: PONG
```

### 3. Проверка API:
```bash
curl http://localhost:8000/health
```

### 4. API Документация:
Откройте в браузере: `https://your-repl-name.your-username.repl.co:8000/docs`

---

## 🔄 Автозапуск при старте Replit

Добавьте в `.replit` файл в корне проекта:

```toml
run = "cd app_v2 && ./start.sh"
```

Или создайте новый `.replit`:

```bash
cd ~/workspace/chatbotik
cat > .replit << 'EOF'
run = "cd app_v2 && ./start.sh"
language = "python3"

[nix]
channel = "stable-22_11"

[deployment]
run = ["sh", "-c", "cd app_v2 && ./start.sh"]
EOF
```

---

## 🐛 Troubleshooting

### PostgreSQL не запускается:
```bash
sudo service postgresql restart
sudo -u postgres psql -c "SELECT 1"
```

### Redis не запускается:
```bash
sudo service redis-server restart
redis-cli ping
```

### Ошибка "Module not found":
```bash
cd ~/workspace/chatbotik/app_v2
pip install -r requirements.txt --force-reinstall
```

### Ошибка подключения к БД:
Проверьте DATABASE_URL в .env:
```bash
cat .env | grep DATABASE_URL
```

---

## 💡 Полезные команды

```bash
# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Логи Redis
sudo tail -f /var/log/redis/redis-server.log

# Логи приложения
tail -f logs/app.log

# Подключение к БД
psql -U shopbot -d shopbot

# Проверка Redis
redis-cli monitor
```

---

## 🚀 Production Ready!

Теперь у вас ПОЛНОЦЕННАЯ production-ready версия:

- 🏗️ **Clean Architecture** - легко поддерживать
- 📊 **PostgreSQL** - надежное хранилище
- ⚡ **Redis** - быстрый кэш
- 🔒 **Security** - все защищено
- 📈 **Scalable** - готово к росту
- 🧪 **Testable** - легко тестировать
- 📚 **Documented** - полная документация

**Никаких компромиссов! Только топ!** 🔥

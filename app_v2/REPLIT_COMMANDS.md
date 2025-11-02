# 🚀 Быстрая установка на Replit - копируй и вставляй

## ⚡ Вариант 1: Одной командой (рекомендуется)

Скопируйте и вставьте всё это в Shell на Replit:

```bash
cd ~/chatbotik/app_v2 && \
mkdir -p ~/.postgresql ~/.redis uploads logs && \
[ ! -f ~/.postgresql/PG_VERSION ] && initdb -D ~/.postgresql -U postgres --auth=trust --locale=C --encoding=UTF8 && \
pg_ctl -D ~/.postgresql status || pg_ctl -D ~/.postgresql -l ~/.postgresql/logfile -o "-k ~/.postgresql" start && \
redis-cli ping || redis-server --daemonize yes --dir ~/.redis && \
psql -h ~/.postgresql -U postgres -lqt | grep shop_db || psql -h ~/.postgresql -U postgres -c "CREATE USER shopbot WITH PASSWORD 'shopbot_pass'; CREATE DATABASE shop_db OWNER shopbot; GRANT ALL PRIVILEGES ON DATABASE shop_db TO shopbot;" && \
pip install -q -r requirements.txt && \
echo "✅ Готово! Запустите: python main.py"
```

---

## 📝 Вариант 2: По шагам (если первый не работает)

### 1. Перейдите в папку проекта
```bash
cd ~/chatbotik/app_v2
```

### 2. Создайте .env (если нет)
```bash
cp .env.example .env
nano .env
```
Заполните: `BOT_TOKEN`, `ADMIN_IDS`, `SECRET_KEY`

### 3. Инициализируйте PostgreSQL
```bash
mkdir -p ~/.postgresql
initdb -D ~/.postgresql -U postgres --auth=trust --locale=C --encoding=UTF8
```

### 4. Запустите PostgreSQL
```bash
pg_ctl -D ~/.postgresql -l ~/.postgresql/logfile -o "-k ~/.postgresql" start
```

### 5. Создайте базу данных
```bash
psql -h ~/.postgresql -U postgres
```

В консоли PostgreSQL выполните:
```sql
CREATE USER shopbot WITH PASSWORD 'shopbot_pass';
CREATE DATABASE shop_db OWNER shopbot;
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shopbot;
\q
```

### 6. Запустите Redis
```bash
mkdir -p ~/.redis
redis-server --daemonize yes --dir ~/.redis
```

### 7. Проверьте Redis
```bash
redis-cli ping
```
Должно ответить: `PONG`

### 8. Установите зависимости
```bash
pip install -r requirements.txt
```

### 9. Создайте директории
```bash
mkdir -p uploads logs
```

### 10. Запустите бота!
```bash
python main.py
```

---

## 🐛 Если что-то не работает

### PostgreSQL не запускается:
```bash
pg_ctl -D ~/.postgresql stop
rm -rf ~/.postgresql/*
initdb -D ~/.postgresql -U postgres --auth=trust --locale=C --encoding=UTF8
pg_ctl -D ~/.postgresql -l ~/.postgresql/logfile -o "-k ~/.postgresql" start
```

### Redis не работает:
```bash
redis-cli shutdown
redis-server --daemonize yes --dir ~/.redis
redis-cli ping
```

### Команды не найдены:
Убедитесь, что модули добавлены в `.replit`:
```
modules = ["python-3.11", "postgresql-15", "redis-7"]
```

Затем перезапустите Repl.

---

## ✅ Проверка работы

```bash
# PostgreSQL
psql -h ~/.postgresql -U shopbot -d shop_db -c "SELECT 1"

# Redis
redis-cli ping

# Python зависимости
python -c "import aiogram; print('✅ aiogram OK')"
```

---

## 🎯 Запуск бота

```bash
cd ~/chatbotik/app_v2
python main.py
```

Всё! 🚀

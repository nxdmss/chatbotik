# 📦 Полный гайд по установке проекта

## 🎯 Что вы получите

- ✅ Профессиональный Telegram-бот для магазина
- ✅ Web-приложение с современным UI
- ✅ Enterprise версию с PostgreSQL + Redis (опционально)
- ✅ Готовую к продакшену систему

---

## 📋 Оглавление

1. [Быстрый старт (5 минут)](#быстрый-старт)
2. [Установка на Windows](#установка-на-windows)
3. [Установка на macOS](#установка-на-macos)
4. [Установка на Linux](#установка-на-linux)
5. [Установка на Replit](#установка-на-replit)
6. [Enterprise версия (App V2)](#enterprise-версия)
7. [Решение проблем](#решение-проблем)

---

## 🚀 Быстрый старт

### Шаг 1: Установите Git и Python

**Проверьте, установлены ли они:**
```bash
git --version
python3 --version
```

**Если нет, установите:**
- **Git**: https://git-scm.com/downloads
- **Python 3.11+**: https://www.python.org/downloads/

### Шаг 2: Скачайте проект

```bash
# Перейдите в папку, куда хотите скачать проект
cd ~/Documents

# Клонируйте репозиторий
git clone https://github.com/nxdmss/chatbotik.git

# Перейдите в папку проекта
cd chatbotik
```

### Шаг 3: Создайте виртуальное окружение

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте его
# На macOS/Linux:
source venv/bin/activate

# На Windows:
venv\Scripts\activate
```

### Шаг 4: Установите зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 5: Настройте бота

1. **Получите токен бота:**
   - Откройте Telegram
   - Найдите @BotFather
   - Отправьте `/newbot`
   - Следуйте инструкциям
   - Скопируйте токен

2. **Создайте файл .env:**
```bash
# Скопируйте пример
cp env.example .env

# Откройте .env в любом редакторе
nano .env
# или
code .env
```

3. **Заполните .env:**
```env
# Telegram Bot Token от @BotFather
BOT_TOKEN=your_bot_token_here

# Ваш Telegram ID (узнайте у @userinfobot)
ADMIN_IDS=123456789

# Секретный ключ (любая случайная строка)
SECRET_KEY=your_random_secret_key_here

# База данных (для старта можно не менять)
DATABASE_URL=sqlite:///./shop.db
```

### Шаг 6: Запустите бота

```bash
python main.py
```

**Готово! 🎉** Найдите своего бота в Telegram и отправьте `/start`

---

## 💻 Установка на Windows

### 1. Установите необходимые программы

**Git:**
1. Скачайте с https://git-scm.com/download/win
2. Запустите установщик
3. Используйте настройки по умолчанию

**Python 3.11+:**
1. Скачайте с https://www.python.org/downloads/
2. ⚠️ **ВАЖНО**: Поставьте галочку "Add Python to PATH"
3. Нажмите "Install Now"

### 2. Откройте PowerShell или Command Prompt

Нажмите `Win + R`, введите `powershell`, нажмите Enter

### 3. Скачайте проект

```powershell
# Перейдите в папку для проектов
cd C:\Users\ВашеИмя\Documents

# Клонируйте репозиторий
git clone https://github.com/nxdmss/chatbotik.git

# Перейдите в папку
cd chatbotik
```

### 4. Создайте виртуальное окружение

```powershell
# Создайте venv
python -m venv venv

# Активируйте
venv\Scripts\activate

# Должно появиться (venv) в начале строки
```

### 5. Установите зависимости

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Настройте .env

```powershell
# Скопируйте пример
copy env.example .env

# Откройте блокнотом
notepad .env
```

Заполните как в [Шаге 5 быстрого старта](#шаг-5-настройте-бота)

### 7. Запустите

```powershell
python main.py
```

---

## 🍎 Установка на macOS

### 1. Установите Homebrew (если нет)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Установите необходимое

```bash
# Git и Python
brew install git python@3.11
```

### 3. Скачайте проект

```bash
# Перейдите в Documents
cd ~/Documents

# Клонируйте
git clone https://github.com/nxdmss/chatbotik.git
cd chatbotik
```

### 4. Создайте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Установите зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Настройте и запустите

```bash
# Скопируйте .env
cp env.example .env

# Откройте в редакторе
nano .env
# или
open -a TextEdit .env

# Заполните данные и сохраните

# Запустите
python main.py
```

---

## 🐧 Установка на Linux

### Ubuntu/Debian

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите необходимое
sudo apt install -y git python3 python3-pip python3-venv

# Скачайте проект
cd ~
git clone https://github.com/nxdmss/chatbotik.git
cd chatbotik

# Создайте venv
python3 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Настройте .env
cp env.example .env
nano .env

# Запустите
python main.py
```

### CentOS/RHEL/Fedora

```bash
# Установите необходимое
sudo dnf install -y git python3 python3-pip

# Дальше как в Ubuntu
cd ~
git clone https://github.com/nxdmss/chatbotik.git
cd chatbotik

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp env.example .env
nano .env

python main.py
```

---

## ☁️ Установка на Replit

### Вариант 1: Простая версия (SQLite)

1. **Откройте Replit:**
   - Перейдите на https://replit.com
   - Войдите в аккаунт

2. **Импортируйте проект:**
   - Нажмите "Create Repl"
   - Выберите "Import from GitHub"
   - Вставьте: `https://github.com/nxdmss/chatbotik`
   - Нажмите "Import from GitHub"

3. **Настройте Secrets:**
   - Нажмите на замочек 🔒 слева
   - Добавьте переменные:
   ```
   BOT_TOKEN = ваш_токен_от_BotFather
   ADMIN_IDS = ваш_telegram_id
   SECRET_KEY = любая_случайная_строка
   DATABASE_URL = sqlite:///./shop.db
   ```

4. **Запустите:**
   - Нажмите зеленую кнопку "Run"
   - Бот запустится автоматически!

### Вариант 2: Enterprise версия (PostgreSQL + Redis)

📖 **Полная инструкция:** [app_v2/REPLIT_INSTALL.md](app_v2/REPLIT_INSTALL.md)

**Краткая версия:**

1. **Импортируйте проект** (как выше)

2. **Установите PostgreSQL:**
```bash
sudo apt update
sudo apt install -y postgresql-14 postgresql-contrib
sudo service postgresql start
```

3. **Создайте базу данных:**
```bash
sudo -u postgres psql
```
```sql
CREATE USER shopbot WITH PASSWORD 'shopbot_pass';
CREATE DATABASE shop_db OWNER shopbot;
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shopbot;
\q
```

4. **Установите Redis:**
```bash
sudo apt install -y redis-server
redis-server --daemonize yes
```

5. **Настройте .env:**
```env
BOT_TOKEN=ваш_токен
ADMIN_IDS=ваш_id
SECRET_KEY=случайная_строка
DATABASE_URL=postgresql+asyncpg://shopbot:shopbot_pass@localhost:5432/shop_db
REDIS_URL=redis://localhost:6379/0
```

6. **Запустите:**
```bash
cd app_v2
./start.sh
```

---

## 🏢 Enterprise версия (App V2)

### Что это?

- ✨ Clean Architecture
- 🐘 PostgreSQL (вместо SQLite)
- 🚀 Redis для кэширования
- 🎯 Type Safety (mypy strict)
- 🐳 Docker support
- 📊 Structured logging
- 🔒 Pydantic validation

### Установка локально

**1. Установите зависимости системы:**

**macOS:**
```bash
brew install postgresql@14 redis
brew services start postgresql@14
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install -y postgresql-14 postgresql-contrib redis-server
sudo systemctl start postgresql
sudo systemctl start redis
```

**2. Создайте базу данных:**
```bash
sudo -u postgres psql
```
```sql
CREATE USER shopbot WITH PASSWORD 'shopbot_pass';
CREATE DATABASE shop_db OWNER shopbot;
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shopbot;
\q
```

**3. Настройте проект:**
```bash
cd app_v2

# Скопируйте .env
cp .env.example .env

# Отредактируйте .env
nano .env
```

**4. Установите Python зависимости:**
```bash
# Из корня проекта
cd ..
source venv/bin/activate
cd app_v2
pip install -r requirements.txt
```

**5. Запустите:**
```bash
chmod +x start.sh
./start.sh
```

### Установка через Docker

```bash
cd app_v2

# Создайте .env
cp .env.example .env
nano .env

# Запустите через Docker Compose
docker-compose up -d

# Проверьте логи
docker-compose logs -f
```

---

## 🔧 Решение проблем

### Проблема: "python: command not found"

**Решение:**
```bash
# Попробуйте
python3 --version

# Если работает, используйте python3 вместо python
python3 main.py
```

### Проблема: "pip: command not found"

**Решение:**
```bash
# macOS/Linux
python3 -m pip install --upgrade pip

# Windows
python -m pip install --upgrade pip
```

### Проблема: "ModuleNotFoundError: No module named 'aiogram'"

**Решение:**
```bash
# Убедитесь, что venv активирован
# Должно быть (venv) в начале строки

# Переустановите зависимости
pip install -r requirements.txt
```

### Проблема: "Invalid bot token"

**Решение:**
1. Проверьте, что токен скопирован полностью
2. Проверьте, нет ли лишних пробелов
3. Получите новый токен у @BotFather:
   - `/revoke` - отменить старый
   - Создайте нового бота

### Проблема: "Permission denied: './start.sh'"

**Решение:**
```bash
chmod +x start.sh
./start.sh
```

### Проблема: PostgreSQL не запускается

**Решение:**
```bash
# Проверьте статус
sudo service postgresql status

# Перезапустите
sudo service postgresql restart

# Проверьте логи
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Проблема: Redis не подключается

**Решение:**
```bash
# Проверьте, запущен ли Redis
redis-cli ping
# Должно ответить: PONG

# Если нет, запустите
redis-server --daemonize yes
```

### Проблема: "Port already in use"

**Решение:**
```bash
# Найдите процесс на порту 8000
lsof -i :8000

# Убейте процесс
kill -9 <PID>

# Или измените порт в .env
PORT=8001
```

---

## 📚 Дополнительные ресурсы

### Документация

- 📖 [README.md](README.md) - Основная документация
- 🚀 [QUICK_START.md](QUICK_START.md) - Быстрый старт
- 📋 [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) - Полное руководство
- 🏢 [app_v2/README.md](app_v2/README.md) - Enterprise версия
- ☁️ [app_v2/REPLIT_INSTALL.md](app_v2/REPLIT_INSTALL.md) - Установка на Replit

### Полезные команды

```bash
# Обновить проект
git pull origin main

# Проверить статус Git
git status

# Посмотреть логи
tail -f logs/bot.log

# Остановить бота
Ctrl + C

# Деактивировать venv
deactivate

# Активировать venv снова
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

---

## 🎓 Что дальше?

1. **Настройте бота под себя:**
   - Измените тексты приветствия
   - Добавьте свои товары
   - Настройте дизайн WebApp

2. **Изучите функции:**
   - Админ-панель: `/admin`
   - Каталог товаров: WebApp
   - Управление заказами

3. **Разверните в продакшн:**
   - Используйте Replit или VPS
   - Настройте домен
   - Добавьте мониторинг

4. **Доработайте под нужды:**
   - Интеграция с платежами
   - Уведомления в Telegram
   - Аналитика продаж

---

## 💬 Поддержка

Если что-то не работает:

1. **Проверьте раздел** [Решение проблем](#решение-проблем)
2. **Посмотрите логи:** `logs/bot.log`
3. **Проверьте .env:** все ли переменные заполнены
4. **Создайте Issue** на GitHub

---

## ✨ Успешного запуска!

**Теперь у вас есть:**
- ✅ Полный гайд по установке
- ✅ Инструкции для всех платформ
- ✅ Решение типичных проблем
- ✅ Готовый к работе бот

**Приятной работы! 🚀**

---

*Последнее обновление: 2 ноября 2025 г.*

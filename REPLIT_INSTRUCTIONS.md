# 🚀 Инструкции для запуска в Replit

## 📋 Настройка Preview Run

### Вариант 1: Через скрипт (рекомендуется)
1. Откройте **Preview Run** в Replit
2. Введите команду: `bash run.sh`
3. Нажмите **Run**

### Вариант 2: Через Python
1. Откройте **Preview Run** в Replit  
2. Введите команду: `python3 start_replit.py`
3. Нажмите **Run**

### Вариант 3: Через main.py
1. Откройте **Preview Run** в Replit
2. Введите команду: `python3 main.py`
3. Нажмите **Run**

## 🔧 Что происходит при запуске:

1. **Создаются папки:** `uploads/`, `db_backups/`
2. **Очищаются конфликты:** удаляется `shop_data.json`
3. **Запускается сервер:** на порту 8000
4. **Запускается бот:** Telegram бот

## 📱 Доступные ссылки:

- **Магазин:** http://localhost:8000
- **Админ панель:** пароль `admin123`
- **Тест фото:** http://localhost:8000/test-photo
- **Тест добавления:** http://localhost:8000/test-simple

## 🤖 Настройка бота:

1. Создайте файл `.env` с токеном бота:
```
BOT_TOKEN=your_bot_token_here
```

2. Получите токен у @BotFather в Telegram

## 🛑 Остановка:

Нажмите **Ctrl+C** в Preview Run для остановки всех процессов

## 🔄 Обновление:

Для обновления используйте:
```bash
bash update_and_start.sh
```

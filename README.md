# 🛍️ Улучшенный Telegram Shop Bot

Версия 2.0 с валидацией данных, структурированным логированием, обработкой ошибок и **мобильным приложением с тремя отдельными страницами**.

## 🚀 Быстрый старт в Replit

1. **Создайте Repl** из этого GitHub репозитория
2. **Настройте переменные** в Secrets (см. `REPLIT_SETUP.md`)
3. **Запустите** приложение кнопкой "Run"
4. **Настройте WebApp** в @BotFather

📖 **Подробная инструкция**: [REPLIT_SETUP.md](REPLIT_SETUP.md)

## 🚀 Новые возможности

### ✅ Что добавлено:

1. **Валидация данных с Pydantic**
   - Строгая типизация всех моделей данных
   - Автоматическая валидация пользовательского ввода
   - Защита от некорректных данных

2. **Структурированное логирование**
   - JSON логи с подробной информацией
   - Отдельные логгеры для разных компонентов
   - Логирование всех действий пользователей и администраторов

3. **Обработка ошибок**
   - Централизованная обработка исключений
   - Понятные сообщения об ошибках для пользователей
   - Автоматическое восстановление после сбоев

4. **Улучшенная безопасность**
   - Валидация всех входных данных
   - Проверка прав доступа
   - Санитизация пользовательского ввода

5. **Мониторинг и метрики**
   - Health check endpoint
   - Метрики сервера
   - Отслеживание производительности

## 📁 Структура файлов

```
chatbotik/
├── bot_improved.py          # Улучшенный бот с валидацией
├── server_improved.py       # Улучшенный FastAPI сервер
├── models.py                # Pydantic модели данных
├── logger_config.py         # Конфигурация логирования
├── error_handlers.py        # Обработчики ошибок
├── run_improved.py          # Скрипт запуска
├── config_example.env       # Пример конфигурации
├── requirements.txt         # Обновленные зависимости
└── logs/                    # Директория логов
```

## 🛠️ Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

```bash
# Скопируйте пример конфигурации
cp config_example.env .env

# Отредактируйте .env файл
nano .env
```

Обязательные параметры:
- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMINS` - ID администраторов через запятую
- `WEBAPP_URL` - URL вашего WebApp

### 3. Запуск

#### Простой запуск:
```bash
python run_improved.py
```

#### Ручной запуск:

**Только бот:**
```bash
python bot_improved.py
```

**Только WebApp сервер:**
```bash
python server_improved.py
```

**Одновременно:**
```bash
# В первом терминале
python server_improved.py

# Во втором терминале
python bot_improved.py
```

## 📊 Логирование

### Структура логов

Логи сохраняются в директории `logs/` в JSON формате:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "logger": "bot",
  "event": "user_action",
  "user_id": "123456789",
  "action": "start_command"
}
```

### Типы логов

- **user_action** - действия пользователей
- **admin_action** - действия администраторов
- **order_created** - создание заказов
- **payment_received** - получение платежей
- **error_occurred** - ошибки
- **security_event** - события безопасности

### Просмотр логов

```bash
# Просмотр всех логов
tail -f logs/bot.log

# Фильтрация по типу события
grep "user_action" logs/bot.log

# Поиск ошибок
grep "error_occurred" logs/bot.log
```

## 🔧 API Endpoints

### WebApp API

- `GET /webapp/products.json` - список товаров
- `GET /webapp/admins.json` - список администраторов
- `POST /webapp/upload` - загрузка файлов
- `POST /webapp/add_product?admin=1` - добавление товара
- `POST /webapp/delete_product?admin=1` - удаление товара
- `POST /webapp/restore_product?admin=1` - восстановление товара

### Системные API

- `GET /health` - проверка здоровья сервера
- `GET /metrics` - метрики сервера

## 🛡️ Безопасность

### Валидация данных

Все пользовательские данные проходят валидацию:

```python
# Пример валидации заказа
order = OrderCreate(
    text="Описание заказа",
    items=[CartItem(...)],
    total=1000
)
```

### Проверка прав доступа

```python
# Проверка администратора
validate_admin_access(user_id, ADMINS)
```

### Санитизация ввода

```python
# Очистка пользовательского ввода
clean_text = validate_user_input(user_input, max_length=1000)
```

## 📈 Мониторинг

### Health Check

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "products": "ok",
    "uploads": "ok"
  }
}
```

### Метрики

```bash
curl http://localhost:8000/metrics
```

Ответ:
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "products_count": 15,
  "uploads_count": 8,
  "uptime": "2h 30m"
}
```

## 🐛 Отладка

### Включение отладочного режима

```bash
# В .env файле
LOG_LEVEL=DEBUG
```

### Просмотр ошибок

```bash
# Все ошибки
grep "error_occurred" logs/bot.log

# Ошибки конкретного пользователя
grep "user_id.*123456789" logs/bot.log | grep "error_occurred"
```

### Тестирование API

```bash
# Проверка товаров
curl http://localhost:8000/webapp/products.json

# Проверка администраторов
curl http://localhost:8000/webapp/admins.json
```

## 🔄 Миграция с старой версии

### 1. Резервное копирование

```bash
# Создайте резервную копию данных
cp orders.json orders_backup.json
cp shop/products.json shop/products_backup.json
```

### 2. Обновление зависимостей

```bash
pip install -r requirements.txt
```

### 3. Тестирование

```bash
# Запустите в тестовом режиме
LOG_LEVEL=DEBUG python run_improved.py
```

### 4. Переключение

```bash
# Переименуйте старые файлы
mv bot.py bot_old.py
mv server.py server_old.py

# Переименуйте новые файлы
mv bot_improved.py bot.py
mv server_improved.py server.py
```

## 📝 Changelog

### v2.0.0
- ✅ Добавлена валидация данных с Pydantic
- ✅ Реализовано структурированное логирование
- ✅ Добавлена обработка ошибок
- ✅ Улучшена безопасность
- ✅ Добавлен мониторинг и метрики
- ✅ Создан скрипт автоматического запуска

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи в `logs/bot.log`
2. Убедитесь в корректности конфигурации
3. Проверьте доступность всех зависимостей
4. Обратитесь к документации API

## 📄 Лицензия

MIT License - используйте свободно для коммерческих и некоммерческих проектов.

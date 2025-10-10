# 🚀 Интеграция с Replit

## 📋 Пошаговая инструкция

### 1. Создание Repl

1. Зайдите на [replit.com](https://replit.com)
2. Нажмите **"Create Repl"**
3. Выберите **"Import from GitHub"**
4. Вставьте URL вашего репозитория
5. Нажмите **"Import"**

### 2. Настройка переменных окружения

1. В Replit откройте **Secrets** (🔒 иконка слева)
2. Добавьте следующие переменные:

```
BOT_TOKEN=ваш_токен_бота_от_BotFather
ADMIN_IDS=ваш_telegram_id,id_другого_админа
WEBAPP_URL=https://ваш-repl-name.ваш-username.repl.co
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DEBUG=false
```

### 3. Получение токена бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Придумайте имя и username для бота
4. Скопируйте полученный токен
5. Вставьте в переменную `BOT_TOKEN`

### 4. Получение вашего Telegram ID

1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте любое сообщение
3. Скопируйте ваш ID
4. Вставьте в переменную `ADMIN_IDS`

### 5. Запуск приложения

1. В Replit нажмите **"Run"** (▶️ кнопка)
2. Дождитесь установки зависимостей
3. Приложение запустится автоматически

### 6. Настройка WebApp в Telegram

1. Найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/setmenubutton`
3. Выберите вашего бота
4. Отправьте URL: `https://ваш-repl-name.ваш-username.repl.co/webapp/`
5. Отправьте текст кнопки: `🛍 Открыть магазин`

## 🔧 Структура проекта

```
chatbotik/
├── .replit                 # Конфигурация Replit
├── replit.nix             # Зависимости Nix
├── run.py                 # Главный файл запуска
├── bot.py                 # Telegram бот
├── server.py              # FastAPI сервер
├── models.py              # Pydantic модели
├── error_handlers.py      # Обработчики ошибок
├── logger_config.py       # Настройки логирования
├── requirements.txt       # Python зависимости
├── webapp/                # Мобильное приложение
│   ├── index.html         # HTML с тремя страницами
│   ├── app.js             # JavaScript логика
│   ├── styles.css         # Мобильные стили
│   └── manifest.json      # PWA манифест
└── shop/                  # Данные магазина
    └── products.json      # Товары
```

## 📱 Мобильное приложение

Ваше приложение имеет **три отдельные страницы**:

- **🛍 Каталог** - просмотр и покупка товаров
- **🛒 Корзина** - управление заказами  
- **👤 Профиль** - личная информация

## 🌐 Доступ к приложению

После запуска в Replit:

- **WebApp URL**: `https://ваш-repl-name.ваш-username.repl.co/webapp/`
- **API**: `https://ваш-repl-name.ваш-username.repl.co/api/`
- **Админ панель**: `https://ваш-repl-name.ваш-username.repl.co/admin/`

## 🐛 Решение проблем

### Ошибка "Module not found"
```bash
pip install -r requirements.txt
```

### Ошибка "Port already in use"
```bash
pkill -f python
python run.py
```

### Ошибка "Bot token invalid"
Проверьте правильность токена в Secrets

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в Replit Console
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что бот запущен и отвечает

## 🎯 Готово!

Ваш Telegram магазин с мобильным приложением готов к работе в Replit! 🚀

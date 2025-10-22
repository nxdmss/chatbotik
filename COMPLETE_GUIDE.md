# 🚀 ПОЛНЫЙ ГАЙД ПО НАСТРОЙКЕ И РАБОТЕ С БОТОМ

## 📋 СОДЕРЖАНИЕ
1. [Быстрый старт](#быстрый-старт)
2. [Настройка переменных окружения](#настройка-переменных-окружения)
3. [Структура проекта](#структура-проекта)
4. [Настройка бота](#настройка-бота)
5. [Настройка WebApp](#настройка-webapp)
6. [Работа с товарами](#работа-с-товарами)
7. [Система заказов](#система-заказов)
8. [Админ-панель](#админ-панель)
9. [Кастомизация](#кастомизация)
10. [Развертывание](#развертывание)
11. [Решение проблем](#решение-проблем)

---

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Клонирование и запуск
```bash
git clone https://github.com/your-username/chatbotik.git
cd chatbotik
./FIX_AND_RUN.sh
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
ADMIN_PHONE=+7(999)123-45-67
```

### 3. Запуск на Replit
```bash
cd /home/runner/workspace/chatbotik && git pull origin main && ./FIX_AND_RUN.sh
```

---

## 🔧 НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ

### Обязательные переменные:
- **BOT_TOKEN** - токен вашего Telegram бота от @BotFather
- **ADMIN_IDS** - ID администраторов (через запятую)
- **ADMIN_PHONE** - номер телефона для СБП платежей

### Дополнительные переменные:
- **PORT** - порт для веб-сервера (по умолчанию 8000)
- **DEBUG** - режим отладки (true/false)

### Пример .env файла:
```env
# Основные настройки
BOT_TOKEN=8226153553:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
ADMIN_IDS=1593426947,123456789
ADMIN_PHONE=+7(999)123-45-67

# Дополнительные настройки
PORT=8000
DEBUG=false
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
chatbotik/
├── main.py                          # Главный файл запуска
├── chatbotik/
│   ├── main.py                      # Основная логика приложения
│   ├── simple_telegram_bot.py       # Веб-сервер и API
│   ├── no_telegram_bot.py          # Telegram бот поддержки
│   ├── customer_support.db         # База данных поддержки
│   ├── shop.db                     # База данных магазина
│   ├── uploads/                    # Загруженные изображения
│   └── requirements.txt             # Зависимости Python
├── webapp/
│   ├── index.html                  # Интерфейс WebApp
│   ├── app.js                      # JavaScript логика
│   ├── styles.css                  # Стили
│   ├── products.json               # Каталог товаров
│   └── uploads/                    # Изображения товаров
├── FIX_AND_RUN.sh                  # Скрипт запуска
└── README.md                       # Документация
```

---

## 🤖 НАСТРОЙКА БОТА

### 1. Создание бота в Telegram
1. Напишите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям
4. Сохраните полученный токен

### 2. Настройка WebApp
1. Отправьте @BotFather команду `/newapp`
2. Выберите вашего бота
3. Укажите название и описание
4. Загрузите изображение (опционально)
5. Укажите URL вашего WebApp (например: `https://your-repl-url.repl.co`)

### 3. Настройка меню бота
```python
# В файле no_telegram_bot.py можно настроить меню:
menu_commands = [
    {"command": "start", "description": "🏠 Главное меню"},
    {"command": "catalog", "description": "🛍️ Каталог товаров"},
    {"command": "cart", "description": "🛒 Корзина"},
    {"command": "support", "description": "📞 Поддержка"}
]
```

---

## 🌐 НАСТРОЙКА WEBAPP

### 1. Основные файлы
- **index.html** - структура интерфейса
- **app.js** - логика приложения
- **styles.css** - стили и темы

### 2. Настройка API
В файле `app.js` настройте базовый URL:
```javascript
getApiBase() {
    if (window.Telegram?.WebApp?.initDataUnsafe) {
        const currentUrl = window.location.origin;
        if (currentUrl.includes('repl.co')) {
            return currentUrl;
        }
    }
    return '';  // Для локальной разработки
}
```

### 3. Настройка уведомлений
```javascript
showNotification(message, type = 'info') {
    // type: 'success', 'error', 'warning', 'info'
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
}
```

---

## 🛍️ РАБОТА С ТОВАРАМИ

### 1. Структура товара в products.json
```json
{
    "id": 1,
    "title": "Nike Air Max",
    "description": "Кроссовки для бега",
    "price": 12000,
    "photo": "/webapp/uploads/sneakers.jpg",
    "photos": ["/webapp/uploads/sneakers1.jpg", "/webapp/uploads/sneakers2.jpg"],
    "sizes": ["40", "41", "42", "43", "44"],
    "is_active": true,
    "created_at": "2025-01-21T10:00:00Z"
}
```

### 2. Добавление товара через админ-панель
1. Откройте WebApp
2. Перейдите в раздел "Админ"
3. Нажмите "Добавить товар"
4. Заполните форму
5. Загрузите изображения
6. Сохраните

### 3. Программное добавление товара
```python
import json

# Загрузка товаров
with open('webapp/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Добавление нового товара
new_product = {
    "id": len(products) + 1,
    "title": "Новый товар",
    "description": "Описание товара",
    "price": 5000,
    "photo": "/webapp/uploads/new_product.jpg",
    "sizes": ["S", "M", "L"],
    "is_active": True
}

products.append(new_product)

# Сохранение
with open('webapp/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)
```

---

## 📦 СИСТЕМА ЗАКАЗОВ

### 1. Обработка заказов
Заказы обрабатываются в файле `simple_telegram_bot.py`:

```python
def do_POST(self):
    if self.path == '/api/orders':
        # Получение данных заказа
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # Обработка заказа
        self.process_order(data)
```

### 2. Уведомления администратору
При получении заказа администратор получает два сообщения:

**Сообщение 1 - Информация о заказе:**
```
🔔 НОВЫЙ ЗАКАЗ 5

💰 4 800 ₽
📅 21.10.2025 22:40

👤 КЛИЕНТ:
   Имя: Иван Петров
   Телефон: +7 (912) 345-67-89
   Адрес: г. Москва, ул. Ленина, д. 5

ТОВАРЫ:
1. Jordan 11 Retro (размер: 41) × 1

ЧТО ДЕЛАТЬ:
1️⃣ Нажать кнопку ниже
2️⃣ Уточнить детали доставки
3️⃣ Получить подтверждение оплаты

⏱ Обработать в течение 15 минут

[💬 Связаться с клиентом]
```

**Сообщение 2 - Шаблон для клиента:**
```
📋 ГОТОВЫЙ ТЕКСТ ДЛЯ КЛИЕНТА:

Здравствуйте! Ваш заказ №5 подтвержден.

ВАШИ ТОВАРЫ:
1. Jordan 11 Retro (размер: 41) — 4800 ₽ × 1 = 4800 ₽

ИТОГО: 4 800 ₽

ОПЛАТА СБП (без комиссии):
📱 +7 (999) 123-45-67
👤 Администратор магазина

Другие способы:
💳 Карта — по запросу
💵 Наличные при получении

После оплаты отправьте скриншот.
Доставка 1-3 дня.

Скопируйте текст выше и отправьте клиенту
```

### 3. База данных заказов
Заказы сохраняются в таблице `webapp_orders`:
```sql
CREATE TABLE webapp_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    user_name TEXT,
    user_phone TEXT,
    user_address TEXT,
    items TEXT,
    total REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ АДМИН-ПАНЕЛЬ

### 1. Доступ к админ-панели
Админ-панель доступна только пользователям, чьи ID указаны в `ADMIN_IDS`.

### 2. Функции админ-панели
- **Управление товарами**: добавление, редактирование, удаление
- **Статистика**: количество товаров и заказов
- **Просмотр заказов**: история всех заказов
- **Управление изображениями**: загрузка и удаление

### 3. Настройка прав доступа
В файле `webapp/admins.json`:
```json
{
    "admins": [
        {
            "id": 1593426947,
            "name": "Главный админ",
            "permissions": ["products", "orders", "users"]
        }
    ]
}
```

---

## 🎨 КАСТОМИЗАЦИЯ

### 1. Изменение темы
В файле `webapp/styles.css`:
```css
:root {
    --primary-color: #000000;      /* Основной цвет */
    --accent-color: #1a1a1a;       /* Акцентный цвет */
    --text-color: #ffffff;         /* Цвет текста */
    --success-color: #00ff00;       /* Цвет успеха */
    --border-radius: 8px;           /* Радиус скругления */
}
```

### 2. Изменение логотипа
Замените файл `webapp/uploads/logo.png` на ваш логотип.

### 3. Настройка уведомлений
В файле `app.js`:
```javascript
showNotification(message, type = 'info') {
    // Кастомизация уведомлений
    const colors = {
        success: '#00ff00',
        error: '#ff0000',
        warning: '#ffff00',
        info: '#0099ff'
    };
}
```

### 4. Добавление новых полей товара
В `products.json`:
```json
{
    "id": 1,
    "title": "Товар",
    "brand": "Nike",           // Новое поле
    "color": "Черный",         // Новое поле
    "material": "Кожа",       // Новое поле
    "warranty": "1 год"        // Новое поле
}
```

### 5. Настройка форм
В `index.html` добавьте новые поля:
```html
<div class="form-group">
    <label for="product-brand">Бренд</label>
    <input type="text" id="product-brand" name="brand">
</div>
```

---

## 🚀 РАЗВЕРТЫВАНИЕ

### 1. Локальная разработка
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск
python main.py
```

### 2. Развертывание на Replit
1. Создайте новый Repl
2. Импортируйте репозиторий
3. Установите переменные окружения в Secrets
4. Запустите команду:
```bash
./FIX_AND_RUN.sh
```

### 3. Развертывание на VPS
```bash
# Установка зависимостей
sudo apt update
sudo apt install python3 python3-pip nginx

# Клонирование проекта
git clone https://github.com/your-username/chatbotik.git
cd chatbotik

# Установка Python зависимостей
pip3 install -r requirements.txt

# Настройка systemd сервиса
sudo nano /etc/systemd/system/chatbotik.service
```

### 4. Настройка Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔧 РЕШЕНИЕ ПРОБЛЕМ

### 1. Бот не отвечает
**Проблема**: Бот не реагирует на команды
**Решение**:
- Проверьте правильность BOT_TOKEN
- Убедитесь, что бот запущен
- Проверьте логи: `tail -f logs/bot.log`

### 2. WebApp не загружается
**Проблема**: WebApp показывает ошибку
**Решение**:
- Проверьте URL в настройках бота
- Убедитесь, что веб-сервер запущен
- Проверьте CORS настройки

### 3. Заказы не приходят
**Проблема**: Администратор не получает уведомления
**Решение**:
- Проверьте ADMIN_IDS
- Убедитесь, что бот может писать администратору
- Проверьте настройки уведомлений

### 4. Ошибка "Address already in use"
**Проблема**: Порт 8000 занят
**Решение**:
```bash
# Остановка процессов
pkill -f python
lsof -ti:8000 | xargs kill -9

# Или используйте другой порт
export PORT=8001
```

### 5. Изображения не загружаются
**Проблема**: Товары без изображений
**Решение**:
- Проверьте права доступа к папке uploads
- Убедитесь, что файлы существуют
- Проверьте пути к изображениям

---

## 📞 ПОДДЕРЖКА

### Логи и отладка
```bash
# Просмотр логов бота
tail -f logs/bot.log

# Просмотр логов веб-сервера
tail -f logs/web.log

# Отладка в браузере
# Откройте Developer Tools (F12)
# Перейдите в Console
```

### Полезные команды
```bash
# Проверка статуса процессов
ps aux | grep python

# Очистка логов
> logs/bot.log

# Перезапуск приложения
./FIX_AND_RUN.sh
```

### Контакты
- GitHub Issues: [Создать issue](https://github.com/your-username/chatbotik/issues)
- Telegram: @your_username
- Email: your-email@example.com

---

## 🎯 ЗАКЛЮЧЕНИЕ

Этот гайд содержит всю необходимую информацию для настройки и работы с ботом. Если у вас возникли вопросы или проблемы, обратитесь к разделу "Решение проблем" или создайте issue в репозитории.

**Удачного использования! 🚀**

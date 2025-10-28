# 🤖 Гайд по основам AIOgram 3.x

Полный гайд для начинающих по всем основным аспектам работы с AIOgram 3.x, включая примеры кода для создания рабочего бота.

---

## 📋 Содержание

1. [Установка и настройка AIOgram](#1-установка-и-настройка-aiogram)
2. [Регистрация бота в Telegram](#2-регистрация-бота-в-telegram)
3. [Работа с Dispatcher и Router](#3-работа-с-dispatcher-и-router)
4. [Обработка сообщений и команд](#4-обработка-сообщений-и-команд)
5. [Машина состояний (FSM)](#5-машина-состояний-fsm)
6. [Работа с Inline-кнопками и клавиатурами](#6-работа-с-inline-кнопками-и-клавиатурами)
7. [Фильтры сообщений](#7-фильтры-сообщений)
8. [Middleware](#8-middleware)
9. [Подключение базы данных](#9-подключение-базы-данных)
10. [Логирование и обработка ошибок](#10-логирование-и-обработка-ошибок)
11. [Развёртывание бота](#11-развёртывание-бота)
12. [Примеры готовых ботов](#12-примеры-готовых-ботов)

---

## 1. Установка и настройка AIOgram

### Установка библиотеки через pip

AIOgram 3.x требует Python 3.8 или выше. Установите библиотеку с помощью pip:

```bash
pip install aiogram==3.3.0
```

Для работы с состояниями (FSM) также установите:

```bash
pip install aiofiles
```

### Начальная настройка проекта

Создайте структуру проекта:

```bash
my_bot/
├── bot.py           # Главный файл бота
├── config.py        # Конфигурация
├── handlers/        # Обработчики
│   ├── __init__.py
│   ├── commands.py
│   └── messages.py
├── keyboards/       # Клавиатуры
│   └── __init__.py
├── middlewares/     # Middleware
│   └── __init__.py
└── requirements.txt
```

Создайте файл `requirements.txt`:

```txt
aiogram==3.3.0
aiofiles==23.2.1
python-dotenv==1.0.0
```

---

## 2. Регистрация бота в Telegram

### Получение токена через BotFather

1. Откройте Telegram и найдите бота [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Введите имя бота (например, "My Awesome Bot")
4. Введите username бота (должен заканчиваться на `bot`, например, `my_awesome_bot`)
5. Скопируйте полученный токен (формат: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Настройка токена в коде

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

Создайте файл `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")
```

---

## 3. Работа с Dispatcher и Router

### Зачем нужен диспетчер

**Dispatcher** — это центральный компонент AIOgram, который:
- Управляет обработкой всех входящих обновлений
- Маршрутизирует сообщения к соответствующим обработчикам
- Управляет middleware и фильтрами

В AIOgram 3.x dispatcher работает совместно с **Router** для модульной организации кода.

### Как использовать Router для маршрутизации сообщений

**Router** позволяет организовать обработчики по модулям:

```python
# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

async def main():
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

Пример использования Router:

```python
# handlers/commands.py
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот на AIOgram 3.x")
```

Подключение роутера в главном файле:

```python
# bot.py
from handlers import commands

# Подключаем роутер
dp.include_router(commands.router)
```

---

## 4. Обработка сообщений и команд

### Создание хэндлеров для обработки сообщений

В AIOgram 3.x обработчики создаются с помощью декораторов:

```python
from aiogram import Router, F
from aiogram.types import Message

router = Router()

# Обработка текстовых сообщений
@router.message(F.text)
async def handle_text(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# Обработка фото
@router.message(F.photo)
async def handle_photo(message: Message):
    await message.answer("Спасибо за фото!")

# Обработка документов
@router.message(F.document)
async def handle_document(message: Message):
    await message.answer(f"Получен документ: {message.document.file_name}")
```

### Пример обработки команды `/start`

```python
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот на AIOgram 3.x. Вот мои команды:\n"
        "/help - Помощь\n"
        "/about - О боте"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 Справка по боту:\n\n"
        "Просто отправьте мне сообщение, и я отвечу!"
    )

@router.message(Command("about"))
async def cmd_about(message: Message):
    """Обработчик команды /about"""
    await message.answer(
        "ℹ️ О боте:\n\n"
        "Версия: 1.0\n"
        "Библиотека: AIOgram 3.x\n"
        "Разработчик: @username"
    )
```

---

## 5. Машина состояний (FSM)

### Пример пошагового взаимодействия с пользователем

FSM (Finite State Machine) позволяет создавать многошаговые диалоги с пользователем.

Создайте файл `states.py`:

```python
from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    """Состояния для формы регистрации"""
    name = State()
    age = State()
    city = State()
```

### Настройка состояний и переходов

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states import Form

router = Router()

@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext):
    """Начало регистрации"""
    await message.answer("Как вас зовут?")
    await state.set_state(Form.name)

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    await state.update_data(name=message.text)
    await message.answer("Сколько вам лет?")
    await state.set_state(Form.age)

@router.message(Form.age, F.text.isdigit())
async def process_age(message: Message, state: FSMContext):
    """Обработка возраста"""
    await state.update_data(age=int(message.text))
    await message.answer("В каком городе вы живёте?")
    await state.set_state(Form.city)

@router.message(Form.age)
async def process_age_invalid(message: Message):
    """Обработка неверного возраста"""
    await message.answer("Пожалуйста, введите число")

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    """Завершение регистрации"""
    await state.update_data(city=message.text)
    
    # Получаем все данные
    data = await state.get_data()
    
    await message.answer(
        f"Регистрация завершена!\n\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Город: {data['city']}"
    )
    
    # Очищаем состояние
    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять")
        return
    
    await state.clear()
    await message.answer("Действие отменено")
```

Подключение FSM в главном файле:

```python
from aiogram.fsm.storage.memory import MemoryStorage

# Создаём хранилище для состояний
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
```

---

## 6. Работа с Inline-кнопками и клавиатурами

### Создание инлайн-кнопок

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Меню с инлайн-кнопками"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton(text="🌐 Сайт", url="https://example.com")
            ]
        ]
    )
    
    await message.answer("Выберите пункт меню:", reply_markup=keyboard)
```

### Использование CallbackData для обработки нажатий

Создайте файл `keyboards/callbacks.py`:

```python
from aiogram.filters.callback_data import CallbackData

class MenuCallback(CallbackData, prefix="menu"):
    """Callback для меню"""
    action: str
    page: int = 1

class ProductCallback(CallbackData, prefix="product"):
    """Callback для товаров"""
    action: str
    product_id: int
```

Использование CallbackData:

```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.callbacks import MenuCallback, ProductCallback

router = Router()

@router.message(Command("catalog"))
async def cmd_catalog(message: Message):
    """Каталог товаров"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Товар 1",
                    callback_data=ProductCallback(action="view", product_id=1).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="Товар 2",
                    callback_data=ProductCallback(action="view", product_id=2).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=MenuCallback(action="back").pack()
                )
            ]
        ]
    )
    
    await message.answer("Каталог товаров:", reply_markup=keyboard)

@router.callback_query(ProductCallback.filter(F.action == "view"))
async def process_product_view(callback: CallbackQuery, callback_data: ProductCallback):
    """Просмотр товара"""
    product_id = callback_data.product_id
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data=ProductCallback(action="add_to_cart", product_id=product_id).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ К каталогу",
                    callback_data=MenuCallback(action="catalog").pack()
                )
            ]
        ]
    )
    
    await callback.message.edit_text(
        f"Товар #{product_id}\n\n"
        f"Описание товара...",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(ProductCallback.filter(F.action == "add_to_cart"))
async def process_add_to_cart(callback: CallbackQuery, callback_data: ProductCallback):
    """Добавление в корзину"""
    product_id = callback_data.product_id
    await callback.answer(f"Товар #{product_id} добавлен в корзину!", show_alert=True)
```

Обычные клавиатуры (Reply Keyboard):

```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

@router.message(Command("keyboard"))
async def cmd_keyboard(message: Message):
    """Обычная клавиатура"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📱 Поделиться контактом", request_contact=True)
            ],
            [
                KeyboardButton(text="📍 Отправить локацию", request_location=True)
            ],
            [
                KeyboardButton(text="❌ Убрать клавиатуру")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Выберите действие:", reply_markup=keyboard)
```

---

## 7. Фильтры сообщений

### Использование встроенных фильтров

AIOgram 3.x предоставляет множество встроенных фильтров:

```python
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message

router = Router()

# Фильтр по команде
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Команда /start")

# Фильтр по тексту
@router.message(F.text == "Привет")
async def hello(message: Message):
    await message.answer("Привет!")

# Фильтр по содержанию текста
@router.message(F.text.contains("бот"))
async def contains_bot(message: Message):
    await message.answer("Вы упомянули бота!")

# Фильтр по регулярному выражению
@router.message(F.text.regexp(r"\d{10}"))
async def phone_number(message: Message):
    await message.answer("Это похоже на номер телефона!")

# Фильтр по типу контента
@router.message(F.photo)
async def handle_photo(message: Message):
    await message.answer("Получено фото")

@router.message(F.document)
async def handle_document(message: Message):
    await message.answer("Получен документ")

# Фильтр по нескольким условиям (AND)
@router.message(F.text, F.text.len() > 10)
async def long_text(message: Message):
    await message.answer("Длинное сообщение!")

# Фильтр по нескольким условиям (OR)
@router.message((F.photo) | (F.video))
async def media(message: Message):
    await message.answer("Получено медиа")
```

### Пример создания кастомного фильтра

Создайте файл `filters/custom.py`:

```python
from aiogram.filters import BaseFilter
from aiogram.types import Message

class IsAdmin(BaseFilter):
    """Фильтр для проверки прав администратора"""
    
    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids

class HasLinks(BaseFilter):
    """Фильтр для проверки наличия ссылок"""
    
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        
        return any(entity.type == "url" for entity in (message.entities or []))

class TextLength(BaseFilter):
    """Фильтр по длине текста"""
    
    def __init__(self, min_length: int = 0, max_length: int = None):
        self.min_length = min_length
        self.max_length = max_length
    
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        
        text_len = len(message.text)
        
        if text_len < self.min_length:
            return False
        
        if self.max_length and text_len > self.max_length:
            return False
        
        return True
```

Использование кастомных фильтров:

```python
from aiogram import Router
from aiogram.types import Message
from filters.custom import IsAdmin, HasLinks, TextLength

router = Router()

ADMIN_IDS = [123456789, 987654321]

@router.message(IsAdmin(ADMIN_IDS))
async def admin_only(message: Message):
    """Только для администраторов"""
    await message.answer("Привет, админ!")

@router.message(HasLinks())
async def has_links(message: Message):
    """Сообщения со ссылками"""
    await message.answer("Обнаружена ссылка в сообщении")

@router.message(TextLength(min_length=10, max_length=100))
async def medium_text(message: Message):
    """Сообщения средней длины"""
    await message.answer("Сообщение средней длины принято")
```

---

## 8. Middleware

### Что такое middleware и зачем оно нужно

**Middleware** — это промежуточный слой обработки, который выполняется до или после обработчика. Используется для:
- Логирования
- Проверки прав доступа
- Обработки ошибок
- Сбора статистики
- Модификации данных

### Пример создания и использования middleware

Создайте файл `middlewares/logging.py`:

```python
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования сообщений"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Код до обработчика
        logger.info(
            f"User {event.from_user.id} (@{event.from_user.username}): {event.text}"
        )
        
        # Вызов обработчика
        result = await handler(event, data)
        
        # Код после обработчика
        logger.info(f"Handler executed successfully")
        
        return result
```

Middleware для проверки подписки:

```python
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

class SubscriptionMiddleware(BaseMiddleware):
    """Middleware для проверки подписки на канал"""
    
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем подписку
        try:
            member = await event.bot.get_chat_member(
                chat_id=self.channel_id,
                user_id=event.from_user.id
            )
            
            if member.status in ["left", "kicked"]:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Подписаться на канал",
                                url=f"https://t.me/your_channel"
                            )
                        ]
                    ]
                )
                
                await event.answer(
                    "Для использования бота необходимо подписаться на канал!",
                    reply_markup=keyboard
                )
                return
        except Exception as e:
            # Если не удалось проверить подписку, пропускаем
            pass
        
        return await handler(event, data)
```

Middleware для работы с базой данных:

```python
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import sqlite3

class DatabaseMiddleware(BaseMiddleware):
    """Middleware для подключения к базе данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Создаём подключение к БД
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Добавляем подключение в data
        data['db'] = conn
        
        try:
            # Вызываем обработчик
            result = await handler(event, data)
            conn.commit()
            return result
        finally:
            # Закрываем подключение
            conn.close()
```

Подключение middleware:

```python
# bot.py
from aiogram import Bot, Dispatcher
from middlewares.logging import LoggingMiddleware
from middlewares.subscription import SubscriptionMiddleware
from middlewares.database import DatabaseMiddleware

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем middleware
dp.message.middleware(LoggingMiddleware())
dp.message.middleware(SubscriptionMiddleware(channel_id=-1001234567890))
dp.message.middleware(DatabaseMiddleware(db_path="bot.db"))
```

---

## 9. Подключение базы данных

### Пример интеграции SQLite для хранения данных бота

Создайте файл `database.py`:

```python
import sqlite3
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Получение подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_premium INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица элементов заказа
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    # Методы для работы с пользователями
    
    def add_user(self, user_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None):
        """Добавление нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            logger.info(f"User {user_id} added to database")
        except sqlite3.IntegrityError:
            # Пользователь уже существует, обновляем информацию
            cursor.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, last_activity = ?
                WHERE user_id = ?
            ''', (username, first_name, last_name, datetime.now(), user_id))
            conn.commit()
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_user_balance(self, user_id: int, amount: int):
        """Обновление баланса пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET balance = balance + ? WHERE user_id = ?
        ''', (amount, user_id))
        conn.commit()
        conn.close()
    
    # Методы для работы с товарами
    
    def add_product(self, name: str, description: str, price: float, stock: int = 0):
        """Добавление товара"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (name, description, price, stock)
            VALUES (?, ?, ?, ?)
        ''', (name, description, price, stock))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        
        return product_id
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Получение товара по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_products(self) -> List[Dict]:
        """Получение всех активных товаров"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE is_active = 1')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # Методы для работы с заказами
    
    def create_order(self, user_id: int, items: List[Dict]) -> int:
        """Создание нового заказа"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Вычисляем общую сумму
        total_amount = sum(item['price'] * item['quantity'] for item in items)
        
        # Создаём заказ
        cursor.execute('''
            INSERT INTO orders (user_id, total_amount)
            VALUES (?, ?)
        ''', (user_id, total_amount))
        order_id = cursor.lastrowid
        
        # Добавляем элементы заказа
        for item in items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['quantity'], item['price']))
        
        conn.commit()
        conn.close()
        
        return order_id
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Получение заказов пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
```

Использование базы данных в обработчиках:

```python
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import Database

router = Router()
db = Database()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Добавляем пользователя в базу
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Получаем информацию о пользователе
    user = db.get_user(message.from_user.id)
    
    await message.answer(
        f"Привет, {user['first_name']}!\n"
        f"Ваш баланс: {user['balance']} руб."
    )

@router.message(Command("products"))
async def cmd_products(message: Message):
    """Список товаров"""
    products = db.get_all_products()
    
    if not products:
        await message.answer("Товары пока не добавлены")
        return
    
    text = "📦 Список товаров:\n\n"
    for product in products:
        text += (
            f"#{product['id']} {product['name']}\n"
            f"💰 {product['price']} руб.\n"
            f"📦 В наличии: {product['stock']} шт.\n\n"
        )
    
    await message.answer(text)
```

---

## 10. Логирование и обработка ошибок

### Как настроить логирование

Создайте файл `logger.py`:

```python
import logging
import sys
from datetime import datetime

def setup_logger(name: str = "bot", level: int = logging.INFO):
    """Настройка логирования"""
    
    # Создаём логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик
    file_handler = logging.FileHandler(
        f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
```

### Пример обработки ошибок

```python
from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.error()
async def error_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок"""
    
    logger.error(f"Update: {event.update}")
    logger.error(f"Exception: {event.exception}")
    
    # Обработка конкретных типов ошибок
    if isinstance(event.exception, TelegramBadRequest):
        logger.error(f"Bad request: {event.exception}")
        # Например, попытка отредактировать старое сообщение
        
    elif isinstance(event.exception, TelegramForbiddenError):
        logger.error(f"Forbidden: {event.exception}")
        # Пользователь заблокировал бота
        
    else:
        logger.exception(f"Unhandled exception: {event.exception}")
    
    return True  # Возвращаем True, чтобы остановить распространение ошибки
```

Обработка ошибок в конкретных обработчиках:

```python
from aiogram import Router
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("test"))
async def cmd_test(message: Message):
    """Тестовая команда с обработкой ошибок"""
    try:
        # Ваш код
        result = await some_dangerous_operation()
        await message.answer(f"Результат: {result}")
        
    except TelegramAPIError as e:
        logger.error(f"Telegram API error: {e}")
        await message.answer("Произошла ошибка при работе с Telegram API")
        
    except ValueError as e:
        logger.error(f"Value error: {e}")
        await message.answer("Неверные данные")
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        await message.answer("Произошла непредвиденная ошибка")
```

Использование в главном файле:

```python
# bot.py
import logging
from logger import setup_logger

# Настраиваем логирование
logger = setup_logger("bot", level=logging.INFO)

# В функции main
async def main():
    logger.info("Starting bot...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped")
```

---

## 11. Развёртывание бота

### Запуск на локальном сервере

Создайте файл `.env`:

```env
BOT_TOKEN=your_bot_token_here
```

Запустите бота:

```bash
python bot.py
```

### Развёртывание с использованием Docker

Создайте `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаём директорию для логов
RUN mkdir -p logs

# Запускаем бота
CMD ["python", "bot.py"]
```

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram_bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./bot.db:/app/bot.db
    environment:
      - PYTHONUNBUFFERED=1
```

Команды для развёртывания:

```bash
# Сборка образа
docker-compose build

# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Развёртывание на VPS

```bash
# Подключение к серверу
ssh user@your-server-ip

# Установка зависимостей
sudo apt update
sudo apt install python3 python3-pip git

# Клонирование проекта
git clone https://github.com/yourusername/your-bot.git
cd your-bot

# Установка Python зависимостей
pip3 install -r requirements.txt

# Создание .env файла
nano .env
# Добавьте BOT_TOKEN=your_token

# Создание systemd сервиса
sudo nano /etc/systemd/system/telegram-bot.service
```

Содержимое `telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/your-bot
ExecStart=/usr/bin/python3 /home/your-user/your-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-bot

# Запуск бота
sudo systemctl start telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -f
```

---

## 12. Примеры готовых ботов

### Эхо-бот

Простой бот, который повторяет все полученные сообщения:

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start"""
    await message.answer(
        "👋 Привет! Я эхо-бот.\n"
        "Отправь мне любое сообщение, и я повторю его!"
    )

@router.message(F.text)
async def echo_text(message: Message):
    """Повтор текстовых сообщений"""
    await message.answer(message.text)

@router.message(F.photo)
async def echo_photo(message: Message):
    """Повтор фото"""
    await message.answer_photo(
        photo=message.photo[-1].file_id,
        caption=message.caption or "Получено фото"
    )

@router.message()
async def echo_other(message: Message):
    """Обработка других типов сообщений"""
    await message.answer("Не могу повторить этот тип сообщения")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### Бот с меню и кнопками

Полнофункциональный бот с меню, кнопками и различными функциями:

```python
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Функции для создания клавиатур

def get_main_menu():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
                InlineKeyboardButton(text="🎮 Игры", callback_data="games")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
            ],
            [
                InlineKeyboardButton(text="📞 Поддержка", callback_data="support")
            ]
        ]
    )
    return keyboard

def get_games_menu():
    """Меню игр"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Кости", callback_data="game_dice"),
                InlineKeyboardButton(text="🎯 Дартс", callback_data="game_darts")
            ],
            [
                InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basketball"),
                InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
            ]
        ]
    )
    return keyboard

# Обработчики команд

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start"""
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я многофункциональный бот с меню и кнопками.\n"
        "Выбери пункт меню:",
        reply_markup=get_main_menu()
    )

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu"""
    await message.answer(
        "📋 Главное меню:",
        reply_markup=get_main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = """
📖 Доступные команды:

/start - Начать работу с ботом
/menu - Открыть главное меню
/help - Показать эту справку
/about - Информация о боте

Используй кнопки для навигации по боту!
    """
    await message.answer(help_text)

# Обработчики callback

@router.callback_query(F.data == "about")
async def callback_about(callback: CallbackQuery):
    """О боте"""
    about_text = """
ℹ️ О боте:

Версия: 1.0
Библиотека: AIOgram 3.x
Язык: Python 3.11+

Возможности:
• Интерактивное меню
• Встроенные игры
• Статистика использования
• Настройки пользователя
    """
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
        ]
    )
    
    await callback.message.edit_text(about_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "games")
async def callback_games(callback: CallbackQuery):
    """Меню игр"""
    await callback.message.edit_text(
        "🎮 Выбери игру:",
        reply_markup=get_games_menu()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("game_"))
async def callback_game(callback: CallbackQuery):
    """Запуск игры"""
    game = callback.data.split("_")[1]
    
    game_emoji = {
        "dice": "🎲",
        "darts": "🎯",
        "basketball": "��",
        "football": "⚽"
    }
    
    emoji = game_emoji.get(game, "🎮")
    
    # Отправляем игровой элемент
    if game == "dice":
        result = await callback.message.answer_dice(emoji)
    elif game == "darts":
        result = await callback.message.answer_dice(emoji)
    elif game == "basketball":
        result = await callback.message.answer_dice(emoji)
    elif game == "football":
        result = await callback.message.answer_dice(emoji)
    
    await callback.answer(f"Игра {emoji} запущена!")

@router.callback_query(F.data == "stats")
async def callback_stats(callback: CallbackQuery):
    """Статистика"""
    stats_text = f"""
📊 Ваша статистика:

👤 ID: {callback.from_user.id}
📝 Username: @{callback.from_user.username or 'не указан'}
�� Дата регистрации: {datetime.now().strftime('%d.%m.%Y')}
💬 Сообщений отправлено: 42
🎮 Игр сыграно: 15
    """
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
        ]
    )
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "settings")
async def callback_settings(callback: CallbackQuery):
    """Настройки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔔 Уведомления", callback_data="notif"),
                InlineKeyboardButton(text="🌐 Язык", callback_data="lang")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
            ]
        ]
    )
    
    await callback.message.edit_text(
        "⚙️ Настройки:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def callback_support(callback: CallbackQuery):
    """Поддержка"""
    support_text = """
📞 Поддержка:

Если у вас возникли вопросы или проблемы:

📧 Email: support@example.com
💬 Telegram: @support
🌐 Сайт: https://example.com

Мы ответим в течение 24 часов!
    """
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
        ]
    )
    
    await callback.message.edit_text(support_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def callback_back(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "📋 Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# Обработчик текстовых сообщений

@router.message(F.text)
async def handle_text(message: Message):
    """Обработка текста"""
    text = message.text.lower()
    
    if "привет" in text:
        await message.answer("👋 Привет! Используй /menu для открытия меню")
    elif "как дела" in text:
        await message.answer("Отлично! А у тебя? 😊")
    else:
        await message.answer(
            "Я тебя не понимаю 😔\nИспользуй /help для справки"
        )

async def main():
    """Главная функция"""
    dp.include_router(router)
    logger.info("Bot started")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 Дополнительные ресурсы

### Официальная документация
- [AIOgram 3.x Documentation](https://docs.aiogram.dev/en/latest/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Примеры и туториалы
- [AIOgram Examples](https://github.com/aiogram/aiogram/tree/dev-3.x/examples)
- [Telegram Bot API Updates](https://core.telegram.org/bots/api#recent-changes)

### Сообщество
- [AIOgram Community](https://t.me/aiogram)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/aiogram)

---

## 🎯 Заключение

Этот гайд охватывает все основные аспекты работы с AIOgram 3.x. Теперь вы знаете:

✅ Как установить и настроить AIOgram  
✅ Как создать и зарегистрировать бота  
✅ Как работать с диспетчером и роутерами  
✅ Как обрабатывать сообщения и команды  
✅ Как использовать FSM для многошаговых диалогов  
✅ Как создавать кнопки и клавиатуры  
✅ Как фильтровать сообщения  
✅ Как использовать middleware  
✅ Как работать с базами данных  
✅ Как настроить логирование и обработку ошибок  
✅ Как развернуть бота на разных платформах  

Используйте примеры из этого гайда как основу для создания своих ботов. Удачи в разработке! 🚀

**Версия гайда:** 1.0  
**Дата обновления:** 2025-01-21  
**AIOgram версия:** 3.3.0

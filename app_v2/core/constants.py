"""
Application Constants
====================

Централизованное хранение констант приложения.
"""

from enum import Enum


class OrderStatus(str, Enum):
    """Статусы заказа."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Статусы оплаты."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Методы оплаты."""
    CARD = "card"
    SBP = "sbp"
    CASH = "cash"
    CRYPTO = "crypto"


class UserRole(str, Enum):
    """Роли пользователей."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPERADMIN = "superadmin"


# Emoji константы
class Emoji:
    """Эмодзи для красивых сообщений."""
    
    # Навигация
    HOME = "🏠"
    BACK = "◀️"
    FORWARD = "▶️"
    UP = "⬆️"
    DOWN = "⬇️"
    
    # Действия
    ADD = "➕"
    REMOVE = "➖"
    EDIT = "✏️"
    DELETE = "🗑️"
    SAVE = "💾"
    CANCEL = "❌"
    CONFIRM = "✅"
    
    # Магазин
    CART = "🛒"
    PRODUCT = "📦"
    CATEGORY = "📂"
    PRICE = "💰"
    DISCOUNT = "🏷️"
    SALE = "🔥"
    
    # Заказы
    ORDER = "📋"
    SHIPPING = "🚚"
    DELIVERED = "✅"
    CANCELLED = "❌"
    
    # Оплата
    PAYMENT = "💳"
    CARD = "💳"
    CASH = "💵"
    CRYPTO = "₿"
    
    # Пользователь
    USER = "👤"
    ADMIN = "👑"
    PROFILE = "📱"
    SETTINGS = "⚙️"
    
    # Статусы
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    
    # Поиск и фильтры
    SEARCH = "🔍"
    FILTER = "🔽"
    SORT = "🔃"
    
    # Уведомления
    BELL = "🔔"
    MESSAGE = "💬"
    EMAIL = "📧"
    
    # Разное
    STAR = "⭐"
    HEART = "❤️"
    FIRE = "🔥"
    ROCKET = "🚀"
    GIFT = "🎁"
    CLOCK = "🕐"
    CALENDAR = "📅"


# Лимиты
class Limits:
    """Лимиты приложения."""
    
    # Товары
    MAX_PRODUCT_TITLE_LENGTH = 100
    MAX_PRODUCT_DESCRIPTION_LENGTH = 1000
    MAX_PRODUCT_PRICE = 1_000_000
    MIN_PRODUCT_PRICE = 1
    
    # Заказы
    MAX_CART_ITEMS = 50
    MAX_ORDER_ITEMS = 100
    
    # Файлы
    MAX_IMAGE_SIZE_MB = 10
    MAX_IMAGE_WIDTH = 2048
    MAX_IMAGE_HEIGHT = 2048
    
    # Пользователи
    MAX_USERNAME_LENGTH = 50
    MAX_ADDRESS_LENGTH = 500
    MAX_PHONE_LENGTH = 20
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 30
    MAX_REQUESTS_PER_HOUR = 500


# Сообщения
class Messages:
    """Текстовые сообщения."""
    
    # Приветствия
    WELCOME = f"{Emoji.ROCKET} Добро пожаловать в магазин!"
    WELCOME_BACK = f"{Emoji.HOME} С возвращением!"
    
    # Успех
    SUCCESS_ADD_TO_CART = f"{Emoji.SUCCESS} Товар добавлен в корзину"
    SUCCESS_ORDER_CREATED = f"{Emoji.SUCCESS} Заказ успешно оформлен"
    SUCCESS_PRODUCT_CREATED = f"{Emoji.SUCCESS} Товар создан"
    SUCCESS_PRODUCT_UPDATED = f"{Emoji.SUCCESS} Товар обновлен"
    SUCCESS_PRODUCT_DELETED = f"{Emoji.SUCCESS} Товар удален"
    
    # Ошибки
    ERROR_NOT_FOUND = f"{Emoji.ERROR} Не найдено"
    ERROR_PRODUCT_NOT_FOUND = f"{Emoji.ERROR} Товар не найден"
    ERROR_CART_EMPTY = f"{Emoji.WARNING} Корзина пуста"
    ERROR_INSUFFICIENT_STOCK = f"{Emoji.WARNING} Недостаточно товара на складе"
    ERROR_INVALID_INPUT = f"{Emoji.ERROR} Некорректные данные"
    ERROR_PERMISSION_DENIED = f"{Emoji.ERROR} Недостаточно прав"
    
    # Вопросы
    CONFIRM_DELETE = f"{Emoji.WARNING} Вы уверены что хотите удалить?"
    CONFIRM_CANCEL_ORDER = f"{Emoji.WARNING} Отменить заказ?"
    CONFIRM_CLEAR_CART = f"{Emoji.WARNING} Очистить корзину?"
    
    # Информация
    INFO_LOADING = f"{Emoji.LOADING} Загрузка..."
    INFO_PROCESSING = f"{Emoji.LOADING} Обработка..."
    INFO_EMPTY_CATALOG = f"{Emoji.INFO} Каталог пуст"
    INFO_NO_ORDERS = f"{Emoji.INFO} У вас пока нет заказов"


# URL паттерны
class URLPatterns:
    """URL паттерны для API."""
    
    # Health
    HEALTH = "/health"
    READY = "/ready"
    
    # Auth
    AUTH_LOGIN = "/auth/login"
    AUTH_LOGOUT = "/auth/logout"
    AUTH_REFRESH = "/auth/refresh"
    
    # Products
    PRODUCTS = "/products"
    PRODUCT_DETAIL = "/products/{product_id}"
    PRODUCT_CATEGORIES = "/products/categories"
    
    # Orders
    ORDERS = "/orders"
    ORDER_DETAIL = "/orders/{order_id}"
    ORDER_CANCEL = "/orders/{order_id}/cancel"
    
    # Cart
    CART = "/cart"
    CART_ADD = "/cart/add"
    CART_REMOVE = "/cart/remove"
    CART_CLEAR = "/cart/clear"
    
    # Users
    USERS = "/users"
    USER_DETAIL = "/users/{user_id}"
    USER_PROFILE = "/users/me"
    
    # Admin
    ADMIN_STATS = "/admin/stats"
    ADMIN_USERS = "/admin/users"
    ADMIN_PRODUCTS = "/admin/products"
    ADMIN_ORDERS = "/admin/orders"
    
    # Webhook
    WEBHOOK = "/webhook"


# Регулярные выражения
class RegexPatterns:
    """Регулярные выражения для валидации."""
    
    PHONE = r"^\+?[1-9]\d{1,14}$"
    EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    USERNAME = r"^[a-zA-Z0-9_]{3,50}$"
    SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


# Форматы даты/времени
class DateTimeFormats:
    """Форматы даты и времени."""
    
    DATE = "%d.%m.%Y"
    TIME = "%H:%M"
    DATETIME = "%d.%m.%Y %H:%M"
    DATETIME_FULL = "%d.%m.%Y %H:%M:%S"
    ISO = "%Y-%m-%dT%H:%M:%S"


# Database
class DatabaseConstants:
    """Константы базы данных."""
    
    # Индексы
    INDEX_USER_TELEGRAM_ID = "idx_user_telegram_id"
    INDEX_PRODUCT_SLUG = "idx_product_slug"
    INDEX_ORDER_USER_ID = "idx_order_user_id"
    INDEX_ORDER_STATUS = "idx_order_status"
    INDEX_ORDER_CREATED_AT = "idx_order_created_at"
    
    # Таблицы
    TABLE_USERS = "users"
    TABLE_PRODUCTS = "products"
    TABLE_CATEGORIES = "categories"
    TABLE_ORDERS = "orders"
    TABLE_ORDER_ITEMS = "order_items"
    TABLE_CART_ITEMS = "cart_items"


# Cache keys
class CacheKeys:
    """Ключи для кэша."""
    
    PRODUCT = "product:{product_id}"
    PRODUCTS_LIST = "products:list:{page}:{per_page}"
    PRODUCT_BY_SLUG = "product:slug:{slug}"
    USER = "user:{user_id}"
    USER_BY_TELEGRAM_ID = "user:telegram:{telegram_id}"
    CART = "cart:{user_id}"
    CATEGORIES = "categories"


# Валюты
class Currency:
    """Валюты."""
    
    RUB = "₽"
    USD = "$"
    EUR = "€"
    
    DEFAULT = RUB


# Языки
class Language:
    """Поддерживаемые языки."""
    
    RU = "ru"
    EN = "en"
    
    DEFAULT = RU

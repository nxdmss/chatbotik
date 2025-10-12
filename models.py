"""
Модели данных с валидацией для Telegram бота магазина
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, field_validator, Field
from datetime import datetime
import re


class Product(BaseModel):
    """Модель товара"""
    id: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., gt=0, description="Цена в копейках")
    currency: str = Field(default="RUB", max_length=3)
    photo: str = Field(default="", max_length=500)
    sizes: List[int] = Field(default_factory=list, min_items=1)
    deleted: bool = Field(default=False)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Название товара не может быть пустым')
        # Удаляем потенциально опасные символы
        cleaned = re.sub(r'[<>"\']', '', v.strip())
        if len(cleaned) < 2:
            raise ValueError('Название товара слишком короткое')
        return cleaned
    
    @field_validator('sizes')
    @classmethod
    def validate_sizes(cls, v):
        if not v:
            raise ValueError('Должен быть указан хотя бы один размер')
        for size in v:
            if not isinstance(size, int) or size < 20 or size > 60:
                raise ValueError('Размер должен быть числом от 20 до 60')
        return sorted(list(set(v)))  # Убираем дубликаты и сортируем
    
    @field_validator('photo')
    @classmethod
    def validate_photo(cls, v):
        if not v:
            return v
        # Проверяем, что это валидный URL или путь
        if not (v.startswith('http') or v.startswith('/') or v.startswith('data:')):
            raise ValueError('Некорректный формат URL фото')
        return v


class CartItem(BaseModel):
    """Модель позиции в корзине"""
    product_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    price: int = Field(..., gt=0)
    qty: int = Field(..., gt=0, le=99)
    size: int = Field(..., ge=20, le=60)
    
    @field_validator('qty')
    @classmethod
    def validate_qty(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше 0')
        if v > 99:
            raise ValueError('Максимальное количество: 99')
        return v


class OrderCreate(BaseModel):
    """Модель создания заказа"""
    text: str = Field(..., min_length=3, max_length=1000)
    items: List[CartItem] = Field(..., min_items=1)
    total: int = Field(..., gt=0)
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Описание заказа не может быть пустым')
        # Очищаем от потенциально опасных символов
        cleaned = re.sub(r'[<>"\']', '', v.strip())
        if len(cleaned) < 3:
            raise ValueError('Описание заказа слишком короткое')
        return cleaned
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError('Заказ должен содержать хотя бы один товар')
        # Проверяем уникальность комбинации product_id + size
        seen = set()
        for item in v:
            key = (item.product_id, item.size)
            if key in seen:
                raise ValueError('Дублирующиеся позиции в заказе')
            seen.add(key)
        return v


class Order(BaseModel):
    """Модель заказа"""
    order_id: int = Field(..., gt=0)
    text: str = Field(..., min_length=1)
    status: str = Field(default="new")
    items: List[CartItem] = Field(default_factory=list)
    total: int = Field(..., gt=0)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    from_webapp: bool = Field(default=False)
    paid_at: Optional[str] = Field(default=None)
    invoice_payload: Optional[str] = Field(default=None)
    admin_notes: List[Dict[str, Any]] = Field(default_factory=list)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed_statuses = {'new', 'work', 'done', 'paid', 'cancelled'}
        if v not in allowed_statuses:
            raise ValueError(f'Недопустимый статус: {v}')
        return v


class AdminNote(BaseModel):
    """Модель заметки администратора"""
    admin_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1, max_length=1000)
    time: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Текст заметки не может быть пустым')
        return v.strip()


class DialogMessage(BaseModel):
    """Модель сообщения в диалоге"""
    from_user: str = Field(..., pattern=r'^(user|admin)$')
    text: str = Field(..., min_length=1, max_length=2000)
    photo_id: Optional[str] = Field(default=None)
    file_id: Optional[str] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Текст сообщения не может быть пустым')
        # Очищаем от потенциально опасных символов
        cleaned = re.sub(r'[<>"\']', '', v.strip())
        return cleaned


class UserProfile(BaseModel):
    """Модель профиля пользователя"""
    user_id: str = Field(..., min_length=1)
    username: Optional[str] = Field(default=None, max_length=100)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    is_admin: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebAppData(BaseModel):
    """Модель данных из WebApp"""
    action: str = Field(..., pattern=r'^(checkout|add_product)$')
    items: Optional[List[CartItem]] = Field(default=None)
    total: Optional[int] = Field(default=None, gt=0)
    product: Optional[Product] = Field(default=None)
    
    @field_validator('items')
    @classmethod
    def validate_items_for_checkout(cls, v, values):
        if values.get('action') == 'checkout' and not v:
            raise ValueError('Для действия checkout необходимо указать товары')
        return v
    
    @field_validator('product')
    @classmethod
    def validate_product_for_add(cls, v, values):
        if values.get('action') == 'add_product' and not v:
            raise ValueError('Для действия add_product необходимо указать товар')
        return v


class PaymentData(BaseModel):
    """Модель данных платежа"""
    order_id: int = Field(..., gt=0)
    amount: int = Field(..., gt=0)
    currency: str = Field(default="RUB", max_length=3)
    description: str = Field(..., min_length=1, max_length=200)
    invoice_payload: str = Field(..., min_length=1)
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Описание платежа не может быть пустым')
        return v.strip()


class AdminAction(BaseModel):
    """Модель действия администратора"""
    admin_id: str = Field(..., min_length=1)
    action: str = Field(..., pattern=r'^(add_product|delete_product|restore_product|change_status|add_note)$')
    target_id: str = Field(..., min_length=1)
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        allowed_actions = {
            'add_product', 'delete_product', 'restore_product', 
            'change_status', 'add_note'
        }
        if v not in allowed_actions:
            raise ValueError(f'Недопустимое действие: {v}')
        return v


class Review(BaseModel):
    """Модель отзыва"""
    id: Optional[int] = None
    user_id: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=10, max_length=1000)
    rating: int = Field(..., ge=1, le=5)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_approved: bool = Field(default=False)
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Текст отзыва не может быть пустым')
        # Очищаем от потенциально опасных символов
        cleaned = re.sub(r'[<>"\']', '', v.strip())
        if len(cleaned) < 10:
            raise ValueError('Отзыв слишком короткий (минимум 10 символов)')
        if len(cleaned) > 1000:
            raise ValueError('Отзыв слишком длинный (максимум 1000 символов)')
        return cleaned
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Имя пользователя не может быть пустым')
        cleaned = re.sub(r'[<>"\']', '', v.strip())
        if len(cleaned) < 1:
            raise ValueError('Имя пользователя слишком короткое')
        return cleaned

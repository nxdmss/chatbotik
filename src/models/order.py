"""
Модель заказа
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class OrderItem(BaseModel):
    """Элемент заказа"""
    product_id: int
    title: str
    price: float
    quantity: int = Field(..., gt=0)
    size: Optional[str] = None
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше 0')
        return v
    
    @property
    def total_price(self) -> float:
        return self.price * self.quantity


class OrderCreate(BaseModel):
    """Модель для создания заказа"""
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_phone: str = Field(..., min_length=5, max_length=50)
    customer_address: Optional[str] = Field(None, max_length=500)
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    items: List[OrderItem] = Field(..., min_items=1)
    
    @validator('customer_name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Имя не может быть пустым')
        return v.strip()
    
    @validator('customer_phone')
    def phone_must_be_valid(cls, v):
        # Базовая валидация телефона
        digits = ''.join(c for c in v if c.isdigit())
        if len(digits) < 5:
            raise ValueError('Некорректный номер телефона')
        return v.strip()


class Order(BaseModel):
    """Полная модель заказа"""
    id: int
    order_number: int
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    status: str = 'new'
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @property
    def formatted_total(self) -> str:
        return f"{self.total_amount:,.0f} ₽"

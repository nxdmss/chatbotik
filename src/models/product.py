"""
Модель товара
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class ProductBase(BaseModel):
    """Базовая модель товара"""
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., gt=0, le=1_000_000)
    category: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    weight: Optional[str] = Field(None, max_length=50)
    dimensions: Optional[str] = Field(None, max_length=100)
    sizes: Optional[List[str]] = Field(default_factory=list)
    in_stock: bool = True
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Цена должна быть больше 0')
        return round(v, 2)
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Название не может быть пустым')
        return v.strip()
    
    @validator('sizes', pre=True)
    def parse_sizes(cls, v):
        if isinstance(v, str):
            # Парсим строку с размерами через запятую
            return [s.strip() for s in v.split(',') if s.strip()]
        return v or []


class ProductCreate(ProductBase):
    """Модель для создания товара"""
    pass


class ProductUpdate(BaseModel):
    """Модель для обновления товара"""
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, gt=0, le=1_000_000)
    category: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    material: Optional[str] = Field(None, max_length=100)
    weight: Optional[str] = Field(None, max_length=50)
    dimensions: Optional[str] = Field(None, max_length=100)
    sizes: Optional[List[str]] = None
    in_stock: Optional[bool] = None


class Product(ProductBase):
    """Полная модель товара"""
    id: int
    image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True

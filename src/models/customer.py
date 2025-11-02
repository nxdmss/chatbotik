"""
Модель клиента
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """Базовая модель клиента"""
    telegram_id: str = Field(..., min_length=1)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Модель для создания клиента"""
    pass


class Customer(CustomerBase):
    """Полная модель клиента"""
    id: int
    is_admin: bool = False
    created_at: datetime
    last_activity: datetime
    
    class Config:
        from_attributes = True
    
    @property
    def full_name(self) -> str:
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return ' '.join(parts) or self.username or f"User {self.telegram_id}"

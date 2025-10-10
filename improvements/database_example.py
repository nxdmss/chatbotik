# Пример миграции на SQLAlchemy + SQLite
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default='RUB')
    photo = Column(String)
    sizes = Column(JSON)  # [38, 39, 40, 41]
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    status = Column(String, default='new')
    items = Column(JSON)  # [{product_id, qty, size, price}]
    total = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    invoice_payload = Column(String)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # telegram user_id
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    orders_count = Column(Integer, default=0)

# Подключение
engine = create_engine('sqlite:///shop.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
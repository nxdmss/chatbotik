"""
Core Configuration Module
========================

Централизованная конфигурация приложения с валидацией через Pydantic.
Следует принципам 12-factor app.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения с автоматической загрузкой из environment variables.
    
    Attributes:
        APP_NAME: Название приложения
        APP_VERSION: Версия приложения
        ENVIRONMENT: Окружение (development, staging, production)
        DEBUG: Режим отладки
        
        BOT_TOKEN: Telegram Bot API токен
        WEBHOOK_URL: URL для webhook (опционально)
        WEBHOOK_PATH: Путь для webhook
        
        DATABASE_URL: URL для подключения к PostgreSQL
        DATABASE_ECHO: Логировать SQL запросы
        
        REDIS_URL: URL для подключения к Redis
        REDIS_TTL: Время жизни кэша (секунды)
        
        SECRET_KEY: Секретный ключ для подписей
        ADMIN_IDS: Список ID администраторов
        
        API_HOST: Хост API сервера
        API_PORT: Порт API сервера
        API_WORKERS: Количество воркеров
        
        UPLOAD_DIR: Директория для загрузки файлов
        MAX_UPLOAD_SIZE: Максимальный размер файла (MB)
        ALLOWED_EXTENSIONS: Разрешенные расширения файлов
        
        RATE_LIMIT_REQUESTS: Лимит запросов
        RATE_LIMIT_PERIOD: Период для лимита (секунды)
        
        SENTRY_DSN: Sentry DSN для error tracking
        LOG_LEVEL: Уровень логирования
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Telegram Shop Bot"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = Field(default=True)
    
    # Telegram Bot
    BOT_TOKEN: str = Field(..., min_length=40, description="Telegram Bot API Token")
    WEBHOOK_URL: str | None = Field(default=None, description="Webhook URL")
    WEBHOOK_PATH: str = Field(default="/webhook", description="Webhook path")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/shopbot",
        description="PostgreSQL connection URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    
    # Redis
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_TTL: int = Field(default=300, ge=0, description="Cache TTL in seconds")
    
    # Security
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for signing"
    )
    ADMIN_IDS: list[int] = Field(
        default_factory=list,
        description="List of admin user IDs"
    )
    
    # API
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, ge=1, le=65535, description="API port")
    API_WORKERS: int = Field(default=1, ge=1, le=16, description="Number of workers")
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    # File Upload
    UPLOAD_DIR: Path = Field(default=Path("uploads"), description="Upload directory")
    MAX_UPLOAD_SIZE: int = Field(default=10, ge=1, le=100, description="Max file size in MB")
    ALLOWED_EXTENSIONS: set[str] = Field(
        default={"jpg", "jpeg", "png", "gif", "webp"},
        description="Allowed file extensions"
    )
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=30, ge=1, description="Max requests")
    RATE_LIMIT_PERIOD: int = Field(default=60, ge=1, description="Period in seconds")
    
    # Monitoring
    SENTRY_DSN: str | None = Field(default=None, description="Sentry DSN")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Feature Flags
    ENABLE_WEBHOOK: bool = Field(default=False, description="Enable webhook mode")
    ENABLE_CACHE: bool = Field(default=True, description="Enable Redis cache")
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    
    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: str | list[int]) -> list[int]:
        """Parse admin IDs from string or list."""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    
    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def create_upload_dir(cls, v: Path) -> Path:
        """Create upload directory if not exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")
    
    def get_max_upload_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to create singleton pattern.
    Settings are loaded once and cached for application lifetime.
    
    Returns:
        Settings: Validated settings instance
        
    Raises:
        ValidationError: If environment variables are invalid
    """
    return Settings()


# Convenience accessor
settings = get_settings()


# Type aliases
Environment = Literal["development", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

"""
Logging Configuration
====================

Настройка логирования с поддержкой structured logging.
"""

import logging
import sys
from pathlib import Path
from typing import Any

from core.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Форматтер для structured logging.
    Добавляет контекст и метаданные к логам.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Добавляем extra fields
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in logging.LogRecord(
                "", 0, "", 0, "", (), None
            ).__dict__
        }
        
        # Форматируем сообщение
        message = super().format(record)
        
        # Добавляем extra fields
        if extra_fields:
            extra_str = " ".join(f"{k}={v}" for k, v in extra_fields.items())
            message = f"{message} {extra_str}"
        
        return message


def setup_logging() -> None:
    """
    Настройка логирования для приложения.
    
    Features:
    - Structured logging
    - File and console handlers
    - Different formats for different handlers
    - Log rotation
    """
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # Удаляем существующие handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_format = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    console_handler.setFormatter(StructuredFormatter(console_format))
    root_logger.addHandler(console_handler)
    
    # File handler (все логи)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)
    file_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s"
    )
    file_handler.setFormatter(StructuredFormatter(file_format))
    root_logger.addHandler(file_handler)
    
    # Error file handler (только ошибки)
    error_handler = logging.FileHandler(log_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter(file_format))
    root_logger.addHandler(error_handler)
    
    # Отключаем лишние логи от библиотек
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger для модуля.
    
    Args:
        name: Имя модуля (обычно __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Адаптер для добавления контекста к логам.
    
    Usage:
        logger = LoggerAdapter(logging.getLogger(__name__), {"user_id": 123})
        logger.info("User action", action="buy")
    """
    
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        # Добавляем extra context
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs

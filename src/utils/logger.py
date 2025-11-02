"""
Система логирования
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.config import LOG_LEVEL, LOG_FILE


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Настраивает логгер с правильным форматированием
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов (опционально)
        level: Уровень логирования (опционально)
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level or LOG_LEVEL)
    
    # Убираем существующие хендлеры
    logger.handlers.clear()
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый вывод
    if log_file or LOG_FILE:
        file_handler = logging.FileHandler(log_file or LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получает существующий логгер или создает новый
    
    Args:
        name: Имя логгера
    
    Returns:
        Логгер
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger

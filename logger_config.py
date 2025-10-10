"""
Конфигурация логирования для Telegram бота
"""

import structlog
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


def setup_logging(log_level: str = "INFO", log_file: str = "bot.log") -> None:
    """
    Настройка структурированного логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов
    """
    
    # Создаем директорию для логов если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Настраиваем базовое логирование
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / log_file, encoding='utf-8')
        ]
    )
    
    # Настраиваем structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Получить логгер с заданным именем
    
    Args:
        name: Имя логгера
        
    Returns:
        Настроенный логгер
    """
    return structlog.get_logger(name)


class BotLogger:
    """Класс для логирования действий бота"""
    
    def __init__(self, name: str = "bot"):
        self.logger = get_logger(name)
    
    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None) -> None:
        """Логирование действий пользователя"""
        self.logger.info(
            "user_action",
            user_id=user_id,
            action=action,
            details=details or {}
        )
    
    def log_admin_action(self, admin_id: str, action: str, target: str = None, details: Dict[str, Any] = None) -> None:
        """Логирование действий администратора"""
        self.logger.info(
            "admin_action",
            admin_id=admin_id,
            action=action,
            target=target,
            details=details or {}
        )
    
    def log_order_created(self, order_id: int, user_id: str, total: int, items_count: int) -> None:
        """Логирование создания заказа"""
        self.logger.info(
            "order_created",
            order_id=order_id,
            user_id=user_id,
            total=total,
            items_count=items_count
        )
    
    def log_order_status_changed(self, order_id: int, old_status: str, new_status: str, admin_id: str) -> None:
        """Логирование изменения статуса заказа"""
        self.logger.info(
            "order_status_changed",
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            admin_id=admin_id
        )
    
    def log_payment_received(self, order_id: int, user_id: str, amount: int) -> None:
        """Логирование получения платежа"""
        self.logger.info(
            "payment_received",
            order_id=order_id,
            user_id=user_id,
            amount=amount
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Логирование ошибок"""
        self.logger.error(
            "error_occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {}
        )
    
    def log_security_event(self, event_type: str, user_id: str = None, details: Dict[str, Any] = None) -> None:
        """Логирование событий безопасности"""
        self.logger.warning(
            "security_event",
            event_type=event_type,
            user_id=user_id,
            details=details or {}
        )
    
    def log_webapp_interaction(self, user_id: str, action: str, success: bool, details: Dict[str, Any] = None) -> None:
        """Логирование взаимодействий с WebApp"""
        self.logger.info(
            "webapp_interaction",
            user_id=user_id,
            action=action,
            success=success,
            details=details or {}
        )


# Глобальный экземпляр логгера
bot_logger = BotLogger()

"""
Обработчики ошибок для Telegram бота
"""

import asyncio
from typing import Any, Callable, Optional, Dict
from functools import wraps
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter
from pydantic import ValidationError
from logger_config import bot_logger


class BotError(Exception):
    """Базовый класс для ошибок бота"""
    def __init__(self, message: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.user_id = user_id
        self.context = context or {}
        super().__init__(self.message)


class ValidationError(BotError):
    """Ошибка валидации данных"""
    pass


class SecurityError(BotError):
    """Ошибка безопасности"""
    pass


class BusinessLogicError(BotError):
    """Ошибка бизнес-логики"""
    pass


def handle_errors(func: Callable) -> Callable:
    """
    Декоратор для обработки ошибок в обработчиках сообщений
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            bot_logger.log_error(e, {"user_id": e.user_id, "context": e.context})
            # Отправляем пользователю понятное сообщение об ошибке
            if args and isinstance(args[0], Message):
                await args[0].answer(f"❌ Ошибка в данных: {e.message}")
            elif args and isinstance(args[0], CallbackQuery):
                await args[0].answer(f"❌ Ошибка: {e.message}", show_alert=True)
        except SecurityError as e:
            bot_logger.log_security_event("security_error", e.user_id, e.context)
            if args and isinstance(args[0], Message):
                await args[0].answer("❌ Доступ запрещен")
            elif args and isinstance(args[0], CallbackQuery):
                await args[0].answer("❌ Доступ запрещен", show_alert=True)
        except BusinessLogicError as e:
            bot_logger.log_error(e, {"user_id": e.user_id, "context": e.context})
            if args and isinstance(args[0], Message):
                await args[0].answer(f"❌ {e.message}")
            elif args and isinstance(args[0], CallbackQuery):
                await args[0].answer(f"❌ {e.message}", show_alert=True)
        except TelegramRetryAfter as e:
            bot_logger.log_error(e, {"retry_after": e.retry_after})
            # Ждем указанное время перед повторной попыткой
            await asyncio.sleep(e.retry_after)
            try:
                return await func(*args, **kwargs)
            except Exception as retry_error:
                bot_logger.log_error(retry_error, {"retry_attempt": True})
        except TelegramBadRequest as e:
            bot_logger.log_error(e, {"error_code": e.error_code})
            if args and isinstance(args[0], Message):
                await args[0].answer("❌ Некорректный запрос. Попробуйте позже.")
            elif args and isinstance(args[0], CallbackQuery):
                await args[0].answer("❌ Некорректный запрос", show_alert=True)
        except TelegramNetworkError as e:
            bot_logger.log_error(e, {"network_error": True})
            if args and isinstance(args[0], Message):
                await args[0].answer("❌ Проблемы с сетью. Попробуйте позже.")
            elif args and isinstance(args[0], CallbackQuery):
                await args[0].answer("❌ Проблемы с сетью", show_alert=True)
        except Exception as e:
            bot_logger.log_error(e)
            if args and isinstance(args[0], Message):
                await args[0].answer("❌ Произошла неожиданная ошибка. Попробуйте позже.")
            elif args and isinstance(args[0], CallbackQuery):
                await args[0].answer("❌ Произошла ошибка", show_alert=True)
    
    return wrapper


def handle_webapp_errors(func: Callable) -> Callable:
    """
    Декоратор для обработки ошибок в WebApp обработчиках
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            bot_logger.log_error(e, {"webapp": True, "user_id": e.user_id})
            if args and isinstance(args[0], Message):
                await args[0].answer(f"❌ Ошибка в данных WebApp: {e.message}")
        except Exception as e:
            bot_logger.log_error(e, {"webapp": True})
            if args and isinstance(args[0], Message):
                await args[0].answer("❌ Ошибка обработки данных из WebApp")
    
    return wrapper


async def safe_send_message(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """
    Безопасная отправка сообщения с обработкой ошибок
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        text: Текст сообщения
        **kwargs: Дополнительные параметры
        
    Returns:
        True если сообщение отправлено успешно, False иначе
    """
    try:
        await bot.send_message(chat_id, text, **kwargs)
        return True
    except TelegramBadRequest as e:
        bot_logger.log_error(e, {"chat_id": chat_id, "action": "send_message"})
        return False
    except TelegramNetworkError as e:
        bot_logger.log_error(e, {"chat_id": chat_id, "action": "send_message"})
        return False
    except Exception as e:
        bot_logger.log_error(e, {"chat_id": chat_id, "action": "send_message"})
        return False


async def safe_send_photo(bot: Bot, chat_id: int, photo: str, caption: str = None, **kwargs) -> bool:
    """
    Безопасная отправка фото с обработкой ошибок
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        photo: ID или URL фото
        caption: Подпись к фото
        **kwargs: Дополнительные параметры
        
    Returns:
        True если фото отправлено успешно, False иначе
    """
    try:
        await bot.send_photo(chat_id, photo, caption=caption, **kwargs)
        return True
    except TelegramBadRequest as e:
        bot_logger.log_error(e, {"chat_id": chat_id, "action": "send_photo"})
        return False
    except TelegramNetworkError as e:
        bot_logger.log_error(e, {"chat_id": chat_id, "action": "send_photo"})
        return False
    except Exception as e:
        bot_logger.log_error(e, {"chat_id": chat_id, "action": "send_photo"})
        return False


def validate_user_input(text: str, max_length: int = 1000, min_length: int = 1) -> str:
    """
    Валидация пользовательского ввода
    
    Args:
        text: Входной текст
        max_length: Максимальная длина
        min_length: Минимальная длина
        
    Returns:
        Очищенный текст
        
    Raises:
        ValidationError: Если текст не прошел валидацию
    """
    if not text or not isinstance(text, str):
        raise ValidationError("Текст не может быть пустым")
    
    cleaned = text.strip()
    
    if len(cleaned) < min_length:
        raise ValidationError(f"Текст слишком короткий (минимум {min_length} символов)")
    
    if len(cleaned) > max_length:
        raise ValidationError(f"Текст слишком длинный (максимум {max_length} символов)")
    
    # Удаляем потенциально опасные символы
    dangerous_chars = ['<', '>', '"', "'", '&']
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    
    return cleaned


def validate_admin_access(user_id: str, admins: list) -> bool:
    """
    Проверка прав администратора
    
    Args:
        user_id: ID пользователя
        admins: Список ID администраторов
        
    Returns:
        True если пользователь является администратором
        
    Raises:
        SecurityError: Если доступ запрещен
    """
    if str(user_id) not in admins:
        raise SecurityError("Доступ запрещен", user_id=str(user_id))
    return True


def validate_order_data(data: dict) -> dict:
    """
    Валидация данных заказа
    
    Args:
        data: Словарь с данными заказа
        
    Returns:
        Валидированные данные
        
    Raises:
        ValidationError: Если данные не прошли валидацию
    """
    required_fields = ['text', 'items', 'total']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Отсутствует обязательное поле: {field}")
    
    if not isinstance(data['items'], list) or not data['items']:
        raise ValidationError("Заказ должен содержать товары")
    
    if not isinstance(data['total'], (int, float)) or data['total'] <= 0:
        raise ValidationError("Некорректная сумма заказа")
    
    return data

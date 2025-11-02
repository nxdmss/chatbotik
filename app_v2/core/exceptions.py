"""
Custom Exceptions
================

Кастомные исключения для приложения.
Следуют принципу "exception hierarchy".
"""


class AppException(Exception):
    """Базовое исключение приложения."""
    
    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


# Domain Exceptions
class DomainException(AppException):
    """Исключения доменного слоя."""
    pass


class EntityNotFoundError(DomainException):
    """Сущность не найдена."""
    pass


class ProductNotFoundError(EntityNotFoundError):
    """Товар не найден."""
    pass


class UserNotFoundError(EntityNotFoundError):
    """Пользователь не найден."""
    pass


class OrderNotFoundError(EntityNotFoundError):
    """Заказ не найден."""
    pass


class ValidationError(DomainException):
    """Ошибка валидации данных."""
    pass


class InvalidPriceError(ValidationError):
    """Некорректная цена."""
    pass


class InsufficientStockError(ValidationError):
    """Недостаточно товара на складе."""
    pass


# Application Exceptions
class ApplicationException(AppException):
    """Исключения слоя приложения."""
    pass


class PermissionDeniedError(ApplicationException):
    """Недостаточно прав."""
    pass


class AuthenticationError(ApplicationException):
    """Ошибка аутентификации."""
    pass


# Infrastructure Exceptions
class InfrastructureException(AppException):
    """Исключения инфраструктурного слоя."""
    pass


class DatabaseError(InfrastructureException):
    """Ошибка базы данных."""
    pass


class CacheError(InfrastructureException):
    """Ошибка кэша."""
    pass


class StorageError(InfrastructureException):
    """Ошибка файлового хранилища."""
    pass


class ExternalAPIError(InfrastructureException):
    """Ошибка внешнего API."""
    pass


# Presentation Exceptions
class PresentationException(AppException):
    """Исключения слоя представления."""
    pass


class InvalidRequestError(PresentationException):
    """Некорректный запрос."""
    pass


class RateLimitExceededError(PresentationException):
    """Превышен лимит запросов."""
    pass

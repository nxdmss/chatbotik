"""
Утилиты для аутентификации и авторизации
"""

from functools import wraps
from typing import Callable, Optional
from flask import request, jsonify

from src.config import ADMIN_IDS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def is_admin(user_id: Optional[str]) -> bool:
    """
    Проверяет, является ли пользователь администратором
    
    Args:
        user_id: ID пользователя Telegram
    
    Returns:
        True если пользователь - администратор
    """
    if not user_id:
        return False
    
    return str(user_id) in ADMIN_IDS


def require_admin(func: Callable) -> Callable:
    """
    Декоратор для проверки прав администратора
    
    Usage:
        @app.route('/admin/products')
        @require_admin
        def admin_products():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Получаем user_id из заголовков
        user_id = request.headers.get('X-Telegram-User-ID') or \
                  request.args.get('user_id')
        
        if not is_admin(user_id):
            logger.warning(f"Unauthorized access attempt from user_id: {user_id}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'У вас нет прав доступа'
            }), 403
        
        return func(*args, **kwargs)
    
    return wrapper


def get_current_user_id() -> Optional[str]:
    """
    Получает ID текущего пользователя из запроса
    
    Returns:
        User ID или None
    """
    return request.headers.get('X-Telegram-User-ID') or \
           request.args.get('user_id')

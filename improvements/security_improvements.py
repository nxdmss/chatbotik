# Рекомендации по безопасности

"""
ТЕКУЩИЕ ПРОБЛЕМЫ БЕЗОПАСНОСТИ:

1. ❌ Нет валидации данных от WebApp
2. ❌ Админы определяются только по переменной среды
3. ❌ Нет проверки подлинности Telegram WebApp данных
4. ❌ Файлы загружаются без проверки типа/размера
5. ❌ Нет ограничений на количество запросов

РЕШЕНИЯ:
"""

import hmac
import hashlib
import json
from urllib.parse import unquote

def validate_telegram_data(init_data: str, bot_token: str) -> dict:
    """Проверка подлинности данных от Telegram WebApp"""
    try:
        data = dict([chunk.split("=", 1) for chunk in unquote(init_data).split("&")])
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == data.get('hash'):
            return json.loads(data.get('user', '{}'))
        return None
    except:
        return None

def validate_file_upload(file):
    """Проверка загружаемых файлов"""
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    if not file.filename:
        raise ValueError("Нет имени файла")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Недопустимый тип файла. Разрешены: {ALLOWED_EXTENSIONS}")
    
    # Проверка размера (если доступно)
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise ValueError("Файл слишком большой")
    
    return True

def rate_limit_check(user_id: str, action: str) -> bool:
    """Простая проверка лимитов запросов"""
    # Реализация зависит от выбранного хранилища (Redis, DB)
    pass

# Проверка прав администратора
def is_admin(user_id: str, init_data: str = None) -> bool:
    """Улучшенная проверка админских прав"""
    # 1. Проверка по списку админов
    if str(user_id) in ADMINS:
        return True
    
    # 2. Проверка подлинности WebApp данных
    if init_data:
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if user_data and str(user_data.get('id')) in ADMINS:
            return True
    
    return False
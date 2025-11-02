"""
Конфигурация приложения
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== TELEGRAM =====
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000')
PORT = int(os.getenv('PORT', 8000))

# ===== ADMIN =====
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '1593426947')
ADMIN_IDS = set(aid.strip() for aid in ADMIN_IDS_STR.split(',') if aid.strip())
ADMIN_PHONE = os.getenv('ADMIN_PHONE', '+7 (999) 123-45-67')

# ===== DATABASE =====
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')
DATABASE_URL = f"sqlite:///{BASE_DIR / DATABASE_PATH}"

# ===== UPLOADS =====
UPLOADS_DIR = BASE_DIR / os.getenv('UPLOADS_DIR', 'uploads')
UPLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 5 * 1024 * 1024))  # 5MB
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,webp').split(','))

# ===== LOGGING =====
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / os.getenv('LOG_FILE', 'bot.log')

# ===== PAYMENTS =====
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN', '')

# ===== ВАЛИДАЦИЯ КОНФИГУРАЦИИ =====
def validate_config():
    """Проверяет обязательные параметры конфигурации"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN не установлен")
    
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS не установлен")
    
    if errors:
        raise ValueError(
            "Ошибка конфигурации:\n" + "\n".join(f"  - {e}" for e in errors) +
            "\n\nПроверьте файл .env или переменные окружения"
        )

# Проверяем конфигурацию при импорте (опционально)
# validate_config()

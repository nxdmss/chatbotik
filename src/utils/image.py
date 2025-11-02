"""
Утилиты для работы с изображениями
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
import base64

try:
    from PIL import Image
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from src.config import UPLOADS_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImageValidationError(Exception):
    """Ошибка валидации изображения"""
    pass


def validate_image(image_data: bytes, max_size: int = MAX_FILE_SIZE) -> None:
    """
    Валидирует изображение
    
    Args:
        image_data: Байты изображения
        max_size: Максимальный размер в байтах
    
    Raises:
        ImageValidationError: Если изображение невалидно
    """
    # Проверяем размер
    if len(image_data) > max_size:
        raise ImageValidationError(
            f"Размер файла ({len(image_data)} байт) превышает "
            f"максимальный ({max_size} байт)"
        )
    
    # Проверяем формат с помощью PIL
    if PIL_AVAILABLE:
        try:
            img = Image.open(BytesIO(image_data))
            img.verify()
            
            # Проверяем расширение
            if img.format.lower() not in ALLOWED_EXTENSIONS:
                raise ImageValidationError(
                    f"Неподдерживаемый формат: {img.format}. "
                    f"Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
                )
        except Exception as e:
            raise ImageValidationError(f"Невалидное изображение: {e}")
    else:
        # Базовая проверка без PIL
        if not image_data.startswith(b'\xff\xd8\xff'):  # JPEG magic number
            if not image_data.startswith(b'\x89PNG'):    # PNG magic number
                raise ImageValidationError("Неподдерживаемый формат изображения")


def optimize_image(
    image_data: bytes,
    max_width: int = 1200,
    max_height: int = 1200,
    quality: int = 85
) -> bytes:
    """
    Оптимизирует изображение (сжатие, ресайз)
    
    Args:
        image_data: Байты изображения
        max_width: Максимальная ширина
        max_height: Максимальная высота
        quality: Качество JPEG (1-100)
    
    Returns:
        Оптимизированные байты изображения
    """
    if not PIL_AVAILABLE:
        logger.warning("PIL не установлен, пропускаем оптимизацию")
        return image_data
    
    try:
        # Открываем изображение
        img = Image.open(BytesIO(image_data))
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Ресайз если нужно
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            logger.info(f"Изображение уменьшено до {img.width}x{img.height}")
        
        # Сохраняем в байты
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        optimized_data = output.getvalue()
        
        logger.info(
            f"Изображение оптимизировано: "
            f"{len(image_data)} -> {len(optimized_data)} байт "
            f"({100 - len(optimized_data) * 100 // len(image_data)}% сжатие)"
        )
        
        return optimized_data
        
    except Exception as e:
        logger.error(f"Ошибка оптимизации изображения: {e}")
        return image_data


def save_image(
    image_data: str,
    optimize: bool = True,
    validate: bool = True
) -> str:
    """
    Сохраняет изображение из base64 строки
    
    Args:
        image_data: Base64 строка с изображением
        optimize: Оптимизировать изображение
        validate: Валидировать изображение
    
    Returns:
        URL сохраненного изображения
    
    Raises:
        ImageValidationError: Если изображение невалидно
    """
    try:
        # Проверяем входные данные
        if not image_data or not image_data.strip():
            raise ImageValidationError("Пустые данные изображения")
        
        # Убираем data:image/...;base64, если есть
        if image_data.startswith('data:'):
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
        
        # Декодируем base64
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise ImageValidationError(f"Ошибка декодирования base64: {e}")
        
        # Валидируем
        if validate:
            validate_image(image_bytes)
        
        # Оптимизируем
        if optimize:
            image_bytes = optimize_image(image_bytes)
        
        # Генерируем уникальное имя
        filename = f"{uuid.uuid4().hex[:16]}.jpg"
        filepath = UPLOADS_DIR / filename
        
        # Сохраняем файл
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Проверяем что файл создался
        if not filepath.exists():
            raise ImageValidationError(f"Не удалось создать файл: {filepath}")
        
        file_size = filepath.stat().st_size
        logger.info(f"Изображение сохранено: {filename} ({file_size} байт)")
        
        return f"/uploads/{filename}"
        
    except ImageValidationError:
        raise
    except Exception as e:
        logger.error(f"Ошибка сохранения изображения: {e}")
        raise ImageValidationError(f"Не удалось сохранить изображение: {e}")

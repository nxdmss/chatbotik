#!/usr/bin/env python3
"""
🖼️ СОВРЕМЕННАЯ СИСТЕМА ИЗОБРАЖЕНИЙ
===================================
Профессиональное решение для загрузки, обработки и отображения изображений
"""

import os
import base64
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
import time

try:
    from PIL import Image, ImageOps
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ModernImageProcessor:
    """Современный процессор изображений с оптимизацией"""
    
    def __init__(self, uploads_dir: str = "uploads"):
        self.uploads_dir = Path(uploads_dir)
        self.uploads_dir.mkdir(exist_ok=True)
        
        # Создаем подпапки для организации
        self.thumbnails_dir = self.uploads_dir / "thumbnails"
        self.originals_dir = self.uploads_dir / "originals"
        self.thumbnails_dir.mkdir(exist_ok=True)
        self.originals_dir.mkdir(exist_ok=True)
        
        # Настройки оптимизации
        self.max_size = (800, 600)  # Максимальный размер для отображения
        self.thumbnail_size = (300, 300)  # Размер превью
        self.quality = 85  # Качество JPEG
        self.max_file_size = 5 * 1024 * 1024  # 5MB максимум
        
        print(f"🖼️ ModernImageProcessor инициализирован")
        print(f"📁 Папки: {self.uploads_dir}, {self.thumbnails_dir}, {self.originals_dir}")
    
    def validate_image(self, base64_data: str) -> Tuple[bool, str]:
        """Валидация изображения"""
        if not base64_data:
            return False, "Нет данных изображения"
        
        # Проверяем размер
        if len(base64_data) > self.max_file_size * 4 / 3:  # Примерный размер base64
            return False, f"Изображение слишком большое (максимум {self.max_file_size // 1024 // 1024}MB)"
        
        # Проверяем формат
        if not base64_data.startswith('data:image/'):
            return False, "Неподдерживаемый формат изображения"
        
        return True, "OK"
    
    def extract_image_data(self, base64_string: str) -> Tuple[str, str, bytes]:
        """Извлечение данных из base64 строки"""
        try:
            # Парсим data URL
            header, data = base64_string.split(',', 1)
            mime_type = header.split(';')[0].replace('data:', '')
            
            # Декодируем base64
            image_data = base64.b64decode(data)
            
            return mime_type, data, image_data
            
        except Exception as e:
            raise ValueError(f"Ошибка парсинга base64: {e}")
    
    def generate_filename(self, original_name: str = "", mime_type: str = "image/jpeg") -> str:
        """Генерация уникального имени файла"""
        # Определяем расширение
        ext = mimetypes.guess_extension(mime_type) or '.jpg'
        
        # Генерируем уникальное имя
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        
        if original_name:
            # Создаем хеш от оригинального имени для консистентности
            name_hash = hashlib.md5(original_name.encode()).hexdigest()[:8]
            filename = f"{name_hash}_{timestamp}_{unique_id}{ext}"
        else:
            filename = f"img_{timestamp}_{unique_id}{ext}"
        
        return filename
    
    def optimize_image(self, image_data: bytes, target_size: Tuple[int, int], quality: int = 85) -> bytes:
        """Оптимизация изображения с помощью PIL"""
        if not PIL_AVAILABLE:
            return image_data
        
        try:
            # Открываем изображение
            image = Image.open(BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'LA', 'P'):
                # Создаем белый фон для прозрачных изображений
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Изменяем размер с сохранением пропорций
            image.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Применяем оптимизацию
            image = ImageOps.exif_transpose(image)  # Правильная ориентация
            
            # Сохраняем в буфер
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            print(f"⚠️ Ошибка оптимизации изображения: {e}")
            return image_data
    
    def save_image(self, base64_data: str, original_name: str = "") -> dict:
        """Сохранение и оптимизация изображения"""
        try:
            print(f"🖼️ Начинаем сохранение изображения...")
            
            # Валидация
            is_valid, message = self.validate_image(base64_data)
            if not is_valid:
                raise ValueError(message)
            
            # Извлекаем данные
            mime_type, data, image_data = self.extract_image_data(base64_data)
            print(f"📸 Извлечены данные: {len(image_data)} байт, тип: {mime_type}")
            
            # Генерируем имена файлов
            filename = self.generate_filename(original_name, mime_type)
            original_path = self.originals_dir / filename
            thumbnail_path = self.thumbnails_dir / filename
            
            # Сохраняем оригинал
            with open(original_path, 'wb') as f:
                f.write(image_data)
            
            # Создаем оптимизированную версию
            optimized_data = self.optimize_image(image_data, self.max_size, self.quality)
            with open(thumbnail_path, 'wb') as f:
                f.write(optimized_data)
            
            # Возвращаем информацию о файле
            result = {
                'success': True,
                'filename': filename,
                'original_path': str(original_path),
                'thumbnail_path': str(thumbnail_path),
                'original_size': len(image_data),
                'optimized_size': len(optimized_data),
                'mime_type': mime_type,
                'url': f'/uploads/thumbnails/{filename}',
                'original_url': f'/uploads/originals/{filename}'
            }
            
            print(f"✅ Изображение сохранено:")
            print(f"   📁 Файл: {filename}")
            print(f"   📊 Оригинал: {len(image_data)} → Оптимизировано: {len(optimized_data)} байт")
            print(f"   🌐 URL: {result['url']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка сохранения изображения: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_image(self, filename: str) -> bool:
        """Удаление изображения и всех его версий"""
        try:
            deleted_count = 0
            
            # Удаляем из всех папок
            for folder in [self.originals_dir, self.thumbnails_dir]:
                file_path = folder / filename
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
                    print(f"🗑️ Удален: {file_path}")
            
            return deleted_count > 0
            
        except Exception as e:
            print(f"❌ Ошибка удаления изображения {filename}: {e}")
            return False
    
    def get_image_info(self, filename: str) -> Optional[dict]:
        """Получение информации об изображении"""
        try:
            thumbnail_path = self.thumbnails_dir / filename
            original_path = self.originals_dir / filename
            
            if not thumbnail_path.exists():
                return None
            
            # Получаем размеры файлов
            thumbnail_size = thumbnail_path.stat().st_size
            original_size = original_path.stat().st_size if original_path.exists() else thumbnail_size
            
            return {
                'filename': filename,
                'thumbnail_exists': thumbnail_path.exists(),
                'original_exists': original_path.exists(),
                'thumbnail_size': thumbnail_size,
                'original_size': original_size,
                'thumbnail_url': f'/uploads/thumbnails/{filename}',
                'original_url': f'/uploads/originals/{filename}'
            }
            
        except Exception as e:
            print(f"❌ Ошибка получения информации об изображении {filename}: {e}")
            return None
    
    def list_images(self) -> list:
        """Список всех изображений"""
        try:
            images = []
            for thumbnail_path in self.thumbnails_dir.glob('*'):
                if thumbnail_path.is_file():
                    info = self.get_image_info(thumbnail_path.name)
                    if info:
                        images.append(info)
            return images
        except Exception as e:
            print(f"❌ Ошибка получения списка изображений: {e}")
            return []

# Тестирование
if __name__ == "__main__":
    processor = ModernImageProcessor()
    
    # Тестовые данные
    test_base64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
    
    result = processor.save_image(test_base64, "test_image.jpg")
    print(f"Результат теста: {result}")

# 💾 Система автоматического сохранения базы данных

## 🎯 Что делает система

Теперь **база данных сохраняется автоматически** при каждом изменении:

1. ✅ **Автобэкап при запуске сервера** - создается резервная копия
2. ✅ **Автосохранение после каждого действия**:
   - Добавление товара → сохранение в JSON
   - Удаление товара → сохранение в JSON
   - Редактирование товара → сохранение в JSON
3. ✅ **Экспорт в JSON** - файл `products_backup.json` всегда актуален
4. ✅ **Автоочистка** - хранятся только 10 последних бэкапов БД

## 📂 Файлы

- `shop.db` - основная база данных
- `products_backup.json` - JSON бэкап (в Git)
- `db_backups/` - директория с бэкапами БД (не в Git)
- `backup_db.py` - скрипт для ручного управления бэкапами

## 🚀 Автоматическая работа

Система работает автоматически! При запуске `perfect_server.py`:

```bash
python perfect_server.py
```

Вы увидите:
```
✅ База данных инициализирована
💾 Автобэкап создан: db_backups/shop_backup_20251012_043020.db
📄 JSON бэкап: products_backup.json (7 товаров)
```

При каждом изменении:
```
✅ Товар добавлен в БД: ID=8, Новые кроссовки
📄 JSON бэкап: products_backup.json (8 товаров)
```

## 🔧 Ручное управление

### Создать бэкап
```bash
python backup_db.py backup
```

### Экспортировать в JSON
```bash
python backup_db.py export
```

### Восстановить из последнего бэкапа
```bash
python backup_db.py restore
```

### Восстановить из JSON
```bash
python backup_db.py restore-json
```

## 📦 Восстановление на Replit

Если база данных сброшена на Replit:

1. **Автоматически** (из JSON):
```bash
python backup_db.py restore-json
```

2. **Или скопируйте из GitHub**:
```bash
git pull origin main
python backup_db.py restore-json
```

## 🔄 Синхронизация с GitHub

### Важно! 

Файл `products_backup.json` автоматически сохраняется в Git.

Чтобы отправить последнюю версию:
```bash
git add products_backup.json shop.db
git commit -m "Обновление базы данных"
git push origin main
```

### В Replit для получения изменений:
```bash
git stash  # Сохранить локальные изменения
git pull origin main  # Скачать изменения
git stash pop  # Вернуть локальные изменения (если нужно)
```

## ⚡ Быстрые команды для Replit

### Полная синхронизация с GitHub:
```bash
# Сохранить и отправить
git add products_backup.json shop.db && git commit -m "DB update" && git push

# Получить с GitHub
git stash && git pull origin main
```

### Если база пустая:
```bash
python backup_db.py restore-json
```

## 🛡️ Защита от потери данных

1. **10 локальных бэкапов БД** в `db_backups/`
2. **JSON бэкап** в Git - `products_backup.json`
3. **Основная БД** в Git - `shop.db`
4. **Автосохранение** после каждого действия

## 📊 Структура JSON бэкапа

```json
[
  {
    "id": 1,
    "title": "Кроссовки Nike",
    "description": "Удобные кроссовки",
    "price": 5990.0,
    "sizes": ["40", "41", "42"],
    "photo": "/webapp/static/uploads/photo_123.jpg",
    "is_active": true,
    "created_at": "2025-10-12T04:20:00"
  }
]
```

## ✨ Преимущества

- ✅ **Всегда актуальные данные** в Git
- ✅ **Легкое восстановление** за 1 команду
- ✅ **Человекочитаемый JSON** для проверки
- ✅ **Не нужно помнить** - все автоматически!
- ✅ **Защита от сбоев** Replit

---

**Теперь вы никогда не потеряете данные!** 🎉


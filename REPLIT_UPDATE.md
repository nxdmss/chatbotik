# 🚀 Быстрое обновление в Replit

## ⚡ Одна команда - всё готово!

Запустите в Shell (Replit):

```bash
bash update_replit.sh
```

Эта команда автоматически:
- 💾 Сохранит локальные изменения
- 📥 Скачает обновления с GitHub
- 🛑 Остановит старый сервер
- 🔍 Проверит базу данных
- 📦 Восстановит БД если нужно
- 🚀 Запустит новый сервер

---

## 📋 Альтернативные команды

### Быстрый перезапуск сервера
```bash
lsof -ti :8000 | xargs kill -9; python3 perfect_server.py
```

### Обновление с GitHub
```bash
git stash && git pull origin main
```

### Восстановление базы данных
```bash
python3 backup_db.py restore-json
```

### Полная синхронизация
```bash
git stash
git pull origin main
lsof -ti :8000 | xargs kill -9
sleep 2
python3 backup_db.py restore-json
python3 perfect_server.py
```

---

## 🔥 Частые проблемы

### Порт занят (Address already in use)
```bash
lsof -ti :8000 | xargs kill -9
```

### База данных пустая
```bash
python3 backup_db.py restore-json
```

### Конфликт при git pull
```bash
git stash
git pull origin main
```

### Нет изменений после обновления
Очистите кеш браузера: **Ctrl+Shift+R** (или Cmd+Shift+R на Mac)

---

## 💡 Совет

Добавьте в `.replit` файл:

```toml
run = "bash update_replit.sh"
```

Теперь кнопка **Run** будет автоматически обновлять и запускать проект! 🎉


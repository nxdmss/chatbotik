"""
ИНСТРУКЦИЯ ПО МИГРАЦИИ НА НОВУЮ СТРУКТУРУ
==========================================

1. РЕЗЕРВНОЕ КОПИРОВАНИЕ
   Перед началом создайте резервные копии:
   ```bash
   cp shop.db shop.db.backup
   cp customer_support.db customer_support.db.backup
   cp -r uploads uploads.backup
   ```

2. УСТАНОВКА ЗАВИСИМОСТЕЙ
   ```bash
   pip install -r requirements.txt
   ```

3. НАСТРОЙКА .env
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Обязательно заполните:
   - BOT_TOKEN (получите от @BotFather)
   - ADMIN_IDS (получите от @userinfobot)
   - WEBAPP_URL (ваш URL или http://localhost:8000)

4. ИНИЦИАЛИЗАЦИЯ НОВОЙ БАЗЫ ДАННЫХ
   ```bash
   python -m src.database
   ```
   
   Это создаст новую БД database.db и автоматически мигрирует данные
   из shop.db и customer_support.db

5. ЗАПУСК
   ```bash
   python main_new.py
   ```

6. ПРОВЕРКА
   - Откройте http://localhost:8000
   - Проверьте что все товары на месте
   - Проверьте админ-панель
   - Проверьте что бот отвечает

7. ПЕРЕХОД НА НОВУЮ СТРУКТУРУ
   Когда убедитесь что все работает:
   ```bash
   # Переименуйте старый main.py
   mv main.py main_old.py
   
   # Переименуйте новый main.py
   mv main_new.py main.py
   
   # Переименуйте новый README
   mv README.md README_OLD.md
   mv README_NEW.md README.md
   
   # Удалите старые файлы (ОСТОРОЖНО!)
   rm no_telegram_bot_fixed.py
   rm config_example.env
   rm env.replit.example
   ```

8. ОЧИСТКА (опционально)
   После успешной миграции и когда убедитесь что все работает:
   ```bash
   # Удалите старые базы данных
   rm shop.db customer_support.db
   
   # Удалите резервные копии (если все ОК)
   rm *.backup
   rm -rf uploads.backup
   ```

ВАЖНЫЕ ЗАМЕТКИ:
- НЕ удаляйте старые файлы пока не убедитесь что новая версия работает!
- Файл .env НИКОГДА не коммитьте в Git!
- В продакшене используйте HTTPS
- Регулярно делайте backup базы данных

ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК:
1. Остановите приложение (Ctrl+C)
2. Восстановите из резервных копий:
   ```bash
   cp shop.db.backup shop.db
   cp customer_support.db.backup customer_support.db
   cp -r uploads.backup uploads
   ```
3. Запустите старую версию:
   ```bash
   python main_old.py
   ```

ПОДДЕРЖКА:
- GitHub Issues: https://github.com/nxdmss/chatbotik/issues
- Документация: README.md

# 🚀 ЗАПУСК НА REPLIT

Токен уже в Secrets? Отлично! Просто запустите! 🎉

---

## ⚡ БЫСТРЫЙ ЗАПУСК (1 команда)

```bash
./REPLIT_RUN.sh
```

**ВСЁ!** Скрипт всё сделает сам! 🎯

---

## 📋 Что делает скрипт:

✅ Останавливает старые процессы  
✅ Освобождает порты  
✅ Берет токен из Secrets  
✅ Обновляет код из Git  
✅ Запускает приложение  

---

## 🎯 Ручной запуск (если нужно):

### Вариант 1 - Простой:
```bash
python3 main.py
```

### Вариант 2 - С обновлением:
```bash
git pull origin main && python3 main.py
```

### Вариант 3 - Из папки chatbotik:
```bash
cd chatbotik && python3 main.py
```

---

## ⚙️ Настройка Secrets в Replit:

1. Откройте **Secrets** (🔐 в левом меню)
2. Добавьте/проверьте:
   - **Key:** `BOT_TOKEN`
   - **Value:** `8226153553:ваш_полный_токен`
3. Сохраните
4. Перезапустите Repl

---

## 🌐 WebApp URL для бота:

После запуска ваш URL будет:
```
https://ваш-repl.username.repl.co/webapp/
```

Или просто:
```
https://ваш-repl.repl.co
```

Укажите этот URL в настройках бота (@BotFather) как WebApp URL.

---

## 📦 Настройка WebApp в боте:

1. Напишите @BotFather в Telegram
2. Выберите `/mybots`
3. Выберите вашего бота
4. Нажмите `Bot Settings`
5. Нажмите `Menu Button`
6. Укажите URL: `https://ваш-repl.repl.co/webapp/`

---

## 🧪 Тестирование:

1. Запустите: `./REPLIT_RUN.sh`
2. Дождитесь: `✅ Бот готов к работе`
3. Напишите боту: `/start`
4. Нажмите "Открыть магазин"
5. Сделайте тестовый заказ
6. **Заказ придет вам!** ✅

---

## 🐛 Если что-то не работает:

### Токен не найден?
```bash
# Проверить
echo $BOT_TOKEN

# Если пусто - проверьте Secrets в Replit
```

### Порт занят?
```bash
lsof -ti:8000 | xargs kill -9
```

### Обновить код:
```bash
git pull origin main
```

### Перезапустить:
```bash
pkill -9 -f python
./REPLIT_RUN.sh
```

---

## 📊 Проверка логов:

```bash
tail -f logs/bot.log
```

или

```bash
tail -f chatbotik/logs/bot.log
```

---

## ✨ ГОТОВО!

Ваш магазин работает на Replit! 🛍️

**Админ:** ID 1593426947  
**Порт:** 8000  
**URL:** https://ваш-repl.repl.co

---

## 💡 Полезные команды:

### Проверить процессы:
```bash
ps aux | grep python
```

### Остановить всё:
```bash
pkill -9 -f python
```

### Посмотреть порты:
```bash
lsof -i :8000
```

### Обновить и запустить:
```bash
git pull origin main && ./REPLIT_RUN.sh
```

---

🎉 **Всё работает! Принимайте заказы!**


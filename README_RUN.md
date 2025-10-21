# 🚀 ЗАПУСК МАГАЗИН-БОТА

## ⚡ БЫСТРЫЙ СТАРТ (2 команды)

### 1️⃣ Установите токен бота:
```bash
export BOT_TOKEN='8226153553:ваш_полный_токен_от_BotFather'
```

### 2️⃣ Запустите:
```bash
./LAUNCH.sh
```

**ВСЁ!** 🎉

---

## 🎯 Что работает:

✅ Веб-сервер на http://localhost:8000  
✅ Telegram бот получает команды  
✅ WebApp открывается через бота  
✅ **Заказы приходят вам в Telegram!**  

---

## 📝 Полная инструкция:

### Шаг 1: Клонируйте/обновите репозиторий
```bash
git pull origin main
```

### Шаг 2: Установите токен
```bash
export BOT_TOKEN='ваш_токен'
```

### Шаг 3: Запустите
```bash
cd /Users/nxdms/Documents/GitHub/chatbot/chatbotik
./LAUNCH.sh
```

---

## 🌐 Для сервера (Replit):

```bash
cd /workspace/chatbotik
export BOT_TOKEN='ваш_токен'
./LAUNCH.sh
```

Или:
```bash
export BOT_TOKEN='ваш_токен' && git pull origin main && ./LAUNCH.sh
```

---

## 🧪 Тестирование:

1. Запустите бота (`./LAUNCH.sh`)
2. Напишите боту `/start` в Telegram
3. Нажмите "Открыть магазин"
4. Добавьте товары в корзину
5. Нажмите "Оформить заказ"
6. **Заказ придет вам!** ✅

---

## 🐛 Если что-то не работает:

### Порт занят?
```bash
lsof -ti:8000 | xargs kill -9
```

### Токен не установлен?
```bash
echo $BOT_TOKEN  # Проверить
export BOT_TOKEN='ваш_токен'  # Установить
```

### Процессы не останавливаются?
```bash
pkill -9 -f python
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

Ваш магазин-бот с заказами работает! 🛍️

**Админ ID:** 1593426947  
**Порт:** 8000  
**База данных:** shop.db, customer_support.db

---

💡 **Совет:** Сохраните команду с токеном в `.bashrc` или `.zshrc`:
```bash
echo "export BOT_TOKEN='ваш_токен'" >> ~/.bashrc
source ~/.bashrc
```

Тогда токен будет всегда доступен!


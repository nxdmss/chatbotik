# ⚡ БЫСТРЫЙ СТАРТ

## 🚀 **Обновить Replit из GitHub:**

### В Shell Replit введите:
```bash
git pull origin main
python3 main.py
```

**Готово!** Приложение работает! 🎉

---

## 🔧 **Если ошибка "Port already in use":**
```bash
pkill -9 -f "python.*server"
python3 main.py
```

---

## 📦 **Если ошибка "Module not found":**
```bash
pip install -r requirements.txt
python3 main.py
```

---

## ✅ **Проверить работу API:**

```bash
# Список товаров
curl http://localhost:8000/webapp/products.json

# Добавить товар
curl -X POST http://localhost:8000/webapp/admin/products \
  -H "Content-Type: application/json" \
  -d '{"title":"Новый товар","price":1500,"sizes":["M","L"]}'

# Удалить товар (ID=1)
curl -X DELETE http://localhost:8000/webapp/admin/products/1?user_id=admin
```

---

## 📱 **URL вашего приложения:**
```
https://chatbotik-ваш-username.replit.app
```

---

**Полная инструкция:** [REPLIT_UPDATE_GUIDE.md](./REPLIT_UPDATE_GUIDE.md)

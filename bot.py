#!/usr/bin/env python3
# coding: utf-8

import os
import json
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
    WebAppInfo,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
from shop.catalog import PRODUCTS, get_product, format_price
from shop.cart import get_cart, cart_total

# ======================
# 🔹 Настройки и переменные
# ======================

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [x.strip() for x in os.getenv("ADMINS", "").split(",") if x.strip()]

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

ADMINS = [str(x) for x in ADMINS]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

DATA_FILE = "orders.json"
ADMIN_MSGS_FILE = "admin_msgs.json"

data = {
    "orders": {},
    "order_counter": 1,
    "user_states": {},
    "admin_note_state": {},
    "dialogs": {}  # user_id: [ {"from": "user"/"admin", "text": ...} ]
}

STATUSES = {"Новый": "new", "В работе": "work", "Завершён": "done"}
REVERSE_STATUSES = {v: k for k, v in STATUSES.items()}

# Catalog and cart helpers are provided by shop package (shop.catalog, shop.cart)


# ======================
# 🔹 FSM: админский диалог
# ======================
class AdminDialog(StatesGroup):
    chatting = State()

class ContactAdmin(StatesGroup):
    waiting_message = State()

# ======================
# 🔹 Работа с данными
# ======================

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            data.update(loaded)

load_data()

def save_admin_msgs(admin_id, msg_id):
    msgs = {}
    if os.path.exists(ADMIN_MSGS_FILE):
        with open(ADMIN_MSGS_FILE, "r", encoding="utf-8") as f:
            msgs = json.load(f)
    msgs.setdefault(str(admin_id), []).append(msg_id)
    with open(ADMIN_MSGS_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

def get_admin_msgs(admin_id):
    if not os.path.exists(ADMIN_MSGS_FILE):
        return []
    with open(ADMIN_MSGS_FILE, "r", encoding="utf-8") as f:
        msgs = json.load(f)
    return msgs.get(str(admin_id), [])

def clear_admin_msgs(admin_id):
    if not os.path.exists(ADMIN_MSGS_FILE):
        return
    with open(ADMIN_MSGS_FILE, "r", encoding="utf-8") as f:
        msgs = json.load(f)
    msgs[str(admin_id)] = []
    with open(ADMIN_MSGS_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

# ======================
# 🔹 Клавиатуры
# ======================

def main_kb():
    # Динамически формируем клавиатуру: если есть WEBAPP_URL — показываем WebApp кнопку
    web_url = os.getenv('WEBAPP_URL') or os.getenv('REPL_URL') or os.getenv('REPL_SLUG')
    kb = []
    # Первая строка — крупная кнопка магазина (WebApp если доступен)
    if web_url and isinstance(web_url, str) and web_url.startswith('http'):
        kb.append([KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=web_url))])
    else:
        kb.append([KeyboardButton(text="🛍 Открыть магазин")])

    # Вторая строка — FAQ и связь с админом (оставляем только базовые клиентские кнопки)
    kb.append([KeyboardButton(text="❓ FAQ"), KeyboardButton(text="💬 Связь с админом")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_main_kb():
    web_url = os.getenv('WEBAPP_URL') or os.getenv('REPL_URL') or os.getenv('REPL_SLUG')
    kb = []
    # Админ-панель и быстрые команды
    kb.append([KeyboardButton(text="Админ-панель")])
    kb.append([KeyboardButton(text="🗑 Очистить чат")])
    # Если доступен webapp — добавим кнопку открытия магазина для админа
    if web_url and isinstance(web_url, str) and web_url.startswith('http'):
        # Open admin view (add admin=1 param)
        admin_url = web_url
        if '?' in admin_url:
            admin_url = admin_url + '&admin=1'
        else:
            admin_url = admin_url + '?admin=1'
        kb.append([KeyboardButton(text="🛍 Открыть магазин (админ)", web_app=WebAppInfo(url=admin_url))])
    else:
        kb.append([KeyboardButton(text="🛍 Открыть магазин (админ)")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_user_kb(user_id):
    return admin_main_kb() if str(user_id) in ADMINS else main_kb()

def exit_dialog_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Выйти из диалога")]],
        resize_keyboard=True
    )

def rating_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 6)]],
        resize_keyboard=True
    )

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Отмена")]],
        resize_keyboard=True
    )

async def get_user_name(user_id):
    try:
        chat = await bot.get_chat(int(user_id))
        return getattr(chat, "full_name", None) or getattr(chat, "username", None) or str(user_id)
    except Exception:
        return str(user_id)

async def admin_clients_kb():
    buttons = []
    for user_id in data.get("orders", {}):
        user_name = await get_user_name(user_id)
        buttons.append([
            InlineKeyboardButton(
                text=user_name,
                callback_data=f"adminclient_{user_id}"
            ),
            InlineKeyboardButton(
                text=f"💬 Связь с {user_name}",
                callback_data=f"adminchat_{user_id}"
            )
        ])
    if not buttons:
        buttons.append([InlineKeyboardButton(text="Нет клиентов", callback_data="none")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_client_orders_kb(user_id):
    buttons = []
    orders = data.get("orders", {}).get(user_id, [])
    for order in orders:
        btn_text = f"Заказ №{order['order_id']} | {order['text'][:20]}"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"adminorder_{user_id}_{order['order_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="adminback")])
    if len(orders) == 0:
        buttons.insert(0, [InlineKeyboardButton(text="Нет заказов", callback_data="none")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_order_full_kb(order, user_id, order_id):
    kb = [
        [InlineKeyboardButton(text="📝 Добавить заметку", callback_data=f"note_{user_id}_{order_id}")]
    ] + [
        [InlineKeyboardButton(text=f"📌 {name}", callback_data=f"status_{user_id}_{order_id}_{code}")]
        for name, code in STATUSES.items()
    ]
    # add delete button
    kb.append([InlineKeyboardButton(text="🗑 Удалить заказ", callback_data=f"delete_{user_id}_{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ======================
# 🔹 Пользовательские команды
# ======================

@dp.message(Command("start"))
async def start(msg: Message):
    data["user_states"].pop(str(msg.chat.id), None)
    if str(msg.chat.id) in ADMINS:
        await msg.answer(f"👋 Привет, админ!", reply_markup=admin_main_kb())
    else:
        await msg.answer(f"👋 Привет, {msg.from_user.first_name}!", reply_markup=main_kb())

@dp.message(F.text == "Админ-панель")
async def admin_panel_btn(msg: Message):
    if str(msg.chat.id) not in ADMINS:
        await msg.answer("❌ Только для админов!")
        return
    kb = await admin_clients_kb()
    await msg.answer(
        "Выберите клиента для просмотра заказов и связи:",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data.startswith("adminclient_"))
async def admin_client_orders(c: CallbackQuery):
    user_id = c.data.split("_")[1]
    kb = admin_client_orders_kb(user_id)
    user_name = await get_user_name(user_id)
    user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
    await c.message.edit_text(
        f"Клиент: {user_link}\nВыберите заказ или начните диалог:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    save_admin_msgs(c.from_user.id, c.message.message_id)
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith("adminchat_"))
async def admin_chat_with_client(c: CallbackQuery, state: FSMContext):
    user_id = c.data.split("_")[1]
    await state.set_state(AdminDialog.chatting)
    await state.update_data(user_id=user_id, order_id=None)
    history = data.get("dialogs", {}).get(user_id, [])
    history_text = "\n".join([
        f"{'👤 Пользователь' if m['from']=='user' else '🛠 Админ'}: {m.get('text','')}"
        for m in history[-20:]
    ]) if history else "Чат пуст. Напишите сообщение клиенту."
    user_name = await get_user_name(user_id)
    await bot.send_message(
        c.from_user.id,
        f"💬 Диалог с клиентом <b>{user_name}</b>:\n\n{history_text}",
        reply_markup=exit_dialog_kb(),
        parse_mode="HTML"
    )
    await c.answer()

@dp.callback_query(lambda c: c.data == "adminback")
async def admin_back_to_clients(c: CallbackQuery):
    kb = await admin_clients_kb()
    await c.message.edit_text(
        "Выберите клиента для просмотра заказов и связи:",
        reply_markup=kb
    )
    save_admin_msgs(c.from_user.id, c.message.message_id)
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith("adminorder_"))
async def admin_order_info(c: CallbackQuery):
    _, user_id, order_id = c.data.split("_")
    order_id = int(order_id)
    user_orders = data["orders"].get(user_id, [])
    order = next((o for o in user_orders if o["order_id"] == order_id), None)
    if not order:
        await c.answer("Заказ не найден", show_alert=True)
        return

    user_name = await get_user_name(user_id)
    user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"

    status_name = REVERSE_STATUSES.get(order["status"], order["status"])
    text = (f"🛒 Заказ №{order_id}\n"
            f"Статус: <b>{status_name}</b>\n"
            f"Пользователь: {user_link}\n"
            f"Текст: {order['text']}\n\n")
    notes = order.get("admin_notes", [])
    if notes:
        text += "🔒 Заметки админа (приватно):\n"
        for n in notes:
            t = n.get("time", "")
            aid = n.get("admin_id", "")
            atxt = n.get("text", "")
            text += f"- [{t}] admin {aid}: {atxt}\n"
    else:
        text += "🔒 Заметок админа нет.\n"

    kb = admin_order_full_kb(order, user_id, order_id)
    try:
        if "photo_id" in order:
            msg = await bot.send_photo(c.from_user.id, order["photo_id"], caption=text, reply_markup=kb)
        else:
            msg = await bot.send_message(c.from_user.id, text, reply_markup=kb)
        save_admin_msgs(
            c.from_user.id,
            msg.message_id if hasattr(msg, "message_id") else c.message.message_id)
    except Exception:
        pass
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith("open_"))
async def admin_open_order_dialog(c: CallbackQuery, state: FSMContext):
    await c.answer("Диалог по заказу больше не поддерживается.", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("note_"))
async def admin_add_note_cb(c: CallbackQuery):
    if str(c.from_user.id) not in ADMINS:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    _, user_id, order_id = c.data.split("_")
    data["admin_note_state"][str(c.from_user.id)] = (user_id, int(order_id))
    await bot.send_message(c.from_user.id, "📝 Введите заметку по этому заказу. Она будет видна только администраторам.")
    await c.answer()


@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def admin_delete_order(c: CallbackQuery):
    if str(c.from_user.id) not in ADMINS:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    _, user_id, order_id = c.data.split("_")
    order_id = int(order_id)
    user_orders = data.get('orders', {}).get(user_id, [])
    idx = next((i for i,o in enumerate(user_orders) if o.get('order_id')==order_id), None)
    if idx is None:
        await c.answer('Заказ не найден', show_alert=True)
        return
    # remove order
    removed = user_orders.pop(idx)
    # save back
    data['orders'][user_id] = user_orders
    save_data()
    # notify involved parties
    try:
        await bot.send_message(int(user_id), f"🗑 Ваш заказ #{order_id} был удалён администрацией.")
    except Exception:
        pass
    for admin_id in ADMINS:
        try:
            await bot.send_message(int(admin_id), f"🗑 Заказ #{order_id} пользователя {user_id} удалён администратором {c.from_user.id}")
        except Exception:
            pass
    await c.answer('Заказ удалён', show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("status_"))
async def change_order_status(c: CallbackQuery):
    _, user_id, order_id, status_code = c.data.split("_")
    order_id = int(order_id)
    if status_code not in REVERSE_STATUSES:
        await c.answer("Некорректный статус.", show_alert=True)
        return
    user_orders = data["orders"].get(user_id, [])
    order = next((o for o in user_orders if o["order_id"] == order_id), None)
    if not order:
        await c.answer("Заказ не найден.", show_alert=True)
        return
    order["status"] = status_code
    save_data()
    await c.answer(f"Статус изменён на '{REVERSE_STATUSES[status_code]}'", show_alert=True)
    try:
        await admin_order_info(c)
    except Exception:
        pass

@dp.message(F.text == "🗑 Очистить чат")
async def admin_clear_chat(msg: Message, state: FSMContext):
    if str(msg.chat.id) not in ADMINS:
        await msg.answer("❌ Только для админов!")
        return
    msgs = get_admin_msgs(msg.chat.id)
    for mid in msgs:
        try:
            await bot.delete_message(msg.chat.id, mid)
        except Exception:
            pass
    clear_admin_msgs(msg.chat.id)
    await state.clear()
    await msg.answer("✅ Чат и все окна очищены.", reply_markup=admin_main_kb())

@dp.message(F.text == "❓ FAQ")
async def faq(msg: Message):
    await msg.answer(
        "❓ <b>FAQ</b>\n\n"
        "📦 Как оформить заказ — нажмите '🛒 Сделать заказ' и опишите, что нужно.\n"
        "🚚 Доставка — мы свяжемся для уточнения.\n"
        "🔁 Возврат — в течение 14 дней.\n"
        "💬 Вопросы — просто напишите сообщение в чат!",
        reply_markup=get_user_kb(msg.chat.id)
    )


# ======================
# 🔹 Магазин: каталог, корзина, checkout (MVP)
# ======================

@dp.message(Command("catalog"))
@dp.message(F.text == "🛍 Каталог")
async def show_catalog(msg: Message):
    # Вывод простого каталога с inline-кнопкой "Добавить"
    webapp_url = os.getenv('WEBAPP_URL') or os.getenv('REPL_URL') or os.getenv('REPL_SLUG')
    if webapp_url and webapp_url.startswith('http'):
        kb_main = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛒 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]])
        try:
            await msg.answer("Откройте магазин внутри Telegram:", reply_markup=kb_main)
        except Exception:
            pass
    for p in PRODUCTS:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"Добавить — {format_price(p['price'])}", callback_data=f"addcart_{p['id']}")
        ]])
        text = f"<b>{p['title']}</b>\nЦена: {format_price(p['price'])}\nРазмеры: {', '.join(map(str,p['sizes']))}"
        try:
            if p.get('photo'):
                await msg.answer_photo(p['photo'], caption=text, reply_markup=kb)
            else:
                await msg.answer(text, reply_markup=kb)
        except Exception:
            await msg.answer(text, reply_markup=kb)



# Обработчик web_app_data: когда Web App вызывает Telegram.WebApp.sendData()
@dp.message()
async def handle_web_app_message(msg: Message):
    wad = getattr(msg, 'web_app_data', None)
    if not wad:
        return
    try:
        payload = json.loads(wad.data)
    except Exception:
        await msg.answer('⚠️ Неверный формат данных из Web App.')
        return

    # Ожидаем payload вида { action: 'checkout', items: [{id, qty}], total }
    action = payload.get('action')
    if action == 'add_product':
        # админ добавляет новый товар через WebApp
        if str(msg.from_user.id) not in ADMINS:
            await msg.answer('❌ Только администраторы могут добавлять товары.')
            return
        prod = payload.get('product') or {}
        # минимальная валидация
        title = prod.get('title')
        price = int(prod.get('price') or 0)
        sizes = prod.get('sizes') or []
        from shop.catalog import add_product
        if not title or price <= 0:
            await msg.answer('⚠️ Неверные данные товара. Проверьте название и цену.')
            return
        newp = {'title': title, 'price': price, 'currency': prod.get('currency','RUB'), 'photo': prod.get('photo',''), 'sizes': sizes}
        created = add_product(newp)
        await msg.answer(f"✅ Товар '{created.get('title')}' добавлен с id {created.get('id')}")
        # Notify other admins
        for admin_id in ADMINS:
            try:
                await bot.send_message(int(admin_id), f"🆕 Админ добавил товар: <b>{created.get('title')}</b> (id: {created.get('id')})", parse_mode='HTML')
            except Exception:
                pass
        return

    if action != 'checkout':
        await msg.answer('⚠️ Неподдерживаемое действие из Web App.')
        return

    user_id = str(msg.from_user.id)
    items = payload.get('items', [])
    total = payload.get('total', 0)

    # --- Server-side validation: пересчитаем сумму по PRODUCTS, чтобы не допустить подделки суммы ---
    expected_total = 0
    bad_items = []
    for it in items:
        pid = it.get('id') or it.get('product_id')
        qty = int(it.get('qty', 0) or 0)
        if not pid or qty <= 0:
            bad_items.append(it)
            continue
        prod = get_product(pid)
        if not prod:
            bad_items.append(it)
            continue
        expected_total += prod['price'] * qty

    if bad_items:
        await msg.answer('⚠️ В заказе обнаружены некорректные позиции. Пожалуйста, обновите корзину и попробуйте снова.')
        return

    if int(expected_total) != int(total):
        # Логируем несоответствие и отказываем в обработке
        await msg.answer('⚠️ Сумма заказа не совпадает с серверной проверкой. Пожалуйста, обновите корзину и попробуйте снова.')
        return

    order_id = data['order_counter']
    data['order_counter'] += 1
    order = {
        'order_id': order_id,
        'text': f"Заказ из WebApp, {len(items)} позиций, сумма {expected_total} ₽",
        'status': 'new',
        'items': items,
        'total': expected_total,
        'created_at': datetime.now().isoformat(),
        'from_webapp': True,
    }
    data.setdefault('orders', {}).setdefault(user_id, []).append(order)
    save_data()

    for admin_id in ADMINS:
        try:
            await bot.send_message(int(admin_id), f"🆕 Новый заказ #{order_id} (WebApp) от <a href='tg://user?id={user_id}'>Пользователя</a>\nСумма: {format_price(total)}", parse_mode='HTML')
        except Exception:
            pass

    await msg.answer(f"✅ Заказ #{order_id} создан. Администратор скоро свяжется для подтверждения.")


@dp.callback_query(lambda c: c.data and c.data.startswith('addcart_'))
async def add_to_cart_cb(c: CallbackQuery):
    pid = c.data.split('_', 1)[1]
    user_id = str(c.from_user.id)
    cart = get_cart(data, user_id)
    cart[pid] = cart.get(pid, 0) + 1
    save_data()
    await c.answer(text=f"Добавлено {get_product(pid)['title']} в корзину.")


@dp.message(F.text == "🛒 Моя корзина")
@dp.message(Command("cart"))
async def show_cart(msg: Message):
    user_id = str(msg.chat.id)
    cart = get_cart(data, user_id)
    if not cart:
        await msg.answer("🛒 Ваша корзина пуста", reply_markup=get_user_kb(msg.chat.id))
        return
    text = "🧾 Ваша корзина:\n"
    for pid, qty in cart.items():
        p = get_product(pid)
        if p:
            text += f"{p['title']} x{qty} — {format_price(p['price']*qty)}\n"
    total = cart_total(data, cart)
    text += f"\n<b>Итого: {format_price(total)}</b>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="Очистить корзину", callback_data="clearcart")]
    ])
    await msg.answer(text, reply_markup=kb, parse_mode="HTML")


@dp.callback_query(lambda c: c.data == 'clearcart')
async def clear_cart_cb(c: CallbackQuery):
    user_id = str(c.from_user.id)
    data.setdefault('carts', {})[user_id] = {}
    save_data()
    await c.answer('Корзина очищена')
    await c.message.edit_text('🛒 Ваша корзина пуста')


@dp.callback_query(lambda c: c.data == 'checkout')
async def checkout_cb(c: CallbackQuery):
    user_id = str(c.from_user.id)
    cart = get_cart(data, user_id)
    if not cart:
        await c.answer('Корзина пуста', show_alert=True)
        return
    total = cart_total(data, cart)
    # MVP: создаём заказ и имитируем переход на оплату (заглушка)
    order_id = data['order_counter']
    data['order_counter'] += 1
    items = []
    for pid, qty in cart.items():
        p = get_product(pid)
        if not p:
            continue
        items.append({'product_id': pid, 'title': p['title'], 'qty': qty, 'price': p['price']})

    order = {
        'order_id': order_id,
        'text': f"Заказ из корзины, {len(items)} позиций, сумма {total} ₽",
        'status': 'new',
        'items': items,
        'total': total,
        'created_at': datetime.now().isoformat()
    }
    data.setdefault('orders', {}).setdefault(user_id, []).append(order)
    # Очищаем корзину после создания заказа
    data.setdefault('carts', {})[user_id] = {}
    save_data()

    # Уведомляем админов
    for admin_id in ADMINS:
        try:
            await bot.send_message(int(admin_id), f"🆕 Новый заказ #{order_id} от <a href='tg://user?id={user_id}'>Пользователя</a>\nСумма: {format_price(total)}", parse_mode='HTML')
        except Exception:
            pass

    # Попытка отправить Invoice через Telegram Payments, если задан PROVIDER_TOKEN
    provider = os.getenv('PROVIDER_TOKEN')
    invoice_payload = f"order_{order_id}"
    order['invoice_payload'] = invoice_payload
    save_data()

    if provider:
        try:
            prices = [LabeledPrice(label=f"Оплата заказа #{order_id}", amount=int(total * 100))]
            await bot.send_invoice(
                chat_id=c.from_user.id,
                title=f"Оплата заказа #{order_id}",
                description=f"Заказ из корзины, {len(items)} позиций",
                payload=invoice_payload,
                provider_token=provider,
                currency="RUB",
                prices=prices,
                start_parameter=invoice_payload,
            )
            await c.message.edit_text(f"✅ Заказ #{order_id} создан. Счет отправлен в этот чат.")
            await c.answer()
            return
        except Exception:
            # если не получилось — fallback на ссылку
            pass

    # fallback: имитируем оплату: даём ссылку-заглушку
    pay_link = f"https://example.com/pay?order_id={order_id}&user_id={user_id}"
    await c.message.edit_text(f"✅ Заказ #{order_id} создан. Сумма: {format_price(total)}\nОплатите по ссылке: {pay_link}")
    await c.answer()


# Removed legacy 'make order' flow handlers: users create orders via WebApp or cart checkout.

async def send_order_to_admin(admin_id: int, user_id: str, order_info: dict):
    kb = admin_order_full_kb(order_info, user_id, order_info['order_id'])
    status_name = REVERSE_STATUSES.get(order_info['status'], "Новый")
    user_name = await get_user_name(user_id)
    user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
    text = f"🛒 Заказ №{order_info['order_id']} от {user_link}:\n{order_info['text']}\nСтатус: {status_name}"
    try:
        if "photo_id" in order_info:
            msg = await bot.send_photo(
                admin_id,
                order_info["photo_id"],
                caption=text,
                reply_markup=kb)
        else:
            msg = await bot.send_message(admin_id, text, reply_markup=kb)
        save_admin_msgs(admin_id, msg.message_id)
    except Exception:
        pass

@dp.message(F.text == "💬 Связь с админом")
async def client_start_chat(msg: Message, state: FSMContext):
    await state.set_state(ContactAdmin.waiting_message)
    await msg.answer("✍️ Напишите сообщение для администратора. Для выхода нажмите '🔙 Выйти из диалога'.", reply_markup=exit_dialog_kb())

@dp.message(ContactAdmin.waiting_message)
async def client_chat_message(msg: Message, state: FSMContext):
    user_id = str(msg.chat.id)
    if msg.text and msg.text.strip() and msg.text == "🔙 Выйти из диалога":
        await state.clear()
        await msg.answer("🚪 Вы вышли из диалога с админом.", reply_markup=get_user_kb(msg.chat.id))
        return
    dialogs = data.setdefault("dialogs", {}).setdefault(user_id, [])
    if msg.text:
        dialogs.append({"from": "user", "text": msg.text})
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        dialogs.append({"from": "user", "text": "[Фото]", "photo_id": file_id})
    elif msg.document:
        file_id = msg.document.file_id
        dialogs.append({"from": "user", "text": "[Документ]", "file_id": file_id})
    else:
        await msg.answer("⚠️ Сообщение не может быть пустым.")
        return
    data["dialogs"][user_id] = dialogs[-100:]
    save_data()
    user_name = await get_user_name(user_id)
    user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
    for admin_id in ADMINS:
        try:
            if msg.text:
                await bot.send_message(int(admin_id), f"💬 Сообщение от клиента {user_link}:\n{msg.text}")
            elif msg.photo:
                file_id = msg.photo[-1].file_id
                await bot.send_photo(int(admin_id), file_id, caption=f"💬 Сообщение от клиента {user_link}: [Фото]")
            elif msg.document:
                file_id = msg.document.file_id
                await bot.send_document(int(admin_id), file_id, caption=f"💬 Сообщение от клиента {user_link}: [Документ]")
        except Exception:
            pass
    await msg.answer("✅ Сообщение отправлено администратору.", reply_markup=exit_dialog_kb())

# Handler for 'My orders' removed per request; users can view orders via commands or admin panels.

@dp.message(F.text == "🔙 Назад")
async def back_to_main(msg: Message):
    await msg.answer("Главное меню:", reply_markup=get_user_kb(msg.chat.id))

@dp.message(Command("profile"))
async def user_profile(msg: Message):
    if str(msg.chat.id) in ADMINS:
        await msg.answer("Профиль доступен только пользователям.", reply_markup=admin_main_kb())
        return
    user_id = str(msg.chat.id)
    orders = data["orders"].get(user_id, [])
    total = len(orders)
    done = sum(o["status"] == "done" for o in orders)
    await msg.answer(f"👤 <b>Ваш профиль</b>\nID: <code>{user_id}</code>\nВсего заказов: <b>{total}</b>\nЗавершённых: <b>{done}</b>")


@dp.message(Command("dump_products"))
async def dump_products_cmd(msg: Message):
    if str(msg.chat.id) not in ADMINS:
        await msg.answer('❌ Только для админов')
        return
    path = os.path.join(os.path.dirname(__file__), 'shop', 'products.json')
    if not os.path.exists(path):
        await msg.answer('Файл каталога не найден')
        return
    try:
        await bot.send_document(msg.chat.id, path)
    except Exception:
        await msg.answer('Не удалось отправить файл')


# ======================
# 🔹 Админские диалоги и заметки
# ======================

@dp.message(AdminDialog.chatting)
async def admin_to_user(msg: Message, state: FSMContext):
    admin_id = str(msg.chat.id)
    data_state = await state.get_data()
    user_id = data_state.get("user_id")
    order_id = data_state.get("order_id")
    if not user_id:
        await msg.answer("❌ Информация о диалоге не найдена.", reply_markup=get_user_kb(msg.chat.id))
        await state.clear()
        return
    if msg.text and msg.text.strip() and msg.text == "🔙 Выйти из диалога":
        await state.clear()
        await msg.answer("🚪 Вы вышли из диалога.", reply_markup=get_user_kb(msg.chat.id))
        return
    if not (msg.text and msg.text.strip()) and not msg.photo and not msg.document:
        await msg.answer("⚠️ Сообщение не может быть пустым.")
        return
    dialogs = data.setdefault("dialogs", {}).setdefault(user_id, [])
    if msg.text:
        dialogs.append({"from": "admin", "text": msg.text})
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        dialogs.append({"from": "admin", "text": "[Фото]", "photo_id": file_id})
    elif msg.document:
        file_id = msg.document.file_id
        dialogs.append({"from": "admin", "text": "[Документ]", "file_id": file_id})
    data["dialogs"][user_id] = dialogs[-100:]
    save_data()
    try:
        if msg.text:
            await bot.send_message(int(user_id), f"💬 Сообщение от администратора:\n{msg.text}", reply_markup=get_user_kb(user_id))
            await msg.answer("✅ Сообщение отправлено клиенту.", reply_markup=exit_dialog_kb())
        elif msg.photo:
            file_id = msg.photo[-1].file_id
            await bot.send_photo(int(user_id), file_id, caption="💬 Сообщение от администратора:", reply_markup=get_user_kb(user_id))
            await msg.answer("✅ Фото отправлено клиенту.", reply_markup=exit_dialog_kb())
        elif msg.document:
            file_id = msg.document.file_id
            await bot.send_document(int(user_id), file_id, caption="💬 Сообщение от администратора:", reply_markup=get_user_kb(user_id))
            await msg.answer("✅ Документ отправлен клиенту.", reply_markup=exit_dialog_kb())
    except Exception:
        await msg.answer("⚠️ Не удалось доставить сообщение клиенту.", reply_markup=exit_dialog_kb())
    return

# NOTE: логика отправки сообщений по конкретному заказу пользователем удалена по запросу.

@dp.message(F.text == "🔙 Выйти из диалога")
async def exit_dialog(msg: Message, state: FSMContext):
    # Выходим из текущего FSM-диалога (админский или контакт с админом)
    current_state = await state.get_state()
    if current_state == AdminDialog.chatting.state or current_state == ContactAdmin.waiting_message.state:
        await state.clear()
        await msg.answer("🚪 Вы вышли из диалога.", reply_markup=get_user_kb(msg.chat.id))
        return

    await msg.answer("ℹ️ Вы не находитесь в диалоге.", reply_markup=get_user_kb(msg.chat.id))

@dp.message(lambda m: data["user_states"].get(str(m.chat.id)) == "waiting_rating")
async def receive_rating(msg: Message):
    user_id = str(msg.chat.id)
    rating = (msg.text or "").strip()
    if rating not in ["1", "2", "3", "4", "5"]:
        await msg.answer("Пожалуйста, оцените от 1 до 5.", reply_markup=rating_kb())
        return
    data["user_states"].pop(user_id, None)
    for admin_id in ADMINS:
        try:
            await bot.send_message(int(admin_id), f"⭐ Оценка от пользователя ID {user_id}: {rating}/5")
        except Exception:
            pass
    await msg.answer("Спасибо за вашу оценку!", reply_markup=get_user_kb(user_id))

@dp.message(lambda m: str(m.chat.id) in data.get("admin_note_state", {}))
async def admin_receive_note(msg: Message):
    admin_id = str(msg.chat.id)
    if admin_id not in ADMINS:
        await msg.answer("❌ Только для админов!")
        data["admin_note_state"].pop(admin_id, None)
        return
    state = data["admin_note_state"].pop(admin_id, None)
    if not state:
        await msg.answer("❌ Состояние не найдено.")
        return
    user_id, order_id = state
    user_orders = data["orders"].get(user_id, [])
    order = next((o for o in user_orders if o["order_id"] == order_id), None)
    if not order:
        await msg.answer("❌ Заказ не найден.")
        return
    note = {
        "admin_id": admin_id,
        "text": msg.text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    order.setdefault("admin_notes", []).append(note)
    order["admin_notes"] = order["admin_notes"][-100:]
    save_data()
    await msg.answer("✅ Заметка сохранена (видна только админам).", reply_markup=get_user_kb(msg.chat.id))

# ======================
# 🔹 Запуск
# ======================

async def main():
    print("🤖 Бот запущен на aiogram 3.x (с FSM для админских диалогов)!")
    await dp.start_polling(bot)


# ======================
# 🔹 Telegram Payments: обработчики pre_checkout и successful_payment
# ======================


@dp.pre_checkout_query()
async def handle_pre_checkout(pre: PreCheckoutQuery):
    # Подтверждаем pre-checkout (пока всегда одобряем)
    try:
        await bot.answer_pre_checkout_query(pre.id, ok=True)
    except Exception:
        pass


@dp.message()
async def handle_successful_payment(msg: Message):
    # Если сообщение содержит successful_payment — отмечаем заказ как оплаченный
    if not getattr(msg, 'successful_payment', None):
        return
    payload = msg.successful_payment.invoice_payload
    # payload мы сохраняем в order['invoice_payload'] как 'order_<id>'
    if not payload or not payload.startswith('order_'):
        return
    try:
        order_id = int(payload.split('_', 1)[1])
    except Exception:
        return

    user_id = str(msg.from_user.id)
    user_orders = data.get('orders', {}).get(user_id, [])
    order = next((o for o in user_orders if o.get('order_id') == order_id), None)
    if not order:
        # возможно заказ в другой структуре — пробуем искать по всему хранилищу
        for uid, orders in data.get('orders', {}).items():
            for o in orders:
                if o.get('invoice_payload') == payload:
                    order = o
                    user_id = uid
                    break
            if order:
                break

    if not order:
        return

    order['status'] = 'paid'
    order['paid_at'] = datetime.now().isoformat()
    save_data()

    # уведомляем администратора(ов)
    for admin_id in ADMINS:
        try:
            await bot.send_message(int(admin_id), f"✅ Заказ #{order_id} оплачен пользователем <a href='tg://user?id={user_id}'>Пользователь</a>", parse_mode='HTML')
        except Exception:
            pass

    # подтверждение пользователю
    try:
        await msg.answer("✅ Оплата получена. Спасибо! Ваш заказ в обработке.")
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())
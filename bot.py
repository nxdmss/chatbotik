#!/usr/bin/env python3
# coding: utf-8

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
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

# Импортируем наши новые модули
from models import (
    Product, CartItem, OrderCreate, Order, AdminNote, 
    DialogMessage, UserProfile, WebAppData, PaymentData, AdminAction
)
from logger_config import setup_logging, bot_logger
from error_handlers import (
    handle_errors, handle_webapp_errors, safe_send_message, 
    safe_send_photo, validate_user_input, validate_admin_access, 
    validate_order_data, ValidationError, SecurityError, BusinessLogicError
)
from database import db

from shop.catalog import PRODUCTS, get_product, format_price, add_product as catalog_add_product
from shop.cart import get_cart, cart_total

# ======================
# 🔹 Настройки и переменные
# ======================

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [x.strip() for x in os.getenv("ADMINS", "").split(",") if x.strip()]

# Мигрируем данные из JSON в базу данных при запуске
db.migrate_from_json()

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")

ADMINS = [str(x) for x in ADMINS]

# Настраиваем логирование
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
bot_logger.logger.info("Bot starting up", admins_count=len(ADMINS))

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
    "dialogs": {}
}

STATUSES = {"Новый": "new", "В работе": "work", "Завершён": "done"}
REVERSE_STATUSES = {v: k for k, v in STATUSES.items()}

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

def save_data() -> None:
    """Безопасное сохранение данных с обработкой ошибок"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        bot_logger.logger.debug("Data saved successfully")
    except Exception as e:
        bot_logger.log_error(e, {"action": "save_data"})
        raise

def load_data() -> None:
    """Безопасная загрузка данных с обработкой ошибок"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                data.update(loaded)
            bot_logger.logger.debug("Data loaded successfully")
    except Exception as e:
        bot_logger.log_error(e, {"action": "load_data"})
        # Создаем пустую структуру данных если файл поврежден
        data.update({
            "orders": {},
            "order_counter": 1,
            "user_states": {},
            "admin_note_state": {},
            "dialogs": {}
        })

load_data()

def save_admin_msgs(admin_id: str, msg_id: int) -> None:
    """Сохранение ID сообщений администратора"""
    try:
        msgs = {}
        if os.path.exists(ADMIN_MSGS_FILE):
            with open(ADMIN_MSGS_FILE, "r", encoding="utf-8") as f:
                msgs = json.load(f)
        msgs.setdefault(str(admin_id), []).append(msg_id)
        with open(ADMIN_MSGS_FILE, "w", encoding="utf-8") as f:
            json.dump(msgs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        bot_logger.log_error(e, {"action": "save_admin_msgs", "admin_id": admin_id})

def get_admin_msgs(admin_id: str) -> List[int]:
    """Получение ID сообщений администратора"""
    try:
        if not os.path.exists(ADMIN_MSGS_FILE):
            return []
        with open(ADMIN_MSGS_FILE, "r", encoding="utf-8") as f:
            msgs = json.load(f)
        return msgs.get(str(admin_id), [])
    except Exception as e:
        bot_logger.log_error(e, {"action": "get_admin_msgs", "admin_id": admin_id})
        return []

def clear_admin_msgs(admin_id: str) -> None:
    """Очистка ID сообщений администратора"""
    try:
        if not os.path.exists(ADMIN_MSGS_FILE):
            return
        with open(ADMIN_MSGS_FILE, "r", encoding="utf-8") as f:
            msgs = json.load(f)
        msgs[str(admin_id)] = []
        with open(ADMIN_MSGS_FILE, "w", encoding="utf-8") as f:
            json.dump(msgs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        bot_logger.log_error(e, {"action": "clear_admin_msgs", "admin_id": admin_id})

# ======================
# 🔹 Функции аутентификации и уведомлений
# ======================

@handle_errors
async def register_user(message: Message) -> bool:
    """Регистрирует пользователя в базе данных"""
    user = message.from_user
    return db.add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

@handle_errors
async def is_user_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    user = db.get_user(user_id)
    return user and user.get('is_admin', False)

@handle_errors
async def send_notification_to_admins(message_text: str, order_data: Dict = None):
    """Отправляет уведомление всем админам"""
    for admin_id in ADMINS:
        try:
            if order_data:
                text = f"🔔 **Новое уведомление**\n\n{message_text}\n\n"
                text += f"📦 **Детали заказа:**\n"
                text += f"💰 Сумма: {order_data.get('total_amount', 0)} ₽\n"
                text += f"👤 Пользователь: {order_data.get('user_name', 'Неизвестно')}\n"
                text += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            else:
                text = f"🔔 **Уведомление**\n\n{message_text}"
            
            await safe_send_message(bot, int(admin_id), text)
        except Exception as e:
            bot_logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")

@handle_errors
async def send_order_notification(order_id: int, user_id: int, status: str):
    """Отправляет уведомление о статусе заказа пользователю"""
    status_messages = {
        'paid': "✅ Ваш заказ оплачен! Мы начинаем сборку.",
        'shipped': "🚚 Ваш заказ отправлен! Отслеживайте доставку.",
        'delivered': "🎉 Заказ доставлен! Спасибо за покупку!",
        'cancelled': "❌ Заказ отменен. Обратитесь к поддержке."
    }
    
    message = status_messages.get(status, f"📦 Статус заказа #{order_id}: {status}")
    await safe_send_message(bot, user_id, message)

# ======================
# 🔹 Клавиатуры
# ======================

def main_kb() -> ReplyKeyboardMarkup:
    """Основная клавиатура для пользователей"""
    web_url = os.getenv('WEBAPP_URL') or os.getenv('REPL_URL') or os.getenv('REPL_SLUG')
    kb = []
    
    if web_url and isinstance(web_url, str) and web_url.startswith('http'):
        kb.append([KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=web_url))])
    else:
        kb.append([KeyboardButton(text="🛍 Открыть магазин")])
    
    kb.append([KeyboardButton(text="❓ FAQ"), KeyboardButton(text="💬 Связь с админом")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def admin_main_kb() -> ReplyKeyboardMarkup:
    """Основная клавиатура для администраторов"""
    web_url = os.getenv('WEBAPP_URL') or os.getenv('REPL_URL') or os.getenv('REPL_SLUG')
    kb = []
    
    kb.append([KeyboardButton(text="Админ-панель")])
    kb.append([KeyboardButton(text="📊 Статистика")])
    kb.append([KeyboardButton(text="🗑 Очистить чат")])
    kb.append([KeyboardButton(text="🛒 МАГАЗИН", web_app=WebAppInfo(url=web_url))])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_user_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Получение клавиатуры в зависимости от роли пользователя"""
    return admin_main_kb() if str(user_id) in ADMINS else main_kb()

def exit_dialog_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для выхода из диалога"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Выйти из диалога")]],
        resize_keyboard=True
    )

async def get_user_name(user_id: int) -> str:
    """Получение имени пользователя с обработкой ошибок"""
    try:
        chat = await bot.get_chat(int(user_id))
        return getattr(chat, "full_name", None) or getattr(chat, "username", None) or str(user_id)
    except Exception as e:
        bot_logger.log_error(e, {"user_id": user_id, "action": "get_user_name"})
        return str(user_id)

async def admin_clients_kb() -> InlineKeyboardMarkup:
    """Клавиатура со списком клиентов для администратора"""
    buttons = []
    try:
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
    except Exception as e:
        bot_logger.log_error(e, {"action": "admin_clients_kb"})
        buttons.append([InlineKeyboardButton(text="Ошибка загрузки", callback_data="none")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_client_orders_kb(user_id: str) -> InlineKeyboardMarkup:
    """Клавиатура с заказами клиента"""
    buttons = []
    try:
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
    except Exception as e:
        bot_logger.log_error(e, {"action": "admin_client_orders_kb", "user_id": user_id})
        buttons.append([InlineKeyboardButton(text="Ошибка загрузки", callback_data="none")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_order_full_kb(order: dict, user_id: str, order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления заказом"""
    kb = [
        [InlineKeyboardButton(text="📝 Добавить заметку", callback_data=f"note_{user_id}_{order_id}")]
    ] + [
        [InlineKeyboardButton(text=f"📌 {name}", callback_data=f"status_{user_id}_{order_id}_{code}")]
        for name, code in STATUSES.items()
    ]
    kb.append([InlineKeyboardButton(text="🗑 Удалить заказ", callback_data=f"delete_{user_id}_{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ======================
# 🔹 Пользовательские команды
# ======================

@dp.message(Command("start"))
@handle_errors
async def start(msg: Message):
    """Обработчик команды /start"""
    user_id = str(msg.chat.id)
    data["user_states"].pop(user_id, None)
    
    # Регистрируем пользователя в базе данных
    await register_user(msg)
    
    bot_logger.log_user_action(user_id, "start_command")
    
    if user_id in ADMINS:
        await msg.answer(f"👋 Привет, админ!", reply_markup=admin_main_kb())
        bot_logger.log_admin_action(user_id, "start_command")
    else:
        await msg.answer(f"👋 Привет, {msg.from_user.first_name}!", reply_markup=main_kb())

@dp.message(F.text == "Админ-панель")
@handle_errors
async def admin_panel_btn(msg: Message):
    """Обработчик кнопки админ-панели"""
    user_id = str(msg.chat.id)
    
    try:
        validate_admin_access(user_id, ADMINS)
    except SecurityError:
        await msg.answer("❌ Только для админов!")
        return
    
    kb = await admin_clients_kb()
    await msg.answer(
        "Выберите клиента для просмотра заказов и связи:",
        reply_markup=kb
    )
    bot_logger.log_admin_action(user_id, "open_admin_panel")

@dp.callback_query(lambda c: c.data.startswith("adminclient_"))
@handle_errors
async def admin_client_orders(c: CallbackQuery):
    """Обработчик выбора клиента администратором"""
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
    
    bot_logger.log_admin_action(str(c.from_user.id), "view_client_orders", user_id)

@dp.callback_query(lambda c: c.data.startswith("adminchat_"))
@handle_errors
async def admin_chat_with_client(c: CallbackQuery, state: FSMContext):
    """Обработчик начала диалога с клиентом"""
    user_id = c.data.split("_")[1]
    admin_id = str(c.from_user.id)
    
    try:
        validate_admin_access(admin_id, ADMINS)
    except SecurityError:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    
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
    
    bot_logger.log_admin_action(admin_id, "start_chat_with_client", user_id)

@dp.callback_query(lambda c: c.data == "adminback")
@handle_errors
async def admin_back_to_clients(c: CallbackQuery):
    """Обработчик возврата к списку клиентов"""
    kb = await admin_clients_kb()
    await c.message.edit_text(
        "Выберите клиента для просмотра заказов и связи:",
        reply_markup=kb
    )
    save_admin_msgs(c.from_user.id, c.message.message_id)
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith("adminorder_"))
@handle_errors
async def admin_order_info(c: CallbackQuery):
    """Обработчик просмотра информации о заказе"""
    _, user_id, order_id = c.data.split("_")
    order_id = int(order_id)
    
    try:
        validate_admin_access(str(c.from_user.id), ADMINS)
    except SecurityError:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    
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
    except Exception as e:
        bot_logger.log_error(e, {"action": "admin_order_info", "order_id": order_id})
        await c.answer("Ошибка отображения заказа", show_alert=True)
        return
    
    await c.answer()
    bot_logger.log_admin_action(str(c.from_user.id), "view_order", f"order_{order_id}")

@dp.callback_query(lambda c: c.data.startswith("note_"))
@handle_errors
async def admin_add_note_cb(c: CallbackQuery):
    """Обработчик добавления заметки к заказу"""
    try:
        validate_admin_access(str(c.from_user.id), ADMINS)
    except SecurityError:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    
    _, user_id, order_id = c.data.split("_")
    data["admin_note_state"][str(c.from_user.id)] = (user_id, int(order_id))
    await bot.send_message(c.from_user.id, "📝 Введите заметку по этому заказу. Она будет видна только администраторам.")
    await c.answer()
    
    bot_logger.log_admin_action(str(c.from_user.id), "add_note_request", f"order_{order_id}")

@dp.callback_query(lambda c: c.data.startswith("delete_"))
@handle_errors
async def admin_delete_order(c: CallbackQuery):
    """Обработчик удаления заказа"""
    try:
        validate_admin_access(str(c.from_user.id), ADMINS)
    except SecurityError:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    
    _, user_id, order_id = c.data.split("_")
    order_id = int(order_id)
    user_orders = data.get('orders', {}).get(user_id, [])
    idx = next((i for i,o in enumerate(user_orders) if o.get('order_id')==order_id), None)
    
    if idx is None:
        await c.answer('Заказ не найден', show_alert=True)
        return
    
    # Удаляем заказ
    removed = user_orders.pop(idx)
    data['orders'][user_id] = user_orders
    save_data()
    
    # Уведомляем заинтересованные стороны
    try:
        await safe_send_message(bot, int(user_id), f"🗑 Ваш заказ #{order_id} был удалён администрацией.")
    except Exception as e:
        bot_logger.log_error(e, {"action": "notify_user_order_deleted", "user_id": user_id})
    
    for admin_id in ADMINS:
        try:
            await safe_send_message(bot, int(admin_id), f"🗑 Заказ #{order_id} пользователя {user_id} удалён администратором {c.from_user.id}")
        except Exception as e:
            bot_logger.log_error(e, {"action": "notify_admin_order_deleted", "admin_id": admin_id})
    
    await c.answer('Заказ удалён', show_alert=True)
    bot_logger.log_admin_action(str(c.from_user.id), "delete_order", f"order_{order_id}")

@dp.callback_query(lambda c: c.data.startswith("status_"))
@handle_errors
async def change_order_status(c: CallbackQuery):
    """Обработчик изменения статуса заказа"""
    try:
        validate_admin_access(str(c.from_user.id), ADMINS)
    except SecurityError:
        await c.answer("❌ Только для админов!", show_alert=True)
        return
    
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
    
    old_status = order["status"]
    order["status"] = status_code
    save_data()
    
    await c.answer(f"Статус изменён на '{REVERSE_STATUSES[status_code]}'", show_alert=True)
    
    try:
        await admin_order_info(c)
    except Exception as e:
        bot_logger.log_error(e, {"action": "refresh_order_info"})
    
    bot_logger.log_order_status_changed(order_id, old_status, status_code, str(c.from_user.id))

@dp.message(F.text == "🗑 Очистить чат")
@handle_errors
async def admin_clear_chat(msg: Message, state: FSMContext):
    """Обработчик очистки чата администратора"""
    try:
        validate_admin_access(str(msg.chat.id), ADMINS)
    except SecurityError:
        await msg.answer("❌ Только для админов!")
        return
    
    msgs = get_admin_msgs(msg.chat.id)
    for mid in msgs:
        try:
            await bot.delete_message(msg.chat.id, mid)
        except Exception as e:
            bot_logger.log_error(e, {"action": "delete_admin_message", "message_id": mid})
    
    clear_admin_msgs(msg.chat.id)
    await state.clear()
    await msg.answer("✅ Чат и все окна очищены.", reply_markup=admin_main_kb())
    
    bot_logger.log_admin_action(str(msg.chat.id), "clear_chat")


@dp.message(F.text == "📊 Статистика")
@handle_errors
async def admin_statistics(msg: Message):
    """Обработчик статистики для админа"""
    user_id = str(msg.chat.id)
    
    try:
        validate_admin_access(user_id, ADMINS)
    except SecurityError:
        await msg.answer("❌ Только для админов!")
        return
    
    # Получаем статистику из базы данных
    try:
        products_count = len(db.get_products())
        orders = db.get_all_orders()
        orders_count = len(orders)
        total_revenue = sum(order['total_amount'] for order in orders)
        
        stats_text = f"""
📊 **Статистика магазина**

🛍 **Товары:** {products_count}
📦 **Заказы:** {orders_count}
💰 **Выручка:** {total_revenue:,.0f} ₽

📈 **Последние заказы:**
"""
        
        # Показываем последние 5 заказов
        for order in orders[:5]:
            stats_text += f"• #{order['id']} - {order['total_amount']:,.0f} ₽ ({order['status']})\n"
        
        await msg.answer(stats_text, reply_markup=admin_main_kb())
        bot_logger.log_admin_action(user_id, "view_statistics")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка получения статистики: {e}", reply_markup=admin_main_kb())
        bot_logger.log_error(e, {"action": "admin_statistics", "admin_id": user_id})

@dp.message(F.text == "❓ FAQ")
@handle_errors
async def faq(msg: Message):
    """Обработчик FAQ"""
    await msg.answer(
        "❓ <b>FAQ</b>\n\n"
        "📦 Как оформить заказ — нажмите '🛒 Сделать заказ' и опишите, что нужно.\n"
        "🚚 Доставка — мы свяжемся для уточнения.\n"
        "🔁 Возврат — в течение 14 дней.\n"
        "💬 Вопросы — просто напишите сообщение в чат!",
        reply_markup=get_user_kb(msg.chat.id)
    )
    
    bot_logger.log_user_action(str(msg.chat.id), "view_faq")

# ======================
# 🔹 WebApp обработчики
# ======================


@dp.message()
@handle_webapp_errors
async def handle_web_app_message(msg: Message):
    """Обработчик данных из WebApp"""
    wad = getattr(msg, 'web_app_data', None)
    if not wad:
        return
    
    try:
        payload = json.loads(wad.data)
    except Exception as e:
        bot_logger.log_error(e, {"action": "parse_webapp_data"})
        await msg.answer('⚠️ Неверный формат данных из Web App.')
        return

    # Валидируем данные с помощью Pydantic
    try:
        webapp_data = WebAppData(**payload)
    except ValidationError as e:
        bot_logger.log_error(e, {"action": "validate_webapp_data", "user_id": str(msg.from_user.id)})
        await msg.answer('⚠️ Некорректные данные из Web App.')
        return

    action = webapp_data.action
    user_id = str(msg.from_user.id)
    
    bot_logger.log_webapp_interaction(user_id, action, True)

    if action == 'add_product':
        # Админ добавляет новый товар через WebApp
        try:
            validate_admin_access(user_id, ADMINS)
        except SecurityError:
            await msg.answer('❌ Только администраторы могут добавлять товары.')
            return
        
        try:
            # Валидируем товар
            product = Product(**webapp_data.product.dict())
            created = catalog_add_product(product.dict())
            await msg.answer(f"✅ Товар '{created.get('title')}' добавлен с id {created.get('id')}")
            
            # Уведомляем других админов
            for admin_id in ADMINS:
                try:
                    await safe_send_message(
                        bot, int(admin_id), 
                        f"🆕 Админ добавил товар: <b>{created.get('title')}</b> (id: {created.get('id')})", 
                        parse_mode='HTML'
                    )
                except Exception as e:
                    bot_logger.log_error(e, {"action": "notify_admin_product_added", "admin_id": admin_id})
            
            bot_logger.log_admin_action(user_id, "add_product", created.get('id'))
        except ValidationError as e:
            await msg.answer(f'⚠️ Ошибка валидации товара: {e.message}')
        except Exception as e:
            bot_logger.log_error(e, {"action": "add_product", "user_id": user_id})
            await msg.answer('⚠️ Ошибка при добавлении товара.')
        return

    if action != 'checkout':
        await msg.answer('⚠️ Неподдерживаемое действие из Web App.')
        return

    # Обработка заказа
    try:
        # Валидируем данные заказа
        order_data = OrderCreate(
            text=f"Заказ из WebApp, {len(webapp_data.items)} позиций, сумма {webapp_data.total} ₽",
            items=webapp_data.items,
            total=webapp_data.total
        )
        
        # Server-side validation: пересчитываем сумму
        expected_total = 0
        for item in order_data.items:
            prod = get_product(item.product_id)
            if not prod:
                raise ValidationError(f"Товар {item.product_id} не найден")
            expected_total += prod['price'] * item.qty

        if expected_total != order_data.total:
            raise ValidationError("Сумма заказа не совпадает с серверной проверкой")

        # Создаем заказ
        order_id = data['order_counter']
        data['order_counter'] += 1
        
        order = Order(
            order_id=order_id,
            text=order_data.text,
            status='new',
            items=[item.dict() for item in order_data.items],
            total=expected_total,
            from_webapp=True
        )
        
        data.setdefault('orders', {}).setdefault(user_id, []).append(order.dict())
        save_data()

        # Уведомляем админов
        for admin_id in ADMINS:
            try:
                await safe_send_message(
                    bot, int(admin_id), 
                    f"🆕 Новый заказ #{order_id} (WebApp) от <a href='tg://user?id={user_id}'>Пользователя</a>\nСумма: {format_price(expected_total)}", 
                    parse_mode='HTML'
                )
            except Exception as e:
                bot_logger.log_error(e, {"action": "notify_admin_new_order", "admin_id": admin_id})

        await msg.answer(f"✅ Заказ #{order_id} создан. Администратор скоро свяжется для подтверждения.")
        bot_logger.log_order_created(order_id, user_id, expected_total, len(order_data.items))
        
    except ValidationError as e:
        await msg.answer(f'⚠️ Ошибка валидации заказа: {e.message}')
    except Exception as e:
        bot_logger.log_error(e, {"action": "process_webapp_order", "user_id": user_id})
        await msg.answer('⚠️ Ошибка при создании заказа.')

# ======================
# 🔹 Диалоги с администратором
# ======================

@dp.message(F.text == "💬 Связь с админом")
@handle_errors
async def client_start_chat(msg: Message, state: FSMContext):
    """Обработчик начала диалога с администратором"""
    await state.set_state(ContactAdmin.waiting_message)
    await msg.answer("✍️ Напишите сообщение для администратора. Для выхода нажмите '🔙 Выйти из диалога'.", reply_markup=exit_dialog_kb())
    
    bot_logger.log_user_action(str(msg.chat.id), "start_admin_chat")

@dp.message(ContactAdmin.waiting_message)
@handle_errors
async def client_chat_message(msg: Message, state: FSMContext):
    """Обработчик сообщений в диалоге с администратором"""
    user_id = str(msg.chat.id)
    
    if msg.text and msg.text.strip() and msg.text == "🔙 Выйти из диалога":
        await state.clear()
        await msg.answer("🚪 Вы вышли из диалога с админом.", reply_markup=get_user_kb(msg.chat.id))
        return
    
    # Валидируем сообщение
    try:
        if msg.text:
            validated_text = validate_user_input(msg.text, max_length=2000)
        else:
            validated_text = None
    except ValidationError as e:
        await msg.answer(f"❌ {e.message}")
        return
    
    dialogs = data.setdefault("dialogs", {}).setdefault(user_id, [])
    
    if msg.text and validated_text:
        dialogs.append({"from": "user", "text": validated_text})
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        dialogs.append({"from": "user", "text": "[Фото]", "photo_id": file_id})
    elif msg.document:
        file_id = msg.document.file_id
        dialogs.append({"from": "user", "text": "[Документ]", "file_id": file_id})
    else:
        await msg.answer("⚠️ Сообщение не может быть пустым.")
        return
    
    data["dialogs"][user_id] = dialogs[-100:]  # Ограничиваем историю
    save_data()
    
    user_name = await get_user_name(user_id)
    user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"
    
    # Отправляем сообщение всем админам
    for admin_id in ADMINS:
        try:
            if msg.text:
                await safe_send_message(
                    bot, int(admin_id), 
                    f"💬 Сообщение от клиента {user_link}:\n{validated_text}"
                )
            elif msg.photo:
                file_id = msg.photo[-1].file_id
                await safe_send_photo(
                    bot, int(admin_id), file_id, 
                    caption=f"💬 Сообщение от клиента {user_link}: [Фото]"
                )
            elif msg.document:
                file_id = msg.document.file_id
                await bot.send_document(
                    int(admin_id), file_id, 
                    caption=f"💬 Сообщение от клиента {user_link}: [Документ]"
                )
        except Exception as e:
            bot_logger.log_error(e, {"action": "send_message_to_admin", "admin_id": admin_id})
    
    await msg.answer("✅ Сообщение отправлено администратору.", reply_markup=exit_dialog_kb())
    bot_logger.log_user_action(user_id, "send_message_to_admin")

@dp.message(AdminDialog.chatting)
@handle_errors
async def admin_to_user(msg: Message, state: FSMContext):
    """Обработчик сообщений администратора клиенту"""
    admin_id = str(msg.chat.id)
    data_state = await state.get_data()
    user_id = data_state.get("user_id")
    
    if not user_id:
        await msg.answer("❌ Информация о диалоге не найдена.", reply_markup=get_user_kb(msg.chat.id))
        await state.clear()
        return
    
    if msg.text and msg.text.strip() and msg.text == "🔙 Выйти из диалога":
        await state.clear()
        await msg.answer("🚪 Вы вышли из диалога.", reply_markup=get_user_kb(msg.chat.id))
        return
    
    # Валидируем сообщение
    try:
        if msg.text:
            validated_text = validate_user_input(msg.text, max_length=2000)
        else:
            validated_text = None
    except ValidationError as e:
        await msg.answer(f"❌ {e.message}")
        return
    
    if not validated_text and not msg.photo and not msg.document:
        await msg.answer("⚠️ Сообщение не может быть пустым.")
        return
    
    dialogs = data.setdefault("dialogs", {}).setdefault(user_id, [])
    
    if msg.text and validated_text:
        dialogs.append({"from": "admin", "text": validated_text})
    elif msg.photo:
        file_id = msg.photo[-1].file_id
        dialogs.append({"from": "admin", "text": "[Фото]", "photo_id": file_id})
    elif msg.document:
        file_id = msg.document.file_id
        dialogs.append({"from": "admin", "text": "[Документ]", "file_id": file_id})
    
    data["dialogs"][user_id] = dialogs[-100:]  # Ограничиваем историю
    save_data()
    
    try:
        if msg.text and validated_text:
            await safe_send_message(
                bot, int(user_id), 
                f"💬 Сообщение от администратора:\n{validated_text}", 
                reply_markup=get_user_kb(user_id)
            )
            await msg.answer("✅ Сообщение отправлено клиенту.", reply_markup=exit_dialog_kb())
        elif msg.photo:
            file_id = msg.photo[-1].file_id
            await safe_send_photo(
                bot, int(user_id), file_id, 
                caption="💬 Сообщение от администратора:", 
                reply_markup=get_user_kb(user_id)
            )
            await msg.answer("✅ Фото отправлено клиенту.", reply_markup=exit_dialog_kb())
        elif msg.document:
            file_id = msg.document.file_id
            await bot.send_document(
                int(user_id), file_id, 
                caption="💬 Сообщение от администратора:", 
                reply_markup=get_user_kb(user_id)
            )
            await msg.answer("✅ Документ отправлен клиенту.", reply_markup=exit_dialog_kb())
    except Exception as e:
        bot_logger.log_error(e, {"action": "send_message_to_user", "user_id": user_id})
        await msg.answer("⚠️ Не удалось доставить сообщение клиенту.", reply_markup=exit_dialog_kb())
    
    bot_logger.log_admin_action(admin_id, "send_message_to_user", user_id)

@dp.message(F.text == "🔙 Выйти из диалога")
@handle_errors
async def exit_dialog(msg: Message, state: FSMContext):
    """Обработчик выхода из диалога"""
    current_state = await state.get_state()
    if current_state == AdminDialog.chatting.state or current_state == ContactAdmin.waiting_message.state:
        await state.clear()
        await msg.answer("🚪 Вы вышли из диалога.", reply_markup=get_user_kb(msg.chat.id))
        return

    await msg.answer("ℹ️ Вы не находитесь в диалоге.", reply_markup=get_user_kb(msg.chat.id))

@dp.message(lambda m: str(m.chat.id) in data.get("admin_note_state", {}))
@handle_errors
async def admin_receive_note(msg: Message):
    """Обработчик получения заметки от администратора"""
    admin_id = str(msg.chat.id)
    
    try:
        validate_admin_access(admin_id, ADMINS)
    except SecurityError:
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
    
    # Валидируем заметку
    try:
        validated_text = validate_user_input(msg.text, max_length=1000)
    except ValidationError as e:
        await msg.answer(f"❌ {e.message}")
        return
    
    note = AdminNote(
        admin_id=admin_id,
        text=validated_text
    )
    
    order.setdefault("admin_notes", []).append(note.dict())
    order["admin_notes"] = order["admin_notes"][-100:]  # Ограничиваем количество заметок
    save_data()
    
    await msg.answer("✅ Заметка сохранена (видна только админам).", reply_markup=get_user_kb(msg.chat.id))
    bot_logger.log_admin_action(admin_id, "add_note", f"order_{order_id}")

# ======================
# 🔹 Telegram Payments
# ======================

@dp.pre_checkout_query()
@handle_errors
async def handle_pre_checkout(pre: PreCheckoutQuery):
    """Обработчик pre-checkout запроса"""
    try:
        await bot.answer_pre_checkout_query(pre.id, ok=True)
        bot_logger.logger.info("Pre-checkout approved", query_id=pre.id)
    except Exception as e:
        bot_logger.log_error(e, {"action": "pre_checkout", "query_id": pre.id})
        try:
            await bot.answer_pre_checkout_query(pre.id, ok=False, error_message="Ошибка обработки платежа")
        except Exception:
            pass

@dp.message()
@handle_errors
async def handle_successful_payment(msg: Message):
    """Обработчик успешного платежа"""
    if not getattr(msg, 'successful_payment', None):
        return
    
    payload = msg.successful_payment.invoice_payload
    if not payload or not payload.startswith('order_'):
        return
    
    try:
        order_id = int(payload.split('_', 1)[1])
    except (ValueError, IndexError):
        bot_logger.log_error(Exception("Invalid payload format"), {"payload": payload})
        return

    user_id = str(msg.from_user.id)
    user_orders = data.get('orders', {}).get(user_id, [])
    order = next((o for o in user_orders if o.get('order_id') == order_id), None)
    
    if not order:
        # Ищем заказ по всему хранилищу
        for uid, orders in data.get('orders', {}).items():
            for o in orders:
                if o.get('invoice_payload') == payload:
                    order = o
                    user_id = uid
                    break
            if order:
                break

    if not order:
        bot_logger.log_error(Exception("Order not found"), {"order_id": order_id, "payload": payload})
        return

    order['status'] = 'paid'
    order['paid_at'] = datetime.now().isoformat()
    save_data()

    # Уведомляем администраторов
    for admin_id in ADMINS:
        try:
            await safe_send_message(
                bot, int(admin_id), 
                f"✅ Заказ #{order_id} оплачен пользователем <a href='tg://user?id={user_id}'>Пользователь</a>", 
                parse_mode='HTML'
            )
        except Exception as e:
            bot_logger.log_error(e, {"action": "notify_admin_payment", "admin_id": admin_id})

    # Подтверждение пользователю
    try:
        await msg.answer("✅ Оплата получена. Спасибо! Ваш заказ в обработке.")
    except Exception as e:
        bot_logger.log_error(e, {"action": "confirm_payment_to_user", "user_id": user_id})
    
    bot_logger.log_payment_received(order_id, user_id, order.get('total', 0))

# ======================
# 🔹 Запуск
# ======================

async def main():
    """Основная функция запуска бота"""
    try:
        bot_logger.logger.info("Bot starting up", version="2.0", features=["validation", "logging", "error_handling"])
        print("🤖 Улучшенный бот запущен на aiogram 3.x с валидацией, логированием и обработкой ошибок!")
        await dp.start_polling(bot)
    except Exception as e:
        bot_logger.log_error(e, {"action": "main_startup"})
        raise

if __name__ == "__main__":
    asyncio.run(main())

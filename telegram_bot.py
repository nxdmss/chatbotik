#!/usr/bin/env python3
"""
🤖 PROFESSIONAL TELEGRAM BOT
============================
Современный Telegram бот для электронной коммерции
с интеграцией веб-приложения
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
import requests

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000')
DATABASE_PATH = "shop.db"

# Загрузка ID администраторов
def load_admin_ids():
    """Загрузка ID администраторов из файла или переменных окружения"""
    admin_ids = []
    
    # Сначала пытаемся загрузить из переменных окружения
    admin_ids_env = os.getenv('ADMIN_IDS', '')
    if admin_ids_env:
        try:
            admin_ids = [int(x.strip()) for x in admin_ids_env.split(',') if x.strip()]
        except ValueError:
            pass
    
    # Если не нашли, пытаемся загрузить из файла
    if not admin_ids:
        admins_file = Path(__file__).parent / 'webapp' / 'admins.json'
        if admins_file.exists():
            try:
                with open(admins_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    admin_ids = [int(x) for x in data.get('admins', [])]
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Ошибка загрузки admins.json: {e}")
    
    # По умолчанию используем ваш ID
    if not admin_ids:
        admin_ids = [1593426947]
    
    print(f"👑 Администраторы: {admin_ids}")
    return admin_ids

ADMIN_IDS = load_admin_ids()

class TelegramBot:
    def __init__(self):
        self.application = None
        self.webapp_url = WEBAPP_URL
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=self.webapp_url))],
            [InlineKeyboardButton("📦 Каталог товаров", callback_data='catalog')],
            [InlineKeyboardButton("🛒 Корзина", callback_data='cart')],
            [InlineKeyboardButton("📞 Связаться с нами", callback_data='contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в наш интернет-магазин! 

🛍️ **У нас вы найдете:**
• Электронику и гаджеты
• Одежду и аксессуары  
• Книги и многое другое

✨ **Особенности:**
• Быстрая доставка
• Гарантия качества
• Поддержка 24/7

Нажмите кнопку ниже, чтобы открыть магазин!
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🆘 **Справка по командам:**

/start - Главное меню
/help - Эта справка
/catalog - Посмотреть каталог товаров
/orders - История ваших заказов
/contact - Связаться с поддержкой

🛍️ **Как сделать заказ:**
1. Нажмите "Открыть магазин"
2. Выберите товары
3. Добавьте в корзину
4. Оформите заказ

❓ **Нужна помощь?**
Обращайтесь к нашей службе поддержки!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def catalog_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /catalog"""
        try:
            # Получаем товары из API
            response = requests.get(f"{self.webapp_url}/api/products")
            if response.status_code == 200:
                products = response.json()
                
                if not products:
                    await update.message.reply_text("📦 Каталог пока пуст. Зайдите позже!")
                    return
                
                # Показываем первые 5 товаров
                catalog_text = "🛍️ **Каталог товаров:**\n\n"
                
                for i, product in enumerate(products[:5]):
                    price = f"{product['price']:,} ₽".replace(',', ' ')
                    catalog_text += f"{i+1}. **{product['title']}**\n"
                    catalog_text += f"   💰 {price}\n"
                    if product.get('description'):
                        catalog_text += f"   📝 {product['description'][:50]}...\n"
                    catalog_text += "\n"
                
                if len(products) > 5:
                    catalog_text += f"... и еще {len(products) - 5} товаров\n\n"
                
                catalog_text += "Нажмите кнопку ниже, чтобы открыть полный каталог!"
                
                keyboard = [
                    [InlineKeyboardButton("🛍️ Открыть полный каталог", web_app=WebAppInfo(url=self.webapp_url))]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    catalog_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Ошибка загрузки каталога. Попробуйте позже.")
                
        except Exception as e:
            print(f"Error in catalog_command: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /orders"""
        user_id = update.effective_user.id
        
        try:
            # Получаем заказы пользователя из базы данных
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, total_amount, status, created_at 
                FROM orders 
                WHERE customer_phone = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (str(user_id),))
            
            orders = cursor.fetchall()
            conn.close()
            
            if not orders:
                keyboard = [
                    [InlineKeyboardButton("🛍️ Сделать первый заказ", web_app=WebAppInfo(url=self.webapp_url))]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "📦 У вас пока нет заказов.\n\nСделайте первый заказ в нашем магазине!",
                    reply_markup=reply_markup
                )
                return
            
            orders_text = "📋 **Ваши заказы:**\n\n"
            
            for order in orders:
                order_id, total, status, created_at = order
                date_str = datetime.fromisoformat(created_at).strftime("%d.%m.%Y %H:%M")
                status_emoji = {"pending": "⏳", "processing": "🔄", "shipped": "🚚", "delivered": "✅"}.get(status, "❓")
                
                orders_text += f"🆔 **Заказ #{order_id}**\n"
                orders_text += f"💰 {total:,} ₽\n".replace(',', ' ')
                orders_text += f"{status_emoji} {status.title()}\n"
                orders_text += f"📅 {date_str}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🛍️ Новый заказ", web_app=WebAppInfo(url=self.webapp_url))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                orders_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            print(f"Error in orders_command: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /contact"""
        contact_text = """
📞 **Связаться с нами:**

🕐 **Время работы:** 9:00 - 21:00 (МСК)

📱 **Телефон:** +7 (999) 123-45-67
📧 **Email:** support@eshoppro.ru
💬 **Telegram:** @eshoppro_support

🏢 **Адрес:**
г. Москва, ул. Примерная, д. 123

❓ **Частые вопросы:**
• Доставка по всей России
• Оплата картой или наличными
• Возврат в течение 14 дней
• Гарантия на все товары

Напишите нам, и мы обязательно поможем!
        """
        
        keyboard = [
            [InlineKeyboardButton("💬 Написать в поддержку", url="https://t.me/eshoppro_support")],
            [InlineKeyboardButton("🛍️ Вернуться в магазин", web_app=WebAppInfo(url=self.webapp_url))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            contact_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'catalog':
            await self.catalog_command(update, context)
        elif query.data == 'cart':
            keyboard = [
                [InlineKeyboardButton("🛍️ Открыть корзину", web_app=WebAppInfo(url=self.webapp_url))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🛒 **Ваша корзина**\n\nДля управления корзиной откройте веб-приложение:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif query.data == 'contact':
            await self.contact_command(update, context)

    async def web_app_data_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик данных от WebApp"""
        if update.message and update.message.web_app_data:
            try:
                data = json.loads(update.message.web_app_data.data)
                print(f"📦 Received WebApp data: {data}")
                
                user = update.effective_user
                user_info = f"👤 {user.first_name}"
                if user.last_name:
                    user_info += f" {user.last_name}"
                if user.username:
                    user_info += f" (@{user.username})"
                user_info += f"\n🆔 ID: {user.id}"
                
                # Обрабатываем заказ
                if data.get('action') == 'order':
                    items = data.get('items', [])
                    total = data.get('total', 0)
                    
                    # Формируем сообщение о заказе
                    order_message = f"🛒 **НОВЫЙ ЗАКАЗ**\n\n"
                    order_message += f"{user_info}\n\n"
                    order_message += f"📋 **Товары:**\n"
                    
                    # Получаем информацию о товарах
                    try:
                        response = requests.get(f"{self.webapp_url}/api/products", timeout=5)
                        if response.status_code == 200:
                            products = {p['id']: p for p in response.json()}
                            
                            for i, item in enumerate(items, 1):
                                product_id = item.get('productId')
                                quantity = item.get('quantity', 1)
                                size = item.get('size')
                                
                                product = products.get(product_id)
                                if product:
                                    order_message += f"{i}. **{product['title']}**\n"
                                    order_message += f"   Количество: {quantity}\n"
                                    if size:
                                        order_message += f"   Размер: {size}\n"
                                    price = product.get('price', 0)
                                    item_total = price * quantity
                                    order_message += f"   Сумма: {item_total:,} ₽\n".replace(',', ' ')
                                    order_message += "\n"
                                else:
                                    order_message += f"{i}. Товар ID: {product_id} (кол-во: {quantity})\n\n"
                        else:
                            # Если не удалось получить товары, просто показываем ID
                            for i, item in enumerate(items, 1):
                                order_message += f"{i}. Товар ID: {item.get('productId')} (кол-во: {item.get('quantity', 1)})\n"
                            order_message += "\n"
                    except Exception as e:
                        print(f"⚠️ Ошибка загрузки товаров: {e}")
                        # Показываем базовую информацию
                        for i, item in enumerate(items, 1):
                            order_message += f"{i}. Товар ID: {item.get('productId')} (кол-во: {item.get('quantity', 1)})\n"
                        order_message += "\n"
                    
                    order_message += f"💰 **Итого: {total:,} ₽**\n".replace(',', ' ')
                    order_message += f"\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                    
                    # Отправляем уведомление администраторам
                    sent_to_admins = 0
                    for admin_id in ADMIN_IDS:
                        try:
                            await context.bot.send_message(
                                chat_id=admin_id,
                                text=order_message,
                                parse_mode=ParseMode.MARKDOWN
                            )
                            sent_to_admins += 1
                            print(f"✅ Заказ отправлен администратору {admin_id}")
                        except Exception as e:
                            print(f"❌ Ошибка отправки администратору {admin_id}: {e}")
                    
                    # Отправляем подтверждение пользователю
                    if sent_to_admins > 0:
                        await update.message.reply_text(
                            "✅ **Заказ успешно оформлен!**\n\n"
                            "Ваш заказ получен и передан администратору.\n"
                            "Мы свяжемся с вами в ближайшее время!\n\n"
                            "Спасибо за покупку! 🛍️",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_to_message_id=update.message.message_id
                        )
                        print(f"✅ Заказ обработан, отправлено {sent_to_admins} администраторам")
                    else:
                        await update.message.reply_text(
                            "⚠️ **Заказ получен, но возникла проблема с уведомлением администратора.**\n\n"
                            "Мы исправим это в ближайшее время. Ваш заказ не потерян!",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_to_message_id=update.message.message_id
                        )
                        print("⚠️ Не удалось отправить заказ ни одному администратору")
                else:
                    # Другие типы данных
                    await update.message.reply_text(
                        "✅ Данные получены! Спасибо за использование нашего магазина!",
                        reply_to_message_id=update.message.message_id
                    )
                    
                    # Отправляем данные администраторам
                    data_message = f"📨 **Данные от пользователя**\n\n{user_info}\n\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"
                    for admin_id in ADMIN_IDS:
                        try:
                            await context.bot.send_message(
                                chat_id=admin_id,
                                text=data_message,
                                parse_mode=ParseMode.MARKDOWN
                            )
                        except Exception as e:
                            print(f"❌ Ошибка отправки данных администратору {admin_id}: {e}")
                
            except Exception as e:
                print(f"❌ Error processing WebApp data: {e}")
                import traceback
                traceback.print_exc()
                
                await update.message.reply_text(
                    "❌ Произошла ошибка при обработке данных.\n"
                    "Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.",
                    reply_to_message_id=update.message.message_id
                )

    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("catalog", self.catalog_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        
        # Кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # WebApp данные
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_data_handler))

    async def run(self):
        """Запуск бота"""
        if not BOT_TOKEN:
            print("❌ BOT_TOKEN не найден! Установите переменную окружения BOT_TOKEN")
            return
        
        print("🤖 ЗАПУСК TELEGRAM BOT")
        print("=" * 30)
        print(f"🌐 WebApp URL: {self.webapp_url}")
        print(f"📱 Bot Token: {BOT_TOKEN[:10]}...")
        print("=" * 30)
        
        # Создаем приложение
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Настраиваем обработчики
        self.setup_handlers()
        
        # Запускаем бота
        print("✅ Бот запущен и готов к работе!")
        await self.application.run_polling()

async def main():
    """Главная функция"""
    bot = TelegramBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())

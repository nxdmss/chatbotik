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

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
import requests

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000')
DATABASE_PATH = "shop.db"

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
                print(f"Received WebApp data: {data}")
                
                # Здесь можно обработать данные от веб-приложения
                await update.message.reply_text(
                    "✅ Данные получены! Спасибо за использование нашего магазина!",
                    reply_to_message_id=update.message.message_id
                )
            except Exception as e:
                print(f"Error processing WebApp data: {e}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при обработке данных.",
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

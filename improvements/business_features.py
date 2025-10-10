# Дополнительные функции для улучшения бизнеса

class BusinessFeatures:
    """
    РЕКОМЕНДУЕМЫЕ НОВЫЕ ФУНКЦИИ:
    """
    
    # 1. СИСТЕМА СКИДОК И ПРОМОКОДОВ
    def apply_discount(self, cart_total: float, promo_code: str = None) -> float:
        """
        Промокоды: WELCOME10, BULK20, NEWUSER
        Автоскидки: при сумме >10000₽ - 5%, >20000₽ - 10%
        """
        pass
    
    # 2. УВЕДОМЛЕНИЯ О СТАТУСЕ ЗАКАЗА
    def send_order_status_notification(self, user_id: str, order_id: int, new_status: str):
        """
        Автоматические уведомления:
        - Заказ принят
        - Заказ собран
        - Заказ отправлен
        - Заказ доставлен
        """
        pass
    
    # 3. СИСТЕМА ОТЗЫВОВ
    def request_review(self, user_id: str, order_id: int):
        """
        После доставки запрашивать отзыв с рейтингом 1-5
        Сохранять отзывы к товарам
        """
        pass
    
    # 4. АНАЛИТИКА ПРОДАЖ
    def generate_sales_report(self, start_date, end_date):
        """
        - Топ товаров
        - Выручка по дням
        - Конверсия в покупку
        - Среднний чек
        """
        pass
    
    # 5. УПРАВЛЕНИЕ ЗАПАСАМИ
    def track_inventory(self, product_id: str, size: str, quantity_sold: int):
        """
        - Остатки товаров
        - Уведомления о низких остатках
        - Автоматическое скрытие распроданных товаров
        """
        pass
    
    # 6. СИСТЕМА ЛОЯЛЬНОСТИ
    def calculate_loyalty_points(self, user_id: str, order_total: float):
        """
        - Начисление баллов за покупки
        - Статусы клиентов (Bronze, Silver, Gold)
        - Специальные предложения для VIP
        """
        pass

# КОНКРЕТНЫЕ УЛУЧШЕНИЯ ДЛЯ ВАШЕГО КОДА:

# bot.py - Добавить после создания заказа:
async def send_order_confirmation(user_id: str, order: dict):
    """Подтверждение заказа с деталями"""
    text = f"""
✅ <b>Заказ #{order['order_id']} принят!</b>

📦 Товары:
{format_order_items(order['items'])}

💰 <b>Итого: {format_price(order['total'])}</b>

⏰ Статус: Новый
📞 Мы свяжемся с вами в течение часа для подтверждения.

Отследить заказ: /order_{order['order_id']}
"""
    await bot.send_message(user_id, text)

# webapp/app.js - Добавить в корзину:
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Показывать toast при добавлении в корзину
cart[key].qty += qty;
showToast(`${prod.title} добавлен в корзину!`);

# server.py - Добавить endpoint для аналитики:
@app.get('/admin/analytics')
async def analytics_endpoint(request: Request):
    if not is_admin_request(request):
        raise HTTPException(403)
    
    # Собрать статистику из orders.json
    return {
        'total_orders': len(orders),
        'total_revenue': sum(o['total'] for o in orders),
        'top_products': get_top_selling_products(),
        'daily_sales': get_daily_sales_chart()
    }
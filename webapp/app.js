// ===== МОБИЛЬНОЕ ПРИЛОЖЕНИЕ МАГАЗИНА =====

class MobileShopApp {
  constructor() {
    this.PRODUCTS = [];
    this.cart = this.loadCart();
    this.currentPage = 'catalog';
    this.userInfo = null;
    this.isAdmin = false;
    
    this.CART_KEY = 'mobile_shop_cart_v2';
    this.ORDERS_KEY = 'mobile_shop_orders_v1';
    
    this.init();
  }

  // ===== ИНИЦИАЛИЗАЦИЯ =====
  
  async init() {
    try {
      // Настройка Telegram WebApp
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        this.userInfo = window.Telegram.WebApp.initDataUnsafe?.user;
      }
      
      // Загрузка данных
      await this.fetchProducts();
      await this.checkAdminStatus();
      
      // Настройка интерфейса
      this.setupEventListeners();
      this.renderCurrentPage();
      this.updateCartBadge();
      
      console.log('✅ Приложение инициализировано');
    } catch (error) {
      console.error('❌ Ошибка инициализации:', error);
    }
  }

  // ===== ЗАГРУЗКА ДАННЫХ =====
  
  async fetchProducts() {
    try {
      const response = await fetch('/webapp/products.json');
      if (response.ok) {
        this.PRODUCTS = await response.json();
      } else {
        throw new Error('Не удалось загрузить товары');
      }
    } catch (error) {
      console.warn('Используем тестовые товары:', error);
      this.PRODUCTS = [
        {id:'p1', title:'Кроссовки Sprint', price:4990, sizes:[38,39,40,41], photo:''},
        {id:'p2', title:'Кеды Classic', price:3490, sizes:[36,37,38,39,40], photo:''},
        {id:'p3', title:'Ботинки Trail', price:7990, sizes:[40,41,42,43], photo:''}
      ];
    }
  }

  async checkAdminStatus() {
    try {
      // Проверяем URL параметр
      if (new URLSearchParams(window.location.search).get('admin') === '1') {
        this.isAdmin = true;
        return;
      }
      
      // Проверяем через API
      const response = await fetch('/webapp/admins.json');
      if (response.ok) {
        const admins = await response.json();
        const userId = this.userInfo?.id || this.userInfo?.user_id;
        this.isAdmin = userId && admins.includes(String(userId));
      }
    } catch (error) {
      console.warn('Не удалось проверить статус администратора:', error);
      this.isAdmin = false;
    }
  }

  // ===== КОРЗИНА =====
  
  loadCart() {
    try {
      return JSON.parse(localStorage.getItem(this.CART_KEY) || '{}');
    } catch (error) {
      console.warn('Ошибка загрузки корзины:', error);
      return {};
    }
  }

  saveCart() {
    try {
      localStorage.setItem(this.CART_KEY, JSON.stringify(this.cart));
    } catch (error) {
      console.warn('Ошибка сохранения корзины:', error);
    }
  }

  addToCart(productId, size, quantity = 1) {
    const product = this.PRODUCTS.find(p => p.id === productId);
    if (!product) return;

    const key = `${productId}::${size}`;
    if (!this.cart[key]) {
      this.cart[key] = {
        id: productId,
        title: product.title,
        price: product.price,
        size: size,
        qty: 0
      };
    }
    
    this.cart[key].qty += quantity;
    this.saveCart();
    this.updateCartBadge();
    
    // Показываем уведомление
    this.showNotification(`${product.title} добавлен в корзину`);
  }

  removeFromCart(key) {
    delete this.cart[key];
    this.saveCart();
    this.updateCartBadge();
  }

  clearCart() {
    this.cart = {};
    this.saveCart();
    this.updateCartBadge();
    this.renderCartPage();
  }

  getCartTotal() {
    return Object.values(this.cart).reduce((total, item) => total + (item.price * item.qty), 0);
  }

  getCartItemsCount() {
    return Object.values(this.cart).reduce((count, item) => count + item.qty, 0);
  }

  // ===== НАВИГАЦИЯ =====
  
  showPage(pageName) {
    // Скрываем все страницы
    document.querySelectorAll('.page').forEach(page => {
      page.classList.remove('active');
    });
    
    // Показываем нужную страницу
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
      targetPage.classList.add('active');
      this.currentPage = pageName;
    }
    
    // Обновляем навигацию
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    
    const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
    if (activeNavItem) {
      activeNavItem.classList.add('active');
    }
    
    // Рендерим страницу
    this.renderCurrentPage();
  }

  renderCurrentPage() {
    switch (this.currentPage) {
      case 'catalog':
        this.renderCatalogPage();
        break;
      case 'cart':
        this.renderCartPage();
        break;
      case 'profile':
        this.renderProfilePage();
        break;
    }
  }

  // ===== СТРАНИЦА КАТАЛОГА =====
  
  renderCatalogPage() {
    const productsEl = document.getElementById('products');
    if (!productsEl) return;

    const searchQuery = document.getElementById('search')?.value?.toLowerCase() || '';
    
    const filteredProducts = this.PRODUCTS.filter(product => {
      if (product.deleted) return false;
      if (!searchQuery) return true;
      return product.title.toLowerCase().includes(searchQuery);
    });

    productsEl.innerHTML = filteredProducts.map(product => this.renderProductCard(product)).join('');
    
    // Добавляем обработчики событий
    this.setupProductEventListeners();
  }

  renderProductCard(product) {
    const photoSrc = product.photo || 
      'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width=400 height=300><rect width=400 height=300 fill=%23eeeeee/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill=%23999>Нет фото</text></svg>';
    
    return `
      <div class="product-card" data-product-id="${product.id}">
        <img src="${photoSrc}" alt="${product.title}" class="product-image">
        <div class="product-title">${product.title}</div>
        <div class="product-price">${this.formatPrice(product.price)}</div>
        <div class="product-controls">
          <select class="size-select" data-product-id="${product.id}">
            ${product.sizes.map(size => `<option value="${size}">Размер ${size}</option>`).join('')}
        </select>
          <div class="qty-controls">
            <button class="qty-btn qty-decrease" data-product-id="${product.id}">-</button>
            <div class="qty-display" data-product-id="${product.id}">1</div>
            <button class="qty-btn qty-increase" data-product-id="${product.id}">+</button>
          </div>
        </div>
        <div class="product-actions">
          <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
            🛒 Добавить
          </button>
          <button class="btn btn-success quick-buy" data-product-id="${product.id}">
            ⚡ Купить
          </button>
          ${this.isAdmin ? `<button class="btn btn-danger btn-sm delete-product" data-product-id="${product.id}">🗑 Удалить</button>` : ''}
        </div>
      </div>
    `;
  }

  setupProductEventListeners() {
    // Кнопки количества
    document.querySelectorAll('.qty-increase, .qty-decrease').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const productId = e.target.dataset.productId;
        const qtyEl = document.querySelector(`[data-product-id="${productId}"].qty-display`);
        let qty = parseInt(qtyEl.textContent);
        
        if (e.target.classList.contains('qty-increase')) {
          qty = Math.min(qty + 1, 99);
        } else {
          qty = Math.max(qty - 1, 1);
        }
        
        qtyEl.textContent = qty;
      });
    });

    // Добавить в корзину
    document.querySelectorAll('.add-to-cart').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const productId = e.target.dataset.productId;
        const sizeSelect = document.querySelector(`[data-product-id="${productId}"].size-select`);
        const qtyEl = document.querySelector(`[data-product-id="${productId}"].qty-display`);
        
        const size = parseInt(sizeSelect.value);
        const qty = parseInt(qtyEl.textContent);
        
        this.addToCart(productId, size, qty);
        qtyEl.textContent = '1'; // Сбрасываем количество
      });
    });

    // Быстрая покупка
    document.querySelectorAll('.quick-buy').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const productId = e.target.dataset.productId;
        const sizeSelect = document.querySelector(`[data-product-id="${productId}"].size-select`);
        const qtyEl = document.querySelector(`[data-product-id="${productId}"].qty-display`);
        
        const size = parseInt(sizeSelect.value);
        const qty = parseInt(qtyEl.textContent);
        
        this.addToCart(productId, size, qty);
        this.showPage('cart');
        qtyEl.textContent = '1';
      });
    });

    // Удаление товара (админ)
    if (this.isAdmin) {
      document.querySelectorAll('.delete-product').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const productId = e.target.dataset.productId;
          this.deleteProduct(productId);
        });
      });
    }
  }

  // ===== СТРАНИЦА КОРЗИНЫ =====
  
  renderCartPage() {
    const cartListEl = document.getElementById('cart-list');
    const totalEl = document.getElementById('total');
    
    if (!cartListEl || !totalEl) return;

    const cartItems = Object.entries(this.cart);
    
    if (cartItems.length === 0) {
      cartListEl.innerHTML = `
        <div class="text-center" style="padding: 40px 20px; color: var(--text-light);">
          <div style="font-size: 48px; margin-bottom: 16px;">🛒</div>
          <h3>Корзина пуста</h3>
          <p>Добавьте товары из каталога</p>
        </div>
      `;
      totalEl.textContent = '0 ₽';
      return;
    }

    cartListEl.innerHTML = cartItems.map(([key, item]) => `
      <div class="cart-item" data-key="${key}">
        <div class="cart-item-info">
          <div class="cart-item-title">${item.title}</div>
          <div class="cart-item-details">Размер ${item.size} × ${item.qty}</div>
        </div>
        <div class="cart-item-price">${this.formatPrice(item.price * item.qty)}</div>
        <button class="btn btn-danger" onclick="app.removeFromCart('${key}')" style="padding: 8px; margin-left: 8px;">×</button>
      </div>
    `).join('');

    totalEl.textContent = this.formatPrice(this.getCartTotal());
  }

  // ===== СТРАНИЦА ПРОФИЛЯ =====
  
  renderProfilePage() {
    this.updateUserInfo();
    this.updateProfileStats();
  }

  updateUserInfo() {
    const userNameEl = document.getElementById('user-name');
    const userIdEl = document.getElementById('user-id');
    
    if (userNameEl) {
      const name = this.userInfo?.first_name || 'Пользователь';
      const lastName = this.userInfo?.last_name || '';
      userNameEl.textContent = `${name} ${lastName}`.trim();
    }
    
    if (userIdEl) {
      const userId = this.userInfo?.id || this.userInfo?.user_id || 'Неизвестно';
      userIdEl.textContent = `ID: ${userId}`;
    }
  }

  updateProfileStats() {
    const orders = this.loadOrders();
    const totalOrders = orders.length;
    const completedOrders = orders.filter(order => order.status === 'done').length;
    const totalSpent = orders.reduce((sum, order) => sum + (order.total || 0), 0);

    const totalOrdersEl = document.getElementById('total-orders');
    const completedOrdersEl = document.getElementById('completed-orders');
    const totalSpentEl = document.getElementById('total-spent');

    if (totalOrdersEl) totalOrdersEl.textContent = totalOrders;
    if (completedOrdersEl) completedOrdersEl.textContent = completedOrders;
    if (totalSpentEl) totalSpentEl.textContent = this.formatPrice(totalSpent);
  }

  loadOrders() {
    try {
      return JSON.parse(localStorage.getItem(this.ORDERS_KEY) || '[]');
    } catch (error) {
      console.warn('Ошибка загрузки заказов:', error);
      return [];
    }
  }

  saveOrder(order) {
    try {
      const orders = this.loadOrders();
      orders.push(order);
      localStorage.setItem(this.ORDERS_KEY, JSON.stringify(orders));
    } catch (error) {
      console.warn('Ошибка сохранения заказа:', error);
    }
  }

  // ===== ОФОРМЛЕНИЕ ЗАКАЗА =====
  
  async checkout() {
    const items = Object.values(this.cart);
    if (items.length === 0) {
      this.showNotification('Корзина пуста', 'warning');
    return;
    }

    const total = this.getCartTotal();
    const order = {
      id: Date.now(),
      items: items,
      total: total,
      status: 'new',
      created_at: new Date().toISOString(),
      from_webapp: true
    };

    // Сохраняем заказ локально
    this.saveOrder(order);

    // Отправляем заказ на сервер
    try {
      const response = await fetch('/webapp/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: this.userInfo?.id || 0,
          products: items,
          total_amount: total
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Заказ создан на сервере:', result);
      }
    } catch (error) {
      console.error('❌ Ошибка создания заказа на сервере:', error);
    }

    // Отправляем в бота
    const payload = {
      action: 'checkout',
      items: items.map(item => ({
        id: item.id,
        qty: item.qty,
        size: item.size
      })),
      total: total
    };

    try {
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify(payload));
        this.showNotification('Заказ отправлен!', 'success');
        this.clearCart();
        this.showPage('profile');
      } else {
        throw new Error('Не в Telegram');
      }
    } catch (error) {
      console.error('Ошибка отправки заказа:', error);
      this.showNotification('Ошибка отправки заказа', 'error');
    }
  }

  // ===== МОДАЛЬНЫЕ ОКНА =====
  
  showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      this.renderModalContent(modalId);
    }
  }

  hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  }

  renderModalContent(modalId) {
    switch (modalId) {
      case 'orders-modal':
        this.renderOrdersModal();
        break;
      case 'faq-modal':
        // FAQ уже в HTML
        break;
    }
  }

  renderOrdersModal() {
    const ordersListEl = document.getElementById('orders-list');
    if (!ordersListEl) return;

    const orders = this.loadOrders();
    
    if (orders.length === 0) {
      ordersListEl.innerHTML = `
        <div class="text-center" style="padding: 20px; color: var(--text-light);">
          <div style="font-size: 48px; margin-bottom: 16px;">📋</div>
          <h3>Нет заказов</h3>
          <p>Ваши заказы появятся здесь</p>
        </div>
      `;
      return;
    }

    ordersListEl.innerHTML = orders.map(order => `
      <div class="order-item">
        <div class="order-header">
          <div class="order-id">Заказ #${order.id}</div>
          <div class="order-status ${order.status}">${this.getStatusText(order.status)}</div>
        </div>
        <div class="order-details">
          ${order.items.length} товаров на сумму ${this.formatPrice(order.total)}
        </div>
        <div class="order-total">
          ${new Date(order.created_at).toLocaleDateString('ru-RU')}
        </div>
      </div>
    `).join('');
  }

  getStatusText(status) {
    const statusMap = {
      'new': 'Новый',
      'work': 'В работе',
      'done': 'Завершён',
      'paid': 'Оплачен'
    };
    return statusMap[status] || status;
  }

  // ===== АДМИН ФУНКЦИИ =====
  
  async deleteProduct(productId) {
    if (!this.isAdmin) return;
    
    if (!confirm('Удалить товар из каталога?')) return;

    try {
      const response = await fetch('/webapp/delete_product?admin=1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: productId })
      });

      if (response.ok) {
        this.showNotification('Товар удалён', 'success');
        this.renderCatalogPage();
      } else {
        throw new Error('Ошибка удаления');
      }
    } catch (error) {
      console.error('Ошибка удаления товара:', error);
      this.showNotification('Ошибка удаления товара', 'error');
    }
  }

  // ===== УТИЛИТЫ =====
  
  formatPrice(price) {
    return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ₽';
  }

  updateCartBadge() {
    const badge = document.getElementById('cart-badge');
    const count = this.getCartItemsCount();
    
    if (badge) {
      if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'block';
      } else {
        badge.style.display = 'none';
      }
    }
  }

  showNotification(message, type = 'info') {
    // Простое уведомление
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--accent)'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 10000;
      font-weight: 600;
      box-shadow: var(--shadow-lg);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  // ===== ОБРАБОТЧИКИ СОБЫТИЙ =====
  
  setupEventListeners() {
    // Навигация
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        const page = e.currentTarget.dataset.page;
        this.showPage(page);
      });
    });

    // Поиск
    const searchInput = document.getElementById('search');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        this.renderCatalogPage();
      });
    }

    // Очистка корзины
    const clearCartBtn = document.getElementById('clear-cart');
    if (clearCartBtn) {
      clearCartBtn.addEventListener('click', () => {
        if (confirm('Очистить корзину?')) {
          this.clearCart();
        }
      });
    }

    // Оформление заказа
    const checkoutBtn = document.getElementById('checkout');
    if (checkoutBtn) {
      checkoutBtn.addEventListener('click', () => {
        this.checkout();
      });
    }

    // Модальные окна
    document.getElementById('my-orders-btn')?.addEventListener('click', () => {
      this.showModal('orders-modal');
    });

    document.getElementById('faq-btn')?.addEventListener('click', () => {
      this.showModal('faq-modal');
    });

    document.getElementById('contact-admin-btn')?.addEventListener('click', () => {
      this.contactAdmin();
    });

    // Закрытие модальных окон
    document.querySelectorAll('.modal-close').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const modal = e.target.closest('.modal');
        if (modal) {
          this.hideModal(modal.id);
        }
      });
    });

    // Закрытие по клику вне модального окна
    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.hideModal(modal.id);
        }
      });
    });
  }

  contactAdmin() {
    if (window.Telegram && window.Telegram.WebApp) {
      // Отправляем сообщение в бота
      const payload = {
        action: 'contact_admin',
        message: 'Пользователь хочет связаться с администратором'
      };
      
      try {
      window.Telegram.WebApp.sendData(JSON.stringify(payload));
        this.showNotification('Сообщение отправлено администратору', 'success');
      } catch (error) {
        console.error('Ошибка отправки сообщения:', error);
        this.showNotification('Ошибка отправки сообщения', 'error');
    }
  } else {
      this.showNotification('Откройте приложение в Telegram', 'warning');
    }
  }
}

// ===== ЗАПУСК ПРИЛОЖЕНИЯ =====

let app;

document.addEventListener('DOMContentLoaded', () => {
  app = new MobileShopApp();
});

// Экспортируем для глобального доступа
window.app = app;

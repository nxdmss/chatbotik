// ===== МОБИЛЬНОЕ ПРИЛОЖЕНИЕ МАГАЗИНА =====

class MobileShopApp {
  constructor() {
    this.PRODUCTS = [];
    this.cart = this.loadCart();
    this.currentPage = 'catalog';
    this.userInfo = null;
    this.isAdmin = false;
    this.editingProduct = null;
    
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
      console.log('Загружаем товары...');
      const response = await fetch('/webapp/products.json');
      if (response.ok) {
        this.PRODUCTS = await response.json();
        console.log('✅ Товары загружены:', this.PRODUCTS.length, 'шт.');
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
      console.log('✅ Тестовые товары загружены:', this.PRODUCTS.length, 'шт.');
    }
  }

  async checkAdminStatus() {
    try {
      // Проверяем URL параметр
      if (new URLSearchParams(window.location.search).get('admin') === '1') {
        this.isAdmin = true;
        console.log('Admin status: true (URL parameter)');
        this.showAdminPanel();
        return;
      }
      
      // Проверяем через API
      const response = await fetch('/webapp/admins.json');
      if (response.ok) {
        const data = await response.json();
        const admins = data.admins || data;
        const userId = this.userInfo?.id || this.userInfo?.user_id;
        this.isAdmin = userId && admins.includes(String(userId));
        console.log('Admin status:', this.isAdmin, 'User ID:', userId, 'Admins:', admins);
        
        if (this.isAdmin) {
          this.showAdminPanel();
        }
      }
    } catch (error) {
      console.warn('Не удалось проверить статус администратора:', error);
      this.isAdmin = false;
    }
  }

  showAdminPanel() {
    // Показываем кнопку админ-панели в навигации
    const adminNavBtn = document.getElementById('admin-nav-btn');
    if (adminNavBtn) {
      adminNavBtn.style.display = 'block';
    }
    
    // Показываем кнопку добавления товара в каталоге
    const adminActions = document.getElementById('admin-actions');
    if (adminActions) {
      adminActions.style.display = 'block';
    }
  }

  // ===== АДМИНСКИЕ ФУНКЦИИ =====
  
  async addProduct(productData) {
    try {
      const response = await fetch('/webapp/admin/add-product', {
        method: 'POST',
        body: productData
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Товар добавлен:', result);
        this.showNotification('Товар успешно добавлен!', 'success');
        await this.fetchProducts(); // Обновляем список товаров
        this.renderCurrentPage(); // Перерисовываем страницу
        return true;
      } else {
        throw new Error('Ошибка добавления товара');
      }
    } catch (error) {
      console.error('❌ Ошибка добавления товара:', error);
      this.showNotification('Ошибка добавления товара', 'error');
      return false;
    }
  }

  async deleteProduct(productId) {
    try {
      const response = await fetch(`/webapp/admin/delete-product/${productId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        console.log('✅ Товар удален');
        this.showNotification('Товар удален!', 'success');
        await this.fetchProducts(); // Обновляем список товаров
        this.renderCurrentPage(); // Перерисовываем страницу
        return true;
      } else {
        throw new Error('Ошибка удаления товара');
      }
    } catch (error) {
      console.error('❌ Ошибка удаления товара:', error);
      this.showNotification('Ошибка удаления товара', 'error');
      return false;
    }
  }

  showAddProductModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h3>➕ Добавить товар</h3>
          <button class="close-btn" onclick="this.closest('.modal').remove()">×</button>
        </div>
        <div class="modal-body">
          <form id="add-product-form">
            <div class="form-group">
              <label>Название товара:</label>
              <input type="text" id="product-title" required>
            </div>
            <div class="form-group">
              <label>Цена (₽):</label>
              <input type="number" id="product-price" required min="0" step="0.01">
            </div>
            <div class="form-group">
              <label>Размеры (через запятую):</label>
              <input type="text" id="product-sizes" placeholder="S,M,L" required>
            </div>
            <div class="form-group">
              <label>Описание:</label>
              <textarea id="product-description" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>Фото:</label>
              <input type="file" id="product-photo" accept="image/*">
            </div>
            <div class="form-actions">
              <button type="button" class="btn btn-outline" onclick="this.closest('.modal').remove()">Отмена</button>
              <button type="submit" class="btn btn-primary">Добавить товар</button>
            </div>
          </form>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Обработчик формы
    document.getElementById('add-product-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData();
      formData.append('title', document.getElementById('product-title').value);
      formData.append('price', document.getElementById('product-price').value);
      formData.append('sizes', document.getElementById('product-sizes').value);
      formData.append('description', document.getElementById('product-description').value);
      
      const photoFile = document.getElementById('product-photo').files[0];
      if (photoFile) {
        formData.append('photo', photoFile);
      }
      
      const success = await this.addProduct(formData);
      if (success) {
        modal.remove();
      }
    });
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
      case 'admin':
        this.renderAdminPage();
        break;
    }
  }

  // ===== СТРАНИЦА АДМИН-ПАНЕЛИ =====
  
  renderAdminPage() {
    if (!this.isAdmin) {
      this.showNotification('Доступ запрещен', 'error');
      this.showPage('catalog');
      return;
    }
    
    this.loadAdminProducts();
  }

  // ===== СТРАНИЦА КАТАЛОГА =====
  
  renderCatalogPage() {
    const productsEl = document.getElementById('products');
    if (!productsEl) return;

    console.log('Рендерим каталог. Товаров:', this.PRODUCTS.length, 'Админ:', this.isAdmin);

    const searchQuery = document.getElementById('search')?.value?.toLowerCase() || '';
    
    const filteredProducts = this.PRODUCTS.filter(product => {
      if (product.deleted) return false;
      if (!searchQuery) return true;
      return product.title.toLowerCase().includes(searchQuery);
    });

    console.log('Отфильтрованных товаров:', filteredProducts.length);

    // Добавляем кнопку "Добавить товар" для админов
    let adminButton = '';
    if (this.isAdmin) {
      adminButton = `
        <div class="admin-actions" style="margin-bottom: 20px; text-align: center;">
          <button class="btn btn-success" onclick="window.mobileShopApp.showAddProductModal()">
            ➕ Добавить товар
          </button>
        </div>
      `;
      console.log('Кнопка админа добавлена');
    }

    productsEl.innerHTML = adminButton + filteredProducts.map(product => this.renderProductCard(product)).join('');
    
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

    // Админ-панель
    this.setupAdminEventListeners();

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

  // ===== АДМИН-ПАНЕЛЬ =====

  async loadAdminProducts() {
    try {
      const response = await fetch('/webapp/admin/products');
      if (response.ok) {
        const products = await response.json();
        this.renderAdminProducts(products);
        this.updateAdminStats(products);
      } else {
        throw new Error('Не удалось загрузить товары');
      }
    } catch (error) {
      console.error('Ошибка загрузки товаров для админа:', error);
      this.showNotification('Ошибка загрузки товаров', 'error');
    }
  }

  renderAdminProducts(products) {
    const container = document.getElementById('admin-products-list');
    if (!container) return;

    container.innerHTML = products.map(product => `
      <div class="admin-product-item" data-product-id="${product.id}">
        <img src="${product.photo || '/webapp/static/uploads/no-image.jpg'}" 
             alt="${product.title}" class="admin-product-image">
        <div class="admin-product-info">
          <div class="admin-product-title">${product.title}</div>
          <div class="admin-product-price">${this.formatPrice(product.price)}</div>
          <div class="admin-product-status">
            ${product.is_active ? '✅ Активен' : '❌ Неактивен'}
          </div>
        </div>
        <div class="admin-product-actions">
          <button class="btn btn-primary btn-sm" onclick="window.mobileShopApp.editProduct(${product.id})">
            ✏️
          </button>
          <button class="btn btn-danger btn-sm" onclick="window.mobileShopApp.deleteProduct(${product.id})">
            🗑️
          </button>
        </div>
      </div>
    `).join('');
  }

  updateAdminStats(products) {
    const activeProducts = products.filter(p => p.is_active).length;
    document.getElementById('admin-products-count').textContent = activeProducts;
    
    // Здесь можно добавить загрузку статистики заказов
    document.getElementById('admin-orders-count').textContent = '0';
    document.getElementById('admin-revenue').textContent = '0 ₽';
  }

  showAddProductModal() {
    this.editingProduct = null;
    document.getElementById('product-modal-title').textContent = '➕ Добавить товар';
    document.getElementById('product-form').reset();
    document.getElementById('photo-preview').innerHTML = '';
    this.showModal('product-modal');
  }

  editProduct(productId) {
    const product = this.PRODUCTS.find(p => p.id == productId);
    if (!product) return;

    this.editingProduct = product;
    document.getElementById('product-modal-title').textContent = '✏️ Редактировать товар';
    
    // Заполняем форму
    document.getElementById('product-title').value = product.title;
    document.getElementById('product-description').value = product.description || '';
    document.getElementById('product-price').value = product.price;
    document.getElementById('product-sizes').value = product.sizes.join(', ');
    
    // Показываем текущее фото
    if (product.photo) {
      document.getElementById('photo-preview').innerHTML = `
        <img src="${product.photo}" alt="Текущее фото" style="max-width: 100px; max-height: 100px; border-radius: 8px;">
      `;
    }
    
    this.showModal('product-modal');
  }

  async deleteProduct(productId) {
    if (!confirm('Вы уверены, что хотите удалить этот товар?')) return;

    try {
      const response = await fetch(`/webapp/admin/products/${productId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        this.showNotification('Товар удален', 'success');
        this.loadAdminProducts(); // Перезагружаем список
        this.fetchProducts(); // Обновляем основной каталог
      } else {
        throw new Error('Ошибка удаления товара');
      }
    } catch (error) {
      console.error('Ошибка удаления товара:', error);
      this.showNotification('Ошибка удаления товара', 'error');
    }
  }

  async saveProduct(formData) {
    try {
      const url = this.editingProduct 
        ? `/webapp/admin/products/${this.editingProduct.id}`
        : '/webapp/admin/products';
      
      const method = this.editingProduct ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        body: formData
      });

      if (response.ok) {
        const action = this.editingProduct ? 'обновлен' : 'добавлен';
        this.showNotification(`Товар ${action}`, 'success');
        this.hideModal('product-modal');
        this.loadAdminProducts(); // Перезагружаем список
        this.fetchProducts(); // Обновляем основной каталог
      } else {
        throw new Error('Ошибка сохранения товара');
      }
    } catch (error) {
      console.error('Ошибка сохранения товара:', error);
      this.showNotification('Ошибка сохранения товара', 'error');
    }
  }

  setupAdminEventListeners() {
    // Кнопка добавления товара
    document.getElementById('add-product-btn')?.addEventListener('click', () => {
      this.showAddProductModal();
    });

    // Форма товара
    document.getElementById('product-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      this.saveProduct(formData);
    });

    // Кнопка отмены
    document.getElementById('cancel-product')?.addEventListener('click', () => {
      this.hideModal('product-modal');
    });

    // Предварительный просмотр фото
    document.getElementById('product-photo')?.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          document.getElementById('photo-preview').innerHTML = `
            <img src="${e.target.result}" alt="Предварительный просмотр" style="max-width: 100px; max-height: 100px; border-radius: 8px;">
          `;
        };
        reader.readAsDataURL(file);
      }
    });
  }
}

// ===== ЗАПУСК ПРИЛОЖЕНИЯ =====

let app;

document.addEventListener('DOMContentLoaded', () => {
  app = new MobileShopApp();
  // Экспортируем для глобального доступа
  window.mobileShopApp = app;
});

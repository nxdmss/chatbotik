/**
 * Чистое приложение для Telegram WebApp магазина
 */

class MobileShopApp {
    constructor() {
        this.products = [];
        this.cart = [];
        this.isAdmin = false;
        this.currentPage = 'catalog';
        this.editingProduct = null;
        
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Инициализация приложения...');
            
            // Настройка Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
                this.userInfo = window.Telegram.WebApp.initDataUnsafe?.user;
            }
            
            // Загрузка данных
            await this.fetchProducts();
            await this.checkAdminStatus();
            this.loadCart();
            
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
            const data = await response.json();
            this.products = data.products || [];
            console.log('📦 Загружено товаров:', this.products.length);
        } catch (error) {
            console.error('❌ Ошибка загрузки товаров:', error);
            this.products = [];
        }
    }

    async checkAdminStatus() {
        try {
            // Проверяем по URL параметру
            const urlParams = new URLSearchParams(window.location.search);
            const isAdminParam = urlParams.get('admin') === 'true';
            
            // Проверяем через API
            const response = await fetch('/webapp/admins.json');
            const data = await response.json();
            const adminIds = data.admins || [];
            
            // Проверяем ID пользователя
            let userId = null;
            if (this.userInfo && this.userInfo.id) {
                userId = this.userInfo.id.toString();
            }
            
            // Проверяем, является ли пользователь админом
            this.isAdmin = isAdminParam || (userId && adminIds.includes(userId));
            
            // Дополнительная проверка для вашего ID
            if (userId === '1593426947') {
                this.isAdmin = true;
                console.log('👑 Главный администратор обнаружен');
            }
            
            if (this.isAdmin) {
                this.showAdminPanel();
                console.log('👑 Пользователь является администратором, ID:', userId);
            } else {
                console.log('👤 Обычный пользователь, ID:', userId);
            }
        } catch (error) {
            console.warn('Не удалось проверить статус администратора:', error);
            this.isAdmin = false;
        }
    }

    showAdminPanel() {
        console.log('Показываем админ-панель...');
        
        // Показываем кнопку админ-панели в навигации
        const adminNavBtn = document.getElementById('admin-nav-btn');
        if (adminNavBtn) {
            adminNavBtn.style.display = 'block';
            console.log('Кнопка админ-панели показана');
    } else {
            console.error('Кнопка админ-панели не найдена!');
        }
        
        // Показываем кнопку добавления товара в каталоге
        const adminActions = document.getElementById('admin-actions');
        if (adminActions) {
            adminActions.style.display = 'block';
            console.log('Кнопка добавления товара показана');
      } else {
            console.error('Кнопка добавления товара не найдена!');
        }
    }

    // ===== НАВИГАЦИЯ =====

    showPage(page) {
        console.log('Переход на страницу:', page);
        
        // Скрываем все страницы
        document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
        
        // Показываем выбранную страницу
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.style.display = 'block';
        }
        
        // Обновляем навигацию
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.page === page) {
                btn.classList.add('active');
            }
        });
        
        this.currentPage = page;
        
        // Рендерим содержимое страницы
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

    // ===== КАТАЛОГ =====

    renderCatalogPage() {
        const container = document.getElementById('products-grid');
        if (!container) return;
        
        const searchTerm = document.getElementById('search')?.value.toLowerCase() || '';
        const filteredProducts = this.products.filter(product => 
            product.title.toLowerCase().includes(searchTerm) ||
            product.description.toLowerCase().includes(searchTerm)
        );
        
        container.innerHTML = filteredProducts.map(product => this.renderProductCard(product)).join('');
        
        // Настраиваем обработчики событий для товаров
        this.setupProductEventListeners();
    }

    renderProductCard(product) {
        return `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image">
                    <img src="${product.photo}" alt="${product.title}" onerror="this.src='/webapp/static/uploads/default.jpg'">
                </div>
                <div class="product-info">
                    <h3 class="product-title">${product.title}</h3>
                    <p class="product-description">${product.description}</p>
                    <div class="product-price">${this.formatPrice(product.price)}</div>
                    
                    ${product.sizes && product.sizes.length > 0 ? `
                        <select class="size-select" data-product-id="${product.id}">
                            <option value="">Выберите размер</option>
                            ${product.sizes.map(size => `<option value="${size}">${size}</option>`).join('')}
        </select>
                    ` : ''}
                    
                    <div class="qty-controls">
                        <button class="qty-btn qty-decrease" data-product-id="${product.id}">-</button>
                        <span class="qty-display" data-product-id="${product.id}">0</span>
                        <button class="qty-btn qty-increase" data-product-id="${product.id}">+</button>
                    </div>
                    
                    <div class="product-actions">
                        <button class="btn btn-primary add-to-cart" data-product-id="${product.id}">
                            🛒 В корзину
                        </button>
                        <button class="btn btn-outline quick-buy" data-product-id="${product.id}">
                            ⚡ Быстрая покупка
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ===== КОРЗИНА =====

    renderCartPage() {
        const container = document.getElementById('cart-items');
        const totalElement = document.getElementById('cart-total');
        
        if (!container || !totalElement) return;
        
        if (this.cart.length === 0) {
            container.innerHTML = '<p class="empty-cart">Корзина пуста</p>';
            totalElement.textContent = '0 ₽';
            return;
        }
        
        container.innerHTML = this.cart.map(item => this.renderCartItem(item)).join('');
        totalElement.textContent = this.formatPrice(this.getCartTotal());
        
        // Настраиваем обработчики событий для корзины
        this.setupCartEventListeners();
    }

    renderCartItem(item) {
        const product = this.products.find(p => p.id === item.productId);
        if (!product) return '';
        
        return `
            <div class="cart-item" data-product-id="${item.productId}">
                <div class="cart-item-image">
                    <img src="${product.photo}" alt="${product.title}">
                </div>
                <div class="cart-item-info">
                    <h4>${product.title}</h4>
                    <p>Размер: ${item.size || 'Не указан'}</p>
                    <div class="cart-item-price">${this.formatPrice(product.price * item.quantity)}</div>
                </div>
                <div class="cart-item-controls">
                    <button class="qty-btn qty-decrease" data-product-id="${item.productId}">-</button>
                    <span class="qty-display">${item.quantity}</span>
                    <button class="qty-btn qty-increase" data-product-id="${item.productId}">+</button>
                    <button class="btn btn-danger btn-sm remove-item" data-product-id="${item.productId}">🗑️</button>
                </div>
            </div>
        `;
    }

    // ===== ПРОФИЛЬ =====

    renderProfilePage() {
        // Профиль пока простой, можно расширить
        console.log('Рендерим профиль');
    }

    // ===== АДМИН-ПАНЕЛЬ =====

    async renderAdminPage() {
        if (!this.isAdmin) return;
        
        try {
            await this.loadAdminProducts();
            this.updateAdminStats();
        } catch (error) {
            console.error('Ошибка загрузки админ-панели:', error);
        }
    }

    async loadAdminProducts() {
        try {
            const response = await fetch('/webapp/admin/products?user_id=admin');
            const data = await response.json();
            this.adminProducts = data.products || [];
            this.renderAdminProducts(this.adminProducts);
        } catch (error) {
            console.error('Ошибка загрузки товаров для админа:', error);
        }
    }

    renderAdminProducts(products) {
        const container = document.getElementById('admin-products-list');
        if (!container) return;
        
        container.innerHTML = products.map(product => this.renderAdminProductItem(product)).join('');
    }

    renderAdminProductItem(product) {
        return `
            <div class="admin-product-item" data-product-id="${product.id}">
                <div class="admin-product-image">
                    <img src="${product.photo}" alt="${product.title}">
                </div>
                <div class="admin-product-info">
                    <h4>${product.title}</h4>
                    <p>${product.description}</p>
                    <div class="admin-product-price">${this.formatPrice(product.price)}</div>
                    <div class="admin-product-status ${product.is_active ? 'active' : 'inactive'}">
                        ${product.is_active ? 'Активен' : 'Неактивен'}
        </div>
      </div>
                <div class="admin-product-actions">
                    <button class="btn btn-primary btn-sm" onclick="editProduct(${product.id})">
                        ✏️ Редактировать
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id})">
                        🗑️ Удалить
                    </button>
                </div>
      </div>
    `;
    }

    updateAdminStats() {
        const productsCount = document.getElementById('products-count');
        const ordersCount = document.getElementById('orders-count');
        
        if (productsCount) {
            productsCount.textContent = this.products.length;
        }
        
        if (ordersCount) {
            ordersCount.textContent = '0'; // Пока заглушка
        }
    }

    // ===== КОРЗИНА - ЛОГИКА =====

    addToCart(productId, size = null) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;
        
        const existingItem = this.cart.find(item => 
            item.productId === productId && item.size === size
        );
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                productId: productId,
                quantity: 1,
                size: size
            });
        }
        
        this.updateCartBadge();
        this.saveCart();
        
        if (this.currentPage === 'cart') {
            this.renderCartPage();
        }
        
        console.log('Товар добавлен в корзину:', product.title);
    }

    removeFromCart(productId, size = null) {
        const itemIndex = this.cart.findIndex(item => 
            item.productId === productId && item.size === size
        );
        
        if (itemIndex !== -1) {
            this.cart.splice(itemIndex, 1);
            this.updateCartBadge();
            this.saveCart();
            
            if (this.currentPage === 'cart') {
                this.renderCartPage();
            }
        }
    }

    updateQuantity(productId, size = null, quantity) {
        const item = this.cart.find(item => 
            item.productId === productId && item.size === size
        );
        
        if (item) {
            if (quantity <= 0) {
                this.removeFromCart(productId, size);
            } else {
                item.quantity = quantity;
                this.updateCartBadge();
                this.saveCart();
                
                if (this.currentPage === 'cart') {
                    this.renderCartPage();
                }
            }
        }
    }

    getCartTotal() {
        return this.cart.reduce((total, item) => {
            const product = this.products.find(p => p.id === item.productId);
            return total + (product ? product.price * item.quantity : 0);
        }, 0);
    }

    clearCart() {
        this.cart = [];
        this.updateCartBadge();
        this.saveCart();
        this.renderCartPage();
    }

    updateCartBadge() {
        const badge = document.getElementById('cart-badge');
        if (badge) {
            const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
            if (totalItems > 0) {
                badge.textContent = totalItems;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    // ===== ОФОРМЛЕНИЕ ЗАКАЗА =====

    async checkout() {
        if (this.cart.length === 0) {
            alert('Корзина пуста');
    return;
  }
        
        try {
            const orderData = {
                action: 'order',
                items: this.cart,
                total: this.getCartTotal()
            };
            
            // Отправляем данные в бот
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.sendData(JSON.stringify(orderData));
            } else {
                // Для тестирования в браузере
                console.log('Данные заказа:', orderData);
                alert('Заказ отправлен! (тестовый режим)');
            }
            
            // Очищаем корзину
            this.clearCart();
            
        } catch (error) {
            console.error('Ошибка оформления заказа:', error);
            alert('Ошибка при оформлении заказа');
        }
    }

    // ===== АДМИН-ФУНКЦИИ =====

    showAddProductModal() {
        if (!this.isAdmin) return;
        
        this.editingProduct = null;
        document.getElementById('product-modal-title').textContent = '➕ Добавить товар';
        document.getElementById('product-form').reset();
        document.getElementById('photo-preview').style.display = 'none';
        this.showModal('product-modal');
    }

    async editProduct(productId) {
        if (!this.isAdmin) return;
        
        const product = this.products.find(p => p.id === productId);
        if (!product) return;
        
        this.editingProduct = product;
        document.getElementById('product-modal-title').textContent = '✏️ Редактировать товар';
        
        // Заполняем форму
        document.getElementById('product-title').value = product.title;
        document.getElementById('product-description').value = product.description;
        document.getElementById('product-price').value = product.price;
        document.getElementById('product-sizes').value = product.sizes ? product.sizes.join(', ') : '';
        
        this.showModal('product-modal');
    }

    async deleteProduct(productId) {
        if (!this.isAdmin) return;
        
        if (!confirm('Удалить товар?')) return;
        
        try {
            const response = await fetch(`/webapp/admin/products/${productId}?user_id=admin`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await this.fetchProducts();
                await this.loadAdminProducts();
                this.updateAdminStats();
            } else {
                alert('Ошибка при удалении товара');
            }
        } catch (error) {
            console.error('Ошибка удаления товара:', error);
            alert('Ошибка при удалении товара');
        }
    }

    async saveProduct(formData) {
        try {
            const url = this.editingProduct 
                ? `/webapp/admin/products/${this.editingProduct.id}?user_id=admin`
                : '/webapp/admin/products?user_id=admin';
            
            const method = this.editingProduct ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                body: formData
            });
            
            if (response.ok) {
                await this.fetchProducts();
                await this.loadAdminProducts();
                this.updateAdminStats();
                this.hideModal('product-modal');
            } else {
                alert('Ошибка при сохранении товара');
            }
        } catch (error) {
            console.error('Ошибка сохранения товара:', error);
            alert('Ошибка при сохранении товара');
        }
    }

    // ===== МОДАЛЬНЫЕ ОКНА =====

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    contactAdmin() {
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.openTelegramLink('https://t.me/your_bot_username');
        } else {
            alert('Свяжитесь с нами через Telegram: @your_bot_username');
        }
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

        // Форма товара
        const productForm = document.getElementById('product-form');
        if (productForm) {
            productForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                this.saveProduct(formData);
            });
        }

        // Предварительный просмотр фото
        const photoInput = document.getElementById('product-photo');
        if (photoInput) {
            photoInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const preview = document.getElementById('photo-preview');
                        const img = document.getElementById('preview-img');
                        img.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

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

    setupProductEventListeners() {
        // Кнопки количества
        document.querySelectorAll('.qty-increase, .qty-decrease').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                const isIncrease = e.target.classList.contains('qty-increase');
                const qtyEl = document.querySelector(`[data-product-id="${productId}"].qty-display`);
                
                if (qtyEl) {
                    let quantity = parseInt(qtyEl.textContent) || 0;
                    quantity += isIncrease ? 1 : -1;
                    quantity = Math.max(0, quantity);
                    qtyEl.textContent = quantity;
                }
            });
        });

        // Добавить в корзину
        document.querySelectorAll('.add-to-cart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                const sizeSelect = document.querySelector(`[data-product-id="${productId}"].size-select`);
                const size = sizeSelect ? sizeSelect.value : null;
                
                if (sizeSelect && !size) {
                    alert('Выберите размер');
                    return;
                }
                
                this.addToCart(productId, size);
            });
        });

        // Быстрая покупка
        document.querySelectorAll('.quick-buy').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                const sizeSelect = document.querySelector(`[data-product-id="${productId}"].size-select`);
                const size = sizeSelect ? sizeSelect.value : null;
                
                if (sizeSelect && !size) {
                    alert('Выберите размер');
                    return;
                }
                
                this.addToCart(productId, size);
                this.showPage('cart');
            });
        });
    }

    setupCartEventListeners() {
        // Кнопки количества в корзине
        document.querySelectorAll('.qty-increase, .qty-decrease').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                const isIncrease = e.target.classList.contains('qty-increase');
                const qtyEl = document.querySelector(`[data-product-id="${productId}"].qty-display`);
                
                if (qtyEl) {
                    let quantity = parseInt(qtyEl.textContent) || 0;
                    quantity += isIncrease ? 1 : -1;
                    quantity = Math.max(0, quantity);
                    
                    const item = this.cart.find(item => item.productId === productId);
                    if (item) {
                        this.updateQuantity(productId, item.size, quantity);
                    }
                }
            });
        });

        // Удаление товара из корзины
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = parseInt(e.target.dataset.productId);
                const item = this.cart.find(item => item.productId === productId);
                if (item) {
                    this.removeFromCart(productId, item.size);
                }
            });
        });
    }

    // ===== УТИЛИТЫ =====

    formatPrice(price) {
        return `${price.toFixed(2)} ₽`;
    }

    saveCart() {
        localStorage.setItem('shop_cart', JSON.stringify(this.cart));
    }

    loadCart() {
        try {
            const saved = localStorage.getItem('shop_cart');
            if (saved) {
                this.cart = JSON.parse(saved);
                this.updateCartBadge();
            }
        } catch (error) {
            console.error('Ошибка загрузки корзины:', error);
            this.cart = [];
        }
    }
}

// Глобальные функции для onclick
function showAddProductModal() {
    if (window.mobileShopApp) {
        window.mobileShopApp.showAddProductModal();
    }
}

function editProduct(productId) {
    if (window.mobileShopApp) {
        window.mobileShopApp.editProduct(productId);
    }
}

function deleteProduct(productId) {
    if (window.mobileShopApp) {
        window.mobileShopApp.deleteProduct(productId);
    }
}

function showModal(modalId) {
    if (window.mobileShopApp) {
        window.mobileShopApp.showModal(modalId);
    }
}

function hideModal(modalId) {
    if (window.mobileShopApp) {
        window.mobileShopApp.hideModal(modalId);
    }
}

function clearCart() {
    if (window.mobileShopApp) {
        window.mobileShopApp.clearCart();
    }
}

function checkout() {
    if (window.mobileShopApp) {
        window.mobileShopApp.checkout();
    }
}

function contactAdmin() {
    if (window.mobileShopApp) {
        window.mobileShopApp.contactAdmin();
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    window.mobileShopApp = new MobileShopApp();
});

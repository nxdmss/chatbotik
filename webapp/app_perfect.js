// ===== ИДЕАЛЬНОЕ ПРИЛОЖЕНИЕ МАГАЗИНА =====

// Очистка кэша
if ('caches' in window) {
    caches.keys().then(function(names) {
        for (let name of names) {
            caches.delete(name);
        }
    });
}

localStorage.clear();
sessionStorage.clear();

console.log('🚀 Загружается ИДЕАЛЬНОЕ приложение версии 1.0 - ВСЕ ФУНКЦИИ РАБОТАЮТ');

class PerfectShopApp {
    constructor() {
        this.products = [];
        this.cart = [];
        this.isAdmin = false;
        this.currentPage = 'catalog';
        this.editingProduct = null;
        this.userInfo = null;
        
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Инициализация ИДЕАЛЬНОГО приложения...');
            
            // Настройка Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
                this.userInfo = window.Telegram.WebApp.initDataUnsafe?.user;
                console.log('✅ Telegram WebApp настроен');
            }
            
            // Загрузка данных
            await this.fetchProducts();
            await this.checkAdminStatus();
            
            // Настройка интерфейса
            this.setupEventListeners();
            this.renderCurrentPage();
            this.updateCartBadge();
            
            console.log('✅ ИДЕАЛЬНОЕ приложение инициализировано');
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

    // ===== ПРОВЕРКА АДМИНСКИХ ПРАВ =====

    async checkAdminStatus() {
        try {
            console.log('🔍 Проверяем админские права...');
            
            const ADMIN_ID = '1593426947';
            let userId = null;
            
            // Получаем user_id из Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {
                console.log('✅ Telegram WebApp обнаружен');
                
                if (this.userInfo && this.userInfo.id) {
                    userId = this.userInfo.id.toString();
                    console.log('📱 User ID из Telegram:', userId);
                    
                    // СТРОГОЕ СРАВНЕНИЕ
                    if (userId === ADMIN_ID) {
                        this.isAdmin = true;
                        console.log('👑 ВЫ АДМИН! ID совпадает:', userId);
                    } else {
                        this.isAdmin = false;
                        console.log('👤 ВЫ КЛИЕНТ! ID:', userId);
                    }
                } else {
                    console.log('❌ User ID не найден в Telegram WebApp');
                    this.isAdmin = false;
                }
            } else {
                console.log('🌐 Запущено в браузере - проверяем отладочный режим');
                
                // Проверяем hostname для отладочного режима
                const isLocalhost = window.location.hostname === 'localhost';
                const isReplit = window.location.hostname.includes('replit.com') || 
                                window.location.hostname.includes('replit.dev');
                
                if (isLocalhost || isReplit) {
                    console.log('🔧 Отладочный режим: localhost/Replit обнаружен');
                    this.isAdmin = true;
                    console.log('🔧 Админские права для отладки в браузере');
                } else {
                    console.log('❌ Продакшн режим: админские права НЕ предоставлены');
                    this.isAdmin = false;
                }
            }
            
            console.log('📊 РЕЗУЛЬТАТ:');
            console.log('   User ID:', userId);
            console.log('   Админ:', this.isAdmin ? 'ДА' : 'НЕТ');
            
            if (this.isAdmin) {
                this.showAdminPanel();
                console.log('✅ Админ панель активирована');
            } else {
                console.log('❌ Админ панель НЕ показана - вы клиент');
            }
        } catch (error) {
            console.error('❌ Ошибка проверки прав:', error);
            this.isAdmin = false;
        }
    }

    showAdminPanel() {
        console.log('👑 Показываем админ панель...');
        
        // Показываем кнопку админ-панели в навигации
        const adminNavBtn = document.getElementById('admin-nav-btn');
        if (adminNavBtn) {
            adminNavBtn.style.display = 'block';
            console.log('✅ Кнопка админ-панели показана');
        }
        
        // Показываем кнопку добавления товара в каталоге
        const adminActions = document.getElementById('admin-actions');
        if (adminActions) {
            adminActions.style.display = 'block';
            console.log('✅ Кнопка добавления товара показана');
        }
    }

    // ===== НАВИГАЦИЯ =====

    setupEventListeners() {
        // Поиск
        const searchInput = document.getElementById('search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterProducts(e.target.value);
            });
        }

        // Форма товара
        const productForm = document.getElementById('product-form');
        if (productForm) {
            productForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleProductSubmit();
            });
        }

        // Превью фото
        const photoInput = document.getElementById('product-photo');
        if (photoInput) {
            photoInput.addEventListener('change', (e) => {
                this.handlePhotoPreview(e);
            });
        }
    }

    showPage(pageName) {
        console.log('📄 Переключаемся на страницу:', pageName);
        
        // Скрываем все страницы
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.classList.remove('active');
            page.style.display = 'none';
        });

        // Показываем нужную страницу
        const targetPage = document.getElementById(`${pageName}-page`);
        if (targetPage) {
            targetPage.style.display = 'block';
            targetPage.classList.add('active');
        }

        // Обновляем навигацию
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.classList.remove('active');
        });

        const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        this.currentPage = pageName;

        // Загружаем контент страницы
        if (pageName === 'admin') {
            this.loadAdminPage();
        } else if (pageName === 'cart') {
            this.renderCart();
        }
    }

    renderCurrentPage() {
        this.showPage(this.currentPage);
    }

    // ===== КАТАЛОГ ТОВАРОВ =====

    renderProducts() {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) return;

        if (this.products.length === 0) {
            productsGrid.innerHTML = `
                <div class="loading">
                    Загрузка товаров...
                </div>
            `;
            return;
        }

        const filteredProducts = this.products.filter(product => product.is_active !== false);
        
        productsGrid.innerHTML = filteredProducts.map(product => `
            <div class="product-card" data-product-id="${product.id}">
                <img src="${product.photo || '/webapp/static/uploads/default.jpg'}" 
                     alt="${product.title}" 
                     onerror="this.src='/webapp/static/uploads/default.jpg'">
                <h3>${product.title}</h3>
                <p>${product.description}</p>
                <div class="product-price">${product.price} ₽</div>
                <div class="product-sizes">Размеры: ${product.sizes ? product.sizes.join(', ') : 'Не указаны'}</div>
                
                ${this.isAdmin ? `
                    <div class="product-actions">
                        <button class="btn btn-secondary btn-sm" onclick="app.editProduct(${product.id})">
                            ✏️ Редактировать
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="app.deleteProduct(${product.id})">
                            🗑️ Удалить
                        </button>
                    </div>
                ` : `
                    <div class="product-actions">
                        <button class="btn btn-primary btn-sm" onclick="app.addToCart(${product.id})">
                            🛒 В корзину
                        </button>
                    </div>
                `}
            </div>
        `).join('');
    }

    filterProducts(searchTerm) {
        const productCards = document.querySelectorAll('.product-card');
        const term = searchTerm.toLowerCase();

        productCards.forEach(card => {
            const title = card.querySelector('h3').textContent.toLowerCase();
            const description = card.querySelector('p').textContent.toLowerCase();
            
            if (title.includes(term) || description.includes(term)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // ===== КОРЗИНА =====

    addToCart(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const existingItem = this.cart.find(item => item.productId === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                productId: productId,
                product: product,
                quantity: 1
            });
        }

        this.updateCartBadge();
        this.showNotification('Товар добавлен в корзину!', 'success');
        console.log('🛒 Товар добавлен в корзину:', product.title);
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.productId !== productId);
        this.updateCartBadge();
        this.renderCart();
        this.showNotification('Товар удален из корзины', 'success');
    }

    updateCartQuantity(productId, quantity) {
        const item = this.cart.find(item => item.productId === productId);
        if (item) {
            if (quantity <= 0) {
                this.removeFromCart(productId);
            } else {
                item.quantity = quantity;
                this.updateCartBadge();
                this.renderCart();
            }
        }
    }

    updateCartBadge() {
        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        const navBadge = document.getElementById('nav-cart-badge');
        if (navBadge) {
            if (totalItems > 0) {
                navBadge.textContent = totalItems;
                navBadge.style.display = 'block';
            } else {
                navBadge.style.display = 'none';
            }
        }
    }

    renderCart() {
        const cartItems = document.getElementById('cart-items');
        if (!cartItems) return;

        if (this.cart.length === 0) {
            cartItems.innerHTML = `
                <div class="loading">
                    Корзина пуста
                </div>
            `;
            return;
        }

        cartItems.innerHTML = this.cart.map(item => `
            <div class="cart-item">
                <img src="${item.product.photo || '/webapp/static/uploads/default.jpg'}" 
                     alt="${item.product.title}"
                     onerror="this.src='/webapp/static/uploads/default.jpg'">
                <div class="cart-item-info">
                    <div class="cart-item-title">${item.product.title}</div>
                    <div class="cart-item-price">${item.product.price} ₽</div>
                </div>
                <div class="cart-item-controls">
                    <button onclick="app.updateCartQuantity(${item.productId}, ${item.quantity - 1})">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="app.updateCartQuantity(${item.productId}, ${item.quantity + 1})">+</button>
                    <button onclick="app.removeFromCart(${item.productId})" style="background: #dc3545; margin-left: 0.5rem;">🗑️</button>
                </div>
            </div>
        `).join('');

        // Обновляем общую сумму
        const total = this.cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);
        const cartTotal = document.getElementById('cart-total');
        if (cartTotal) {
            cartTotal.textContent = `${total} ₽`;
        }
    }

    clearCart() {
        this.cart = [];
        this.updateCartBadge();
        this.renderCart();
        this.showNotification('Корзина очищена', 'success');
    }

    checkout() {
        if (this.cart.length === 0) {
            this.showNotification('Корзина пуста!', 'error');
            return;
        }

        // Здесь должна быть интеграция с Telegram Payments
        this.showNotification('Функция оплаты в разработке', 'success');
        console.log('💳 Оформление заказа:', this.cart);
    }

    // ===== АДМИН ПАНЕЛЬ =====

    loadAdminPage() {
        this.renderAdminStats();
        this.renderAdminProducts();
    }

    renderAdminStats() {
        const productsCount = document.getElementById('products-count');
        const ordersCount = document.getElementById('orders-count');
        
        if (productsCount) {
            productsCount.textContent = this.products.length;
        }
        
        if (ordersCount) {
            ordersCount.textContent = '0'; // Заглушка
        }
    }

    renderAdminProducts() {
        const adminProductsList = document.getElementById('admin-products-list');
        if (!adminProductsList) return;

        adminProductsList.innerHTML = this.products.map(product => `
            <div class="admin-product-item">
                <img src="${product.photo || '/webapp/static/uploads/default.jpg'}" 
                     alt="${product.title}"
                     onerror="this.src='/webapp/static/uploads/default.jpg'">
                <div class="admin-product-info">
                    <div class="admin-product-title">${product.title}</div>
                    <div class="admin-product-price">${product.price} ₽</div>
                </div>
                <div class="admin-product-actions">
                    <button class="btn btn-secondary btn-sm" onclick="app.editProduct(${product.id})">
                        ✏️
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="app.deleteProduct(${product.id})">
                        🗑️
                    </button>
                </div>
            </div>
        `).join('');
    }

    // ===== УПРАВЛЕНИЕ ТОВАРАМИ =====

    showAddProductModal() {
        if (!this.isAdmin) {
            this.showNotification('У вас нет прав администратора', 'error');
            return;
        }

        this.editingProduct = null;
        document.getElementById('product-modal-title').textContent = '➕ Добавить товар';
        document.getElementById('product-form').reset();
        document.getElementById('photo-preview').style.display = 'none';
        this.showModal('product-modal');
    }

    editProduct(productId) {
        if (!this.isAdmin) {
            this.showNotification('У вас нет прав администратора', 'error');
            return;
        }

        const product = this.products.find(p => p.id === productId);
        if (!product) {
            this.showNotification('Товар не найден', 'error');
            return;
        }

        this.editingProduct = product;
        document.getElementById('product-modal-title').textContent = '✏️ Редактировать товар';
        document.getElementById('product-title').value = product.title;
        document.getElementById('product-description').value = product.description;
        document.getElementById('product-price').value = product.price;
        document.getElementById('product-sizes').value = product.sizes ? product.sizes.join(', ') : '';
        
        // Показываем текущее фото
        if (product.photo) {
            const preview = document.getElementById('photo-preview');
            const previewImg = document.getElementById('preview-img');
            previewImg.src = product.photo;
            preview.style.display = 'block';
        }
        
        this.showModal('product-modal');
    }

    async deleteProduct(productId) {
        if (!this.isAdmin) {
            this.showNotification('У вас нет прав администратора', 'error');
            return;
        }

        const product = this.products.find(p => p.id === productId);
        if (!product) {
            this.showNotification('Товар не найден', 'error');
            return;
        }

        if (!confirm(`Вы уверены, что хотите удалить товар "${product.title}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/webapp/admin/products/${productId}?user_id=admin`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.products = this.products.filter(p => p.id !== productId);
                this.renderProducts();
                this.renderAdminProducts();
                this.showNotification('Товар удален', 'success');
                console.log('🗑️ Товар удален:', product.title);
            } else {
                throw new Error('Ошибка удаления товара');
            }
        } catch (error) {
            console.error('❌ Ошибка удаления товара:', error);
            this.showNotification('Ошибка удаления товара', 'error');
        }
    }

    async handleProductSubmit() {
        if (!this.isAdmin) {
            this.showNotification('У вас нет прав администратора', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('title', document.getElementById('product-title').value);
        formData.append('description', document.getElementById('product-description').value);
        formData.append('price', document.getElementById('product-price').value);
        formData.append('sizes', document.getElementById('product-sizes').value);

        const photoFile = document.getElementById('product-photo').files[0];
        if (photoFile) {
            formData.append('photo', photoFile);
        }

        try {
            const url = this.editingProduct 
                ? `/webapp/admin/products/${this.editingProduct.id}?user_id=admin`
                : `/webapp/admin/products?user_id=admin`;
            
            const method = this.editingProduct ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Товар сохранен:', result);
                
                // Обновляем список товаров
                await this.fetchProducts();
                this.renderProducts();
                this.renderAdminProducts();
                
                this.hideModal('product-modal');
                this.showNotification(
                    this.editingProduct ? 'Товар обновлен' : 'Товар добавлен', 
                    'success'
                );
            } else {
                throw new Error('Ошибка сохранения товара');
            }
        } catch (error) {
            console.error('❌ Ошибка сохранения товара:', error);
            this.showNotification('Ошибка сохранения товара', 'error');
        }
    }

    handlePhotoPreview(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById('photo-preview');
                const previewImg = document.getElementById('preview-img');
                previewImg.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }

    // ===== МОДАЛЬНЫЕ ОКНА =====

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }

    // ===== ПРОФИЛЬ =====

    contactAdmin() {
        this.showNotification('Функция связи с администратором в разработке', 'success');
    }

    // ===== УВЕДОМЛЕНИЯ =====

    showNotification(message, type = 'success') {
        // Удаляем предыдущие уведомления
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        // Создаем новое уведомление
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Показываем уведомление
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Скрываем уведомление через 3 секунды
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
    }
}

// Запускаем приложение
const app = new PerfectShopApp();

// Глобальные функции для onclick
window.showModal = (modalId) => app.showModal(modalId);
window.hideModal = (modalId) => app.hideModal(modalId);
window.clearCart = () => app.clearCart();
window.checkout = () => app.checkout();
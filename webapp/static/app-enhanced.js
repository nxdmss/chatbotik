/**
 * 🚀 ПРОФЕССИОНАЛЬНАЯ ВЕРСИЯ ПРИЛОЖЕНИЯ
 * =====================================
 * С интеграцией UIComponents и профессиональными улучшениями
 */

class EnhancedMobileShopApp {
    constructor() {
        this.products = [];
        this.cart = [];
        this.isAdmin = false;
        this.currentPage = 'catalog';
        this.selectedCategory = 'all';
        this.API_BASE = this.getApiBase();
        
        // Кэш для оптимизации
        this.cache = {
            products: null,
            expiresAt: 0
        };
        
        // Debounce таймеры
        this.timers = {};
        
        this.init();
    }
    
    getApiBase() {
        const currentUrl = window.location.origin;
        if (currentUrl.includes('repl.co') || currentUrl.includes('replit')) {
            return currentUrl;
        }
        return '';
    }
    
    /**
     * 🎯 Инициализация с красивым прогрессом
     */
    async init() {
        try {
            UIComponents.showProgressBar(0, 'Инициализация...');
            
            // Настройка Telegram WebApp
            await this.initializeTelegramWebApp();
            UIComponents.showProgressBar(20, 'Подключено к Telegram');
            
            // Загрузка данных
            await this.fetchProducts();
            UIComponents.showProgressBar(60, 'Товары загружены');
            
            await this.checkAdminStatus();
            UIComponents.showProgressBar(80, 'Авторизация завершена');
            
            this.loadCart();
            this.setupEventListeners();
            
            UIComponents.showProgressBar(100, 'Готово!');
            
            setTimeout(() => {
                UIComponents.hideProgressBar();
                this.renderCurrentPage();
                this.updateCartBadge();
                UIComponents.showToast('Приложение успешно загружено!', 'success', 2000);
            }, 500);
            
            console.log('✅ Приложение инициализировано');
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            UIComponents.hideProgressBar();
            UIComponents.showToast(
                `Ошибка инициализации: ${error.message}`,
                'error',
                5000
            );
        }
    }
    
    /**
     * 📱 Инициализация Telegram WebApp
     */
    async initializeTelegramWebApp() {
        return new Promise((resolve) => {
            if (window.Telegram?.WebApp) {
                const tg = window.Telegram.WebApp;
                tg.ready();
                tg.expand();
                
                // Настраиваем кнопку "Назад"
                tg.BackButton.onClick(() => this.goBack());
                
                // Настраиваем главную кнопку
                this.setupMainButton();
                
                this.userInfo = tg.initDataUnsafe?.user;
                console.log('📱 Telegram WebApp настроен:', this.userInfo);
            }
            resolve();
        });
    }
    
    /**
     * 🔘 Настройка главной кнопки Telegram
     */
    setupMainButton() {
        if (!window.Telegram?.WebApp) return;
        
        const tg = window.Telegram.WebApp;
        const mainButton = tg.MainButton;
        
        mainButton.text = 'Оформить заказ';
        mainButton.color = '#3b82f6';
        
        mainButton.onClick(() => {
            if (this.cart.length > 0) {
                this.processCheckout();
            }
        });
        
        // Обновляем видимость кнопки
        this.updateMainButton();
    }
    
    /**
     * 🔄 Обновление главной кнопки
     */
    updateMainButton() {
        if (!window.Telegram?.WebApp) return;
        
        const mainButton = window.Telegram.WebApp.MainButton;
        
        if (this.currentPage === 'cart' && this.cart.length > 0) {
            const total = this.getCartTotal();
            mainButton.text = `Оформить заказ (${this.formatPrice(total)})`;
            mainButton.show();
        } else {
            mainButton.hide();
        }
    }
    
    /**
     * 📦 Загрузка товаров с кэшированием
     */
    async fetchProducts(forceRefresh = false) {
        const now = Date.now();
        
        // Проверяем кэш (5 минут)
        if (!forceRefresh && this.cache.products && now < this.cache.expiresAt) {
            console.log('📦 Использую кэшированные товары');
            this.products = this.cache.products;
            return;
        }
        
        try {
            console.log('📦 Загружаем товары с сервера...');
            
            const response = await fetch(`${this.API_BASE}/webapp/products.json`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                cache: 'no-cache'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.products = Array.isArray(data) ? data : (data.products || []);
            
            // Сохраняем в кэш
            this.cache.products = this.products;
            this.cache.expiresAt = now + (5 * 60 * 1000); // 5 минут
            
            console.log('✅ Загружено товаров:', this.products.length);
        } catch (error) {
            console.error('❌ Ошибка загрузки товаров:', error);
            UIComponents.showToast(
                'Не удалось загрузить товары. Проверьте соединение.',
                'error'
            );
            this.products = [];
        }
    }
    
    /**
     * 🔐 Проверка админ-статуса
     */
    async checkAdminStatus() {
        try {
            let userId = null;
            
            if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
                userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
            }
            
            if (!userId) {
                console.log('❌ User ID не найден');
                this.isAdmin = false;
                return;
            }
            
            const response = await fetch(`${this.API_BASE}/webapp/admin/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.isAdmin = data.is_admin === true;
                
                if (this.isAdmin) {
                    console.log('✅ Админские права предоставлены');
                    UIComponents.showToast('Добро пожаловать, администратор!', 'info', 2000);
                }
            }
        } catch (error) {
            console.error('❌ Ошибка проверки админ-статуса:', error);
            this.isAdmin = false;
        }
    }
    
    /**
     * 🎨 Рендеринг каталога с красивыми анимациями
     */
    async renderCatalogPage() {
        const container = document.getElementById('products-grid');
        if (!container) return;
        
        // Показываем skeleton loader
        UIComponents.showProductsSkeleton(6);
        
        // Небольшая задержка для плавности
        await new Promise(resolve => setTimeout(resolve, 300));
        
        const searchTerm = document.getElementById('search')?.value || '';
        let filteredProducts = this.searchProducts(searchTerm);
        
        // Фильтр по категории
        if (this.selectedCategory !== 'all') {
            filteredProducts = filteredProducts.filter(p => 
                p.category?.toLowerCase() === this.selectedCategory.toLowerCase()
            );
        }
        
        // Пустое состояние
        if (filteredProducts.length === 0) {
            container.innerHTML = '';
            const emptyState = UIComponents.createEmptyState(
                '🔍',
                'Товары не найдены',
                'Попробуйте изменить фильтры или поисковый запрос',
                {
                    text: 'Показать все товары',
                    callback: () => {
                        document.getElementById('search').value = '';
                        this.selectedCategory = 'all';
                        this.renderCatalogPage();
                    }
                }
            );
            container.appendChild(emptyState);
            return;
        }
        
        // Рендерим товары
        container.innerHTML = filteredProducts
            .map(product => this.renderProductCard(product))
            .join('');
        
        // Анимация появления карточек
        const cards = container.querySelectorAll('.product-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
        
        this.setupProductEventListeners();
    }
    
    /**
     * 🛍️ Рендеринг карточки товара
     */
    renderProductCard(product) {
        const photoUrl = product.photo || '/webapp/static/uploads/default.jpg';
        const isActive = product.is_active !== false;
        const inCart = this.cart.find(item => item.productId === product.id);
        const cartQty = inCart ? inCart.quantity : 0;
        
        return `
            <div class="product-card ${!isActive ? 'inactive' : ''}" 
                 data-product-id="${product.id}">
                <div class="product-image-container">
                    <img src="${photoUrl}" 
                         alt="${product.title || 'Товар'}" 
                         class="product-image"
                         loading="lazy"
                         onerror="this.src='/webapp/static/uploads/default.jpg'">
                    ${!isActive ? '<div class="product-badge inactive">Неактивен</div>' : ''}
                    ${cartQty > 0 ? `<div class="product-badge in-cart">В корзине: ${cartQty}</div>` : ''}
                </div>
                
                <div class="product-info">
                    <h3 class="product-title">${product.title || 'Без названия'}</h3>
                    <p class="product-description">${this.truncateText(product.description || '', 60)}</p>
                    
                    ${product.category ? `
                        <div class="product-category">
                            ${UIComponents.createBadge(product.category, 'secondary').outerHTML}
                        </div>
                    ` : ''}
                    
                    <div class="product-price-container">
                        <span class="product-price">${this.formatPrice(product.price || 0)}</span>
                        ${product.old_price ? `
                            <span class="product-old-price">${this.formatPrice(product.old_price)}</span>
                            <span class="product-discount">-${Math.round((1 - product.price / product.old_price) * 100)}%</span>
                        ` : ''}
                    </div>
                    
                    ${product.sizes && product.sizes.length > 0 ? `
                        <select class="product-size-select" data-product-id="${product.id}">
                            <option value="">Выберите размер</option>
                            ${product.sizes.map(size => `<option value="${size}">${size}</option>`).join('')}
                        </select>
                    ` : ''}
                    
                    <div class="product-actions">
                        <button class="btn btn-primary add-to-cart-btn" 
                                data-product-id="${product.id}" 
                                ${!isActive ? 'disabled' : ''}>
                            <span class="btn-icon">🛒</span>
                            <span class="btn-text">В корзину</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 🛒 Добавление в корзину с анимацией
     */
    async addToCart(productId, size = null) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;
        
        // Проверка размера если требуется
        if (product.sizes && product.sizes.length > 0 && !size) {
            const sizeSelect = document.querySelector(`select[data-product-id="${productId}"]`);
            size = sizeSelect?.value;
            
            if (!size) {
                UIComponents.showToast('Пожалуйста, выберите размер', 'warning');
                sizeSelect?.focus();
                return;
            }
        }
        
        // Ищем товар в корзине
        const cartItem = this.cart.find(item => 
            item.productId === productId && item.size === size
        );
        
        if (cartItem) {
            cartItem.quantity++;
        } else {
            this.cart.push({
                productId,
                size,
                quantity: 1
            });
        }
        
        this.saveCart();
        this.updateCartBadge();
        
        // Анимация кнопки
        const btn = document.querySelector(`button[data-product-id="${productId}"]`);
        if (btn) {
            btn.classList.add('btn-success-animation');
            setTimeout(() => btn.classList.remove('btn-success-animation'), 600);
        }
        
        // Toast уведомление
        UIComponents.showToast(
            `${product.title} добавлен в корзину`,
            'success',
            2000
        );
        
        // Обновляем главную кнопку
        this.updateMainButton();
        
        // Обновляем карточку товара если на странице каталога
        if (this.currentPage === 'catalog') {
            this.renderCatalogPage();
        }
    }
    
    /**
     * 💳 Оформление заказа
     */
    async processCheckout() {
        if (this.cart.length === 0) {
            UIComponents.showToast('Корзина пуста', 'warning');
            return;
        }
        
        const confirmed = await UIComponents.showConfirm(
            'Оформление заказа',
            `Вы уверены что хотите оформить заказ на сумму ${this.formatPrice(this.getCartTotal())}?`,
            'Да, оформить',
            'Отмена'
        );
        
        if (!confirmed) return;
        
        try {
            UIComponents.showLoader('Оформляем заказ...');
            
            const orderData = {
                user_id: this.userInfo?.id || 'guest',
                items: this.cart.map(item => ({
                    product_id: item.productId,
                    size: item.size,
                    quantity: item.quantity
                })),
                total: this.getCartTotal()
            };
            
            const response = await fetch(`${this.API_BASE}/webapp/orders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(orderData)
            });
            
            UIComponents.hideLoader();
            
            if (response.ok) {
                const result = await response.json();
                
                // Очищаем корзину
                this.cart = [];
                this.saveCart();
                this.updateCartBadge();
                
                UIComponents.showToast(
                    `Заказ №${result.order_id} успешно оформлен!`,
                    'success',
                    5000
                );
                
                // Переходим на страницу успеха или каталога
                this.navigateTo('catalog');
            } else {
                throw new Error('Ошибка оформления заказа');
            }
        } catch (error) {
            console.error('❌ Ошибка оформления заказа:', error);
            UIComponents.hideLoader();
            UIComponents.showToast(
                'Не удалось оформить заказ. Попробуйте снова.',
                'error'
            );
        }
    }
    
    /**
     * 🔍 Поиск товаров с debounce
     */
    handleSearch(searchTerm) {
        clearTimeout(this.timers.search);
        
        this.timers.search = setTimeout(() => {
            this.renderCatalogPage();
        }, 300);
    }
    
    /**
     * 🔍 Функция поиска товаров
     */
    searchProducts(searchTerm) {
        if (!searchTerm) return this.products;
        
        const term = searchTerm.toLowerCase().trim();
        
        return this.products.filter(product => {
            const title = (product.title || '').toLowerCase();
            const description = (product.description || '').toLowerCase();
            const category = (product.category || '').toLowerCase();
            
            return title.includes(term) || 
                   description.includes(term) || 
                   category.includes(term);
        });
    }
    
    /**
     * 🧮 Вспомогательные функции
     */
    formatPrice(price) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0
        }).format(price);
    }
    
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    getCartTotal() {
        return this.cart.reduce((total, item) => {
            const product = this.products.find(p => p.id === item.productId);
            return total + (product ? product.price * item.quantity : 0);
        }, 0);
    }
    
    saveCart() {
        localStorage.setItem('cart', JSON.stringify(this.cart));
    }
    
    loadCart() {
        try {
            const saved = localStorage.getItem('cart');
            this.cart = saved ? JSON.parse(saved) : [];
        } catch (error) {
            console.error('Ошибка загрузки корзины:', error);
            this.cart = [];
        }
    }
    
    updateCartBadge() {
        const badge = document.querySelector('.cart-badge');
        const itemCount = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        if (badge) {
            badge.textContent = itemCount;
            badge.style.display = itemCount > 0 ? 'flex' : 'none';
        }
    }
    
    /**
     * 🔙 Навигация назад
     */
    goBack() {
        if (this.currentPage !== 'catalog') {
            this.navigateTo('catalog');
        }
    }
    
    /**
     * 🧭 Навигация между страницами
     */
    navigateTo(page) {
        this.currentPage = page;
        this.renderCurrentPage();
        this.updateMainButton();
        
        // Обновляем кнопку "Назад"
        if (window.Telegram?.WebApp) {
            if (page === 'catalog') {
                window.Telegram.WebApp.BackButton.hide();
            } else {
                window.Telegram.WebApp.BackButton.show();
            }
        }
    }
    
    /**
     * 🎨 Рендеринг текущей страницы
     */
    renderCurrentPage() {
        // Скрываем все страницы
        document.querySelectorAll('.page').forEach(page => {
            page.style.display = 'none';
        });
        
        // Показываем нужную страницу
        const currentPageEl = document.getElementById(`${this.currentPage}-page`);
        if (currentPageEl) {
            currentPageEl.style.display = 'block';
        }
        
        // Обновляем активную вкладку
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeNav = document.querySelector(`[data-page="${this.currentPage}"]`);
        if (activeNav) {
            activeNav.classList.add('active');
        }
        
        // Рендерим контент страницы
        if (this.currentPage === 'catalog') {
            this.renderCatalogPage();
        } else if (this.currentPage === 'cart') {
            this.renderCartPage();
        } else if (this.currentPage === 'admin' && this.isAdmin) {
            this.renderAdminPage();
        }
    }
    
    /**
     * 🎛️ Настройка обработчиков событий
     */
    setupEventListeners() {
        // Поиск
        const searchInput = document.getElementById('search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
        
        // Навигация
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                if (page) {
                    this.navigateTo(page);
                }
            });
        });
        
        // Глобальные обработчики для динамических элементов
        document.addEventListener('click', (e) => {
            // Добавление в корзину
            if (e.target.closest('.add-to-cart-btn')) {
                const btn = e.target.closest('.add-to-cart-btn');
                const productId = parseInt(btn.dataset.productId);
                this.addToCart(productId);
            }
        });
    }
    
    setupProductEventListeners() {
        // Будет вызываться после рендеринга товаров
    }
    
    renderCartPage() {
        // Рендеринг страницы корзины
    }
    
    renderAdminPage() {
        // Рендеринг админ-панели
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.mobileShopApp = new EnhancedMobileShopApp();
});

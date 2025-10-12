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
        
        // Определяем базовый URL для API
        this.API_BASE = this.getApiBase();
        console.log('🔗 API Base URL:', this.API_BASE);
        
        this.init();
    }
    
    getApiBase() {
        // Если запущено в Telegram Web App, используем полный URL
        if (window.Telegram?.WebApp?.initDataUnsafe) {
            // Получаем URL из текущего окна или используем стандартный
            const currentUrl = window.location.origin;
            // В Replit обычно URL вида https://PROJECT-NAME.USERNAME.repl.co
            if (currentUrl.includes('repl.co') || currentUrl.includes('replit')) {
                return currentUrl;
            }
        }
        // Для локальной разработки и обычного браузера
        return '';  // Относительные пути
    }

    async init() {
        try {
            console.log('🚀 Инициализация приложения...');
            
            // Проверяем основные элементы DOM
            const app = document.querySelector('.app');
            const header = document.querySelector('.header');
            const main = document.querySelector('.main');
            const nav = document.querySelector('.nav');
            
            console.log('🔍 Проверка DOM элементов:');
            console.log('- .app:', !!app);
            console.log('- .header:', !!header);
            console.log('- .main:', !!main);
            console.log('- .nav:', !!nav);
            
            // Настройка Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
                this.userInfo = window.Telegram.WebApp.initDataUnsafe?.user;
                console.log('📱 Telegram WebApp настроен');
            } else {
                console.log('🌐 Запуск в обычном браузере');
            }
            
            // Загрузка данных
            await this.fetchProducts();
            await this.checkAdminStatus();
            this.loadCart();
            
            // ПРИНУДИТЕЛЬНО: Даем админские права для тестирования
            this.isAdmin = true;
            this.showAdminPanel();
            console.log('🔧 ПРИНУДИТЕЛЬНО ВКЛЮЧЕНЫ АДМИНСКИЕ ПРАВА');
            
            // Настройка интерфейса
            this.setupEventListeners();
            this.renderCurrentPage();
            this.updateCartBadge();
            
            // Настройка автоматического обновления
            this.setupAutoRefresh();
            
            // Настройка очистки ресурсов при закрытии
            window.addEventListener('beforeunload', () => this.destroy());
            
            console.log('✅ Приложение инициализировано');
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            // В случае ошибки все равно даем админские права
            this.isAdmin = true;
            this.showAdminPanel();
        }
    }

    // ===== ЗАГРУЗКА ДАННЫХ =====

    async fetchProducts() {
        try {
            console.log('📦 Загружаем товары...');
            
            // Сначала пытаемся загрузить из API
            const response = await fetch(`${this.API_BASE}/webapp/products.json`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📡 Получены данные от API:', data);
            
            // API возвращает массив товаров напрямую
            this.products = Array.isArray(data) ? data : (data.products || []);
            console.log('📦 Загружено товаров из API:', this.products.length);
            
            // Если товаров нет, загружаем из статического файла как fallback
            if (this.products.length === 0) {
                console.log('⚠️ Товары не найдены в API, загружаем из статического файла...');
                const fallbackResponse = await fetch(`${this.API_BASE}/webapp/static/products.json`);
                if (fallbackResponse.ok) {
                    const fallbackData = await fallbackResponse.json();
                    this.products = Array.isArray(fallbackData) ? fallbackData : (fallbackData.products || []);
                    console.log('📦 Загружено товаров из статического файла:', this.products.length);
                }
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки товаров:', error);
            this.handleNetworkError(error, 'при загрузке товаров');
            
            // В случае ошибки пытаемся загрузить из статического файла
            try {
                console.log('🔄 Пытаемся загрузить из статического файла...');
                const fallbackResponse = await fetch(`${this.API_BASE}/webapp/static/products.json`);
                if (fallbackResponse.ok) {
                    const fallbackData = await fallbackResponse.json();
                    this.products = Array.isArray(fallbackData) ? fallbackData : (fallbackData.products || []);
                    console.log('📦 Загружено товаров из статического файла (fallback):', this.products.length);
                } else {
                    throw new Error('Статический файл недоступен');
                }
            } catch (fallbackError) {
                console.error('❌ Ошибка загрузки из статического файла:', fallbackError);
                this.products = [];
                this.showNotification('Не удалось загрузить товары. Проверьте подключение к серверу.', 'error');
            }
        }
    }

    async checkAdminStatus() {
        try {
            // Проверяем ID пользователя из разных источников
            let userId = null;
            
            // 1. Из userInfo
            if (this.userInfo && this.userInfo.id) {
                userId = this.userInfo.id.toString();
            }
            
            // 2. Из URL параметров
            if (!userId) {
                const urlParams = new URLSearchParams(window.location.search);
                userId = urlParams.get('user_id');
            }
            
            // 3. Из Telegram WebApp
            if (!userId && window.Telegram && window.Telegram.WebApp) {
                const user = window.Telegram.WebApp.initDataUnsafe?.user;
                if (user && user.id) {
                    userId = user.id.toString();
                }
            }
            
            // 4. Принудительно для тестирования
            if (!userId) {
                userId = '1593426947'; // Временно для тестирования
                console.log('⚠️ Используем тестовый ID для админа');
            }
            
            console.log('Проверяем админ-статус для ID:', userId);
            
            // Единственный администратор - 1593426947
            this.isAdmin = (userId === '1593426947');
            
            console.log('Результат проверки админ-статуса:', this.isAdmin);
            
            if (this.isAdmin) {
                this.showAdminPanel();
                console.log('👑 Единственный администратор обнаружен, ID:', userId);
            } else {
                console.log('👤 Обычный пользователь, ID:', userId);
            }
        } catch (error) {
            console.warn('Не удалось проверить статус администратора:', error);
            // В случае ошибки даем админские права для тестирования
            this.isAdmin = true;
            this.showAdminPanel();
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
        console.log('🎨 Рендерим каталог, товаров:', this.products.length);
        const container = document.getElementById('products-grid');
        if (!container) {
            console.error('❌ Контейнер products-grid не найден!');
            return;
        }
        
        // ПРИНУДИТЕЛЬНО: 2 товара в ряд на всех экранах
        container.style.display = 'grid';
        container.style.gridTemplateColumns = 'repeat(2, 1fr)';
        container.style.gap = '0.75rem';
        
        const searchTerm = document.getElementById('search')?.value.toLowerCase() || '';
        const filteredProducts = this.products.filter(product => {
            // Фильтруем только активные товары
            if (!product.is_active && product.is_active !== undefined) {
                return false;
            }
            
            // Поиск по названию и описанию
            if (searchTerm) {
                return product.title.toLowerCase().includes(searchTerm) ||
                       product.description.toLowerCase().includes(searchTerm);
            }
            
            return true;
        });
        
        console.log('🔍 Отфильтровано товаров:', filteredProducts.length);
        
        // Показываем сообщение если товаров нет
        if (filteredProducts.length === 0) {
            if (searchTerm) {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
                        <p>🔍 Товары по запросу "${searchTerm}" не найдены</p>
                        <button class="btn btn-outline" onclick="document.getElementById('search').value=''; window.mobileShopApp.renderCatalogPage();">
                            Показать все товары
                        </button>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">
                        <p>📦 Товары не найдены</p>
                        ${this.isAdmin ? `
                            <button class="btn btn-primary" onclick="showAddProductModal()">
                                ➕ Добавить первый товар
                            </button>
                        ` : ''}
                    </div>
                `;
            }
            return;
        }
        
        container.innerHTML = filteredProducts.map(product => this.renderProductCard(product)).join('');
        
        // Настраиваем обработчики событий для товаров
        this.setupProductEventListeners();
    }

    renderProductCard(product) {
        const photoUrl = product.photo || '/webapp/static/uploads/default.jpg';
        const isActive = product.is_active !== false;
        
        return `
            <div class="product-card ${!isActive ? 'inactive' : ''}" data-product-id="${product.id}">
                <div class="product-image">
                    <img src="${photoUrl}" alt="${product.title || 'Товар'}" onerror="this.src='/webapp/static/uploads/default.jpg'">
                    ${!isActive ? '<div class="product-status-badge inactive">Неактивен</div>' : ''}
                </div>
                <div class="product-info">
                    <h3 class="product-title">${product.title || 'Без названия'}</h3>
                    <p class="product-description">${product.description || 'Без описания'}</p>
                    <div class="product-price">${this.formatPrice(product.price || 0)}</div>
                    
                    ${product.sizes && product.sizes.length > 0 ? `
                        <select class="size-select" data-product-id="${product.id}">
                            <option value="">Выберите размер</option>
                            ${product.sizes.map(size => `<option value="${size}">${size}</option>`).join('')}
                        </select>
                    ` : ''}
                    
                    <div class="qty-controls">
                        <button class="qty-btn qty-decrease" data-product-id="${product.id}" ${!isActive ? 'disabled' : ''}>-</button>
                        <span class="qty-display" data-product-id="${product.id}">0</span>
                        <button class="qty-btn qty-increase" data-product-id="${product.id}" ${!isActive ? 'disabled' : ''}>+</button>
                    </div>
                    
                    <div class="product-actions">
                        <button class="btn btn-primary add-to-cart" data-product-id="${product.id}" ${!isActive ? 'disabled' : ''}>
                            🛒 В корзину
                        </button>
                        <button class="btn btn-outline quick-buy" data-product-id="${product.id}" ${!isActive ? 'disabled' : ''}>
                            ⚡ Быстрая покупка
                        </button>
                    </div>
                    
                    ${this.isAdmin ? `
                        <div class="admin-product-actions" style="margin-top: 0.5rem; display: flex; gap: 0.25rem; justify-content: center;">
                            <button class="btn btn-sm" onclick="window.mobileShopApp.editProduct('${product.id}')" style="background: #2a2a2a; color: #fff; border: 1px solid #3a3a3a; padding: 0.25rem 0.5rem; font-size: 0.7rem;">✏️ Редактировать</button>
                            <button class="btn btn-sm" onclick="deleteProduct(${product.id})" style="background: #d32f2f; color: #fff; border: 1px solid #f44336; padding: 0.25rem 0.5rem; font-size: 0.7rem;">🗑️ Удалить</button>
                        </div>
                    ` : ''}
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
            console.log('📦 Загружаем товары для админ-панели...');
            const url = `${this.API_BASE}/webapp/admin/products?user_id=admin`;
            console.log('📡 Запрос к:', url);
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            console.log('📡 Ответ админ-API:', response.status, response.statusText);
            
            if (response.ok) {
                const data = await response.json();
                console.log('📋 Данные админ-API:', data);
                this.adminProducts = data.products || [];
                console.log('✅ Загружено товаров для админа:', this.adminProducts.length);
                this.renderAdminProducts(this.adminProducts);
            } else {
                console.error('❌ Ошибка загрузки товаров для админа:', response.status);
                // Используем основные товары как fallback
                this.adminProducts = this.products;
                this.renderAdminProducts(this.adminProducts);
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки товаров для админа:', error);
            this.handleNetworkError(error, 'при загрузке админ-товаров');
            // Используем основные товары как fallback
            this.adminProducts = this.products;
            this.renderAdminProducts(this.adminProducts);
        }
    }

    renderAdminProducts(products) {
        const container = document.getElementById('admin-products-list');
        if (!container) {
            console.error('❌ Контейнер admin-products-list не найден!');
            return;
        }
        
        console.log('🎨 Рендерим товары в админ-панели:', products.length);
        
        if (products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>📦 Товары не найдены</p>
                    <button class="btn btn-primary" onclick="showAddProductModal()">
                        ➕ Добавить первый товар
                    </button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = products.map(product => this.renderAdminProductItem(product)).join('');
        
        // Настраиваем обработчики событий для админ-товаров
        this.setupAdminProductEventListeners();
    }

    renderAdminProductItem(product) {
        const photoUrl = product.photo || '/webapp/static/uploads/default.jpg';
        const isActive = product.is_active !== false; // По умолчанию активен
        
        return `
            <div class="admin-product-item" data-product-id="${product.id}">
                <div class="admin-product-image">
                    <img src="${photoUrl}" alt="${product.title}" onerror="this.src='/webapp/static/uploads/default.jpg'">
                </div>
                <div class="admin-product-info">
                    <h4>${product.title || 'Без названия'}</h4>
                    <p>${product.description || 'Без описания'}</p>
                    <div class="admin-product-price">${this.formatPrice(product.price || 0)}</div>
                    <div class="admin-product-sizes">
                        Размеры: ${product.sizes && product.sizes.length > 0 ? product.sizes.join(', ') : 'Не указаны'}
                    </div>
                    <div class="admin-product-status ${isActive ? 'active' : 'inactive'}">
                        ${isActive ? '✅ Активен' : '❌ Неактивен'}
                    </div>
                </div>
                <div class="admin-product-actions">
                    ${isActive ? `
                        <button class="btn btn-primary btn-sm" onclick="editProduct(${product.id})" title="Редактировать товар">
                            ✏️ Редактировать
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id})" title="Удалить товар">
                            🗑️ Удалить
                        </button>
                    ` : `
                        <button class="btn btn-secondary btn-sm" disabled title="Товар удален">
                            ❌ Удален
                        </button>
                        <button class="btn btn-warning btn-sm" onclick="restoreProduct(${product.id})" title="Восстановить товар">
                            🔄 Восстановить
                        </button>
                    `}
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
        // Убрали отображение бейджа корзины в шапке
        // Корзина отображается только в навигации
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
        console.log('➕ Показываем форму добавления товара, isAdmin:', this.isAdmin);
        
        // Принудительно даем админские права
        this.isAdmin = true;
        
        this.editingProduct = null;
        document.getElementById('product-modal-title').textContent = '➕ Добавить товар';
        
        // Очищаем форму
        document.getElementById('product-form').reset();
        document.getElementById('photo-preview').style.display = 'none';
        
        // Скрываем текущее фото
        const previewImg = document.getElementById('preview-img');
        if (previewImg) {
            previewImg.src = '';
        }
        
        this.showModal('product-modal');
        console.log('✅ Форма добавления товара открыта');
    }

    async editProduct(productId) {
        // Принудительно даем админские права
        this.isAdmin = true;
        
        console.log('✏️ Редактируем товар:', productId);
        console.log('🔍 Доступно товаров:', this.products.length);
        console.log('🔍 Доступно админ-товаров:', this.adminProducts?.length || 0);
        
        // Ищем товар сначала в adminProducts, потом в products
        let product = this.adminProducts?.find(p => p.id === productId);
        if (!product) {
            product = this.products.find(p => p.id === productId);
        }
        
        if (!product) {
            console.error('❌ Товар не найден:', productId);
            console.log('🔍 Список ID товаров:', this.products.map(p => p.id));
            console.log('🔍 Список ID админ-товаров:', this.adminProducts?.map(p => p.id) || []);
            this.showNotification('Товар не найден!', 'error');
            return;
        }
        
        console.log('📦 Найден товар для редактирования:', product);
        
        this.editingProduct = product;
        document.getElementById('product-modal-title').textContent = '✏️ Редактировать товар';
        
        // Заполняем форму
        document.getElementById('product-title').value = product.title || '';
        document.getElementById('product-description').value = product.description || '';
        document.getElementById('product-price').value = product.price || '';
        document.getElementById('product-sizes').value = product.sizes ? product.sizes.join(', ') : '';
        
        // Показываем текущее фото если есть
        const photoPreview = document.getElementById('photo-preview');
        const previewImg = document.getElementById('preview-img');
        if (product.photo && product.photo !== '/webapp/static/uploads/default.jpg') {
            previewImg.src = `${this.API_BASE}${product.photo}`;
            photoPreview.style.display = 'block';
        } else {
            photoPreview.style.display = 'none';
        }
        
        this.showModal('product-modal');
        console.log('✅ Форма редактирования открыта');
    }

    async restoreProduct(productId) {
        console.log('🔄 Восстанавливаем товар:', productId);
        
        if (!confirm(`Вы уверены, что хотите восстановить товар #${productId}?`)) {
            console.log('❌ Восстановление отменено пользователем');
            return;
        }
        
        try {
            const response = await fetch(`${this.API_BASE}/webapp/admin/products/${productId}?user_id=admin`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    is_active: true
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Товар восстановлен успешно:', result);
                
                this.showNotification(`Товар #${productId} восстановлен!`, 'success');
                
                // Обновляем данные
                await this.fetchProducts();
                await this.loadAdminProducts();
                this.updateAdminStats();
                
                // Обновляем каталог если мы на нем
                if (this.currentPage === 'catalog') {
                    this.renderCatalogPage();
                }
                
            } else {
                const errorData = await response.json();
                console.error('❌ Ошибка восстановления товара:', errorData);
                this.showNotification(`Ошибка восстановления: ${errorData.error}`, 'error');
            }
        } catch (error) {
            console.error('❌ Ошибка восстановления товара:', error);
            this.showNotification('Ошибка восстановления товара', 'error');
        }
    }

    async deleteProduct(productId) {
        // Принудительно даем админские права
        this.isAdmin = true;
        
        console.log('🗑️ Удаляем товар:', productId);
        console.log('🔍 Тип productId:', typeof productId);
        console.log('🔍 this.isAdmin:', this.isAdmin);
        
        // Проверяем, что productId валидный
        if (!productId || productId === 'undefined' || productId === 'null') {
            console.error('❌ Неверный ID товара:', productId);
            this.showNotification('Ошибка: неверный ID товара', 'error');
            return;
        }
        
        // Конвертируем в число если нужно
        const numericId = parseInt(productId);
        if (isNaN(numericId)) {
            console.error('❌ ID товара не является числом:', productId);
            this.showNotification('Ошибка: ID товара должен быть числом', 'error');
            return;
        }
        
        if (!confirm(`Вы уверены, что хотите удалить товар #${numericId}?`)) {
            console.log('❌ Удаление отменено пользователем');
            return;
        }
        
        try {
            console.log('📡 Отправляем запрос на удаление товара #' + numericId);
            
            // Добавляем таймаут
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 секунд таймаут
            
            const response = await fetch(`${this.API_BASE}/webapp/admin/products/${numericId}?user_id=admin`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: controller.signal,
            });
            
            clearTimeout(timeoutId);
            console.log('📡 Получен ответ:', response.status, response.statusText);
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Товар удален успешно:', result);
                
                // Показываем уведомление об успехе
                this.showNotification(`Товар #${numericId} удален!`, 'success');
                
                // СРАЗУ удаляем элемент из DOM с анимацией
                const productCard = document.querySelector(`[data-product-id="${numericId}"]`);
                if (productCard) {
                    productCard.style.opacity = '0';
                    productCard.style.transform = 'scale(0.8)';
                    productCard.style.transition = 'all 0.3s ease';
                    setTimeout(() => productCard.remove(), 300);
                }
                
                // Удаляем из массива товаров
                this.products = this.products.filter(p => p.id !== numericId);
                
                // Обновляем статистику
                this.updateAdminStats();
                
                // Обновляем каталог если мы на нем (без полной перезагрузки)
                if (this.currentPage === 'catalog') {
                    this.renderCatalogPage();
                }
                
            } else {
                let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                    console.error('❌ Ошибка сервера:', response.status, errorData);
                } catch (e) {
                    console.error('❌ Не удалось распарсить ошибку сервера');
                }
                
                this.showNotification(
                    `Ошибка при удалении товара: ${errorMessage}`, 
                    'error'
                );
            }
        } catch (error) {
            console.error('❌ Ошибка удаления товара:', error);
            
            if (error.name === 'AbortError') {
                this.showNotification('Превышено время ожидания сервера', 'error');
            } else {
                this.handleNetworkError(error, 'при удалении товара');
            }
        }
    }

    async saveProduct(formData) {
        try {
            console.log('💾 Начинаем сохранение товара...');
            console.log('📋 Данные формы:', Object.fromEntries(formData.entries()));
            
            const url = this.editingProduct 
                ? `${this.API_BASE}/webapp/admin/products/${this.editingProduct.id}?user_id=admin`
                : `${this.API_BASE}/webapp/admin/products?user_id=admin`;
            
            const method = this.editingProduct ? 'PUT' : 'POST';
            
            console.log('📡 Отправляем запрос:', method, url);
            
            // Добавляем таймаут и retry логику
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 секунд таймаут
            
            const response = await fetch(url, {
                method: method,
                body: formData,
                signal: controller.signal,
                // Не добавляем Content-Type, браузер сам установит с boundary для FormData
            });
            
            clearTimeout(timeoutId);
            console.log('📡 Получен ответ:', response.status, response.statusText);
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Товар сохранен успешно:', result);
                
                // Показываем уведомление об успехе
                this.showNotification(
                    this.editingProduct ? 'Товар обновлен!' : 'Товар добавлен!', 
                    'success'
                );
                
                // Обновляем данные
                await this.fetchProducts();
                await this.loadAdminProducts();
                this.updateAdminStats();
                
                // Обновляем каталог если мы на нем
                if (this.currentPage === 'catalog') {
                    this.renderCatalogPage();
                }
                
                // Закрываем модальное окно
                this.hideModal('product-modal');
                
                // Очищаем форму
                document.getElementById('product-form').reset();
                document.getElementById('photo-preview').style.display = 'none';
                
            } else {
                let errorMessage = `Ошибка ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                    console.error('❌ Ошибка сервера:', response.status, errorData);
                } catch (e) {
                    console.error('❌ Не удалось распарсить ошибку сервера');
                }
                
                this.showNotification(
                    `Ошибка при сохранении товара: ${errorMessage}`, 
                    'error'
                );
            }
        } catch (error) {
            console.error('❌ Ошибка сохранения товара:', error);
            
            if (error.name === 'AbortError') {
                this.showNotification('Превышено время ожидания сервера', 'error');
            } else {
                this.handleNetworkError(error, 'при сохранении товара');
            }
        }
    }

    // ===== МОДАЛЬНЫЕ ОКНА =====

    showModal(modalId) {
        console.log('Показываем модальное окно:', modalId);
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'flex';
            console.log('Модальное окно показано:', modalId);
        } else {
            console.error('Модальное окно не найдено:', modalId);
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
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
                
                // Валидация формы
                if (!this.validateProductForm(e.target)) {
                    return;
                }
                
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

    setupAdminProductEventListeners() {
        // Обработчики для админ-товаров уже настроены через onclick
        // Но можем добавить дополнительные обработчики здесь если нужно
        console.log('🔧 Настроены обработчики событий для админ-товаров');
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

    // ===== ВАЛИДАЦИЯ =====

    validateProductForm(form) {
        console.log('🔍 Валидация формы товара...');
        
        const title = form.querySelector('#product-title').value.trim();
        const description = form.querySelector('#product-description').value.trim();
        const price = parseFloat(form.querySelector('#product-price').value);
        const photo = form.querySelector('#product-photo').files[0];
        
        // Проверяем название
        if (!title) {
            this.showNotification('Введите название товара', 'error');
            form.querySelector('#product-title').focus();
            return false;
        }
        
        if (title.length < 2) {
            this.showNotification('Название должно содержать минимум 2 символа', 'error');
            form.querySelector('#product-title').focus();
            return false;
        }
        
        // Проверяем описание
        if (!description) {
            this.showNotification('Введите описание товара', 'error');
            form.querySelector('#product-description').focus();
            return false;
        }
        
        if (description.length < 10) {
            this.showNotification('Описание должно содержать минимум 10 символов', 'error');
            form.querySelector('#product-description').focus();
            return false;
        }
        
        // Проверяем цену
        if (isNaN(price) || price <= 0) {
            this.showNotification('Введите корректную цену (больше 0)', 'error');
            form.querySelector('#product-price').focus();
            return false;
        }
        
        if (price > 1000000) {
            this.showNotification('Цена не может превышать 1,000,000 ₽', 'error');
            form.querySelector('#product-price').focus();
            return false;
        }
        
        // Проверяем фото (только для новых товаров)
        if (!this.editingProduct && !photo) {
            this.showNotification('Загрузите фото товара', 'error');
            form.querySelector('#product-photo').focus();
            return false;
        }
        
        // Проверяем размер файла фото
        if (photo && photo.size > 5 * 1024 * 1024) { // 5MB
            this.showNotification('Размер фото не должен превышать 5MB', 'error');
            form.querySelector('#product-photo').focus();
            return false;
        }
        
        // Проверяем тип файла фото
        if (photo && !photo.type.startsWith('image/')) {
            this.showNotification('Загрузите файл изображения', 'error');
            form.querySelector('#product-photo').focus();
            return false;
        }
        
        console.log('✅ Форма прошла валидацию');
        return true;
    }

    // ===== АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ =====

    setupAutoRefresh() {
        // Обновляем данные каждые 30 секунд
        this.autoRefreshInterval = setInterval(async () => {
            try {
                console.log('🔄 Автоматическое обновление данных...');
                await this.fetchProducts();
                
                // Обновляем текущую страницу если нужно
                if (this.currentPage === 'catalog') {
                    this.renderCatalogPage();
                } else if (this.currentPage === 'admin') {
                    await this.loadAdminProducts();
                    this.updateAdminStats();
                }
                
                console.log('✅ Данные обновлены автоматически');
            } catch (error) {
                console.error('❌ Ошибка автоматического обновления:', error);
            }
        }, 30000); // 30 секунд
        
        console.log('⏰ Автоматическое обновление настроено (каждые 30 секунд)');
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('⏹️ Автоматическое обновление остановлено');
        }
    }

    // ===== УВЕДОМЛЕНИЯ =====

    showNotification(message, type = 'info') {
        console.log(`🔔 Уведомление [${type}]:`, message);
        
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">
                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                </span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        // Добавляем стили если их нет
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    max-width: 300px;
                    padding: 12px 16px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    animation: slideIn 0.3s ease-out;
                    font-size: 14px;
                    line-height: 1.4;
                }
                
                .notification-success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                
                .notification-error {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
                
                .notification-info {
                    background: #d1ecf1;
                    color: #0c5460;
                    border: 1px solid #bee5eb;
                }
                
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .notification-icon {
                    font-size: 16px;
                    flex-shrink: 0;
                }
                
                .notification-message {
                    flex: 1;
                }
                
                .notification-close {
                    background: none;
                    border: none;
                    font-size: 18px;
                    cursor: pointer;
                    color: inherit;
                    opacity: 0.7;
                    padding: 0;
                    margin-left: 8px;
                }
                
                .notification-close:hover {
                    opacity: 1;
                }
                
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Добавляем уведомление на страницу
        document.body.appendChild(notification);
        
        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    // ===== ОБРАБОТКА ОШИБОК =====

    handleNetworkError(error, context = '') {
        console.error(`❌ Ошибка сети ${context}:`, error);
        
        let message = 'Ошибка соединения с сервером';
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            message = 'Не удается подключиться к серверу';
        } else if (error.name === 'TypeError' && error.message.includes('Load failed')) {
            message = 'Ошибка загрузки данных. Сервер может быть недоступен.';
        } else if (error.message.includes('404')) {
            message = 'Сервер не найден';
        } else if (error.message.includes('500')) {
            message = 'Ошибка сервера';
        } else if (error.message.includes('timeout')) {
            message = 'Превышено время ожидания';
        }
        
        this.showNotification(`${message} ${context}`, 'error');
    }

    // ===== ОЧИСТКА РЕСУРСОВ =====

    destroy() {
        console.log('🧹 Очистка ресурсов приложения...');
        
        // Останавливаем автоматическое обновление
        this.stopAutoRefresh();
        
        // Очищаем обработчики событий
        document.removeEventListener('beforeunload', this.destroy);
        
        console.log('✅ Ресурсы очищены');
    }
}

// Глобальные функции для onclick
function showAddProductModal() {
    if (window.mobileShopApp) {
        window.mobileShopApp.showAddProductModal();
    }
}

function editProduct(productId) {
    console.log('🔗 Вызов editProduct из глобальной функции:', productId);
    console.log('🔍 window.mobileShopApp:', window.mobileShopApp);
    
    if (window.mobileShopApp) {
        console.log('✅ Приложение найдено, вызываем editProduct');
        window.mobileShopApp.editProduct(productId);
    } else {
        console.error('❌ mobileShopApp не инициализирован');
        console.log('🔍 Попытка инициализации...');
        
        try {
            window.mobileShopApp = new MobileShopApp();
            console.log('✅ Приложение инициализировано, повторяем вызов');
            setTimeout(() => {
                window.mobileShopApp.editProduct(productId);
            }, 500); // Даем время на загрузку данных
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            alert('Ошибка инициализации приложения. Попробуйте обновить страницу.');
        }
    }
}

function restoreProduct(productId) {
    console.log('🔗 Вызов restoreProduct из глобальной функции:', productId);
    console.log('🔍 window.mobileShopApp:', window.mobileShopApp);
    
    if (window.mobileShopApp) {
        console.log('✅ Приложение найдено, вызываем restoreProduct');
        window.mobileShopApp.restoreProduct(productId);
    } else {
        console.error('❌ mobileShopApp не инициализирован');
        console.log('🔍 Попытка инициализации...');
        
        try {
            window.mobileShopApp = new MobileShopApp();
            console.log('✅ Приложение инициализировано, повторяем вызов');
            setTimeout(() => {
                window.mobileShopApp.restoreProduct(productId);
            }, 500);
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            alert('Ошибка инициализации приложения. Попробуйте обновить страницу.');
        }
    }
}

function deleteProduct(productId) {
    console.log('🔗 Вызов deleteProduct из глобальной функции:', productId);
    console.log('🔍 window.mobileShopApp:', window.mobileShopApp);
    
    if (window.mobileShopApp) {
        console.log('✅ Приложение найдено, вызываем deleteProduct');
        window.mobileShopApp.deleteProduct(productId);
    } else {
        console.error('❌ mobileShopApp не инициализирован');
        console.log('🔍 Попытка инициализации...');
        
        try {
            window.mobileShopApp = new MobileShopApp();
            console.log('✅ Приложение инициализировано, повторяем вызов');
            window.mobileShopApp.deleteProduct(productId);
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            alert('Ошибка инициализации приложения. Попробуйте обновить страницу.');
        }
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
    console.log('🚀 Инициализация приложения...');
    try {
        window.mobileShopApp = new MobileShopApp();
        console.log('✅ Приложение инициализировано успешно');
        console.log('🔍 mobileShopApp:', window.mobileShopApp);
    } catch (error) {
        console.error('❌ Ошибка инициализации приложения:', error);
        alert('Ошибка инициализации приложения: ' + error.message);
    }
});

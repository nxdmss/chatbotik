// ======================
// 🔹 Простая логика админских прав
// ======================

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

console.log('🚀 Загружается приложение версии SIMPLE - ТОЛЬКО ВАШ ID АДМИН');

class SimpleShopApp {
    constructor() {
        this.isAdmin = false;
        this.products = [];
        this.init();
    }

    async init() {
        console.log('🔧 Инициализация простого приложения...');
        
        // СТРОГАЯ ПРОВЕРКА АДМИНСКИХ ПРАВ
        await this.checkAdminRights();
        
        // Загружаем товары
        await this.loadProducts();
        
        // Рендерим интерфейс
        this.render();
        
        console.log('✅ Приложение инициализировано');
    }

    async checkAdminRights() {
        console.log('🔍 ПРОВЕРЯЕМ АДМИНСКИЕ ПРАВА...');
        
        const ADMIN_ID = '1593426947';
        let userId = null;
        
        try {
            // Проверяем Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {
                console.log('✅ Telegram WebApp найден');
                
                // Получаем user_id
                if (window.Telegram.WebApp.initDataUnsafe && 
                    window.Telegram.WebApp.initDataUnsafe.user && 
                    window.Telegram.WebApp.initDataUnsafe.user.id) {
                    
                    userId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
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
                console.log('🌐 Запущено в браузере - отладочный режим');
                this.isAdmin = true;
                userId = 'browser_debug';
                console.log('🔧 Админские права для отладки');
            }
            
            console.log('📊 РЕЗУЛЬТАТ:');
            console.log('   User ID:', userId);
            console.log('   Админ:', this.isAdmin ? 'ДА' : 'НЕТ');
            
        } catch (error) {
            console.error('❌ Ошибка проверки прав:', error);
            this.isAdmin = false;
        }
    }

    async loadProducts() {
        try {
            const response = await fetch('/webapp/products.json');
            if (response.ok) {
                this.products = await response.json();
                console.log('📦 Загружено товаров:', this.products.length);
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки товаров:', error);
            this.products = [];
        }
    }

    render() {
        const container = document.getElementById('app-container');
        if (!container) return;

        let html = `
            <div class="container">
                <header class="header">
                    <h1>🛍️ Каталог товаров</h1>
        `;

        // Показываем админ панель только если админ
        if (this.isAdmin) {
            html += `
                <div class="admin-panel" style="background: #ff6b6b; color: white; padding: 10px; margin: 10px 0; border-radius: 5px;">
                    <h3>👑 АДМИН ПАНЕЛЬ</h3>
                    <button onclick="app.addProduct()" class="btn btn-primary">➕ Добавить товар</button>
                    <button onclick="app.manageProducts()" class="btn btn-secondary">📝 Управление</button>
                </div>
            `;
        }

        html += `
                </header>
                
                <div class="products-grid">
        `;

        // Показываем товары
        this.products.forEach(product => {
            html += `
                <div class="product-card">
                    <img src="${product.photo || '/webapp/static/uploads/default.jpg'}" alt="${product.title}" onerror="this.src='/webapp/static/uploads/default.jpg'">
                    <h3>${product.title}</h3>
                    <p>${product.description}</p>
                    <div class="price">${product.price} ₽</div>
                    <div class="sizes">Размеры: ${product.sizes.join(', ')}</div>
                    
                    ${this.isAdmin ? `
                        <div class="admin-actions">
                            <button onclick="app.editProduct(${product.id})" class="btn btn-small">✏️</button>
                            <button onclick="app.deleteProduct(${product.id})" class="btn btn-small btn-danger">🗑️</button>
                        </div>
                    ` : ''}
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        container.innerHTML = html;
        
        // Показываем статус
        const status = this.isAdmin ? '👑 АДМИН' : '👤 КЛИЕНТ';
        console.log('🎯 Статус пользователя:', status);
    }

    addProduct() {
        if (!this.isAdmin) {
            alert('❌ У вас нет прав администратора');
            return;
        }
        alert('➕ Добавление товара (функция в разработке)');
    }

    editProduct(id) {
        if (!this.isAdmin) {
            alert('❌ У вас нет прав администратора');
            return;
        }
        alert(`✏️ Редактирование товара ${id} (функция в разработке)`);
    }

    deleteProduct(id) {
        if (!this.isAdmin) {
            alert('❌ У вас нет прав администратора');
            return;
        }
        alert(`🗑️ Удаление товара ${id} (функция в разработке)`);
    }

    manageProducts() {
        if (!this.isAdmin) {
            alert('❌ У вас нет прав администратора');
            return;
        }
        alert('📝 Управление товарами (функция в разработке)');
    }
}

// Запускаем приложение
const app = new SimpleShopApp();

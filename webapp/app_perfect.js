/**
 * ИДЕАЛЬНАЯ ВЕРСИЯ - Простая и рабочая
 */

const API_BASE = window.location.origin; // Автоматически определяем базовый URL

class ShopApp {
    constructor() {
        this.products = [];
        this.isAdmin = true; // Всегда админ для тестирования
        this.init();
    }

    async init() {
        console.log('🚀 Инициализация ShopApp');
        console.log('📍 API Base URL:', API_BASE);
        
        // Telegram WebApp
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }
        
        await this.loadProducts();
        this.render();
        this.setupEventListeners();
    }

    async loadProducts() {
        try {
            console.log('📦 Загружаем товары...');
            const response = await fetch(`${API_BASE}/webapp/products.json`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            this.products = await response.json();
            console.log(`✅ Загружено ${this.products.length} товаров`);
            return this.products;
        } catch (error) {
            console.error('❌ Ошибка загрузки товаров:', error);
            this.showNotification('Ошибка загрузки товаров', 'error');
            return [];
        }
    }

    async addProduct(productData) {
        try {
            console.log('➕ Добавляем товар:', productData);
            
            const response = await fetch(`${API_BASE}/webapp/admin/products`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(productData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ Товар добавлен:', result);
            
            this.showNotification('Товар добавлен успешно!', 'success');
            await this.loadProducts();
            this.render();
            
            return result;
        } catch (error) {
            console.error('❌ Ошибка добавления товара:', error);
            this.showNotification(`Ошибка добавления: ${error.message}`, 'error');
            throw error;
        }
    }

    async deleteProduct(productId) {
        try {
            console.log('🗑️ Удаляем товар ID:', productId);
            
            if (!confirm(`Удалить товар #${productId}?`)) {
                return;
            }
            
            const response = await fetch(`${API_BASE}/webapp/admin/products/${productId}?user_id=admin`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ Товар удален:', result);
            
            this.showNotification('Товар удален успешно!', 'success');
            await this.loadProducts();
            this.render();
            
            return result;
        } catch (error) {
            console.error('❌ Ошибка удаления товара:', error);
            this.showNotification(`Ошибка удаления: ${error.message}`, 'error');
            throw error;
        }
    }

    render() {
        const catalogContainer = document.getElementById('catalog-container');
        if (!catalogContainer) {
            console.error('❌ Контейнер каталога не найден');
            return;
        }

        catalogContainer.innerHTML = '';

        if (this.products.length === 0) {
            catalogContainer.innerHTML = '<p class="no-products">Товары не найдены</p>';
            return;
        }

        this.products.forEach(product => {
            const productCard = this.createProductCard(product);
            catalogContainer.appendChild(productCard);
        });

        console.log('✅ Отрисовано', this.products.length, 'товаров');
    }

    createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <img src="${product.photo || '/webapp/static/uploads/default.jpg'}" 
                 alt="${product.title}" 
                 onerror="this.src='/webapp/static/uploads/default.jpg'">
            <div class="product-info">
                <h3>${product.title}</h3>
                <p>${product.description || ''}</p>
                <p class="price">${product.price} ₽</p>
                ${product.sizes ? `<p class="sizes">Размеры: ${product.sizes.join(', ')}</p>` : ''}
            </div>
            ${this.isAdmin ? `
                <div class="admin-actions">
                    <button class="btn-delete" onclick="app.deleteProduct(${product.id})">
                        🗑️ Удалить
                    </button>
                </div>
            ` : ''}
        `;
        return card;
    }

    setupEventListeners() {
        // Кнопка добавления товара
        const addBtn = document.getElementById('add-product-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showAddProductForm());
        }

        // Форма добавления товара
        const form = document.getElementById('product-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleProductSubmit(e));
        }

        console.log('✅ Event listeners установлены');
    }

    showAddProductForm() {
        const modal = document.getElementById('product-modal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    hideAddProductForm() {
        const modal = document.getElementById('product-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    async handleProductSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        
        const productData = {
            title: formData.get('title'),
            description: formData.get('description'),
            price: parseFloat(formData.get('price')),
            sizes: formData.get('sizes').split(',').map(s => s.trim())
        };
        
        try {
            await this.addProduct(productData);
            form.reset();
            this.hideAddProductForm();
        } catch (error) {
            console.error('Ошибка отправки формы:', error);
        }
    }

    showNotification(message, type = 'info') {
        console.log(`${type === 'error' ? '❌' : '✅'} ${message}`);
        
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'error' ? '#f44336' : '#4CAF50'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Глобальная переменная для доступа из onclick
let app;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎬 DOM загружен, запускаем приложение');
    app = new ShopApp();
});

// Глобальная функция для удаления (для onclick)
window.deleteProduct = function(productId) {
    if (app) {
        app.deleteProduct(productId);
    } else {
        console.error('❌ Приложение не инициализировано');
    }
};

console.log('✅ app_perfect.js загружен');


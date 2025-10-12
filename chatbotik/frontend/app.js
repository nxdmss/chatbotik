/**
 * 🚀 TELEGRAM MINI APP - E-COMMERCE PLATFORM
 * ===========================================
 * Современный JavaScript для управления интерфейсом
 */

class TelegramECommerceApp {
    constructor() {
        this.tg = window.Telegram.WebApp
        this.products = []
        this.cart = []
        this.currentProductId = null
        
        this.init()
    }

    async init() {
        // Инициализируем Telegram WebApp
        this.tg.ready()
        this.tg.expand()
        
        // Загружаем данные пользователя
        this.user = this.tg.initDataUnsafe?.user
        console.log('Telegram user:', this.user)
        
        this.setupEventListeners()
        await this.loadProducts()
        this.updateCartUI()
        this.showTab('catalog')
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab
                this.showTab(tab)
            })
        })

        // Search
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.filterProducts(e.target.value)
        })

        // Category filter
        document.getElementById('categoryFilter').addEventListener('change', (e) => {
            this.filterByCategory(e.target.value)
        })

        // Add product button
        document.getElementById('addProductBtn').addEventListener('click', () => {
            this.openProductModal()
        })

        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal()
        })

        document.getElementById('closeOrderModal').addEventListener('click', () => {
            this.closeOrderModal()
        })

        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeModal()
        })

        document.getElementById('cancelOrderBtn').addEventListener('click', () => {
            this.closeOrderModal()
        })

        // Forms
        document.getElementById('productForm').addEventListener('submit', (e) => {
            e.preventDefault()
            this.saveProduct()
        })

        document.getElementById('orderForm').addEventListener('submit', (e) => {
            e.preventDefault()
            this.createOrder()
        })

        // Image upload
        document.getElementById('productImage').addEventListener('change', (e) => {
            this.handleImageUpload(e.target.files[0])
        })

        // Checkout button
        document.getElementById('checkoutBtn').addEventListener('click', () => {
            if (this.cart.length > 0) {
                this.openOrderModal()
            }
        })

        // Close modals on outside click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active')
                }
            })
        })
    }

    showTab(tabName) {
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active')
        })
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active')

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active')
        })
        document.getElementById(tabName).classList.add('active')

        // Load specific tab data
        if (tabName === 'cart') {
            this.updateCartUI()
        } else if (tabName === 'admin') {
            this.loadAdminProducts()
        }
    }

    async loadProducts() {
        try {
            this.showLoading(true)
            const response = await fetch('/api/products')
            this.products = await response.json()
            this.renderProducts()
        } catch (error) {
            this.showToast('Ошибка загрузки товаров', 'error')
            console.error('Error loading products:', error)
        } finally {
            this.showLoading(false)
        }
    }

    renderProducts() {
        const grid = document.getElementById('productsGrid')
        
        if (this.products.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-box-open"></i>
                    <h3>Товары не найдены</h3>
                    <p>В каталоге пока нет товаров</p>
                </div>
            `
            return
        }

        grid.innerHTML = this.products.map(product => `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image">
                    ${product.image_url ? 
                        `<img src="${product.image_url}" alt="${product.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                         <div class="product-placeholder" style="display:none;"><i class="fas fa-image"></i></div>` :
                        `<i class="fas fa-image"></i>`
                    }
                </div>
                <div class="product-info">
                    <h3 class="product-title">${product.title}</h3>
                    ${product.description ? `<p class="product-description">${product.description}</p>` : ''}
                    <div class="product-footer">
                        <span class="product-price">${product.price.toLocaleString()} ₽</span>
                        <button class="add-to-cart-btn" onclick="app.addToCart(${product.id})">
                            <i class="fas fa-plus"></i>
                            В корзину
                        </button>
                    </div>
                </div>
            </div>
        `).join('')
    }

    filterProducts(searchTerm) {
        const filtered = this.products.filter(product => 
            product.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (product.description && product.description.toLowerCase().includes(searchTerm.toLowerCase()))
        )
        this.renderFilteredProducts(filtered)
    }

    filterByCategory(category) {
        if (!category) {
            this.renderProducts()
            return
        }

        const filtered = this.products.filter(product => product.category === category)
        this.renderFilteredProducts(filtered)
    }

    renderFilteredProducts(products) {
        const grid = document.getElementById('productsGrid')
        
        if (products.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>Товары не найдены</h3>
                    <p>Попробуйте изменить поисковый запрос</p>
                </div>
            `
            return
        }

        grid.innerHTML = products.map(product => `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image">
                    ${product.image_url ? 
                        `<img src="${product.image_url}" alt="${product.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                         <div class="product-placeholder" style="display:none;"><i class="fas fa-image"></i></div>` :
                        `<i class="fas fa-image"></i>`
                    }
                </div>
                <div class="product-info">
                    <h3 class="product-title">${product.title}</h3>
                    ${product.description ? `<p class="product-description">${product.description}</p>` : ''}
                    <div class="product-footer">
                        <span class="product-price">${product.price.toLocaleString()} ₽</span>
                        <button class="add-to-cart-btn" onclick="app.addToCart(${product.id})">
                            <i class="fas fa-plus"></i>
                            В корзину
                        </button>
                    </div>
                </div>
            </div>
        `).join('')
    }

    addToCart(productId) {
        const product = this.products.find(p => p.id === productId)
        if (!product) return

        const existingItem = this.cart.find(item => item.product_id === productId)
        
        if (existingItem) {
            existingItem.quantity += 1
        } else {
            this.cart.push({
                product_id: productId,
                quantity: 1,
                product: product
            })
        }

        this.updateCartUI()
        this.showToast(`${product.title} добавлен в корзину`, 'success')
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.product_id !== productId)
        this.updateCartUI()
    }

    updateCartQuantity(productId, quantity) {
        if (quantity <= 0) {
            this.removeFromCart(productId)
            return
        }

        const item = this.cart.find(item => item.product_id === productId)
        if (item) {
            item.quantity = quantity
            this.updateCartUI()
        }
    }

    updateCartUI() {
        // Update cart count in header
        const cartCount = this.cart.reduce((sum, item) => sum + item.quantity, 0)
        document.querySelector('.cart-count').textContent = cartCount

        // Update cart items
        const cartItems = document.getElementById('cartItems')
        const totalPrice = document.querySelector('.total-price')
        
        if (this.cart.length === 0) {
            cartItems.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-shopping-cart"></i>
                    <h3>Корзина пуста</h3>
                    <p>Добавьте товары из каталога</p>
                </div>
            `
            totalPrice.textContent = '0 ₽'
            document.getElementById('checkoutBtn').disabled = true
            return
        }

        cartItems.innerHTML = this.cart.map(item => `
            <div class="cart-item">
                <img class="cart-item-image" src="${item.product.image_url || ''}" 
                     alt="${item.product.title}"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="cart-placeholder" style="display:none;"><i class="fas fa-image"></i></div>
                <div class="cart-item-info">
                    <h4 class="cart-item-title">${item.product.title}</h4>
                    <p class="cart-item-price">${item.product.price.toLocaleString()} ₽</p>
                    <div class="cart-item-controls">
                        <button class="quantity-btn" onclick="app.updateCartQuantity(${item.product_id}, ${item.quantity - 1})">
                            <i class="fas fa-minus"></i>
                        </button>
                        <input type="number" class="quantity-input" value="${item.quantity}" 
                               min="1" onchange="app.updateCartQuantity(${item.product_id}, parseInt(this.value))">
                        <button class="quantity-btn" onclick="app.updateCartQuantity(${item.product_id}, ${item.quantity + 1})">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="remove-btn" onclick="app.removeFromCart(${item.product_id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('')

        // Update total
        const total = this.cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0)
        totalPrice.textContent = `${total.toLocaleString()} ₽`
        document.getElementById('checkoutBtn').disabled = false
    }

    async loadAdminProducts() {
        try {
            this.showLoading(true)
            const response = await fetch('/api/products')
            const products = await response.json()
            this.renderAdminProducts(products)
        } catch (error) {
            this.showToast('Ошибка загрузки товаров', 'error')
            console.error('Error loading admin products:', error)
        } finally {
            this.showLoading(false)
        }
    }

    renderAdminProducts(products) {
        const container = document.getElementById('adminProductsList')
        
        if (products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-box-open"></i>
                    <h3>Товары не найдены</h3>
                    <p>Добавьте первый товар</p>
                </div>
            `
            return
        }

        container.innerHTML = products.map(product => `
            <div class="admin-product-card">
                <div class="admin-product-content">
                    <div class="admin-product-image">
                        ${product.image_url ? 
                            `<img src="${product.image_url}" alt="${product.title}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                             <div class="product-placeholder" style="display:none;"><i class="fas fa-image"></i></div>` :
                            `<i class="fas fa-image"></i>`
                        }
                    </div>
                    <div class="admin-product-info">
                        <h3 class="admin-product-title">${product.title}</h3>
                        <p class="admin-product-price">${product.price.toLocaleString()} ₽</p>
                        <p class="admin-product-description">${product.description || 'Нет описания'}</p>
                        <span class="admin-product-category">${this.formatCategoryName(product.category)}</span>
                    </div>
                    <div class="admin-product-actions">
                        <button class="edit-btn" onclick="app.editProduct(${product.id})">
                            <i class="fas fa-edit"></i>
                            Редактировать
                        </button>
                        <button class="delete-btn" onclick="app.deleteProduct(${product.id})">
                            <i class="fas fa-trash"></i>
                            Удалить
                        </button>
                    </div>
                </div>
            </div>
        `).join('')
    }

    formatCategoryName(category) {
        const names = {
            'electronics': 'Электроника',
            'clothing': 'Одежда',
            'food': 'Еда',
            'books': 'Книги',
            'general': 'Общее'
        }
        return names[category] || category
    }

    openProductModal(productId = null) {
        this.currentProductId = productId
        const modal = document.getElementById('productModal')
        const title = document.getElementById('modalTitle')
        const form = document.getElementById('productForm')
        
        title.textContent = productId ? 'Редактировать товар' : 'Добавить товар'
        
        if (productId) {
            const product = this.products.find(p => p.id === productId)
            if (product) {
                document.getElementById('productTitle').value = product.title
                document.getElementById('productPrice').value = product.price
                document.getElementById('productCategory').value = product.category
                document.getElementById('productDescription').value = product.description || ''
            }
        } else {
            form.reset()
            document.getElementById('imagePreview').innerHTML = ''
        }
        
        modal.classList.add('active')
    }

    closeModal() {
        document.getElementById('productModal').classList.remove('active')
        this.currentProductId = null
    }

    openOrderModal() {
        document.getElementById('orderModal').classList.add('active')
    }

    closeOrderModal() {
        document.getElementById('orderModal').classList.remove('active')
    }

    async handleImageUpload(file) {
        if (!file) return

        const reader = new FileReader()
        reader.onload = (e) => {
            const preview = document.getElementById('imagePreview')
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`
        }
        reader.readAsDataURL(file)
    }

    async saveProduct() {
        try {
            this.showLoading(true)
            
            const formData = new FormData()
            formData.append('title', document.getElementById('productTitle').value)
            formData.append('price', document.getElementById('productPrice').value)
            formData.append('category', document.getElementById('productCategory').value)
            formData.append('description', document.getElementById('productDescription').value)
            
            const url = this.currentProductId ? 
                `/api/products/${this.currentProductId}` : 
                '/api/products'
            
            const method = this.currentProductId ? 'PUT' : 'POST'
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'X-Admin-Password': 'admin123'
                },
                body: formData
            })
            
            if (response.ok) {
                this.showToast(
                    this.currentProductId ? 'Товар обновлен' : 'Товар добавлен', 
                    'success'
                )
                this.closeModal()
                await this.loadProducts()
                await this.loadAdminProducts()
            } else {
                throw new Error('Failed to save product')
            }
        } catch (error) {
            this.showToast('Ошибка сохранения товара', 'error')
            console.error('Error saving product:', error)
        } finally {
            this.showLoading(false)
        }
    }

    editProduct(productId) {
        this.openProductModal(productId)
    }

    async deleteProduct(productId) {
        if (!confirm('Вы уверены, что хотите удалить этот товар?')) {
            return
        }

        try {
            this.showLoading(true)
            
            const response = await fetch(`/api/products/${productId}`, {
                method: 'DELETE',
                headers: {
                    'X-Admin-Password': 'admin123'
                }
            })
            
            if (response.ok) {
                this.showToast('Товар удален', 'success')
                await this.loadProducts()
                await this.loadAdminProducts()
            } else {
                throw new Error('Failed to delete product')
            }
        } catch (error) {
            this.showToast('Ошибка удаления товара', 'error')
            console.error('Error deleting product:', error)
        } finally {
            this.showLoading(false)
        }
    }

    async createOrder() {
        try {
            this.showLoading(true)
            
            const orderData = {
                type: 'order',
                order: {
                    customer_name: document.getElementById('customerName').value,
                    customer_phone: document.getElementById('customerPhone').value,
                    customer_address: document.getElementById('customerAddress').value,
                    items: this.cart.map(item => ({
                        product_id: item.product_id,
                        quantity: item.quantity
                    }))
                }
            }
            
            // Отправляем данные в Telegram
            this.tg.sendData(JSON.stringify(orderData))
            
            this.showToast('Заказ отправлен!', 'success')
            this.cart = []
            this.updateCartUI()
            this.closeOrderModal()
            document.getElementById('orderForm').reset()
            
        } catch (error) {
            this.showToast('Ошибка создания заказа', 'error')
            console.error('Error creating order:', error)
        } finally {
            this.showLoading(false)
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay')
        overlay.classList.toggle('active', show)
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer')
        const toast = document.createElement('div')
        toast.className = `toast ${type}`
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `
        
        container.appendChild(toast)
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove()
        }, 5000)
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        }
        return icons[type] || 'info-circle'
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TelegramECommerceApp()
})

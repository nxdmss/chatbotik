/**
 * 🎨 ПРОФЕССИОНАЛЬНЫЕ UI КОМПОНЕНТЫ
 * ==================================
 * Готовые компоненты для красивого интерфейса
 */

// ===== ЗАГРУЗЧИКИ И ИНДИКАТОРЫ =====

class UIComponents {
    /**
     * Показывает красивый loader с сообщением
     */
    static showLoader(message = 'Загрузка...') {
        const existingLoader = document.getElementById('app-loader');
        if (existingLoader) {
            existingLoader.remove();
        }
        
        const loader = document.createElement('div');
        loader.id = 'app-loader';
        loader.className = 'loader-overlay';
        loader.innerHTML = `
            <div class="loader-container">
                <div class="loader-spinner"></div>
                <div class="loader-text">${message}</div>
                <div class="loader-progress">
                    <div class="loader-progress-bar"></div>
                </div>
            </div>
        `;
        document.body.appendChild(loader);
        
        // Анимация прогресс-бара
        setTimeout(() => {
            const progressBar = loader.querySelector('.loader-progress-bar');
            if (progressBar) {
                progressBar.style.width = '70%';
            }
        }, 100);
        
        return loader;
    }
    
    /**
     * Скрывает loader
     */
    static hideLoader() {
        const loader = document.getElementById('app-loader');
        if (loader) {
            loader.classList.add('fade-out');
            setTimeout(() => loader.remove(), 300);
        }
    }
    
    /**
     * Показывает прогресс-бар для загрузки
     */
    static showProgressBar(progress = 0, message = '') {
        let progressBar = document.getElementById('app-progress-bar');
        
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.id = 'app-progress-bar';
            progressBar.className = 'progress-bar-container';
            progressBar.innerHTML = `
                <div class="progress-bar-message"></div>
                <div class="progress-bar-track">
                    <div class="progress-bar-fill"></div>
                    <div class="progress-bar-percentage">0%</div>
                </div>
            `;
            document.body.appendChild(progressBar);
        }
        
        const fill = progressBar.querySelector('.progress-bar-fill');
        const percentage = progressBar.querySelector('.progress-bar-percentage');
        const messageEl = progressBar.querySelector('.progress-bar-message');
        
        if (fill) fill.style.width = `${progress}%`;
        if (percentage) percentage.textContent = `${Math.round(progress)}%`;
        if (messageEl) messageEl.textContent = message;
        
        return progressBar;
    }
    
    /**
     * Скрывает прогресс-бар
     */
    static hideProgressBar() {
        const progressBar = document.getElementById('app-progress-bar');
        if (progressBar) {
            progressBar.classList.add('fade-out');
            setTimeout(() => progressBar.remove(), 300);
        }
    }
    
    /**
     * Показывает toast уведомление
     */
    static showToast(message, type = 'info', duration = 3000) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close">&times;</button>
        `;
        
        document.body.appendChild(toast);
        
        // Показываем с анимацией
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Закрытие
        const closeToast = () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        };
        
        toast.querySelector('.toast-close').addEventListener('click', closeToast);
        
        // Автозакрытие
        if (duration > 0) {
            setTimeout(closeToast, duration);
        }
        
        return toast;
    }
    
    /**
     * Показывает красивую модалку с подтверждением
     */
    static async showConfirm(title, message, confirmText = 'Да', cancelText = 'Нет') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-header">
                        <h3>${title}</h3>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline modal-cancel">${cancelText}</button>
                        <button class="btn btn-primary modal-confirm">${confirmText}</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            setTimeout(() => modal.classList.add('show'), 10);
            
            const closeModal = (result) => {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.remove();
                    resolve(result);
                }, 300);
            };
            
            modal.querySelector('.modal-confirm').addEventListener('click', () => closeModal(true));
            modal.querySelector('.modal-cancel').addEventListener('click', () => closeModal(false));
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal(false);
            });
        });
    }
    
    /**
     * Показывает skeleton loader для карточек товаров
     */
    static showProductsSkeleton(count = 6) {
        const container = document.getElementById('products-grid');
        if (!container) return;
        
        container.innerHTML = '';
        
        for (let i = 0; i < count; i++) {
            const skeleton = document.createElement('div');
            skeleton.className = 'product-card-skeleton';
            skeleton.innerHTML = `
                <div class="skeleton-image"></div>
                <div class="skeleton-content">
                    <div class="skeleton-title"></div>
                    <div class="skeleton-description"></div>
                    <div class="skeleton-price"></div>
                    <div class="skeleton-button"></div>
                </div>
            `;
            container.appendChild(skeleton);
        }
    }
    
    /**
     * Создает красивую пустую страницу
     */
    static createEmptyState(icon, title, message, action = null) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div class="empty-state-icon">${icon}</div>
            <h3 class="empty-state-title">${title}</h3>
            <p class="empty-state-message">${message}</p>
            ${action ? `<button class="btn btn-primary empty-state-action">${action.text}</button>` : ''}
        `;
        
        if (action && action.callback) {
            const btn = emptyState.querySelector('.empty-state-action');
            btn.addEventListener('click', action.callback);
        }
        
        return emptyState;
    }
    
    /**
     * Показывает индикатор загрузки на кнопке
     */
    static showButtonLoading(button, text = 'Загрузка...') {
        if (!button) return;
        
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.classList.add('btn-loading');
        button.innerHTML = `
            <span class="btn-spinner"></span>
            <span>${text}</span>
        `;
    }
    
    /**
     * Скрывает индикатор загрузки на кнопке
     */
    static hideButtonLoading(button) {
        if (!button) return;
        
        button.disabled = false;
        button.classList.remove('btn-loading');
        button.innerHTML = button.dataset.originalText || 'OK';
        delete button.dataset.originalText;
    }
    
    /**
     * Создает красивый badge
     */
    static createBadge(text, type = 'primary') {
        const badge = document.createElement('span');
        badge.className = `badge badge-${type}`;
        badge.textContent = text;
        return badge;
    }
    
    /**
     * Анимация появления элемента
     */
    static animateIn(element, animation = 'fadeInUp') {
        element.classList.add('animate__animated', `animate__${animation}`);
        
        return new Promise((resolve) => {
            element.addEventListener('animationend', () => {
                element.classList.remove('animate__animated', `animate__${animation}`);
                resolve();
            }, { once: true });
        });
    }
    
    /**
     * Анимация исчезновения элемента
     */
    static animateOut(element, animation = 'fadeOutDown') {
        element.classList.add('animate__animated', `animate__${animation}`);
        
        return new Promise((resolve) => {
            element.addEventListener('animationend', () => {
                element.remove();
                resolve();
            }, { once: true });
        });
    }
}

// ===== СТИЛИ ДЛЯ КОМПОНЕНТОВ =====

const COMPONENT_STYLES = `
/* Loader Overlay */
.loader-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.3s ease;
}

.loader-overlay.fade-out {
    animation: fadeOut 0.3s ease;
}

.loader-container {
    background: #2d2d2d;
    border-radius: 16px;
    padding: 32px;
    text-align: center;
    min-width: 200px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.loader-spinner {
    width: 48px;
    height: 48px;
    margin: 0 auto 16px;
    border: 4px solid rgba(59, 130, 246, 0.2);
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loader-text {
    color: #ffffff;
    font-size: 16px;
    margin-bottom: 16px;
}

.loader-progress {
    width: 100%;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
}

.loader-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    width: 0%;
    transition: width 0.5s ease;
    border-radius: 2px;
}

/* Progress Bar */
.progress-bar-container {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #2d2d2d;
    padding: 16px 24px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    z-index: 9999;
    min-width: 300px;
    animation: slideDown 0.3s ease;
}

.progress-bar-container.fade-out {
    animation: slideUp 0.3s ease;
}

@keyframes slideDown {
    from { transform: translateX(-50%) translateY(-100%); }
    to { transform: translateX(-50%) translateY(0); }
}

@keyframes slideUp {
    from { transform: translateX(-50%) translateY(0); }
    to { transform: translateX(-50%) translateY(-100%); }
}

.progress-bar-message {
    color: #ffffff;
    font-size: 14px;
    margin-bottom: 8px;
    text-align: center;
}

.progress-bar-track {
    position: relative;
    width: 100%;
    height: 24px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
}

.progress-bar-fill {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    border-radius: 12px;
    transition: width 0.3s ease;
}

.progress-bar-percentage {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* Toast */
.toast {
    position: fixed;
    bottom: -100px;
    left: 50%;
    transform: translateX(-50%);
    background: #2d2d2d;
    padding: 16px 20px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    gap: 12px;
    max-width: 90%;
    z-index: 9998;
    transition: bottom 0.3s ease;
}

.toast.show {
    bottom: 20px;
}

.toast-icon {
    font-size: 24px;
    flex-shrink: 0;
}

.toast-message {
    color: #ffffff;
    font-size: 14px;
    flex: 1;
}

.toast-close {
    background: none;
    border: none;
    color: #888;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.toast-success { border-left: 4px solid #10b981; }
.toast-error { border-left: 4px solid #ef4444; }
.toast-warning { border-left: 4px solid #f59e0b; }
.toast-info { border-left: 4px solid #3b82f6; }

/* Skeleton Loader */
.product-card-skeleton {
    background: #2d2d2d;
    border-radius: 12px;
    overflow: hidden;
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.skeleton-image {
    width: 100%;
    padding-top: 100%;
    background: linear-gradient(90deg, #2d2d2d 25%, #3d3d3d 50%, #2d2d2d 75%);
    background-size: 200% 100%;
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.skeleton-content {
    padding: 12px;
}

.skeleton-title,
.skeleton-description,
.skeleton-price,
.skeleton-button {
    background: linear-gradient(90deg, #2d2d2d 25%, #3d3d3d 50%, #2d2d2d 75%);
    background-size: 200% 100%;
    animation: shimmer 2s infinite;
    border-radius: 4px;
    margin-bottom: 8px;
}

.skeleton-title { height: 16px; width: 80%; }
.skeleton-description { height: 12px; width: 100%; }
.skeleton-price { height: 14px; width: 60%; }
.skeleton-button { height: 36px; width: 100%; border-radius: 6px; }

/* Empty State */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    grid-column: 1 / -1;
}

.empty-state-icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-state-title {
    color: #ffffff;
    font-size: 20px;
    margin-bottom: 8px;
}

.empty-state-message {
    color: #888;
    font-size: 14px;
    margin-bottom: 24px;
}

/* Button Loading */
.btn-loading {
    position: relative;
    pointer-events: none;
    opacity: 0.7;
}

.btn-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    margin-right: 8px;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.badge-primary { background: #3b82f6; color: #ffffff; }
.badge-success { background: #10b981; color: #ffffff; }
.badge-warning { background: #f59e0b; color: #ffffff; }
.badge-danger { background: #ef4444; color: #ffffff; }
.badge-secondary { background: #6b7280; color: #ffffff; }

/* Modal Dialog */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10001;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.modal-overlay.show {
    opacity: 1;
}

.modal-dialog {
    background: #2d2d2d;
    border-radius: 16px;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    transform: scale(0.9);
    transition: transform 0.3s ease;
}

.modal-overlay.show .modal-dialog {
    transform: scale(1);
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid #333;
}

.modal-header h3 {
    margin: 0;
    color: #ffffff;
    font-size: 18px;
}

.modal-body {
    padding: 20px;
}

.modal-body p {
    margin: 0;
    color: #cccccc;
    font-size: 14px;
    line-height: 1.6;
}

.modal-footer {
    padding: 20px;
    border-top: 1px solid #333;
    display: flex;
    gap: 12px;
    justify-content: flex-end;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}
`;

// Добавляем стили на страницу
const styleElement = document.createElement('style');
styleElement.textContent = COMPONENT_STYLES;
document.head.appendChild(styleElement);

// Экспорт для использования
window.UIComponents = UIComponents;

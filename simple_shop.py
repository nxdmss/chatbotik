#!/usr/bin/env python3
import json
import socket
import os
import uuid
import base64
from urllib.parse import urlparse

# Настройки
PORT = 8000
DATA_FILE = 'shop_data.json'
UPLOADS_DIR = 'uploads'
ADMIN_PASSWORD = "admin123"

# Создаем папку для загрузок
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def save_photo(photo_data, filename):
    """Сохранение фотографии"""
    try:
        # Убираем data:image/jpeg;base64, если есть
        if ',' in photo_data:
            photo_data = photo_data.split(',')[1]
        
        # Декодируем base64
        photo_bytes = base64.b64decode(photo_data)
        
        # Сохраняем файл
        filepath = os.path.join(UPLOADS_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(photo_bytes)
        
        print(f"📷 Фото сохранено: {filename}")
        return f"/uploads/{filename}"
    except Exception as e:
        print(f"❌ Ошибка сохранения фото: {e}")
        return ""

# Загрузка товаров
def load_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Начальные товары
    products = [
        {"id": 1, "title": "Футболка", "price": 1500, "description": "Крутая футболка", "image": "👕"},
        {"id": 2, "title": "Джинсы", "price": 3000, "description": "Стильные джинсы", "image": "👖"},
        {"id": 3, "title": "Кроссовки", "price": 5000, "description": "Удобные кроссовки", "image": "👟"}
    ]
    save_products(products)
    return products

# Сохранение товаров
def save_products(products):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# Глобальные переменные
products = load_products()

# Обработка запросов
def handle_request(client_socket):
    try:
        request = client_socket.recv(8192).decode('utf-8')
        if not request:
            return
        
        lines = request.split('\n')
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 3:
            return
        
        method, path, protocol = parts[0], parts[1], parts[2]
        parsed_path = urlparse(path)
        
        print(f"📥 {method} {path}")
        
        # API товаров
        if parsed_path.path == '/api/products' and method == 'GET':
            response_body = json.dumps(products, ensure_ascii=False)
            response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        
        # Проверка админ пароля
        elif parsed_path.path == '/api/admin/check' and method == 'POST':
            content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
            post_data = request.split('\r\n\r\n')[1][:content_length]
            data = json.loads(post_data)
            password = data.get('password', '')
            
            is_admin = password == ADMIN_PASSWORD
            response_body = json.dumps({"success": is_admin}, ensure_ascii=False)
            response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        
        # Добавление товара
        elif parsed_path.path == '/api/products' and method == 'POST':
            try:
                admin_password = ""
                for line in lines:
                    if line.startswith('X-Admin-Password:'):
                        admin_password = line.split(':')[1].strip()
                        break
                
                if admin_password != ADMIN_PASSWORD:
                    response_body = json.dumps({"success": False, "error": "Access denied"}, ensure_ascii=False)
                    response = f"""HTTP/1.1 403 Forbidden
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                else:
                    # Получаем длину контента
                    content_length = 0
                    for line in lines:
                        if line.startswith('Content-Length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    if content_length > 0:
                        post_data = request.split('\r\n\r\n')[1][:content_length]
                        data = json.loads(post_data)
                        
                        max_id = max([p['id'] for p in products]) if products else 0
                        
                        # Обработка фотографии
                        photo_url = ""
                        if data.get('photo'):
                            filename = f"product_{max_id + 1}_{uuid.uuid4().hex[:8]}.jpg"
                            photo_url = save_photo(data['photo'], filename)
                        
                        new_product = {
                            "id": max_id + 1,
                            "title": data.get('title', 'Новый товар'),
                            "price": int(data.get('price', 0)),
                            "description": data.get('description', ''),
                            "image": data.get('image', '📦'),
                            "photo": photo_url
                        }
                        
                        products.append(new_product)
                        save_products(products)
                        print(f"✅ Добавлен товар: {new_product['title']}")
                        
                        response_body = json.dumps({"success": True, "product": new_product}, ensure_ascii=False)
                        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                    else:
                        response_body = json.dumps({"success": False, "error": "No data received"}, ensure_ascii=False)
                        response = f"""HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
            except Exception as e:
                print(f"❌ Ошибка добавления товара: {e}")
                response_body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
                response = f"""HTTP/1.1 500 Internal Server Error
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        
        # Удаление товара
        elif parsed_path.path.startswith('/api/products/') and method == 'DELETE':
            admin_password = ""
            for line in lines:
                if line.startswith('X-Admin-Password:'):
                    admin_password = line.split(':')[1].strip()
                    break
            
            if admin_password != ADMIN_PASSWORD:
                response_body = json.dumps({"success": False, "error": "Access denied"}, ensure_ascii=False)
                response = f"""HTTP/1.1 403 Forbidden
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
            else:
                product_id = int(parsed_path.path.split('/')[-1])
                for i, product in enumerate(products):
                    if product['id'] == product_id:
                        del products[i]
                        save_products(products)
                        print(f"✅ Удален товар ID: {product_id}")
                        
                        response_body = json.dumps({"success": True}, ensure_ascii=False)
                        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                        break
        
        # Статические файлы (фотографии)
        elif parsed_path.path.startswith('/uploads/'):
            try:
                file_path = parsed_path.path[1:]  # Убираем первый /
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    response = f"""HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Length: {len(file_content)}

"""
                    response = response.encode() + file_content
                else:
                    response_body = "<h1>404 - File not found</h1>"
                    response = f"""HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}

{response_body}"""
            except Exception as e:
                print(f"❌ Ошибка загрузки файла: {e}")
                response_body = "<h1>500 - Server Error</h1>"
                response = f"""HTTP/1.1 500 Internal Server Error
Content-Type: text/html; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}

{response_body}"""
        
        # Тестовая страница
        elif parsed_path.path == '/test':
            with open('test_add.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            response = f"""HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: {len(html_content.encode('utf-8'))}

{html_content}"""
        
        # Главная страница
        elif parsed_path.path == '/':
            html_content = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Магазин</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #000; color: #fff; font-family: Arial, sans-serif; padding: 15px; }
        .search { padding: 8px; background: #111; border: 1px solid #333; border-radius: 5px; color: #fff; width: 100%; margin-bottom: 15px; }
        .btn { background: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
        .btn.admin { background: #2196F3; }
        .btn.danger { background: #f44336; }
        .tab-content { display: none; min-height: calc(100vh - 120px); padding-bottom: 80px; }
        .tab-content.active { display: block; }
        .products { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; max-width: 800px; margin: 0 auto; }
        .product { border: 1px solid #333; padding: 12px; border-radius: 8px; height: 200px; position: relative; }
        .product-image { height: 80px; background: #222; border-radius: 6px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; overflow: hidden; }
        .product-image img { max-width: 100%; max-height: 100%; object-fit: cover; }
        .product-image span { font-size: 2em; }
        .product-title { font-size: 13px; font-weight: bold; margin-bottom: 4px; }
        .product-price { color: #4CAF50; font-weight: bold; margin-bottom: 8px; }
        .cart-content { max-width: 800px; margin: 0 auto; }
        .product-controls { display: flex; gap: 6px; align-items: center; }
        .qty-btn { background: #333; color: white; border: none; width: 20px; height: 20px; border-radius: 3px; font-size: 10px; cursor: pointer; }
        .qty-input { width: 35px; text-align: center; background: #222; border: 1px solid #333; color: #fff; padding: 2px; font-size: 10px; }
        .add-btn { background: #4CAF50; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 10px; flex: 1; cursor: pointer; }
        .admin-controls { position: absolute; top: 5px; right: 5px; display: none; gap: 3px; }
        .admin-controls.show { display: flex; }
        .admin-btn { border: none; padding: 3px 6px; border-radius: 3px; font-size: 10px; cursor: pointer; }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #111; border-top: 1px solid #333; padding: 10px; display: flex; justify-content: space-around; z-index: 999; }
        .nav-btn { background: #333; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; flex: 1; margin: 0 5px; }
        .nav-btn.active { background: #4CAF50; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; }
        .modal.show { display: block; }
        .modal-content { background: #111; margin: 10% auto; padding: 20px; border-radius: 10px; width: 80%; max-width: 500px; }
        .form-group { margin: 10px 0; }
        .form-input { width: 100%; padding: 8px; background: #222; border: 1px solid #333; color: #fff; border-radius: 4px; }
        .close-btn { background: #666; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <!-- Каталог -->
    <div id="catalogTab" class="tab-content active">
        <input type="text" placeholder="🔍 Поиск..." id="search" class="search">
        <div id="products" class="products"></div>
    </div>

    <!-- Корзина -->
    <div id="cartTab" class="tab-content">
        <div class="cart-content">
            <h2 style="text-align: center; margin-bottom: 20px;">🛒 Корзина</h2>
            <div id="cartContent"></div>
        </div>
    </div>

    <!-- Админ -->
    <div id="adminTab" class="tab-content">
        <div class="cart-content">
            <h2 style="text-align: center; margin-bottom: 20px;">🔐 Админ Панель</h2>
            <div id="adminLogin">
                <div class="form-group">
                    <input type="password" id="adminPassword" placeholder="Введите пароль админа" class="form-input">
                </div>
                <button onclick="checkAdminPassword()" class="btn">Войти</button>
            </div>
            <div id="adminPanel" style="display:none;">
                <div style="color: #4CAF50; margin-bottom: 15px; text-align: center;">✅ Админ авторизован</div>
                <button onclick="addNew()" class="btn" style="width: 100%; margin-bottom: 10px;">➕ Добавить товар</button>
            </div>
        </div>
    </div>

    <!-- Нижняя навигация -->
    <div class="bottom-nav">
        <button onclick="showCatalog()" class="nav-btn active" id="catalogBtn">📦 Каталог</button>
        <button onclick="showCart()" class="nav-btn" id="cartBtn">🛒 Корзина <span id="cartCount">0</span></button>
        <button onclick="showAdmin()" class="nav-btn" id="adminBtn">🔐 Админ</button>
    </div>


    <!-- Добавление товара -->
    <div id="addModal" class="modal">
        <div class="modal-content">
            <h2>➕ Добавить товар</h2>
            <form id="addForm">
                <div class="form-group">
                    <input type="text" id="addName" placeholder="Название" class="form-input">
                </div>
                <div class="form-group">
                    <input type="number" id="addPrice" placeholder="Цена" class="form-input">
                </div>
                <div class="form-group">
                    <input type="text" id="addEmoji" placeholder="Эмодзи" class="form-input">
                </div>
                <div class="form-group">
                    <label style="display:block;margin-bottom:5px;">📷 Фотография:</label>
                    <input type="file" id="addPhoto" accept="image/*" class="form-input">
                    <div id="photoPreview" style="margin-top:10px;text-align:center;"></div>
                </div>
                <button type="submit" class="btn">💾 Сохранить</button>
            </form>
            <button onclick="closeAdd()" class="close-btn">Отмена</button>
        </div>
    </div>

    <script>
        let products = [];
        let cart = [];
        let isAdmin = false;
        let adminPassword = '';
        let currentPhoto = null;

        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                products = await response.json();
                renderProducts();
            } catch (error) {
                console.error('Ошибка загрузки товаров:', error);
            }
        }

        function updateCartCount() {
            const count = cart.reduce((sum, item) => sum + item.quantity, 0);
            document.getElementById('cartCount').textContent = count;
        }

        function showCatalog() {
            document.getElementById('catalogTab').classList.add('active');
            document.getElementById('cartTab').classList.remove('active');
            document.getElementById('adminTab').classList.remove('active');
            document.getElementById('catalogBtn').classList.add('active');
            document.getElementById('cartBtn').classList.remove('active');
            document.getElementById('adminBtn').classList.remove('active');
        }

        function showCart() {
            document.getElementById('catalogTab').classList.remove('active');
            document.getElementById('cartTab').classList.add('active');
            document.getElementById('adminTab').classList.remove('active');
            document.getElementById('catalogBtn').classList.remove('active');
            document.getElementById('cartBtn').classList.add('active');
            document.getElementById('adminBtn').classList.remove('active');
            loadCart();
        }

        function showAdmin() {
            document.getElementById('catalogTab').classList.remove('active');
            document.getElementById('cartTab').classList.remove('active');
            document.getElementById('adminTab').classList.add('active');
            document.getElementById('catalogBtn').classList.remove('active');
            document.getElementById('cartBtn').classList.remove('active');
            document.getElementById('adminBtn').classList.add('active');
        }

        function renderProducts() {
            let html = products.map(p => `
                <div class="product">
                    <div class="admin-controls ${isAdmin ? 'show' : ''}">
                        <button onclick="deleteProduct(${p.id})" class="admin-btn danger">🗑️</button>
                    </div>
                    <div class="product-image">
                        ${p.photo ? `<img src="${p.photo}" alt="${p.title}">` : `<span>${p.image}</span>`}
                    </div>
                    <div class="product-title">${p.title}</div>
                    <div class="product-price">${p.price} ₽</div>
                    <div class="product-controls">
                        <button onclick="changeQty(${p.id}, -1)" class="qty-btn">-</button>
                        <input type="number" id="qty_${p.id}" value="1" min="1" max="99" class="qty-input">
                        <button onclick="changeQty(${p.id}, 1)" class="qty-btn">+</button>
                        <button onclick="addToCart(${p.id})" class="add-btn">➕</button>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('products').innerHTML = html;
        }

        function changeQty(id, change) {
            const input = document.getElementById('qty_' + id);
            let value = parseInt(input.value) + change;
            if (value < 1) value = 1;
            if (value > 99) value = 99;
            input.value = value;
        }

        function addToCart(productId) {
            const quantity = parseInt(document.getElementById('qty_' + productId).value);
            const product = products.find(p => p.id === productId);
            
            const existingItem = cart.find(item => item.id === productId);
            if (existingItem) {
                existingItem.quantity += quantity;
            } else {
                cart.push({
                    id: productId,
                    title: product.title,
                    price: product.price,
                    image: product.image,
                    quantity: quantity
                });
            }
            
            updateCartCount();
            alert(`✅ Добавлено в корзину: ${product.title} x${quantity}`);
            document.getElementById('qty_' + productId).value = 1;
        }

        function loadCart() {
            const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            document.getElementById('cartContent').innerHTML = cart.map(item => `
                <div style="border:1px solid #333;padding:10px;margin:5px 0;border-radius:5px;">
                    <strong>${item.title}</strong> - ${item.price} ₽ × ${item.quantity} = ${item.price * item.quantity} ₽
                </div>
            `).join('') + `<div style="margin-top:10px;font-weight:bold;">Итого: ${total} ₽</div>`;
        }


        async function checkAdminPassword() {
            try {
                const password = document.getElementById('adminPassword').value;
                
                const response = await fetch('/api/admin/check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: password})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    isAdmin = true;
                    adminPassword = password;
                    document.getElementById('adminLogin').style.display = 'none';
                    document.getElementById('adminPanel').style.display = 'block';
                    document.getElementById('adminPassword').value = '';
                    renderProducts();
                } else {
                    alert('❌ Неверный пароль!');
                    document.getElementById('adminPassword').value = '';
                }
            } catch (error) {
                console.error('Ошибка проверки пароля:', error);
            }
        }


        function addNew() {
            if (!isAdmin) {
                alert('❌ Нужны админ права!');
                return;
            }
            
            document.getElementById('addName').value = '';
            document.getElementById('addPrice').value = '';
            document.getElementById('addEmoji').value = '📦';
            document.getElementById('addPhoto').value = '';
            document.getElementById('photoPreview').innerHTML = '<div style="color:#666;">Выберите фотографию</div>';
            currentPhoto = null;
            document.getElementById('addModal').classList.add('show');
        }

        document.getElementById('addPhoto').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    currentPhoto = e.target.result;
                    const preview = document.getElementById('photoPreview');
                    preview.innerHTML = `<img src="${currentPhoto}" alt="Предпросмотр" style="max-width:150px;max-height:100px;border-radius:5px;">`;
                };
                reader.readAsDataURL(file);
            }
        });

        document.getElementById('addForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!isAdmin) {
                alert('❌ Нужны админ права!');
                return;
            }
            
            const data = {
                title: document.getElementById('addName').value,
                price: parseInt(document.getElementById('addPrice').value),
                description: '',
                image: document.getElementById('addEmoji').value || '📦'
            };
            
            if (currentPhoto) {
                data.photo = currentPhoto;
            }
            
            try {
                const response = await fetch('/api/products', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Admin-Password': adminPassword
                    },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    alert('✅ Товар добавлен!');
                    closeAdd();
                    loadProducts();
                } else {
                    alert('❌ Ошибка добавления!');
                }
            } catch (error) {
                alert('❌ Ошибка сети: ' + error.message);
            }
        });

        async function deleteProduct(id) {
            if (!isAdmin) {
                alert('❌ Нужны админ права!');
                return;
            }
            
            if (!confirm('Удалить товар?')) return;
            
            try {
                const response = await fetch(`/api/products/${id}`, {
                    method: 'DELETE',
                    headers: {'X-Admin-Password': adminPassword}
                });
                if (response.ok) {
                    alert('✅ Товар удален!');
                    loadProducts();
                }
            } catch (error) {
                alert('❌ Ошибка удаления');
            }
        }

        function closeAdd() {
            document.getElementById('addModal').classList.remove('show');
            currentPhoto = null;
            document.getElementById('addPhoto').value = '';
        }

        // Закрытие модальных окон
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('show');
            }
        });

        // Загрузка товаров при старте
        loadProducts();
        updateCartCount();
    </script>
</body>
</html>"""
            response = f"""HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: {len(html_content.encode('utf-8'))}

{html_content}"""
        else:
            response_body = "<h1>404 - Not Found</h1>"
            response = f"""HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}

{response_body}"""
        
        client_socket.send(response.encode('utf-8'))
        client_socket.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        client_socket.close()

# Запуск сервера
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('', PORT))
        server_socket.listen(5)
        
        print(f"🚀 Простой магазин запущен на http://localhost:{PORT}")
        print(f"🔑 Админ пароль: {ADMIN_PASSWORD}")
        print(f"📦 Товаров: {len(products)}")
        print("🛑 Для остановки: Ctrl+C")
        
        while True:
            client_socket, addr = server_socket.accept()
            handle_request(client_socket)
            
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        save_products(products)
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СЕРВЕР С ПОСТОЯННЫМ СОХРАНЕНИЕМ
Товары сохраняются навсегда в файл
"""

import json
import socket
import uuid
import os

# Порт
PORT = 8000

# Файл для сохранения данных
DATA_FILE = 'products_data.json'

# Функция загрузки товаров из файла
def load_products():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('products', [])
        else:
            # Создаем начальные товары
            initial_products = [
                {"id": 1, "title": "Футболка", "price": 1500, "description": "Крутая футболка", "image": "👕", "active": True},
                {"id": 2, "title": "Джинсы", "price": 3000, "description": "Стильные джинсы", "image": "👖", "active": True},
                {"id": 3, "title": "Кроссовки", "price": 5000, "description": "Удобные кроссовки", "image": "👟", "active": True},
                {"id": 4, "title": "Куртка", "price": 4000, "description": "Теплая куртка", "image": "🧥", "active": True}
            ]
            save_products(initial_products)
            return initial_products
    except Exception as e:
        print(f"Ошибка загрузки товаров: {e}")
        return []

# Функция сохранения товаров в файл
def save_products(products):
    try:
        data = {
            'products': products,
            'last_saved': str(uuid.uuid4())  # Для отслеживания изменений
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено {len(products)} товаров в {DATA_FILE}")
    except Exception as e:
        print(f"Ошибка сохранения товаров: {e}")

# Загружаем товары при запуске
products = load_products()

# Корзины пользователей (в памяти)
carts = {}

def get_cart(user_id):
    if user_id not in carts:
        carts[user_id] = []
    return carts[user_id]

def handle_request(client_socket):
    global products  # Используем глобальную переменную
    
    request = client_socket.recv(4096).decode('utf-8')
    if not request:
        return
    
    lines = request.split('\n')
    first_line = lines[0]
    parts = first_line.split()
    if len(parts) < 3:
        return
    
    method, path, protocol = parts[0], parts[1], parts[2]
    print(f"📥 {method} {path}")
    
    # API товаров
    if path == '/api/products':
        response_body = json.dumps(products, ensure_ascii=False)
        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # API корзины
    elif path.startswith('/api/cart/'):
        user_id = path.split('/')[-1]
        if method == 'GET':
            cart = get_cart(user_id)
            response_body = json.dumps(cart, ensure_ascii=False)
            response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        elif method == 'POST':
            content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
            post_data = request.split('\r\n\r\n')[1][:content_length]
            data = json.loads(post_data)
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            
            cart = get_cart(user_id)
            product = None
            for p in products:
                if p['id'] == product_id:
                    product = p
                    break
            
            if product:
                existing_item = None
                for item in cart:
                    if item['product_id'] == product_id:
                        existing_item = item
                        break
                
                if existing_item:
                    existing_item['quantity'] += quantity
                else:
                    cart.append({
                        'id': str(uuid.uuid4()),
                        'product_id': product_id,
                        'title': product['title'],
                        'price': product['price'],
                        'image': product['image'],
                        'quantity': quantity
                    })
                
                response_body = json.dumps({"success": True, "cart": cart}, ensure_ascii=False)
                response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
            else:
                response_body = json.dumps({"success": False, "error": "Product not found"}, ensure_ascii=False)
                response = f"""HTTP/1.1 404 Not Found
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Добавление товара
    elif path == '/api/products' and method == 'POST':
        content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
        post_data = request.split('\r\n\r\n')[1][:content_length]
        data = json.loads(post_data)
        
        # Находим максимальный ID
        max_id = max([p['id'] for p in products]) if products else 0
        
        new_product = {
            "id": max_id + 1,
            "title": data.get('title', 'Новый товар'),
            "price": data.get('price', 0),
            "description": data.get('description', ''),
            "image": data.get('image', '📦'),
            "active": True
        }
        
        products.append(new_product)
        save_products(products)  # Сохраняем в файл
        
        response_body = json.dumps({"success": True, "product": new_product}, ensure_ascii=False)
        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Редактирование товара
    elif path.startswith('/api/products/') and method == 'PUT':
        product_id = int(path.split('/')[-1])
        content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
        post_data = request.split('\r\n\r\n')[1][:content_length]
        data = json.loads(post_data)
        
        for i, product in enumerate(products):
            if product['id'] == product_id:
                products[i] = {
                    "id": product_id,
                    "title": data.get('title', product['title']),
                    "price": data.get('price', product['price']),
                    "description": data.get('description', product['description']),
                    "image": data.get('image', product.get('image', '📦')),
                    "active": True
                }
                save_products(products)  # Сохраняем в файл
                
                response_body = json.dumps({"success": True, "product": products[i]}, ensure_ascii=False)
                response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                break
        else:
            response_body = json.dumps({"success": False, "error": "Product not found"}, ensure_ascii=False)
            response = f"""HTTP/1.1 404 Not Found
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Удаление товара (РЕАЛЬНОЕ УДАЛЕНИЕ ИЗ ФАЙЛА)
    elif path.startswith('/api/products/') and method == 'DELETE':
        product_id = int(path.split('/')[-1])
        
        for i, product in enumerate(products):
            if product['id'] == product_id:
                del products[i]
                save_products(products)  # Сохраняем в файл
                
                response_body = json.dumps({"success": True}, ensure_ascii=False)
                response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                break
        else:
            response_body = json.dumps({"success": False, "error": "Product not found"}, ensure_ascii=False)
            response = f"""HTTP/1.1 404 Not Found
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Главная страница
    elif path == '/':
        html_content = """<!DOCTYPE html>
<html><head><title>Магазин с Сохранением</title></head>
<body style="background:#000;color:#fff;font-family:Arial;margin:0;padding:15px;">
<h1 style="text-align:center;margin-bottom:20px;">🛍️ Магазин с Сохранением</h1>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
<input type="text" placeholder="🔍 Поиск..." id="search" style="padding:8px;background:#111;border:1px solid #333;border-radius:5px;color:#fff;width:200px;">
<button onclick="openCart()" style="background:#4CAF50;color:white;border:none;padding:8px 15px;border-radius:5px;">🛒 Корзина <span id="cartCount">0</span></button>
<button onclick="toggleAdmin()" style="background:#2196F3;color:white;border:none;padding:8px 15px;border-radius:5px;">⚙️ Админ</button>
</div>

<!-- ЖЕСТКАЯ ПРИВЯЗКА - ВСЕГДА 2 СТОЛБИКА -->
<div id="products" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:800px;margin:0 auto;"></div>

<div id="cartModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:1000;">
<div style="background:#111;margin:10% auto;padding:20px;border-radius:10px;width:80%;max-width:500px;">
<h2>🛒 Корзина</h2>
<div id="cartContent"></div>
<button onclick="closeCart()" style="background:#666;color:white;border:none;padding:10px 20px;border-radius:5px;">Закрыть</button>
</div>
</div>

<div id="editModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:1000;">
<div style="background:#111;margin:10% auto;padding:20px;border-radius:10px;width:80%;max-width:400px;">
<h2 id="editTitle">✏️ Редактировать</h2>
<form id="editForm">
<input type="hidden" id="editId">
<input type="text" id="editName" placeholder="Название" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<input type="number" id="editPrice" placeholder="Цена" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<input type="text" id="editDesc" placeholder="Описание" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<input type="text" id="editEmoji" placeholder="Эмодзи" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<button type="submit" style="background:#4CAF50;color:white;border:none;padding:10px 20px;border-radius:5px;width:100%;margin:10px 0;">💾 Сохранить НАВСЕГДА</button>
</form>
<button onclick="closeEdit()" style="background:#666;color:white;border:none;padding:10px 20px;border-radius:5px;width:100%;">Отмена</button>
</div>
</div>

<script>
let products = [];
let cart = [];
let userId = 'user_' + Math.random().toString(36).substr(2, 9);
let isAdmin = false;

async function loadProducts() {
    const response = await fetch('/api/products');
    products = await response.json();
    renderProducts();
}

function renderProducts() {
    let html = products.map(p => `
        <div style="border:1px solid #333;padding:12px;border-radius:8px;height:200px;position:relative;">
            <div style="position:absolute;top:5px;right:5px;display:${isAdmin ? 'flex' : 'none'};gap:3px;">
                <button onclick="editProduct(${p.id})" style="background:#ff9800;color:white;border:none;padding:3px 6px;border-radius:3px;font-size:10px;">✏️</button>
                <button onclick="deleteProduct(${p.id})" style="background:#f44336;color:white;border:none;padding:3px 6px;border-radius:3px;font-size:10px;">🗑️</button>
            </div>
            <div style="height:60px;background:#222;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:2em;margin-bottom:8px;">${p.image}</div>
            <div style="font-size:13px;font-weight:bold;margin-bottom:4px;">${p.title}</div>
            <div style="color:#ccc;font-size:10px;margin-bottom:6px;">${p.description}</div>
            <div style="color:#4CAF50;font-weight:bold;margin-bottom:8px;">${p.price} ₽</div>
            <div style="display:flex;gap:6px;align-items:center;">
                <button onclick="changeQty(${p.id}, -1)" style="background:#333;color:white;border:none;width:20px;height:20px;border-radius:3px;font-size:10px;">-</button>
                <input type="number" id="qty_${p.id}" value="1" min="1" max="99" style="width:35px;text-align:center;background:#222;border:1px solid #333;color:#fff;padding:2px;font-size:10px;">
                <button onclick="changeQty(${p.id}, 1)" style="background:#333;color:white;border:none;width:20px;height:20px;border-radius:3px;font-size:10px;">+</button>
                <button onclick="addToCart(${p.id})" style="background:#4CAF50;color:white;border:none;padding:4px 8px;border-radius:4px;font-size:10px;flex:1;">➕</button>
            </div>
        </div>
    `).join('');
    
    if (isAdmin) {
        html += `
            <div onclick="addNew()" style="border:2px dashed #555;padding:12px;border-radius:8px;height:200px;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;">
                <div style="font-size:2em;color:#666;margin-bottom:8px;">➕</div>
                <div style="color:#666;font-size:12px;">Добавить товар</div>
            </div>
        `;
    }
    
    document.getElementById('products').innerHTML = html;
}

function changeQty(id, change) {
    const input = document.getElementById('qty_' + id);
    let value = parseInt(input.value) + change;
    if (value < 1) value = 1;
    if (value > 99) value = 99;
    input.value = value;
}

async function addToCart(productId) {
    const quantity = parseInt(document.getElementById('qty_' + productId).value);
    const response = await fetch('/api/cart/' + userId, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: productId, quantity: quantity})
    });
    if (response.ok) {
        const result = await response.json();
        cart = result.cart;
        updateCartCount();
        alert('✅ Товар добавлен в корзину!');
        document.getElementById('qty_' + productId).value = 1;
    }
}

function updateCartCount() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById('cartCount').textContent = count;
}

function openCart() {
    document.getElementById('cartModal').style.display = 'block';
    loadCart();
}

function closeCart() {
    document.getElementById('cartModal').style.display = 'none';
}

async function loadCart() {
    const response = await fetch('/api/cart/' + userId);
    cart = await response.json();
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.getElementById('cartContent').innerHTML = cart.map(item => `
        <div style="border:1px solid #333;padding:10px;margin:5px 0;border-radius:5px;">
            <strong>${item.title}</strong> - ${item.price} ₽ × ${item.quantity} = ${item.price * item.quantity} ₽
        </div>
    `).join('') + `<div style="margin-top:10px;font-weight:bold;">Итого: ${total} ₽</div>`;
}

function toggleAdmin() {
    isAdmin = !isAdmin;
    alert(isAdmin ? '👑 Админ режим включен' : '👤 Обычный режим');
    renderProducts();
}

function editProduct(id) {
    const product = products.find(p => p.id === id);
    document.getElementById('editId').value = id;
    document.getElementById('editName').value = product.title;
    document.getElementById('editPrice').value = product.price;
    document.getElementById('editDesc').value = product.description;
    document.getElementById('editEmoji').value = product.image;
    document.getElementById('editTitle').textContent = '✏️ Редактировать';
    document.getElementById('editModal').style.display = 'block';
}

function addNew() {
    document.getElementById('editId').value = '';
    document.getElementById('editName').value = '';
    document.getElementById('editPrice').value = '';
    document.getElementById('editDesc').value = '';
    document.getElementById('editEmoji').value = '📦';
    document.getElementById('editTitle').textContent = '➕ Добавить товар';
    document.getElementById('editModal').style.display = 'block';
}

document.getElementById('editForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const id = document.getElementById('editId').value;
    const isEdit = id !== '';
    
    const data = {
        title: document.getElementById('editName').value,
        price: parseInt(document.getElementById('editPrice').value),
        description: document.getElementById('editDesc').value,
        image: document.getElementById('editEmoji').value || '📦',
        active: true
    };
    
    try {
        let response;
        if (isEdit) {
            response = await fetch(`/api/products/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch('/api/products', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            alert(isEdit ? '✅ Товар обновлен НАВСЕГДА!' : '✅ Товар добавлен НАВСЕГДА!');
            closeEdit();
            loadProducts();
        }
    } catch (error) {
        alert('❌ Ошибка');
    }
});

async function deleteProduct(id) {
    if (!confirm('Удалить товар НАВСЕГДА из файла?')) return;
    
    try {
        const response = await fetch(`/api/products/${id}`, {method: 'DELETE'});
        if (response.ok) {
            alert('✅ Товар удален НАВСЕГДА из файла!');
            loadProducts();
        }
    } catch (error) {
        alert('❌ Ошибка');
    }
}

function closeEdit() {
    document.getElementById('editModal').style.display = 'none';
}

loadProducts();
</script>
</body></html>"""
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

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen(5)
    
    print(f"🌐 Сервер с сохранением запущен на http://localhost:{PORT}")
    print(f"📱 Магазин: http://localhost:{PORT}")
    print(f"💾 Данные сохраняются в файл: {DATA_FILE}")
    print(f"📦 Загружено товаров: {len(products)}")
    print("🛑 Для остановки: Ctrl+C")
    
    try:
        while True:
            client_socket, addr = server_socket.accept()
            handle_request(client_socket)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        print(f"💾 Финальное сохранение {len(products)} товаров...")
        save_products(products)
        server_socket.close()

if __name__ == "__main__":
    start_server()

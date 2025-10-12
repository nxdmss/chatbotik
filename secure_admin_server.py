#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
БЕЗОПАСНЫЙ СЕРВЕР С АДМИНКОЙ ПО ПАРОЛЮ
"""

import json
import socket
import uuid
import os
import base64
import hashlib
from urllib.parse import urlparse, parse_qs

# Порт
PORT = 8000
DATA_FILE = 'products_data.json'
UPLOADS_DIR = 'uploads'

# АДМИН ПАРОЛЬ (измени на свой!)
ADMIN_PASSWORD = "admin123"  # ЗАМЕНИ НА СВОЙ ПАРОЛЬ!

# Создаем папку для загрузок
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

def load_products():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('products', [])
        else:
            initial_products = [
                {"id": 1, "title": "Футболка", "price": 1500, "description": "Крутая футболка", "image": "👕", "photo": "", "active": True},
                {"id": 2, "title": "Джинсы", "price": 3000, "description": "Стильные джинсы", "image": "👖", "photo": "", "active": True},
                {"id": 3, "title": "Кроссовки", "price": 5000, "description": "Удобные кроссовки", "image": "👟", "photo": "", "active": True},
                {"id": 4, "title": "Куртка", "price": 4000, "description": "Теплая куртка", "image": "🧥", "photo": "", "active": True}
            ]
            save_products(initial_products)
            return initial_products
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

def save_products(products):
    try:
        data = {
            'products': products,
            'last_saved': str(uuid.uuid4())
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено {len(products)} товаров в {DATA_FILE}")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def save_photo(photo_data, filename):
    try:
        if ',' in photo_data:
            photo_data = photo_data.split(',')[1]
        photo_bytes = base64.b64decode(photo_data)
        filepath = os.path.join(UPLOADS_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(photo_bytes)
        return f"/uploads/{filename}"
    except Exception as e:
        print(f"Ошибка сохранения фото: {e}")
        return ""

def check_admin_password(password):
    """Проверка админ пароля"""
    return password == ADMIN_PASSWORD

products = load_products()
carts = {}

def get_cart(user_id):
    if user_id not in carts:
        carts[user_id] = []
    return carts[user_id]

def handle_request(client_socket):
    global products
    
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
    
    # API товаров GET
    if parsed_path.path == '/api/products' and method == 'GET':
        response_body = json.dumps(products, ensure_ascii=False)
        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # API корзины
    elif parsed_path.path.startswith('/api/cart/'):
        user_id = parsed_path.path.split('/')[-1]
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
                        'photo': product.get('photo', ''),
                        'quantity': quantity
                    })
                
                response_body = json.dumps({"success": True, "cart": cart}, ensure_ascii=False)
                response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # ПРОВЕРКА АДМИН ПАРОЛЯ
    elif parsed_path.path == '/api/admin/check' and method == 'POST':
        content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
        post_data = request.split('\r\n\r\n')[1][:content_length]
        data = json.loads(post_data)
        password = data.get('password', '')
        
        is_admin = check_admin_password(password)
        response_body = json.dumps({"success": is_admin}, ensure_ascii=False)
        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # ДОБАВЛЕНИЕ ТОВАРА (ТОЛЬКО ДЛЯ АДМИНА)
    elif parsed_path.path == '/api/products' and method == 'POST':
        try:
            # Проверяем пароль в заголовке
            admin_password = ""
            for line in lines:
                if line.startswith('X-Admin-Password:'):
                    admin_password = line.split(':')[1].strip()
                    break
            
            if not check_admin_password(admin_password):
                response_body = json.dumps({"success": False, "error": "Access denied"}, ensure_ascii=False)
                response = f"""HTTP/1.1 403 Forbidden
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
            else:
                content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
                post_data = request.split('\r\n\r\n')[1][:content_length]
                data = json.loads(post_data)
                
                max_id = max([p['id'] for p in products]) if products else 0
                
                photo_url = ""
                if data.get('photo'):
                    filename = f"product_{max_id + 1}_{uuid.uuid4().hex[:8]}.jpg"
                    photo_url = save_photo(data['photo'], filename)
                
                new_product = {
                    "id": max_id + 1,
                    "title": data.get('title', 'Новый товар'),
                    "price": data.get('price', 0),
                    "description": data.get('description', ''),
                    "image": data.get('image', '📦'),
                    "photo": photo_url,
                    "active": True
                }
                
                products.append(new_product)
                save_products(products)
                print(f"✅ АДМИН добавил товар: {new_product['title']}")
                
                response_body = json.dumps({"success": True, "product": new_product}, ensure_ascii=False)
                response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        except Exception as e:
            response_body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
            response = f"""HTTP/1.1 500 Internal Server Error
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # РЕДАКТИРОВАНИЕ ТОВАРА (ТОЛЬКО ДЛЯ АДМИНА)
    elif parsed_path.path.startswith('/api/products/') and method == 'PUT':
        # Проверяем пароль
        admin_password = ""
        for line in lines:
            if line.startswith('X-Admin-Password:'):
                admin_password = line.split(':')[1].strip()
                break
        
        if not check_admin_password(admin_password):
            response_body = json.dumps({"success": False, "error": "Access denied"}, ensure_ascii=False)
            response = f"""HTTP/1.1 403 Forbidden
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        else:
            product_id = int(parsed_path.path.split('/')[-1])
            content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
            post_data = request.split('\r\n\r\n')[1][:content_length]
            data = json.loads(post_data)
            
            for i, product in enumerate(products):
                if product['id'] == product_id:
                    photo_url = product.get('photo', '')
                    if data.get('photo'):
                        filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.jpg"
                        photo_url = save_photo(data['photo'], filename)
                    
                    products[i] = {
                        "id": product_id,
                        "title": data.get('title', product['title']),
                        "price": data.get('price', product['price']),
                        "description": data.get('description', product['description']),
                        "image": data.get('image', product.get('image', '📦')),
                        "photo": photo_url,
                        "active": True
                    }
                    save_products(products)
                    print(f"✅ АДМИН обновил товар: {products[i]['title']}")
                    
                    response_body = json.dumps({"success": True, "product": products[i]}, ensure_ascii=False)
                    response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                    break
    
    # УДАЛЕНИЕ ТОВАРА (ТОЛЬКО ДЛЯ АДМИНА)
    elif parsed_path.path.startswith('/api/products/') and method == 'DELETE':
        # Проверяем пароль
        admin_password = ""
        for line in lines:
            if line.startswith('X-Admin-Password:'):
                admin_password = line.split(':')[1].strip()
                break
        
        if not check_admin_password(admin_password):
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
                    print(f"✅ АДМИН удалил товар ID: {product_id}")
                    
                    response_body = json.dumps({"success": True}, ensure_ascii=False)
                    response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
                    break
    
    # Статические файлы (фотографии)
    elif parsed_path.path.startswith('/uploads/'):
        file_path = parsed_path.path[1:]
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
    
    # Главная страница
    elif parsed_path.path == '/':
        html_content = """<!DOCTYPE html>
<html><head><title>Безопасный Магазин</title></head>
<body style="background:#000;color:#fff;font-family:Arial;margin:0;padding:15px;">
<h1 style="text-align:center;margin-bottom:20px;">🛍️ Безопасный Магазин</h1>
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
<input type="text" placeholder="🔍 Поиск..." id="search" style="padding:8px;background:#111;border:1px solid #333;border-radius:5px;color:#fff;width:200px;">
<button onclick="openCart()" style="background:#4CAF50;color:white;border:none;padding:8px 15px;border-radius:5px;">🛒 Корзина <span id="cartCount">0</span></button>
<button onclick="toggleAdmin()" style="background:#2196F3;color:white;border:none;padding:8px 15px;border-radius:5px;">🔐 Админ</button>
</div>

<div id="products" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:800px;margin:0 auto;"></div>

<div id="cartModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:1000;">
<div style="background:#111;margin:10% auto;padding:20px;border-radius:10px;width:80%;max-width:500px;">
<h2>🛒 Корзина</h2>
<div id="cartContent"></div>
<button onclick="closeCart()" style="background:#666;color:white;border:none;padding:10px 20px;border-radius:5px;">Закрыть</button>
</div>
</div>

<div id="adminModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:1000;">
<div style="background:#111;margin:10% auto;padding:30px;border-radius:10px;width:80%;max-width:400px;">
<h2 style="text-align:center;margin-bottom:20px;">🔐 Админ Панель</h2>
<div id="adminLogin" style="text-align:center;">
<input type="password" id="adminPassword" placeholder="Введите пароль админа" style="width:100%;padding:12px;background:#222;border:1px solid #333;color:#fff;border-radius:5px;margin-bottom:15px;font-size:16px;">
<button onclick="checkAdminPassword()" style="background:#4CAF50;color:white;border:none;padding:12px 25px;border-radius:5px;font-size:16px;width:100%;">Войти</button>
<button onclick="closeAdmin()" style="background:#666;color:white;border:none;padding:8px 15px;border-radius:5px;margin-top:10px;">Отмена</button>
</div>
<div id="adminPanel" style="display:none;">
<div style="text-align:center;margin-bottom:20px;">
<span style="color:#4CAF50;">✅ Админ авторизован</span>
<button onclick="logoutAdmin()" style="background:#f44336;color:white;border:none;padding:5px 10px;border-radius:3px;margin-left:10px;font-size:12px;">Выйти</button>
</div>
<button onclick="addNew()" style="background:#4CAF50;color:white;border:none;padding:10px 20px;border-radius:5px;width:100%;margin:5px 0;">➕ Добавить товар</button>
</div>
</div>
</div>

<div id="editModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:1000;">
<div style="background:#111;margin:5% auto;padding:20px;border-radius:10px;width:90%;max-width:500px;max-height:90vh;overflow-y:auto;">
<h2 id="editTitle">✏️ Редактировать</h2>
<form id="editForm">
<input type="hidden" id="editId">
<input type="text" id="editName" placeholder="Название" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<input type="number" id="editPrice" placeholder="Цена" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<input type="text" id="editDesc" placeholder="Описание" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<input type="text" id="editEmoji" placeholder="Эмодзи" style="width:100%;padding:8px;margin:5px 0;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<div style="margin:10px 0;">
<label style="display:block;margin-bottom:5px;">📷 Фотография:</label>
<input type="file" id="editPhoto" accept="image/*" style="width:100%;padding:8px;background:#222;border:1px solid #333;color:#fff;border-radius:4px;">
<div id="photoPreview" style="margin-top:10px;text-align:center;"></div>
</div>
<button type="submit" style="background:#4CAF50;color:white;border:none;padding:10px 20px;border-radius:5px;width:100%;margin:10px 0;">💾 Сохранить</button>
</form>
<button onclick="closeEdit()" style="background:#666;color:white;border:none;padding:10px 20px;border-radius:5px;width:100%;">Отмена</button>
</div>
</div>

<script>
let products = [];
let cart = [];
let userId = 'user_' + Math.random().toString(36).substr(2, 9);
let isAdmin = false;
let adminPassword = '';
let currentPhoto = null;

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
            <div style="height:60px;background:#222;border-radius:6px;display:flex;align-items:center;justify-content:center;margin-bottom:8px;overflow:hidden;">
                ${p.photo ? `<img src="${p.photo}" alt="${p.title}" style="max-width:100%;max-height:100%;object-fit:cover;">` : `<span style="font-size:2em;">${p.image}</span>`}
            </div>
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
    document.getElementById('adminModal').style.display = 'block';
}

async function checkAdminPassword() {
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
}

function logoutAdmin() {
    isAdmin = false;
    adminPassword = '';
    document.getElementById('adminLogin').style.display = 'block';
    document.getElementById('adminPanel').style.display = 'none';
    renderProducts();
}

function closeAdmin() {
    document.getElementById('adminModal').style.display = 'none';
    document.getElementById('adminPassword').value = '';
}

function editProduct(id) {
    if (!isAdmin) {
        alert('❌ Нужны админ права!');
        return;
    }
    
    const product = products.find(p => p.id === id);
    document.getElementById('editId').value = id;
    document.getElementById('editName').value = product.title;
    document.getElementById('editPrice').value = product.price;
    document.getElementById('editDesc').value = product.description;
    document.getElementById('editEmoji').value = product.image;
    document.getElementById('editTitle').textContent = '✏️ Редактировать';
    
    const preview = document.getElementById('photoPreview');
    if (product.photo) {
        preview.innerHTML = `<img src="${product.photo}" alt="Текущее фото" style="max-width:150px;max-height:100px;border-radius:5px;">`;
    } else {
        preview.innerHTML = '<div style="color:#666;">Нет фотографии</div>';
    }
    
    document.getElementById('editModal').style.display = 'block';
}

function addNew() {
    if (!isAdmin) {
        alert('❌ Нужны админ права!');
        return;
    }
    
    document.getElementById('editId').value = '';
    document.getElementById('editName').value = '';
    document.getElementById('editPrice').value = '';
    document.getElementById('editDesc').value = '';
    document.getElementById('editEmoji').value = '📦';
    document.getElementById('editTitle').textContent = '➕ Добавить товар';
    document.getElementById('photoPreview').innerHTML = '<div style="color:#666;">Выберите фотографию</div>';
    document.getElementById('editModal').style.display = 'block';
}

document.getElementById('editPhoto').addEventListener('change', function(e) {
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

document.getElementById('editForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!isAdmin) {
        alert('❌ Нужны админ права!');
        return;
    }
    
    const id = document.getElementById('editId').value;
    const isEdit = id !== '';
    
    const data = {
        title: document.getElementById('editName').value,
        price: parseInt(document.getElementById('editPrice').value),
        description: document.getElementById('editDesc').value,
        image: document.getElementById('editEmoji').value || '📦',
        active: true
    };
    
    if (currentPhoto) {
        data.photo = currentPhoto;
    }
    
    try {
        let response;
        if (isEdit) {
            response = await fetch(`/api/products/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Password': adminPassword
                },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch('/api/products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Password': adminPassword
                },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            alert(isEdit ? '✅ Товар обновлен!' : '✅ Товар добавлен!');
            closeEdit();
            loadProducts();
        } else {
            const error = await response.text();
            alert('❌ Ошибка: ' + error);
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
    
    if (!confirm('Удалить товар НАВСЕГДА?')) return;
    
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
        alert('❌ Ошибка');
    }
}

function closeEdit() {
    document.getElementById('editModal').style.display = 'none';
    currentPhoto = null;
    document.getElementById('editPhoto').value = '';
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
    
    if isinstance(response, str):
        client_socket.send(response.encode('utf-8'))
    else:
        client_socket.send(response)
    client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen(5)
    
    print(f"🔐 БЕЗОПАСНЫЙ сервер запущен на http://localhost:{PORT}")
    print(f"📱 Магазин: http://localhost:{PORT}")
    print(f"🔑 АДМИН ПАРОЛЬ: {ADMIN_PASSWORD}")
    print(f"📷 Фотографии: {UPLOADS_DIR}")
    print(f"💾 Данные: {DATA_FILE}")
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

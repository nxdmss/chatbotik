#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ФИНАЛЬНЫЙ СЕРВЕР
С полным редактированием и жесткой привязкой интерфейса
"""

import json
import socket
import os
import uuid

# Порт
PORT = 8000

# Хранилище данных
products = [
    {
        "id": 1, 
        "title": "Футболка", 
        "price": 1500, 
        "description": "Крутая футболка из хлопка",
        "image": "👕",
        "active": True
    },
    {
        "id": 2, 
        "title": "Джинсы", 
        "price": 3000, 
        "description": "Стильные джинсы скинни",
        "image": "👖", 
        "active": True
    },
    {
        "id": 3, 
        "title": "Кроссовки", 
        "price": 5000, 
        "description": "Удобные беговые кроссовки",
        "image": "👟", 
        "active": True
    },
    {
        "id": 4, 
        "title": "Куртка", 
        "price": 4000, 
        "description": "Теплая зимняя куртка",
        "image": "🧥", 
        "active": True
    },
    {
        "id": 5, 
        "title": "Рюкзак", 
        "price": 2500, 
        "description": "Стильный городской рюкзак",
        "image": "🎒", 
        "active": True
    },
    {
        "id": 6, 
        "title": "Часы", 
        "price": 8000, 
        "description": "Элегантные наручные часы",
        "image": "⌚", 
        "active": True
    }
]

# Корзины пользователей
carts = {}

def get_cart(user_id):
    """Получить корзину пользователя"""
    if user_id not in carts:
        carts[user_id] = []
    return carts[user_id]

def handle_request(client_socket):
    """Обработка запроса"""
    request = client_socket.recv(4096).decode('utf-8')
    
    if not request:
        return
    
    # Парсим запрос
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
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type

{response_body}"""
    
    # API корзины
    elif path.startswith('/api/cart/'):
        user_id = path.split('/')[-1]
        
        if method == 'GET':
            # Получить корзину
            cart = get_cart(user_id)
            response_body = json.dumps(cart, ensure_ascii=False)
            response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        
        elif method == 'POST':
            # Добавить в корзину
            content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
            post_data = request.split('\r\n\r\n')[1][:content_length]
            
            try:
                data = json.loads(post_data)
                product_id = data.get('product_id')
                quantity = data.get('quantity', 1)
                
                cart = get_cart(user_id)
                
                # Найти товар
                product = None
                for p in products:
                    if p['id'] == product_id:
                        product = p
                        break
                
                if product:
                    # Проверить, есть ли уже в корзине
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
            except Exception as e:
                response_body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
                response = f"""HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        
        elif method == 'DELETE':
            # Удалить из корзины
            content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
            post_data = request.split('\r\n\r\n')[1][:content_length]
            
            try:
                data = json.loads(post_data)
                item_id = data.get('item_id')
                
                cart = get_cart(user_id)
                cart = [item for item in cart if item['id'] != item_id]
                carts[user_id] = cart
                
                response_body = json.dumps({"success": True, "cart": cart}, ensure_ascii=False)
                response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
            except Exception as e:
                response_body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
                response = f"""HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Добавление товара
    elif path == '/api/products' and method == 'POST':
        content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
        post_data = request.split('\r\n\r\n')[1][:content_length]
        
        try:
            data = json.loads(post_data)
            
            new_product = {
                "id": len(products) + 1,
                "title": data.get('title', 'Новый товар'),
                "price": data.get('price', 0),
                "description": data.get('description', ''),
                "image": data.get('image', '📦'),
                "active": True
            }
            
            products.append(new_product)
            
            response_body = json.dumps({"success": True, "product": new_product}, ensure_ascii=False)
            response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
        except Exception as e:
            response_body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
            response = f"""HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Редактирование товара
    elif path.startswith('/api/products/') and method == 'PUT':
        product_id = int(path.split('/')[-1])
        content_length = int(request.split('Content-Length: ')[1].split('\n')[0])
        post_data = request.split('\r\n\r\n')[1][:content_length]
        
        try:
            data = json.loads(post_data)
            
            for i, product in enumerate(products):
                if product['id'] == product_id:
                    products[i] = {
                        "id": product_id,
                        "title": data.get('title', product['title']),
                        "price": data.get('price', product['price']),
                        "description": data.get('description', product['description']),
                        "image": data.get('image', product.get('image', '📦')),
                        "active": data.get('active', product['active'])
                    }
                    
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
        except Exception as e:
            response_body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
            response = f"""HTTP/1.1 400 Bad Request
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *

{response_body}"""
    
    # Удаление товара (РЕАЛЬНОЕ УДАЛЕНИЕ)
    elif path.startswith('/api/products/') and method == 'DELETE':
        product_id = int(path.split('/')[-1])
        
        for i, product in enumerate(products):
            if product['id'] == product_id:
                del products[i]
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
        try:
            with open('final_index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            html_content = "<h1>Магазин не найден</h1>"
        
        response = f"""HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: {len(html_content.encode('utf-8'))}

{html_content}"""
    
    else:
        # 404
        response_body = "<h1>404 - Not Found</h1>"
        response = f"""HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}

{response_body}"""
    
    client_socket.send(response.encode('utf-8'))
    client_socket.close()

def start_server():
    """Запуск сервера"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen(5)
    
    print(f"🌐 Финальный сервер запущен на http://localhost:{PORT}")
    print(f"📱 Магазин: http://localhost:{PORT}")
    print(f"🛒 Корзина: встроена в магазин")
    print("🛑 Для остановки: Ctrl+C")
    
    try:
        while True:
            client_socket, addr = server_socket.accept()
            handle_request(client_socket)
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        server_socket.close()

if __name__ == "__main__":
    start_server()

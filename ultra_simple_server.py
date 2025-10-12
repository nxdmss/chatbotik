#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УЛЬТРА ПРОСТОЙ СЕРВЕР
Максимально простая версия без сложностей
"""

import json
import socket
from urllib.parse import urlparse, parse_qs

# Порт
PORT = 8000

# Простое хранилище товаров (в памяти)
products = [
    {"id": 1, "title": "Футболка", "price": 1500, "description": "Крутая футболка", "active": True},
    {"id": 2, "title": "Джинсы", "price": 3000, "description": "Стильные джинсы", "active": True},
    {"id": 3, "title": "Кроссовки", "price": 5000, "description": "Удобные кроссовки", "active": True}
]

def handle_request(client_socket):
    """Обработка запроса"""
    request = client_socket.recv(1024).decode('utf-8')
    
    if not request:
        return
    
    # Парсим запрос
    lines = request.split('\n')
    first_line = lines[0]
    method, path, protocol = first_line.split()
    
    print(f"📥 {method} {path}")
    
    # Определяем тип ответа
    if path == '/api/products':
        # API товаров
        response_body = json.dumps(products, ensure_ascii=False)
        response = f"""HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: {len(response_body.encode('utf-8'))}
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type

{response_body}"""
    
    elif path == '/admin':
        # Админ панель
        try:
            with open('simple_admin.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            html_content = "<h1>Админ панель не найдена</h1>"
        
        response = f"""HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: {len(html_content.encode('utf-8'))}

{html_content}"""
    
    elif path == '/' or path == '/index.html':
        # Главная страница
        try:
            with open('simple_index.html', 'r', encoding='utf-8') as f:
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
    
    print(f"🌐 Ультра простой сервер запущен на http://localhost:{PORT}")
    print(f"📱 Магазин: http://localhost:{PORT}")
    print(f"⚙️ Админ: http://localhost:{PORT}/admin")
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
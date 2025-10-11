#!/usr/bin/env python3
"""
Простой HTTP сервер для тестирования веб-приложения
"""

import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs
import mimetypes

# Простые товары для тестирования
test_products = [
    {
        "id": 1,
        "title": "Тестовые кроссовки",
        "description": "Кроссовки для тестирования функциональности",
        "price": 5000,
        "sizes": ["40", "41", "42"],
        "photo": "/webapp/static/uploads/default.jpg",
        "is_active": True
    },
    {
        "id": 2,
        "title": "Тестовые кеды",
        "description": "Кеды для тестирования функциональности",
        "price": 3000,
        "sizes": ["38", "39", "40"],
        "photo": "/webapp/static/uploads/default.jpg",
        "is_active": True
    }
]

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"GET {self.path}")
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open('local_test.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
            return
            
        elif self.path == '/webapp/products.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(test_products).encode('utf-8'))
            return
            
        elif self.path.startswith('/webapp/admin/products'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"products": test_products}).encode('utf-8'))
            return
            
        elif self.path == '/webapp/static/uploads/default.jpg':
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            # Отправляем простую заглушку
            self.wfile.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9')
            return
            
        else:
            # Пытаемся отдать статический файл
            super().do_GET()
    
    def do_POST(self):
        print(f"POST {self.path}")
        
        if self.path.startswith('/webapp/admin/products'):
            # Читаем данные формы
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            print(f"Получены данные: {post_data}")
            
            # Создаем новый товар
            new_product = {
                "id": len(test_products) + 1,
                "title": "Новый товар",
                "description": "Описание нового товара",
                "price": 1000,
                "sizes": ["M", "L"],
                "photo": "/webapp/static/uploads/default.jpg",
                "is_active": True
            }
            
            test_products.append(new_product)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "success": True,
                "product_id": new_product["id"],
                "message": "Товар создан успешно"
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_PUT(self):
        print(f"PUT {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            product_id = int(self.path.split('/')[-1])
            
            # Находим товар
            product = next((p for p in test_products if p["id"] == product_id), None)
            if product:
                product["title"] = "Обновленный товар"
                product["description"] = "Обновленное описание"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"success": True, "message": "Товар обновлен успешно"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"error": "Товар не найден"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_DELETE(self):
        print(f"DELETE {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            product_id = int(self.path.split('/')[-1])
            
            # Находим товар
            product = next((p for p in test_products if p["id"] == product_id), None)
            if product:
                product["is_active"] = False
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"success": True, "message": "Товар удален успешно"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"error": "Товар не найден"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8000
    
    print(f"🚀 Запуск тестового сервера на порту {PORT}")
    print(f"📱 Откройте http://localhost:{PORT} для тестирования")
    
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен")
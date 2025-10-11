#!/usr/bin/env python3
"""
Надежный HTTP сервер для тестирования веб-приложения
"""

import http.server
import socketserver
import json
import os
import threading
import time

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

class RobustHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # Добавляем CORS заголовки
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Обработка preflight запросов
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        print(f"GET {self.path}")
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('debug_app.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
            return
            
        elif self.path == '/webapp/products.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(test_products).encode('utf-8'))
            return
            
        elif self.path.startswith('/webapp/admin/products'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"products": test_products}).encode('utf-8'))
            return
            
        elif self.path == '/webapp/static/uploads/default.jpg':
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
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
            try:
                # Читаем данные формы
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Пустые данные"}).encode('utf-8'))
                    return
                
                post_data = self.rfile.read(content_length)
                print(f"Получены данные ({content_length} байт)")
                
                # Парсим multipart/form-data
                form_data = self.parse_multipart_data(post_data, self.headers.get('Content-Type', ''))
                print(f"Распарсенные данные: {form_data}")
                
                # Создаем новый товар
                new_product = {
                    "id": len(test_products) + 1,
                    "title": form_data.get('title', 'Новый товар'),
                    "description": form_data.get('description', 'Описание нового товара'),
                    "price": float(form_data.get('price', 1000)),
                    "sizes": [s.strip() for s in form_data.get('sizes', 'M,L').split(',') if s.strip()],
                    "photo": "/webapp/static/uploads/default.jpg",
                    "is_active": True
                }
                
                test_products.append(new_product)
                print(f"✅ Товар добавлен: {new_product}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "success": True,
                    "product_id": new_product["id"],
                    "message": "Товар создан успешно"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            except Exception as e:
                print(f"❌ Ошибка обработки POST: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": f"Ошибка сервера: {str(e)}"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def parse_multipart_data(self, data, content_type):
        """Простой парсер multipart/form-data"""
        form_data = {}
        
        if 'multipart/form-data' not in content_type:
            return form_data
        
        # Извлекаем boundary
        boundary = content_type.split('boundary=')[1]
        boundary = boundary.encode('utf-8')
        
        # Разделяем данные по boundary
        parts = data.split(b'--' + boundary)
        
        for part in parts:
            if b'Content-Disposition: form-data' in part:
                # Извлекаем имя поля
                lines = part.split(b'\r\n')
                for line in lines:
                    if b'name=' in line:
                        name_start = line.find(b'name="') + 6
                        name_end = line.find(b'"', name_start)
                        field_name = line[name_start:name_end].decode('utf-8')
                        
                        # Извлекаем значение
                        value_start = part.find(b'\r\n\r\n') + 4
                        value_end = part.rfind(b'\r\n')
                        if value_end == -1:
                            value_end = len(part)
                        
                        field_value = part[value_start:value_end].decode('utf-8')
                        form_data[field_name] = field_value
                        break
        
        return form_data
    
    def do_PUT(self):
        print(f"PUT {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            # Извлекаем product_id из пути, убирая query параметры
            path_parts = self.path.split('/')
            product_id_str = path_parts[-1].split('?')[0]  # Убираем query параметры
            product_id = int(product_id_str)
            
            # Находим товар
            product = next((p for p in test_products if p["id"] == product_id), None)
            if product:
                product["title"] = "Обновленный товар"
                product["description"] = "Обновленное описание"
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"success": True, "message": "Товар обновлен успешно"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
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
            # Извлекаем product_id из пути, убирая query параметры
            path_parts = self.path.split('/')
            product_id_str = path_parts[-1].split('?')[0]  # Убираем query параметры
            product_id = int(product_id_str)
            
            # Находим товар
            product = next((p for p in test_products if p["id"] == product_id), None)
            if product:
                product["is_active"] = False
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"success": True, "message": "Товар удален успешно"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"error": "Товар не найден"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        else:
            self.send_response(404)
            self.end_headers()

def start_server():
    PORT = 8000
    
    print(f"🚀 Запуск надежного сервера на порту {PORT}")
    print(f"📱 Откройте http://localhost:{PORT} для тестирования")
    print(f"🌐 Или http://127.0.0.1:{PORT}")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), RobustHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен")

if __name__ == "__main__":
    start_server()

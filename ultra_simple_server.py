#!/usr/bin/env python3
"""
Ультра-простой сервер для работы с товарами
Полностью переделанная логика
"""

import http.server
import socketserver
import json
import os
import sqlite3
from urllib.parse import urlparse, parse_qs

# Глобальный список товаров (в памяти для простоты)
products = [
    {
        "id": 1,
        "title": "Кроссовки Nike Air Max",
        "description": "Удобные кроссовки для спорта",
        "price": 5990,
        "sizes": ["40", "41", "42", "43"],
        "photo": "/webapp/static/uploads/photo_2025-10-05_12-32-10.jpg",
        "is_active": True
    },
    {
        "id": 2,
        "title": "Кеды Adidas Stan Smith",
        "description": "Классические кеды в белом цвете",
        "price": 3990,
        "sizes": ["38", "39", "40", "41"],
        "photo": "/webapp/static/uploads/photo_2025-10-10_00-57-51.jpg",
        "is_active": True
    },
    {
        "id": 3,
        "title": "Ботинки Timberland",
        "description": "Прочные ботинки для активного отдыха",
        "price": 7990,
        "sizes": ["40", "41", "42", "43"],
        "photo": "/webapp/static/uploads/photo_2025-10-10_00-59-18.jpg",
        "is_active": True
    },
    {
        "id": 4,
        "title": "Сандалии Birkenstock",
        "description": "Ортопедические сандалии для комфорта",
        "price": 4590,
        "sizes": ["38", "39", "40", "41", "42"],
        "photo": "/webapp/static/uploads/photo_2025-10-10_01-01-46.jpg",
        "is_active": True
    },
    {
        "id": 5,
        "title": "Кроссовки New Balance",
        "description": "Спортивные кроссовки с амортизацией",
        "price": 5490,
        "sizes": ["39", "40", "41", "42", "43"],
        "photo": "/webapp/static/uploads/photo_2025-10-10_01-02-41.jpg",
        "is_active": True
    }
]

class UltraSimpleHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # CORS заголовки
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_GET(self):
        print(f"GET {self.path}")
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            try:
                with open('webapp/index_clean.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except:
                self.wfile.write('<h1>Сервер работает!</h1>'.encode('utf-8'))
            return
        
        elif self.path == '/webapp/products.json':
            # Возвращаем все товары
            active_products = [p for p in products if p['is_active']]
            self._send_json_response(200, active_products)
            return
        
        elif self.path == '/webapp/admin/products':
            # Возвращаем все товары для админа
            self._send_json_response(200, {"products": products})
            return
        
        elif self.path.startswith('/webapp/static/'):
            # Статические файлы
            super().do_GET()
            return
        
        else:
            # Пытаемся отдать файл
            super().do_GET()
    
    def do_POST(self):
        print(f"POST {self.path}")
        
        if self.path == '/webapp/admin/products':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # Простой парсинг JSON
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except:
                    # Если не JSON, парсим form-data
                    data = self._parse_form_data(post_data)
                
                # Создаем новый товар
                new_id = max([p['id'] for p in products]) + 1 if products else 1
                new_product = {
                    "id": new_id,
                    "title": data.get('title', 'Новый товар'),
                    "description": data.get('description', 'Описание товара'),
                    "price": float(data.get('price', 1000)),
                    "sizes": data.get('sizes', ['M', 'L']),
                    "photo": "/webapp/static/uploads/default.jpg",
                    "is_active": True
                }
                
                products.append(new_product)
                print(f"✅ Товар добавлен: {new_product['title']}")
                
                self._send_json_response(200, {
                    "success": True,
                    "product_id": new_id,
                    "message": "Товар создан успешно"
                })
                return
                
            except Exception as e:
                print(f"❌ Ошибка создания товара: {e}")
                self._send_json_response(500, {"error": f"Ошибка создания товара: {str(e)}"})
                return
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_PUT(self):
        print(f"PUT {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            try:
                # Извлекаем ID товара
                product_id = int(self.path.split('/')[-1].split('?')[0])
                
                # Находим товар
                product = next((p for p in products if p['id'] == product_id), None)
                if not product:
                    self._send_json_response(404, {"error": "Товар не найден"})
                    return
                
                # Читаем данные
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except:
                    data = self._parse_form_data(post_data)
                
                # Обновляем товар
                product['title'] = data.get('title', product['title'])
                product['description'] = data.get('description', product['description'])
                product['price'] = float(data.get('price', product['price']))
                product['sizes'] = data.get('sizes', product['sizes'])
                
                print(f"✅ Товар обновлен: {product['title']}")
                
                self._send_json_response(200, {
                    "success": True,
                    "message": "Товар обновлен успешно"
                })
                return
                
            except Exception as e:
                print(f"❌ Ошибка обновления товара: {e}")
                self._send_json_response(500, {"error": f"Ошибка обновления товара: {str(e)}"})
                return
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_DELETE(self):
        print(f"DELETE {self.path}")
        
        if self.path.startswith('/webapp/admin/products/'):
            try:
                # Извлекаем ID товара
                product_id = int(self.path.split('/')[-1].split('?')[0])
                
                # Находим товар
                product = next((p for p in products if p['id'] == product_id), None)
                if not product:
                    self._send_json_response(404, {"error": "Товар не найден"})
                    return
                
                # Деактивируем товар (мягкое удаление)
                product['is_active'] = False
                print(f"✅ Товар удален (деактивирован): {product['title']}")
                
                self._send_json_response(200, {
                    "success": True,
                    "message": "Товар удален успешно"
                })
                return
                
            except Exception as e:
                print(f"❌ Ошибка удаления товара: {e}")
                self._send_json_response(500, {"error": f"Ошибка удаления товара: {str(e)}"})
                return
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def _parse_form_data(self, data):
        """Простой парсер form-data"""
        result = {}
        try:
            # Пытаемся парсить как JSON
            return json.loads(data.decode('utf-8'))
        except:
            # Если не JSON, возвращаем пустой словарь
            return {}

def start_server():
    PORT = 8000
    
    print(f"🚀 Запуск ультра-простого сервера на порту {PORT}")
    print(f"📱 Откройте http://localhost:{PORT}")
    print(f"🛍️ Товаров в системе: {len([p for p in products if p['is_active']])}")
    print("=" * 50)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), UltraSimpleHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Сервер остановлен")

if __name__ == "__main__":
    start_server()
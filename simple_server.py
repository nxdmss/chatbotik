#!/usr/bin/env python3
"""
Простой HTTP сервер для тестирования WebApp
"""

import http.server
import socketserver
import os
import json
from urllib.parse import urlparse, parse_qs

class WebAppHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/webapp/'):
            # Обслуживаем файлы WebApp
            file_path = self.path[8:]  # убираем /webapp/
            if file_path == '' or file_path == '/':
                file_path = 'index.html'
            
            full_path = os.path.join('webapp', file_path)
            if os.path.exists(full_path):
                self.send_response(200)
                if file_path.endswith('.html'):
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                elif file_path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                elif file_path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                elif file_path.endswith('.json'):
                    self.send_header('Content-type', 'application/json')
                else:
                    self.send_header('Content-type', 'text/plain')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")
        elif self.path == '/api/products':
            # API для получения товаров
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Загружаем товары из файла
            try:
                with open('shop/products.json', 'r', encoding='utf-8') as f:
                    products = json.load(f)
                self.wfile.write(json.dumps(products, ensure_ascii=False).encode('utf-8'))
            except:
                self.wfile.write(json.dumps([], ensure_ascii=False).encode('utf-8'))
        elif self.path == '/':
            # Главная страница с демо
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            with open('demo.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

def run_server(port=8000):
    """Запуск сервера"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", port), WebAppHandler) as httpd:
        print(f"🚀 Сервер запущен на http://localhost:{port}")
        print(f"📱 WebApp доступен по адресу: http://localhost:{port}/webapp/")
        print(f"🧪 Демо страница: http://localhost:{port}/")
        print("Нажмите Ctrl+C для остановки")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Сервер остановлен")

if __name__ == "__main__":
    run_server()

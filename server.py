"""
Улучшенный FastAPI сервер для Telegram WebApp магазина
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel, ValidationError

# Импортируем наши модули
from models import Product, AdminAction
from logger_config import setup_logging, bot_logger
from error_handlers import validate_admin_access, ValidationError as BotValidationError
from database import db

# Настраиваем логирование
setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = bot_logger.logger

app = FastAPI(
    title="Telegram Shop WebApp API",
    description="API для Telegram WebApp магазина",
    version="2.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEBAPP_DIR = os.path.join(os.path.dirname(__file__), 'webapp')
UPLOADS_DIR = os.path.join(WEBAPP_DIR, 'uploads')
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

def datetime_now() -> str:
    """Получение текущего времени в ISO формате"""
    return datetime.now().isoformat()

# Монтируем статические файлы
app.mount('/webapp/static', StaticFiles(directory=WEBAPP_DIR), name='webapp_static')

# Модели для API
class ProductCreate(BaseModel):
    """Модель для создания товара через API"""
    title: str
    price: int
    currency: str = "RUB"
    photo: str = ""
    sizes: List[int] = []

class ProductResponse(BaseModel):
    """Модель ответа с товаром"""
    id: str
    title: str
    price: int
    currency: str
    photo: str
    sizes: List[int]
    deleted: bool = False

class AdminResponse(BaseModel):
    """Модель ответа с информацией об администраторах"""
    admins: List[str]

class UploadResponse(BaseModel):
    """Модель ответа при загрузке файла"""
    url: str
    filename: str

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования HTTP запросов"""
    start_time = datetime.now()
    
    # Логируем входящий запрос
    logger.info(
        "http_request",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    try:
        response = await call_next(request)
        
        # Логируем ответ
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            "http_response",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        return response
    except Exception as e:
        # Логируем ошибку
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(
            "http_error",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=process_time
        )
        raise

@app.get('/')
async def index():
    """Главная страница"""
    try:
    return FileResponse(os.path.join(WEBAPP_DIR, 'index.html'))
    except Exception as e:
        logger.error("Error serving index page", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get('/webapp')
async def webapp():
    """WebApp страница"""
    try:
    return FileResponse(os.path.join(WEBAPP_DIR, 'index.html'))
    except Exception as e:
        logger.error("Error serving webapp page", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get('/webapp/products.json')
async def products_json():
    """API для получения списка товаров из базы данных"""
    try:
        products = db.get_products(active_only=True)
        logger.info(f"Serving {len(products)} products from database")
        
        # Если в базе нет товаров, используем JSON файл как fallback
        if not products:
            logger.warning("No products in database, using JSON fallback")
            products_file = os.path.join(os.path.dirname(__file__), 'webapp', 'products.json')
            if os.path.exists(products_file):
                with open(products_file, 'r', encoding='utf-8') as f:
                    import json
                    products = json.load(f)
                    logger.info(f"Loaded {len(products)} products from JSON file")
        
        return JSONResponse(products)
    except Exception as e:
        logger.error("Error serving products from database", error=str(e))
        raise HTTPException(status_code=500, detail="Error loading products")

@app.post('/webapp/orders')
async def create_order(order_data: Dict[str, Any]):
    """API для создания заказа"""
    try:
        user_id = order_data.get('user_id')
        products = order_data.get('products', [])
        total_amount = order_data.get('total_amount', 0)
        
        if not user_id or not products:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        order_id = db.add_order(user_id, products, total_amount)
        if order_id:
            logger.info(f"Order {order_id} created for user {user_id}")
            return JSONResponse({"order_id": order_id, "status": "created"})
        else:
            raise HTTPException(status_code=500, detail="Failed to create order")
    except Exception as e:
        logger.error("Error creating order", error=str(e))
        raise HTTPException(status_code=500, detail="Error creating order")

@app.post('/webapp/admin/add-product')
async def admin_add_product(
    title: str = Form(...),
    price: float = Form(...),
    sizes: str = Form(...),
    description: str = Form(""),
    photo: UploadFile = File(None)
):
    """API для добавления товара админом"""
    try:
        # Парсим размеры
        sizes_list = [size.strip() for size in sizes.split(',') if size.strip()]
        
        # Обрабатываем фото
        photo_url = None
        if photo and photo.filename:
            # Сохраняем файл
            filename = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
            file_path = os.path.join(UPLOADS_DIR, filename)
            
            with open(file_path, "wb") as buffer:
                content = await photo.read()
                buffer.write(content)
            
            photo_url = f"/webapp/static/uploads/{filename}"
        
        # Добавляем товар в базу данных
        product_id = db.add_product(
            title=title,
            description=description,
            price=price,
            sizes=sizes_list,
            photo=photo_url
        )
        
        if product_id:
            logger.info(f"Product {product_id} added by admin")
            return JSONResponse({"product_id": product_id, "status": "created"})
        else:
            raise HTTPException(status_code=500, detail="Failed to create product")
    except Exception as e:
        logger.error("Error adding product", error=str(e))
        raise HTTPException(status_code=500, detail="Error adding product")

@app.delete('/webapp/admin/delete-product/{product_id}')
async def admin_delete_product(product_id: int):
    """API для удаления товара админом"""
    try:
        # Обновляем статус товара в базе данных
        success = db.update_product_status(product_id, is_active=False)
        
        if success:
            logger.info(f"Product {product_id} deactivated by admin")
            return JSONResponse({"status": "deleted"})
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    except Exception as e:
        logger.error("Error deleting product", error=str(e))
        raise HTTPException(status_code=500, detail="Error deleting product")

@app.get('/webapp/admins.json', response_model=AdminResponse)
async def admins_json():
    """API для получения списка администраторов"""
    try:
    admins = os.getenv('ADMINS', '')
        admin_list = [x.strip() for x in admins.split(',') if x.strip()]

        logger.info("Admins list requested", admins_count=len(admin_list))
        return AdminResponse(admins=admin_list)
    except Exception as e:
        logger.error("Error serving admins list", error=str(e))
        raise HTTPException(status_code=500, detail="Error loading admins")

@app.post('/webapp/upload', response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """API для загрузки файлов"""
    try:
    if not file.filename:
            raise HTTPException(status_code=400, detail='No filename provided')
        
        # Валидация типа файла
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail='Invalid file type. Only images are allowed.')
        
        # Валидация размера файла (максимум 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail='File too large. Maximum size is 10MB.')
        
        # Санитизация имени файла
    filename = os.path.basename(file.filename)
        # Удаляем потенциально опасные символы
        filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
        
        # Избегаем перезаписи файлов
    base, ext = os.path.splitext(filename)
    i = 1
        save_path = os.path.join(UPLOADS_DIR, filename)
    while os.path.exists(save_path):
        filename = f"{base}_{i}{ext}"
        save_path = os.path.join(UPLOADS_DIR, filename)
        i += 1
        
        # Сохраняем файл
        with open(save_path, 'wb') as f:
            f.write(content)
        
        public_url = f"/webapp/static/uploads/{filename}"
        
        logger.info("File uploaded successfully", filename=filename, size=len(content))
        return UploadResponse(url=public_url, filename=filename)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading file", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail="Error uploading file")

@app.post('/webapp/add_product')
async def add_product_endpoint(request: Request):
    """API для добавления товара (только для администраторов)"""
    try:
        # Проверяем права администратора
        admin_param = request.query_params.get('admin')
        if admin_param != '1':
            logger.warning("Unauthorized product addition attempt", 
                         client_ip=request.client.host if request.client else "unknown")
            return JSONResponse({'error': 'Admin access required'}, status_code=403)
        
        # Получаем данные
    try:
        body = await request.json()
        except Exception as e:
            logger.error("Invalid JSON in add_product request", error=str(e))
            return JSONResponse({'error': 'Invalid JSON'}, status_code=400)
        
        if not isinstance(body, dict) or 'product' not in body:
            return JSONResponse({'error': 'Product data missing'}, status_code=400)
        
        # Валидируем данные товара
        try:
            product_data = ProductCreate(**body['product'])
            product = Product(
                id="",  # Будет сгенерирован в catalog
                title=product_data.title,
                price=product_data.price,
                currency=product_data.currency,
                photo=product_data.photo,
                sizes=product_data.sizes
            )
        except ValidationError as e:
            logger.error("Product validation failed", error=str(e), product_data=body['product'])
            return JSONResponse({'error': f'Validation failed: {e}'}, status_code=400)
        
        # Добавляем товар в каталог
        try:
    from shop.catalog import add_product as catalog_add_product
            created = catalog_add_product(product.dict())
            
            # Логируем действие администратора
            admin_action = AdminAction(
                admin_id="webapp_user",  # В реальном приложении получать из сессии
                action="add_product",
                target_id=created.get('id', ''),
                details={"title": created.get('title', ''), "price": created.get('price', 0)}
            )
            logger.info("Product added via API", **admin_action.dict())
            
    return JSONResponse({'ok': True, 'product': created})

        except Exception as e:
            logger.error("Error adding product to catalog", error=str(e))
            return JSONResponse({'error': 'Failed to add product'}, status_code=500)
    
    except Exception as e:
        logger.error("Unexpected error in add_product", error=str(e))
        return JSONResponse({'error': 'Internal server error'}, status_code=500)

@app.post('/webapp/delete_product')
async def delete_product_endpoint(request: Request):
    """API для удаления товара (только для администраторов)"""
    try:
        # Проверяем права администратора
        admin_param = request.query_params.get('admin')
        if admin_param != '1':
            logger.warning("Unauthorized product deletion attempt", 
                         client_ip=request.client.host if request.client else "unknown")
            return JSONResponse({'error': 'Admin access required'}, status_code=403)
        
        # Получаем данные
    try:
        body = await request.json()
        except Exception as e:
            logger.error("Invalid JSON in delete_product request", error=str(e))
            return JSONResponse({'error': 'Invalid JSON'}, status_code=400)
        
        product_id = body.get('id')
        if not product_id:
            return JSONResponse({'error': 'Product ID required'}, status_code=400)
        
        # Удаляем товар
        try:
    from shop.catalog import delete_product
            success = delete_product(product_id)
            
            if not success:
                return JSONResponse({'error': 'Product not found'}, status_code=404)
            
            # Логируем действие
            logger.info("Product deleted via API", product_id=product_id)
            
    return JSONResponse({'ok': True})

        except Exception as e:
            logger.error("Error deleting product", error=str(e), product_id=product_id)
            return JSONResponse({'error': 'Failed to delete product'}, status_code=500)
    
    except Exception as e:
        logger.error("Unexpected error in delete_product", error=str(e))
        return JSONResponse({'error': 'Internal server error'}, status_code=500)

@app.post('/webapp/restore_product')
async def restore_product_endpoint(request: Request):
    """API для восстановления товара (только для администраторов)"""
    try:
        # Проверяем права администратора
        admin_param = request.query_params.get('admin')
        if admin_param != '1':
            logger.warning("Unauthorized product restoration attempt", 
                         client_ip=request.client.host if request.client else "unknown")
            return JSONResponse({'error': 'Admin access required'}, status_code=403)
        
        # Получаем данные
    try:
        body = await request.json()
        except Exception as e:
            logger.error("Invalid JSON in restore_product request", error=str(e))
            return JSONResponse({'error': 'Invalid JSON'}, status_code=400)
        
        product_id = body.get('id')
        if not product_id:
            return JSONResponse({'error': 'Product ID required'}, status_code=400)
        
        # Восстанавливаем товар
        try:
    from shop.catalog import restore_product
            success = restore_product(product_id)
            
            if not success:
                return JSONResponse({'error': 'Product not found or not deleted'}, status_code=404)
            
            # Логируем действие
            logger.info("Product restored via API", product_id=product_id)
            
            return JSONResponse({'ok': True})
            
        except Exception as e:
            logger.error("Error restoring product", error=str(e), product_id=product_id)
            return JSONResponse({'error': 'Failed to restore product'}, status_code=500)
    
    except Exception as e:
        logger.error("Unexpected error in restore_product", error=str(e))
        return JSONResponse({'error': 'Internal server error'}, status_code=500)

@app.get('/health')
async def health_check():
    """Проверка здоровья сервера"""
    try:
        # Проверяем доступность файлов
        products_file = os.path.join(os.path.dirname(__file__), 'shop', 'products.json')
        products_accessible = os.path.exists(products_file)
        
        uploads_accessible = os.path.exists(UPLOADS_DIR) and os.access(UPLOADS_DIR, os.W_OK)
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime_now(),
            "services": {
                "products": "ok" if products_accessible else "error",
                "uploads": "ok" if uploads_accessible else "error"
            }
        })
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse({
            "status": "unhealthy",
            "timestamp": datetime_now(),
            "error": str(e)
        }, status_code=500)

@app.get('/metrics')
async def metrics():
    """Метрики сервера (базовая версия)"""
    try:
        # Подсчитываем количество товаров
        products_file = os.path.join(os.path.dirname(__file__), 'shop', 'products.json')
        products_count = 0
        if os.path.exists(products_file):
            try:
                import json
                with open(products_file, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                    products_count = len(products)
            except Exception:
                pass
        
        # Подсчитываем количество загруженных файлов
        uploads_count = 0
        if os.path.exists(UPLOADS_DIR):
            try:
                uploads_count = len([f for f in os.listdir(UPLOADS_DIR) if os.path.isfile(os.path.join(UPLOADS_DIR, f))])
    except Exception:
        pass
        
        return JSONResponse({
            "timestamp": datetime_now(),
            "products_count": products_count,
            "uploads_count": uploads_count,
            "uptime": "N/A"  # В реальном приложении можно добавить отслеживание времени работы
        })
    except Exception as e:
        logger.error("Error getting metrics", error=str(e))
        return JSONResponse({"error": "Failed to get metrics"}, status_code=500)

# Обработчик ошибок
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Обработчик 404 ошибок"""
    logger.warning("404 error", url=str(request.url), method=request.method)
    return JSONResponse({"error": "Not found"}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Обработчик 500 ошибок"""
    logger.error("500 error", url=str(request.url), method=request.method, error=str(exc))
    return JSONResponse({"error": "Internal server error"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server", version="2.0.0")
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from fastapi import Request
import logging
from datetime import datetime

app = FastAPI()

WEBAPP_DIR = os.path.join(os.path.dirname(__file__), 'webapp')
UPLOADS_DIR = os.path.join(WEBAPP_DIR, 'uploads')
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

def datetime_now():
    return datetime.now().isoformat()

# mount webapp static (includes uploads)
app.mount('/webapp/static', StaticFiles(directory=WEBAPP_DIR), name='webapp_static')


@app.get('/')
async def index():
    return FileResponse(os.path.join(WEBAPP_DIR, 'index.html'))


@app.get('/webapp')
async def webapp():
    return FileResponse(os.path.join(WEBAPP_DIR, 'index.html'))


@app.get('/webapp/products.json')
async def products_json():
    # Return the server-side products file so WebApp can fetch latest catalog
    return FileResponse(os.path.join(os.path.dirname(__file__), 'shop', 'products.json'))


@app.get('/webapp/admins.json')
async def admins_json():
    # Return ADMINS list from environment as JSON array of strings
    admins = os.getenv('ADMINS', '')
    lst = [x.strip() for x in admins.split(',') if x.strip()]
    return JSONResponse(lst)


@app.post('/webapp/upload')
async def upload_file(file: UploadFile = File(...)):
    # simple upload handler — saves file into webapp/uploads and returns public URL path
    if not file.filename:
        raise HTTPException(status_code=400, detail='No filename')
    # sanitize filename a bit
    filename = os.path.basename(file.filename)
    save_path = os.path.join(UPLOADS_DIR, filename)
    # avoid overwriting: if exists, append counter
    base, ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(save_path):
        filename = f"{base}_{i}{ext}"
        save_path = os.path.join(UPLOADS_DIR, filename)
        i += 1
    try:
        with open(save_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # return URL that WebApp can use — served via /webapp/static/
    public_url = f"/webapp/static/uploads/{filename}"
    return JSONResponse({"url": public_url})


@app.post('/webapp/add_product')
async def add_product_endpoint(request: Request):
    """Fallback endpoint: accepts JSON product and adds it to shop/products.json when called with ?admin=1"""
    qs = request.query_params
    if qs.get('admin') != '1':
        return JSONResponse({'error': 'admin required'}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({'error': 'invalid json'}, status_code=400)
    prod = body.get('product') if isinstance(body, dict) else None
    if not prod:
        return JSONResponse({'error': 'product missing'}, status_code=400)
    # minimal validation
    title = prod.get('title')
    price = int(prod.get('price') or 0)
    from shop.catalog import add_product as catalog_add_product
    if not title or price <= 0:
        return JSONResponse({'error': 'invalid product'}, status_code=400)
    created = catalog_add_product({
        'title': title,
        'price': price,
        'currency': prod.get('currency', 'RUB'),
        'photo': prod.get('photo', ''),
        'sizes': prod.get('sizes', []),
    })
    return JSONResponse({'ok': True, 'product': created})


@app.post('/webapp/delete_product')
async def delete_product_endpoint(request: Request):
    qs = request.query_params
    if qs.get('admin') != '1':
        return JSONResponse({'error': 'admin required'}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({'error': 'invalid json'}, status_code=400)
    pid = body.get('id')
    if not pid:
        return JSONResponse({'error': 'id required'}, status_code=400)
    from shop.catalog import delete_product
    ok = delete_product(pid)
    if not ok:
        return JSONResponse({'error': 'not found'}, status_code=404)
    # log admin action
    try:
        with open('admin_actions.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime_now()} DELETE_PRODUCT {pid}\n")
    except Exception:
        pass
    return JSONResponse({'ok': True})


@app.post('/webapp/restore_product')
async def restore_product_endpoint(request: Request):
    qs = request.query_params
    if qs.get('admin') != '1':
        return JSONResponse({'error': 'admin required'}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({'error': 'invalid json'}, status_code=400)
    pid = body.get('id')
    if not pid:
        return JSONResponse({'error': 'id required'}, status_code=400)
    from shop.catalog import restore_product
    ok = restore_product(pid)
    if not ok:
        return JSONResponse({'error': 'not found or not deleted'}, status_code=404)
    try:
        with open('admin_actions.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime_now()} RESTORE_PRODUCT {pid}\n")
    except Exception:
        pass
    return JSONResponse({'ok': True})

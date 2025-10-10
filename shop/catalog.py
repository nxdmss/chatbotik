"""Catalog definitions and helpers for the shop."""

import os
import json

PROD_FILE = os.path.join(os.path.dirname(__file__), 'products.json')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

def load_products():
    try:
        with open(PROD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_products(products):
    # atomic write: write to temp file then replace
    tmp = PROD_FILE + '.tmp'
    # backup existing file if exists
    try:
        if os.path.exists(PROD_FILE):
            bak_name = os.path.join(BACKUP_DIR, f"products_{int(os.path.getmtime(PROD_FILE))}.json")
            # copy only if backup not exists
            if not os.path.exists(bak_name):
                with open(PROD_FILE, 'r', encoding='utf-8') as rf, open(bak_name, 'w', encoding='utf-8') as wf:
                    wf.write(rf.read())
    except Exception:
        pass
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    try:
        os.replace(tmp, PROD_FILE)
    except Exception:
        # fallback to non-atomic
        with open(PROD_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

PRODUCTS = load_products()

def get_product(pid: str):
    return next((p for p in PRODUCTS if p["id"] == pid), None)

def add_product(prod: dict):
    # assign simple unique id
    existing_ids = {p['id'] for p in PRODUCTS}
    base = prod.get('id') or ('p' + str(len(PRODUCTS) + 1))
    new_id = base
    i = 1
    while new_id in existing_ids:
        new_id = f"{base}_{i}"
        i += 1
    prod['id'] = new_id
    PRODUCTS.append(prod)
    save_products(PRODUCTS)
    return prod


def delete_product(pid: str):
    # soft-delete: mark as deleted
    for p in PRODUCTS:
        if p.get('id') == pid:
            p['deleted'] = True
            save_products(PRODUCTS)
            return True
    return False


def restore_product(pid: str):
    for p in PRODUCTS:
        if p.get('id') == pid and p.get('deleted'):
            p.pop('deleted', None)
            save_products(PRODUCTS)
            return True
    return False

def format_price(price_cents_or_rub):
    return f"{price_cents_or_rub} ₽"

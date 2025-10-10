"""Cart helpers for the shop package. Uses an in-memory data store passed in by the bot.

This module provides thin wrappers; the bot keeps the actual `data` structure.
"""

def get_cart(data_store: dict, user_id: str):
    return data_store.setdefault("carts", {}).setdefault(user_id, {})

def cart_total(data_store: dict, cart: dict):
    total = 0
    from .catalog import get_product
    for pid, qty in cart.items():
        p = get_product(pid)
        if p:
            total += p["price"] * qty
    return total

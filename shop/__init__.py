"""Shop package: catalog and cart utilities."""

from .catalog import PRODUCTS, get_product, format_price
from .cart import get_cart, cart_total

__all__ = ["PRODUCTS", "get_product", "format_price", "get_cart", "cart_total"]

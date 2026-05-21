import json
from datetime import datetime
import secrets

def calculate_invoice_amounts(items_list):
    """
    Given a list of items [{"name": "...", "price": 100.0, "qty": 2}],
    calculates subtotal, 18% GST tax, and total.
    """
    subtotal = 0.0
    for item in items_list:
        subtotal += float(item.get("price", 0.0)) * int(item.get("qty", 1))
        
    tax = subtotal * 0.18 # 18% GST
    total = subtotal + tax
    
    return round(subtotal, 2), round(tax, 2), round(total, 2)

def generate_invoice_number():
    """
    Generates a unique invoice number format, e.g., INV-2026-XXXXX
    """
    random_hex = secrets.token_hex(4).upper()
    current_year = datetime.now().year
    return f"INV-{current_year}-{random_hex}"

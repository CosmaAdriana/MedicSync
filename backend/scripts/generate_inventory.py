"""
Acest script populează tabelul `inventory_items` cu materiale medicale,
simulând stocuri și date de expirare realiste.

"""

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app.models import Base, InventoryItem

# Lista de materiale medicale comune
INITIAL_INVENTORY = [
    {"name": "Seringă 10ml (cutie 100)", "min_stock": 50, "max_stock": 200},
    {"name": "Mănuși chirurgicale M (cutie 100)", "min_stock": 100, "max_stock": 300},
    {"name": "Paracetamol 500mg (cutie 50)", "min_stock": 80, "max_stock": 250},
    {"name": "Dezinfectant mâini 1L", "min_stock": 40, "max_stock": 100},
    {"name": "Fașă elastică 10cm", "min_stock": 150, "max_stock": 400},
    {"name": "Betadină soluție 200ml", "min_stock": 30, "max_stock": 90},
    {"name": "Cateter intravenos 20G", "min_stock": 200, "max_stock": 500},
    {"name": "Ibuprofen 400mg (cutie 30)", "min_stock": 70, "max_stock": 200},
]


def generate_inventory_data():
    """Generează și inserează datele în baza de date."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if db.query(InventoryItem).first():
        print("INFO: Baza de date conține deja date în `inventory_items`. Scriptul se oprește.")
        db.close()
        return

    print("INFO: Se generează datele sintetice pentru inventar...")

    inventory_objects = []
    today = date.today()

    for item in INITIAL_INVENTORY:
        current_stock = random.randint(item["min_stock"], item["max_stock"])
        expiration_date = today + timedelta(days=random.randint(90, 3 * 365))

        inventory_entry = InventoryItem(
            product_name=item["name"],
            current_stock=current_stock,
            min_stock_level=item["min_stock"],
            expiration_date=expiration_date,
        )
        inventory_objects.append(inventory_entry)

    db.bulk_save_objects(inventory_objects)
    db.commit()
    print(f"SUCCESS: Au fost generate și salvate {len(inventory_objects)} articole în inventar.")
    db.close()


if __name__ == "__main__":
    generate_inventory_data()
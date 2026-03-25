"""
Populează tabelul `inventory_items` cu materiale medicale per departament.
"""

import random
from datetime import date, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Department, InventoryItem

# Produse comune tuturor secțiilor
COMMON_ITEMS = [
    {"name": "Seringă 10ml (cutie 100)",        "min_stock": 50,  "max_stock": 200},
    {"name": "Mănuși chirurgicale M (cutie 100)","min_stock": 100, "max_stock": 300},
    {"name": "Paracetamol 500mg (cutie 50)",     "min_stock": 80,  "max_stock": 250},
    {"name": "Dezinfectant mâini 1L",            "min_stock": 40,  "max_stock": 100},
    {"name": "Fașă elastică 10cm",               "min_stock": 150, "max_stock": 400},
    {"name": "Betadină soluție 200ml",           "min_stock": 30,  "max_stock": 90},
    {"name": "Cateter intravenos 20G",           "min_stock": 200, "max_stock": 500},
    {"name": "Ibuprofen 400mg (cutie 30)",       "min_stock": 70,  "max_stock": 200},
    {"name": "Comprese sterile 10x10cm",         "min_stock": 200, "max_stock": 500},
    {"name": "Plasture 5x10cm (cutie 50)",       "min_stock": 100, "max_stock": 300},
]

# Produse specifice per secție (după keyword în nume)
DEPT_SPECIFIC = {
    "ATI": [
        {"name": "Morfină 10mg/ml fiole",             "min_stock": 20, "max_stock": 60},
        {"name": "Propofol 200mg/20ml",               "min_stock": 15, "max_stock": 50},
        {"name": "Adrenalină 1mg/ml fiole",           "min_stock": 30, "max_stock": 80},
        {"name": "Ventilator consumabile (set)",      "min_stock": 10, "max_stock": 30},
        {"name": "Cateter venos central 7Fr",         "min_stock": 20, "max_stock": 60},
    ],
    "Cardiologie": [
        {"name": "Aspirină 100mg (cutie 30)",         "min_stock": 100, "max_stock": 300},
        {"name": "Heparină 5000 UI/ml",               "min_stock": 50,  "max_stock": 150},
        {"name": "Nitroglicerină 0.5mg sublingual",   "min_stock": 40,  "max_stock": 120},
        {"name": "Electrozi EKG (set 10)",            "min_stock": 80,  "max_stock": 200},
        {"name": "Metoprolol 50mg (cutie 30)",        "min_stock": 60,  "max_stock": 180},
    ],
    "Chirurgie": [
        {"name": "Fire chirurgicale absorbabile 2-0", "min_stock": 50,  "max_stock": 150},
        {"name": "Bisturiu de unică folosință nr.22", "min_stock": 30,  "max_stock": 100},
        {"name": "Dren chirurgical 28Fr",             "min_stock": 20,  "max_stock": 60},
        {"name": "Câmp operator steril (set)",        "min_stock": 40,  "max_stock": 120},
        {"name": "Lidocaină 2% fiole 10ml",           "min_stock": 60,  "max_stock": 180},
    ],
    "Pediatrie": [
        {"name": "Paracetamol sirop 120mg/5ml",       "min_stock": 80,  "max_stock": 200},
        {"name": "Seringă 2ml pediatrică",            "min_stock": 100, "max_stock": 300},
        {"name": "Canulă nazală O2 pediatrică",       "min_stock": 20,  "max_stock": 60},
        {"name": "Ser rehidratare orală plicuri",     "min_stock": 60,  "max_stock": 180},
        {"name": "Termometru digital",                "min_stock": 10,  "max_stock": 30},
    ],
    "UPU": [
        {"name": "Defibrilator electrozi adulți",     "min_stock": 10,  "max_stock": 30},
        {"name": "Tub endotraheal 7.5mm",             "min_stock": 20,  "max_stock": 60},
        {"name": "Guler cervical reglabil",           "min_stock": 15,  "max_stock": 45},
        {"name": "Soluție NaCl 0.9% 500ml",          "min_stock": 100, "max_stock": 300},
        {"name": "Masca O2 cu rezervor",              "min_stock": 30,  "max_stock": 90},
    ],
}


def get_dept_key(dept_name: str) -> str:
    for key in DEPT_SPECIFIC:
        if key.lower() in dept_name.lower():
            return key
    return None


def generate_inventory_data():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    today = date.today()

    # Șterge inventarul existent
    deleted = db.query(InventoryItem).delete()
    db.commit()
    print(f"INFO: {deleted} produse existente șterse.")

    departments = db.query(Department).all()
    if not departments:
        print("ERROR: Nu există departamente în baza de date!")
        db.close()
        return

    total = 0
    for dept in departments:
        key = get_dept_key(dept.name)
        items = COMMON_ITEMS + (DEPT_SPECIFIC.get(key, []) if key else [])

        for item in items:
            # Simulate some items below min stock for realism
            if random.random() < 0.15:
                stock = random.randint(0, item["min_stock"] - 1)
            else:
                stock = random.randint(item["min_stock"], item["max_stock"])

            exp_days = random.randint(-10, 3 * 365)  # unele expirate pentru FEFO demo
            exp_date = today + timedelta(days=exp_days)

            db.add(InventoryItem(
                product_name=item["name"],
                current_stock=stock,
                min_stock_level=item["min_stock"],
                expiration_date=exp_date,
                department_id=dept.id,
            ))
            total += 1

        print(f"  ✓ {dept.name}: {len(items)} produse")

    db.commit()
    db.close()
    print(f"\nSUCCESS: {total} produse generate pentru {len(departments)} departamente.")


if __name__ == "__main__":
    generate_inventory_data()

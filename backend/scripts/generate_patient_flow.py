"""
Acest script populează tabelul `daily_patient_flow` cu date istorice
pe o perioadă de 3 ani, simulând sezonalitatea și evenimente speciale.

"""

import random
from datetime import timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

# Adaugă calea proiectului pentru a putea importa modulele aplicației
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app.models import Base, DailyPatientFlow, Department


def generate_synthetic_data():
    # Asigură-te că tabelul există
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    # Verifică dacă există deja date pentru a nu le duplica
    if db.query(DailyPatientFlow).first():
        print("INFO: Baza de date conține deja date în `daily_patient_flow`. Scriptul se oprește.")
        db.close()
        return

    print("INFO: Se generează datele sintetice pentru fluxul de pacienți...")

    # Creează departamentele default dacă nu există
    departments_data = [
        {"name": "UPU (Urgență)", "description": "Unitatea de Primiri Urgențe - flux imprevizibil, vârfuri seara/weekend"},
        {"name": "ATI (Terapie Intensivă)", "description": "Anestezie și Terapie Intensivă - pacienți critici, flux constant"},
        {"name": "Cardiologie", "description": "Departament de cardiologie - sezonier, mai multe cazuri iarna"},
        {"name": "Pediatrie", "description": "Departament de pediatrie - vârfuri la epidemii, toamnă/iarnă"},
        {"name": "Chirurgie", "description": "Departament de chirurgie - flux programat, mai uniform"},
    ]

    departments = []
    for dept_data in departments_data:
        existing_dept = db.query(Department).filter(Department.name == dept_data["name"]).first()
        if existing_dept:
            departments.append(existing_dept)
        else:
            dept = Department(name=dept_data["name"], description=dept_data["description"])
            db.add(dept)
            departments.append(dept)

    db.commit()
    print(f"INFO: Departamente create/verificate: {len(departments)}")

    # Definirea perioadei: ultimii 3 ani
    end_date = pd.Timestamp.now().date()
    start_date = end_date - timedelta(days=3 * 365)
    date_range = pd.date_range(start_date, end_date, freq="D")

    # Parametrii specifici per departament
    department_params = {
        "UPU (Urgență)": {
            "base": 50,
            "winter_increase": 30,
            "holiday_decrease": -10,
            "epidemic_multiplier": 2.0,
            "epidemic_chance": 0.04,
            "variance": 15,
        },
        "ATI (Terapie Intensivă)": {
            "base": 15,
            "winter_increase": 5,
            "holiday_decrease": 0,
            "epidemic_multiplier": 1.2,
            "epidemic_chance": 0.02,
            "variance": 3,
        },
        "Cardiologie": {
            "base": 25,
            "winter_increase": 20,
            "holiday_decrease": -5,
            "epidemic_multiplier": 1.1,
            "epidemic_chance": 0.01,
            "variance": 8,
        },
        "Pediatrie": {
            "base": 30,
            "winter_increase": 35,
            "holiday_decrease": -8,
            "epidemic_multiplier": 2.5,
            "epidemic_chance": 0.06,
            "variance": 12,
        },
        "Chirurgie": {
            "base": 20,
            "winter_increase": 5,
            "holiday_decrease": -12,
            "epidemic_multiplier": 1.0,
            "epidemic_chance": 0.005,
            "variance": 5,
        },
    }

    patient_flow_objects = []

    # Generează date pentru fiecare departament
    for dept in departments:
        params = department_params[dept.name]
        is_epidemic_period = False
        epidemic_days_left = 0

        for day in date_range:
            patient_count = params["base"] + random.randint(-params["variance"], params["variance"])
            is_holiday = day.month == 12 and day.day in [25, 26] or day.month == 1 and day.day == 1

            # Sezonalitate (iarna vin mai mulți pacienți)
            if day.month in [11, 12, 1, 2]:
                patient_count += params["winter_increase"]
                weather_temp = random.uniform(-5, 5)
            else:
                weather_temp = random.uniform(15, 28)

            # Efectul sărbătorilor
            if is_holiday:
                patient_count += params["holiday_decrease"]

            # Simulare epidemii (perioade de 1-2 săptămâni cu număr crescut)
            if not is_epidemic_period and random.random() < params["epidemic_chance"]:
                is_epidemic_period = True
                epidemic_days_left = random.randint(7, 14)

            if is_epidemic_period and epidemic_days_left > 0:
                patient_count *= params["epidemic_multiplier"]
                epidemic_days_left -= 1
            else:
                is_epidemic_period = False

            flow_entry = DailyPatientFlow(
                date=day.date(),
                department_id=dept.id,
                patient_count=int(max(5, patient_count)),  # Asigurăm un minim de pacienți
                weather_temp=round(weather_temp, 1),
                is_holiday=is_holiday,
                is_epidemic=is_epidemic_period,
            )
            patient_flow_objects.append(flow_entry)

        print(f"INFO: Generate {len(date_range)} zile pentru {dept.name}")

    try:
        db.bulk_save_objects(patient_flow_objects)
        db.commit()
        print(f"SUCCESS: Au fost generate și salvate {len(patient_flow_objects)} înregistrări pentru {len(departments)} departamente.")
    except Exception as e:
        print(f"ERROR: A apărut o eroare la salvarea datelor: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    generate_synthetic_data()
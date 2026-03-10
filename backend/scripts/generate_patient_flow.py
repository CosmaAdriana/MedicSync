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
from app.models import Base, DailyPatientFlow


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

    # Definirea perioadei: ultimii 3 ani
    end_date = pd.Timestamp.now().date()
    start_date = end_date - timedelta(days=3 * 365)
    date_range = pd.date_range(start_date, end_date, freq="D")

    # Parametrii pentru simulare
    base_patient_count = 40
    winter_increase = 25  # Pacienți în plus iarna
    holiday_decrease = -15  # Pacienți mai puțini de sărbători
    epidemic_chance = 0.03  # 3% șansă de a începe o epidemie

    is_epidemic_period = False
    epidemic_days_left = 0

    patient_flow_objects = []

    for day in date_range:
        patient_count = base_patient_count + random.randint(-5, 5)
        is_holiday = day.month == 12 and day.day in [25, 26] or day.month == 1 and day.day == 1

        # Sezonalitate (iarna vin mai mulți pacienți)
        if day.month in [11, 12, 1, 2]:
            patient_count += winter_increase
            weather_temp = random.uniform(-5, 5)
        else:
            weather_temp = random.uniform(15, 28)

        # Efectul sărbătorilor
        if is_holiday:
            patient_count += holiday_decrease

        # Simulare epidemii (perioade de 1-2 săptămâni cu număr crescut)
        if not is_epidemic_period and random.random() < epidemic_chance:
            is_epidemic_period = True
            epidemic_days_left = random.randint(7, 14)

        if is_epidemic_period and epidemic_days_left > 0:
            patient_count *= 1.5  # Creștere cu 50% în timpul epidemiei
            epidemic_days_left -= 1
        else:
            is_epidemic_period = False

        flow_entry = DailyPatientFlow(
            date=day.date(),
            patient_count=int(max(10, patient_count)), # Asigurăm un minim de pacienți
            weather_temp=round(weather_temp, 1),
            is_holiday=is_holiday,
            is_epidemic=is_epidemic_period,
        )
        patient_flow_objects.append(flow_entry)

    try:
        db.bulk_save_objects(patient_flow_objects)
        db.commit()
        print(f"SUCCESS: Au fost generate și salvate {len(patient_flow_objects)} înregistrări.")
    except Exception as e:
        print(f"ERROR: A apărut o eroare la salvarea datelor: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    generate_synthetic_data()
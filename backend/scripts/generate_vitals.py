"""
Acest script populează tabelele `users`, `patients` și `vital_signs`.
Creează personal medical, pacienți și un istoric de semne vitale pentru aceștia,
simulând inclusiv evenimente critice.

"""

import random
from datetime import datetime, timedelta

from faker import Faker
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Adaugă calea proiectului pentru a putea importa modulele aplicației
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app.models import Base, Patient, RoleEnum, User, VitalSign

# --- Configurare ---
NUM_PATIENTS = 25
NUM_NURSES = 10
NUM_DOCTORS = 5
DAYS_OF_RECORDS = 5  # Câte zile de istoric per pacient
RECORDS_PER_DAY = 6  # Câte înregistrări pe zi (la fiecare 4 ore)
CRITICAL_EVENT_CHANCE = 0.1  # 10% șansă ca un pacient să aibă un eveniment critic

fake = Faker("ro_RO")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def generate_vitals_data():
    """Generează și inserează datele în baza de date."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    if db.query(User).first() or db.query(Patient).first():
        print("INFO: Baza de date conține deja utilizatori sau pacienți. Scriptul se oprește.")
        db.close()
        return

    print("INFO: Se generează utilizatori, pacienți și semne vitale...")

    try:
        # 1. Creare Utilizatori (Personal Medical)
        users = []
        for _ in range(NUM_NURSES):
            users.append(User(full_name=fake.name(), email=fake.email(), password_hash=get_password_hash("string"), role=RoleEnum.nurse))
        for _ in range(NUM_DOCTORS):
            users.append(User(full_name=fake.name(), email=fake.email(), password_hash=get_password_hash("string"), role=RoleEnum.doctor))
        db.bulk_save_objects(users)

        # 2. Creare Pacienți
        patients = []
        for _ in range(NUM_PATIENTS):
            admission_date = datetime.now().date() - timedelta(days=random.randint(DAYS_OF_RECORDS, DAYS_OF_RECORDS + 30))
            patients.append(Patient(full_name=fake.name(), admission_date=admission_date))
        db.bulk_save_objects(patients, return_defaults=True)

        # 3. Generare Semne Vitale
        vital_signs = []
        for patient in patients:
            is_critical_patient = random.random() < CRITICAL_EVENT_CHANCE
            critical_event_start = datetime.now() - timedelta(days=random.randint(1, DAYS_OF_RECORDS - 1), hours=random.randint(0, 23))
            critical_event_end = critical_event_start + timedelta(hours=random.randint(4, 8))

            for day in range(DAYS_OF_RECORDS):
                for record_num in range(RECORDS_PER_DAY):
                    record_time = datetime.now() - timedelta(days=day, hours=record_num * 4)

                    # Valori normale
                    pulse = random.randint(65, 95)
                    systolic = random.randint(110, 130)
                    diastolic = random.randint(70, 85)
                    resp_rate = random.randint(14, 20)
                    o2_sat = random.uniform(96.0, 99.5)

                    # Simulare eveniment critic
                    if is_critical_patient and critical_event_start <= record_time <= critical_event_end:
                        pulse += random.randint(30, 50)  # Tahicardie
                        systolic += random.randint(20, 40) # Hipertensiune
                        resp_rate += random.randint(8, 15) # Tahipnee
                        o2_sat -= random.uniform(5.0, 10.0) # Hipoxie

                    vital = VitalSign(
                        patient_id=patient.id, # Acum patient.id are o valoare corectă
                        blood_pressure=f"{systolic}/{diastolic}",
                        pulse=pulse,
                        respiratory_rate=resp_rate,
                        oxygen_saturation=round(max(85.0, o2_sat), 1),
                        recorded_at=record_time,
                    )
                    vital_signs.append(vital)

        db.bulk_save_objects(vital_signs)
        db.commit()
        print(f"SUCCESS: Au fost creați {len(users)} utilizatori.")
        print(f"SUCCESS: Au fost creați {len(patients)} pacienți.")
        print(f"SUCCESS: Au fost generate {len(vital_signs)} înregistrări de semne vitale.")
    except Exception as e:
        print(f"ERROR: A apărut o eroare la salvarea datelor: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    generate_vitals_data()
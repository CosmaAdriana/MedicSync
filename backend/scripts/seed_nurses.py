"""
Script: Creare departamente + asistenti de test în baza de date.
Rulează din directorul backend/:  python scripts/seed_nurses.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
from app.database import engine, SessionLocal
from app.models import Base, Department, User, RoleEnum

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEPARTMENTS = []  # nu cream departamente noi

NURSES = [
    ("Adriana Lungu",       "adriana.lungu@medicsync.ro",    2),
    ("Beatrice Moldovan",   "beatrice.m@medicsync.ro",       2),
    ("Carmen Diaconu",      "carmen.d@medicsync.ro",         2),
    ("Diana Ivanescu",      "diana.i@medicsync.ro",          2),
    ("Elena Cotea",         "elena.cotea@medicsync.ro",      2),
    ("Florina Badea",       "florina.b@medicsync.ro",        2),
    ("Georgiana Neagu",     "georgiana.n@medicsync.ro",      2),
    ("Ioana Zamfir",        "ioana.zamfir@medicsync.ro",     2),
    ("Lacramioara Toma",    "lacramioara.t@medicsync.ro",    2),
    ("Magdalena Voicu",     "magdalena.v@medicsync.ro",      2),

    ("Maria Popa",          "maria.popa@medicsync.ro",       3),
    ("Andreea Nistor",      "andreea.n@medicsync.ro",        3),
    ("Laura Iordache",      "laura.i@medicsync.ro",          3),
    ("Daniela Marin",       "daniela.m@medicsync.ro",        3),
    ("Oana Serban",         "oana.s@medicsync.ro",           3),
    ("Bianca Tanase",       "bianca.t@medicsync.ro",         3),
    ("Narcisa Craciun",     "narcisa.c@medicsync.ro",        3),
    ("Petronela Dinu",      "petronela.d@medicsync.ro",      3),
    ("Ramona Mihai",        "ramona.mihai@medicsync.ro",     3),
    ("Silvia Enache",       "silvia.e@medicsync.ro",         3),


    ("Gabriela Tudor",      "gabriela.t@medicsync.ro",       4),
    ("Simona Apostol",      "simona.a@medicsync.ro",         4),
    ("Roxana Florea",       "roxana.f@medicsync.ro",         4),
    ("Alina Dobre",         "alina.d@medicsync.ro",          4),
    ("Stefania Ungur",      "stefania.u@medicsync.ro",       4),
    ("Corina Blaga",        "corina.b@medicsync.ro",         4),
    ("Teodora Niculescu",   "teodora.nic@medicsync.ro",      4),
    ("Valentina Paun",      "valentina.p@medicsync.ro",      4),
    ("Xenia Ionita",        "xenia.i@medicsync.ro",          4),
    ("Zoe Draghici",        "zoe.d@medicsync.ro",            4),


    ("Ana Bucur",           "ana.bucur@medicsync.ro",        5),
    ("Brindusa Coman",      "brindusa.c@medicsync.ro",       5),
    ("Catalina Preda",      "catalina.p@medicsync.ro",       5),
    ("Denisa Radu",         "denisa.r@medicsync.ro",         5),
    ("Emilia Stanescu",     "emilia.s@medicsync.ro",         5),
    ("Felicia Moraru",      "felicia.m@medicsync.ro",        5),
    ("Gina Lazar",          "gina.l@medicsync.ro",           5),
    ("Helga Chirila",       "helga.c@medicsync.ro",          5),
    ("Irina Costea",        "irina.costea@medicsync.ro",     5),
    ("Janina Duta",         "janina.d@medicsync.ro",         5),

    ("Ana Maria Ionescu",   "ana.ionescu@medicsync.ro",      6),
    ("Elena Popescu",       "elena.popescu@medicsync.ro",    6),
    ("Mihaela Constantin",  "mihaela.c@medicsync.ro",        6),
    ("Cristina Dumitrescu", "cristina.d@medicsync.ro",       6),
    ("Ioana Stan",          "ioana.stan@medicsync.ro",        6),
    ("Raluca Gheorghe",     "raluca.g@medicsync.ro",         6),
    ("Patricia Vlad",       "patricia.v@medicsync.ro",       6),
    ("Teodora Ciobanu",     "teodora.c@medicsync.ro",        6),
    ("Simona Ciuca",        "simona.ciuca@medicsync.ro",     6),
    ("Veronica Iancu",      "veronica.iancu@medicsync.ro",   6),

    ("Luminita Balan",      "luminita.b@medicsync.ro",       7),
    ("Nicoleta Rusu",       "nicoleta.r@medicsync.ro",       7),
    ("Veronica Matei",      "veronica.m@medicsync.ro",       7),
    ("Camelia Stoica",      "camelia.s@medicsync.ro",        7),
    ("Florentina Ene",      "florentina.e@medicsync.ro",     7),
    ("Mariana Oprea",       "mariana.o@medicsync.ro",        7),
    ("Natalita Sandu",      "natalita.s@medicsync.ro",       7),
    ("Otilia Petre",        "otilia.p@medicsync.ro",         7),
    ("Paula Moise",         "paula.moise@medicsync.ro",      7),
    ("Rebeca Anghel",       "rebeca.a@medicsync.ro",         7),
]

MANAGERS = []

DEFAULT_PASSWORD = "parola123"

def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    hashed = pwd_ctx.hash(DEFAULT_PASSWORD)

    created_depts = 0
    created_nurses = 0
    created_managers = 0
    skipped = 0

    dept_map = {}
    for d in DEPARTMENTS:
        existing = db.query(Department).filter(Department.name == d["name"]).first()
        if not existing:
            dept = Department(name=d["name"], description=d["description"])
            db.add(dept)
            db.flush()
            dept_map[d["name"]] = dept.id
            created_depts += 1
        else:
            dept_map[d["name"]] = existing.id

    db.commit()

    # Asistenti
    for full_name, email, dept_id in NURSES:
        if db.query(User).filter(User.email == email).first():
            skipped += 1
            continue
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hashed,
            role=RoleEnum.nurse,
            department_id=dept_id,
        )
        db.add(user)
        created_nurses += 1

    db.commit()
    db.close()

    print(f"Departamente create: {created_depts}")
    print(f"Asistente create:    {created_nurses}")
    print(f"Manageri creati:     {created_managers}")
    print(f"Deja existente:      {skipped}")
    print(f"\nParola implicita pentru toti: '{DEFAULT_PASSWORD}'")
    print("\nConturi manager:")
    for _, email, dept in MANAGERS:
        print(f"  {email}  ->  {dept}")

if __name__ == "__main__":
    run()

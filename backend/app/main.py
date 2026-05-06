"""
MedicSync — FastAPI Application Entry Point
Run with:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, patients, vitals, inventory, orders, shifts, predictions, fhir, departments, schedule, notifications, users

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    try:
        from .services.staff_predictor import _load_model
        _load_model()
    except Exception:
        pass
    yield


app = FastAPI(
    title="MedicSync API",
    description="Backend API for MedicSync — Health 4.0 hospital management platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(patients.router)
app.include_router(vitals.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(shifts.router)
app.include_router(predictions.router)
app.include_router(fhir.router)
app.include_router(schedule.router)
app.include_router(notifications.router)
app.include_router(users.router)


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "MedicSync API is running"}

"""
MedicSync — FastAPI Application Entry Point
Run with:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, patients, vitals, inventory, orders, shifts, predictions

# Load environment variables from .env (SECRET_KEY, etc.)
load_dotenv()


# ---------------------------------------------------------------------------
# Lifespan — create tables on startup (dev convenience)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (development mode)."""
    # Import models so they register with Base.metadata
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="MedicSync API",
    description="Backend API for MedicSync — Health 4.0 hospital management platform.",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Configuration (Required for React & Streamlit)
# ---------------------------------------------------------------------------
origins = [
    "http://localhost:3000",  # React default port
    "http://localhost:8501",  # Streamlit default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # In development, allow all. In prod, use 'origins' list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — CRUD endpoints
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(vitals.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(shifts.router)
app.include_router(predictions.router)


# ---------------------------------------------------------------------------
# Health-check endpoint
# ---------------------------------------------------------------------------
@app.get("/ping")
def ping():
    """Simple health-check to verify the API is running."""
    return {"status": "ok", "message": "MedicSync API is running 🚀"}

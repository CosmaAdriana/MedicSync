"""
MedicSync — FastAPI Application Entry Point
Run with:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine


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
# Health-check endpoint
# ---------------------------------------------------------------------------
@app.get("/ping")
def ping():
    """Simple health-check to verify the API is running."""
    return {"status": "ok", "message": "MedicSync API is running 🚀"}

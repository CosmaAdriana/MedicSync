"""
MedicSync — Pydantic Schemas
Request/response validation for the FastAPI endpoints.
All schemas use `from_attributes=True` to work seamlessly with SQLAlchemy models.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ========================== User ==========================================

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "nurse"  # doctor | nurse | admin


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: str


# ========================== Patient =======================================

class PatientCreate(BaseModel):
    full_name: str
    admission_date: Optional[date] = None
    status: str = "admitted"  # admitted | discharged | critical


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    admission_date: date
    status: str


# ========================== VitalSign =====================================

class VitalSignCreate(BaseModel):
    patient_id: int
    blood_pressure: str          # e.g. "120/80"
    pulse: int                   # bpm
    respiratory_rate: int        # breaths/min
    oxygen_saturation: float     # SpO2 %


class VitalSignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    blood_pressure: str
    pulse: int
    respiratory_rate: int
    oxygen_saturation: float
    recorded_at: datetime


# ========================== ClinicalAlert =================================

class ClinicalAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    risk_level: str
    message: str
    is_resolved: bool
    created_at: datetime


# ========================== InventoryItem =================================

class InventoryItemCreate(BaseModel):
    product_name: str
    current_stock: int = 0
    expiration_date: date


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    current_stock: int
    expiration_date: date


# ========================== Shift =========================================

class ShiftCreate(BaseModel):
    user_id: int
    start_time: datetime
    end_time: datetime


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    start_time: datetime
    end_time: datetime


# ========================== DailyPatientFlow ==============================

class DailyPatientFlowCreate(BaseModel):
    date: date
    patient_count: int
    weather_temp: Optional[float] = None
    is_holiday: bool = False
    is_epidemic: bool = False


class DailyPatientFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    patient_count: int
    weather_temp: Optional[float]
    is_holiday: bool
    is_epidemic: bool

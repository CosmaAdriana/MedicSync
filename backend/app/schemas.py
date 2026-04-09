"""
MedicSync — Pydantic Schemas
Request/response validation for the FastAPI endpoints.
All schemas use `from_attributes=True` to work seamlessly with SQLAlchemy models.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ========================== Auth ===========================================

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ========================== User ==========================================

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "nurse"  # doctor | nurse | manager | inventory_manager
    department_id: Optional[int] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: str
    department_id: Optional[int] = None


# ========================== Department ====================================

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]


# ========================== Patient =======================================

class PatientCreate(BaseModel):
    full_name: str
    department_id: int
    admission_date: Optional[date] = None
    status: str = "admitted"  # admitted | discharged | critical


class PatientStatusUpdate(BaseModel):
    status: str  # admitted | discharged | critical


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    department_id: int
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

# ========================== OrderItem =====================================

class OrderItemCreate(BaseModel):
    inventory_item_id: int
    quantity: int
    unit_price: float

class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    inventory_item_id: int
    quantity: int
    unit_price: float

# ========================== Order =========================================

class OrderCreate(BaseModel):
    items: list[OrderItemCreate] 

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    status: str
    total_amount: float
    created_at: datetime
    items: list[OrderItemOut] = []


# ========================== InventoryItem =================================

class InventoryItemCreate(BaseModel):
    product_name: str
    current_stock: int = 0
    min_stock_level: int = 0
    expiration_date: date
    unit_price: float = 0.0
    department_id: Optional[int] = None


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    current_stock: int
    min_stock_level: int
    expiration_date: date
    unit_price: float
    department_id: Optional[int] = None


# ========================== Shift =========================================

class ShiftCreate(BaseModel):
    user_id: int
    department_id: int
    start_time: datetime
    end_time: datetime


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    department_id: int
    start_time: datetime
    end_time: datetime


# ========================== DailyPatientFlow ==============================

class DailyPatientFlowCreate(BaseModel):
    date: date
    department_id: int
    patient_count: int
    weather_temp: Optional[float] = None
    is_holiday: bool = False
    is_epidemic: bool = False


class DailyPatientFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    department_id: int
    patient_count: int
    weather_temp: Optional[float]
    is_holiday: bool
    is_epidemic: bool


# ========================== Decision Support ====================

class VitalSignOutWithAlert(BaseModel):
    """Response for POST /vitals — includes auto-generated alert if any."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    blood_pressure: str
    pulse: int
    respiratory_rate: int
    oxygen_saturation: float
    recorded_at: datetime
    alert: Optional[ClinicalAlertOut] = None


class StaffPredictionOut(BaseModel):
    """Response for GET /predict/staff-needs."""
    date: str
    department_name: Optional[str] = None
    predicted_patients: int
    recommended_nurses: int
    model_r2: float
    model_mae: float


class InventoryPredictionItemOut(BaseModel):
    """Single item in GET /predict/inventory response."""
    product_name: str
    current_stock: int
    min_stock_level: int
    avg_daily_consumption: float
    safety_stock: int
    reorder_needed: bool


class FefoAlertOut(BaseModel):
    """Single item in GET /inventory/fefo-alerts response."""
    product_name: str
    current_stock: int
    expiration_date: date
    days_until_expiry: int
    severity: str  # "expired", "critical" (≤7 days), "warning" (≤30 days)

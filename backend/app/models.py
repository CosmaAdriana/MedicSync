"""
MedicSync — ORM Models
"""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class RoleEnum(str, enum.Enum):
    doctor = "doctor"
    nurse = "nurse"
    manager = "manager"
    inventory_manager = "inventory_manager"


class PatientStatusEnum(str, enum.Enum):
    admitted = "admitted"
    discharged = "discharged"
    critical = "critical"


class RiskLevelEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class OrderStatusEnum(str, enum.Enum):
    draft = "draft"
    placed = "placed"
    processed = "processed"
    rejected = "rejected"
    delivered = "delivered"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    patients = relationship("Patient", back_populates="department")
    shifts = relationship("Shift", back_populates="department")
    patient_flows = relationship("DailyPatientFlow", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.nurse)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    shifts = relationship("Shift", back_populates="user")
    department = relationship("Department", foreign_keys=[department_id])


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    admission_date = Column(Date, nullable=False, default=date.today)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    status = Column(Enum(PatientStatusEnum), nullable=False, default=PatientStatusEnum.admitted)

    department = relationship("Department", back_populates="patients")
    vital_signs = relationship("VitalSign", back_populates="patient")
    clinical_alerts = relationship("ClinicalAlert", back_populates="patient")


class VitalSign(Base):
    __tablename__ = "vital_signs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    blood_pressure = Column(String(20), nullable=False)
    pulse = Column(Integer, nullable=False)
    respiratory_rate = Column(Integer, nullable=False)
    oxygen_saturation = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="vital_signs")


class ClinicalAlert(Base):
    __tablename__ = "clinical_alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    risk_level = Column(Enum(RiskLevelEnum), nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="clinical_alerts")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.draft)
    total_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order")
    admin = relationship("User")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    item = relationship("InventoryItem")


class InventoryItem(Base):
    """Medical supply tracked under FEFO policy."""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False)
    current_stock = Column(Integer, nullable=False, default=0)
    min_stock_level = Column(Integer, nullable=False, default=0)
    expiration_date = Column(Date, nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    department = relationship("Department", foreign_keys=[department_id])


class StockUsageLog(Base):
    __tablename__ = "stock_usage_logs"

    id            = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    quantity_used = Column(Integer, nullable=False)
    used_at       = Column(DateTime, nullable=False)

    item       = relationship("InventoryItem")
    department = relationship("Department")


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="shifts")
    department = relationship("Department", back_populates="shifts")


class VacationRequestStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class RequestTypeEnum(str, enum.Enum):
    vacation = "vacation"
    day_off = "day_off"


class VacationRequest(Base):
    __tablename__ = "vacation_requests"

    id = Column(Integer, primary_key=True, index=True)
    nurse_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    request_type = Column(Enum(RequestTypeEnum), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(VacationRequestStatusEnum), nullable=False,
                    default=VacationRequestStatusEnum.pending)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    nurse = relationship("User", foreign_keys=[nurse_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class VacationBalance(Base):
    __tablename__ = "vacation_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    total_days = Column(Integer, nullable=False, default=21)
    used_days = Column(Integer, nullable=False, default=0)

    user = relationship("User", foreign_keys=[user_id])


class MonthlySchedule(Base):
    __tablename__ = "monthly_schedules"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    schedule_data = Column(Text, nullable=False)  # JSON
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_finalized = Column(Boolean, nullable=False, default=False)

    department = relationship("Department", foreign_keys=[department_id])
    creator = relationship("User", foreign_keys=[created_by])


class DailyPatientFlow(Base):
    """Historical daily patient admissions per department, used for ML training."""
    __tablename__ = "daily_patient_flow"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    patient_count = Column(Integer, nullable=False)
    weather_temp = Column(Float, nullable=True)
    is_holiday = Column(Boolean, nullable=False, default=False)
    is_epidemic = Column(Boolean, nullable=False, default=False)

    department = relationship("Department", back_populates="patient_flows")
